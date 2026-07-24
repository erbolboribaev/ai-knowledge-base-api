from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# Asinxron engine - PostgreSQL bilan asyncpg drayveri orqali ishlaydi
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # DEBUG=True bo'lsa, barcha SQL so'rovlar konsolga chiqadi
    future=True,
)

# Har bir so'rov uchun yangi sessiya yaratuvchi factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db():
    """
    FastAPI dependency: har bir so'rovga alohida DB sessiya beradi,
    so'rov tugagach avtomatik yopadi.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
