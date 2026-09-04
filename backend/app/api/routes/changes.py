from fastapi import APIRouter

from app.schemas.scoring import ChangeBundle
from app.services.change_bundle_service import build_change_bundle

router = APIRouter(prefix="/changes", tags=["changes"])


@router.get("/{symbol}", response_model=ChangeBundle)
async def get_change_bundle(symbol: str) -> ChangeBundle:
    return await build_change_bundle(symbol.upper())
