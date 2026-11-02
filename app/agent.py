import json
import logging
import os

import requests
from dotenv import load_dotenv
from strands import Agent
from strands.models.gemini import GeminiModel

from tools.advisory_tool import (
    check_agricultural_sources,
    get_crop_advisory,
)
from tools.crop_diagnosis import assess_crop_symptoms
from tools.crop_tool import get_crop_context
from tools.rule_based_advisory import get_weather_based_advice
from tools.weather_tool import fetch_weather


# --------------------------------------------------
# 1. Configuration
# --------------------------------------------------

load_dotenv()

logging.getLogger("strands").setLevel(logging.WARNING)


def _create_agent(model_id=None):
    """Create the Strands AI agent. Requires GOOGLE_API_KEY."""

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY not found. Check your .env file."
        )

    chosen_model = model_id or os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

    model = GeminiModel(
        client_args={"api_key": api_key},
        model_id=chosen_model,
        params={"max_output_tokens": 2048},
    )

    return Agent(
        model=model,
        tools=[
            get_crop_context,
            get_crop_advisory,
            check_agricultural_sources,
            assess_crop_symptoms,
        ],
        system_prompt="""
You are KrishiRakshak AI, an agricultural climate
resilience assistant for farmers in India.

Your responsibilities:
1. Support English, Marathi, and Hindi.
2. Explain weather forecasts in simple language.
3. Use only actual weather data supplied in the prompt.
4. State forecast dates, rain probability, and expected
   rainfall when available.
5. Explain that forecasts can change.
6. Never invent weather data or guarantee crop safety.
7. Give practical, cautious farming guidance.
8. Ask about the crop and growth stage when needed.

Agricultural advisory rules:
1. For crop-specific advice, use get_crop_advisory (supports crop, region, stage).
2. Clearly distinguish official source content from your own AI explanation.
3. Identify the issuing authority/source name and publication date when available.
4. When citing an advisory marked as historical, explicitly explain that it is historical context and must not be used as current seasonal advice.
5. If no relevant verified advisory is available for the crop or region, state that limitation clearly.
6. Never invent or recommend chemical treatments, pesticide dosages, or fertilizer quantities. Do not recommend chemicals simply because they appeared in older bulletins.
7. Treat institutional sources as zone-specific: an advisory for Vidarbha may not apply to Western Maharashtra.
8. Explain uncertainty in simple language.
9. Respond in the farmer's language when possible (English, Marathi, Hindi).
10. For pest or disease issues, always recommend taking a physical sample to the nearest local Krishi Vigyan Kendra (KVK) or Taluka Agriculture Officer.

Weather guidance is not a crop diagnosis.
Do not claim to have retrieved weather data unless it
was actually supplied.
Keep responses concise and farmer-friendly.
""",
    )


# --------------------------------------------------
# 2. Confirm the farmer's location
# --------------------------------------------------

def confirm_location():
    """Search for a location and ask the farmer to confirm it."""

    while True:
        search_location = input(
            "Enter your village/town and district: "
        ).strip()

        if not search_location:
            print("Please enter a location.")
            continue

        try:
            response = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={
                    "name": search_location,
                    "count": 5,
                    "language": "en",
                    "format": "json",
                },
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()

        except requests.RequestException as error:
            print(f"Unable to search for this location: {error}")
            return None

        results = data.get("results", [])

        if not results:
            print("Location not found. Please try another name.")
            continue

        print("\n🌾 Possible locations:\n")

        for index, place in enumerate(results, start=1):
            print(
                f"{index}. "
                f"{place.get('name', 'Unknown')}, "
                f"{place.get('admin1', 'Unknown region')}, "
                f"{place.get('country', 'Unknown country')}"
            )

        choice = input(
            "\nSelect the correct location number "
            "or enter 0 to search again: "
        ).strip()

        if choice == "0":
            continue

        if not choice.isdigit():
            print("Please enter a valid number.")
            continue

        selected_index = int(choice) - 1

        if not 0 <= selected_index < len(results):
            print("Invalid selection. Please try again.")
            continue

        place = results[selected_index]

        name = place.get("name", "Unknown")
        region = place.get("admin1", "")
        country = place.get("country", "")

        print("\n✅ Location selected!")
        print(f"Name: {name}")
        print(f"Region: {region or 'Not available'}")
        print(f"Country: {country or 'Not available'}")

        confirmation = input(
            "\nIs this the correct location? (yes/no): "
        ).strip().lower()

        if confirmation in ("yes", "y"):
            return {
                "name": name,
                "region": region,
                "country": country,
                "latitude": place["latitude"],
                "longitude": place["longitude"],
            }

        print("\nLet's search again.")


# --------------------------------------------------
# 3. Display the forecast and rule-based guidance
# --------------------------------------------------

def display_weather_summary(forecast, location):
    """Display weather and general guidance without Gemini."""

    print("\n" + "=" * 48)
    print("🌦️ KRISHIRAKSHAK AI — WEATHER SUMMARY")
    print("=" * 48)

    location_parts = [
        location.get("name", ""),
        location.get("region", ""),
        location.get("country", ""),
    ]

    location_text = ", ".join(
        part for part in location_parts if part
    )

    print(f"📍 Location: {location_text}")
    print(f"📡 Weather source: {forecast.get('source', 'Open-Meteo')}")

    dates = forecast.get("dates", [])
    probabilities = forecast.get("rain_probability_percent", [])
    rainfall_values = forecast.get("rainfall_mm", [])
    weather_codes = forecast.get("weather_codes", [])

    if not dates:
        print("\nNo forecast dates were returned.")
        return

    for index, forecast_date in enumerate(dates):
        print(f"\n📅 Date: {forecast_date}")

        rain_probability = (
            probabilities[index]
            if index < len(probabilities)
            else None
        )

        rainfall = (
            rainfall_values[index]
            if index < len(rainfall_values)
            else None
        )

        weather_code = (
            weather_codes[index]
            if index < len(weather_codes)
            else -1
        )

        print(
            f"🌧️ Rain probability: "
            f"{rain_probability if rain_probability is not None else 'Unavailable'}"
            f"{'%' if rain_probability is not None else ''}"
        )

        print(
            f"💧 Expected rainfall: "
            f"{rainfall if rainfall is not None else 'Unavailable'}"
            f"{' mm' if rainfall is not None else ''}"
        )

        if rain_probability is None or rainfall is None:
            print(
                "⚠️ Incomplete weather information. "
                "Check an updated local forecast."
            )
            continue

        guidance = get_weather_based_advice(
            rain_probability=rain_probability,
            rainfall_mm=rainfall,
            weather_code=weather_code,
        )

        print("\n🌱 General Weather-Based Farming Guidance:")

        for item in guidance.get("advice", []):
            print(f"• {item}")

    print("\n" + "-" * 48)
    print("⚠️ Important:")
    print(
        "Forecasts can change. This is general weather-based "
        "guidance, not a verified crop-specific recommendation."
    )
    print(
        "Weather data alone cannot diagnose pests or diseases "
        "or determine pesticide and fertilizer requirements."
    )
    print(
        "For crop-specific treatment advice, consult your local "
        "Krishi Vigyan Kendra (KVK) or Taluka Agriculture Officer."
    )
    print("-" * 48 + "\n")


# --------------------------------------------------
# 4. Crop symptom assessment without Gemini
# --------------------------------------------------

def run_crop_assessment():
    """Collect crop symptoms and assess them without Gemini."""

    print("\n🌱 Crop Symptom Assessment")
    print("Currently supported crops: soybean and cotton.\n")

    crop = input("Crop name (soybean/cotton): ").strip()
    growth_stage = input("Current growth stage: ").strip()

    # 3. Affected plant part
    print("\nWhich part of the plant is affected?")
    print("1. Older leaves")
    print("2. Newer leaves")
    print("3. Stems")
    print("4. Roots")
    print("5. Flowers")
    print("6. Pods or fruit")
    print("7. Whole plant")
    print("8. Not sure / Unknown")

    part_options = {
        "1": "older leaves",
        "2": "newer leaves",
        "3": "stems",
        "4": "roots",
        "5": "flowers",
        "6": "pods or fruit",
        "7": "whole plant",
        "8": "unknown",
    }
    part_choice = input("Choose 1–8: ").strip()
    affected_part = part_options.get(part_choice, "unknown")

    # 4. Visible symptoms
    print("\nWhat visible symptoms do you observe?")
    print("1. Yellowing")
    print("2. Wilting")
    print("3. Spots")
    print("4. Holes")
    print("5. Discoloration")
    print("6. Rot")
    print("7. Stunted growth")
    print("8. Other")

    symptom_options = {
        "1": "yellowing",
        "2": "wilting",
        "3": "spots",
        "4": "holes",
        "5": "discoloration",
        "6": "rot",
        "7": "stunted growth",
    }
    symptom_choice = input("Choose 1–8: ").strip()
    if symptom_choice in symptom_options:
        symptoms = symptom_options[symptom_choice]
    else:
        symptoms = input("Describe the symptoms: ").strip()

    # 5. Symptom duration
    print("\nHow long have these symptoms been visible?")
    print("1. Started today")
    print("2. A few days ago")
    print("3. More than a week ago")
    print("4. Unknown / Not sure")

    duration_options = {
        "1": "started today",
        "2": "a few days ago",
        "3": "more than a week ago",
        "4": "unknown",
    }
    duration_choice = input("Choose 1–4: ").strip()
    if duration_choice in duration_options:
        symptom_duration = duration_options[duration_choice]
    else:
        symptom_duration = duration_choice

    # 6. Field distribution
    print("\nWhere are the affected plants located in the field?")
    print("1. Across the whole field")
    print("2. In isolated patches")
    print("3. Near field edges")
    print("4. Individual plants")
    print("5. Not sure / Unknown")

    pattern_options = {
        "1": "whole field",
        "2": "isolated patches",
        "3": "field edges",
        "4": "individual plants",
        "5": "unknown",
    }
    pattern_choice = input("Choose 1–5: ").strip()
    field_pattern = pattern_options.get(pattern_choice, "unknown")

    # 7. Soil moisture
    print("\nWhat is the soil moisture condition?")
    print("1. Dry")
    print("2. Normal")
    print("3. Waterlogged")
    print("4. Not sure / Unknown")

    moisture_options = {
        "1": "dry",
        "2": "normal",
        "3": "waterlogged",
        "4": "unknown",
    }
    moisture_choice = input("Choose 1–4: ").strip()
    soil_moisture = moisture_options.get(moisture_choice, "unknown")

    # 8. Recent rainfall or irrigation
    recent_rainfall = input(
        "\nAny recent rainfall or irrigation? "
        "(e.g. heavy rain 2 days ago, or press Enter to skip): "
    ).strip()

    # 9. Optional notes
    farmer_notes = input(
        "Optional notes or additional observations (or press Enter to skip): "
    ).strip()

    result = assess_crop_symptoms(
        crop=crop,
        growth_stage=growth_stage,
        symptoms=symptoms,
        field_pattern=field_pattern,
        affected_part=affected_part,
        symptom_duration=symptom_duration,
        soil_moisture=soil_moisture,
        recent_rainfall=recent_rainfall,
        farmer_notes=farmer_notes,
    )

    print("\n🌾 KrishiRakshak AI — Crop Assessment")
    print("-" * 46)
    print(f"Status: {result['status']}")

    if result.get("crop"):
        print(f"Crop: {result['crop']}")

    if result.get("growth_stage"):
        print(f"Growth stage: {result['growth_stage']}")

    if result.get("reported_symptoms"):
        print(f"Reported symptoms: {result['reported_symptoms']}")

    if result.get("affected_part") and result["affected_part"] != "unknown":
        print(f"Affected plant part: {result['affected_part']}")

    if result.get("symptom_duration"):
        print(f"Symptom duration: {result['symptom_duration']}")

    if result.get("field_pattern"):
        print(f"Field pattern: {result['field_pattern']}")

    if result.get("soil_moisture") and result["soil_moisture"] != "unknown":
        print(f"Soil moisture: {result['soil_moisture']}")

    if result.get("recent_rainfall"):
        print(f"Recent rainfall/irrigation: {result['recent_rainfall']}")

    if result.get("observations", {}).get("farmer_notes"):
        print(f"Farmer notes: {result['observations']['farmer_notes']}")

    print(f"\n{result['message']}")

    # Display evidence-based possible explanations (distinguishing from confirmation)
    explanations = result.get("possible_explanations", [])
    if explanations:
        print("\n🔍 Possible Explanations (For discussion with local KVK / Officer — NOT a confirmed diagnosis):")
        for exp in explanations:
            print(f"  • {exp}")

    if result.get("missing_information"):
        print("\nℹ️ Additional information that would help an agricultural officer:")
        for item in result["missing_information"]:
            print(f"  • {item}")

    if result.get("recommended_next_steps"):
        print("\nRecommended next steps:")
        for step in result["recommended_next_steps"]:
            print(f"• {step}")

    print("\nChemical recommendations:")
    recommendations = result.get("chemical_recommendations", [])
    if recommendations:
        for recommendation in recommendations:
            print(f"• {recommendation}")
    else:
        print("• No chemical recommendations provided.")

    if result.get("safety_note"):
        print(f"\n⚠️ {result['safety_note']}")

    print()


# --------------------------------------------------
# 5. Main application
# --------------------------------------------------

def main():
    print("\n🌾 Welcome to KrishiRakshak AI!")
    print("Your AI-powered agricultural climate assistant.")
    print("\nCommands:")
    print("  weather  - Show weather without calling Gemini")
    print("  crop     - Assess crop symptoms without Gemini")
    print("  exit     - Quit the application")
    print("\nAsk a farming question to get started.\n")

    # Lazily initialize agent when needed so weather and crop commands work offline
    agent = None
    try:
        agent = _create_agent()
    except ValueError:
        agent = None

    while True:
        question = input("Farmer: ").strip()

        if question.lower() in ("exit", "quit"):
            print("\nThank you for using KrishiRakshak AI! 🌱")
            break

        if not question:
            continue

        # These commands work without Gemini or a location lookup.
        if question.lower() in ("crop", "/crop", "crop assessment"):
            run_crop_assessment()
            continue

        # Other questions require a confirmed location and weather.
        location = confirm_location()

        if not location:
            print("Location could not be confirmed. Try again.\n")
            continue

        forecast = fetch_weather(
            location["latitude"],
            location["longitude"],
        )

        if "error" in forecast:
            print(f"\nWeather service error: {forecast['error']}\n")
            continue

        if question.lower() in (
            "weather",
            "/weather",
            "forecast",
            "/forecast",
        ):
            display_weather_summary(forecast, location)
            continue

        location_text = ", ".join(
            part
            for part in (
                location["name"],
                location.get("region", ""),
                location.get("country", ""),
            )
            if part
        )

        prompt = f"""
Farmer's question:
{question}

Confirmed location:
{location_text}

Actual weather forecast retrieved from Open-Meteo:
{json.dumps(forecast, ensure_ascii=False)}

Instructions:
- Answer the farmer's original question.
- Use the supplied weather data when relevant.
- Include relevant forecast dates and rainfall information.
- Give cautious, practical farming guidance.
- Do not invent weather data.
- Do not invent crop diagnoses or chemical doses.
- Clearly state when crop-specific recommendations
  cannot be verified.
- Answer in the language used by the farmer.
"""

        # Verify agent availability before invoking
        if agent is None:
            try:
                agent = _create_agent()
            except ValueError:
                print("\n⚠️ AI language assistant is unavailable (GOOGLE_API_KEY not configured).")
                print("Showing weather guidance without Gemini:")
                display_weather_summary(forecast, location)
                continue

        try:
            response = agent(prompt)
            print(f"\n🌱 KrishiRakshak AI:\n{response}\n")

        except Exception as error:
            error_message = str(error).lower()

            # Ensure API key is never exposed in printed error message
            api_key = os.getenv("GOOGLE_API_KEY", "")
            sanitized_err_str = str(error)
            if api_key and len(api_key) > 5:
                sanitized_err_str = sanitized_err_str.replace(api_key, "[REDACTED_API_KEY]")

            print("\n⚠️ AI explanation is temporarily unavailable.")

            if (
                "quota" in error_message
                or "429" in error_message
                or "rate limit" in error_message
            ):
                print(
                    "Gemini API quota or rate limit reached. "
                    "Showing weather guidance without Gemini."
                )
            elif (
                "503" in error_message
                or "unavailable" in error_message
            ):
                print(
                    "Gemini is temporarily unavailable. "
                    "Showing weather guidance without Gemini."
                )
            else:
                print(
                    "The AI service encountered an error. "
                    "Showing weather guidance without Gemini."
                )

            display_weather_summary(forecast, location)


# --------------------------------------------------
# 6. Start the application
# --------------------------------------------------

if __name__ == "__main__":
    main()
