from typing import Union, Optional, List
from strands import tool


SUPPORTED_CROPS = {
    "soybean": "Soybean",
    "cotton": "Cotton",
}

# Standardized plant parts matching agricultural scouting protocols
VALID_PLANT_PARTS = {
    "older leaves": "Older leaves",
    "newer leaves": "Newer leaves",
    "leaves": "Leaves",
    "stems": "Stems",
    "roots": "Roots",
    "flowers": "Flowers",
    "pods or fruit": "Pods or fruit",
    "pods": "Pods or fruit",
    "bolls": "Pods or fruit",
    "fruit": "Pods or fruit",
    "whole plant": "Whole plant",
    "unknown": "Unknown",
}

# Standardized visible symptoms
VALID_SYMPTOMS = {
    "yellowing": "Yellowing",
    "wilting": "Wilting",
    "spots": "Spots",
    "holes": "Holes",
    "discoloration": "Discoloration",
    "rot": "Rot",
    "stunted growth": "Stunted growth",
    "other": "Other",
}

# Standardized symptom duration
VALID_DURATIONS = {
    "started today": "Started today",
    "today": "Started today",
    "a few days ago": "A few days ago",
    "few days": "A few days ago",
    "more than a week ago": "More than a week ago",
    "week": "More than a week ago",
    "unknown": "Unknown",
}

# Standardized field distribution patterns
VALID_FIELD_PATTERNS = {
    "whole field": "Whole field",
    "isolated patches": "Isolated patches",
    "patches": "Isolated patches",
    "field edges": "Field edges",
    "edges": "Field edges",
    "individual plants": "Individual plants",
    "unknown": "Unknown",
}

# Standardized soil moisture conditions
VALID_SOIL_MOISTURE = {
    "dry": "Dry",
    "normal": "Normal",
    "moist": "Normal",
    "waterlogged": "Waterlogged",
    "unknown": "Unknown",
}


def _determine_possible_explanations(
    crop_name: str,
    stage: str,
    symptoms_text: str,
    symptoms_list: list[str],
    part: str,
    pattern: str,
    moisture: str,
    rainfall_info: str,
) -> list[str]:
    """
    Generate evidence-based possible explanations for discussion with an
    agricultural extension officer or KVK specialist.

    SAFETY RULES:
    1. NEVER declare a confirmed diagnosis based on symptoms alone.
    2. NEVER generate confidence scores or probability percentages.
    3. Clearly state multiple possible causes (especially for non-specific
       symptoms like yellowing leaves).
    4. Only return explanations when observations provide sufficient context.
    """
    explanations: list[str] = []
    text_lower = f"{symptoms_text} {' '.join(symptoms_list)}".lower()
    part_lower = part.lower()
    pattern_lower = pattern.lower()
    moisture_lower = moisture.lower()
    rain_lower = rainfall_info.lower() if rainfall_info else ""

    # Check if evidence is too vague or minimal
    is_vague = (
        part_lower == "unknown"
        and pattern_lower == "unknown"
        and moisture_lower == "unknown"
    )
    if is_vague:
        return []

    # -------------------------------------------------------------
    # 1. SOYBEAN EVIDENCE ASSESSMENT
    # -------------------------------------------------------------
    if crop_name == "Soybean":
        # Yellowing symptom analysis (explicitly handling multiple causes)
        if "yellow" in text_lower or "discoloration" in text_lower:
            if "older leaves" in part_lower or "leaves" in part_lower:
                if moisture_lower == "waterlogged" or "heavy rain" in rain_lower:
                    explanations.append(
                        "Waterlogging stress / root oxygen deprivation (Possible abiotic factor): "
                        "Excess soil moisture impairs root respiration and nodule function, "
                        "frequently resulting in lower leaf chlorosis; not a confirmed diagnosis."
                    )
                if pattern_lower in ("whole field", "isolated patches"):
                    explanations.append(
                        "Nitrogen or mobile nutrient deficiency (Possible nutritional factor): "
                        "When nitrogen is deficient, plants translocate mobile nutrients from older "
                        "leaves to new growth, causing uniform lower leaf yellowing."
                    )

            if "newer leaves" in part_lower:
                explanations.append(
                    "Micronutrient deficiency or Yellow Mosaic (Possible abiotic/viral factor): "
                    "Chlorosis starting on upper or newer trifoliate leaves often reflects immobile "
                    "nutrient limitation (e.g. iron or sulfur in calcareous soils) or early viral symptoms "
                    "vectored by whitefly. Requires inspection for interveinal patterns or mosaic mottling."
                )

            if "spots" in text_lower:
                explanations.append(
                    "Foliar fungal leaf spot (Possible biotic factor): "
                    "Spots with yellow halos on soybean leaves can be caused by fungal pathogens "
                    "(such as Cercospora or Septoria brown spot). Microscopic or field verification is required."
                )

        # Wilting symptom analysis
        if "wilt" in text_lower:
            if moisture_lower == "dry":
                explanations.append(
                    "Moisture stress / temporary wilting (Possible abiotic factor): "
                    "In dry soil conditions, daytime leaf drooping is common under high heat or low root moisture."
                )
            elif moisture_lower == "waterlogged" or "root" in part_lower:
                explanations.append(
                    "Root rot or collar rot complex (Possible fungal factor): "
                    "Wilting under wet or poorly drained soils often indicates root/stem base pathogen damage "
                    "(e.g. Rhizoctonia, Sclerotium, or Phytophthora). Requires inspecting the root collar."
                )

        # Chewed foliage / Holes
        if "hole" in text_lower or "chew" in text_lower:
            explanations.append(
                "Defoliator feeding activity (Possible insect pest): "
                "Irregular holes in soybean foliage typically point to lepidopteran larvae "
                "(such as semilooper or Spodoptera) or beetles. Check the undersides of leaves and soil surface."
            )

        # Stem symptoms
        if "stem" in part_lower or "girdle" in text_lower:
            explanations.append(
                "Stem borer or Girdle beetle activity (Possible insect pest): "
                "Ring cuts on stems or petiole wilting are characteristic of girdle beetle (Obereopsis brevis) "
                "or stem fly in Central India. Inspect stems for entry holes or swelling."
            )

    # -------------------------------------------------------------
    # 2. COTTON EVIDENCE ASSESSMENT
    # -------------------------------------------------------------
    elif crop_name == "Cotton":
        # Yellowing / Discoloration
        if "yellow" in text_lower or "discoloration" in text_lower:
            if "older leaves" in part_lower:
                explanations.append(
                    "Nutrient depletion or red leaf complex (Possible nutritional/physiological factor): "
                    "Reddening or yellowing on older lower leaves during boll development often relates to "
                    "magnesium or nitrogen translocations, or sudden temperature drops in black soils."
                )
            if "newer leaves" in part_lower or pattern_lower == "isolated patches":
                explanations.append(
                    "Sucking pest injury (Possible pest factor): "
                    "Curling, yellow margins, or hopper burn on upper leaves are frequently associated with "
                    "jassids (leafhoppers), aphids, or whiteflies. Inspect the undersides of young leaves."
                )
            if moisture_lower == "waterlogged" or "heavy rain" in rain_lower:
                explanations.append(
                    "Parawilt / root suffocation (Possible abiotic factor): "
                    "Cotton in heavy Vertisol soils is sensitive to saturated root zones following rain, "
                    "often displaying sudden leaf chlorosis or drooping."
                )

        # Wilting
        if "wilt" in text_lower:
            if moisture_lower == "dry":
                explanations.append(
                    "Soil moisture deficit (Possible abiotic factor): "
                    "Temporary mid-day wilting occurs when soil moisture drops below square/boll filling requirements."
                )
            else:
                explanations.append(
                    "Vascular wilt or root rot complex (Possible fungal/bacterial factor): "
                    "Wilting in moist or normal soil can indicate vascular infection (Fusarium or Verticillium) "
                    "or root rot. Requires splitting the lower stem to check for vascular browning."
                )

        # Pods / Bolls / Fruit damage
        if "boll" in part_lower or "pod" in part_lower or "fruit" in part_lower or "flower" in part_lower or "hole" in text_lower:
            explanations.append(
                "Bollworm complex damage (Possible insect pest): "
                "Holes in green bolls, flared squares, or flower damage in Maharashtra cotton commonly "
                "relate to bollworm feeding (such as Pink bollworm or American bollworm). Inspect internal bolls for larvae or frass."
            )

    return explanations


@tool
def assess_crop_symptoms(
    crop: str,
    growth_stage: str,
    symptoms: Union[str, list[str]],
    field_pattern: str = "unknown",
    affected_part: Union[str, list[str]] = "unknown",
    affected_plant_parts: Optional[Union[str, list[str]]] = None,
    symptom_duration: str = "unknown",
    soil_moisture: str = "unknown",
    recent_rainfall: str = "",
    recent_rainfall_or_irrigation: Optional[str] = None,
    farmer_notes: str = "",
    notes: Optional[str] = None,
) -> dict:
    """
    Organize farmer-reported crop symptoms and provide cautious next steps
    without diagnosing disease or prescribing chemical treatments.

    Collects structured observations across:
    1. Crop name (Soybean or Cotton)
    2. Growth stage
    3. Affected plant part(s)
    4. Visible symptoms
    5. Symptom duration
    6. Field distribution pattern
    7. Soil moisture
    8. Recent rainfall or irrigation
    9. Farmer notes

    Args:
        crop: Crop name ('soybean' or 'cotton').
        growth_stage: Current crop growth stage.
        symptoms: Reported visible symptoms (string or list of strings).
        field_pattern: Where affected plants are located in the field.
        affected_part: Which plant part is affected (legacy singular parameter).
        affected_plant_parts: Plant parts affected (list or string).
        symptom_duration: How long symptoms have been visible.
        soil_moisture: Soil moisture condition ('dry', 'normal', 'waterlogged', 'unknown').
        recent_rainfall: Recent rainfall or irrigation info (legacy parameter).
        recent_rainfall_or_irrigation: Recent rainfall or irrigation details.
        farmer_notes: Optional additional context or notes from the farmer.
        notes: Alias for farmer_notes.

    Returns:
        Structured assessment with observations, possible explanations,
        missing information, and cautious non-chemical recommended steps.
    """

    # -------------------------------------------------------------
    # 1. Validate Crop
    # -------------------------------------------------------------
    if not crop or not isinstance(crop, str) or not crop.strip():
        return {
            "status": "unsupported_crop",
            "supported_crops": list(SUPPORTED_CROPS.values()),
            "message": (
                "Currently, symptom assessment supports soybean "
                "and cotton only."
            ),
        }

    crop_key = crop.strip().lower()
    if crop_key not in SUPPORTED_CROPS:
        return {
            "status": "unsupported_crop",
            "supported_crops": list(SUPPORTED_CROPS.values()),
            "message": (
                "Currently, symptom assessment supports soybean "
                "and cotton only."
            ),
        }

    canonical_crop = SUPPORTED_CROPS[crop_key]

    # -------------------------------------------------------------
    # 2. Validate Growth Stage
    # -------------------------------------------------------------
    if not growth_stage or not isinstance(growth_stage, str) or not growth_stage.strip():
        return {
            "status": "missing_growth_stage",
            "message": "Please provide the crop's growth stage.",
        }

    stage_clean = growth_stage.strip()

    # -------------------------------------------------------------
    # 3. Validate Symptoms
    # -------------------------------------------------------------
    if symptoms is None:
        return {
            "status": "missing_symptoms",
            "message": "Please describe the symptoms you can observe.",
        }

    symptoms_list: list[str] = []
    if isinstance(symptoms, list):
        for s in symptoms:
            if isinstance(s, str) and s.strip():
                symptoms_list.append(s.strip())
        symptoms_str = ", ".join(symptoms_list)
    elif isinstance(symptoms, str):
        symptoms_str = symptoms.strip()
        if symptoms_str:
            symptoms_list = [s.strip() for s in symptoms_str.split(",") if s.strip()]
    else:
        return {
            "status": "missing_symptoms",
            "message": "Please describe the symptoms you can observe.",
        }

    if not symptoms_str:
        return {
            "status": "missing_symptoms",
            "message": "Please describe the symptoms you can observe.",
        }

    # -------------------------------------------------------------
    # 4. Normalize Affected Plant Parts
    # -------------------------------------------------------------
    # Resolve precedence between affected_plant_parts and affected_part
    raw_parts = affected_plant_parts if affected_plant_parts is not None else affected_part
    parts_list: list[str] = []

    if isinstance(raw_parts, list):
        for p in raw_parts:
            if isinstance(p, str):
                p_clean = p.strip().lower()
                canonical_part = VALID_PLANT_PARTS.get(p_clean)
                if canonical_part and canonical_part != "Unknown":
                    parts_list.append(p_clean)
    elif isinstance(raw_parts, str):
        p_clean = raw_parts.strip().lower()
        if p_clean in VALID_PLANT_PARTS and VALID_PLANT_PARTS[p_clean] != "Unknown":
            parts_list.append(p_clean)

    if not parts_list:
        parts_list = ["unknown"]

    # Primary singular part for backward compatibility
    primary_part = parts_list[0] if parts_list else "unknown"

    # -------------------------------------------------------------
    # 5. Normalize Field Pattern
    # -------------------------------------------------------------
    pattern_raw = str(field_pattern).strip().lower() if field_pattern is not None else "unknown"
    pattern = VALID_FIELD_PATTERNS.get(pattern_raw, "unknown")
    if pattern != "unknown":
        pattern = pattern_raw if pattern_raw in ("whole field", "patches", "isolated patches", "field edges", "individual plants") else pattern.lower()
        # map "patches" uniformly for field_pattern while preserving backward tests
        if pattern == "isolated patches":
            pattern = "patches" if pattern_raw == "patches" else "isolated patches"
    else:
        pattern = "unknown"

    # -------------------------------------------------------------
    # 6. Normalize Soil Moisture
    # -------------------------------------------------------------
    moisture_raw = str(soil_moisture).strip().lower() if soil_moisture is not None else "unknown"
    if moisture_raw in VALID_SOIL_MOISTURE:
        moisture = moisture_raw
    else:
        moisture = "unknown"

    # -------------------------------------------------------------
    # 7. Normalize Symptom Duration
    # -------------------------------------------------------------
    duration_raw = str(symptom_duration).strip() if symptom_duration is not None else ""
    duration_clean: Optional[str] = None
    if duration_raw:
        dur_lower = duration_raw.lower()
        if dur_lower in ("unknown", "none", ""):
            duration_clean = None
        elif dur_lower in VALID_DURATIONS:
            duration_clean = VALID_DURATIONS[dur_lower]
        else:
            duration_clean = duration_raw

    # -------------------------------------------------------------
    # 8. Normalize Recent Rainfall / Irrigation
    # -------------------------------------------------------------
    raw_rainfall = recent_rainfall_or_irrigation if recent_rainfall_or_irrigation is not None else recent_rainfall
    rainfall_str = str(raw_rainfall).strip() if raw_rainfall is not None else ""
    rainfall_clean: Optional[str] = rainfall_str if rainfall_str else None

    # -------------------------------------------------------------
    # 9. Normalize Notes
    # -------------------------------------------------------------
    raw_notes = farmer_notes if farmer_notes else (notes if notes else "")
    notes_clean: Optional[str] = str(raw_notes).strip() if raw_notes else None

    # -------------------------------------------------------------
    # 10. Compile Structured Observations
    # -------------------------------------------------------------
    observations = {
        "crop": canonical_crop,
        "growth_stage": stage_clean,
        "affected_plant_parts": parts_list,
        "reported_symptoms": symptoms_list if len(symptoms_list) > 1 else symptoms_str,
        "symptom_duration": duration_clean,
        "field_distribution": pattern,
        "soil_moisture": moisture,
        "recent_rainfall_or_irrigation": rainfall_clean,
        "farmer_notes": notes_clean,
    }

    # -------------------------------------------------------------
    # 11. Missing Information & Follow-Up Questions
    # -------------------------------------------------------------
    missing_info = []

    if primary_part == "unknown":
        missing_info.append(
            "Which part of the plant is affected? "
            "(older leaves, newer leaves, stems, roots, flowers, pods/bolls, or whole plant)"
        )

    if not duration_clean:
        missing_info.append(
            "How long have you seen these symptoms? "
            "(started today, a few days ago, more than a week ago)"
        )

    if moisture == "unknown":
        missing_info.append(
            "What is the current soil moisture condition? "
            "(dry, normal, or waterlogged)"
        )

    if not rainfall_clean:
        missing_info.append(
            "Has there been recent rainfall or irrigation? "
            "If yes, approximately how much and when?"
        )

    # -------------------------------------------------------------
    # 12. Determine Possible Explanations (Strict Non-Diagnosis)
    # -------------------------------------------------------------
    possible_explanations = _determine_possible_explanations(
        crop_name=canonical_crop,
        stage=stage_clean,
        symptoms_text=symptoms_str,
        symptoms_list=symptoms_list,
        part=primary_part,
        pattern=pattern,
        moisture=moisture,
        rainfall_info=rainfall_clean or "",
    )

    # -------------------------------------------------------------
    # 13. Recommended Next Steps (Actionable & Non-Chemical)
    # -------------------------------------------------------------
    next_steps = []

    if primary_part == "unknown":
        next_steps.append(
            "Check whether symptoms occur on older leaves, newer leaves, "
            "stems, roots, flowers, or pods/bolls."
        )
    elif "leaves" in primary_part:
        next_steps.append(
            "Examine the undersides of affected leaves with a hand lens "
            "for sap-sucking pests, mites, webbings, or fungal pustules."
        )

    if pattern == "unknown":
        next_steps.append(
            "Walk across the field in a zig-zag pattern to inspect whether "
            "symptoms occur uniformly or in localized low-lying patches."
        )

    if moisture == "unknown" or moisture == "waterlogged":
        next_steps.append(
            "Check field drainage channels to ensure excess water can drain "
            "freely away from root zones."
        )

    next_steps.append(
        "Photograph healthy vs affected plants and record the date "
        "when symptoms were first observed."
    )
    next_steps.append(
        "Take a sample plant to your nearest Krishi Vigyan Kendra (KVK) "
        "or consult a Taluka Agricultural Officer for an in-person assessment."
    )

    # -------------------------------------------------------------
    # 14. User-Facing Message & Status
    # -------------------------------------------------------------
    if missing_info:
        message = (
            "The symptoms have been recorded. Some observations are "
            "missing, which are listed below. Providing this information "
            "can help an agricultural officer assess the problem better."
        )
    else:
        message = (
            "The symptoms have been recorded with detailed observations. "
            "However, the cause cannot be reliably determined from this "
            "information alone. A field visit by an agricultural officer "
            "is recommended for accurate diagnosis."
        )

    return {
        "status": "assessment_recorded",
        "crop": canonical_crop,
        "growth_stage": stage_clean,
        "affected_plant_parts": parts_list,
        "affected_part": primary_part,
        "reported_symptoms": symptoms_str,
        "symptom_duration": duration_clean,
        "field_pattern": pattern,
        "soil_moisture": moisture,
        "recent_rainfall_or_irrigation": rainfall_clean,
        "recent_rainfall": rainfall_clean,
        "observations": observations,
        "possible_explanations": possible_explanations,
        "missing_information": missing_info if missing_info else None,
        "recommended_next_steps": next_steps,
        "chemical_recommendations": [],
        "safety_note": (
            "No pesticide, herbicide, or fertilizer dose is recommended. "
            "Do not select or spray a chemical treatment based on symptoms alone. "
            "Common symptoms like leaf yellowing or wilting have multiple distinct causes "
            "(water stress, nutrient deficiency, or root rot) that require field verification."
        ),
        "diagnosis": None,
        "message": message,
    }
