from fastapi import APIRouter

from app.core.config import get_settings
from app.services.demo_data import get_demo_scenarios

router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("/scenarios")
async def list_scenarios() -> dict:
    settings = get_settings()
    return {
        "demo_mode": settings.demo_mode,
        "scenarios": get_demo_scenarios() if settings.demo_mode else [],
    }
