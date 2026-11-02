"""Unit tests for services/image_service.py."""

import json
import pytest
from unittest.mock import patch, MagicMock
from services.image_service import (
    validate_image_bytes,
    analyze_crop_image_bytes,
    is_vision_capable_model,
    ImageValidationError,
    MAX_IMAGE_SIZE_BYTES,
)

VALID_JPEG = b"\xFF\xD8\xFF\xE0\x00\x10JFIF" + b"\x00" * 64
VALID_PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"\x00" * 32
VALID_WEBP = b"RIFF\x20\x00\x00\x00WEBPVP8 " + b"\x00" * 16


class TestImageValidation:
    """Tests for validate_image_bytes function."""

    def test_valid_jpeg(self):
        mime = validate_image_bytes(VALID_JPEG, "image/jpeg", "leaf.jpg")
        assert mime == "image/jpeg"

    def test_valid_png(self):
        mime = validate_image_bytes(VALID_PNG, "image/png", "leaf.png")
        assert mime == "image/png"

    def test_valid_webp(self):
        mime = validate_image_bytes(VALID_WEBP, "image/webp", "leaf.webp")
        assert mime == "image/webp"

    def test_empty_bytes_raises_400(self):
        with pytest.raises(ImageValidationError) as exc_info:
            validate_image_bytes(b"", "image/jpeg", "empty.jpg")
        assert exc_info.value.status_code == 400
        assert "empty" in exc_info.value.message.lower()

    def test_oversized_bytes_raises_413(self):
        huge_bytes = b"x" * (MAX_IMAGE_SIZE_BYTES + 1024)
        with pytest.raises(ImageValidationError) as exc_info:
            validate_image_bytes(huge_bytes, "image/jpeg", "huge.jpg")
        assert exc_info.value.status_code == 413
        assert "too large" in exc_info.value.message.lower()

    def test_unsupported_mime_raises_415(self):
        with pytest.raises(ImageValidationError) as exc_info:
            validate_image_bytes(b"some text content", "text/plain", "doc.txt")
        assert exc_info.value.status_code == 415

    def test_corrupted_jpeg_magic_bytes_raises_415(self):
        corrupted_jpeg = b"NOT_A_JPEG_HEADER" + b"\x00" * 50
        with pytest.raises(ImageValidationError) as exc_info:
            validate_image_bytes(corrupted_jpeg, "image/jpeg", "fake.jpg")
        assert exc_info.value.status_code == 415
        assert "corrupted" in exc_info.value.message.lower()

    def test_corrupted_png_magic_bytes_raises_415(self):
        corrupted_png = b"\x00\x01\x02\x03PNG" + b"\x00" * 50
        with pytest.raises(ImageValidationError) as exc_info:
            validate_image_bytes(corrupted_png, "image/png", "fake.png")
        assert exc_info.value.status_code == 415


class TestModelVisionCapability:
    """Tests for vision model detection."""

    def test_vision_capable_models(self):
        assert is_vision_capable_model("gemini-3.8-flash") is True
        assert is_vision_capable_model("gemini-2.5-flash") is True
        assert is_vision_capable_model("gemini-2.5-pro") is True
        assert is_vision_capable_model("gemini-1.5-flash") is True

    def test_text_only_models_rejected(self):
        assert is_vision_capable_model("text-bison") is False
        assert is_vision_capable_model("chat-bison") is False
        assert is_vision_capable_model("gemini-1.0-text") is False
        assert is_vision_capable_model("text-embedding-004") is False


class TestImageAnalysis:
    """Tests for analyze_crop_image_bytes function."""

    @patch.dict("os.environ", {}, clear=True)
    def test_missing_api_key_returns_vision_unavailable(self):
        """When GOOGLE_API_KEY is not set, returns vision_unavailable status."""
        result = analyze_crop_image_bytes(VALID_JPEG, "image/jpeg", "leaf.jpg")
        assert result["status"] == "vision_unavailable"
        assert "GOOGLE_API_KEY" in result["message"]
        assert "safety_note" in result

    def test_unsupported_crop_raises_422(self):
        """Unsupported crop raises ImageValidationError with status 422."""
        with pytest.raises(ImageValidationError) as exc_info:
            analyze_crop_image_bytes(
                VALID_JPEG,
                "image/jpeg",
                "wheat.jpg",
                crop="wheat",
            )
        assert exc_info.value.status_code == 422
        assert "soybean and cotton" in exc_info.value.message.lower()

    @patch.dict("os.environ", {"GOOGLE_API_KEY": "fake_test_key"})
    def test_text_only_model_returns_vision_unavailable(self):
        """Reject configured text-only models and return vision_unavailable."""
        result = analyze_crop_image_bytes(
            VALID_JPEG,
            "image/jpeg",
            "leaf.jpg",
            model_id="text-bison",
        )
        assert result["status"] == "vision_unavailable"
        assert "does not support multimodal" in result["message"]

    @patch("google.genai.Client")
    @patch.dict("os.environ", {"GOOGLE_API_KEY": "fake_test_key"})
    def test_structured_json_analysis_success(self, mock_client_cls):
        """When Gemini returns JSON, fields are parsed into structured output."""
        gemini_json = {
            "visible_plant_parts": ["older leaves", "leaf veins"],
            "observable_visual_symptoms": ["interveinal chlorosis", "green veins"],
            "image_quality_limitations": ["leaf underside not visible"],
            "possible_explanations": ["Possible magnesium or iron deficiency", "Possible early root stress"],
            "additional_observations_needed": ["Check soil pH and moisture", "Inspect lower stems"],
            "recommended_safe_next_steps": ["Ensure proper drainage", "Take leaf sample to local KVK"],
            "professional_assessment_advisable": True,
            "narrative": "Leaves display classic interveinal chlorosis with dark green veins intact.",
        }
        mock_response = MagicMock()
        mock_response.text = json.dumps(gemini_json)

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = analyze_crop_image_bytes(
            VALID_JPEG,
            "image/jpeg",
            "soybean_chlorosis.jpg",
            crop="soybean",
            growth_stage="flowering",
            notes="Yellowing between veins after rain",
        )

        assert result["status"] == "analysis_completed"
        assert result["crop"] == "Soybean"
        assert result["growth_stage"] == "flowering"
        assert "older leaves" in result["visible_plant_parts"]
        assert "interveinal chlorosis" in result["observable_visual_symptoms"]
        assert result["professional_assessment_advisable"] is True
        assert len(result["possible_explanations"]) == 2
        # Safety invariant checks
        assert "safety_note" in result
        assert "uncertainty_note" in result
        assert "chemical_recommendations" not in result or result.get("chemical_recommendations") == []

    @patch("google.genai.Client")
    @patch.dict("os.environ", {"GOOGLE_API_KEY": "fake_test_key"})
    def test_heuristic_fallback_for_plain_text(self, mock_client_cls):
        """When Gemini returns freeform text instead of JSON, heuristic parser extracts structure."""
        mock_response = MagicMock()
        mock_response.text = (
            "Visual Observations:\n"
            "- Yellow mosaic pattern on upper leaves.\n"
            "Possible Explanations (Uncertain):\n"
            "- May indicate Yellow Mosaic Virus or nutrient deficiency.\n"
            "Recommendation:\n"
            "- Check leaf underside for whiteflies. Consult local KVK."
        )
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = analyze_crop_image_bytes(
            VALID_JPEG,
            "image/jpeg",
            "soybean_leaf.jpg",
            crop="soybean",
        )

        assert result["status"] == "analysis_completed"
        assert result["crop"] == "Soybean"
        assert len(result["visible_plant_parts"]) > 0
        assert len(result["observable_visual_symptoms"]) > 0
        assert "safety_note" in result
        assert result["file_name"] == "soybean_leaf.jpg"

    @patch("google.genai.Client")
    @patch.dict("os.environ", {"GOOGLE_API_KEY": "fake_test_key"})
    def test_gemini_quota_error_handled_gracefully(self, mock_client_cls):
        """When Gemini raises quota/rate-limit error, returns safe fallback."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("ResourceExhausted: 429 Quota exceeded")
        mock_client_cls.return_value = mock_client

        result = analyze_crop_image_bytes(VALID_JPEG, "image/jpeg", "cotton_boll.jpg")

        assert result["status"] == "vision_unavailable"
        assert "quota" in result["message"].lower() or "rate limit" in result["message"].lower()
        assert "safety_note" in result

    @patch("google.genai.Client")
    @patch.dict("os.environ", {"GOOGLE_API_KEY": "fake_test_key"})
    def test_timeout_handled_gracefully(self, mock_client_cls):
        """When Gemini call times out, returns safe vision_unavailable status."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = TimeoutError("Request timed out after 30 seconds")
        mock_client_cls.return_value = mock_client

        result = analyze_crop_image_bytes(VALID_JPEG, "image/jpeg", "cotton_leaf.jpg")

        assert result["status"] == "vision_unavailable"
        assert "timed out" in result["message"].lower()
        assert "safety_note" in result

    @patch("google.genai.Client")
    @patch.dict("os.environ", {"GOOGLE_API_KEY": "fake_test_key"})
    def test_model_fallback_on_unavailable_primary(self, mock_client_cls):
        """When primary model fails with 503 / 404, service falls back to next candidate."""
        mock_response = MagicMock()
        mock_response.text = json.dumps({"visible_plant_parts": ["leaf"]})

        mock_client = MagicMock()
        # First call fails (e.g. 503 Service Unavailable), second call succeeds
        mock_client.models.generate_content.side_effect = [
            Exception("503 Service Unavailable: Model overloaded"),
            mock_response,
        ]
        mock_client_cls.return_value = mock_client

        result = analyze_crop_image_bytes(
            VALID_JPEG,
            "image/jpeg",
            "cotton_leaf.jpg",
            crop="cotton",
        )

        assert result["status"] == "analysis_completed"
        assert result["model_used"] in ["gemini-3.5-flash-lite", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-3.8-flash"]
        assert mock_client.models.generate_content.call_count == 2
