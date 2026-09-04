from fastapi import APIRouter, Depends

from app.core.session import get_current_user_id
from app.schemas.rag import AskRequest, AskResponse
from app.services.rag_service import ask as ask_service

router = APIRouter(tags=["rag"])


@router.post("/ask", response_model=AskResponse)
async def ask(body: AskRequest, user_id: str = Depends(get_current_user_id)) -> AskResponse:
    return await ask_service(body.symbol.upper(), body.question, user_id=user_id)
