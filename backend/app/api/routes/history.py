from fastapi import APIRouter, Depends, Query

from app.core.session import get_current_user_id
from app.repositories import history_repository
from app.schemas.history import HistoryResponse

router = APIRouter(tags=["history"])


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    filter: str = Query("all", pattern="^(all|today|seen|unseen)$"),
    user_id: str = Depends(get_current_user_id),
) -> HistoryResponse:
    entries = await history_repository.get_history(user_id, filter_mode=filter)
    total = await history_repository.count_history(user_id)
    return HistoryResponse(entries=entries, total=total)
