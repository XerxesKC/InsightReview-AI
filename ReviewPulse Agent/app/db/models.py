from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class KnowledgeBase(TimestampMixin, Base):
    __tablename__ = "knowledge_base"

    kb_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    admin_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    owner_type: Mapped[str] = mapped_column(String(20), index=True)
    owner_id: Mapped[str] = mapped_column(String(100), index=True)
    embedding_model: Mapped[str] = mapped_column(String(100), default="BAAI/bge-large-zh-v1.5")
    chroma_collection: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    is_deleted: Mapped[str] = mapped_column(String(1), default="F")


class Document(TimestampMixin, Base):
    __tablename__ = "document"

    doc_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    kb_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_base.kb_id"), nullable=True, index=True)
    uploader_type: Mapped[str] = mapped_column(String(20), index=True)
    uploader_id: Mapped[str] = mapped_column(String(100), index=True)
    doc_name: Mapped[str] = mapped_column(String(255), index=True)
    doc_type: Mapped[str] = mapped_column(String(20), default="txt")
    doc_size: Mapped[int] = mapped_column(BigInteger, default=0)
    file_path: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    chunk_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_overlap: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    is_deleted: Mapped[str] = mapped_column(String(1), default="F")


class ChatSession(TimestampMixin, Base):
    __tablename__ = "chat_session"

    session_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(100), index=True)
    owner_type: Mapped[str] = mapped_column(String(20), index=True)
    title: Mapped[str] = mapped_column(String(255), default="新会话")
    turn_count: Mapped[int] = mapped_column(Integer, default=0)
    active_turn_count: Mapped[int] = mapped_column(Integer, default=0)
    retrieval_top_k: Mapped[int | None] = mapped_column(Integer, nullable=True)
    similarity_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)


class ChatTurn(TimestampMixin, Base):
    __tablename__ = "chat_turn"

    turn_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("chat_session.session_id"), index=True)
    turn_no: Mapped[int] = mapped_column(Integer, default=1, index=True)
    query: Mapped[str] = mapped_column(Text)
    input_type: Mapped[str] = mapped_column(String(20), default="text", index=True)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer: Mapped[str] = mapped_column(Text)
    rewritten_query: Mapped[str | None] = mapped_column(Text, nullable=True)
    sources: Mapped[str] = mapped_column(Text, default="[]")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    tokens: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[int] = mapped_column(Integer, default=0)


class SystemConfig(TimestampMixin, Base):
    __tablename__ = "system_configs"

    config_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    config_key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    config_value: Mapped[str] = mapped_column(Text, default="")
