from fastapi import APIRouter, Depends, HTTPException

from app.core.session import get_current_user_id
from app.repositories import watchlist_repository
from app.schemas.watchlist import AddStockRequest, Watchlist

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.get("", response_model=Watchlist)
async def get_watchlist(user_id: str = Depends(get_current_user_id)) -> Watchlist:
    return await watchlist_repository.get_watchlist(user_id)


@router.post("/stocks", response_model=Watchlist)
async def add_stock(body: AddStockRequest, user_id: str = Depends(get_current_user_id)) -> Watchlist:
    symbol = body.symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol is required")
    return await watchlist_repository.add_stock(user_id, symbol)


@router.delete("/stocks/{symbol}", response_model=Watchlist)
async def remove_stock(symbol: str, user_id: str = Depends(get_current_user_id)) -> Watchlist:
    return await watchlist_repository.remove_stock(user_id, symbol.upper())
