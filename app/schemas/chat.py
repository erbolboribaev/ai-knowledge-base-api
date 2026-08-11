from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Foydalanuvchi savoli"""
    question: str = Field(..., min_length=3, max_length=1000)
    use_web_search: bool = False


class SourceChunk(BaseModel):
    """Javob qaysi hujjat bo'lagidan olinganini ko'rsatish uchun (shaffoflik)"""
    document_filename: str
    content: str
    similarity_score: float


class WebSource(BaseModel):
    """Javobda ishlatilgan internet manbasi"""
    title: str
    url: str
    snippet: str


class ChatResponse(BaseModel):
    """RAG orqali generatsiya qilingan javob"""
    answer: str
    sources: list[SourceChunk]
    web_sources: list[WebSource] = []
