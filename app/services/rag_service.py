import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.chunk import Chunk
from app.models.document import Document
from app.services.embedding_service import embed_text
from app.services.llm_client import generate_answer
from app.schemas.chat import SourceChunk


async def answer_question(db: AsyncSession, owner_id: uuid.UUID, question: str, top_k: int = 3):
    """
    RAG asosiy oqimi:
    1. Savolni vektorga aylantirish
    2. pgvector orqali eng o'xshash bo'laklarni topish (faqat shu foydalanuvchining hujjatlaridan)
    3. Topilgan bo'laklarni LLM'ga context sifatida berib, javob generatsiya qilish
    """
    question_embedding = embed_text(question)

    # cosine_distance 0 (aynan bir xil) dan 2 (butunlay qarama-qarshi) gacha bo'ladi.
    # Buni o'qish oson bo'lgan "o'xshashlik" (1 = aynan mos, 0 = mos emas) ga aylantiramiz.
    distance_col = Chunk.embedding.cosine_distance(question_embedding).label("distance")

    result = await db.execute(
        select(Chunk, Document.filename, distance_col)
        .join(Document, Chunk.document_id == Document.id)
        .where(Document.owner_id == owner_id)
        .order_by(distance_col)
        .limit(top_k)
    )
    rows = result.all()

    if not rows:
        return "Sizda hali hujjat yuklanmagan yoki mos ma'lumot topilmadi.", []

    context_chunks = [chunk.content for chunk, _, _ in rows]
    answer = await generate_answer(question, context_chunks)

    sources = [
        SourceChunk(
            document_filename=filename,
            content=chunk.content[:200],
            similarity_score=round(1 - distance, 4),
        )
        for chunk, filename, distance in rows
    ]

    return answer, sources
