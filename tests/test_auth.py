import pytest


@pytest.mark.asyncio
async def test_register_new_user(client):
    """Yangi foydalanuvchi muvaffaqiyatli ro'yxatdan o'tishi kerak"""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "user1@example.com", "password": "testpass123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "user1@example.com"
    assert "hashed_password" not in data  # Parol hech qachon qaytmasligi kerak
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_register_duplicate_email_fails(client):
    """Bir xil email bilan ikkinchi marta ro'yxatdan o'tish rad etilishi kerak"""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "duplicate@example.com", "password": "testpass123"},
    )
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "duplicate@example.com", "password": "anotherpass"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_with_correct_credentials(client):
    """To'g'ri email/parol bilan kirish token qaytarishi kerak"""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login_test@example.com", "password": "correctpass"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "login_test@example.com", "password": "correctpass"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_with_wrong_password_fails(client):
    """Noto'g'ri parol bilan kirish 401 qaytarishi kerak"""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "wrongpass_test@example.com", "password": "correctpass"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "wrongpass_test@example.com", "password": "wrongpass"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_with_nonexistent_user_fails(client):
    """Mavjud bo'lmagan foydalanuvchi bilan kirish 401 qaytarishi kerak"""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "doesnotexist@example.com", "password": "anypass"},
    )
    assert response.status_code == 401
