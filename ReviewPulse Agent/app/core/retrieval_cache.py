from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from app.core.chat_redis_trace import log_vector_cache_call
from app.core.config import get_settings
from app.core.redis_client import get_redis_client

_memory_cache: dict[str, tuple[float, str]] = {}


def build_vector_cache_key(*, payload: dict[str, Any]) -> str:
    settings = get_settings()
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"{settings.chat_vector_cache_prefix}:{digest}"


def _normalize_backend(value: str | None) -> str:
    backend = (value or "auto").strip().lower()
    if backend in {"auto", "redis", "memory", "none", "off", "disabled"}:
        return backend
    return "auto"


def _is_disabled(value: str) -> bool:
    return value in {"none", "off", "disabled"}


async def get_vector_cache_items(*, key: str, backend: str | None = None) -> list[dict[str, Any]] | None:
    started = time.monotonic()
    settings = get_settings()
    selected = _normalize_backend(backend or settings.chat_vector_cache_backend)
    if _is_disabled(selected):
        log_vector_cache_call(
            "vector_cache_get",
            status="disabled",
            backend=selected,
            key=key,
            duration_ms=int((time.monotonic() - started) * 1000),
        )
        return None

    if selected in {"auto", "redis"}:
        client = await get_redis_client()
        if client is not None:
            payload = await client.get(key)
            if payload:
                try:
                    data = json.loads(payload)
                    if isinstance(data, list):
                        log_vector_cache_call(
                            "vector_cache_get",
                            status="hit",
                            backend="redis",
                            key=key,
                            duration_ms=int((time.monotonic() - started) * 1000),
                            extra={"items_count": len(data)},
                        )
                        return data
                except json.JSONDecodeError:
                    log_vector_cache_call(
                        "vector_cache_get",
                        status="decode_error",
                        backend="redis",
                        key=key,
                        duration_ms=int((time.monotonic() - started) * 1000),
                    )
                    return None
            if selected == "redis":
                log_vector_cache_call(
                    "vector_cache_get",
                    status="miss",
                    backend="redis",
                    key=key,
                    duration_ms=int((time.monotonic() - started) * 1000),
                )
                return None
        elif selected == "redis":
            log_vector_cache_call(
                "vector_cache_get",
                status="redis_unavailable",
                backend="redis",
                key=key,
                duration_ms=int((time.monotonic() - started) * 1000),
            )
            return None

    expiry_and_payload = _memory_cache.get(key)
    if not expiry_and_payload:
        log_vector_cache_call(
            "vector_cache_get",
            status="miss",
            backend="memory" if selected == "memory" else "auto->memory",
            key=key,
            duration_ms=int((time.monotonic() - started) * 1000),
        )
        return None
    expire_at, payload = expiry_and_payload
    if expire_at <= time.time():
        _memory_cache.pop(key, None)
        log_vector_cache_call(
            "vector_cache_get",
            status="expired",
            backend="memory" if selected == "memory" else "auto->memory",
            key=key,
            duration_ms=int((time.monotonic() - started) * 1000),
        )
        return None
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        log_vector_cache_call(
            "vector_cache_get",
            status="decode_error",
            backend="memory" if selected == "memory" else "auto->memory",
            key=key,
            duration_ms=int((time.monotonic() - started) * 1000),
        )
        return None
    log_vector_cache_call(
        "vector_cache_get",
        status="hit" if isinstance(data, list) else "invalid_payload",
        backend="memory" if selected == "memory" else "auto->memory",
        key=key,
        duration_ms=int((time.monotonic() - started) * 1000),
        extra={"items_count": len(data) if isinstance(data, list) else None},
    )
    return data if isinstance(data, list) else None


async def set_vector_cache_items(
    *,
    key: str,
    items: list[dict[str, Any]],
    ttl_seconds: int,
    backend: str | None = None,
) -> None:
    started = time.monotonic()
    safe_ttl = max(int(ttl_seconds), 1)
    settings = get_settings()
    selected = _normalize_backend(backend or settings.chat_vector_cache_backend)
    if _is_disabled(selected):
        log_vector_cache_call(
            "vector_cache_set",
            status="disabled",
            backend=selected,
            key=key,
            duration_ms=int((time.monotonic() - started) * 1000),
        )
        return

    payload = json.dumps(items, ensure_ascii=False)

    if selected in {"auto", "redis"}:
        client = await get_redis_client()
        if client is not None:
            await client.set(key, payload, ex=safe_ttl)
            log_vector_cache_call(
                "vector_cache_set",
                status="ok",
                backend="redis",
                key=key,
                duration_ms=int((time.monotonic() - started) * 1000),
                extra={"ttl_seconds": safe_ttl, "items_count": len(items)},
            )
            return
        if selected == "redis":
            log_vector_cache_call(
                "vector_cache_set",
                status="redis_unavailable",
                backend="redis",
                key=key,
                duration_ms=int((time.monotonic() - started) * 1000),
            )
            return

    _memory_cache[key] = (time.time() + safe_ttl, payload)
    log_vector_cache_call(
        "vector_cache_set",
        status="ok",
        backend="memory" if selected == "memory" else "auto->memory",
        key=key,
        duration_ms=int((time.monotonic() - started) * 1000),
        extra={"ttl_seconds": safe_ttl, "items_count": len(items)},
    )


