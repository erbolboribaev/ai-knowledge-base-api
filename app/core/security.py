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
    Qisqa muddatli JWT token yaratadi (API so'rovlarini avtorizatsiya qilish uchun).
    'type: access' claim'i orqali refresh token'dan farqlanadi.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    to_encode = {"sub": subject, "exp": expire, "type": "access"}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(subject: str) -> str:
    """
    Uzoq muddatli JWT token yaratadi (faqat yangi access token olish uchun ishlatiladi,
    API so'rovlarini avtorizatsiya qilish uchun emas). 'type: refresh' claim'i bilan
    belgilanadi, shunda access token o'rniga xato ishlatib bo'lmaydi.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    to_encode = {"sub": subject, "exp": expire, "type": "refresh"}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str, expected_type: str = "access") -> str | None:
    """
    Tokenni tekshiradi va ichidan foydalanuvchi ID'sini qaytaradi.
    Token noto'g'ri, buzilgan, muddati o'tgan, yoki kutilgan turga
    (access/refresh) mos kelmasa - None qaytaradi.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != expected_type:
            return None
        return payload.get("sub")
    except JWTError:
        return None


def decode_access_token(token: str) -> str | None:
    """Orqaga qarab moslik uchun saqlangan - access token'ni tekshiradi"""
    return decode_token(token, expected_type="access")
