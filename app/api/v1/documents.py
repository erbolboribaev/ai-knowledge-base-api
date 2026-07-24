import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentDetailResponse
from app.workers.tasks import process_document_task

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
