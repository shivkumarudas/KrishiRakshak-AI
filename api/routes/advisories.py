"""Agricultural advisory lookup endpoint."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from api.models import AdvisoryFilterRequest
from tools.advisory_tool import get_crop_advisory, check_agricultural_sources

router = APIRouter()


@router.get("/advisories")
async def get_advisories(
    crop: str = Query(
        ...,
        min_length=1,
        description="Crop name (soybean or cotton)",
    ),
    region: Optional[str] = Query(
        default=None,
        description="Optional region filter (e.g. Marathwada, Vidarbha, Western Maharashtra)",
    ),
    stage: Optional[str] = Query(
        default=None,
        description="Optional crop growth stage filter",
    ),
    verification_status: Optional[str] = Query(
        default=None,
        description="Optional verification status filter (e.g. verified_current_seasonal, verified_historical_reference)",
    ),
    include_historical: bool = Query(
        default=True,
        description="Whether to include historical reference bulletins",
    ),
    check_sources: bool = Query(
        default=False,
        description="Also check whether source URLs are reachable",
    ),
):
    """
    Look up agricultural advisories for a crop, prioritizing verified current
    guidance over historical baselines, with optional regional and stage filtering.
    """
    advisory = get_crop_advisory(
        crop=crop,
        region=region,
        stage=stage,
        verification_status=verification_status,
        include_historical=include_historical,
    )

    if "error" in advisory:
        raise HTTPException(
            status_code=422,
            detail=advisory["error"],
        )

    # Optionally check source reachability.
    if check_sources:
        source_check = check_agricultural_sources(crop)
        advisory["source_reachability"] = source_check

    return advisory


@router.post("/advisories")
async def filter_advisories(request: AdvisoryFilterRequest):
    """
    Look up agricultural advisories for a crop with optional growth stage,
    region, verification status filters, and source reachability verification.
    """
    advisory = get_crop_advisory(
        crop=request.crop,
        region=request.region,
        stage=request.stage,
        verification_status=request.verification_status,
        include_historical=request.include_historical,
    )

    if "error" in advisory:
        raise HTTPException(
            status_code=422,
            detail=advisory["error"],
        )

    # Optionally check source reachability
    if request.check_sources:
        source_check = check_agricultural_sources(request.crop)
        advisory["source_reachability"] = source_check

    return advisory
