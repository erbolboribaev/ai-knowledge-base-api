import uuid
import base64
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentDetailResponse
from app.workers.tasks import process_document_task
from app.services.llm_client import describe_image

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    document_data: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Yangi hujjat yuklaydi. Hujjat darhol PENDING holatida saqlanadi,
    so'ng Celery'ga fon vazifasi yuboriladi - bo'laklarga bo'lish va
    embedding yaratish asinxron ravishda amalga oshiriladi, foydalanuvchi
    darhol javob oladi (kutmaydi).
    """
    document = Document(
        owner_id=current_user.id,
        filename=document_data.filename,
        content=document_data.content,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Fon vazifasini navbatga qo'shish (Celery worker uni fonda bajaradi)
    process_document_task.delay(str(document.id))

    return document


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Joriy foydalanuvchining barcha hujjatlari ro'yxati"""
    result = await db.execute(
        select(Document).where(Document.owner_id == current_user.id).order_by(Document.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bitta hujjatni to'liq matni bilan ko'rish - faqat egasi ko'ra oladi"""
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Hujjat topilmadi")
    if document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bu hujjatga ruxsatingiz yo'q")

    return document


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hujjatni o'chiradi - faqat egasi o'chira oladi. Bog'liq chunk'lar ham avtomatik o'chadi (cascade)."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Hujjat topilmadi")
    if document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bu hujjatga ruxsatingiz yo'q")

    await db.delete(document)
    await db.commit()


@router.post("/from-image", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_image_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Rasm/skrinshot yuklaydi, Groq vizual modeli orqali undagi matn va
    tavsifni ajratib oladi, keyin uni oddiy hujjat sifatida saqlaydi -
    shundan keyin xuddi matnli hujjat kabi bo'laklarga bo'linib, RAG uchun
    embedding yaratiladi.
    """
    allowed_types = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type: {file.content_type}. Use PNG, JPEG, or WEBP.",
        )

    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 10MB).")

    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    try:
        extracted_text = await describe_image(base64_image, mime_type=file.content_type)
    except Exception:
        raise HTTPException(status_code=502, detail="Could not process image with AI model.")

    if not extracted_text:
        raise HTTPException(status_code=422, detail="No content could be extracted from image.")

    document = Document(
        owner_id=current_user.id,
        filename=file.filename or "screenshot.png",
        content=extracted_text,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    process_document_task.delay(str(document.id))

    return document
