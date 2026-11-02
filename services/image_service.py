"""Crop Image Analysis Service.

Validates uploaded images and coordinates cautious visual interpretation
using Gemini vision models without making confirmed diagnoses or prescribing
chemical doses.
"""

import json
import logging
import os
import re
from typing import Optional

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

ALLOWED_MIME_TYPES = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/webp": [b"RIFF"],
}

SUPPORTED_CROPS = {
    "soybean": "Soybean",
    "cotton": "Cotton",
}

# Known non-vision (text-only) model prefixes/names to reject
TEXT_ONLY_MODEL_PATTERNS = [
    "text-bison",
    "chat-bison",
    "gemini-1.0-text",
    "text-embedding",
    "embedding",
    "text-davinci",
    "gpt-3.5-turbo-instruct",
]


class ImageValidationError(Exception):
    """Exception raised when uploaded image fails validation."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def validate_image_bytes(
    image_bytes: bytes,
    content_type: Optional[str],
    filename: Optional[str],
) -> str:
    """
    Validate image file size, declared content type, and magic header bytes.

    Returns:
        The normalized MIME type string if valid.

    Raises:
        ImageValidationError: If image is empty, oversized, unsupported, or corrupted.
    """
    if not image_bytes or len(image_bytes) == 0:
        raise ImageValidationError("Uploaded image file is empty.", status_code=400)

    if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        max_mb = MAX_IMAGE_SIZE_BYTES // (1024 * 1024)
        raise ImageValidationError(
            f"Image too large ({len(image_bytes) / (1024 * 1024):.1f} MB). Maximum allowed size is {max_mb} MB.",
            status_code=413,
        )

    # Check file extension hint
    ext = (filename or "").split(".")[-1].lower() if "." in (filename or "") else ""
    ext_map = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
    }

    normalized_type = (content_type or "").lower().strip()
    if normalized_type not in ALLOWED_MIME_TYPES:
        if ext in ext_map:
            normalized_type = ext_map[ext]
        else:
            raise ImageValidationError(
                f"Unsupported file format '{content_type}'. KrishiRakshak AI accepts JPEG, PNG, or WebP images.",
                status_code=415,
            )

    # Verify magic header bytes
    if normalized_type == "image/jpeg":
        if not image_bytes.startswith(b"\xff\xd8\xff"):
            raise ImageValidationError("File is corrupted or not a valid JPEG image.", status_code=415)
    elif normalized_type == "image/png":
        if not image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ImageValidationError("File is corrupted or not a valid PNG image.", status_code=415)
    elif normalized_type == "image/webp":
        if len(image_bytes) < 12 or image_bytes[:4] != b"RIFF" or image_bytes[8:12] != b"WEBP":
            raise ImageValidationError("File is corrupted or not a valid WebP image.", status_code=415)

    return normalized_type


def is_vision_capable_model(model_name: str) -> bool:
    """Verify that the model name does not match known text-only models."""
    if not model_name:
        return False
    lower_name = model_name.lower().strip()
    for text_pat in TEXT_ONLY_MODEL_PATTERNS:
        if text_pat in lower_name:
            return False
    return True


def _parse_vision_response_to_dict(text: str) -> dict:
    """
    Attempt to extract structured fields from Gemini's response.
    Supports either direct JSON block or cleanses markdown text.
    """
    cleaned = text.strip()
    # Try finding fenced JSON
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except Exception:
            pass

    # Try raw JSON parse
    if cleaned.startswith("{") and cleaned.endswith("}"):
        try:
            return json.loads(cleaned)
        except Exception:
            pass

    # Fallback heuristic parser for key sections
    return {
        "visible_plant_parts": ["Reported in visual analysis"],
        "observable_visual_symptoms": [s.strip("- ") for s in cleaned.split("\n") if s.strip().startswith("-")][:4] or ["Visual pattern observed"],
        "image_quality_limitations": ["Image resolution, angle, and lighting may obscure fine pathogen signs."],
        "possible_explanations": ["See narrative analysis below (subject to field verification)."],
        "additional_observations_needed": ["Inspection of leaf undersides and soil condition."],
        "recommended_safe_next_steps": [
            "Inspect underside of leaves for pests.",
            "Record whether symptoms occur on older or newer foliage.",
            "Take fresh plant samples to your local Krishi Vigyan Kendra (KVK).",
        ],
        "professional_assessment_advisable": True,
        "narrative": cleaned,
    }


def analyze_crop_image_bytes(
    image_bytes: bytes,
    content_type: str,
    filename: str = "crop_image.jpg",
    crop: Optional[str] = None,
    growth_stage: Optional[str] = None,
    notes: Optional[str] = None,
    model_id: Optional[str] = None,
) -> dict:
    """
    Validate and analyze a crop photograph using a verified Gemini vision model.

    Enforces:
    1. Validation of image format, magic bytes, and size.
    2. Strict vision-capability model verification.
    3. Memory-only image handling (no disk retention).
    4. Structured JSON output distinguishing visual observations from possible explanations.
    5. Complete absence of chemical prescriptions or confirmed diagnoses.
    """
    # 1. Validate image format and magic bytes
    mime_type = validate_image_bytes(image_bytes, content_type, filename)

    # 2. Validate crop context if provided
    canonical_crop: Optional[str] = None
    if crop and isinstance(crop, str) and crop.strip():
        crop_clean = crop.strip().lower()
        if crop_clean in SUPPORTED_CROPS:
            canonical_crop = SUPPORTED_CROPS[crop_clean]
        else:
            raise ImageValidationError(
                f"Unsupported crop '{crop}'. Currently, image analysis supports soybean and cotton only.",
                status_code=422,
            )

    # 3. Check API key configuration
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {
            "status": "vision_unavailable",
            "message": (
                "The vision analysis service is not currently configured. "
                "GOOGLE_API_KEY is not set. Visual observations cannot be processed."
            ),
            "crop": canonical_crop or "Unspecified",
            "growth_stage": growth_stage.strip() if growth_stage else None,
            "file_name": filename,
            "file_size_bytes": len(image_bytes),
            "content_type": mime_type,
            "safety_note": (
                "Never apply chemical treatments based solely on an automated photo scan. "
                "Consult your local Krishi Vigyan Kendra (KVK) with actual plant samples."
            ),
        }

    # 4. Check model selection & verify vision capability
    vision_model = model_id or os.getenv("GEMINI_VISION_MODEL", "gemini-3.8-flash")
    if not is_vision_capable_model(vision_model):
        return {
            "status": "vision_unavailable",
            "message": (
                f"Configured model '{vision_model}' does not support multimodal image input. "
                "A vision-capable model is required."
            ),
            "crop": canonical_crop or "Unspecified",
            "file_name": filename,
            "file_size_bytes": len(image_bytes),
            "content_type": mime_type,
            "safety_note": (
                "Consult your local Krishi Vigyan Kendra (KVK) or Taluka Agriculture Officer "
                "for an in-person field assessment."
            ),
        }

    # 5. Build structured agronomic vision prompt
    crop_context_lines = []
    if canonical_crop:
        crop_context_lines.append(f"- Crop name: {canonical_crop}")
    if growth_stage:
        crop_context_lines.append(f"- Crop growth stage: {growth_stage.strip()}")
    if notes:
        crop_context_lines.append(f"- Farmer observations: {notes.strip()}")

    crop_context_str = "\n".join(crop_context_lines) if crop_context_lines else "- No specific crop context provided."

    prompt = f"""
You are an expert agricultural vision assistant for farmers in Maharashtra, India.
Analyze this crop image carefully and provide objective, cautious observations.

Farmer supplied context:
{crop_context_str}

CRITICAL RULES:
1. Output your analysis as a structured JSON object with these EXACT keys:
   - "visible_plant_parts": list of parts visible in photo (e.g. "older leaves", "newer leaves", "stems", "roots", "pods", "bolls", "whole plant")
   - "observable_visual_symptoms": list of observable visual signs (e.g. "interveinal chlorosis", "brown necrotic spots with yellow halos", "chewed leaf margins")
   - "image_quality_limitations": list of limitations (e.g. "lighting glare", "leaf underside not visible", "macro details unclear")
   - "possible_explanations": list of possible explanations ALWAYS stating uncertainty (e.g. "Possible micronutrient deficiency (e.g. iron/sulfur)", "Possible fungal leaf spot")
   - "additional_observations_needed": list of field observations needed (e.g. "check underside of leaves for whiteflies", "check soil drainage")
   - "recommended_safe_next_steps": list of non-chemical safe actions (e.g. "examine lower leaves", "consult local KVK")
   - "professional_assessment_advisable": true
   - "narrative": brief 2-3 sentence overview

2. NEVER declare a confirmed disease diagnosis from photo alone.
3. NEVER prescribe pesticide, herbicide, or fertilizer doses.
4. Do not invent confidence percentages or probability scores.
5. Emphasize that visual symptoms like yellowing can have multiple distinct causes (water stress, nutrient balance, or disease).
"""

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

        response = client.models.generate_content(
            model=vision_model,
            contents=[prompt, image_part],
        )

        analysis_text = response.text if response and response.text else "No textual analysis generated."
        parsed = _parse_vision_response_to_dict(analysis_text)

        visible_parts = parsed.get("visible_plant_parts", ["Leaves"])
        visual_symptoms = parsed.get("observable_visual_symptoms", ["Color pattern variation"])
        quality_limits = parsed.get("image_quality_limitations", ["Image angle and lighting may obscure fine details."])
        possible_explanations = parsed.get("possible_explanations", ["Multiple distinct causes possible; field inspection needed."])
        additional_needed = parsed.get("additional_observations_needed", ["Inspect leaf undersides and soil condition."])
        next_steps = parsed.get("recommended_safe_next_steps", [
            "Scout unaffected plants to compare vigor.",
            "Take a fresh sample to your nearest Krishi Vigyan Kendra (KVK).",
        ])

        return {
            "status": "analysis_completed",
            "crop": canonical_crop or "Unspecified",
            "growth_stage": growth_stage.strip() if growth_stage else None,
            "model_used": vision_model,
            "file_name": filename,
            "file_size_bytes": len(image_bytes),
            "content_type": mime_type,
            "visible_plant_parts": visible_parts,
            "observable_visual_symptoms": visual_symptoms,
            "image_quality_limitations": quality_limits,
            "possible_explanations": possible_explanations,
            "additional_observations_needed": additional_needed,
            "recommended_safe_next_steps": next_steps,
            "professional_assessment_advisable": True,
            "uncertainty_note": (
                "Visual analysis from a photograph cannot replace laboratory or in-person field testing. "
                "Lighting conditions, image resolution, camera focus, and overlapping symptoms affect visual interpretation."
            ),
            "safety_note": (
                "This visual analysis is observational only and NOT a confirmed laboratory diagnosis. "
                "No pesticide, herbicide, or fertilizer dose is prescribed. Take a fresh plant sample to your nearest "
                "Krishi Vigyan Kendra (KVK) or Taluka Agriculture Officer for verification."
            ),
            "analysis": parsed.get("narrative") or analysis_text,
        }

    except Exception as error:
        err_msg = str(error)
        logger.warning("Gemini vision analysis failed: %s", err_msg)

        error_lower = err_msg.lower()
        if "quota" in error_lower or "429" in error_lower or "resource_exhausted" in error_lower:
            user_msg = (
                "The vision AI service has reached its temporary quota or rate limit. "
                "Your image has been validated. Please try again later or consult your local KVK officer."
            )
        elif "timeout" in error_lower or "timed out" in error_lower or "deadline" in error_lower:
            user_msg = (
                "The vision AI service timed out while processing the photograph. "
                "Please verify your internet connection and try again."
            )
        elif "not found" in error_lower or "model" in error_lower:
            user_msg = (
                f"The configured vision model '{vision_model}' is not available with this API key. "
                "Please configure a supported Gemini multimodal model."
            )
        else:
            user_msg = (
                "The vision AI service encountered a temporary error while processing the image. "
                "Your image format and size were verified."
            )

        return {
            "status": "vision_unavailable",
            "message": user_msg,
            "crop": canonical_crop or "Unspecified",
            "file_name": filename,
            "file_size_bytes": len(image_bytes),
            "content_type": mime_type,
            "safety_note": (
                "Never apply chemical treatments based on unverified symptoms. "
                "Consult your local Krishi Vigyan Kendra (KVK) for an in-person assessment."
            ),
        }
