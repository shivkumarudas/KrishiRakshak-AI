"""Tests for tools/rule_based_advisory.py — get_weather_based_advice."""

from tools.rule_based_advisory import get_weather_based_advice


class TestGetWeatherBasedAdvice:
    """Tests for the get_weather_based_advice function."""

    def test_high_rain_probability(self):
        """Rain probability >= 70% triggers high-rain guidance."""
        result = get_weather_based_advice(
            rain_probability=85,
            rainfall_mm=30.0,
            weather_code=61,
        )

        assert "High forecast probability of rain" in result["risks"]
        assert any("forecast" in a.lower() or "spray" in a.lower() for a in result["advice"])

    def test_moderate_rain_probability(self):
        """Rain probability between 30% and 70% triggers moderate guidance."""
        result = get_weather_based_advice(
            rain_probability=50,
            rainfall_mm=5.0,
            weather_code=3,
        )

        assert "Some possibility of rain" in result["risks"]

    def test_low_rain_probability(self):
        """Rain probability < 30% triggers low-rain guidance."""
        result = get_weather_based_advice(
            rain_probability=10,
            rainfall_mm=0.0,
            weather_code=0,
        )

        assert "Low forecast probability of rain" in result["risks"]
        assert any("irrigation" in a.lower() or "soil moisture" in a.lower() for a in result["advice"])

    def test_heavy_rainfall(self):
        """Rainfall >= 20 mm triggers drainage warning."""
        result = get_weather_based_advice(
            rain_probability=90,
            rainfall_mm=25.0,
            weather_code=63,
        )

        assert "Forecast rainfall of 20 mm or more" in result["risks"]
        assert any("drainage" in a.lower() or "waterlogging" in a.lower() for a in result["advice"])

    def test_light_rainfall(self):
        """Rainfall > 0 but < 20 mm gives moderate rainfall advice."""
        result = get_weather_based_advice(
            rain_probability=40,
            rainfall_mm=8.0,
            weather_code=51,
        )

        assert any("rainfall" in a.lower() for a in result["advice"])

    def test_zero_rainfall(self):
        """Zero rainfall does not mention drainage or waterlogging."""
        result = get_weather_based_advice(
            rain_probability=10,
            rainfall_mm=0.0,
            weather_code=0,
        )

        assert not any("waterlogging" in a.lower() for a in result["advice"])

    def test_foggy_conditions(self):
        """Weather code 45 (fog) triggers fog-related guidance."""
        result = get_weather_based_advice(
            rain_probability=20,
            rainfall_mm=0.0,
            weather_code=45,
        )

        assert "Foggy conditions forecast" in result["risks"]

    def test_foggy_conditions_code_48(self):
        """Weather code 48 (depositing rime fog) also triggers fog guidance."""
        result = get_weather_based_advice(
            rain_probability=15,
            rainfall_mm=0.0,
            weather_code=48,
        )

        assert "Foggy conditions forecast" in result["risks"]

    def test_non_foggy_code(self):
        """A non-fog weather code does not trigger fog warnings."""
        result = get_weather_based_advice(
            rain_probability=50,
            rainfall_mm=10.0,
            weather_code=61,
        )

        assert "Foggy conditions forecast" not in result["risks"]

    def test_disclaimer_always_present(self):
        """Every response includes a disclaimer."""
        result = get_weather_based_advice(
            rain_probability=50,
            rainfall_mm=10.0,
            weather_code=3,
        )

        assert "disclaimer" in result
        assert "general" in result["disclaimer"].lower()

    def test_type_is_general_guidance(self):
        """The response type is always 'general_weather_based_guidance'."""
        result = get_weather_based_advice(
            rain_probability=50,
            rainfall_mm=10.0,
            weather_code=3,
        )

        assert result["type"] == "general_weather_based_guidance"

    def test_boundary_rain_probability_70(self):
        """Exactly 70% triggers the high-rain threshold."""
        result = get_weather_based_advice(
            rain_probability=70,
            rainfall_mm=15.0,
            weather_code=61,
        )

        assert "High forecast probability of rain" in result["risks"]

    def test_boundary_rain_probability_30(self):
        """Exactly 30% triggers the moderate-rain threshold."""
        result = get_weather_based_advice(
            rain_probability=30,
            rainfall_mm=2.0,
            weather_code=3,
        )

        assert "Some possibility of rain" in result["risks"]

    def test_boundary_rainfall_20mm(self):
        """Exactly 20 mm triggers the heavy-rainfall threshold."""
        result = get_weather_based_advice(
            rain_probability=80,
            rainfall_mm=20.0,
            weather_code=63,
        )

        assert "Forecast rainfall of 20 mm or more" in result["risks"]

    def test_none_or_missing_inputs(self):
        """None values for rain_probability and rainfall_mm do not crash."""
        result = get_weather_based_advice(
            rain_probability=None,
            rainfall_mm=None,
            weather_code=None,
        )
        assert result["type"] == "general_weather_based_guidance"
        assert "advice" in result
        assert "risks" in result
        assert "disclaimer" in result

    def test_invalid_types_handled_gracefully(self):
        """Non-numeric strings or negative values are handled safely."""
        result = get_weather_based_advice(
            rain_probability="invalid",
            rainfall_mm=-10.0,
            weather_code="invalid",
        )
        assert result["type"] == "general_weather_based_guidance"
        assert isinstance(result["advice"], list)

    def test_never_prescribes_chemical_dosages(self):
        """Advice and risks must never include chemical dosage prescriptions."""
        result = get_weather_based_advice(
            rain_probability=85,
            rainfall_mm=35.0,
            weather_code=65,
        )
        all_text = " ".join(result["advice"] + result["risks"]).lower()
        forbidden_terms = ["ml/l", "g/l", "kg/ha", "dose:", "dosage", "apply 2ml", "spray 500g"]
        for term in forbidden_terms:
            assert term not in all_text
