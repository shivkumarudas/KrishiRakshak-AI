"""Pydantic models for API requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, Union


# --------------------------------------------------
# Location models
# --------------------------------------------------

class LocationResult(BaseModel):
    """A single geocoding result."""

    name: str
    region: Optional[str] = None
    country: Optional[str] = None
    latitude: float
    longitude: float


class LocationSearchResponse(BaseModel):
    """Response from the location search endpoint."""

    query: str
    results: list[LocationResult]


# --------------------------------------------------
# Weather models
# --------------------------------------------------

class DayGuidance(BaseModel):
    """Rule-based weather guidance for a single day."""

    date: str
    rain_probability_percent: Optional[int] = None
    rainfall_mm: Optional[float] = None
    weather_code: int = -1
    risks: list[str] = []
    advice: list[str] = []


class WeatherResponse(BaseModel):
    """Response from the weather forecast endpoint."""

    location_name: str
    latitude: float
    longitude: float
    source: str = "Open-Meteo"
    dates: list[str]
    rain_probability_percent: list[Optional[int]]
    rainfall_mm: list[Optional[float]]
    weather_codes: list[int]
    daily_guidance: list[DayGuidance] = []
    disclaimer: str = (
        "Forecasts can change. This is general weather-based "
        "guidance, not a verified crop-specific recommendation."
    )


# --------------------------------------------------
# Crop assessment models
# --------------------------------------------------

class CropAssessRequest(BaseModel):
    """Request body for the crop symptom assessment endpoint."""

    crop: str = Field(..., min_length=1, description="Crop name (soybean or cotton)")
    growth_stage: str = Field(..., min_length=1, description="Current growth stage")
    symptoms: Union[str, list[str]] = Field(..., description="Visible symptoms")
    field_pattern: str = Field(default="unknown", description="Where affected plants are located")
    affected_part: str = Field(default="unknown", description="Which plant part is affected")
    affected_plant_parts: Optional[Union[str, list[str]]] = Field(default=None, description="Plant parts affected")
    symptom_duration: str = Field(default="", description="How long symptoms have been visible")
    soil_moisture: str = Field(default="unknown", description="Current soil moisture condition")
    recent_rainfall: str = Field(default="", description="Recent rainfall or irrigation info")
    recent_rainfall_or_irrigation: Optional[str] = Field(default=None, description="Recent rainfall or irrigation info")
    farmer_notes: Optional[str] = Field(default="", description="Optional context notes from the farmer")


# --------------------------------------------------
# Advisory models
# --------------------------------------------------

class AdvisoryFilterRequest(BaseModel):
    """Request body for the POST /api/advisories endpoint."""

    crop: str = Field(..., min_length=1, description="Crop name (soybean or cotton)")
    stage: Optional[str] = Field(default=None, description="Optional crop growth stage filter")
    region: Optional[str] = Field(default=None, description="Optional region filter")
    verification_status: Optional[str] = Field(default=None, description="Optional verification status filter")
    include_historical: bool = Field(default=True, description="Whether to include historical reference bulletins")
    check_sources: bool = Field(default=False, description="Whether to verify source URL reachability")


# --------------------------------------------------
# Chat models
# --------------------------------------------------

class ChatRequest(BaseModel):
    """Request body for the AI chat endpoint."""

    message: str = Field(..., min_length=1, description="The farmer's question or message")
    location: Optional[LocationResult] = Field(
        default=None,
        description="Optional confirmed location for weather context",
    )


class ChatResponse(BaseModel):
    """Response from the AI chat endpoint."""

    response: str
    weather_included: bool = False
    fallback_used: bool = False


# --------------------------------------------------
# Error model
# --------------------------------------------------

class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: Optional[str] = None
