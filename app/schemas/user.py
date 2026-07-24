import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


class UserCreate(BaseModel):
    """Ro'yxatdan o'tish uchun kiruvchi ma'lumot"""
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """Kirish uchun kiruvchi ma'lumot"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """
    API javobida qaytariladigan ma'lumot.
    MUHIM: hashed_password bu yerda YO'Q - parol hech qachon
    tashqariga chiqmasligi kerak.
    """
    id: uuid.UUID
    email: EmailStr
    is_active: bool
    is_admin: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)  # SQLAlchemy obyektidan to'g'ridan-to'g'ri o'qish uchun


class Token(BaseModel):
    """Login muvaffaqiyatli bo'lganda qaytariladigan JWT token"""
    access_token: str
    token_type: str = "bearer"
