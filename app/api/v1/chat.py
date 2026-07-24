from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_service import answer_question

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Foydalanuvchi savol beradi, tizim uning hujjatlaridan eng mos
    bo'lakni topib, LLM orqali javob generatsiya qiladi (RAG).
    """
    answer, sources = await answer_question(db, current_user.id, request.question)
    return ChatResponse(answer=answer, sources=sources)
