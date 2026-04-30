from __future__ import annotations

import asyncio

from app.core.security import get_current_user
from app.db.models import ChatSession, ChatTurn, Document, KnowledgeBase


def test_knowledge_base_schema_matches_shared_table() -> None:
    columns = KnowledgeBase.__table__.columns
    assert KnowledgeBase.__tablename__ == "knowledge_base"
    assert "kb_id" in columns
    assert "owner_type" in columns
    assert "owner_id" in columns
    assert "embedding_model" in columns
    assert "chroma_collection" in columns
    assert "is_deleted" in columns


def test_document_schema_matches_shared_table() -> None:
    columns = Document.__table__.columns
    assert Document.__tablename__ == "document"
    assert "doc_id" in columns
    assert "kb_id" in columns
    assert "uploader_type" in columns
    assert "uploader_id" in columns
    assert "doc_name" in columns
    assert "doc_type" in columns
    assert "doc_size" in columns
    assert "chunk_size" in columns
    assert "chunk_overlap" in columns
    assert "chunk_count" in columns
    assert "is_deleted" in columns


def test_chat_session_schema_supports_persistent_session_demo() -> None:
    columns = ChatSession.__table__.columns
    assert ChatSession.__tablename__ == "chat_session"
    assert "session_id" in columns
    assert "owner_id" in columns
    assert "owner_type" in columns
    assert "title" in columns
    assert "turn_count" in columns
    assert "active_turn_count" in columns
    assert "is_deleted" in columns


def test_chat_turn_schema_supports_turn_level_sources_and_context_demo() -> None:
    columns = ChatTurn.__table__.columns
    assert ChatTurn.__tablename__ == "chat_turn"
    assert "turn_id" in columns
    assert "session_id" in columns
    assert "turn_no" in columns
    assert "query" in columns
    assert "answer" in columns
    assert "rewritten_query" in columns
    assert "sources" in columns
    assert "is_active" in columns


def test_current_user_defaults_to_admin_actor_context() -> None:
    user = asyncio.run(get_current_user(x_user_id=None, x_user_type=None))
    assert user == {
        "user_id": "system",
        "user_type": "admin",
    }


def test_current_user_normalizes_headers() -> None:
    user = asyncio.run(get_current_user(x_user_id="m-100", x_user_type="Merchant"))
    assert user["user_id"] == "m-100"
    assert user["user_type"] == "merchant"
