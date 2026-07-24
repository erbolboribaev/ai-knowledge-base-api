from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password, create_access_token


async def register_user(db: AsyncSession, user_data: UserCreate) -> User:
    """
    Yangi foydalanuvchi ro'yxatdan o'tkazadi.
    Email allaqachon mavjud bo'lsa, xato qaytaradi (bitta email = bitta hisob).
    """
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu email bilan foydalanuvchi allaqachon mavjud",
        )

    new_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    """
    Email va parolni tekshiradi. To'g'ri kelsa - foydalanuvchini qaytaradi.
    Xato bo'lsa - 401 qaytaradi (email yoki parol xato ekanini alohida
    aytmaymiz - bu xavfsizlik yaxshi amaliyoti, hujumchiga ortiqcha ma'lumot bermaslik uchun).
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email yoki parol noto'g'ri",
        )

    return user


def create_token_for_user(user: User) -> str:
    """Foydalanuvchi uchun JWT token yaratadi"""
    return create_access_token(subject=str(user.id))
