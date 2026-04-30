from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.api.v1 import knowledge as knowledge_api
from app.core.database import get_db


class _FakeStoredPath:
    def __init__(self, file_path: str = "data/files/u_demo.txt", file_name: str = "u_demo.txt", size: int = 12):
        self._file_path = file_path
        self.name = file_name
        self._size = size

    def stat(self):
        return SimpleNamespace(st_size=self._size)

    def __str__(self):
        return self._file_path


def _build_test_client(db_session: AsyncMock) -> TestClient:
    async def _override_get_db():
        yield db_session

    app = FastAPI()
    app.include_router(knowledge_api.router, prefix="/api/v1")
    app.dependency_overrides[get_db] = _override_get_db
    return TestClient(app)


def _install_fake_chromadb(monkeypatch, names: list[str]) -> None:
    fake_module = ModuleType("chromadb")

    class _FakeClient:
        def list_collections(self):
            return [SimpleNamespace(name=item) for item in names]

    fake_module.PersistentClient = lambda path: _FakeClient()
    monkeypatch.setitem(sys.modules, "chromadb", fake_module)


@pytest.fixture
def db_session() -> AsyncMock:
    return AsyncMock(name="db_session")


@pytest.fixture
def client(db_session: AsyncMock) -> TestClient:
    return _build_test_client(db_session)


def test_upload_document_happy_path_returns_200(client: TestClient, monkeypatch) -> None:
    async def _fake_get_system_config_value(session, key):
        return "10"

    async def _fake_save_upload_file(file, max_upload_size_mb=None):
        return _FakeStoredPath(file_name="demo.txt")

    async def _fake_create_document(session, **kwargs):
        return SimpleNamespace(doc_id=1, status="pending", uploader_type="merchant", uploader_id=1001)

    async def _fake_enqueue_ingest_document(path):
        return "task-1"

    monkeypatch.setattr(knowledge_api, "get_system_config_value", _fake_get_system_config_value)
    monkeypatch.setattr(knowledge_api, "save_upload_file", _fake_save_upload_file)
    monkeypatch.setattr(knowledge_api, "create_document", _fake_create_document)
    monkeypatch.setattr(knowledge_api, "enqueue_ingest_document", _fake_enqueue_ingest_document)

    response = client.post(
        "/api/v1/knowledge/upload",
        data={"uploader_type": "merchant", "uploader_id": "1001"},
        files={"file": ("demo.txt", b"hello", "text/plain")},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 200
    assert body["data"]["doc_id"] == 1


def test_upload_document_not_found_returns_404(client: TestClient, monkeypatch) -> None:
    async def _fake_get_system_config_value(session, key):
        return None

    async def _fake_save_upload_file(file, max_upload_size_mb=None):
        raise HTTPException(status_code=404, detail="文件不存在")

    monkeypatch.setattr(knowledge_api, "get_system_config_value", _fake_get_system_config_value)
    monkeypatch.setattr(knowledge_api, "save_upload_file", _fake_save_upload_file)

    response = client.post(
        "/api/v1/knowledge/upload",
        data={"uploader_type": "merchant", "uploader_id": "1001"},
        files={"file": ("demo.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 404


def test_get_documents_happy_path_returns_200(client: TestClient, monkeypatch) -> None:
    async def _fake_list_documents(session, user_type, user_id, kb_id=None):
        return [
            SimpleNamespace(
                doc_id=1,
                kb_id=10,
                doc_name="demo.txt",
                doc_type="txt",
                doc_size=100,
                file_path="data/files/demo.txt",
                status="pending",
                uploader_type="merchant",
                uploader_id=1001,
                chunk_size=500,
                chunk_overlap=50,
                chunk_count=2,
                created_at=None,
            )
        ]

    monkeypatch.setattr(knowledge_api, "list_documents", _fake_list_documents)

    response = client.get("/api/v1/knowledge/list", params={"user_type": "merchant", "user_id": 1001})
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 200
    assert len(body["data"]["items"]) == 1


def test_get_documents_not_found_returns_404(client: TestClient, monkeypatch) -> None:
    async def _fake_list_documents(session, user_type, user_id, kb_id=None):
        raise HTTPException(status_code=404, detail="文档不存在")

    monkeypatch.setattr(knowledge_api, "list_documents", _fake_list_documents)

    response = client.get("/api/v1/knowledge/list", params={"user_type": "merchant", "user_id": 1001})

    assert response.status_code == 404


def test_delete_document_happy_path_returns_200(client: TestClient, monkeypatch) -> None:
    current_doc = SimpleNamespace(doc_id=1, is_deleted="F", doc_name="demo.txt", uploader_type="merchant", uploader_id=1001)
    history_doc = SimpleNamespace(doc_id=2)

    async def _fake_get_document_by_id(session, document_id):
        return current_doc

    async def _fake_list_document_versions(session, doc_name, uploader_type, uploader_id, current_doc_id):
        return [history_doc]

    async def _fake_soft_delete_document(session, document_id):
        return SimpleNamespace(doc_id=document_id, doc_name="demo.txt")

    monkeypatch.setattr(knowledge_api, "get_document_by_id", _fake_get_document_by_id)
    monkeypatch.setattr(knowledge_api, "list_document_versions", _fake_list_document_versions)
    monkeypatch.setattr(knowledge_api, "soft_delete_document", _fake_soft_delete_document)

    response = client.delete("/api/v1/knowledge/delete", params={"document_id": 1})
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 200
    assert body["data"]["items"][0]["total_deleted"] == 2


def test_delete_document_not_found_returns_404(client: TestClient, monkeypatch) -> None:
    async def _fake_get_document_by_id(session, document_id):
        return None

    monkeypatch.setattr(knowledge_api, "get_document_by_id", _fake_get_document_by_id)

    response = client.delete("/api/v1/knowledge/delete", params={"document_id": 1})

    assert response.status_code == 404


def test_edit_document_happy_path_returns_200(client: TestClient, monkeypatch) -> None:
    async def _fake_get_system_config_value(session, key):
        return "10"

    async def _fake_save_upload_file(file, max_upload_size_mb=None):
        return _FakeStoredPath(file_name="edited.txt")

    async def _fake_update_document(session, doc_id, **kwargs):
        return SimpleNamespace(doc_id=doc_id, doc_name="edited.txt", status="pending")

    async def _fake_enqueue_ingest_document(path):
        return "task-2"

    monkeypatch.setattr(knowledge_api, "get_system_config_value", _fake_get_system_config_value)
    monkeypatch.setattr(knowledge_api, "save_upload_file", _fake_save_upload_file)
    monkeypatch.setattr(knowledge_api, "update_document", _fake_update_document)
    monkeypatch.setattr(knowledge_api, "enqueue_ingest_document", _fake_enqueue_ingest_document)

    response = client.post(
        "/api/v1/knowledge/edit",
        data={"doc_id": "1", "kb_id": "10"},
        files={"file": ("edited.txt", b"hello", "text/plain")},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 200
    assert body["data"]["updated"] is True


def test_edit_document_not_found_returns_404(client: TestClient, monkeypatch) -> None:
    async def _fake_get_system_config_value(session, key):
        return None

    async def _fake_save_upload_file(file, max_upload_size_mb=None):
        raise HTTPException(status_code=404, detail="文件不存在")

    monkeypatch.setattr(knowledge_api, "get_system_config_value", _fake_get_system_config_value)
    monkeypatch.setattr(knowledge_api, "save_upload_file", _fake_save_upload_file)

    response = client.post(
        "/api/v1/knowledge/edit",
        data={"doc_id": "1"},
        files={"file": ("edited.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 404


def test_download_document_happy_path_returns_200(client: TestClient, monkeypatch) -> None:
    async def _fake_get_document_by_id(session, doc_id):
        return SimpleNamespace(doc_name="demo.txt", file_path="data/files/demo.txt")

    monkeypatch.setattr(knowledge_api, "get_document_by_id", _fake_get_document_by_id)
    monkeypatch.setattr(knowledge_api.Path, "is_file", lambda self: True)
    monkeypatch.setattr(
        knowledge_api,
        "FileResponse",
        lambda path, filename, content_disposition_type: JSONResponse({"code": 200, "msg": "ok", "filename": filename}),
    )

    response = client.get("/api/v1/knowledge/download", params={"doc_id": 1})
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 200
    assert body["filename"] == "demo.txt"


def test_download_document_not_found_returns_404(client: TestClient, monkeypatch) -> None:
    async def _fake_get_document_by_id(session, doc_id):
        return None

    monkeypatch.setattr(knowledge_api, "get_document_by_id", _fake_get_document_by_id)

    response = client.get("/api/v1/knowledge/download", params={"doc_id": 1})

    assert response.status_code == 404


def test_create_knowledge_base_happy_path_returns_200(client: TestClient, monkeypatch) -> None:
    async def _fake_create_kb_db(db, **kwargs):
        return SimpleNamespace(
            kb_id=1,
            admin_id="admin-1",
            name="KB",
            description="desc",
            owner_type="merchant",
            owner_id="1001",
            embedding_model="bge",
            chroma_collection="",
        )

    monkeypatch.setattr(knowledge_api, "create_kb_db", _fake_create_kb_db)

    response = client.post(
        "/api/v1/knowledge_base/create",
        json={
            "admin_id": "admin-1",
            "name": "KB",
            "description": "desc",
            "owner_type": "merchant",
            "owner_id": "1001",
            "embedding_model": "bge",
            "chroma_collection": "",
        },
    )
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 200
    assert body["data"]["id"] == 1


def test_create_knowledge_base_not_found_returns_404(client: TestClient, monkeypatch) -> None:
    async def _fake_create_kb_db(db, **kwargs):
        raise HTTPException(status_code=404, detail="管理员不存在")

    monkeypatch.setattr(knowledge_api, "create_kb_db", _fake_create_kb_db)

    response = client.post(
        "/api/v1/knowledge_base/create",
        json={
            "admin_id": "admin-1",
            "name": "KB",
            "description": "desc",
            "owner_type": "merchant",
            "owner_id": "1001",
            "embedding_model": "bge",
            "chroma_collection": "",
        },
    )

    assert response.status_code == 404


def test_list_knowledge_bases_happy_path_returns_200(client: TestClient, monkeypatch) -> None:
    async def _fake_list_kbs_db(db, name=None, owner_type=None, created_from=None, created_to=None):
        return [
            SimpleNamespace(
                kb_id=1,
                admin_id="admin-1",
                name="KB",
                description="desc",
                owner_type="merchant",
                owner_id="1001",
                embedding_model="bge",
                chroma_collection="m_1001",
                created_at=None,
            )
        ]

    async def _fake_get_owner_name(db, owner_type, owner_id):
        return "张三"

    monkeypatch.setattr(knowledge_api, "list_kbs_db", _fake_list_kbs_db)
    monkeypatch.setattr(knowledge_api, "get_owner_name", _fake_get_owner_name)

    response = client.get("/api/v1/knowledge_base/list")
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 200
    assert body["data"][0]["owner_name"] == "张三"


def test_list_knowledge_bases_not_found_returns_404(client: TestClient, monkeypatch) -> None:
    async def _fake_list_kbs_db(db, name=None, owner_type=None, created_from=None, created_to=None):
        raise HTTPException(status_code=404, detail="知识库不存在")

    monkeypatch.setattr(knowledge_api, "list_kbs_db", _fake_list_kbs_db)

    response = client.get("/api/v1/knowledge_base/list")

    assert response.status_code == 404


def test_get_kb_options_happy_path_returns_200(client: TestClient, monkeypatch) -> None:
    _install_fake_chromadb(monkeypatch, ["merchant_1001"])
    monkeypatch.setattr(knowledge_api.Path, "exists", lambda self: True)
    monkeypatch.setattr(
        knowledge_api,
        "get_settings",
        lambda: SimpleNamespace(
            chroma_path="data/chroma",
            embedding_models_root="data/bge-model",
            bge_model_path="data/bge-model/BAAI/bge",
            bge_model_name="BAAI/bge",
        ),
    )
    monkeypatch.setattr(
        knowledge_api,
        "list_local_embedding_models",
        lambda root: [{"name": "BAAI/bge", "path": "data/bge-model/BAAI/bge"}],
    )
    monkeypatch.setattr(knowledge_api, "resolve_local_embedding_model_path", lambda **kwargs: Path("data/bge-model/BAAI/bge"))

    response = client.get("/api/v1/knowledge_base/options")
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 200
    assert "embedding_models" in body["data"]


def test_get_kb_options_not_found_returns_404(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(
        knowledge_api,
        "list_local_embedding_models",
        lambda root: (_ for _ in ()).throw(HTTPException(status_code=404, detail="模型不存在")),
    )

    response = client.get("/api/v1/knowledge_base/options")

    assert response.status_code == 404


def test_get_vector_collections_happy_path_returns_200(client: TestClient, monkeypatch) -> None:
    _install_fake_chromadb(monkeypatch, ["merchant_1001", "merchant_1002"])
    monkeypatch.setattr(knowledge_api.Path, "exists", lambda self: True)

    response = client.get("/api/v1/knowledge_base/vector_collections")
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 200
    assert isinstance(body["data"], list)


def test_get_vector_collections_not_found_returns_404(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(
        knowledge_api.Path,
        "exists",
        lambda self: (_ for _ in ()).throw(HTTPException(status_code=404, detail="向量库目录不存在")),
    )

    response = client.get("/api/v1/knowledge_base/vector_collections")

    assert response.status_code == 404


def test_get_embedding_models_happy_path_returns_200(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(
        knowledge_api,
        "get_settings",
        lambda: SimpleNamespace(embedding_models_root="data/bge-model"),
    )
    monkeypatch.setattr(
        knowledge_api,
        "list_local_embedding_models",
        lambda root: [{"name": "BAAI/bge", "path": "data/bge-model/BAAI/bge"}],
    )

    response = client.get("/api/v1/knowledge_base/models")
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 200
    assert body["data"] == ["BAAI/bge"]


def test_get_embedding_models_not_found_returns_404(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(
        knowledge_api,
        "list_local_embedding_models",
        lambda root: (_ for _ in ()).throw(HTTPException(status_code=404, detail="模型目录不存在")),
    )

    response = client.get("/api/v1/knowledge_base/models")

    assert response.status_code == 404


def test_get_owners_happy_path_returns_200(client: TestClient, monkeypatch) -> None:
    async def _fake_list_owners(db, owner_type, keyword):
        return [{"id": "1001", "name": "张三"}]

    monkeypatch.setattr(knowledge_api, "list_owners", _fake_list_owners)

    response = client.get("/api/v1/knowledge_base/owners", params={"owner_type": "merchant", "keyword": "张"})
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 200
    assert body["data"][0]["name"] == "张三"


def test_get_owners_not_found_returns_404(client: TestClient, monkeypatch) -> None:
    async def _fake_list_owners(db, owner_type, keyword):
        raise RuntimeError("负责人不存在")

    monkeypatch.setattr(knowledge_api, "list_owners", _fake_list_owners)

    response = client.get("/api/v1/knowledge_base/owners", params={"owner_type": "merchant"})
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 500


def test_get_knowledge_base_happy_path_returns_200(client: TestClient, monkeypatch) -> None:
    async def _fake_get_kb_db(db, kb_id):
        return SimpleNamespace(
            kb_id=1,
            admin_id="admin-1",
            name="测试知识库",
            description="用于测试",
            owner_type="merchant",
            owner_id="1001",
            embedding_model="bge",
            chroma_collection="merchant_1001",
        )

    monkeypatch.setattr(knowledge_api, "get_kb_db", _fake_get_kb_db)

    response = client.get("/api/v1/knowledge_base/1")
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 200
    assert body["data"]["id"] == 1


def test_get_knowledge_base_not_found_returns_404(client: TestClient, monkeypatch) -> None:
    async def _fake_get_kb_db(db, kb_id):
        return None

    monkeypatch.setattr(knowledge_api, "get_kb_db", _fake_get_kb_db)

    response = client.get("/api/v1/knowledge_base/9999")

    assert response.status_code == 404


def test_update_knowledge_base_happy_path_returns_200(client: TestClient, monkeypatch) -> None:
    async def _fake_update_kb_db(db, kb_id, **kwargs):
        return SimpleNamespace(
            kb_id=kb_id,
            admin_id="admin-1",
            name="KB-Updated",
            description="desc",
            owner_type="merchant",
            owner_id="1001",
            embedding_model="bge",
            chroma_collection="merchant_1001",
        )

    monkeypatch.setattr(knowledge_api, "update_kb_db", _fake_update_kb_db)

    response = client.post("/api/v1/knowledge_base/update", params={"kb_id": 1}, json={"name": "KB-Updated"})
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 200
    assert body["data"]["name"] == "KB-Updated"


def test_update_knowledge_base_not_found_returns_404(client: TestClient, monkeypatch) -> None:
    async def _fake_update_kb_db(db, kb_id, **kwargs):
        return None

    monkeypatch.setattr(knowledge_api, "update_kb_db", _fake_update_kb_db)

    response = client.post("/api/v1/knowledge_base/update", params={"kb_id": 1}, json={"name": "KB-Updated"})

    assert response.status_code == 404


def test_delete_knowledge_base_happy_path_returns_200(client: TestClient, monkeypatch) -> None:
    async def _fake_delete_kb_db(db, kb_id):
        return SimpleNamespace(kb_id=kb_id)

    monkeypatch.setattr(knowledge_api, "delete_kb_db", _fake_delete_kb_db)

    response = client.post("/api/v1/knowledge_base/delete", params={"kb_id": 1})
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 200
    assert body["data"]["deleted"] is True


def test_delete_knowledge_base_not_found_returns_404(client: TestClient, monkeypatch) -> None:
    async def _fake_delete_kb_db(db, kb_id):
        return None

    monkeypatch.setattr(knowledge_api, "delete_kb_db", _fake_delete_kb_db)

    response = client.post("/api/v1/knowledge_base/delete", params={"kb_id": 1})

    assert response.status_code == 404


def test_check_duplicate_document_happy_path_returns_200(client: TestClient, monkeypatch) -> None:
    async def _fake_check_duplicate_document(session, doc_name, uploader_type, uploader_id):
        return [SimpleNamespace(doc_id=1)]

    monkeypatch.setattr(knowledge_api, "check_duplicate_document", _fake_check_duplicate_document)

    response = client.get(
        "/api/v1/knowledge/check-duplicate",
        params={"doc_name": "demo.txt", "uploader_type": "merchant", "uploader_id": 1001},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 200
    assert body["data"]["exists"] is True


def test_check_duplicate_document_not_found_returns_404(client: TestClient, monkeypatch) -> None:
    async def _fake_check_duplicate_document(session, doc_name, uploader_type, uploader_id):
        raise HTTPException(status_code=404, detail="上传者不存在")

    monkeypatch.setattr(knowledge_api, "check_duplicate_document", _fake_check_duplicate_document)

    response = client.get(
        "/api/v1/knowledge/check-duplicate",
        params={"doc_name": "demo.txt", "uploader_type": "merchant", "uploader_id": 1001},
    )

    assert response.status_code == 404


def test_deprecated_document_happy_path_returns_200(client: TestClient, monkeypatch) -> None:
    async def _fake_deprecated_document(session, document_id):
        return SimpleNamespace(doc_id=document_id, status="deprecated")

    monkeypatch.setattr(knowledge_api, "deprecated_document", _fake_deprecated_document)

    response = client.post("/api/v1/knowledge/deprecated_document", params={"document_id": 1})
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 200
    assert body["data"]["status"] == "deprecated"


def test_deprecated_document_not_found_returns_404(client: TestClient, monkeypatch) -> None:
    async def _fake_deprecated_document(session, document_id):
        return None

    monkeypatch.setattr(knowledge_api, "deprecated_document", _fake_deprecated_document)

    response = client.post("/api/v1/knowledge/deprecated_document", params={"document_id": 1})

    assert response.status_code == 404


def test_get_document_history_happy_path_returns_200(client: TestClient, monkeypatch) -> None:
    async def _fake_list_document_versions(session, doc_name, uploader_type, uploader_id, current_doc_id):
        return [
            SimpleNamespace(
                doc_id=1,
                doc_name=doc_name,
                doc_type="txt",
                doc_size=100,
                status="deprecated",
                created_at=None,
                file_path="data/files/demo.txt",
            )
        ]

    monkeypatch.setattr(knowledge_api, "list_document_versions", _fake_list_document_versions)

    response = client.get(
        "/api/v1/knowledge/history_document",
        params={
            "doc_name": "demo.txt",
            "uploader_type": "merchant",
            "uploader_id": 1001,
            "current_doc_id": 2,
        },
    )
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 200
    assert len(body["data"]["items"]) == 1


def test_get_document_history_not_found_returns_404(client: TestClient, monkeypatch) -> None:
    async def _fake_list_document_versions(session, doc_name, uploader_type, uploader_id, current_doc_id):
        raise HTTPException(status_code=404, detail="历史文档不存在")

    monkeypatch.setattr(knowledge_api, "list_document_versions", _fake_list_document_versions)

    response = client.get(
        "/api/v1/knowledge/history_document",
        params={
            "doc_name": "demo.txt",
            "uploader_type": "merchant",
            "uploader_id": 1001,
            "current_doc_id": 2,
        },
    )

    assert response.status_code == 404


def test_activate_document_happy_path_returns_200(client: TestClient, monkeypatch) -> None:
    async def _fake_activate_document(session, document_id):
        return SimpleNamespace(doc_id=document_id, status="active")

    monkeypatch.setattr(knowledge_api, "activate_document", _fake_activate_document)

    response = client.post("/api/v1/knowledge/activate_document", params={"document_id": 1})
    body = response.json()

    assert response.status_code == 200
    assert body["code"] == 200
    assert body["data"]["status"] == "active"


def test_activate_document_not_found_returns_404(client: TestClient, monkeypatch) -> None:
    async def _fake_activate_document(session, document_id):
        return None

    monkeypatch.setattr(knowledge_api, "activate_document", _fake_activate_document)

    response = client.post("/api/v1/knowledge/activate_document", params={"document_id": 1})

    assert response.status_code == 404
