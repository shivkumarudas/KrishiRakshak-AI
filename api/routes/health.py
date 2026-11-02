"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Return the API health status."""

    return {
        "status": "ok",
        "service": "KrishiRakshak AI",
        "version": "1.0.0",
    }
