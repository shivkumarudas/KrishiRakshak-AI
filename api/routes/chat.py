"""AI Agricultural Assistant chat endpoint."""

import json
import logging
import os
from fastapi import APIRouter
from api.models import ChatRequest, ChatResponse
from app.agent import _create_agent
from tools.weather_tool import fetch_weather
from tools.rule_based_advisory import get_weather_based_advice

router = APIRouter()
logger = logging.getLogger(__name__)

# Cache agent instance if created
_agent_instance = None


def get_agent():
    """Retrieve or initialize the Strands agent."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = _create_agent()
    return _agent_instance


def generate_offline_weather_text(forecast: dict, location_name: str) -> str:
    """Generate friendly text summary of weather and rule-based advice."""
    lines = [
        f"Weather for {location_name}:",
        "Source: Open-Meteo",
        "",
    ]
    dates = forecast.get("dates", [])
    probabilities = forecast.get("rain_probability_percent", [])
    rainfall_values = forecast.get("rainfall_mm", [])
    weather_codes = forecast.get("weather_codes", [])

    for i, date_str in enumerate(dates):
        prob = probabilities[i] if i < len(probabilities) else None
        rain = rainfall_values[i] if i < len(rainfall_values) else None
        w_code = weather_codes[i] if i < len(weather_codes) else -1

        prob_str = f"{prob}%" if prob is not None else "Unavailable"
        rain_str = f"{rain} mm" if rain is not None else "Unavailable"

        lines.append(f"Date: {date_str}")
        lines.append(f"• Rain Probability: {prob_str}")
        lines.append(f"• Expected Rainfall: {rain_str}")

        if prob is not None and rain is not None:
            advice = get_weather_based_advice(prob, rain, w_code)
            for item in advice.get("advice", []):
                lines.append(f"  - {item}")
        lines.append("")

    lines.append(
        "Important: Forecasts can change. This is general weather guidance, "
        "not a confirmed crop diagnosis or treatment recommendation. "
        "Consult your local Krishi Vigyan Kendra (KVK) for field-specific advice."
    )
    return "\n".join(lines)


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(request: ChatRequest):
    """
    Chat with KrishiRakshak AI agricultural assistant.
    Supports English, Marathi, and Hindi queries.
    Uses confirmed location and weather data when provided.
    Falls back gracefully to rule-based assistance if Gemini is unavailable.
    """
    forecast_data = None
    weather_included = False
    location_text = ""

    if request.location:
        loc = request.location
        location_parts = [loc.name, loc.region, loc.country]
        location_text = ", ".join(p for p in location_parts if p)

        try:
            forecast = fetch_weather(loc.latitude, loc.longitude)
            if "error" not in forecast:
                forecast_data = forecast
                weather_included = True
        except Exception as e:
            logger.warning("Could not retrieve weather for chat: %s", e)

    # Prepare prompt
    prompt_sections = [f"Farmer's question:\n{request.message}"]

    if location_text:
        prompt_sections.append(f"Confirmed location:\n{location_text}")

    if forecast_data:
        prompt_sections.append(
            f"Actual weather forecast retrieved from Open-Meteo:\n"
            f"{json.dumps(forecast_data, ensure_ascii=False)}"
        )

    prompt_sections.append(
        """Instructions:
- Answer the farmer's question in simple language.
- Respond in the language used by the farmer (English, Marathi, or Hindi).
- Use the supplied weather data when relevant.
- Do not invent weather data, disease diagnoses, or chemical doses.
- Explain uncertainty clearly.
- If crop-specific recommendations cannot be verified, state that clearly.
- Recommend consulting a local Krishi Vigyan Kendra (KVK) when appropriate."""
    )

    full_prompt = "\n\n".join(prompt_sections)

    try:
        agent = get_agent()
        agent_response = agent(full_prompt)
        return ChatResponse(
            response=str(agent_response),
            weather_included=weather_included,
            fallback_used=False,
        )
    except Exception as error:
        err_str = str(error).lower()
        logger.warning("AI model invocation failed: %s", error)

        # Build informative, safe fallback message
        fallback_prefix = (
            "⚠️ The AI language assistant is temporarily unavailable "
            "(service limit or network issue)."
        )

        if forecast_data and location_text:
            weather_text = generate_offline_weather_text(forecast_data, location_text)
            fallback_message = (
                f"{fallback_prefix}\n\n"
                f"Here is the local weather forecast and agricultural guidance based on rules:\n\n"
                f"{weather_text}"
            )
        else:
            fallback_message = (
                f"{fallback_prefix}\n\n"
                "You can still use the dedicated Weather Forecast, Crop Assessment, "
                "and Agricultural Advisory sections from the dashboard without AI."
            )

        return ChatResponse(
            response=fallback_message,
            weather_included=weather_included,
            fallback_used=True,
        )
