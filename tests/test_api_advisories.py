"""Tests for agricultural advisory API endpoints."""

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestAdvisoriesEndpoint:
    """Tests for GET /api/advisories."""

    def test_get_advisories_soybean_success(self):
        """Supported crop soybean returns 200 with source references and normalized fields."""
        response = client.get("/api/advisories?crop=soybean")
        assert response.status_code == 200
        data = response.json()
        assert data["crop"] == "Soybean"
        assert "sources" in data
        assert isinstance(data["sources"], list)
        assert len(data.get("advisories", [])) > 0
        first_adv = data["advisories"][0]
        # Verify 12-field schema
        assert "source_id" in first_adv
        assert "source_name" in first_adv
        assert "official_url" in first_adv
        assert "crop" in first_adv
        assert "region" in first_adv
        assert "advisory_title" in first_adv
        assert "publication_date" in first_adv
        assert "validity_period" in first_adv
        assert "advisory_text" in first_adv
        assert "last_checked_at" in first_adv
        assert "content_verification_status" in first_adv
        assert "source_type" in first_adv

    def test_get_advisories_cotton_success(self):
        """Supported crop cotton returns 200 with source references."""
        response = client.get("/api/advisories?crop=cotton")
        assert response.status_code == 200
        data = response.json()
        assert data["crop"] == "Cotton"
        assert "sources" in data

    def test_get_advisories_with_region_filter(self):
        """GET /api/advisories?crop=cotton&region=Vidarbha returns Vidarbha / statewide advisories."""
        response = client.get("/api/advisories?crop=cotton&region=Vidarbha")
        assert response.status_code == 200
        data = response.json()
        for adv in data.get("advisories", []):
            region_str = adv.get("region", "").lower()
            assert "vidarbha" in region_str or "maharashtra" in region_str

    def test_get_advisories_unsupported_crop(self):
        """Unsupported crop returns 422 error."""
        response = client.get("/api/advisories?crop=wheat")
        assert response.status_code == 422
        assert "soybean and cotton" in response.json()["detail"].lower()

    @patch("api.routes.advisories.check_agricultural_sources")
    def test_get_advisories_with_source_check(self, mock_check):
        """Passing check_sources=true includes reachability check."""
        mock_check.return_value = {
            "crop": "Soybean",
            "checked_at": "2026-10-26T18:00:00+05:30",
            "sources": [
                {
                    "source_name": "ICAR",
                    "official_url": "https://example.com",
                    "reachable": True,
                    "content_verification_status": "verified_current_seasonal",
                }
            ],
            "warning": "Reachable does not prove current",
        }

        response = client.get("/api/advisories?crop=soybean&check_sources=true")
        assert response.status_code == 200
        data = response.json()
        assert "source_reachability" in data
        assert data["source_reachability"]["sources"][0]["reachable"] is True


class TestPostAdvisoriesEndpoint:
    """Tests for POST /api/advisories."""

    def test_post_advisories_soybean_success(self):
        """POST with valid soybean returns 200 and advisory records."""
        payload = {"crop": "soybean"}
        response = client.post("/api/advisories", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["crop"] == "Soybean"
        assert len(data.get("advisories", [])) > 0

    def test_post_advisories_cotton_success(self):
        """POST with valid cotton returns 200 and advisory records."""
        payload = {"crop": "cotton"}
        response = client.post("/api/advisories", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["crop"] == "Cotton"
        assert len(data.get("advisories", [])) > 0

    def test_post_advisories_with_stage_filter(self):
        """POST with stage filter narrows advisory records."""
        payload = {"crop": "soybean", "stage": "Sowing"}
        response = client.post("/api/advisories", json=payload)
        assert response.status_code == 200
        data = response.json()
        for adv in data.get("advisories", []):
            combined_text = f"{adv.get('applicable_stage', '')} {adv.get('title', '')} {adv.get('summary', '')}".lower()
            assert "sowing" in combined_text

    def test_post_advisories_with_verification_filter(self):
        """POST with verification_status filters historical vs current."""
        payload = {
            "crop": "soybean",
            "verification_status": "verified_current_seasonal",
        }
        response = client.post("/api/advisories", json=payload)
        assert response.status_code == 200
        data = response.json()
        for adv in data.get("advisories", []):
            assert adv["content_verification_status"] == "verified_current_seasonal"

    def test_post_advisories_exclude_historical(self):
        """POST with include_historical=false excludes historical records."""
        payload = {
            "crop": "cotton",
            "include_historical": False,
        }
        response = client.post("/api/advisories", json=payload)
        assert response.status_code == 200
        data = response.json()
        for adv in data.get("advisories", []):
            assert adv.get("is_historical") is False

    def test_post_advisories_unsupported_crop(self):
        """POST with unsupported crop returns 422."""
        payload = {"crop": "sugarcane"}
        response = client.post("/api/advisories", json=payload)
        assert response.status_code == 422
        assert "soybean and cotton" in response.json()["detail"].lower()

    def test_post_advisories_missing_crop(self):
        """POST missing crop field returns 422 validation error."""
        payload = {"stage": "vegetative"}
        response = client.post("/api/advisories", json=payload)
        assert response.status_code == 422

    @patch("api.routes.advisories.check_agricultural_sources")
    def test_post_advisories_with_source_check(self, mock_check):
        """POST with check_sources=true returns source reachability."""
        mock_check.return_value = {
            "crop": "Cotton",
            "checked_at": "2026-10-26T18:00:00+05:30",
            "sources": [{"name": "CICR", "url": "https://example.com", "reachable": True}],
            "warning": "Reachable does not prove current",
        }
        payload = {"crop": "cotton", "check_sources": True}
        response = client.post("/api/advisories", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "source_reachability" in data
        assert data["source_reachability"]["sources"][0]["reachable"] is True
