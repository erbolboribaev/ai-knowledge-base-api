import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.core.security import decode_access_token
from app.models.user import User

# Swagger UI'da "Authorize" tugmasi shu orqali ishlaydi
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    So'rov headerdagi Bearer tokenni tekshiradi va mos foydalanuvchini
    bazadan topib qaytaradi. Token yaroqsiz bo'lsa - 401 xato beradi.
    Bu funksiya himoyalangan endpointlarda Depends() orqali ishlatiladi.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Tizimga kirish ma'lumotlari yaroqsiz",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_id = decode_access_token(token)
    if user_id is None:
        raise credentials_exception

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Foydalanuvchi faol emas")

    return user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Faqat admin huquqiga ega foydalanuvchilarga ruxsat beradi"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu amal uchun administrator huquqi kerak",
        )
    return current_user
