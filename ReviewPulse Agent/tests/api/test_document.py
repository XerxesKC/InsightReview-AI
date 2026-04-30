from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.api.v1 import document as document_api
from app.core.database import get_db
from app.core.security import get_current_user


class _FakeExecResult:
    def __init__(self, scalar_value=None):
        self._scalar_value = scalar_value

    def scalar_one_or_none(self):
        return self._scalar_value


def _build_test_client(db_session: AsyncMock) -> TestClient:
    async def _fake_get_db():
        yield db_session

    async def _fake_get_current_user():
        return {"user_id": "u-test", "user_type": "admin"}

    app = FastAPI()
    app.include_router(document_api.router, prefix="/api/v1")
    app.dependency_overrides[get_db] = _fake_get_db
    app.dependency_overrides[get_current_user] = _fake_get_current_user
    return TestClient(app)


@pytest.fixture
def db_session() -> AsyncMock:
    return AsyncMock(name="db_session")


@pytest.fixture
def client(db_session: AsyncMock) -> TestClient:
    return _build_test_client(db_session)


def test_search_documents_accepts_query_params(client: TestClient, monkeypatch) -> None:
    async def _fake_search_documents(*args, **kwargs):
        return [], 0

    monkeypatch.setattr(document_api, "search_documents", _fake_search_documents)

    response = client.get("/api/v1/admin/doc-workbench/search", params={"page": 1, "page_size": 10})
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 200


def test_get_pending_documents_accepts_query_params(client: TestClient, monkeypatch) -> None:
    async def _fake_search_documents(*args, **kwargs):
        return [], 0

    monkeypatch.setattr(document_api, "search_documents", _fake_search_documents)

    response = client.get("/api/v1/admin/documents/pending", params={"page": 1, "page_size": 10})
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 200


def test_get_document_detail_accepts_path_param(client: TestClient, db_session: AsyncMock) -> None:
    db_session.execute = AsyncMock(return_value=_FakeExecResult(scalar_value=None))

    response = client.get("/api/v1/admin/documents/1")

    assert response.status_code == 404


def test_preview_document_chunks_accepts_path_and_query_params(client: TestClient, db_session: AsyncMock) -> None:
    db_session.execute = AsyncMock(return_value=_FakeExecResult(scalar_value=None))

    response = client.post(
        "/api/v1/admin/documents/1/preview-chunks",
        params={"chunk_size": 500, "chunk_overlap": 50},
    )

    assert response.status_code == 404


def test_generate_document_vectors_accepts_json_payload(client: TestClient, db_session: AsyncMock) -> None:
    db_session.execute = AsyncMock(return_value=_FakeExecResult(scalar_value=None))

    response = client.post(
        "/api/v1/admin/documents/1/generate-vectors",
        json={"chunks": [{"content": "hello"}], "target_index": "default_vector_index"},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 404


def test_approve_document_accepts_json_payload(client: TestClient, db_session: AsyncMock) -> None:
    db_session.execute = AsyncMock(return_value=_FakeExecResult(scalar_value=None))

    response = client.post(
        "/api/v1/admin/documents/1/approve",
        json={"chunks": [{"content": "hello"}], "target_index": "default_vector_index"},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 404


def test_reject_document_accepts_path_param(client: TestClient, monkeypatch) -> None:
    async def _fake_reject_document(session, document_id):
        return None

    monkeypatch.setattr(document_api, "reject_document", _fake_reject_document)

    response = client.post("/api/v1/admin/documents/1/reject")
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 404


def test_preview_document_file_accepts_path_param(client: TestClient, monkeypatch) -> None:
    async def _fake_get_document_by_id(session, document_id):
        return None

    monkeypatch.setattr(document_api, "get_document_by_id", _fake_get_document_by_id)

    response = client.get("/api/v1/admin/documents/1/preview")

    assert response.status_code == 404


def test_intelligent_preview_accepts_path_and_query_params(client: TestClient, monkeypatch) -> None:
    async def _fake_get_document_by_id(session, document_id):
        return None

    monkeypatch.setattr(document_api, "get_document_by_id", _fake_get_document_by_id)

    response = client.post(
        "/api/v1/admin/documents/1/intelligent-preview",
        params={"chunk_size": 500, "chunk_overlap": 50, "splitter_type": "semantic", "similarity_threshold": 0.7},
    )

    assert response.status_code == 404
