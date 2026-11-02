"""Tests for crop assessment and image analysis API endpoints."""

import io
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

VALID_JPEG = b"\xFF\xD8\xFF\xE0\x00\x10JFIF" + b"\x00" * 64


class TestCropAssessEndpoint:
    """Tests for POST /api/crops/assess."""

    def test_assess_crop_success_soybean(self):
        """Valid soybean assessment returns 200 with recorded details."""
        payload = {
            "crop": "soybean",
            "growth_stage": "flowering",
            "symptoms": "yellow spots on upper leaves",
            "field_pattern": "patches",
            "affected_part": "leaves",
            "symptom_duration": "3 days",
            "soil_moisture": "moist",
            "recent_rainfall": "light shower yesterday",
        }
        response = client.post("/api/crops/assess", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "assessment_recorded"
        assert data["crop"] == "Soybean"
        assert data["diagnosis"] is None
        assert data["chemical_recommendations"] == []
        assert "safety_note" in data

    def test_assess_crop_success_cotton(self):
        """Valid cotton assessment returns 200 with recorded details."""
        payload = {
            "crop": "cotton",
            "growth_stage": "boll development",
            "symptoms": "bollworm entrance holes",
            "field_pattern": "individual plants",
        }
        response = client.post("/api/crops/assess", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "assessment_recorded"
        assert data["crop"] == "Cotton"

    def test_assess_crop_extended_observations(self):
        """Extended observation fields are correctly captured."""
        payload = {
            "crop": "soybean",
            "growth_stage": "pod filling",
            "symptoms": ["yellowing", "wilting"],
            "affected_plant_parts": ["older leaves"],
            "field_pattern": "isolated patches",
            "symptom_duration": "a few days ago",
            "soil_moisture": "normal",
            "recent_rainfall_or_irrigation": "10 mm two days ago",
            "farmer_notes": "noticed in eastern low-lying area",
        }
        response = client.post("/api/crops/assess", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "assessment_recorded"
        assert data["observations"]["farmer_notes"] == "noticed in eastern low-lying area"
        assert "older leaves" in data["affected_plant_parts"]
        assert len(data.get("possible_explanations", [])) > 0

    def test_assess_crop_unsupported_crop(self):
        """Unsupported crop returns 422 Unprocessable Entity."""
        payload = {
            "crop": "sugarcane",
            "growth_stage": "tillering",
            "symptoms": "red rot signs",
        }
        response = client.post("/api/crops/assess", json=payload)
        assert response.status_code == 422
        assert "soybean and cotton" in response.json()["detail"].lower()

    def test_assess_crop_missing_symptoms(self):
        """Empty symptoms string returns 422."""
        payload = {
            "crop": "soybean",
            "growth_stage": "flowering",
            "symptoms": "",
        }
        response = client.post("/api/crops/assess", json=payload)
        assert response.status_code == 422

    def test_assess_crop_missing_growth_stage(self):
        """Empty growth_stage returns 422."""
        payload = {
            "crop": "soybean",
            "growth_stage": "",
            "symptoms": "wilting",
        }
        response = client.post("/api/crops/assess", json=payload)
        assert response.status_code == 422


class TestAnalyzeImageEndpoint:
    """Tests for POST /api/crops/analyze-image."""

    @patch("api.routes.crops.analyze_crop_image_bytes")
    def test_valid_image_upload_success(self, mock_analyze):
        """Valid JPEG image upload coordinates with image service."""
        mock_analyze.return_value = {
            "status": "analysis_completed",
            "model_used": "gemini-2.5-flash",
            "crop": "Soybean",
            "growth_stage": "flowering",
            "file_name": "leaf.jpg",
            "file_size_bytes": len(VALID_JPEG),
            "content_type": "image/jpeg",
            "analysis": "Visible yellowing on leaf margins.",
            "safety_note": "Visual assessment is not laboratory-confirmed.",
        }
        files = {
            "image": ("leaf.jpg", io.BytesIO(VALID_JPEG), "image/jpeg"),
        }
        data = {
            "crop": "soybean",
            "growth_stage": "flowering",
            "notes": "Yellow spots on upper leaves",
        }
        response = client.post("/api/crops/analyze-image", files=files, data=data)
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "analysis_completed"
        assert result["content_type"] == "image/jpeg"
        assert result["crop"] == "Soybean"
        assert "Visible yellowing" in result["analysis"]
        mock_analyze.assert_called_once()
        call_kwargs = mock_analyze.call_args[1]
        assert call_kwargs["crop"] == "soybean"
        assert call_kwargs["growth_stage"] == "flowering"
        assert call_kwargs["notes"] == "Yellow spots on upper leaves"

    def test_unsupported_crop_returns_422(self):
        """Uploading an image for an unsupported crop returns 422."""
        files = {
            "image": ("leaf.jpg", io.BytesIO(VALID_JPEG), "image/jpeg"),
        }
        data = {
            "crop": "rice",
        }
        response = client.post("/api/crops/analyze-image", files=files, data=data)
        assert response.status_code == 422
        assert "soybean and cotton" in response.json()["detail"].lower()

    def test_unsupported_file_type(self):
        """Unsupported file type returns 415 Unsupported Media Type."""
        files = {
            "image": ("document.pdf", io.BytesIO(b"%PDF-1.4 sample content"), "application/pdf"),
        }
        response = client.post("/api/crops/analyze-image", files=files)
        assert response.status_code == 415
        assert "unsupported" in response.json()["detail"].lower()

    def test_corrupted_image_magic_bytes(self):
        """Corrupted JPEG magic bytes returns 415."""
        fake_jpeg = b"FAKE_NOT_A_JPEG_HEADER" + b"\x00" * 30
        files = {
            "image": ("bad.jpg", io.BytesIO(fake_jpeg), "image/jpeg"),
        }
        response = client.post("/api/crops/analyze-image", files=files)
        assert response.status_code == 415
        assert "corrupted" in response.json()["detail"].lower()

    def test_empty_image_file(self):
        """Empty uploaded file returns 400 Bad Request."""
        files = {
            "image": ("empty.png", io.BytesIO(b""), "image/png"),
        }
        response = client.post("/api/crops/analyze-image", files=files)
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_oversized_image_file(self):
        """File exceeding size limit returns 413 Payload Too Large."""
        oversized_data = b"x" * (11 * 1024 * 1024)  # 11 MB
        files = {
            "image": ("huge.jpg", io.BytesIO(oversized_data), "image/jpeg"),
        }
        response = client.post("/api/crops/analyze-image", files=files)
        assert response.status_code == 413
        assert "too large" in response.json()["detail"].lower()
