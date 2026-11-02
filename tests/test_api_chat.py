"""Tests for AI Agricultural Assistant chat API endpoint."""

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestChatEndpoint:
    """Tests for POST /api/chat."""

    @patch("api.routes.chat.get_agent")
    def test_chat_success_without_location(self, mock_get_agent):
        """Chat succeeds without location, returns AI response."""
        mock_agent = MagicMock()
        mock_agent.return_value = "Soybean requires well-drained soil and 450-500mm water."
        mock_get_agent.return_value = mock_agent

        payload = {"message": "How much water does soybean need?"}
        response = client.post("/api/chat", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "Soybean requires" in data["response"]
        assert data["weather_included"] is False
        assert data["fallback_used"] is False

    @patch("api.routes.chat.fetch_weather")
    @patch("api.routes.chat.get_agent")
    def test_chat_success_with_location(self, mock_get_agent, mock_fetch_weather):
        """Chat with location includes weather context."""
        mock_fetch_weather.return_value = {
            "dates": ["2026-10-26"],
            "rain_probability_percent": [20],
            "rainfall_mm": [0.0],
            "weather_codes": [0],
            "source": "Open-Meteo",
        }
        mock_agent = MagicMock()
        mock_agent.return_value = "The forecast for Pune shows dry weather. You may irrigate your crop."
        mock_get_agent.return_value = mock_agent

        payload = {
            "message": "Should I irrigate my cotton field today?",
            "location": {
                "name": "Pune",
                "region": "Maharashtra",
                "country": "India",
                "latitude": 18.52,
                "longitude": 73.86,
            },
        }
        response = client.post("/api/chat", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "irrigate" in data["response"].lower()
        assert data["weather_included"] is True
        assert data["fallback_used"] is False

    @patch("api.routes.chat.get_agent")
    def test_chat_fallback_on_gemini_error(self, mock_get_agent):
        """When Gemini raises quota/rate-limit error, fallback is returned gracefully."""
        mock_agent = MagicMock()
        mock_agent.side_effect = Exception("ResourceExhausted: 429 Quota exceeded")
        mock_get_agent.return_value = mock_agent

        payload = {"message": "What pest is attacking my crop?"}
        response = client.post("/api/chat", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["fallback_used"] is True
        assert "temporarily unavailable" in data["response"].lower()
        assert "dedicated" in data["response"].lower()

    @patch("api.routes.chat.fetch_weather")
    @patch("api.routes.chat.get_agent")
    def test_chat_fallback_with_weather_context(self, mock_get_agent, mock_fetch_weather):
        """When Gemini fails but location was given, fallback includes weather rules."""
        mock_fetch_weather.return_value = {
            "dates": ["2026-10-26"],
            "rain_probability_percent": [80],
            "rainfall_mm": [25.0],
            "weather_codes": [61],
            "source": "Open-Meteo",
        }
        mock_agent = MagicMock()
        mock_agent.side_effect = Exception("503 Service Unavailable")
        mock_get_agent.return_value = mock_agent

        payload = {
            "message": "Will it rain?",
            "location": {
                "name": "Nagpur",
                "region": "Maharashtra",
                "country": "India",
                "latitude": 21.14,
                "longitude": 79.08,
            },
        }
        response = client.post("/api/chat", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["fallback_used"] is True
        assert data["weather_included"] is True
        assert "Nagpur" in data["response"]
        assert "80%" in data["response"]

    def test_chat_missing_message(self):
        """Empty message returns 422 error."""
        response = client.post("/api/chat", json={"message": ""})
        assert response.status_code == 422
