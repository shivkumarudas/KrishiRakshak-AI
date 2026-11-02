"""Tests for tools/weather_tool.py — fetch_weather and get_weather_forecast."""

from unittest.mock import patch, MagicMock
from tools.weather_tool import fetch_weather, get_weather_forecast


# --------------------------------------------------
# fetch_weather tests
# --------------------------------------------------

class TestFetchWeather:
    """Tests for the fetch_weather function."""

    def _mock_forecast_response(self):
        """Return a realistic Open-Meteo daily forecast response."""
        return {
            "daily": {
                "time": ["2026-10-26", "2026-10-27", "2026-10-28"],
                "precipitation_probability_max": [80, 45, 10],
                "precipitation_sum": [25.0, 5.2, 0.0],
                "weather_code": [61, 3, 0],
            }
        }

    @patch("tools.weather_tool.requests.get")
    def test_valid_coordinates(self, mock_get):
        """A valid API response returns dates, probabilities, and rainfall."""
        mock_response = MagicMock()
        mock_response.json.return_value = self._mock_forecast_response()
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_weather(18.52, 73.86)

        assert "error" not in result
        assert result["dates"] == ["2026-10-26", "2026-10-27", "2026-10-28"]
        assert result["rain_probability_percent"] == [80, 45, 10]
        assert result["rainfall_mm"] == [25.0, 5.2, 0.0]
        assert result["weather_codes"] == [61, 3, 0]
        assert result["source"] == "Open-Meteo"

    @patch("tools.weather_tool.requests.get")
    def test_network_error(self, mock_get):
        """A network failure returns an error dict."""
        import requests
        mock_get.side_effect = requests.ConnectionError("Network down")

        result = fetch_weather(18.52, 73.86)

        assert "error" in result
        assert "Unable to retrieve weather" in result["error"]

    @patch("tools.weather_tool.requests.get")
    def test_timeout_error(self, mock_get):
        """A request timeout returns an error dict."""
        import requests
        mock_get.side_effect = requests.Timeout("Request timed out")

        result = fetch_weather(18.52, 73.86)

        assert "error" in result

    @patch("tools.weather_tool.requests.get")
    def test_malformed_json(self, mock_get):
        """Missing 'daily' key in response returns an error dict."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"unexpected": "data"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_weather(18.52, 73.86)

        assert "error" in result

    @patch("tools.weather_tool.requests.get")
    def test_http_500_error(self, mock_get):
        """An HTTP 500 response returns an error dict."""
        import requests
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = (
            requests.HTTPError("500 Server Error")
        )
        mock_get.return_value = mock_response

        result = fetch_weather(18.52, 73.86)

        assert "error" in result

    def test_invalid_latitude_out_of_bounds(self):
        """Latitude out of range [-90, 90] returns error without calling API."""
        result = fetch_weather(95.0, 73.86)
        assert "error" in result
        assert "latitude must be between -90 and 90" in result["error"].lower()

        result_low = fetch_weather(-91.0, 73.86)
        assert "error" in result_low

    def test_invalid_longitude_out_of_bounds(self):
        """Longitude out of range [-180, 180] returns error without calling API."""
        result = fetch_weather(18.52, 185.0)
        assert "error" in result
        assert "longitude between -180 and 180" in result["error"].lower()

        result_low = fetch_weather(18.52, -185.0)
        assert "error" in result_low

    def test_non_numeric_coordinates(self):
        """Non-numeric coordinates return an error dictionary."""
        result = fetch_weather("not-a-number", 73.86)
        assert "error" in result
        assert "valid numbers" in result["error"]

    @patch("tools.weather_tool.requests.get")
    def test_missing_time_key_in_daily(self, mock_get):
        """Missing 'time' array in 'daily' payload returns error."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "daily": {
                "precipitation_probability_max": [80],
                "precipitation_sum": [25.0],
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_weather(18.52, 73.86)
        assert "error" in result
        assert "forecast dates missing" in result["error"].lower()


# --------------------------------------------------
# get_weather_forecast tests (Strands @tool)
# --------------------------------------------------

class TestGetWeatherForecast:
    """Tests for the get_weather_forecast Strands tool function."""

    def _mock_geocoding_and_forecast(self):
        """Return mock geocoding results and forecast data."""
        geocoding = {
            "results": [
                {
                    "name": "Pune",
                    "admin1": "Maharashtra",
                    "country": "India",
                    "latitude": 18.52,
                    "longitude": 73.86,
                }
            ]
        }
        forecast = {
            "daily": {
                "time": ["2026-10-26"],
                "precipitation_probability_max": [60],
                "precipitation_sum": [12.0],
                "weather_code": [3],
            }
        }
        return geocoding, forecast

    @patch("tools.weather_tool.requests.get")
    def test_valid_location(self, mock_get):
        """A recognized location returns forecast data."""
        geocoding, forecast = self._mock_geocoding_and_forecast()

        def side_effect(url, **kwargs):
            mock = MagicMock()
            mock.raise_for_status = MagicMock()
            if "geocoding" in url:
                mock.json.return_value = geocoding
            else:
                mock.json.return_value = forecast
            return mock

        mock_get.side_effect = side_effect

        result = get_weather_forecast("Pune")

        assert "error" not in result
        assert result["location"] == "Pune"
        assert result["country"] == "India"
        assert result["dates"] == ["2026-10-26"]

    @patch("tools.weather_tool.requests.get")
    def test_location_not_found(self, mock_get):
        """An unrecognized location returns an error."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response

        result = get_weather_forecast("xyznonexistent123")

        assert "error" in result
        assert "not found" in result["error"].lower()

    @patch("tools.weather_tool.requests.get")
    def test_geocoding_network_error(self, mock_get):
        """A network error during geocoding returns an error."""
        import requests
        mock_get.side_effect = requests.ConnectionError("Offline")

        result = get_weather_forecast("Pune")

        assert "error" in result

    def test_empty_or_invalid_location_string(self):
        """Empty, non-string, or whitespace-only location returns error."""
        assert "error" in get_weather_forecast("")
        assert "error" in get_weather_forecast("   ")
        assert "error" in get_weather_forecast(None)
        assert "error" in get_weather_forecast(12345)


class TestWeatherCacheAndRateLimiting:
    """Tests for weather forecast caching and 429 rate-limiting resilience."""

    def setup_method(self):
        from tools.weather_tool import clear_weather_cache
        clear_weather_cache()

    def teardown_method(self):
        from tools.weather_tool import clear_weather_cache
        clear_weather_cache()

    def test_cache_storage_and_retrieval(self):
        """Weather data is stored and retrieved by coordinate cell."""
        from tools.weather_tool import store_weather_cache, get_cached_weather

        mock_data = {
            "dates": ["2026-11-02", "2026-11-03", "2026-11-04"],
            "rain_probability_percent": [10, 20, 0],
            "rainfall_mm": [0.0, 1.2, 0.0],
            "weather_codes": [1, 2, 0],
            "source": "Open-Meteo",
        }

        store_weather_cache(18.5204, 73.8567, mock_data, ttl=60)

        # Coordinate rounding matches within ~1km cell (18.52, 73.86)
        cached = get_cached_weather(18.5211, 73.8572)
        assert cached is not None
        assert cached["dates"] == ["2026-11-02", "2026-11-03", "2026-11-04"]
        assert cached["source"] == "Open-Meteo"

    def test_expired_cache_not_returned_by_default(self):
        """Expired cache entries are ignored by default."""
        from tools.weather_tool import store_weather_cache, get_cached_weather

        mock_data = {"dates": ["2026-11-02"], "source": "Open-Meteo"}
        store_weather_cache(18.52, 73.86, mock_data, ttl=-10)  # already expired

        assert get_cached_weather(18.52, 73.86, allow_expired=False) is None

    def test_expired_cache_returned_when_allowed_with_notice(self):
        """Expired cache entries are returned with safety notice when allow_expired=True."""
        from tools.weather_tool import store_weather_cache, get_cached_weather

        mock_data = {"dates": ["2026-11-02"], "source": "Open-Meteo"}
        store_weather_cache(18.52, 73.86, mock_data, ttl=-10)

        stale = get_cached_weather(18.52, 73.86, allow_expired=True)
        assert stale is not None
        assert stale["is_cached"] is True
        assert stale["is_stale_fallback"] is True
        assert "notice" in stale

    @patch("tools.weather_tool.requests.get")
    def test_http_429_returns_clean_error_when_no_cache(self, mock_get):
        """HTTP 429 returns a friendly user error rather than an unhandled 502 crash."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "45"}
        mock_get.return_value = mock_response

        result = fetch_weather(18.52, 73.86)
        assert "error" in result
        assert "rate limit reached" in result["error"].lower()
        assert result.get("status_code") == 429
        assert result.get("retry_after") == 45

    @patch("tools.weather_tool.requests.get")
    def test_http_429_returns_stale_cache_when_available(self, mock_get):
        """HTTP 429 returns recent cached forecast with notice if available."""
        from tools.weather_tool import store_weather_cache

        mock_data = {
            "dates": ["2026-11-02"],
            "rain_probability_percent": [5],
            "rainfall_mm": [0.0],
            "weather_codes": [1],
            "source": "Open-Meteo",
        }
        store_weather_cache(18.52, 73.86, mock_data, ttl=-5)  # expired cache entry

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_get.return_value = mock_response

        result = fetch_weather(18.52, 73.86)
        assert "error" not in result
        assert result["dates"] == ["2026-11-02"]
        assert result.get("is_stale_fallback") is True
        assert result.get("is_cached") is True
        assert "notice" in result

    @patch("tools.weather_tool.requests.get")
    def test_rate_limit_cooldown_prevents_subsequent_http_calls(self, mock_get):
        """Subsequent requests during the cooldown window do not call Open-Meteo."""
        import os
        from tools.weather_tool import _set_rate_limited, _is_rate_limited

        # Set a 60-second rate-limit cooldown
        _set_rate_limited(60)
        is_limited, remaining = _is_rate_limited()
        assert is_limited is True
        assert remaining > 0

        # Run with cache enabled so rate limit check is active
        with patch.dict(os.environ, {"ENABLE_TEST_CACHE": "true"}):
            result = fetch_weather(18.52, 73.86)
            # requests.get should NOT be called at all
            mock_get.assert_not_called()
            assert "error" in result
            assert result.get("status_code") == 429
            assert result.get("retry_after") > 0

    @patch("tools.weather_tool.requests.get")
    def test_cache_hit_avoids_network_call_and_sets_cached_flag(self, mock_get):
        """When cache is populated, subsequent fetch returns cached forecast without network."""
        import os

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "daily": {
                "time": ["2026-11-02", "2026-11-03", "2026-11-04"],
                "precipitation_probability_max": [10, 20, 0],
                "precipitation_sum": [0.0, 1.0, 0.0],
                "weather_code": [1, 2, 0],
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"ENABLE_TEST_CACHE": "true"}):
            # First fetch: calls network
            res1 = fetch_weather(18.52, 73.86)
            assert mock_get.call_count == 1
            assert res1.get("is_cached") is False
            assert "fetched_at" in res1
            first_timestamp = res1["fetched_at"]

            # Second fetch: served from cache, no second network call
            res2 = fetch_weather(18.5201, 73.8601)  # nearby coordinate in same cell
            assert mock_get.call_count == 1
            assert res2.get("is_cached") is True
            assert res2.get("is_stale") is False
            assert res2.get("fetched_at") == first_timestamp

    @patch("tools.weather_tool.requests.get")
    def test_force_refresh_bypasses_cache(self, mock_get):
        """force_refresh=True forces a fresh API request even if cached."""
        import os

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "daily": {
                "time": ["2026-11-02"],
                "precipitation_probability_max": [10],
                "precipitation_sum": [0.0],
                "weather_code": [1],
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"ENABLE_TEST_CACHE": "true"}):
            fetch_weather(18.52, 73.86)
            assert mock_get.call_count == 1

            # force_refresh=True makes a 2nd call
            fetch_weather(18.52, 73.86, force_refresh=True)
            assert mock_get.call_count == 2

    def test_disk_cache_save_and_reload(self, tmp_path):
        """Disk cache survives in-memory cache clearing."""
        from tools.weather_tool import store_weather_cache, get_cached_weather, _load_disk_cache, _weather_cache_lock, _weather_cache
        import tools.weather_tool
        import os

        test_cache_file = tmp_path / "test_weather_cache.json"
        orig_file = tools.weather_tool._CACHE_FILE_PATH
        tools.weather_tool._CACHE_FILE_PATH = test_cache_file

        try:
            with patch.dict(os.environ, {"ENABLE_TEST_CACHE": "true"}):
                sample_data = {
                    "dates": ["2026-11-02"],
                    "source": "Open-Meteo",
                    "fetched_at": "2026-11-02T10:00:00+00:00",
                }
                store_weather_cache(18.52, 73.86, sample_data, ttl=300)
                assert test_cache_file.exists()

                # Clear in-memory dictionary
                with _weather_cache_lock:
                    _weather_cache.clear()
                assert get_cached_weather(18.52, 73.86) is None

                # Reload from disk
                _load_disk_cache()
                reloaded = get_cached_weather(18.52, 73.86)
                assert reloaded is not None
                assert reloaded["dates"] == ["2026-11-02"]
        finally:
            tools.weather_tool._CACHE_FILE_PATH = orig_file
