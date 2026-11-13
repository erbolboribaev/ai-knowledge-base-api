from fastapi import FastAPI
from fastapi.responses import JSONResponse
from redis import asyncio as aioredis
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings
from app.core.limiter import limiter
from app.db.session import AsyncSessionLocal
from app.api.v1.router import api_router
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Server ishlab turganini tekshirish uchun oddiy endpoint"""
    return {"status": "ok", "app": settings.app_name}


@app.get("/health")
async def health():
    """
    Orchestrator (Docker/Kubernetes) uchun sog'liq tekshiruvi: PostgreSQL va Redis
    haqiqatan javob berayotganini tekshiradi. Biri ishlamasa 503 qaytaradi.
    """
    checks = {}

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unavailable"

    redis_client = aioredis.from_url(settings.redis_url)
    try:
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "unavailable"
    finally:
        await redis_client.aclose()

    healthy = all(value == "ok" for value in checks.values())
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={"status": "ok" if healthy else "degraded", "checks": checks},
    )
