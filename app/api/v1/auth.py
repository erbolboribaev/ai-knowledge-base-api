from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.oauth import oauth
from app.core.config import settings
from app.services.auth_service import get_or_create_oauth_user

from app.db.session import get_db
from app.core.limiter import limiter
from app.api.deps import get_current_user
from app.models.user import User
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


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Joriy tizimga kirgan foydalanuvchi ma'lumotini qaytaradi"""
    return current_user


@router.get("/google/login")
async def google_login(request: Request):
    """Foydalanuvchini Google roziligini so'rash sahifasiga yo'naltiradi"""
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """Google'dan qaytgandan keyin foydalanuvchini topib/yaratib, frontend'ga tokenlar bilan yo'naltiradi"""
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")

    user = await get_or_create_oauth_user(
        db, email=user_info["email"], provider="google", oauth_id=user_info["sub"]
    )
    access_token, refresh_token = create_token_for_user(user)

    redirect_url = (
        f"{settings.frontend_url}/oauth/callback"
        f"?access_token={access_token}&refresh_token={refresh_token}"
    )
    return RedirectResponse(redirect_url)


@router.get("/github/login")
async def github_login(request: Request):
    """Foydalanuvchini GitHub roziligini so'rash sahifasiga yo'naltiradi"""
    redirect_uri = request.url_for("github_callback")
    return await oauth.github.authorize_redirect(request, redirect_uri)


@router.get("/github/callback")
async def github_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """GitHub'dan qaytgandan keyin foydalanuvchini topib/yaratib, frontend'ga tokenlar bilan yo'naltiradi"""
    token = await oauth.github.authorize_access_token(request)

    resp = await oauth.github.get("user", token=token)
    profile = resp.json()

    email = profile.get("email")
    if not email:
        # GitHub ba'zan asosiy email'ni ochiq qoldirmaydi - alohida so'raymiz
        emails_resp = await oauth.github.get("user/emails", token=token)
        emails = emails_resp.json()
        primary = next((e for e in emails if e.get("primary")), emails[0] if emails else None)
        email = primary["email"] if primary else f"{profile['id']}@users.noreply.github.com"

    user = await get_or_create_oauth_user(
        db, email=email, provider="github", oauth_id=str(profile["id"])
    )
    access_token, refresh_token = create_token_for_user(user)

    redirect_url = (
        f"{settings.frontend_url}/oauth/callback"
        f"?access_token={access_token}&refresh_token={refresh_token}"
    )
    return RedirectResponse(redirect_url)
