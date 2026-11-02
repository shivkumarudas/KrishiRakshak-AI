import requests
from strands import tool


def fetch_weather(latitude: float, longitude: float) -> dict:
    """Fetch a three-day weather forecast using coordinates."""

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
        response.raise_for_status()

        data = response.json()
        if not isinstance(data, dict) or "daily" not in data or not isinstance(data["daily"], dict):
            return {"error": "Invalid response format: 'daily' forecast data missing from Open-Meteo."}

        daily = data["daily"]
        dates = daily.get("time")

        if not isinstance(dates, list) or len(dates) == 0:
            return {"error": "Incomplete weather information: forecast dates missing."}

        return {
            "dates": dates,
            "rain_probability_percent": daily.get("precipitation_probability_max", []),
            "rainfall_mm": daily.get("precipitation_sum", []),
            "weather_codes": daily.get("weather_code", []),
            "source": "Open-Meteo",
        }

    except (requests.RequestException, KeyError, ValueError) as error:
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
        response.raise_for_status()

        results = response.json().get("results", [])

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

    except (requests.RequestException, KeyError, ValueError) as error:
        return {"error": f"Unable to retrieve weather data: {error}"}
