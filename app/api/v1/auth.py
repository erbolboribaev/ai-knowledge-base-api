from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse, Token
from app.services.auth_service import register_user, authenticate_user, create_token_for_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Yangi foydalanuvchi ro'yxatdan o'tkazish"""
    user = await register_user(db, user_data)
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Email (username maydonida) va parol orqali kirish.
    OAuth2PasswordRequestForm ishlatilyapti - bu Swagger UI'dagi
    standart 'Authorize' oynasi bilan mos ishlashi uchun.
    """
    user = await authenticate_user(db, email=form_data.username, password=form_data.password)
    token = create_token_for_user(user)
    return Token(access_token=token)
