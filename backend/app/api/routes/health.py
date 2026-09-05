from fastapi import APIRouter

from app.core.chroma_client import chroma_status
from app.core.config import get_settings
from app.core.database import mongo_status
from app.core.redis_client import redis_status

router = APIRouter()


def _gemini_status() -> dict:
    settings = get_settings()
    configured = bool(settings.gemini_api_key)
    result = {
        "configured": configured,
        "model": settings.gemini_model if configured else None,
    }
    if not configured:
        result["detail"] = "GEMINI_API_KEY not set in .env"
    return result


@router.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "demo_mode": get_settings().demo_mode,
        "services": {
            "mongodb": mongo_status(),
            "redis": redis_status(),
            "chroma": chroma_status(),
            "gemini": _gemini_status(),
        },
    }
