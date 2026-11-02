"""Tests for tools/advisory_tool.py — get_crop_advisory and check_agricultural_sources."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import requests
from tools.advisory_tool import (
    get_crop_advisory,
    check_agricultural_sources,
    ADVISORY_FILE,
)


# --------------------------------------------------
# Sample knowledge bases for testing
# --------------------------------------------------

SAMPLE_KB_NO_ADVISORIES = {
    "soybean": {
        "display_name": "Soybean",
        "region": "Maharashtra, India",
        "status": "source_catalog_only",
        "advisories": [],
        "sources": [
            {
                "source_id": "SRC-01",
                "name": "ICAR Soybean Research",
                "source_name": "ICAR Soybean Research",
                "type": "official_research_institute",
                "source_type": "icar_institute",
                "url": "https://example.com/soybean",
                "official_url": "https://example.com/soybean",
                "crop": "Soybean",
                "region": "Maharashtra",
                "publication_date": "2026",
                "validity_period": "Kharif 2026",
                "source_status": "active_official_portal",
                "content_verification_status": "verified_current_seasonal",
                "last_verification_date": "2026-10-26",
                "last_checked_at": "2026-10-26T10:00:00+05:30",
                "purpose": "Soybean research bulletins",
            }
        ],
    },
    "cotton": {
        "display_name": "Cotton",
        "region": "Maharashtra, India",
        "status": "source_catalog_only",
        "advisories": [],
        "sources": [],
    },
}

SAMPLE_KB_WITH_ADVISORIES = {
    "soybean": {
        "display_name": "Soybean",
        "region": "Maharashtra, India",
        "advisories": [
            {
                "source_id": "SOY-01",
                "id": "SOY-01",
                "advisory_title": "Kharif 2026 soybean sowing guidance",
                "title": "Kharif 2026 soybean sowing guidance",
                "source_name": "ICAR",
                "issuing_authority": "ICAR",
                "crop": "Soybean",
                "region": "Marathwada, Maharashtra",
                "applicable_stage": "Sowing",
                "publication_date": "2026-06",
                "validity_period": "Kharif 2026",
                "content_verification_status": "verified_current_seasonal",
                "verification_status": "verified_official_guidance",
                "last_checked_at": "2026-10-26T10:00:00+05:30",
                "last_verification_date": "2026-10-26",
                "advisory_text": "Use certified seed varieties.",
                "summary": "Use certified seed varieties.",
            },
            {
                "source_id": "SOY-HIST-01",
                "id": "SOY-HIST-01",
                "advisory_title": "Historical 2024 Sowing Baseline",
                "title": "Historical 2024 Sowing Baseline",
                "source_name": "ICAR Central Zone",
                "issuing_authority": "ICAR Central Zone",
                "crop": "Soybean",
                "region": "Entire Maharashtra",
                "applicable_stage": "Sowing",
                "publication_date": "2024-06",
                "validity_period": "Kharif 2024 (Historical)",
                "content_verification_status": "verified_historical_reference",
                "verification_status": "historical_reference",
                "last_checked_at": "2026-10-26T10:00:00+05:30",
                "last_verification_date": "2026-10-26",
                "advisory_text": "Historical reference: check current season conditions.",
                "summary": "Historical reference: check current season conditions.",
            },
        ],
        "sources": [
            {
                "source_id": "SRC-01",
                "name": "ICAR Soybean Research",
                "source_name": "ICAR Soybean Research",
                "url": "https://example.com/soybean",
                "official_url": "https://example.com/soybean",
                "crop": "Soybean",
                "region": "Maharashtra",
                "publication_date": "2026",
                "validity_period": "Kharif 2026",
                "source_status": "active_official_portal",
                "content_verification_status": "verified_current_seasonal",
                "last_verification_date": "2026-10-26",
                "last_checked_at": "2026-10-26T10:00:00+05:30",
            }
        ],
    },
    "cotton": {
        "display_name": "Cotton",
        "region": "Maharashtra, India",
        "advisories": [],
        "sources": [],
    },
}


def _write_temp_kb(data):
    """Write a temporary knowledge base file and return its Path."""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    )
    json.dump(data, tmp)
    tmp.close()
    return Path(tmp.name)


# --------------------------------------------------
# get_crop_advisory tests
# --------------------------------------------------

class TestGetCropAdvisory:
    """Tests for the get_crop_advisory function."""

    @patch("tools.advisory_tool.ADVISORY_FILE")
    def test_no_advisories_returns_sources(self, mock_file):
        """When advisories list is empty, sources are still returned."""
        tmp_path = _write_temp_kb(SAMPLE_KB_NO_ADVISORIES)
        mock_file.__class__ = type(tmp_path)
        mock_file.open = tmp_path.open

        result = get_crop_advisory("soybean")

        assert result["status"] == "no_verified_advisories_available"
        assert result["crop"] == "Soybean"
        assert len(result["sources"]) == 1
        tmp_path.unlink(missing_ok=True)

    @patch("tools.advisory_tool.ADVISORY_FILE")
    def test_with_advisories_returns_data(self, mock_file):
        """When advisories exist, they are returned with correct status."""
        tmp_path = _write_temp_kb(SAMPLE_KB_WITH_ADVISORIES)
        mock_file.__class__ = type(tmp_path)
        mock_file.open = tmp_path.open

        result = get_crop_advisory("soybean")

        assert result["status"] == "advisories_available"
        assert len(result["advisories"]) == 2
        assert result["advisories"][0]["issuing_authority"] == "ICAR"
        tmp_path.unlink(missing_ok=True)

    def test_unsupported_crop(self):
        """An unsupported crop returns an error."""
        result = get_crop_advisory("wheat")
        assert "error" in result
        assert "soybean" in result["error"].lower() or "cotton" in result["error"].lower()

    @patch("tools.advisory_tool.ADVISORY_FILE")
    def test_missing_file(self, mock_file):
        """A missing knowledge base file returns an error."""
        mock_file.open.side_effect = OSError("File not found")

        result = get_crop_advisory("soybean")

        assert "error" in result
        assert "could not be loaded" in result["error"]

    @patch("tools.advisory_tool.ADVISORY_FILE")
    def test_corrupt_json(self, mock_file):
        """Corrupt JSON in the knowledge base returns an error."""
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        tmp.write("{corrupt json!!!")
        tmp.close()
        tmp_path = Path(tmp.name)
        mock_file.__class__ = type(tmp_path)
        mock_file.open = tmp_path.open

        result = get_crop_advisory("soybean")

        assert "error" in result
        tmp_path.unlink(missing_ok=True)

    def test_case_insensitive_crop(self):
        """Crop name matching is case-insensitive."""
        result = get_crop_advisory("COTTON")
        assert "error" not in result or "unsupported" not in result.get("error", "").lower()

    def test_none_or_non_string_crop_handled(self):
        """None or non-string crop inputs return error dictionary."""
        assert "error" in get_crop_advisory(None)
        assert "error" in get_crop_advisory(12345)
        assert "error" in check_agricultural_sources(None)
        assert "error" in check_agricultural_sources(12345)

    @patch("tools.advisory_tool.ADVISORY_FILE")
    def test_filter_by_region(self, mock_file):
        """Regional filtering matches specific region or statewide advisories."""
        tmp_path = _write_temp_kb(SAMPLE_KB_WITH_ADVISORIES)
        mock_file.__class__ = type(tmp_path)
        mock_file.open = tmp_path.open

        result = get_crop_advisory("soybean", region="Marathwada")
        assert result["status"] == "advisories_available"
        # Both SOY-01 (Marathwada) and SOY-HIST-01 (Entire Maharashtra) match
        assert len(result["advisories"]) == 2
        assert result["advisories"][0]["source_id"] == "SOY-01"

        tmp_path.unlink(missing_ok=True)

    @patch("tools.advisory_tool.ADVISORY_FILE")
    def test_filter_by_verification_status(self, mock_file):
        """Filtering by verification status separates current from historical."""
        tmp_path = _write_temp_kb(SAMPLE_KB_WITH_ADVISORIES)
        mock_file.__class__ = type(tmp_path)
        mock_file.open = tmp_path.open

        current_res = get_crop_advisory("soybean", verification_status="verified_current_seasonal")
        assert len(current_res["advisories"]) == 1
        assert current_res["advisories"][0]["source_id"] == "SOY-01"

        hist_res = get_crop_advisory("soybean", verification_status="historical")
        assert len(hist_res["advisories"]) == 1
        assert hist_res["advisories"][0]["source_id"] == "SOY-HIST-01"

        tmp_path.unlink(missing_ok=True)

    @patch("tools.advisory_tool.ADVISORY_FILE")
    def test_exclude_historical(self, mock_file):
        """Setting include_historical=False excludes historical bulletins."""
        tmp_path = _write_temp_kb(SAMPLE_KB_WITH_ADVISORIES)
        mock_file.__class__ = type(tmp_path)
        mock_file.open = tmp_path.open

        result = get_crop_advisory("soybean", include_historical=False)
        assert len(result["advisories"]) == 1
        assert result["advisories"][0]["source_id"] == "SOY-01"

        tmp_path.unlink(missing_ok=True)

    @patch("tools.advisory_tool.ADVISORY_FILE")
    def test_prioritization_verified_current_over_historical(self, mock_file):
        """Current seasonal verified advisories are prioritized ahead of historical."""
        tmp_path = _write_temp_kb(SAMPLE_KB_WITH_ADVISORIES)
        mock_file.__class__ = type(tmp_path)
        mock_file.open = tmp_path.open

        result = get_crop_advisory("soybean")
        advisories = result["advisories"]
        assert advisories[0]["content_verification_status"] == "verified_current_seasonal"
        assert advisories[-1]["content_verification_status"] == "verified_historical_reference"

        tmp_path.unlink(missing_ok=True)

    @patch("tools.advisory_tool.ADVISORY_FILE")
    def test_missing_fields_normalized_to_unknown(self, mock_file):
        """Incomplete advisory records populate missing fields with 'Unknown' instead of failing."""
        sparse_kb = {
            "soybean": {
                "display_name": "Soybean",
                "advisories": [
                    {
                        "source_id": "SPARSE-01",
                        "advisory_title": "Minimal advisory",
                    }
                ],
                "sources": [],
            }
        }
        tmp_path = _write_temp_kb(sparse_kb)
        mock_file.__class__ = type(tmp_path)
        mock_file.open = tmp_path.open

        result = get_crop_advisory("soybean")
        adv = result["advisories"][0]
        assert adv["source_id"] == "SPARSE-01"
        assert adv["source_name"] == "Unknown Source"
        assert adv["publication_date"] == "Unknown"
        assert adv["validity_period"] == "Unknown"

        tmp_path.unlink(missing_ok=True)


# --------------------------------------------------
# check_agricultural_sources tests
# --------------------------------------------------

class TestCheckAgriculturalSources:
    """Tests for the check_agricultural_sources function."""

    def test_unsupported_crop(self):
        """An unsupported crop returns an error."""
        result = check_agricultural_sources("rice")
        assert "error" in result

    @patch("tools.advisory_tool.requests.get")
    @patch("tools.advisory_tool.ADVISORY_FILE")
    def test_reachable_source_preserves_metadata(self, mock_file, mock_get):
        """A reachable source is reported correctly and metadata is preserved."""
        tmp_path = _write_temp_kb(SAMPLE_KB_NO_ADVISORIES)
        mock_file.__class__ = type(tmp_path)
        mock_file.open = tmp_path.open

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.history = []
        mock_get.return_value = mock_response

        result = check_agricultural_sources("soybean")

        assert "error" not in result
        src = result["sources"][0]
        assert src["reachable"] is True
        assert src["http_status"] == 200
        assert src["crop"] == "Soybean"
        assert src["region"] == "Maharashtra"
        assert src["source_status"] == "verified_current_seasonal"
        assert "warning" in result
        assert "reachable page is not proof" in result["warning"].lower()
        tmp_path.unlink(missing_ok=True)

    @patch("tools.advisory_tool.requests.get")
    @patch("tools.advisory_tool.ADVISORY_FILE")
    def test_reachability_does_not_modify_verification_status(self, mock_file, mock_get):
        """HTTP reachability must NOT change unverified content to verified."""
        unverified_kb = {
            "soybean": {
                "display_name": "Soybean",
                "sources": [
                    {
                        "source_id": "PORTAL-01",
                        "name": "General Portal",
                        "url": "https://example.com/portal",
                        "content_verification_status": "unverified_portal_only",
                    }
                ],
            }
        }
        tmp_path = _write_temp_kb(unverified_kb)
        mock_file.__class__ = type(tmp_path)
        mock_file.open = tmp_path.open

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.history = []
        mock_get.return_value = mock_response

        result = check_agricultural_sources("soybean")
        src = result["sources"][0]
        assert src["reachable"] is True
        # Content verification status remains unverified_portal_only
        assert src["content_verification_status"] == "unverified_portal_only"

        tmp_path.unlink(missing_ok=True)

    @patch("tools.advisory_tool.requests.get")
    @patch("tools.advisory_tool.ADVISORY_FILE")
    def test_unreachable_source(self, mock_file, mock_get):
        """An unreachable source is reported correctly with preserved metadata."""
        tmp_path = _write_temp_kb(SAMPLE_KB_NO_ADVISORIES)
        mock_file.__class__ = type(tmp_path)
        mock_file.open = tmp_path.open

        mock_get.side_effect = requests.ConnectionError("Cannot connect")

        result = check_agricultural_sources("soybean")

        assert result["sources"][0]["reachable"] is False
        assert result["sources"][0]["source_status"] == "verified_current_seasonal"
        tmp_path.unlink(missing_ok=True)

    @patch("tools.advisory_tool.requests.get")
    @patch("tools.advisory_tool.ADVISORY_FILE")
    def test_timeout_handled_gracefully(self, mock_file, mock_get):
        """A timeout during source reachability check is handled safely."""
        tmp_path = _write_temp_kb(SAMPLE_KB_NO_ADVISORIES)
        mock_file.__class__ = type(tmp_path)
        mock_file.open = tmp_path.open

        mock_get.side_effect = requests.Timeout("Connection timed out after 10s")

        result = check_agricultural_sources("soybean")

        src = result["sources"][0]
        assert src["reachable"] is False
        assert src["error_type"] == "timeout"
        assert "timed out" in src["note"].lower()
        tmp_path.unlink(missing_ok=True)

    @patch("tools.advisory_tool.requests.get")
    @patch("tools.advisory_tool.ADVISORY_FILE")
    def test_redirect_tracked(self, mock_file, mock_get):
        """HTTP redirects are recorded in reachability output."""
        tmp_path = _write_temp_kb(SAMPLE_KB_NO_ADVISORIES)
        mock_file.__class__ = type(tmp_path)
        mock_file.open = tmp_path.open

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.history = [MagicMock(status_code=301)]
        mock_response.url = "https://example.com/soybean/redirected"
        mock_get.return_value = mock_response

        result = check_agricultural_sources("soybean")

        src = result["sources"][0]
        assert src["reachable"] is True
        assert src["redirected"] is True
        assert src["final_url"] == "https://example.com/soybean/redirected"
        tmp_path.unlink(missing_ok=True)

    @patch("tools.advisory_tool.ADVISORY_FILE")
    def test_missing_file(self, mock_file):
        """A missing knowledge base returns an error."""
        mock_file.open.side_effect = OSError("File not found")

        result = check_agricultural_sources("soybean")

        assert "error" in result


# --------------------------------------------------
# Real data file schema tests
# --------------------------------------------------

class TestRealKnowledgeBaseData:
    """Validate that the real crop_advisories.json file is intact and compliant."""

    def test_real_advisory_file_structure(self):
        """The actual data/crop_advisories.json has soybean, cotton, and guidance."""
        with ADVISORY_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        assert "soybean" in data
        assert "cotton" in data
        assert "source_guidance" in data

    def test_real_advisories_metadata(self):
        """Verified advisories contain all canonical 12 fields and backward-compatible fields."""
        with ADVISORY_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        for crop_key in ("soybean", "cotton"):
            advisories = data[crop_key].get("advisories", [])
            assert len(advisories) > 0, f"Expected verified advisories for {crop_key}"
            for adv in advisories:
                # 12-field standard schema
                assert "source_id" in adv
                assert "source_name" in adv
                assert "official_url" in adv
                assert "crop" in adv
                assert "region" in adv
                assert "advisory_title" in adv
                assert "publication_date" in adv
                assert "validity_period" in adv
                assert "advisory_text" in adv
                assert "last_checked_at" in adv
                assert "content_verification_status" in adv
                assert "source_type" in adv
                # Backward-compatibility aliases
                assert "title" in adv
                assert "issuing_authority" in adv
                assert "verification_status" in adv
                assert "last_verification_date" in adv

    def test_real_sources_metadata(self):
        """Sources contain official metadata conforming to the 12-field schema."""
        with ADVISORY_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        for crop_key in ("soybean", "cotton"):
            sources = data[crop_key].get("sources", [])
            assert len(sources) > 0
            for src in sources:
                assert "source_id" in src
                assert "source_name" in src
                assert "official_url" in src
                assert "crop" in src
                assert "region" in src
                assert "source_type" in src
                assert "content_verification_status" in src
                assert "last_checked_at" in src
                # Aliases
                assert "name" in src
                assert "url" in src
                assert "source_status" in src
                assert "last_verification_date" in src
