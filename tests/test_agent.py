"""Tests for app/agent.py — import safety, display_weather_summary, and offline/fallback modes."""

import os
from unittest.mock import patch, MagicMock

from app.agent import (
    display_weather_summary,
    _create_agent,
    run_crop_assessment,
    main,
)


class TestAgentImportSafety:
    """Verify that importing app.agent does not crash without an API key."""

    def test_module_imports_without_api_key(self):
        """The module can be imported even if GOOGLE_API_KEY is unset."""
        # If we got here, the import at the top of this file succeeded.
        assert True

    @patch.dict(os.environ, {}, clear=True)
    def test_create_agent_fails_without_key(self):
        """_create_agent raises ValueError when no API key is set."""
        try:
            _create_agent()
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "GOOGLE_API_KEY" in str(e)


class TestDisplayWeatherSummary:
    """Tests for the display_weather_summary function."""

    def test_complete_forecast(self, capsys):
        """A complete forecast prints dates, probabilities, and rainfall."""
        forecast = {
            "dates": ["2026-10-26", "2026-10-27"],
            "rain_probability_percent": [80, 20],
            "rainfall_mm": [25.0, 0.0],
            "weather_codes": [61, 0],
            "source": "Open-Meteo",
        }
        location = {
            "name": "Pune",
            "region": "Maharashtra",
            "country": "India",
        }

        display_weather_summary(forecast, location)
        output = capsys.readouterr().out

        assert "Pune" in output
        assert "2026-10-26" in output
        assert "80" in output
        assert "25.0" in output

    def test_empty_dates(self, capsys):
        """An empty dates list prints a 'no dates' message."""
        forecast = {
            "dates": [],
            "rain_probability_percent": [],
            "rainfall_mm": [],
            "weather_codes": [],
        }
        location = {"name": "Test"}

        display_weather_summary(forecast, location)
        output = capsys.readouterr().out

        assert "No forecast dates" in output

    def test_missing_values(self, capsys):
        """Missing probability or rainfall shows 'Unavailable'."""
        forecast = {
            "dates": ["2026-10-26"],
            "rain_probability_percent": [],
            "rainfall_mm": [],
            "weather_codes": [],
        }
        location = {"name": "Nagpur"}

        display_weather_summary(forecast, location)
        output = capsys.readouterr().out

        assert "Unavailable" in output

    def test_disclaimer_always_shown(self, capsys):
        """The disclaimer about forecasts changing is always displayed."""
        forecast = {
            "dates": ["2026-10-26"],
            "rain_probability_percent": [50],
            "rainfall_mm": [10.0],
            "weather_codes": [3],
        }
        location = {"name": "Latur"}

        display_weather_summary(forecast, location)
        output = capsys.readouterr().out

        assert "Forecasts can change" in output
        assert "Krishi Vigyan Kendra" in output


class TestOfflineAndFallbackModes:
    """Tests for offline CLI commands and Gemini error fallback handling."""

    @patch("builtins.input")
    def test_run_crop_assessment_offline(self, mock_input, capsys):
        """Crop assessment runs completely offline without calling Gemini."""
        mock_input.side_effect = [
            "soybean",            # crop
            "flowering",          # stage
            "1",                  # part (1 = older leaves)
            "1",                  # symptoms (1 = yellowing)
            "2",                  # duration (2 = a few days ago)
            "2",                  # pattern (2 = isolated patches)
            "2",                  # moisture (2 = normal)
            "none",               # rainfall
            "notes from farmer",  # farmer notes
        ]

        run_crop_assessment()
        output = capsys.readouterr().out

        assert "Crop Assessment" in output
        assert "Soybean" in output
        assert "flowering" in output
        assert "No chemical recommendations provided." in output
        assert "safety" in output.lower() or "diagnosis" in output.lower()

    @patch("app.agent._create_agent", side_effect=ValueError("No key"))
    @patch("builtins.input")
    def test_main_weather_command_without_gemini(self, mock_input, mock_create_agent, capsys):
        """Weather command in main() works when GOOGLE_API_KEY is not set."""
        mock_input.side_effect = [
            "weather",  # question
            "Pune",     # location input
            "1",        # select location #1
            "y",        # confirm location
            "exit",     # quit
        ]

        with patch("app.agent.fetch_weather") as mock_fetch, \
             patch("app.agent.requests.get") as mock_get:
            # Mock geocoding
            mock_geo = MagicMock()
            mock_geo.json.return_value = {
                "results": [{"name": "Pune", "admin1": "Maharashtra", "country": "India", "latitude": 18.52, "longitude": 73.86}]
            }
            mock_geo.raise_for_status = MagicMock()
            mock_get.return_value = mock_geo

            # Mock weather fetch
            mock_fetch.return_value = {
                "dates": ["2026-10-26"],
                "rain_probability_percent": [40],
                "rainfall_mm": [2.0],
                "weather_codes": [3],
                "source": "Open-Meteo",
            }

            main()
            output = capsys.readouterr().out

            assert "WEATHER SUMMARY" in output
            assert "Pune" in output
            assert "Thank you for using KrishiRakshak AI" in output

    @patch("app.agent._create_agent")
    @patch("builtins.input")
    def test_main_gemini_quota_error_fallback(self, mock_input, mock_create_agent, capsys):
        """When Gemini returns a 429 quota error, fallback displays weather summary."""
        mock_agent = MagicMock()
        mock_agent.side_effect = Exception("ResourceExhausted: 429 Quota exceeded for model gemini-3.8-flash")
        mock_create_agent.return_value = mock_agent

        mock_input.side_effect = [
            "Should I irrigate today?",  # question
            "Pune",                      # location
            "1",                         # select location #1
            "y",                         # confirm
            "exit",                      # quit
        ]

        with patch("app.agent.fetch_weather") as mock_fetch, \
             patch("app.agent.requests.get") as mock_get:
            mock_geo = MagicMock()
            mock_geo.json.return_value = {
                "results": [{"name": "Pune", "admin1": "Maharashtra", "country": "India", "latitude": 18.52, "longitude": 73.86}]
            }
            mock_geo.raise_for_status = MagicMock()
            mock_get.return_value = mock_geo

            mock_fetch.return_value = {
                "dates": ["2026-10-26"],
                "rain_probability_percent": [80],
                "rainfall_mm": [25.0],
                "weather_codes": [61],
                "source": "Open-Meteo",
            }

            main()
            output = capsys.readouterr().out

            assert "quota or rate limit reached" in output
            assert "WEATHER SUMMARY" in output

    @patch("app.agent._create_agent")
    @patch("builtins.input")
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "AIzaSySecretApiKey123456789"})
    def test_main_gemini_error_redacts_api_key(self, mock_input, mock_create_agent, capsys):
        """Errors do not leak GOOGLE_API_KEY if present in exception text."""
        secret_key = "AIzaSySecretApiKey123456789"
        mock_agent = MagicMock()
        mock_agent.side_effect = Exception(f"HTTP 500 error contacting service at key={secret_key}")
        mock_create_agent.return_value = mock_agent

        mock_input.side_effect = [
            "What should I do?",  # question
            "Pune",               # location
            "1",                  # select location #1
            "y",                  # confirm
            "exit",               # quit
        ]

        with patch("app.agent.fetch_weather") as mock_fetch, \
             patch("app.agent.requests.get") as mock_get:
            mock_geo = MagicMock()
            mock_geo.json.return_value = {
                "results": [{"name": "Pune", "admin1": "Maharashtra", "country": "India", "latitude": 18.52, "longitude": 73.86}]
            }
            mock_geo.raise_for_status = MagicMock()
            mock_get.return_value = mock_geo

            mock_fetch.return_value = {
                "dates": ["2026-10-26"],
                "rain_probability_percent": [10],
                "rainfall_mm": [0.0],
                "weather_codes": [0],
                "source": "Open-Meteo",
            }

            main()
            output = capsys.readouterr().out

            assert secret_key not in output
            assert "WEATHER SUMMARY" in output
