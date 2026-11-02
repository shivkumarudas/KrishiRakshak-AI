import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple
import requests

try:
    from strands import tool
except ImportError:
    # Graceful fallback decorator if strands is not installed
    def tool(func):
        return func

logger = logging.getLogger(__name__)

# Cache configuration
WEATHER_CACHE_TTL_SECONDS = int(os.getenv("WEATHER_CACHE_TTL_SECONDS", "1200"))  # 20 minutes default TTL
GEOCODING_CACHE_TTL_SECONDS = int(os.getenv("GEOCODING_CACHE_TTL_SECONDS", "3600"))  # 1 hour

_weather_cache_lock = threading.Lock()
_weather_cache = {}  # (round(lat, 2), round(lon, 2)) -> {"data": dict, "expires_at": float, "fetched_at": float, "fetched_at_iso": str}

_geocoding_cache_lock = threading.Lock()
_geocoding_cache = {}  # "location_str" -> {"data": list, "expires_at": float}

# Global rate-limiting cooldown tracking
_rate_limit_lock = threading.Lock()
_rate_limited_until: float = 0.0
_last_retry_after: int = 60

# Per-coordinate fetch locks to eliminate duplicate in-flight requests
_coord_fetch_locks = {}
_coord_locks_mutex = threading.Lock()

# Persistent disk cache path
_CACHE_FILE_PATH = Path(os.getenv("WEATHER_CACHE_FILE", Path(__file__).resolve().parent.parent / "data" / ".weather_cache.json"))


def _is_pytest_running() -> bool:
    """Check if code is executing under pytest and cache is not explicitly enabled."""
    return "PYTEST_CURRENT_TEST" in os.environ and os.getenv("ENABLE_TEST_CACHE") != "true"


def _get_rounded_coord_key(lat: float, lon: float) -> Tuple[float, float]:
    """Round coordinates to 2 decimal places (~1.1 km grid resolution)."""
    return round(lat, 2), round(lon, 2)


def _get_coord_lock(key: Tuple[float, float]) -> threading.Lock:
    """Get or create a threading lock for a specific coordinate cell."""
    with _coord_locks_mutex:
        if key not in _coord_fetch_locks:
            _coord_fetch_locks[key] = threading.Lock()
        return _coord_fetch_locks[key]


def _is_rate_limited() -> Tuple[bool, int]:
    """Check whether Open-Meteo is currently in an active rate-limit window."""
    now = time.time()
    with _rate_limit_lock:
        if now < _rate_limited_until:
            return True, max(1, int(_rate_limited_until - now))
        return False, 0


def _set_rate_limited(retry_after: Optional[int] = None) -> None:
    """Activate rate-limit backoff window respecting Retry-After."""
    global _rate_limited_until, _last_retry_after
    now = time.time()
    window = retry_after if (retry_after is not None and retry_after > 0) else 60
    # Clamp window between 30 and 600 seconds
    window = min(max(window, 30), 600)
    with _rate_limit_lock:
        _rate_limited_until = max(_rate_limited_until, now + window)
        _last_retry_after = window
    logger.warning("Open-Meteo rate limit active. Backing off for %d seconds (until %.0f).", window, _rate_limited_until)


def _parse_retry_after(response: requests.Response) -> int:
    """Extract and parse Retry-After header from HTTP response."""
    retry_header = response.headers.get("Retry-After")
    if retry_header:
        try:
            return int(retry_header)
        except ValueError:
            try:
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(retry_header)
                diff = int(dt.timestamp() - time.time())
                return max(1, diff)
            except Exception:
                pass
    return 60


def _load_disk_cache() -> None:
    """Load persistent weather cache from disk if available."""
    if _is_pytest_running():
        return
    if not _CACHE_FILE_PATH.exists():
        return
    try:
        with _CACHE_FILE_PATH.open("r", encoding="utf-8") as f:
            persisted = json.load(f)
        with _weather_cache_lock:
            for key_str, entry in persisted.items():
                try:
                    lat_str, lon_str = key_str.split(",")
                    key = (round(float(lat_str), 2), round(float(lon_str), 2))
                    if key not in _weather_cache:
                        _weather_cache[key] = entry
                except (ValueError, KeyError):
                    continue
        logger.info("Loaded %d weather cache entries from disk.", len(_weather_cache))
    except Exception as exc:
        logger.debug("Failed to load disk weather cache: %s", exc)


def _save_disk_cache() -> None:
    """Persist weather cache entries to disk for recovery across restarts."""
    if _is_pytest_running():
        return
    try:
        data_to_save = {}
        with _weather_cache_lock:
            for (lat, lon), entry in _weather_cache.items():
                data_to_save[f"{lat},{lon}"] = entry
        _CACHE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _CACHE_FILE_PATH.open("w", encoding="utf-8") as f:
            json.dump(data_to_save, f)
    except Exception as exc:
        logger.debug("Failed to save disk weather cache: %s", exc)


# Initialize disk cache on startup
_load_disk_cache()


def get_cached_weather(lat: float, lon: float, allow_expired: bool = False) -> Optional[dict]:
    """Retrieve weather data from cache if available."""
    key = _get_rounded_coord_key(lat, lon)
    now = time.time()
    with _weather_cache_lock:
        entry = _weather_cache.get(key)
        if not entry:
            return None

        cached_data = dict(entry["data"])
        cached_data["fetched_at"] = (
            entry.get("fetched_at_iso")
            or datetime.fromtimestamp(entry.get("fetched_at", now), tz=timezone.utc).isoformat()
        )

        if entry.get("expires_at", 0) > now:
            cached_data["is_cached"] = True
            cached_data["is_stale"] = False
            cached_data["is_stale_fallback"] = False
            cached_data["notice"] = None
            return cached_data

        if allow_expired:
            cached_data["is_cached"] = True
            cached_data["is_stale"] = True
            cached_data["is_stale_fallback"] = True
            cached_data["notice"] = (
                "Displaying recent forecast due to temporary weather provider rate limits."
            )
            return cached_data
    return None


def store_weather_cache(lat: float, lon: float, data: dict, ttl: int = WEATHER_CACHE_TTL_SECONDS) -> None:
    """Store fresh weather data in in-memory and disk cache."""
    key = _get_rounded_coord_key(lat, lon)
    now = time.time()
    now_iso = data.get("fetched_at") or datetime.now(timezone.utc).isoformat()
    clean_data = dict(data)
    clean_data["fetched_at"] = now_iso

    with _weather_cache_lock:
        _weather_cache[key] = {
            "data": clean_data,
            "fetched_at": now,
            "fetched_at_iso": now_iso,
            "expires_at": now + ttl,
        }
    _save_disk_cache()


def clear_weather_cache() -> None:
    """Clear weather cache and rate limit window (useful for testing)."""
    global _rate_limited_until
    with _weather_cache_lock:
        _weather_cache.clear()
    with _geocoding_cache_lock:
        _geocoding_cache.clear()
    with _rate_limit_lock:
        _rate_limited_until = 0.0
    with _coord_locks_mutex:
        _coord_fetch_locks.clear()
    try:
        if _CACHE_FILE_PATH.exists():
            _CACHE_FILE_PATH.unlink()
    except OSError:
        pass


def fetch_weather(latitude: float, longitude: float, force_refresh: bool = False) -> dict:
    """Fetch a three-day weather forecast using coordinates with caching and 429 protection."""

    # 1. Validate coordinates
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError):
        return {
            "error": "Invalid coordinates: latitude and longitude must be valid numbers."
        }

    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        return {
            "error": (
                "Coordinates out of bounds: latitude must be between -90 and 90, "
                "and longitude between -180 and 180."
            )
        }

    coord_key = _get_rounded_coord_key(lat, lon)

    # 2. Check fresh cache unless force_refresh is requested or pytest is running
    if not force_refresh and not _is_pytest_running():
        cached = get_cached_weather(lat, lon, allow_expired=False)
        if cached is not None:
            return cached

    # 3. Check rate-limit window before making network calls
    is_limited, remaining = _is_rate_limited()
    if is_limited and not _is_pytest_running():
        logger.info("Open-Meteo rate-limited cooldown active (%ds remaining). Checking cache...", remaining)
        stale_cached = get_cached_weather(lat, lon, allow_expired=True)
        if stale_cached is not None:
            stale_cached["retry_after"] = remaining
            stale_cached["notice"] = (
                f"Displaying recent forecast due to temporary weather provider rate limits. Provider reset in {remaining}s."
            )
            return stale_cached
        return {
            "error": (
                "Weather forecast service is temporarily busy (rate limit reached). "
                "Please wait a few moments and try again."
            ),
            "retry_after": remaining,
            "status_code": 429,
        }

    # 4. Coordinate-level lock to deduplicate concurrent backend requests
    coord_lock = _get_coord_lock(coord_key)
    with coord_lock:
        # Double-check cache inside lock in case another thread just fetched it
        if not force_refresh and not _is_pytest_running():
            cached = get_cached_weather(lat, lon, allow_expired=False)
            if cached is not None:
                return cached

        # Double-check rate limit inside lock
        is_limited, remaining = _is_rate_limited()
        if is_limited and not _is_pytest_running():
            stale_cached = get_cached_weather(lat, lon, allow_expired=True)
            if stale_cached is not None:
                stale_cached["retry_after"] = remaining
                return stale_cached
            return {
                "error": (
                    "Weather forecast service is temporarily busy (rate limit reached). "
                    "Please wait a few moments and try again."
                ),
                "retry_after": remaining,
                "status_code": 429,
            }

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": (
                "precipitation_probability_max,"
                "precipitation_sum,"
                "weather_code"
            ),
            "forecast_days": 3,
            "timezone": "Asia/Kolkata",
        }
        headers = {
            "User-Agent": "KrishiRakshak-AI/1.0 (https://github.com/shivkumarudas/KrishiRakshak-AI)",
            "Accept": "application/json",
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)

            # Handle rate limiting (429) specifically
            if response.status_code == 429:
                retry_after = _parse_retry_after(response)
                _set_rate_limited(retry_after)
                logger.warning("Open-Meteo returned 429 Too Many Requests for (%s, %s). Cooldown: %ds", lat, lon, retry_after)

                stale_cached = get_cached_weather(lat, lon, allow_expired=True)
                if stale_cached is not None:
                    stale_cached["retry_after"] = retry_after
                    stale_cached["notice"] = (
                        f"Displaying recent forecast due to temporary weather provider rate limits. Provider reset in {retry_after}s."
                    )
                    return stale_cached
                return {
                    "error": (
                        "Weather forecast service is temporarily busy (rate limit reached). "
                        "Please wait a few moments and try again."
                    ),
                    "retry_after": retry_after,
                    "status_code": 429,
                }

            response.raise_for_status()

            data = response.json()
            if not isinstance(data, dict) or "daily" not in data or not isinstance(data["daily"], dict):
                return {"error": "Invalid response format: 'daily' forecast data missing from Open-Meteo."}

            daily = data["daily"]
            dates = daily.get("time")

            if not isinstance(dates, list) or len(dates) == 0:
                return {"error": "Incomplete weather information: forecast dates missing."}

            now_iso = datetime.now(timezone.utc).isoformat()
            result = {
                "dates": dates,
                "rain_probability_percent": daily.get("precipitation_probability_max", []),
                "rainfall_mm": daily.get("precipitation_sum", []),
                "weather_codes": daily.get("weather_code", []),
                "source": "Open-Meteo",
                "fetched_at": now_iso,
                "is_cached": False,
                "is_stale": False,
                "notice": None,
            }

            # Store in cache unless pytest is running
            if not _is_pytest_running():
                store_weather_cache(lat, lon, result)
            return result

        except requests.RequestException as error:
            err_msg = str(error)
            logger.warning("Open-Meteo request failed: %s", err_msg)

            # If HTTP 429 in error message
            if "429" in err_msg or "too many requests" in err_msg.lower():
                _set_rate_limited(60)
                stale_cached = get_cached_weather(lat, lon, allow_expired=True)
                if stale_cached is not None:
                    stale_cached["retry_after"] = 60
                    stale_cached["notice"] = (
                        "Displaying recent forecast due to temporary weather provider rate limits. Provider reset in 60s."
                    )
                    return stale_cached
                return {
                    "error": (
                        "Weather forecast service is temporarily busy (rate limit reached). "
                        "Please wait a few moments and try again."
                    ),
                    "retry_after": 60,
                    "status_code": 429,
                }

            return {"error": f"Unable to retrieve weather: {error}"}
        except (KeyError, ValueError) as error:
            return {"error": f"Unable to retrieve weather: {error}"}


@tool
def get_weather_forecast(location: str) -> dict:
    """
    Find a village, town, or city and retrieve its weather forecast.

    Args:
        location: Location name, such as Pune, Maharashtra.

    Returns:
        Location details and forecast data.
    """

    if not location or not isinstance(location, str) or not location.strip():
        return {"error": "Location name must be a non-empty string."}

    norm_location = location.strip().lower()
    now = time.time()

    # Check geocoding cache unless running pytest
    results = None
    if not _is_pytest_running():
        with _geocoding_cache_lock:
            geo_entry = _geocoding_cache.get(norm_location)
            if geo_entry and geo_entry["expires_at"] > now:
                results = geo_entry["data"]

    if results is None:
        try:
            response = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={
                    "name": location.strip(),
                    "count": 10,
                    "language": "en",
                    "format": "json",
                },
                headers={
                    "User-Agent": "KrishiRakshak-AI/1.0 (https://github.com/shivkumarudas/KrishiRakshak-AI)",
                    "Accept": "application/json",
                },
                timeout=10,
            )

            if response.status_code == 429:
                return {
                    "error": (
                        "Location search is temporarily busy (rate limit reached). "
                        "Please wait a moment and try again."
                    )
                }

            response.raise_for_status()
            results = response.json().get("results", [])

            # Cache the geocoding results unless running under pytest
            if not _is_pytest_running():
                with _geocoding_cache_lock:
                    _geocoding_cache[norm_location] = {
                        "data": results,
                        "expires_at": now + GEOCODING_CACHE_TTL_SECONDS,
                    }

        except requests.RequestException as error:
            err_msg = str(error)
            if "429" in err_msg or "too many requests" in err_msg.lower():
                return {
                    "error": (
                        "Location search is temporarily busy (rate limit reached). "
                        "Please wait a moment and try again."
                    )
                }
            return {"error": f"Unable to retrieve weather data: {error}"}
        except (KeyError, ValueError) as error:
            return {"error": f"Unable to retrieve weather data: {error}"}

    if not results:
        return {"error": f"Location not found: {location}"}

    # Select the first geocoding result.
    place = results[0]

    forecast = fetch_weather(
        place["latitude"],
        place["longitude"],
    )

    if "error" in forecast:
        return forecast

    return {
        "location": place.get("name"),
        "district_or_region": place.get("admin1"),
        "country": place.get("country"),
        "latitude": place["latitude"],
        "longitude": place["longitude"],
        **forecast,
    }
