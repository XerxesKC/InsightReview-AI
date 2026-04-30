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

from app.api.v1 import admin as admin_api
from app.core.database import get_db


def _build_test_client(db_session: AsyncMock) -> TestClient:
    async def _fake_get_db():
        yield db_session

    app = FastAPI()
    app.include_router(admin_api.router, prefix="/api/v1")
    app.dependency_overrides[get_db] = _fake_get_db
    return TestClient(app)


@pytest.fixture
def db_session() -> AsyncMock:
    return AsyncMock(name="db_session")


@pytest.fixture
def client(db_session: AsyncMock) -> TestClient:
    return _build_test_client(db_session)


def test_save_config_accepts_json_payload(client: TestClient, monkeypatch) -> None:
    async def _fake_upsert_system_config(session, key, value):
        return SimpleNamespace(config_id=1, config_key=key, config_value=value)

    monkeypatch.setattr(admin_api, "upsert_system_config", _fake_upsert_system_config)

    response = client.post("/api/v1/admin/config", json={"key": "k", "value": "v"})
    body = response.json()

    assert response.status_code == 200
    assert body["key"] == "k"
    assert body["value"] == "v"


def test_trigger_fine_tune_accepts_json_payload(client: TestClient) -> None:
    response = client.post(
        "/api/v1/admin/fine-tune",
        json={"model_name": "qwen-test", "dataset_path": "data/finetune/demo.jsonl"},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "accepted"
    assert body["dataset_path"] == "data/finetune/demo.jsonl"


def test_get_embedding_models_accepts_get_request(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(
        admin_api,
        "list_local_embedding_models",
        lambda _: [{"name": "BAAI/bge-small", "path": "data/bge-model/BAAI/bge-small"}],
    )

    async def _fake_get_system_config_value(session, key):
        return None

    monkeypatch.setattr(admin_api, "get_system_config_value", _fake_get_system_config_value)

    response = client.get("/api/v1/admin/system/embedding-models")
    body = response.json()

    assert response.status_code == 200
    assert isinstance(body["models"], list)


def test_set_embedding_model_accepts_put_json_payload(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(
        admin_api,
        "list_local_embedding_models",
        lambda _: [{"name": "BAAI/bge-small", "path": "data/bge-model/BAAI/bge-small"}],
    )

    async def _fake_upsert_system_config_map(session, items):
        return None

    monkeypatch.setattr(admin_api, "upsert_system_config_map", _fake_upsert_system_config_map)

    response = client.put(
        "/api/v1/admin/system/embedding-model",
        json={"modelName": "BAAI/bge-small", "modelPath": "data/bge-model/BAAI/bge-small"},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True


def test_get_system_params_accepts_get_request(client: TestClient, monkeypatch) -> None:
    async def _fake_get_system_config_map(session, keys):
        return {}

    monkeypatch.setattr(admin_api, "get_system_config_map", _fake_get_system_config_map)

    response = client.get("/api/v1/admin/system/params")
    body = response.json()

    assert response.status_code == 200
    assert "chunkSize" in body


def test_update_system_params_accepts_put_json_payload(client: TestClient, monkeypatch) -> None:
    async def _fake_upsert_system_config_map(session, items):
        return None

    monkeypatch.setattr(admin_api, "upsert_system_config_map", _fake_upsert_system_config_map)

    response = client.put(
        "/api/v1/admin/system/params",
        json={
            "chunkSize": 500,
            "chunkOverlap": 50,
            "fileUploadMaxSizeMB": 10,
            "vectorStorePath": "data/chroma",
            "requestTimeoutMs": 30000,
            "chatMaxContextTurns": 10,
            "chatMaxContextTokens": 3000,
            "chatRetrievalTopK": 4,
            "chatSimilarityThreshold": 0.2,
            "chatAnswerMaxChars": 500,
            "chatRetrievalTimeoutMs": 8000,
            "chatGenerationTimeoutMs": 15000,
            "chatVectorCacheEnabled": True,
            "chatVectorCacheBackend": "auto",
            "chatVectorCacheTtlSeconds": 300,
            "chatContextBackend": "auto",
        },
    )
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
