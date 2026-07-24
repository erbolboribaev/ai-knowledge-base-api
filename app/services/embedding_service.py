from sentence_transformers import SentenceTransformer
from app.core.config import settings

# Model faqat bir marta, dastur ishga tushganda yuklanadi (og'ir operatsiya).
# Har bir so'rovda qayta yuklash - ishlashni sekinlashtiradi, shuning uchun
# modul darajasida bitta nusxa (singleton) sifatida saqlaymiz.
_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    """Embedding modelini "lazy load" qiladi - faqat birinchi chaqirilganda yuklanadi"""
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model)
    return _model


def embed_text(text: str) -> list[float]:
    """Bitta matn bo'lagini 384-o'lchamli vektorga aylantiradi"""
    model = get_embedding_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Bir nechta matnni birdan vektorga aylantiradi - bitta-bitta chaqirishdan
    ancha tezroq (batch processing), hujjatni bo'laklarga bo'lganda ishlatiladi.
    """
    model = get_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()
