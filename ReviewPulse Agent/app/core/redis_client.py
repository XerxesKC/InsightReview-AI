from __future__ import annotations

import json
import time
from typing import Any

from redis.asyncio import Redis, from_url

from app.core.config import get_settings
from app.core.chat_redis_trace import log_chat_context_store_call

_redis_client: Redis | None = None


async def get_redis_client() -> Redis | None:
    """Lazily create a Redis client.

    Redis 在这里主要承担“会话上下文缓存”的角色；如果 Redis 暂时不可用，
    接口仍然会回退到数据库，不阻断 demo 联调。
    """

    global _redis_client
    if _redis_client is not None:
        return _redis_client

    settings = get_settings()
    try:
        client = from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
        await client.ping()
    except Exception:
        return None

    _redis_client = client
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client is None:
        return
    await _redis_client.aclose()
    _redis_client = None


def build_chat_session_key(*, user_type: str, user_id: str, session_id: str) -> str:
    settings = get_settings()
    return f"{settings.chat_redis_prefix}:session:{user_type}:{user_id}:{session_id}"


async def get_cached_chat_context(*, user_type: str, user_id: str, session_id: str) -> list[dict[str, Any]] | None:
    started = time.monotonic()
    key = build_chat_session_key(user_type=user_type, user_id=user_id, session_id=session_id)
    client = await get_redis_client()
    if client is None:
        log_chat_context_store_call(
            "chat_context_get",
            status="redis_unavailable",
            backend="redis",
            key=key,
            session_id=session_id,
            duration_ms=int((time.monotonic() - started) * 1000),
        )
        return None

    payload = await client.get(key)
    if not payload:
        log_chat_context_store_call(
            "chat_context_get",
            status="miss",
            backend="redis",
            key=key,
            session_id=session_id,
            duration_ms=int((time.monotonic() - started) * 1000),
        )
        return None

    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        log_chat_context_store_call(
            "chat_context_get",
            status="decode_error",
            backend="redis",
            key=key,
            session_id=session_id,
            duration_ms=int((time.monotonic() - started) * 1000),
        )
        return None
    log_chat_context_store_call(
        "chat_context_get",
        status="hit" if isinstance(data, list) else "invalid_payload",
        backend="redis",
        key=key,
        session_id=session_id,
        duration_ms=int((time.monotonic() - started) * 1000),
        extra={"items_count": len(data) if isinstance(data, list) else None},
    )
    return data if isinstance(data, list) else None


async def set_cached_chat_context(
    *,
    user_type: str,
    user_id: str,
    session_id: str,
    items: list[dict[str, Any]],
) -> bool:
    started = time.monotonic()
    key = build_chat_session_key(user_type=user_type, user_id=user_id, session_id=session_id)
    client = await get_redis_client()
    if client is None:
        log_chat_context_store_call(
            "chat_context_set",
            status="redis_unavailable",
            backend="redis",
            key=key,
            session_id=session_id,
            duration_ms=int((time.monotonic() - started) * 1000),
        )
        return False

    settings = get_settings()
    await client.set(
        key,
        json.dumps(items, ensure_ascii=False),
        ex=settings.chat_context_ttl_seconds,
    )
    log_chat_context_store_call(
        "chat_context_set",
        status="ok",
        backend="redis",
        key=key,
        session_id=session_id,
        duration_ms=int((time.monotonic() - started) * 1000),
        extra={"items_count": len(items), "ttl_seconds": settings.chat_context_ttl_seconds},
    )
    return True


async def clear_cached_chat_context(*, user_type: str, user_id: str, session_id: str) -> bool:
    started = time.monotonic()
    key = build_chat_session_key(user_type=user_type, user_id=user_id, session_id=session_id)
    client = await get_redis_client()
    if client is None:
        log_chat_context_store_call(
            "chat_context_clear",
            status="redis_unavailable",
            backend="redis",
            key=key,
            session_id=session_id,
            duration_ms=int((time.monotonic() - started) * 1000),
        )
        return False

    deleted = await client.delete(key)
    log_chat_context_store_call(
        "chat_context_clear",
        status="ok",
        backend="redis",
        key=key,
        session_id=session_id,
        duration_ms=int((time.monotonic() - started) * 1000),
        extra={"deleted": int(deleted)},
    )
    return True

