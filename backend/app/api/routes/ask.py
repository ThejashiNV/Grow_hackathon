from fastapi import APIRouter

from app.schemas.rag import AskRequest, AskResponse
from app.services.rag_service import ask as ask_service

router = APIRouter(tags=["rag"])


@router.post("/ask", response_model=AskResponse)
async def ask(body: AskRequest) -> AskResponse:
    return await ask_service(body.symbol.upper(), body.question)
