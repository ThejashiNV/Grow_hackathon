from fastapi import APIRouter, Depends

from app.core.session import get_current_user_id
from app.schemas.attention import AttentionResponse
from app.services.attention_service import build_attention_feed

router = APIRouter(tags=["attention"])


@router.get("/attention", response_model=AttentionResponse)
async def get_attention(user_id: str = Depends(get_current_user_id)) -> AttentionResponse:
    return await build_attention_feed(user_id)
