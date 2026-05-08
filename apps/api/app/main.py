from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.security import decode_access_token
from app.services.search_indexing import ensure_search_index

settings = get_settings()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def jwt_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    auth_header = request.headers.get("Authorization", "")
    token = (
        auth_header.removeprefix("Bearer ").strip()
        if auth_header.startswith("Bearer ")
        else None
    )
    request.state.user_id = decode_access_token(token) if token else None
    request.state.authenticated = bool(request.state.user_id)
    return await call_next(request)


app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.on_event("startup")
def initialize_search_indexes() -> None:
    ensure_search_index()


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "recall-api", "status": "ready"}
