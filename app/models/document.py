import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class DocumentStatus(str, PyEnum):
    """Hujjatning qayta ishlanish holati (fon vazifasi bilan bog'liq)"""
    PENDING = "pending"        # Yuklandi, hali qayta ishlanmagan
    PROCESSING = "processing"  # Celery worker hozir bo'laklarga bo'lib, embedding yaratmoqda
    COMPLETED = "completed"    # Tayyor, qidiruv uchun ishlatilishi mumkin
    FAILED = "failed"          # Xatolik yuz berdi


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # Xom matn
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus), default=DocumentStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Bitta hujjat -> ko'p bo'lak (chunk) munosabati
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Document {self.filename} ({self.status})>"
