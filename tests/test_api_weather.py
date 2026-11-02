"""Tests for weather and location search API endpoints."""

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import requests
from api.main import app

client = TestClient(app)


class TestLocationSearchEndpoint:
    """Tests for GET /api/locations/search."""

    @patch("api.routes.weather.http_requests.get")
    def test_search_locations_success(self, mock_get):
        """Valid query returns mapped location results."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
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
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        response = client.get("/api/locations/search?name=Pune")
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "Pune"
        assert len(data["results"]) == 1
        assert data["results"][0]["name"] == "Pune"
        assert data["results"][0]["region"] == "Maharashtra"
        assert data["results"][0]["latitude"] == 18.52

    @patch("api.routes.weather.http_requests.get")
    def test_search_locations_with_q_param(self, mock_get):
        """Query with 'q' parameter returns mapped results."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "name": "Nagpur",
                    "admin1": "Maharashtra",
                    "country": "India",
                    "latitude": 21.14,
                    "longitude": 79.08,
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        response = client.get("/api/locations/search?q=Nagpur")
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "Nagpur"
        assert data["results"][0]["name"] == "Nagpur"

    @patch("api.routes.weather.http_requests.get")
    def test_search_locations_empty_result(self, mock_get):
        """Unknown location returns empty results list."""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        response = client.get("/api/locations/search?name=NonExistentPlaceXYZ")
        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []

    def test_search_locations_missing_param(self):
        """Missing name parameter returns 422 validation error."""
        response = client.get("/api/locations/search")
        assert response.status_code == 422

    @patch("api.routes.weather.http_requests.get")
    def test_search_locations_network_error(self, mock_get):
        """Network error during search returns 502 Bad Gateway."""
        mock_get.side_effect = requests.ConnectionError("Connection failed")
        response = client.get("/api/locations/search?name=Pune")
        assert response.status_code == 502


class TestWeatherEndpoint:
    """Tests for GET /api/weather."""

    def _mock_forecast(self):
        return {
            "dates": ["2026-10-26", "2026-10-27", "2026-10-28"],
            "rain_probability_percent": [75, 40, 10],
            "rainfall_mm": [22.0, 5.0, 0.0],
            "weather_codes": [61, 3, 0],
            "source": "Open-Meteo",
        }

    @patch("api.routes.weather.fetch_weather")
    def test_get_weather_success(self, mock_fetch):
        """Valid coordinates return weather forecast and rule-based guidance."""
        mock_fetch.return_value = self._mock_forecast()

        response = client.get("/api/weather?latitude=18.52&longitude=73.86&location_name=Pune")
        assert response.status_code == 200
        data = response.json()
        assert data["location_name"] == "Pune"
        assert len(data["dates"]) == 3
        assert len(data["daily_guidance"]) == 3
        # Day 1 has high rain probability (75%) and heavy rain (22mm)
        day1 = data["daily_guidance"][0]
        assert day1["rain_probability_percent"] == 75
        assert len(day1["risks"]) > 0
        assert "disclaimer" in data

    def test_get_weather_invalid_latitude(self):
        """Out of bounds latitude returns 422."""
        response = client.get("/api/weather?latitude=999&longitude=73.86")
        assert response.status_code == 422

    def test_get_weather_invalid_longitude(self):
        """Out of bounds longitude returns 422."""
        response = client.get("/api/weather?latitude=18.52&longitude=999")
        assert response.status_code == 422

    @patch("api.routes.weather.fetch_weather")
    def test_get_weather_service_error(self, mock_fetch):
        """Weather service failure returns 502 Bad Gateway."""
        mock_fetch.return_value = {"error": "Open-Meteo timeout"}

        response = client.get("/api/weather?latitude=18.52&longitude=73.86")
        assert response.status_code == 502
        assert "Open-Meteo timeout" in response.json()["detail"]

    @patch("api.routes.weather.fetch_weather")
    def test_get_weather_rate_limit_returns_429_and_retry_after_header(self, mock_fetch):
        """When weather provider hits 429 and no cache exists, returns 429 with Retry-After header."""
        mock_fetch.return_value = {
            "error": "Weather forecast service is temporarily busy (rate limit reached). Please wait a few moments and try again.",
            "retry_after": 75,
            "status_code": 429,
        }

        response = client.get("/api/weather?latitude=18.52&longitude=73.86")
        assert response.status_code == 429
        assert "rate limit reached" in response.json()["detail"].lower()
        assert response.headers.get("retry-after") == "75"

    @patch("api.routes.weather.fetch_weather")
    def test_get_weather_returns_cached_and_stale_metadata(self, mock_fetch):
        """When cached/stale fallback is used, response includes cache flags, timestamp and notice."""
        forecast = self._mock_forecast()
        forecast["is_cached"] = True
        forecast["is_stale"] = True
        forecast["fetched_at"] = "2026-11-02T12:00:00+00:00"
        forecast["notice"] = "Displaying recent forecast due to temporary weather provider rate limits."
        mock_fetch.return_value = forecast

        response = client.get("/api/weather?latitude=18.52&longitude=73.86")
        assert response.status_code == 200
        data = response.json()
        assert data["is_cached"] is True
        assert data["is_stale"] is True
        assert data["fetched_at"] == "2026-11-02T12:00:00+00:00"
        assert "rate limits" in data["notice"]

    @patch("api.routes.weather.fetch_weather")
    def test_get_weather_passes_force_refresh(self, mock_fetch):
        """force_refresh query parameter is passed to fetch_weather."""
        mock_fetch.return_value = self._mock_forecast()

        response = client.get("/api/weather?latitude=18.52&longitude=73.86&force_refresh=true")
        assert response.status_code == 200
        mock_fetch.assert_called_once_with(18.52, 73.86, force_refresh=True)

    @patch("api.routes.weather.store_weather_cache")
    def test_post_weather_cache_sync(self, mock_store):
        """Client-side direct weather fetch syncs to server cache."""
        payload = {
            "latitude": 19.26,
            "longitude": 76.77,
            "dates": ["2026-11-02", "2026-11-03", "2026-11-04"],
            "rain_probability_percent": [5, 10, 0],
            "rainfall_mm": [0.0, 0.0, 0.0],
            "weather_codes": [1, 2, 0],
            "source": "Open-Meteo",
        }
        response = client.post("/api/weather/cache", json=payload)
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "cached": True}
        assert mock_store.call_count == 1
