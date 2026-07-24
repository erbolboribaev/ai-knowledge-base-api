import pytest


async def _register_and_login(client, email="doctest@example.com", password="testpass123"):
    """Yordamchi funksiya: foydalanuvchi yaratib, token qaytaradi"""
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    response = await client.post(
        "/api/v1/auth/login", data={"username": email, "password": password}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_upload_document_without_auth_fails(client):
    """Token bo'lmasa, hujjat yuklab bo'lmasligi kerak"""
    response = await client.post(
        "/api/v1/documents/",
        json={"filename": "test.txt", "content": "Test matni"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_upload_document_with_auth_succeeds(client):
    """Token bilan hujjat muvaffaqiyatli yuklanishi kerak"""
    headers = await _register_and_login(client)
    response = await client.post(
        "/api/v1/documents/",
        json={"filename": "test.txt", "content": "Bu test hujjati matni."},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test.txt"
    assert data["status"] == "pending"  # Celery bu yerda ishlamaydi (worker alohida)


@pytest.mark.asyncio
async def test_list_documents_returns_only_own_documents(client):
    """Foydalanuvchi faqat o'z hujjatlarini ko'rishi kerak, boshqalarnikini emas"""
    headers_user1 = await _register_and_login(client, email="user1@example.com")
    headers_user2 = await _register_and_login(client, email="user2@example.com")

    await client.post(
        "/api/v1/documents/",
        json={"filename": "user1_doc.txt", "content": "User1 hujjati"},
        headers=headers_user1,
    )
    await client.post(
        "/api/v1/documents/",
        json={"filename": "user2_doc.txt", "content": "User2 hujjati"},
        headers=headers_user2,
    )

    response = await client.get("/api/v1/documents/", headers=headers_user1)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["filename"] == "user1_doc.txt"


@pytest.mark.asyncio
async def test_get_other_users_document_forbidden(client):
    """Boshqa foydalanuvchining hujjatini ID orqali ochishga urinish 403 qaytarishi kerak"""
    headers_user1 = await _register_and_login(client, email="owner@example.com")
    headers_user2 = await _register_and_login(client, email="intruder@example.com")

    upload_response = await client.post(
        "/api/v1/documents/",
        json={"filename": "private.txt", "content": "Maxfiy matn"},
        headers=headers_user1,
    )
    document_id = upload_response.json()["id"]

    response = await client.get(f"/api/v1/documents/{document_id}", headers=headers_user2)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_nonexistent_document_returns_404(client):
    """Mavjud bo'lmagan hujjat ID'si 404 qaytarishi kerak"""
    headers = await _register_and_login(client, email="notfound_test@example.com")
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/documents/{fake_id}", headers=headers)
    assert response.status_code == 404
