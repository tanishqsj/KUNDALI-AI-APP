from fastapi import APIRouter

router = APIRouter()


@router.get("/health", summary="Health check")
async def health_check():
    """
    Basic health check endpoint.
    """
    return {
        "status": "ok",
        "service": "kundali-ai",
    }
