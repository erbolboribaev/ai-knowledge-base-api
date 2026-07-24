from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Server ishlab turganini tekshirish uchun oddiy endpoint"""
    return {"status": "ok", "app": settings.app_name}
