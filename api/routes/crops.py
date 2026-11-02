"""Crop assessment and image analysis endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from api.models import CropAssessRequest
from tools.crop_diagnosis import assess_crop_symptoms
from services.image_service import (
    analyze_crop_image_bytes,
    ImageValidationError,
)

router = APIRouter()


# --------------------------------------------------
# POST /api/crops/assess
# --------------------------------------------------

@router.post("/crops/assess")
async def assess_crop(request: CropAssessRequest):
    """Assess crop symptoms based on farmer observations."""

    result = assess_crop_symptoms(
        crop=request.crop,
        growth_stage=request.growth_stage,
        symptoms=request.symptoms,
        field_pattern=request.field_pattern,
        affected_part=request.affected_part,
        affected_plant_parts=request.affected_plant_parts,
        symptom_duration=request.symptom_duration,
        soil_moisture=request.soil_moisture,
        recent_rainfall=request.recent_rainfall,
        recent_rainfall_or_irrigation=request.recent_rainfall_or_irrigation,
        farmer_notes=request.farmer_notes or "",
    )

    # If the tool returned an error status, return 422.
    if result.get("status") in ("unsupported_crop", "missing_growth_stage", "missing_symptoms"):
        raise HTTPException(
            status_code=422,
            detail=result.get("message", "Invalid input."),
        )

    return result


# --------------------------------------------------
# POST /api/crops/analyze-image
# --------------------------------------------------

@router.post("/crops/analyze-image")
async def analyze_crop_image(
    image: UploadFile = File(..., description="Crop image to analyze"),
    crop: Optional[str] = Form(default=None, description="Crop name (soybean or cotton)"),
    growth_stage: Optional[str] = Form(default=None, description="Current growth stage"),
    notes: Optional[str] = Form(default=None, description="Optional farmer observations"),
):
    """
    Validate and analyze an uploaded crop photograph.
    Accepts JPEG, PNG, and WebP (up to 10 MB).
    Provides visual observations with uncertainty and avoids unverified diagnoses.
    """
    contents = await image.read()

    try:
        result = analyze_crop_image_bytes(
            image_bytes=contents,
            content_type=image.content_type,
            filename=image.filename or "crop_image.jpg",
            crop=crop,
            growth_stage=growth_stage,
            notes=notes,
        )
        return result

    except ImageValidationError as val_err:
        raise HTTPException(
            status_code=val_err.status_code,
            detail=val_err.message,
        )
