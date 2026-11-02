"""Tests for tools/crop_tool.py — get_crop_context."""

from tools.crop_tool import get_crop_context


class TestGetCropContext:
    """Tests for the get_crop_context function."""

    def test_valid_soybean(self):
        """Soybean with a growth stage returns crop context."""
        result = get_crop_context("soybean", "flowering")

        assert result["crop"] == "Soybean"
        assert result["growth_stage"] == "flowering"
        assert "next_step" in result

    def test_valid_cotton(self):
        """Cotton with a growth stage returns crop context."""
        result = get_crop_context("cotton", "boll development")

        assert result["crop"] == "Cotton"
        assert result["growth_stage"] == "boll development"

    def test_case_insensitive_crop(self):
        """Crop matching is case-insensitive."""
        result = get_crop_context("SOYBEAN", "maturity")

        assert result["crop"] == "Soybean"

    def test_unsupported_crop(self):
        """An unsupported crop returns an error."""
        result = get_crop_context("wheat", "tillering")

        assert "error" in result
        assert "soybean" in result["error"].lower() or "cotton" in result["error"].lower()

    def test_empty_growth_stage(self):
        """An empty growth stage returns an error."""
        result = get_crop_context("soybean", "")

        assert "error" in result

    def test_whitespace_only_growth_stage(self):
        """A whitespace-only growth stage returns an error."""
        result = get_crop_context("soybean", "   ")

        assert "error" in result

    def test_next_step_discourages_invented_treatments(self):
        """The next_step text discourages inventing recommendations."""
        result = get_crop_context("cotton", "vegetative")

        assert "invent" in result["next_step"].lower() or "do not" in result["next_step"].lower()

    def test_none_or_non_string_inputs(self):
        """None or non-string inputs return an error dictionary."""
        assert "error" in get_crop_context(None, "flowering")
        assert "error" in get_crop_context(123, "flowering")
        assert "error" in get_crop_context("soybean", None)
        assert "error" in get_crop_context("soybean", 123)
