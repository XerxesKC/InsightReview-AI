from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.api.v1 import chat as chat_api
from app.core.database import get_db
from app.core.security import get_current_user


class _FakePath:
    def __init__(self, name: str = "abc_demo.png"):
        self.name = name

    def stat(self):
        return SimpleNamespace(st_size=1)


def _build_test_client(db_session: AsyncMock) -> TestClient:
    async def _fake_get_db():
        yield db_session

    async def _fake_get_current_user():
        return {"user_id": "u-test", "user_type": "user"}

    app = FastAPI()
    app.include_router(chat_api.router, prefix="/api/v1")
    app.dependency_overrides[get_db] = _fake_get_db
    app.dependency_overrides[get_current_user] = _fake_get_current_user
    return TestClient(app)


@pytest.fixture
def db_session() -> AsyncMock:
    return AsyncMock(name="db_session")


@pytest.fixture
def client(db_session: AsyncMock) -> TestClient:
    return _build_test_client(db_session)


def test_upload_chat_image_accepts_form_file(client: TestClient, monkeypatch) -> None:
    async def _fake_save_upload_file(file, allowed_suffixes=None, max_upload_size_mb=None):
        return _FakePath(name="abcdef123_demo.png")

    monkeypatch.setattr(chat_api, "save_upload_file", _fake_save_upload_file)

    response = client.post("/api/v1/chat/images/upload", files={"file": ("a.png", b"1", "image/png")})
    body = response.json()

    assert response.status_code == 200
    assert "image_id" in body


def test_get_chat_image_accepts_path_param(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(chat_api, "_resolve_chat_image_path", lambda image_id, image_url=None: None)

    response = client.get("/api/v1/chat/images/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")

    assert response.status_code == 404


def test_create_completion_accepts_json_payload(client: TestClient) -> None:
    response = client.post(
        "/api/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "hi"}], "max_context_turns": 0},
    )

    assert response.status_code == 422


def test_get_session_history_accepts_path_and_query_params(client: TestClient, monkeypatch) -> None:
    async def _fake_ensure_session_exists(**kwargs):
        return None

    async def _fake_list_chat_turns(*args, **kwargs):
        return []

    monkeypatch.setattr(chat_api, "_ensure_session_exists", _fake_ensure_session_exists)
    monkeypatch.setattr(chat_api, "list_chat_turns", _fake_list_chat_turns)

    response = client.get("/api/v1/chat/sessions/s1/history", params={"include_inactive": False})
    body = response.json()

    assert response.status_code == 200
    assert body["session_id"] == "s1"


def test_get_sessions_accepts_get_request(client: TestClient, monkeypatch) -> None:
    async def _fake_list_chat_sessions(*args, **kwargs):
        return []

    monkeypatch.setattr(chat_api, "list_chat_sessions", _fake_list_chat_sessions)

    response = client.get("/api/v1/chat/sessions")
    body = response.json()

    assert response.status_code == 200
    assert body["items"] == []


def test_get_session_retrieval_config_accepts_path_param(client: TestClient, monkeypatch) -> None:
    async def _fake_ensure_session_exists(**kwargs):
        return None

    async def _fake_resolve_chat_runtime_params(**kwargs):
        return {"retrieval_top_k": 4, "similarity_threshold": 0.2}

    async def _fake_get_chat_session_for_actor(*args, **kwargs):
        return None

    monkeypatch.setattr(chat_api, "_ensure_session_exists", _fake_ensure_session_exists)
    monkeypatch.setattr(chat_api, "_resolve_chat_runtime_params", _fake_resolve_chat_runtime_params)
    monkeypatch.setattr(chat_api, "get_chat_session_for_actor", _fake_get_chat_session_for_actor)

    response = client.get("/api/v1/chat/sessions/s1/retrieval-config")
    body = response.json()

    assert response.status_code == 200
    assert body["session_id"] == "s1"


def test_update_session_retrieval_config_accepts_json_payload(client: TestClient, monkeypatch) -> None:
    async def _fake_ensure_session_exists(**kwargs):
        return None

    async def _fake_update_chat_session_retrieval_config(*args, **kwargs):
        return SimpleNamespace(retrieval_top_k=4, similarity_threshold=0.2)

    async def _fake_clear_cached_chat_context(**kwargs):
        return None

    monkeypatch.setattr(chat_api, "_ensure_session_exists", _fake_ensure_session_exists)
    monkeypatch.setattr(chat_api, "update_chat_session_retrieval_config", _fake_update_chat_session_retrieval_config)
    monkeypatch.setattr(chat_api, "clear_cached_chat_context", _fake_clear_cached_chat_context)

    response = client.put("/api/v1/chat/sessions/s1/retrieval-config", json={"top_k": 4, "similarity_threshold": 0.2})

    assert response.status_code == 200


def test_delete_session_context_accepts_path_param(client: TestClient, monkeypatch) -> None:
    async def _fake_ensure_session_exists(**kwargs):
        return None

    async def _fake_resolve_chat_runtime_params(**kwargs):
        return {"context_backend": "none"}

    async def _fake_clear_chat_context(*args, **kwargs):
        return 0

    monkeypatch.setattr(chat_api, "_ensure_session_exists", _fake_ensure_session_exists)
    monkeypatch.setattr(chat_api, "_resolve_chat_runtime_params", _fake_resolve_chat_runtime_params)
    monkeypatch.setattr(chat_api, "clear_chat_context", _fake_clear_chat_context)

    response = client.delete("/api/v1/chat/sessions/s1/context")

    assert response.status_code == 200


def test_update_session_title_accepts_json_payload(client: TestClient, monkeypatch) -> None:
    async def _fake_rename_chat_session(*args, **kwargs):
        return None

    monkeypatch.setattr(chat_api, "rename_chat_session", _fake_rename_chat_session)

    response = client.patch("/api/v1/chat/sessions/s1", json={"title": "new"})

    assert response.status_code == 404


def test_delete_chat_session_accepts_path_param(client: TestClient, monkeypatch) -> None:
    async def _fake_resolve_chat_runtime_params(**kwargs):
        return {"context_backend": "none"}

    async def _fake_delete_chat_session(*args, **kwargs):
        return SimpleNamespace(session_id="s1")

    monkeypatch.setattr(chat_api, "_resolve_chat_runtime_params", _fake_resolve_chat_runtime_params)
    monkeypatch.setattr(chat_api, "delete_chat_session", _fake_delete_chat_session)

    response = client.delete("/api/v1/chat/sessions/s1")
    body = response.json()

    assert response.status_code == 200
    assert body["deleted"] is True


def test_rollback_session_context_accepts_json_payload(client: TestClient, monkeypatch) -> None:
    async def _fake_ensure_session_exists(**kwargs):
        return None

    async def _fake_resolve_chat_runtime_params(**kwargs):
        return {"context_backend": "none"}

    async def _fake_rollback_chat_context(*args, **kwargs):
        return 1

    async def _fake_get_chat_context(*args, **kwargs):
        return []

    monkeypatch.setattr(chat_api, "_ensure_session_exists", _fake_ensure_session_exists)
    monkeypatch.setattr(chat_api, "_resolve_chat_runtime_params", _fake_resolve_chat_runtime_params)
    monkeypatch.setattr(chat_api, "rollback_chat_context", _fake_rollback_chat_context)
    monkeypatch.setattr(chat_api, "get_chat_context", _fake_get_chat_context)

    response = client.post("/api/v1/chat/sessions/s1/rollback", json={"turn_no": 1})

    assert response.status_code == 200


def test_update_chat_turn_rating_accepts_json_payload(client: TestClient, monkeypatch) -> None:
    async def _fake_ensure_session_exists(**kwargs):
        return None

    async def _fake_update_chat_turn_rating(*args, **kwargs):
        return True

    monkeypatch.setattr(chat_api, "_ensure_session_exists", _fake_ensure_session_exists)
    monkeypatch.setattr(chat_api, "update_chat_turn_rating", _fake_update_chat_turn_rating)

    response = client.put(
        "/api/v1/chat/turn/rating",
        json={"session_id": "s1", "turn_no": 1, "rating": 1},
    )

    assert response.status_code == 200


def test_upload_chat_file_accepts_form_file(client: TestClient) -> None:
    response = client.post(
        "/api/v1/chat/files/upload",
        files={"file": ("bad.exe", b"123", "application/octet-stream")},
    )

    assert response.status_code == 400
