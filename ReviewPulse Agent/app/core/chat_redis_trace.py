from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from app.core.config import get_settings


def _safe_key_tail(key: str | None) -> str | None:
    if not key:
        return None
    text = str(key)
    if len(text) <= 24:
        return text
    return text[-24:]


def _write_trace_line(
    *,
    file_name: str,
    event: str,
    status: str,
    backend: str | None,
    key: str | None,
    session_id: str | None,
    duration_ms: int | None,
    extra: dict[str, Any] | None,
) -> None:
    settings = get_settings()
    log_path: Path = settings.log_path / file_name
    payload: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "status": status,
        "backend": backend,
        "session_id": session_id,
        "duration_ms": duration_ms,
        "key_tail": _safe_key_tail(key),
    }
    if extra:
        payload.update(extra)
    with log_path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload, ensure_ascii=False))
        fp.write("\n")


def log_chat_context_store_call(
    event: str,
    *,
    status: str,
    backend: str | None = None,
    key: str | None = None,
    session_id: str | None = None,
    duration_ms: int | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Best-effort JSONL tracing for chat context storage calls."""

    try:
        _write_trace_line(
            file_name="chat_context_store_calls.jsonl",
            event=event,
            status=status,
            backend=backend,
            key=key,
            session_id=session_id,
            duration_ms=duration_ms,
            extra=extra,
        )
    except Exception:
        return


def log_vector_cache_call(
    event: str,
    *,
    status: str,
    backend: str | None = None,
    key: str | None = None,
    session_id: str | None = None,
    duration_ms: int | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Best-effort JSONL tracing for vector cache calls."""

    try:
        _write_trace_line(
            file_name="vector_cache_calls.jsonl",
            event=event,
            status=status,
            backend=backend,
            key=key,
            session_id=session_id,
            duration_ms=duration_ms,
            extra=extra,
        )
    except Exception:
        return


def log_chat_redis_call(
    event: str,
    *,
    status: str,
    backend: str | None = None,
    key: str | None = None,
    session_id: str | None = None,
    duration_ms: int | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Backward-compatible alias routed to vector cache trace file."""

    try:
        _write_trace_line(
            file_name="chat_redis_calls.jsonl",
            event=event,
            status=status,
            backend=backend,
            key=key,
            session_id=session_id,
            duration_ms=duration_ms,
            extra=extra,
        )
    except Exception:
        return

