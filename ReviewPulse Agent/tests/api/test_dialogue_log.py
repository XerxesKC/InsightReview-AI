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

from app.api.v1 import dialogue_log as dialogue_log_api
from app.core.database import get_db


class _FakeResult:
    def __init__(self, scalar_value=None, rows=None, first_value=None):
        self._scalar_value = scalar_value
        self._rows = rows or []
        self._first_value = first_value

    def scalar_one(self):
        return self._scalar_value

    def scalar_one_or_none(self):
        return self._scalar_value

    def scalars(self):
        class _S:
            def __init__(self, rows):
                self._rows = rows

            def all(self):
                return self._rows

        return _S(self._rows)

    def all(self):
        return self._rows

    def first(self):
        return self._first_value


def _build_test_client(db_session: AsyncMock) -> TestClient:
    async def _fake_get_db():
        yield db_session

    app = FastAPI()
    app.include_router(dialogue_log_api.router, prefix="/api/v1")
    app.dependency_overrides[get_db] = _fake_get_db
    return TestClient(app)


@pytest.fixture
def db_session() -> AsyncMock:
    return AsyncMock(name="db_session")


@pytest.fixture
def client(db_session: AsyncMock) -> TestClient:
    return _build_test_client(db_session)


def test_get_dialogue_logs_accepts_query_params(client: TestClient, db_session: AsyncMock) -> None:
    db_session.execute = AsyncMock(
        side_effect=[
            _FakeResult(scalar_value=0),
            _FakeResult(rows=[]),
        ]
    )

    response = client.get("/api/v1/dialogue-log/list", params={"page": 1, "page_size": 10})
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 200


def test_get_dialogue_detail_accepts_path_params(client: TestClient, db_session: AsyncMock) -> None:
    db_session.execute = AsyncMock(
        side_effect=[
            _FakeResult(scalar_value=SimpleNamespace(session_id="s1", owner_id="u1", owner_type="user", title="t", created_at=None)),
            _FakeResult(rows=[]),
        ]
    )

    response = client.get("/api/v1/dialogue-log/detail/s1")
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 200


def test_export_dialogue_logs_accepts_query_params(client: TestClient, db_session: AsyncMock) -> None:
    db_session.execute = AsyncMock(return_value=_FakeResult(rows=[]))

    response = client.get("/api/v1/dialogue-log/export", params={"format": "csv"})

    assert response.status_code == 200


def test_get_dialogue_analysis_accepts_query_params(client: TestClient, db_session: AsyncMock) -> None:
    db_session.execute = AsyncMock(
        side_effect=[
            _FakeResult(rows=[]),
            _FakeResult(first_value=SimpleNamespace(total=0, success_count=0, avg_tokens=0)),
            _FakeResult(rows=[]),
        ]
    )

    response = client.get("/api/v1/dialogue-log/analysis", params={"days": 30})
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 200
