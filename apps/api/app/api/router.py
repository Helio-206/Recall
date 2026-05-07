from fastapi import APIRouter

from app.api.routes import auth, health, ingestion, spaces, videos

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(spaces.router, prefix="/spaces", tags=["spaces"])
api_router.include_router(videos.router, prefix="/videos", tags=["videos"])
api_router.include_router(ingestion.router, prefix="/ingestion", tags=["ingestion"])
