from __future__ import annotations
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.admin import router as admin_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.chat import router as chat_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.dialogue_log import router as dialogue_log_router
from app.core.config import get_settings
from app.core.database import close_db, init_db
from app.api.v1.document import router as document_router
from app.core.redis_bootstrap import read_bootstrap_status
from app.core.redis_client import close_redis, get_redis_client

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    bootstrap_status = read_bootstrap_status()
    runtime_connected = await get_redis_client() is not None
    app.state.redis_status = {
        **bootstrap_status,
        "runtime_connected": runtime_connected,
        "runtime_message": "Redis async 客户端已连接。" if runtime_connected else "Redis async 客户端未连接，当前会回退到数据库。",
    }
    yield
    await close_redis()
    await close_db()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "error": str(exc)},
    )


@app.get("/")
async def health_check(request: Request) -> dict[str, object]:
    redis_status = getattr(request.app.state, "redis_status", read_bootstrap_status())
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "redis": redis_status,
    }


app.include_router(chat_router, prefix=settings.api_v1_prefix)
app.include_router(knowledge_router, prefix=settings.api_v1_prefix)
app.include_router(analysis_router, prefix=settings.api_v1_prefix)
app.include_router(admin_router, prefix=settings.api_v1_prefix)
app.include_router(document_router, prefix=settings.api_v1_prefix)
app.include_router(dialogue_log_router, prefix=settings.api_v1_prefix)
