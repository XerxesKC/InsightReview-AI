from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.base import Base

settings = get_settings()

engine_options: dict[str, Any] = {
    "echo": settings.debug,
}

if settings.database_url.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}
else:
    engine_options.update(
        {
            "pool_pre_ping": True,
            "pool_recycle": 3600,
            "pool_size": 5,
            "max_overflow": 10,
        }
    )

engine = create_async_engine(settings.database_url, **engine_options)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    from app.db import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
        if settings.database_auto_create:
            await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    await engine.dispose()

