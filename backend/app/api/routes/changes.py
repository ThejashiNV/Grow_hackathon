import asyncio

from fastapi import APIRouter, Depends

from app.core.session import get_current_user_id
from app.repositories import watchlist_repository
from app.schemas.scoring import ChangeBundle
from app.services.change_bundle_service import build_change_bundle

router = APIRouter(prefix="/changes", tags=["changes"])


@router.get("", response_model=list[ChangeBundle])
async def list_changes(user_id: str = Depends(get_current_user_id)) -> list[ChangeBundle]:
    """Change bundles for the user's whole watchlist, unranked (no diff/sector-wide
    logic -- for that, use /api/attention). Useful for a raw per-stock view."""
    watchlist = await watchlist_repository.get_watchlist(user_id)
    symbols = [s.symbol for s in watchlist.stocks]
    if not symbols:
        return []
    return list(await asyncio.gather(*(build_change_bundle(sym) for sym in symbols)))


@router.get("/{symbol}", response_model=ChangeBundle)
async def get_change_bundle(symbol: str) -> ChangeBundle:
    return await build_change_bundle(symbol.upper())
