import uuid
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.chunk import Chunk
from app.models.document import Document
from app.services.embedding_service import embed_text
from app.services.llm_client import generate_answer
from app.services.web_search_service import search_web
from app.schemas.chat import SourceChunk, WebSource

# Bundan past o'xshashlikdagi hujjat bo'laklari aloqasiz deb hisoblanadi
# va context'ga qo'shilmaydi (masalan, boshqa mavzudagi hujjatlar tasodifan
# eng yaqin natija sifatida tanlanib qolmasligi uchun).
MIN_SIMILARITY_THRESHOLD = 0.3


async def answer_question(
    db: AsyncSession,
    owner_id: uuid.UUID,
    question: str,
    top_k: int = 3,
    use_web_search: bool = False,
):
    """
    RAG asosiy oqimi, ixtiyoriy web qidiruv bilan boyitilgan:
    1. Savolni vektorga aylantirish
    2. pgvector orqali eng o'xshash hujjat bo'laklarini topish
    3. Juda past o'xshashlikdagi (aloqasiz) natijalarni chiqarib tashlash
    4. (Ixtiyoriy) DuckDuckGo/Tavily orqali internetdan qo'shimcha kontekst olish
    5. Barcha kontekstni LLM'ga berib, javob generatsiya qilish
    """
    question_embedding = embed_text(question)

    distance_col = Chunk.embedding.cosine_distance(question_embedding).label("distance")

    result = await db.execute(
        select(Chunk, Document.filename, distance_col)
        .join(Document, Chunk.document_id == Document.id)
        .where(Document.owner_id == owner_id)
        .order_by(distance_col)
        .limit(top_k)
    )
    rows = result.all()

    # Faqat minimal chegaradan yuqori o'xshashlikdagi natijalarni qoldiramiz
    relevant_rows = [
        (chunk, filename, distance)
        for chunk, filename, distance in rows
        if (1 - distance) >= MIN_SIMILARITY_THRESHOLD
    ]

    context_chunks = [chunk.content for chunk, _, _ in relevant_rows]
    sources = [
        SourceChunk(
            document_filename=filename,
            content=chunk.content[:200],
            similarity_score=round(1 - distance, 4),
        )
        for chunk, filename, distance in relevant_rows
    ]

    web_sources = []
    if use_web_search:
        web_results = await asyncio.to_thread(search_web, question, 3)
        for r in web_results:
            context_chunks.append(f"[Web: {r['title']}] {r['snippet']}")
            web_sources.append(WebSource(title=r["title"], url=r["url"], snippet=r["snippet"]))

    if not context_chunks:
        return "Sizda hali hujjat yuklanmagan yoki mos ma'lumot topilmadi.", [], []

    answer = await generate_answer(question, context_chunks)

    return answer, sources, web_sources
