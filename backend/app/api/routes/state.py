from fastapi import APIRouter, Depends

from app.core.session import get_current_user_id
from app.repositories import stock_state_repository
from app.schemas.user_state import StockState
from app.services.change_bundle_service import build_change_bundle

router = APIRouter(prefix="/stocks", tags=["state"])


@router.post("/{symbol}/seen", response_model=StockState)
async def mark_seen(symbol: str, user_id: str = Depends(get_current_user_id)) -> StockState:
    symbol = symbol.upper()
    bundle = await build_change_bundle(symbol)
    return await stock_state_repository.mark_seen(
        user_id=user_id,
        symbol=symbol,
        price=bundle.price,
        volume=bundle.volume,
        score=bundle.attention_score,
        event_ids=[e.event_id for e in bundle.events],
    )
