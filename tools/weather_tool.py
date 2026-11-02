import logging
import os
import threading
import time
from typing import Optional, Tuple
import requests
from strands import tool

logger = logging.getLogger(__name__)

# Cache configuration
WEATHER_CACHE_TTL_SECONDS = int(os.getenv("WEATHER_CACHE_TTL_SECONDS", "1200"))  # 20 minutes
GEOCODING_CACHE_TTL_SECONDS = int(os.getenv("GEOCODING_CACHE_TTL_SECONDS", "3600"))  # 1 hour

_weather_cache_lock = threading.Lock()
_weather_cache = {}  # (round(lat, 2), round(lon, 2)) -> {"data": dict, "expires_at": float, "fetched_at": float}

_geocoding_cache_lock = threading.Lock()
_geocoding_cache = {}  # "location_str" -> {"data": list, "expires_at": float}


def _is_pytest_running() -> bool:
    """Check if code is executing under pytest and cache is not explicitly enabled."""
    return "PYTEST_CURRENT_TEST" in os.environ and os.getenv("ENABLE_TEST_CACHE") != "true"


def _get_rounded_coord_key(lat: float, lon: float) -> Tuple[float, float]:
    """Round coordinates to 2 decimal places (~1.1 km grid resolution)."""
    return round(lat, 2), round(lon, 2)


def get_cached_weather(lat: float, lon: float, allow_expired: bool = False) -> Optional[dict]:
    """Retrieve weather data from in-memory cache if available."""
    key = _get_rounded_coord_key(lat, lon)
    now = time.time()
    with _weather_cache_lock:
        entry = _weather_cache.get(key)
        if not entry:
            return None
        if entry["expires_at"] > now:
            return dict(entry["data"])
        if allow_expired:
            expired_data = dict(entry["data"])
            expired_data["is_cached"] = True
            expired_data["is_stale_fallback"] = True
            expired_data["notice"] = (
                "Displaying recent forecast due to temporary weather provider rate limits."
            )
            return expired_data
    return None


def store_weather_cache(lat: float, lon: float, data: dict, ttl: int = WEATHER_CACHE_TTL_SECONDS) -> None:
    """Store fresh weather data in in-memory cache."""
    key = _get_rounded_coord_key(lat, lon)
    now = time.time()
    with _weather_cache_lock:
        _weather_cache[key] = {
            "data": dict(data),
            "fetched_at": now,
            "expires_at": now + ttl,
        }


def clear_weather_cache() -> None:
    """Clear weather cache (useful for testing)."""
    with _weather_cache_lock:
        _weather_cache.clear()
    with _geocoding_cache_lock:
        _geocoding_cache.clear()


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

    # 2. Check cache unless force_refresh is requested or pytest is running
    if not force_refresh and not _is_pytest_running():
        cached = get_cached_weather(lat, lon, allow_expired=False)
        if cached is not None:
            return cached

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

    try:
        response = requests.get(url, params=params, timeout=15)

        # Handle rate limiting (429) specifically
        if response.status_code == 429:
            logger.warning("Open-Meteo returned 429 Too Many Requests for (%s, %s)", lat, lon)
            # Try to return expired cache if available
            stale_cached = get_cached_weather(lat, lon, allow_expired=True)
            if stale_cached is not None:
                return stale_cached
            return {
                "error": (
                    "Weather forecast service is temporarily busy (rate limit reached). "
                    "Please wait a few moments and try again."
                )
            }

        response.raise_for_status()

        data = response.json()
        if not isinstance(data, dict) or "daily" not in data or not isinstance(data["daily"], dict):
            return {"error": "Invalid response format: 'daily' forecast data missing from Open-Meteo."}

        daily = data["daily"]
        dates = daily.get("time")

        if not isinstance(dates, list) or len(dates) == 0:
            return {"error": "Incomplete weather information: forecast dates missing."}

        result = {
            "dates": dates,
            "rain_probability_percent": daily.get("precipitation_probability_max", []),
            "rainfall_mm": daily.get("precipitation_sum", []),
            "weather_codes": daily.get("weather_code", []),
            "source": "Open-Meteo",
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
            stale_cached = get_cached_weather(lat, lon, allow_expired=True)
            if stale_cached is not None:
                return stale_cached
            return {
                "error": (
                    "Weather forecast service is temporarily busy (rate limit reached). "
                    "Please wait a few moments and try again."
                )
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
                timeout=15,
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
