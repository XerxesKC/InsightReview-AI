from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

from app.api.v1 import chat


def _mock_turn(turn_no: int) -> SimpleNamespace:
    return SimpleNamespace(
        turn_id=turn_no,
        turn_no=turn_no,
        query=f"q{turn_no}",
        answer=f"a{turn_no}",
        rewritten_query=f"rq{turn_no}",
        sources="[]",
        created_at=datetime.now(timezone.utc),
        is_active=True,
        rating=0,
    )


def test_normalize_context_backend() -> None:
    assert chat._normalize_context_backend("auto") == "auto"
    assert chat._normalize_context_backend("redis") == "redis"
    assert chat._normalize_context_backend("mysql") == "mysql"
    assert chat._normalize_context_backend("invalid") == "auto"


def test_load_context_mysql_mode_skips_redis(monkeypatch) -> None:
    async def _should_not_call_redis(**_kwargs):
        raise AssertionError("redis path should not be used in mysql mode")

    async def _load_from_mysql(*_args, **_kwargs):
        return [_mock_turn(1), _mock_turn(2)]

    monkeypatch.setattr(chat, "get_cached_chat_context", _should_not_call_redis)
    monkeypatch.setattr(chat, "get_chat_context", _load_from_mysql)
    monkeypatch.setattr(chat, "set_cached_chat_context", _should_not_call_redis)
    monkeypatch.setattr(chat, "log_chat_context_store_call", lambda *args, **kwargs: None)

    items = asyncio.run(
        chat._load_context_items(
            session=object(),
            user_id="u1",
            user_type="admin",
            session_id="s1",
            max_context_turns=10,
            context_backend="mysql",
        )
    )
    assert len(items) == 2


def test_load_context_redis_mode_miss_no_mysql_fallback(monkeypatch) -> None:
    async def _miss_cache(**_kwargs):
        return None

    async def _should_not_load_mysql(*_args, **_kwargs):
        raise AssertionError("mysql fallback should not happen in redis mode")

    monkeypatch.setattr(chat, "get_cached_chat_context", _miss_cache)
    monkeypatch.setattr(chat, "get_chat_context", _should_not_load_mysql)
    monkeypatch.setattr(chat, "log_chat_context_store_call", lambda *args, **kwargs: None)

    items = asyncio.run(
        chat._load_context_items(
            session=object(),
            user_id="u1",
            user_type="admin",
            session_id="s2",
            max_context_turns=10,
            context_backend="redis",
        )
    )
    assert items == []


def test_load_context_auto_fallback_mysql_and_backfill_redis(monkeypatch) -> None:
    calls = {"set_cached": 0}

    async def _miss_cache(**_kwargs):
        return None

    async def _load_from_mysql(*_args, **_kwargs):
        return [_mock_turn(1)]

    async def _set_cache(**_kwargs):
        calls["set_cached"] += 1
        return True

    monkeypatch.setattr(chat, "get_cached_chat_context", _miss_cache)
    monkeypatch.setattr(chat, "get_chat_context", _load_from_mysql)
    monkeypatch.setattr(chat, "set_cached_chat_context", _set_cache)
    monkeypatch.setattr(chat, "log_chat_context_store_call", lambda *args, **kwargs: None)

    items = asyncio.run(
        chat._load_context_items(
            session=object(),
            user_id="u1",
            user_type="admin",
            session_id="s3",
            max_context_turns=10,
            context_backend="auto",
        )
    )
    assert len(items) == 1
    assert calls["set_cached"] == 1

