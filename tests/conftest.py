import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db

import os
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:password@localhost:5433/knowledge_base_test",
)


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """
    Har bir test uchun YANGI engine yaratadi (NullPool bilan - ulanish
    pool'da saqlanmaydi). Bu asyncpg'ning har xil event loop'lar orasida
    "qolib ketish" muammosining oldini oladi.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_engine):
    """Testlar uchun HTTP mijoz - har bir test o'z engine'iga bog'lanadi"""
    TestSessionLocal = async_sessionmaker(bind=db_engine, expire_on_commit=False)

    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    """Testlarda to'g'ridan-to'g'ri bazaga yozish uchun (masalan, Celery ishlamagani uchun chunk'ni qo'lda qo'shish)"""
    TestSessionLocal = async_sessionmaker(bind=db_engine, expire_on_commit=False)
    async with TestSessionLocal() as session:
        yield session
