from fastapi import APIRouter

from app.api.routes import ai_summaries, auth, health, ingestion, search, spaces, transcripts, videos

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(spaces.router, prefix="/spaces", tags=["spaces"])
api_router.include_router(videos.router, prefix="/videos", tags=["videos"])
api_router.include_router(ingestion.router, prefix="/ingestion", tags=["ingestion"])
api_router.include_router(transcripts.router, prefix="/transcripts", tags=["transcripts"])
api_router.include_router(ai_summaries.router, prefix="/ai-summaries", tags=["ai-summaries"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
