from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token


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


def create_token_for_user(user: User) -> tuple[str, str]:
    """Foydalanuvchi uchun access va refresh tokenlarni birga yaratadi"""
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    return access_token, refresh_token


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> str:
    """
    Refresh token orqali yangi access token yaratadi.
    Refresh token yaroqsiz, muddati o'tgan, yoki foydalanuvchi endi
    mavjud/faol bo'lmasa - 401 qaytaradi.
    """
    user_id = decode_token(refresh_token, expected_type="refresh")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token yaroqsiz yoki muddati o'tgan",
        )

    import uuid
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Foydalanuvchi topilmadi yoki faol emas",
        )

    return create_access_token(subject=str(user.id))


async def get_or_create_oauth_user(
    db: AsyncSession, email: str, provider: str, oauth_id: str
) -> User:
    """
    OAuth orqali kirgan foydalanuvchini topadi, yoki mavjud bo'lmasa yangi yaratadi.
    Agar shu email bilan (parol orqali) hisob allaqachon mavjud bo'lsa, o'sha
    hisobga OAuth ma'lumotini bog'laydi - shunda foydalanuvchi ikkala usul bilan
    ham kira oladi.
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        if not user.oauth_provider:
            user.oauth_provider = provider
            user.oauth_id = oauth_id
            await db.commit()
            await db.refresh(user)
        return user

    new_user = User(
        email=email,
        hashed_password=None,
        oauth_provider=provider,
        oauth_id=oauth_id,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
