from strands import tool


@tool
def get_weather_based_advice(
    rain_probability: int | float | None = None,
    rainfall_mm: float | int | None = None,
    weather_code: int | None = -1,
) -> dict:
    """
    Provide general farming guidance based on weather forecast values.
    This tool does not diagnose crop diseases or prescribe chemical treatments.

    Args:
        rain_probability: Maximum forecast probability of rain (0 to 100), or None if unavailable.
        rainfall_mm: Expected precipitation sum in millimeters (>= 0), or None if unavailable.
        weather_code: WMO meteorological weather code, or -1 if unavailable.

    Returns:
        Structured general weather guidance with safety disclaimers.
    """

    advice = []
    risks = []

    # 1. Evaluate rain probability safely
    if rain_probability is not None:
        try:
            prob = float(rain_probability)
            if prob >= 70:
                risks.append("High forecast probability of rain")
                advice.append(
                    "Check the latest local forecast before spraying or "
                    "planning field operations."
                )
            elif prob >= 30:
                risks.append("Some possibility of rain")
                advice.append(
                    "Monitor updated forecasts before deciding when to work "
                    "in the field."
                )
            else:
                risks.append("Low forecast probability of rain")
                advice.append(
                    "Check soil moisture and crop needs before deciding "
                    "whether irrigation is necessary."
                )
        except (ValueError, TypeError):
            risks.append("Rain probability data invalid")
    else:
        risks.append("Rain probability data unavailable")
        advice.append("Check an updated local forecast for rain probability.")

    # 2. Evaluate expected rainfall safely
    if rainfall_mm is not None:
        try:
            rain = float(rainfall_mm)
            if rain >= 20:
                risks.append("Forecast rainfall of 20 mm or more")
                advice.append(
                    "Check field drainage and watch for waterlogging in "
                    "low-lying areas."
                )
            elif rain > 0:
                advice.append(
                    "Consider the expected rainfall when planning irrigation "
                    "and field operations."
                )
        except (ValueError, TypeError):
            pass

    # 3. Evaluate meteorological weather codes safely
    try:
        code = int(weather_code) if weather_code is not None else -1
        if code in (45, 48):
            risks.append("Foggy conditions forecast")
            advice.append(
                "Monitor crop conditions and local agricultural guidance."
            )
    except (ValueError, TypeError):
        code = -1

    return {
        "type": "general_weather_based_guidance",
        "risks": risks,
        "advice": advice,
        "weather_code": code,
        "disclaimer": (
            "This is general weather-based guidance, not a verified "
            "crop-specific recommendation. Forecasts can change. "
            "It does not diagnose pests or diseases or recommend "
            "pesticide or fertilizer doses."
        ),
    }
