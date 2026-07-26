from fastapi import FastAPI, Request
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.core.config import settings
from app.core.limiter import limiter
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Server ishlab turganini tekshirish uchun oddiy endpoint"""
    return {"status": "ok", "app": settings.app_name}
