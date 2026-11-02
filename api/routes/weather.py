"""Weather forecast and location search endpoints."""

from fastapi import APIRouter, HTTPException, Query

import requests as http_requests

from api.models import (
    LocationResult,
    LocationSearchResponse,
    WeatherResponse,
    DayGuidance,
)
from tools.weather_tool import fetch_weather
from tools.rule_based_advisory import get_weather_based_advice

router = APIRouter()


# --------------------------------------------------
# GET /api/locations/search
# --------------------------------------------------

@router.get("/locations/search", response_model=LocationSearchResponse)
async def search_locations(
    name: str = Query(
        default=None,
        description="Village, town, or district name to search for",
    ),
    q: str = Query(
        default=None,
        description="Location query string",
    ),
):
    """Search for a location using the Open-Meteo geocoding API."""

    search_query = q or name
    if not search_query or not search_query.strip():
        raise HTTPException(
            status_code=422,
            detail="Missing required query parameter 'q' or 'name'.",
        )

    clean_query = search_query.strip()

    try:
        response = http_requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={
                "name": clean_query,
                "count": 5,
                "language": "en",
                "format": "json",
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

    except http_requests.RequestException as error:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to search for locations: {error}",
        )

    raw_results = data.get("results", [])

    results = [
        LocationResult(
            name=place.get("name", "Unknown"),
            region=place.get("admin1"),
            country=place.get("country"),
            latitude=place["latitude"],
            longitude=place["longitude"],
        )
        for place in raw_results
    ]

    return LocationSearchResponse(query=clean_query, results=results)


# --------------------------------------------------
# GET /api/weather
# --------------------------------------------------

@router.get("/weather", response_model=WeatherResponse)
async def get_weather(
    latitude: float = Query(
        ..., ge=-90, le=90, description="Latitude of the location",
    ),
    longitude: float = Query(
        ..., ge=-180, le=180, description="Longitude of the location",
    ),
    location_name: str = Query(
        default="Unknown",
        description="Display name for the location",
    ),
):
    """Retrieve a three-day weather forecast with rule-based guidance."""

    forecast = fetch_weather(latitude, longitude)

    if "error" in forecast:
        raise HTTPException(
            status_code=502,
            detail=forecast["error"],
        )

    dates = forecast.get("dates", [])
    probabilities = forecast.get("rain_probability_percent", [])
    rainfall_values = forecast.get("rainfall_mm", [])
    weather_codes = forecast.get("weather_codes", [])

    # Generate daily rule-based guidance.
    daily_guidance = []

    for index, forecast_date in enumerate(dates):
        rain_prob = (
            probabilities[index] if index < len(probabilities) else None
        )
        rainfall = (
            rainfall_values[index] if index < len(rainfall_values) else None
        )
        weather_code = (
            weather_codes[index] if index < len(weather_codes) else -1
        )

        day = DayGuidance(
            date=forecast_date,
            rain_probability_percent=rain_prob,
            rainfall_mm=rainfall,
            weather_code=weather_code,
        )

        if rain_prob is not None and rainfall is not None:
            guidance = get_weather_based_advice(
                rain_probability=rain_prob,
                rainfall_mm=rainfall,
                weather_code=weather_code,
            )
            day.risks = guidance.get("risks", [])
            day.advice = guidance.get("advice", [])

        daily_guidance.append(day)

    return WeatherResponse(
        location_name=location_name,
        latitude=latitude,
        longitude=longitude,
        source=forecast.get("source", "Open-Meteo"),
        dates=dates,
        rain_probability_percent=probabilities,
        rainfall_mm=rainfall_values,
        weather_codes=weather_codes,
        daily_guidance=daily_guidance,
    )
