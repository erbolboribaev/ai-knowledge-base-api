from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.limiter import limiter
from app.schemas.user import UserCreate, UserResponse, Token, RefreshRequest, AccessTokenResponse
from app.services.auth_service import (
    register_user,
    authenticate_user,
    create_token_for_user,
    refresh_access_token,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit("5/minute")
async def register(request: Request, user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Yangi foydalanuvchi ro'yxatdan o'tkazish"""
    user = await register_user(db, user_data)
    return user


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Email (username maydonida) va parol orqali kirish.
    Access token (qisqa muddatli) va refresh token (uzoq muddatli) qaytaradi.
    """
    user = await authenticate_user(db, email=form_data.username, password=form_data.password)
    access_token, refresh_token = create_token_for_user(user)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=AccessTokenResponse)
@limiter.limit("20/minute")
async def refresh(
    request: Request,
    refresh_data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh token orqali yangi access token oladi - foydalanuvchi
    qayta parol kiritmasdan sessiyasini davom ettira oladi.
    """
    new_access_token = await refresh_access_token(db, refresh_data.refresh_token)
    return AccessTokenResponse(access_token=new_access_token)
