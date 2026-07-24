import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.document import DocumentStatus


class DocumentCreate(BaseModel):
    """Yangi hujjat yuklash uchun kiruvchi ma'lumot"""
    filename: str
    content: str


class DocumentResponse(BaseModel):
    """Hujjat haqida qaytariladigan ma'lumot (matn tarkibisiz - katta bo'lishi mumkin)"""
    id: uuid.UUID
    filename: str
    status: DocumentStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(DocumentResponse):
    """Bitta hujjatni ko'rishda - to'liq matn bilan"""
    content: str
