from datetime import datetime, timedelta, timezone
import bcrypt
from jose import jwt, JWTError
from app.core.config import settings


def hash_password(password: str) -> str:
    """
    Xom parolni bcrypt bilan xeshlaydi.
    bcrypt maksimum 72 baytgacha parolni qo'llab-quvvatlaydi - shundan
    uzunini avtomatik qisqartiramiz (bu standart amaliyot).
    """
    password_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kirish paytida kiritilgan parolni bazadagi xesh bilan solishtiradi"""
    password_bytes = plain_password.encode("utf-8")[:72]
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(subject: str) -> str:
    """
    JWT token yaratadi. 'subject' odatda foydalanuvchi ID'si bo'ladi.
    Token ichida muddat (exp) ham saqlanadi - shu orqali eski tokenlar
    avtomatik yaroqsiz bo'ladi.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> str | None:
    """
    Tokenni tekshiradi va ichidan foydalanuvchi ID'sini qaytaradi.
    Token noto'g'ri, buzilgan yoki muddati o'tgan bo'lsa - None qaytaradi.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload.get("sub")
    except JWTError:
        return None
