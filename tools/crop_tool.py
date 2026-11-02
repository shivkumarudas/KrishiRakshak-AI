from strands import tool


@tool
def get_crop_context(crop: str, growth_stage: str) -> dict:
    """
    Collect basic crop context to help prepare relevant farming advice.

    Args:
        crop: Crop name, such as soybean or cotton.
        growth_stage: Current crop stage, such as flowering,
            grain filling, boll development, or maturity.

    Returns:
        Crop context and information needed for a cautious advisory.
    """

    if not crop or not isinstance(crop, str) or not crop.strip():
        return {
            "error": "Currently supported crops are soybean and cotton."
        }

    supported_crops = {
        "soybean": "Soybean",
        "cotton": "Cotton",
    }

    crop_name = supported_crops.get(crop.strip().lower())

    if not crop_name:
        return {
            "error": "Currently supported crops are soybean and cotton."
        }

    if not growth_stage or not isinstance(growth_stage, str) or not growth_stage.strip():
        return {
            "error": "Please provide the current crop growth stage."
        }

    return {
        "crop": crop_name,
        "growth_stage": growth_stage.strip(),
        "next_step": (
            "Use the crop stage and confirmed location to identify "
            "relevant agricultural guidance from a trusted source. "
            "Do not invent treatment recommendations."
        ),
    }
