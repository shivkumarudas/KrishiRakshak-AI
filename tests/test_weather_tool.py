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
