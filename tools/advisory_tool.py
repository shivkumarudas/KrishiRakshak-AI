"""Agricultural Advisory Knowledge Base and Source Verification Tool.

Manages verified agricultural advisories and official institutional sources for
Maharashtra crops (Soybean and Cotton), enforcing strict separation between
network reachability and content verification.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import requests
from strands import tool

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ADVISORY_FILE = PROJECT_ROOT / "data" / "crop_advisories.json"

SUPPORTED_CROPS = ("soybean", "cotton")


def _normalize_advisory_record(raw: dict, default_crop: str, default_region: str) -> dict:
    """
    Ensure advisory record conforms strictly to the 12-field schema,
    keeping missing values explicitly unknown rather than inventing them,
    while retaining compatibility aliases.
    """
    source_id = raw.get("source_id") or raw.get("id") or "Unknown"
    source_name = (
        raw.get("source_name")
        or raw.get("issuing_authority")
        or raw.get("name")
        or "Unknown Source"
    )
    official_url = (
        raw.get("official_url")
        or raw.get("official_source_url")
        or raw.get("url")
        or "Unknown"
    )
    crop = raw.get("crop") or default_crop
    region = raw.get("region") or default_region
    advisory_title = raw.get("advisory_title") or raw.get("title") or "Unknown Advisory"
    publication_date = raw.get("publication_date") or "Unknown"
    validity_period = raw.get("validity_period") or "Unknown"
    advisory_text = (
        raw.get("advisory_text")
        or raw.get("summary")
        or raw.get("extracted_advisory_text")
        or raw.get("purpose")
        or "Unknown"
    )
    last_checked_at = (
        raw.get("last_checked_at")
        or raw.get("last_verification_date")
        or "Unknown"
    )
    content_verification_status = (
        raw.get("content_verification_status")
        or raw.get("verification_status")
        or raw.get("source_status")
        or "unverified_portal_only"
    )
    source_type = raw.get("source_type") or raw.get("type") or "official_institution"

    # Assemble normalized dictionary with both canonical keys and backward-compatible aliases
    return {
        # Canonical 12-field data model
        "source_id": source_id,
        "source_name": source_name,
        "official_url": official_url,
        "crop": crop,
        "region": region,
        "advisory_title": advisory_title,
        "publication_date": publication_date,
        "validity_period": validity_period,
        "advisory_text": advisory_text,
        "last_checked_at": last_checked_at,
        "content_verification_status": content_verification_status,
        "source_type": source_type,
        # Backward-compatible fields for existing components and tests
        "id": source_id,
        "title": advisory_title,
        "name": source_name,
        "issuing_authority": source_name,
        "url": official_url,
        "official_source_url": official_url,
        "summary": advisory_text,
        "verification_status": content_verification_status,
        "last_verification_date": last_checked_at,
        "source_status": content_verification_status,
        "applicable_stage": raw.get("applicable_stage"),
        "precautions": raw.get("precautions"),
        "field_action": raw.get("field_action"),
        "is_historical": (
            content_verification_status == "verified_historical_reference"
            or "historical" in str(validity_period).lower()
            or "historical" in str(publication_date).lower()
        ),
    }


def _calculate_advisory_priority(adv: dict, requested_region: Optional[str]) -> int:
    """
    Calculate sorting priority (lower integer = higher priority):
    1. Verified current seasonal guidance directly matching the requested region.
    2. Verified current seasonal guidance for Maharashtra / Central Zone.
    3. Other verified current seasonal guidance.
    4. Unverified portal references.
    5. Historical reference guidance (always prioritized last).
    """
    status = adv.get("content_verification_status", "")
    adv_region = adv.get("region", "").lower()
    is_hist = adv.get("is_historical", False)

    if is_hist or status == "verified_historical_reference":
        return 100  # Historical references always at the bottom

    if status == "verified_current_seasonal":
        if requested_region and requested_region.strip().lower() in adv_region:
            return 1  # Direct regional match
        if "entire maharashtra" in adv_region or "maharashtra" in adv_region:
            return 2  # State-wide match
        return 3

    return 50  # Other / unverified


@tool
def get_crop_advisory(
    crop: str,
    region: Optional[str] = None,
    stage: Optional[str] = None,
    verification_status: Optional[str] = None,
    include_historical: bool = True,
) -> dict:
    """
    Look up verified agricultural advisories and institutional sources.

    Args:
        crop: Crop name (soybean or cotton).
        region: Optional region filter (e.g., Marathwada, Vidarbha, Western Maharashtra).
        stage: Optional crop growth stage filter.
        verification_status: Optional verification status filter.
        include_historical: Whether to include historical references (default True).

    Returns:
        Structured dictionary containing verified advisories prioritized by relevance,
        institutional sources, and critical verification disclaimers.
    """
    if not crop or not isinstance(crop, str) or not crop.strip():
        return {"error": "Currently supported crops are soybean and cotton."}

    crop_key = crop.strip().lower()
    if crop_key not in SUPPORTED_CROPS:
        return {"error": "Currently supported crops are soybean and cotton."}

    try:
        with ADVISORY_FILE.open("r", encoding="utf-8") as file:
            knowledge_base = json.load(file)
    except (OSError, json.JSONDecodeError):
        return {"error": "The crop advisory knowledge base could not be loaded."}

    crop_data = knowledge_base.get(crop_key)
    if not crop_data:
        return {"error": f"No advisory record found for {crop_key}."}

    default_crop_name = crop_data.get("display_name", crop_key.title())
    default_region = crop_data.get("region", "Maharashtra, India")

    raw_advisories = crop_data.get("advisories", [])
    raw_sources = crop_data.get("sources", [])

    # Normalize all advisories to the strict 12-field schema
    normalized_advisories = [
        _normalize_advisory_record(adv, default_crop_name, default_region)
        for adv in raw_advisories
    ]
    normalized_sources = [
        _normalize_advisory_record(src, default_crop_name, default_region)
        for src in raw_sources
    ]

    filtered_advisories = normalized_advisories

    # 1. Filter by Region if provided
    if region and region.strip():
        r_clean = region.strip().lower()
        filtered_advisories = [
            adv for adv in filtered_advisories
            if r_clean in adv["region"].lower()
            or "entire maharashtra" in adv["region"].lower()
            or (r_clean == "maharashtra" and "maharashtra" in adv["region"].lower())
        ]

    # 2. Filter by Growth Stage if provided
    if stage and stage.strip():
        s_clean = stage.strip().lower()
        filtered_advisories = [
            adv for adv in filtered_advisories
            if (adv.get("applicable_stage") and s_clean in adv["applicable_stage"].lower())
            or s_clean in adv["advisory_title"].lower()
            or s_clean in adv["advisory_text"].lower()
        ]

    # 3. Filter by Verification Status if provided
    if verification_status and verification_status.strip():
        v_clean = verification_status.strip().lower()
        filtered_advisories = [
            adv for adv in filtered_advisories
            if v_clean in adv["content_verification_status"].lower()
            or (v_clean == "verified" and "verified" in adv["content_verification_status"].lower())
            or (v_clean == "historical" and adv.get("is_historical"))
        ]

    # 4. Exclude historical if requested
    if not include_historical:
        filtered_advisories = [
            adv for adv in filtered_advisories if not adv.get("is_historical")
        ]

    # 5. Prioritize by relevance and freshness
    filtered_advisories.sort(key=lambda a: _calculate_advisory_priority(a, region))

    if not filtered_advisories:
        return {
            "crop": default_crop_name,
            "region": region or default_region,
            "status": "no_verified_advisories_available",
            "message": (
                "No verified crop recommendations match the specified criteria. "
                "The following official institutional references may provide guidance. "
                "Verify their seasonal dates and local applicability before adopting."
            ),
            "advisories": [],
            "sources": normalized_sources,
            "safety_note": (
                "Do not apply chemical doses from historical advisories. "
                "Consult your local Krishi Vigyan Kendra (KVK) or Taluka Agriculture Officer."
            ),
        }

    return {
        "crop": default_crop_name,
        "region": region or default_region,
        "status": "advisories_available",
        "advisories": filtered_advisories,
        "sources": normalized_sources,
        "safety_note": (
            "Check advisory dates, crop stage, and regional applicability before following any guidance. "
            "A reachable link or official source does NOT prove that an advisory is current for this season. "
            "Never adopt chemical prescriptions from outdated or historical bulletins."
        ),
        "note": (
            "Check advisory dates, crop stage, and regional applicability "
            "before following any recommendation. A reachable link does not "
            "prove that an advisory is current."
        ),
    }


@tool
def check_agricultural_sources(crop: str) -> dict:
    """
    Check whether registered agricultural reference pages and official portals are reachable.

    CRITICAL INVARIANT:
    Explicitly separates network reachability from content verification.
    A reachable HTTP 200 response confirms that the server is online, but does NOT
    verify that the advisory content is current, seasonal, or applicable to a specific field.
    """
    if not crop or not isinstance(crop, str) or not crop.strip():
        return {"error": "Currently supported crops are soybean and cotton."}

    crop_key = crop.strip().lower()
    if crop_key not in SUPPORTED_CROPS:
        return {"error": "Currently supported crops are soybean and cotton."}

    try:
        with ADVISORY_FILE.open("r", encoding="utf-8") as file:
            knowledge_base = json.load(file)
    except (OSError, json.JSONDecodeError):
        return {"error": "Unable to load the agricultural source catalogue."}

    crop_data = knowledge_base.get(crop_key)
    if not crop_data:
        return {"error": f"No data found for {crop_key}."}

    default_crop_name = crop_data.get("display_name", crop_key.title())
    default_region = crop_data.get("region", "Maharashtra, India")

    raw_sources = crop_data.get("sources", [])
    results = []

    check_timestamp = datetime.now().astimezone().isoformat(timespec="seconds")

    for raw in raw_sources:
        normalized = _normalize_advisory_record(raw, default_crop_name, default_region)
        url = normalized["official_url"]

        source_meta = {
            **normalized,
            "checked_at": check_timestamp,
            "last_checked_at": check_timestamp,
            "redirected": False,
            "final_url": url,
        }

        # If URL is missing or unknown
        if not url or url == "Unknown" or not url.startswith("http"):
            results.append({
                **source_meta,
                "reachable": False,
                "http_status": None,
                "note": "Official URL is unknown or not configured for automated reachability checks.",
            })
            continue

        try:
            response = requests.get(
                url,
                timeout=10,
                headers={"User-Agent": "KrishiRakshakAI/1.0 (Agricultural Safety Verification)"},
                allow_redirects=True,
            )

            was_redirected = len(response.history) > 0
            final_url = response.url if was_redirected else url

            results.append({
                **source_meta,
                "http_status": response.status_code,
                "reachable": response.ok,
                "redirected": was_redirected,
                "final_url": final_url,
                "note": (
                    f"Portal responded with HTTP {response.status_code}. "
                    "Network reachability confirms server availability, but does NOT "
                    "verify that publication date is current or applicable to your field."
                ),
            })

        except requests.Timeout:
            results.append({
                **source_meta,
                "reachable": False,
                "http_status": None,
                "error_type": "timeout",
                "note": "Connection timed out while contacting institutional server.",
            })

        except requests.RequestException as req_err:
            results.append({
                **source_meta,
                "reachable": False,
                "http_status": None,
                "error_type": type(req_err).__name__,
                "note": "Could not connect to this institutional page during reachability check.",
            })

    return {
        "crop": default_crop_name,
        "checked_at": check_timestamp,
        "sources": results,
        "warning": (
            "A reachable page is not proof of a current or applicable "
            "agricultural recommendation. Verify seasonal dates and local applicability."
        ),
        "safety_principle": (
            "Network reachability and content verification are separate. "
            "Never assume guidance is current for this season merely because the portal is online."
        ),
    }
