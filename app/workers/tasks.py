import asyncio
import uuid
from sqlalchemy import select

from app.workers.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.models.document import Document, DocumentStatus
from app.models.chunk import Chunk
from app.services.document_service import split_text_into_chunks
from app.services.embedding_service import embed_texts


async def _process_document(document_id: str):
    """
    Hujjatni qayta ishlaydi: matnni bo'laklarga bo'ladi, har biriga
    embedding yaratadi va bazaga saqlaydi. Xato yuz bersa, hujjat
    holatini FAILED qilib belgilaydi (jimgina yo'qolib qolmasin).
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Document).where(Document.id == uuid.UUID(document_id))
        )
        document = result.scalar_one_or_none()

        if not document:
            return

        try:
            document.status = DocumentStatus.PROCESSING
            await db.commit()

            chunks_text = split_text_into_chunks(document.content)

            if not chunks_text:
                document.status = DocumentStatus.FAILED
                await db.commit()
                return

            embeddings = embed_texts(chunks_text)

            for index, (chunk_text, embedding) in enumerate(zip(chunks_text, embeddings)):
                chunk = Chunk(
                    document_id=document.id,
                    content=chunk_text,
                    chunk_index=index,
                    embedding=embedding,
                )
                db.add(chunk)

            document.status = DocumentStatus.COMPLETED
            await db.commit()

        except Exception:
            document.status = DocumentStatus.FAILED
            await db.commit()
            raise


@celery_app.task(name="process_document")
def process_document_task(document_id: str):
    """
    Celery vazifasi sinxron bo'lishi shart, lekin bizning DB
    operatsiyalarimiz asinxron - shuning uchun asyncio.run() orqali
    asinxron funksiyani shu yerda ishga tushiramiz.
    """
    asyncio.run(_process_document(document_id))
