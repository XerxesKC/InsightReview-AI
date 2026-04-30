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

from app.api.v1 import analysis as analysis_api
from app.core.database import get_db


class _FakeResult:
    def __init__(self, rows=None):
        self._rows = rows or []

    def all(self):
        return self._rows


def _build_test_client(db_session: AsyncMock) -> TestClient:
    async def _fake_get_db():
        yield db_session

    app = FastAPI()
    app.include_router(analysis_api.router, prefix="/api/v1")
    app.dependency_overrides[get_db] = _fake_get_db
    return TestClient(app)


@pytest.fixture
def db_session() -> AsyncMock:
    return AsyncMock(name="db_session")


@pytest.fixture
def client(db_session: AsyncMock) -> TestClient:
    return _build_test_client(db_session)


def test_get_logs_accepts_query_params(client: TestClient, db_session: AsyncMock) -> None:
    db_session.execute = AsyncMock(return_value=_FakeResult(rows=[]))

    response = client.get("/api/v1/analysis/logs", params={"limit": 20})
    body = response.json()

    assert response.status_code == 200
    assert "items" in body


def test_export_logs_accepts_json_payload(client: TestClient) -> None:
    response = client.post(
        "/api/v1/analysis/export",
        json={"format": "json", "include_tokens": False},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["format"] == "json"
    assert body["include_tokens"] is False


def test_pandas_analyze_accepts_json_payload(client: TestClient, monkeypatch) -> None:
    class _FakeAnalyzer:
        async def analyze(self, request):
            return SimpleNamespace(status="error", error_message="mock error")

    async def _fake_get_analyzer():
        return _FakeAnalyzer()

    monkeypatch.setattr(analysis_api, "get_analyzer", _fake_get_analyzer)

    response = client.post(
        "/api/v1/analysis/pandas-analyze",
        json={"dataset_reference": "demo.csv", "analysis_query": "统计条数"},
    )

    assert response.status_code == 400


def test_get_analysis_templates_accepts_get_request(client: TestClient) -> None:
    response = client.get("/api/v1/analysis/pandas-analyze/templates")
    body = response.json()

    assert response.status_code == 200
    assert isinstance(body.get("templates"), list)
