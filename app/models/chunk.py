import uuid
from sqlalchemy import Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app.db.base import Base

# all-MiniLM-L6-v2 embedding modeli 384 o'lchamli vektor qaytaradi
EMBEDDING_DIM = 384


class Chunk(Base):
    """
    Hujjat bir necha kichik matn bo'lagiga (chunk) bo'linadi,
    har birining o'z vektor embeddingi bo'ladi - shu orqali
    RAG qidiruvi eng mos bo'lakni topadi.
    """
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)  # Hujjat ichidagi tartib raqami
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)

    document: Mapped["Document"] = relationship(back_populates="chunks")

    def __repr__(self) -> str:
        return f"<Chunk {self.chunk_index} of document {self.document_id}>"
