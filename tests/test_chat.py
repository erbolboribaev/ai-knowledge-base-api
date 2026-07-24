import uuid
import pytest
from unittest.mock import AsyncMock, patch

from app.models.document import Document, DocumentStatus
from app.models.chunk import Chunk


async def _register_and_login(client, email="chattest@example.com", password="testpass123"):
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    response = await client.post(
        "/api/v1/auth/login", data={"username": email, "password": password}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _get_user_id_from_token(headers):
    """Test ichida foydalanuvchi ID'sini token'dan olish uchun yordamchi"""
    import jose.jwt as jwt
    token = headers["Authorization"].split(" ")[1]
    payload = jwt.get_unverified_claims(token)
    return uuid.UUID(payload["sub"])


@pytest.mark.asyncio
async def test_ask_without_auth_fails(client):
    """Token bo'lmasa, savol berish rad etilishi kerak"""
    response = await client.post("/api/v1/chat/ask", json={"question": "Python nima?"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_ask_with_no_documents_returns_fallback_message(client):
    """Hujjat yuklanmagan bo'lsa, LLM chaqirilmasdan fallback xabar qaytishi kerak"""
    headers = await _register_and_login(client)
    response = await client.post(
        "/api/v1/chat/ask", json={"question": "Python qachon yaratilgan?"}, headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["sources"] == []
    assert "topa olmadim" in data["answer"].lower() or "yuklanmagan" in data["answer"].lower()


@pytest.mark.asyncio
async def test_ask_with_document_calls_llm_and_returns_answer(client, db_session):
    """
    To'liq RAG oqimini sinaydi: hujjat + chunk bevosita bazaga qo'yiladi
    (Celery worker test muhitida ishlamagani uchun), pgvector orqali
    qidiruv haqiqatan ishlaydi, faqat LLM chaqiruvi mock qilinadi
    (haqiqiy Groq API'ga pul sarflab so'rov yubormaslik uchun).
    """
    headers = await _register_and_login(client, email="chat_with_doc@example.com")
    owner_id = _get_user_id_from_token(headers)

    document = Document(
        owner_id=owner_id,
        filename="python_facts.txt",
        content="Python 1991-yilda yaratilgan.",
        status=DocumentStatus.COMPLETED,
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)

    chunk = Chunk(
        document_id=document.id,
        content="Python 1991-yilda Guido van Rossum tomonidan yaratilgan.",
        chunk_index=0,
        embedding=[0.1] * 384,
    )
    db_session.add(chunk)
    await db_session.commit()

    with patch("app.services.rag_service.embed_text", return_value=[0.1] * 384), \
         patch("app.services.rag_service.generate_answer", new=AsyncMock(return_value="Python 1991-yilda yaratilgan.")):

        response = await client.post(
            "/api/v1/chat/ask", json={"question": "Python qachon yaratilgan?"}, headers=headers
        )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Python 1991-yilda yaratilgan."
    assert len(data["sources"]) == 1
    assert data["sources"][0]["document_filename"] == "python_facts.txt"
    assert data["sources"][0]["similarity_score"] == 1.0  # Bir xil vektor - masofa 0, o'xshashlik 1
