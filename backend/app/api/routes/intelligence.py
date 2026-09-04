"""Market intelligence API routes."""

from fastapi import APIRouter, Query

from app.services.intelligence_service import get_stock_intelligence

router = APIRouter(tags=["intelligence"])


@router.get("/intelligence/{symbol}")
async def get_intelligence(
    symbol: str,
    refresh: bool = Query(False, description="Force refresh (bypass cache)"),
):
    return await get_stock_intelligence(symbol, skip_cache=refresh)
