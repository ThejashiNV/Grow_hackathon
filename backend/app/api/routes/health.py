from fastapi import APIRouter

from app.core.chroma_client import chroma_status
from app.core.database import mongo_status
from app.core.redis_client import redis_status

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "services": {
            "mongodb": mongo_status(),
            "redis": redis_status(),
            "chroma": chroma_status(),
        },
    }
