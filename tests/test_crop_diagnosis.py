"""Tests for tools/crop_diagnosis.py — assess_crop_symptoms."""

from tools.crop_diagnosis import assess_crop_symptoms


# --------------------------------------------------
# Original tests (unchanged)
# --------------------------------------------------

class TestAssessCropSymptoms:
    """Tests for the core assess_crop_symptoms functionality."""

    def test_valid_soybean_assessment(self):
        """A valid soybean assessment records symptoms correctly."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="yellow spots on leaves",
            field_pattern="patches",
        )

        assert result["status"] == "assessment_recorded"
        assert result["crop"] == "Soybean"
        assert result["growth_stage"] == "flowering"
        assert result["reported_symptoms"] == "yellow spots on leaves"
        assert result["field_pattern"] == "patches"
        assert result["diagnosis"] is None
        assert result["chemical_recommendations"] == []
        assert "safety_note" in result

    def test_valid_cotton_assessment(self):
        """A valid cotton assessment records symptoms correctly."""
        result = assess_crop_symptoms(
            crop="Cotton",
            growth_stage="boll development",
            symptoms="white fluffy growth on leaves",
            field_pattern="whole field",
        )

        assert result["status"] == "assessment_recorded"
        assert result["crop"] == "Cotton"

    def test_unsupported_crop(self):
        """An unsupported crop returns an unsupported_crop status."""
        result = assess_crop_symptoms(
            crop="wheat",
            growth_stage="tillering",
            symptoms="brown spots",
        )

        assert result["status"] == "unsupported_crop"
        assert "soybean" in result["message"].lower() or "cotton" in result["message"].lower()

    def test_missing_growth_stage(self):
        """An empty growth stage returns missing_growth_stage status."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="",
            symptoms="wilting leaves",
        )

        assert result["status"] == "missing_growth_stage"

    def test_whitespace_only_growth_stage(self):
        """A whitespace-only growth stage is treated as missing."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="   ",
            symptoms="wilting leaves",
        )

        assert result["status"] == "missing_growth_stage"

    def test_missing_symptoms(self):
        """Empty symptoms return missing_symptoms status."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="",
        )

        assert result["status"] == "missing_symptoms"

    def test_whitespace_only_symptoms(self):
        """Whitespace-only symptoms are treated as missing."""
        result = assess_crop_symptoms(
            crop="cotton",
            growth_stage="flowering",
            symptoms="   ",
        )

        assert result["status"] == "missing_symptoms"

    def test_invalid_field_pattern_defaults_to_unknown(self):
        """An unrecognized field pattern defaults to 'unknown'."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="brown spots",
            field_pattern="scattered randomly",
        )

        assert result["status"] == "assessment_recorded"
        assert result["field_pattern"] == "unknown"

    def test_default_field_pattern_is_unknown(self):
        """When field_pattern is not provided, it defaults to 'unknown'."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="brown spots",
        )

        assert result["field_pattern"] == "unknown"

    def test_no_chemical_recommendations_ever(self):
        """The tool never provides chemical recommendations."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="grain filling",
            symptoms="holes in leaves, caterpillar droppings visible",
            field_pattern="whole field",
        )

        assert result["chemical_recommendations"] == []
        assert "safety_note" in result

    def test_recommended_next_steps_present(self):
        """A valid assessment includes recommended next steps."""
        result = assess_crop_symptoms(
            crop="cotton",
            growth_stage="vegetative",
            symptoms="curling leaves",
            field_pattern="individual plants",
        )

        assert isinstance(result["recommended_next_steps"], list)
        assert len(result["recommended_next_steps"]) > 0

    def test_crop_name_case_insensitive(self):
        """Crop name matching is case-insensitive."""
        result = assess_crop_symptoms(
            crop="SOYBEAN",
            growth_stage="flowering",
            symptoms="yellowing",
        )

        assert result["status"] == "assessment_recorded"
        assert result["crop"] == "Soybean"

    def test_crop_name_with_whitespace(self):
        """Leading/trailing whitespace in crop name is handled."""
        result = assess_crop_symptoms(
            crop="  cotton  ",
            growth_stage="flowering",
            symptoms="spots",
        )

        assert result["status"] == "assessment_recorded"
        assert result["crop"] == "Cotton"


# --------------------------------------------------
# New tests for extended fields
# --------------------------------------------------

class TestAffectedPart:
    """Tests for the affected_part parameter."""

    def test_valid_affected_part_leaves(self):
        """'leaves' is accepted as a valid affected part."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="yellow spots",
            affected_part="leaves",
        )

        assert result["affected_part"] == "leaves"

    def test_valid_affected_part_stems(self):
        """'stems' is accepted as a valid affected part."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="black marks",
            affected_part="stems",
        )

        assert result["affected_part"] == "stems"

    def test_valid_affected_part_roots(self):
        """'roots' is accepted as a valid affected part."""
        result = assess_crop_symptoms(
            crop="cotton",
            growth_stage="seedling",
            symptoms="rotting at base",
            affected_part="roots",
        )

        assert result["affected_part"] == "roots"

    def test_valid_affected_part_pods(self):
        """'pods' is accepted as a valid affected part."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="pod filling",
            symptoms="shriveled pods",
            affected_part="pods",
        )

        assert result["affected_part"] == "pods"

    def test_valid_affected_part_bolls(self):
        """'bolls' is accepted as a valid affected part."""
        result = assess_crop_symptoms(
            crop="cotton",
            growth_stage="boll development",
            symptoms="bollworm damage",
            affected_part="bolls",
        )

        assert result["affected_part"] == "bolls"

    def test_valid_affected_part_flowers(self):
        """'flowers' is accepted as a valid affected part."""
        result = assess_crop_symptoms(
            crop="cotton",
            growth_stage="flowering",
            symptoms="flower dropping",
            affected_part="flowers",
        )

        assert result["affected_part"] == "flowers"

    def test_valid_affected_part_whole_plant(self):
        """'whole plant' is accepted as a valid affected part."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="vegetative",
            symptoms="wilting",
            affected_part="whole plant",
        )

        assert result["affected_part"] == "whole plant"

    def test_invalid_affected_part_defaults_to_unknown(self):
        """An unrecognized affected part defaults to 'unknown'."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="spots",
            affected_part="bark",
        )

        assert result["affected_part"] == "unknown"

    def test_default_affected_part_is_unknown(self):
        """When affected_part is not provided, it defaults to 'unknown'."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="spots",
        )

        assert result["affected_part"] == "unknown"

    def test_affected_part_case_insensitive(self):
        """Affected part matching is case-insensitive."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="spots",
            affected_part="LEAVES",
        )

        assert result["affected_part"] == "leaves"

    def test_affected_part_whitespace_trimmed(self):
        """Leading/trailing whitespace in affected_part is trimmed."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="spots",
            affected_part="  stems  ",
        )

        assert result["affected_part"] == "stems"


class TestSymptomDuration:
    """Tests for the symptom_duration parameter."""

    def test_duration_provided(self):
        """A provided duration is recorded."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="yellow leaves",
            symptom_duration="3 days",
        )

        assert result["symptom_duration"] == "3 days"

    def test_duration_empty_string(self):
        """An empty duration is stored as None."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="yellow leaves",
            symptom_duration="",
        )

        assert result["symptom_duration"] is None

    def test_duration_not_provided(self):
        """When duration is not provided, it defaults to None."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="yellow leaves",
        )

        assert result["symptom_duration"] is None

    def test_duration_whitespace_trimmed(self):
        """Whitespace in duration is trimmed."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="spots",
            symptom_duration="  1 week  ",
        )

        assert result["symptom_duration"] == "1 week"

    def test_whitespace_only_duration_is_none(self):
        """A whitespace-only duration is stored as None."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="spots",
            symptom_duration="   ",
        )

        assert result["symptom_duration"] is None


class TestSoilMoisture:
    """Tests for the soil_moisture parameter."""

    def test_valid_dry(self):
        """'dry' is accepted as valid soil moisture."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="wilting",
            soil_moisture="dry",
        )

        assert result["soil_moisture"] == "dry"

    def test_valid_moist(self):
        """'moist' is accepted as valid soil moisture."""
        result = assess_crop_symptoms(
            crop="cotton",
            growth_stage="vegetative",
            symptoms="spots",
            soil_moisture="moist",
        )

        assert result["soil_moisture"] == "moist"

    def test_valid_waterlogged(self):
        """'waterlogged' is accepted as valid soil moisture."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="seedling",
            symptoms="yellowing",
            soil_moisture="waterlogged",
        )

        assert result["soil_moisture"] == "waterlogged"

    def test_invalid_moisture_defaults_to_unknown(self):
        """An unrecognized moisture value defaults to 'unknown'."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="spots",
            soil_moisture="soggy",
        )

        assert result["soil_moisture"] == "unknown"

    def test_default_moisture_is_unknown(self):
        """When soil_moisture is not provided, it defaults to 'unknown'."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="spots",
        )

        assert result["soil_moisture"] == "unknown"

    def test_moisture_case_insensitive(self):
        """Soil moisture matching is case-insensitive."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="spots",
            soil_moisture="DRY",
        )

        assert result["soil_moisture"] == "dry"


class TestRecentRainfall:
    """Tests for the recent_rainfall parameter."""

    def test_rainfall_provided(self):
        """Provided rainfall information is recorded."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="spots",
            recent_rainfall="heavy rain 2 days ago",
        )

        assert result["recent_rainfall"] == "heavy rain 2 days ago"

    def test_rainfall_empty_string(self):
        """An empty rainfall string is stored as None."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="spots",
            recent_rainfall="",
        )

        assert result["recent_rainfall"] is None

    def test_rainfall_not_provided(self):
        """When recent_rainfall is not provided, it defaults to None."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="spots",
        )

        assert result["recent_rainfall"] is None

    def test_rainfall_whitespace_trimmed(self):
        """Whitespace in rainfall info is trimmed."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="spots",
            recent_rainfall="  light drizzle yesterday  ",
        )

        assert result["recent_rainfall"] == "light drizzle yesterday"


class TestMissingInformation:
    """Tests for the missing_information feedback mechanism."""

    def test_all_fields_missing_reports_all(self):
        """When optional fields are missing, all are reported."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="spots",
            # All optional fields at defaults (unknown/empty).
        )

        assert result["missing_information"] is not None
        assert len(result["missing_information"]) == 4

    def test_all_fields_provided_no_missing(self):
        """When all fields are provided, missing_information is None."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="yellow spots on upper leaves",
            field_pattern="patches",
            affected_part="leaves",
            symptom_duration="3 days",
            soil_moisture="moist",
            recent_rainfall="light rain yesterday",
        )

        assert result["missing_information"] is None

    def test_some_fields_missing(self):
        """When some fields are missing, only those are reported."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="spots",
            affected_part="leaves",
            soil_moisture="dry",
            # symptom_duration and recent_rainfall are missing.
        )

        assert result["missing_information"] is not None
        assert len(result["missing_information"]) == 2

    def test_message_differs_with_complete_info(self):
        """The message changes when all information is provided."""
        incomplete = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="spots",
        )

        complete = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="spots",
            affected_part="leaves",
            symptom_duration="2 days",
            soil_moisture="moist",
            recent_rainfall="none",
        )

        assert "missing" in incomplete["message"].lower()
        assert "detailed" in complete["message"].lower()


class TestFullAssessment:
    """Integration-style tests with all fields provided."""

    def test_complete_soybean_assessment(self):
        """A complete soybean assessment has all expected fields."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="pod filling",
            symptoms="brown spots on upper leaves, some defoliation",
            field_pattern="patches",
            affected_part="leaves",
            symptom_duration="5 days",
            soil_moisture="moist",
            recent_rainfall="heavy rain 3 days ago",
        )

        assert result["status"] == "assessment_recorded"
        assert result["crop"] == "Soybean"
        assert result["growth_stage"] == "pod filling"
        assert result["reported_symptoms"] == "brown spots on upper leaves, some defoliation"
        assert result["affected_part"] == "leaves"
        assert result["symptom_duration"] == "5 days"
        assert result["field_pattern"] == "patches"
        assert result["soil_moisture"] == "moist"
        assert result["recent_rainfall"] == "heavy rain 3 days ago"
        assert result["diagnosis"] is None
        assert result["chemical_recommendations"] == []
        assert result["missing_information"] is None
        assert "safety_note" in result

    def test_complete_cotton_assessment(self):
        """A complete cotton assessment has all expected fields."""
        result = assess_crop_symptoms(
            crop="cotton",
            growth_stage="boll development",
            symptoms="bollworm holes visible on bolls",
            field_pattern="individual plants",
            affected_part="bolls",
            symptom_duration="1 week",
            soil_moisture="dry",
            recent_rainfall="no recent rain",
        )

        assert result["status"] == "assessment_recorded"
        assert result["crop"] == "Cotton"
        assert result["affected_part"] == "bolls"
        assert result["diagnosis"] is None
        assert result["chemical_recommendations"] == []

    def test_non_string_or_none_inputs_handled(self):
        """None or non-string inputs for core fields return structured error status."""
        assert assess_crop_symptoms(crop=None, growth_stage="flowering", symptoms="wilting")["status"] == "unsupported_crop"
        assert assess_crop_symptoms(crop=123, growth_stage="flowering", symptoms="wilting")["status"] == "unsupported_crop"
        assert assess_crop_symptoms(crop="soybean", growth_stage=None, symptoms="wilting")["status"] == "missing_growth_stage"
        assert assess_crop_symptoms(crop="soybean", growth_stage="flowering", symptoms=None)["status"] == "missing_symptoms"

    def test_non_string_optional_fields_safe(self):
        """Non-string optional fields do not crash."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="yellow spots",
            field_pattern=999,
            affected_part=888,
            soil_moisture=777,
        )
        assert result["status"] == "assessment_recorded"
        assert result["diagnosis"] is None
        assert result["chemical_recommendations"] == []


# --------------------------------------------------
# Tests for Improved Workflow Requirements
# --------------------------------------------------

class TestWorkflowStructuredOutputs:
    """Validate all required structured output fields are present and predictable."""

    def test_all_required_output_fields_present(self):
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="yellowing",
            field_pattern="isolated patches",
            affected_plant_parts=["older leaves"],
            symptom_duration="a few days ago",
            soil_moisture="normal",
            recent_rainfall_or_irrigation="15 mm rain yesterday",
            farmer_notes="observed near east boundary",
        )

        expected_fields = [
            "status",
            "crop",
            "growth_stage",
            "affected_plant_parts",
            "reported_symptoms",
            "symptom_duration",
            "field_pattern",
            "soil_moisture",
            "recent_rainfall_or_irrigation",
            "observations",
            "possible_explanations",
            "missing_information",
            "recommended_next_steps",
            "chemical_recommendations",
            "safety_note",
            "diagnosis",
        ]
        for field in expected_fields:
            assert field in result, f"Expected '{field}' in result dictionary"

        # Check observations sub-structure
        obs = result["observations"]
        assert obs["crop"] == "Soybean"
        assert obs["growth_stage"] == "flowering"
        assert obs["affected_plant_parts"] == ["older leaves"]
        assert obs["symptom_duration"] == "A few days ago"
        assert obs["field_distribution"] == "isolated patches"
        assert obs["soil_moisture"] == "normal"
        assert obs["recent_rainfall_or_irrigation"] == "15 mm rain yesterday"
        assert obs["farmer_notes"] == "observed near east boundary"


class TestAllPlantPartsObservations:
    """Verify that all specified plant part categories are supported."""

    def test_older_leaves(self):
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="yellowing",
            affected_part="older leaves",
        )
        assert "older leaves" in result["affected_plant_parts"]
        assert result["affected_part"] == "older leaves"

    def test_newer_leaves(self):
        result = assess_crop_symptoms(
            crop="cotton",
            growth_stage="vegetative",
            symptoms="yellowing",
            affected_part="newer leaves",
        )
        assert "newer leaves" in result["affected_plant_parts"]
        assert result["affected_part"] == "newer leaves"

    def test_stems(self):
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="holes",
            affected_part="stems",
        )
        assert "stems" in result["affected_plant_parts"]

    def test_roots(self):
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="seedling",
            symptoms="rot",
            affected_part="roots",
        )
        assert "roots" in result["affected_plant_parts"]

    def test_flowers(self):
        result = assess_crop_symptoms(
            crop="cotton",
            growth_stage="flowering",
            symptoms="holes",
            affected_part="flowers",
        )
        assert "flowers" in result["affected_plant_parts"]

    def test_pods_or_fruit(self):
        result = assess_crop_symptoms(
            crop="cotton",
            growth_stage="boll development",
            symptoms="holes",
            affected_part="pods or fruit",
        )
        assert "pods or fruit" in result["affected_plant_parts"]

    def test_whole_plant(self):
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="wilting",
            affected_part="whole plant",
        )
        assert "whole plant" in result["affected_plant_parts"]

    def test_unknown_part(self):
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="spots",
            affected_part="unknown",
        )
        assert "unknown" in result["affected_plant_parts"]


class TestAllSymptomCategories:
    """Verify that all specified visible symptoms are accepted and recorded."""

    def test_symptom_categories(self):
        categories = [
            "yellowing",
            "wilting",
            "spots",
            "holes",
            "discoloration",
            "rot",
            "stunted growth",
            "other",
        ]
        for symptom in categories:
            result = assess_crop_symptoms(
                crop="soybean",
                growth_stage="flowering",
                symptoms=symptom,
            )
            assert result["status"] == "assessment_recorded"
            assert symptom in result["reported_symptoms"]

    def test_symptoms_list_input(self):
        result = assess_crop_symptoms(
            crop="cotton",
            growth_stage="boll development",
            symptoms=["yellowing", "wilting", "spots"],
        )
        assert result["status"] == "assessment_recorded"
        assert "yellowing" in result["reported_symptoms"]
        assert "wilting" in result["reported_symptoms"]


class TestSymptomDurationCategories:
    """Verify standard duration categories."""

    def test_started_today(self):
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="wilting",
            symptom_duration="started today",
        )
        assert result["symptom_duration"] == "Started today"

    def test_a_few_days_ago(self):
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="spots",
            symptom_duration="a few days ago",
        )
        assert result["symptom_duration"] == "A few days ago"

    def test_more_than_a_week_ago(self):
        result = assess_crop_symptoms(
            crop="cotton",
            growth_stage="flowering",
            symptoms="yellowing",
            symptom_duration="more than a week ago",
        )
        assert result["symptom_duration"] == "More than a week ago"

    def test_unknown_duration(self):
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="spots",
            symptom_duration="unknown",
        )
        assert result["symptom_duration"] is None


class TestFieldDistributionCategories:
    """Verify field distribution categories."""

    def test_whole_field(self):
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="spots",
            field_pattern="whole field",
        )
        assert result["field_pattern"] == "whole field"

    def test_isolated_patches(self):
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="spots",
            field_pattern="isolated patches",
        )
        assert result["field_pattern"] == "isolated patches"

    def test_field_edges(self):
        result = assess_crop_symptoms(
            crop="cotton",
            growth_stage="flowering",
            symptoms="spots",
            field_pattern="field edges",
        )
        assert result["field_pattern"] == "field edges"

    def test_individual_plants(self):
        result = assess_crop_symptoms(
            crop="cotton",
            growth_stage="flowering",
            symptoms="spots",
            field_pattern="individual plants",
        )
        assert result["field_pattern"] == "individual plants"


class TestSoilMoistureCategories:
    """Verify soil moisture options: dry, normal, waterlogged, unknown."""

    def test_normal_moisture(self):
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="spots",
            soil_moisture="normal",
        )
        assert result["soil_moisture"] == "normal"

    def test_moist_maps_to_normal(self):
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="spots",
            soil_moisture="moist",
        )
        assert result["soil_moisture"] in ("normal", "moist")


class TestEvidenceBasedPossibleExplanations:
    """Verify that possible explanations are evidence-based, cautious, and never confirmed."""

    def test_soybean_waterlogging_and_yellowing_older_leaves(self):
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="yellowing",
            affected_part="older leaves",
            soil_moisture="waterlogged",
            recent_rainfall="heavy rain 2 days ago",
            field_pattern="isolated patches",
        )
        assert len(result["possible_explanations"]) > 0
        explanations_text = " ".join(result["possible_explanations"]).lower()
        # Confirms abiotic factors discussed
        assert "waterlogging" in explanations_text or "nutrient" in explanations_text
        # Confirms non-definitive wording
        assert "possible" in explanations_text
        assert "not a confirmed diagnosis" in explanations_text

    def test_cotton_green_boll_holes(self):
        result = assess_crop_symptoms(
            crop="cotton",
            growth_stage="boll development",
            symptoms="holes in green bolls",
            affected_part="pods or fruit",
            field_pattern="individual plants",
            soil_moisture="normal",
        )
        assert len(result["possible_explanations"]) > 0
        explanations_text = " ".join(result["possible_explanations"]).lower()
        assert "bollworm" in explanations_text

    def test_insufficient_evidence_generates_no_premature_explanations(self):
        """When plant part, distribution, and soil moisture are all unknown, no premature explanation is created."""
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="some discoloration",
            affected_part="unknown",
            field_pattern="unknown",
            soil_moisture="unknown",
        )
        assert result["possible_explanations"] == []
        assert result["missing_information"] is not None


class TestYellowLeavesMultipleCauses:
    """Verify that yellow leaves are not assumed to have a single cause."""

    def test_yellow_leaves_discusses_multiple_possibilities(self):
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="yellowing",
            affected_part="older leaves",
            field_pattern="whole field",
            soil_moisture="waterlogged",
            recent_rainfall="continuous heavy rain",
        )
        explanations = result["possible_explanations"]
        assert len(explanations) >= 2, "Expected multiple possible causes for leaf yellowing"
        all_text = " ".join(explanations).lower()
        assert "waterlogging" in all_text
        assert "nutrient" in all_text or "nitrogen" in all_text


class TestSafetySeparationAndNoChemicalDoses:
    """Verify strict safety guidelines."""

    def test_diagnosis_is_strictly_none(self):
        result = assess_crop_symptoms(
            crop="cotton",
            growth_stage="flowering",
            symptoms="yellowing and wilting",
            affected_part="older leaves",
            soil_moisture="dry",
        )
        assert result["diagnosis"] is None

    def test_no_confidence_score_or_probability(self):
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="holes",
            affected_part="leaves",
            field_pattern="whole field",
            soil_moisture="normal",
        )
        all_text = " ".join(result["possible_explanations"] + result["recommended_next_steps"]).lower()
        # Must not contain fabricated confidence scores or probabilities
        assert "%" not in all_text
        assert "confidence score" not in all_text
        assert "probability:" not in all_text

    def test_chemical_recommendations_strictly_empty(self):
        result = assess_crop_symptoms(
            crop="cotton",
            growth_stage="boll development",
            symptoms="caterpillar feeding",
            affected_part="pods or fruit",
            field_pattern="patches",
            soil_moisture="normal",
        )
        assert result["chemical_recommendations"] == []
        assert "safety_note" in result

    def test_recommends_kvk_or_officer(self):
        result = assess_crop_symptoms(
            crop="soybean",
            growth_stage="flowering",
            symptoms="yellowing",
        )
        steps_text = " ".join(result["recommended_next_steps"]).lower()
        assert "krishi vigyan kendra" in steps_text or "kvk" in steps_text or "officer" in steps_text

