from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import PurePosixPath
import re
import time
from collections.abc import AsyncIterator
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.agents.chat.graph import ChatGraphCallbacks
from app.agents.chat.orchestrator import create_orchestrator
from app.agents.chat.state import ChatGraphState
from app.api.deps import CurrentUser, DBSession
from app.core.chat_redis_trace import log_chat_context_store_call
from app.core.config import get_settings
from app.core.datetime_utils import to_rfc3339
from app.core.retrieval_cache import build_vector_cache_key, get_vector_cache_items, set_vector_cache_items
from app.core.redis_client import clear_cached_chat_context, get_cached_chat_context, set_cached_chat_context
from app.db.crud import (
    clear_chat_context,
    create_chat_turn,
    delete_chat_session,
    get_chat_context,
    get_chat_session_for_actor,
    get_system_config_map,
    list_chat_sessions,
    list_chat_turns,
    list_knowledge_bases,
    rename_chat_session,
    rollback_chat_context,
    update_chat_session_retrieval_config,
    update_chat_turn_rating,
)
from app.rag.intent_router import master_router
from app.rag.llm import answer_with_context, answer_with_context_stream, rewrite_question, invoke_chat,\
    invoke_chat_stream
from app.rag.vector_store import get_vector_store
from app.services.chat_ocr import extract_text_from_image
from app.services.file_handler import save_upload_file
from app.tools.executor import process_tool_use_intent

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    role: str = Field(default="user")
    content: str


class ChatCompletionRequest(BaseModel):
    messages: list[ChatMessage] = Field(default_factory=list)
    stream: bool = False
    model: str | None = None
    session_id: str | None = None
    max_context_turns: int | None = Field(default=None, ge=1, le=50)
    image_id: str | None = None
    image_url: str | None = None
    file_ids: list[str] | None = Field(default=None, description="上传的数据文件 doc_id 列表")


class RollbackRequest(BaseModel):
    turn_no: int = Field(..., ge=1)


class RenameSessionRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)


class SessionRetrievalConfigPayload(BaseModel):
    top_k: int | None = Field(default=None, ge=1, le=20)
    similarity_threshold: float | None = Field(default=None, ge=0, le=1)


class ChatTurnRatingUpdate(BaseModel):
    session_id: str
    turn_no: int
    rating: int = Field(..., ge=-1, le=1)  


class SensitiveWordFilter:
    def __init__(self, words: list[str] = None):
        self.words = words
        self.max_word_len = max([len(w) for w in self.words]) if self.words else 0

        if self.words:
            escaped_words = [re.escape(w) for w in sorted(self.words, key=len, reverse=True)]
            self.pattern = re.compile("|".join(escaped_words), re.IGNORECASE)
        else:
            self.pattern = None

    def filter(self, text: str) -> str:
        if not text or not self.pattern:
            return text
        return self.pattern.sub(lambda m: "*" * len(m.group()), text)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
SENSITIVE_WORDS_PATH = BASE_DIR / "sensitive_words.txt"

def load_sensitive_words(filepath: Path = SENSITIVE_WORDS_PATH) -> list[str]:

    if not os.path.exists(filepath):
        return []

    words = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            word = line.strip()
            if word and not word.startswith("#"):
                words.append(word)
    return words

sensitive_filter = SensitiveWordFilter(load_sensitive_words())

def _parse_sources(raw_sources: str | list[dict] | None) -> list[dict]:
    if isinstance(raw_sources, list):
        return raw_sources
    if not raw_sources:
        return []
    try:
        parsed = json.loads(raw_sources)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _serialize_turn_item(item) -> dict:
    return {
        "turn_id": item.turn_id,
        "turn_no": item.turn_no,
        "query": item.query,
        "input_type": getattr(item, "input_type", "text"),
        "ocr_text": getattr(item, "ocr_text", None),
        "answer": item.answer,
        "rewritten_query": item.rewritten_query,
        "sources": _parse_sources(item.sources),
        "created_at": to_rfc3339(item.created_at),
        "is_active": item.is_active,
        "rating": item.rating if hasattr(item, 'rating') else 0,
    }


def _serialize_session_item(item) -> dict:
    return {
        "session_id": item.session_id,
        "title": item.title,
        "turn_count": item.turn_count,
        "active_turn_count": item.active_turn_count,
        "retrieval_top_k": item.retrieval_top_k,
        "similarity_threshold": item.similarity_threshold,
        "created_at": to_rfc3339(item.created_at),
        "updated_at": to_rfc3339(item.updated_at),
        "is_deleted": item.is_deleted,
    }


def _sanitize_sources(items: list[dict]) -> list[dict]:
    sanitized: list[dict] = []
    for item in items:
        metadata = item.get("metadata", {})
        sanitized.append(
            {
                "source": item.get("source") or item.get("metadata", {}).get("source") or "知识库文档",
                "content": item.get("content", ""),
                "score": item.get("score"),
                "vector_score": item.get("vector_score"),
                "bm25_score": item.get("bm25_score"),
                "distance": item.get("distance"),
                "chunk_index": item.get("chunk_index"),
                "document_id": item.get("document_id") or metadata.get("document_id"),
                "kb_name": item.get("kb_name") or metadata.get("kb_name"),
            }
        )
    return sanitized


def _normalize_hybrid_weights(vector_weight: float, bm25_weight: float) -> tuple[float, float]:
    safe_vector = max(float(vector_weight), 0.0)
    safe_bm25 = max(float(bm25_weight), 0.0)
    total = safe_vector + safe_bm25
    if total <= 0:
        return 0.5, 0.5
    return safe_vector / total, safe_bm25 / total


def _rank_map(values: list[float]) -> dict[int, int]:
    ordered = sorted(range(len(values)), key=lambda idx: values[idx], reverse=True)
    return {doc_index: rank + 1 for rank, doc_index in enumerate(ordered)}


def _normalize_scores(values: list[float]) -> list[float]:
    if not values:
        return []
    minimum = min(values)
    maximum = max(values)
    if maximum <= minimum:
        return [1.0 if maximum > 0 else 0.0 for _ in values]
    return [(value - minimum) / (maximum - minimum) for value in values]


def _merge_key_for_hybrid_item(item: dict) -> str:
    item_id = item.get("id")
    if item_id:
        return f"id:{item_id}"
    metadata = item.get("metadata") or {}
    kb_name = str(item.get("kb_name") or metadata.get("kb_name") or "")
    source = str(item.get("source") or metadata.get("source") or "")
    chunk_index = item.get("chunk_index", metadata.get("chunk_index", ""))
    return f"kb:{kb_name}|source:{source}|chunk:{chunk_index}"


def _deduplicate_hybrid_items(items: list[dict]) -> list[dict]:
    if not items:
        return []

    merged: dict[str, dict] = {}
    for item in items:
        key = _merge_key_for_hybrid_item(item)
        if key not in merged:
            merged[key] = dict(item)
            continue

        current = merged[key]
        current["vector_score"] = max(float(current.get("vector_score") or 0.0), float(item.get("vector_score") or 0.0))
        current["bm25_score"] = max(float(current.get("bm25_score") or 0.0), float(item.get("bm25_score") or 0.0))
        current["score"] = max(float(current.get("score") or 0.0), float(item.get("score") or 0.0))
        if current.get("distance") is None:
            current["distance"] = item.get("distance")
        if not current.get("content") and item.get("content"):
            current["content"] = item.get("content")
        if not current.get("metadata") and item.get("metadata"):
            current["metadata"] = item.get("metadata")
        if not current.get("source") and item.get("source"):
            current["source"] = item.get("source")
        if current.get("chunk_index") is None and item.get("chunk_index") is not None:
            current["chunk_index"] = item.get("chunk_index")

    return list(merged.values())


def _rerank_merged_hybrid_items(
    *,
    query: str,
    items: list[dict],
    vector_weight: float,
    bm25_weight: float,
    rrf_k: int,
) -> list[dict]:
    if not items:
        return []

    w_vector, w_bm25 = _normalize_hybrid_weights(vector_weight, bm25_weight)
    vector_values = [float(item.get("vector_score") or 0.0) for item in items]
    bm25_values = [float(item.get("bm25_score") or 0.0) for item in items]
    vector_rank_map = _rank_map(vector_values)
    bm25_rank_map = _rank_map(bm25_values)

    fused_raw: list[float] = []
    for index, item in enumerate(items):
        vector_rank = vector_rank_map.get(index)
        bm25_rank = bm25_rank_map.get(index)
        fused = 0.0
        if vector_rank is not None:
            fused += w_vector / (rrf_k + vector_rank)
        if bm25_rank is not None:
            fused += w_bm25 / (rrf_k + bm25_rank)

        kb_name = str(item.get("kb_name") or "").strip()
        if kb_name and kb_name in query:
            fused += 0.02
        fused_raw.append(fused)

    fused_normalized = _normalize_scores(fused_raw)
    reranked: list[dict] = []
    for index, item in enumerate(items):
        updated = dict(item)
        updated["score"] = round(float(fused_normalized[index]), 6)
        reranked.append(updated)
    reranked.sort(key=lambda row: float(row.get("score") or 0), reverse=True)
    return reranked


def _log_hybrid_retrieval_scores(
    *,
    session_id: str,
    actor: dict[str, str],
    query: str,
    vector_weight: float,
    bm25_weight: float,
    top_k: int,
    threshold: float,
    items: list[dict],
) -> None:
    settings = get_settings()
    if not settings.chat_hybrid_log_enabled:
        return

    payload = {
        "timestamp": to_rfc3339(datetime.now(timezone.utc)),
        "session_id": session_id,
        "actor": {"user_type": actor.get("user_type"), "user_id": actor.get("user_id")},
        "query": query,
        "vector_weight": vector_weight,
        "bm25_weight": bm25_weight,
        "top_k": top_k,
        "similarity_threshold": threshold,
        "items": [
            {
                "kb_name": item.get("kb_name"),
                "source": item.get("source"),
                "chunk_index": item.get("chunk_index"),
                "score": item.get("score"),
                "vector_score": item.get("vector_score"),
                "bm25_score": item.get("bm25_score"),
            }
            for item in items
        ],
    }

    try:
        log_file = settings.log_path / settings.chat_hybrid_log_filename
        with log_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        logger.exception("Failed to write hybrid retrieval diagnostics log")


def _fallback_answer(question: str, sources: list[dict]) -> str:
    if sources:
        top_source = sources[0]
        source_name = top_source.get("source") or "知识库文档"
        snippet = str(top_source.get("content", "")).strip()
        snippet = snippet[:200] + ("..." if len(snippet) > 200 else "")
        return f"根据知识库《{source_name}》检索到的相关内容：{snippet}"
    return f"已收到消息：{question}"


def _parse_int(value: str | int | None, default: int, *, min_value: int, max_value: int) -> int:
    try:
        parsed = int(value) if value is not None else int(default)
    except (TypeError, ValueError):
        parsed = int(default)
    return max(min(parsed, max_value), min_value)


def _parse_float(value: str | float | None, default: float, *, min_value: float, max_value: float) -> float:
    try:
        parsed = float(value) if value is not None else float(default)
    except (TypeError, ValueError):
        parsed = float(default)
    return max(min(parsed, max_value), min_value)


def _parse_bool(value: str | bool | int | None, default: bool) -> bool:
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return bool(default)


def _normalize_context_backend(value: str | None) -> str:
    selected = (value or "auto").strip().lower()
    if selected in {"auto", "redis", "mysql"}:
        return selected
    return "auto"


def _extract_image_id_from_url(image_url: str) -> str | None:
    if not image_url:
        return None
    parsed = urlparse(image_url)
    last_segment = PurePosixPath(parsed.path).name
    image_id = last_segment.strip()
    if re.fullmatch(r"[a-f0-9]{32}", image_id):
        return image_id
    return None


def _resolve_chat_image_path(*, image_id: str | None, image_url: str | None) -> Path | None:
    settings = get_settings()
    resolved_image_id = (image_id or "").strip().lower()
    if not resolved_image_id and image_url:
        resolved_image_id = _extract_image_id_from_url(image_url) or ""

    if not resolved_image_id:
        return None
    if not re.fullmatch(r"[a-f0-9]{32}", resolved_image_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="image_id 格式非法。")

    candidates = sorted(settings.upload_path.glob(f"{resolved_image_id}_*"))
    if not candidates:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在或已过期。")

    target = candidates[0]
    if target.suffix.lower() not in settings.chat_allowed_image_suffixes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅支持图片文件 OCR 预处理。")
    if not target.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在或已过期。")
    return target


def _compose_chat_query_with_ocr(*, user_text: str, ocr_text: str | None) -> str:
    normalized_user_text = (user_text or "").strip()
    normalized_ocr_text = (ocr_text or "").strip()
    if normalized_user_text and normalized_ocr_text:
        return f"{normalized_user_text}\n\n[OCR文本]\n{normalized_ocr_text}"
    if normalized_ocr_text:
        return normalized_ocr_text
    return normalized_user_text


def _build_turn_query_for_storage(*, user_text: str, ocr_text: str | None) -> str:
    normalized_user_text = (user_text or "").strip()
    if normalized_user_text:
        return normalized_user_text
    return (ocr_text or "").strip()


def _detect_chat_input_type(*, user_text: str, ocr_text: str | None, has_image: bool) -> str:
    has_user_text = bool((user_text or "").strip())
    has_ocr_text = bool((ocr_text or "").strip())
    if has_user_text and has_ocr_text:
        return "mixed"
    if has_ocr_text or has_image:
        return "image_ocr"
    return "text"


async def _prepare_chat_input(payload: ChatCompletionRequest) -> dict[str, str | None]:
    user_text = payload.messages[-1].content if payload.messages else ""
    user_text = sensitive_filter.filter(user_text)
    if payload.messages:
        payload.messages[-1].content = user_text

    image_path = _resolve_chat_image_path(image_id=payload.image_id, image_url=payload.image_url)
    ocr_text = None
    if image_path is not None:
        raw_ocr_text = await extract_text_from_image(image_path)
        ocr_text = sensitive_filter.filter(raw_ocr_text) if raw_ocr_text else None

    return {
        "user_text": user_text,
        "last_message": _compose_chat_query_with_ocr(user_text=user_text, ocr_text=ocr_text),
        "input_type": _detect_chat_input_type(user_text=user_text, ocr_text=ocr_text, has_image=image_path is not None),
        "ocr_text": ocr_text,
        "image_id": (payload.image_id or "").strip().lower() or _extract_image_id_from_url(payload.image_url or ""),
        "image_url": payload.image_url,
    }


def _estimate_text_tokens(text: str) -> int:
    if not text:
        return 0
    cjk_count = len(re.findall(r"[\u4e00-\u9fff]", text))
    latin_like_count = len(re.findall(r"[A-Za-z0-9]", text))
    other_count = max(len(text) - cjk_count - latin_like_count, 0)
    estimated = cjk_count + ((latin_like_count + other_count) // 4)
    return max(estimated, 1)


def _estimate_turn_tokens(turn: dict) -> int:
    return _estimate_text_tokens(str(turn.get("query", ""))) + _estimate_text_tokens(str(turn.get("answer", "")))


def _trim_context_by_limits(
    *,
    items: list[dict],
    max_turns: int,
    max_tokens: int,
    session_id: str,
) -> list[dict]:
    limited_items = list(items[-max_turns:])
    removed_by_turns = max(len(items) - len(limited_items), 0)
    removed_by_tokens = 0

    token_costs = [_estimate_turn_tokens(item) for item in limited_items]
    total_tokens = sum(token_costs)
    while len(limited_items) > 1 and total_tokens > max_tokens:
        removed_cost = token_costs.pop(0)
        limited_items.pop(0)
        total_tokens -= removed_cost
        removed_by_tokens += 1

    if removed_by_turns > 0 or removed_by_tokens > 0:
        logger.warning(
            "Chat context trimmed: session_id=%s removed_by_turns=%s removed_by_tokens=%s retained_turns=%s retained_tokens=%s",
            session_id,
            removed_by_turns,
            removed_by_tokens,
            len(limited_items),
            total_tokens,
        )
    else:
        logger.info(
            "Chat context token stats: session_id=%s turns=%s tokens=%s",
            session_id,
            len(limited_items),
            total_tokens,
        )

    return limited_items


def _limit_answer_length(answer: str, max_chars: int) -> str:
    if max_chars <= 0 or len(answer) <= max_chars:
        return answer
    if max_chars <= 3:
        return answer[:max_chars]
    return f"{answer[: max_chars - 3]}..."


def _ensure_chat_actor_allowed(user: dict[str, str]) -> None:
    if user.get("user_type") not in {"user", "merchant"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前角色不支持智能体对话。")


def _resolve_retrieval_owner_type(user_type: str) -> str:
    if user_type == "user":
        return "merchant"
    if user_type == "merchant":
        return "admin"
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前角色不支持智能体对话。")


async def _resolve_chat_runtime_params(
    *,
    session,
    user: dict[str, str],
    session_id: str,
    request_max_context_turns: int | None,
) -> dict[str, float | int | str]:
    settings = get_settings()
    keys = [
        "chat_max_context_turns",
        "chat_max_context_tokens",
        "chat_retrieval_top_k",
        "chat_similarity_threshold",
        "chat_answer_max_chars",
        "chat_retrieval_timeout_ms",
        "chat_generation_timeout_ms",
        "embedding_model_path",
        "embedding_device",
        "chat_vector_cache_enabled",
        "chat_vector_cache_backend",
        "chat_vector_cache_ttl_seconds",
        "chat_context_backend",
    ]
    config_map = await get_system_config_map(session, keys=keys)

    session_record = await get_chat_session_for_actor(
        session,
        owner_id=user["user_id"],
        owner_type=user["user_type"],
        session_id=session_id,
    )

    global_max_context_turns = _parse_int(
        config_map.get("chat_max_context_turns"),
        settings.chat_max_context_turns,
        min_value=1,
        max_value=50,
    )
    max_context_turns = _parse_int(
        request_max_context_turns,
        global_max_context_turns,
        min_value=1,
        max_value=50,
    )
    retrieval_top_k = _parse_int(
        config_map.get("chat_retrieval_top_k"),
        settings.chat_retrieval_top_k,
        min_value=1,
        max_value=20,
    )
    if session_record is not None and session_record.retrieval_top_k is not None:
        retrieval_top_k = _parse_int(session_record.retrieval_top_k, retrieval_top_k, min_value=1, max_value=20)

    similarity_threshold = _parse_float(
        config_map.get("chat_similarity_threshold"),
        settings.chat_similarity_threshold,
        min_value=0,
        max_value=1,
    )
    if session_record is not None and session_record.similarity_threshold is not None:
        similarity_threshold = _parse_float(
            session_record.similarity_threshold,
            similarity_threshold,
            min_value=0,
            max_value=1,
        )

    return {
        "max_context_turns": max_context_turns,
        "max_context_tokens": _parse_int(
            config_map.get("chat_max_context_tokens"),
            settings.chat_max_context_tokens,
            min_value=200,
            max_value=50000,
        ),
        "retrieval_top_k": retrieval_top_k,
        "similarity_threshold": similarity_threshold,
        "hybrid_vector_weight": max(float(settings.chat_hybrid_vector_weight), 0.0),
        "hybrid_bm25_weight": max(float(settings.chat_hybrid_bm25_weight), 0.0),
        "hybrid_candidate_k": _parse_int(
            settings.chat_hybrid_candidate_k,
            40,
            min_value=5,
            max_value=500,
        ),
        "hybrid_rrf_k": _parse_int(
            settings.chat_hybrid_rrf_k,
            60,
            min_value=1,
            max_value=500,
        ),
        "answer_max_chars": _parse_int(
            config_map.get("chat_answer_max_chars"),
            settings.chat_answer_max_chars,
            min_value=50,
            max_value=5000,
        ),
        "retrieval_timeout_ms": _parse_int(
            config_map.get("chat_retrieval_timeout_ms"),
            settings.chat_retrieval_timeout_ms,
            min_value=1000,
            max_value=600000,
        ),
        "generation_timeout_ms": _parse_int(
            config_map.get("chat_generation_timeout_ms"),
            settings.chat_generation_timeout_ms,
            min_value=1000,
            max_value=600000,
        ),
        "embedding_model_path": config_map.get("embedding_model_path") or settings.bge_model_path,
        "embedding_device": (config_map.get("embedding_device") or settings.embedding_device or "auto").strip(),
        "vector_cache_enabled": _parse_bool(
            config_map.get("chat_vector_cache_enabled"),
            settings.chat_vector_cache_enabled,
        ),
        "vector_cache_backend": (
            config_map.get("chat_vector_cache_backend")
            or settings.chat_vector_cache_backend
            or "auto"
        ).strip().lower(),
        "vector_cache_ttl_seconds": _parse_int(
            config_map.get("chat_vector_cache_ttl_seconds"),
            settings.chat_vector_cache_ttl_seconds,
            min_value=1,
            max_value=86400,
        ),
        "context_backend": _normalize_context_backend(
            config_map.get("chat_context_backend") or settings.chat_context_backend
        ),
    }


async def _load_context_items(
    *,
    session,
    user_id: str,
    user_type: str,
    session_id: str,
    max_context_turns: int,
    context_backend: str,
) -> list[dict]:
    backend = _normalize_context_backend(context_backend)

    if backend in {"auto", "redis"}:
        cached_items = await get_cached_chat_context(user_type=user_type, user_id=user_id, session_id=session_id)
        if cached_items is not None:
            return cached_items[-max_context_turns:]
        if backend == "redis":
            log_chat_context_store_call(
                "chat_context_get",
                status="miss",
                backend="redis",
                session_id=session_id,
                extra={"redis_only": True},
            )
            return []

    records = await get_chat_context(
        session,
        owner_id=user_id,
        owner_type=user_type,
        session_id=session_id,
        max_turns=max_context_turns,
    )
    items = [_serialize_turn_item(record) for record in records]
    log_chat_context_store_call(
        "chat_context_get",
        status="ok" if items else "empty",
        backend="mysql",
        session_id=session_id,
        extra={"items_count": len(items), "fallback_from": "redis" if backend == "auto" else None},
    )
    if backend == "auto":
        await set_cached_chat_context(user_type=user_type, user_id=user_id, session_id=session_id, items=items)
    return items


async def _ensure_session_exists(*, session, user: dict[str, str], session_id: str) -> None:
    record = await get_chat_session_for_actor(
        session,
        owner_id=user["user_id"],
        owner_type=user["user_type"],
        session_id=session_id,
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在。")


async def _search_across_knowledge_bases(
    *,
    session,
    actor: dict[str, str],
    query: str,
    top_k: int,
    similarity_threshold: float,
    session_id: str,
    vector_weight: float,
    bm25_weight: float,
    hybrid_candidate_k: int,
    hybrid_rrf_k: int,
    embedding_model_path: str,
    embedding_device: str,
    vector_cache_enabled: bool,
    vector_cache_backend: str,
    vector_cache_ttl_seconds: int,
) -> list[dict]:
    settings = get_settings()
    retrieval_owner_type = _resolve_retrieval_owner_type(actor["user_type"])
    knowledge_bases = await list_knowledge_bases(session, actor=None, owner_type=retrieval_owner_type)
    kb_cache_fingerprint = sorted(
        [
            {
                "name": getattr(item, "name", ""),
                "collection": getattr(item, "chroma_collection", ""),
            }
            for item in knowledge_bases
        ],
        key=lambda row: (str(row.get("collection") or ""), str(row.get("name") or "")),
    )
    cache_payload = {
        "query": query.strip(),
        "owner_type": retrieval_owner_type,
        "owner_id": actor.get("user_id", ""),
        "top_k": int(top_k),
        "similarity_threshold": round(float(similarity_threshold), 6),
        "vector_weight": round(float(vector_weight), 6),
        "bm25_weight": round(float(bm25_weight), 6),
        "candidate_k": int(hybrid_candidate_k),
        "rrf_k": int(hybrid_rrf_k),
        "embedding_model_path": embedding_model_path,
        "embedding_device": embedding_device,
        "knowledge_bases": kb_cache_fingerprint,
    }
    cache_key = build_vector_cache_key(payload=cache_payload)
    if vector_cache_enabled:
        cached_items = await get_vector_cache_items(key=cache_key, backend=vector_cache_backend)
        if cached_items is not None:
            return cached_items

    merged_items: list[dict] = []
    per_kb_top_k = max(top_k, min(hybrid_candidate_k, top_k * 2))

    async def _search_single_knowledge_base(knowledge_base) -> list[dict]:
        try:
            vector_store = get_vector_store(
                collection_name=knowledge_base.chroma_collection,
                persist_directory=settings.chroma_path,
                embedding_device=embedding_device,
                model_path=embedding_model_path,
            )
            kb_items = await asyncio.to_thread(
                vector_store.hybrid_search,
                query,
                k=per_kb_top_k,
                vector_weight=vector_weight,
                bm25_weight=bm25_weight,
                candidate_k=hybrid_candidate_k,
                rrf_k=hybrid_rrf_k,
            )
            for kb_item in kb_items:
                kb_item["kb_name"] = knowledge_base.name
            return kb_items
        except Exception:
            return []

    if knowledge_bases:
        kb_tasks = [asyncio.create_task(_search_single_knowledge_base(knowledge_base)) for knowledge_base in knowledge_bases]
        kb_results = await asyncio.gather(*kb_tasks, return_exceptions=False)
        for kb_items in kb_results:
            if kb_items:
                merged_items.extend(kb_items)

    merged_items = _deduplicate_hybrid_items(merged_items)

    reranked_items = _rerank_merged_hybrid_items(
        query=query,
        items=merged_items,
        vector_weight=vector_weight,
        bm25_weight=bm25_weight,
        rrf_k=hybrid_rrf_k,
    )

    filtered_items: list[dict] = []
    for item in reranked_items:
        score = item.get("score")
        if score is None:
            continue
        try:
            if float(score) >= similarity_threshold:
                filtered_items.append(item)
        except (TypeError, ValueError):
            continue

    filtered_items.sort(key=lambda item: float(item.get("score") or 0), reverse=True)
    final_items = _sanitize_sources(filtered_items[:top_k])
    _log_hybrid_retrieval_scores(
        session_id=session_id,
        actor=actor,
        query=query,
        vector_weight=vector_weight,
        bm25_weight=bm25_weight,
        top_k=top_k,
        threshold=similarity_threshold,
        items=final_items,
    )
    if vector_cache_enabled and final_items:
        await set_vector_cache_items(
            key=cache_key,
            items=final_items,
            ttl_seconds=vector_cache_ttl_seconds,
            backend=vector_cache_backend,
        )
    return final_items


def _sse_payload(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _persist_turn_and_context(
    *,
    session,
    user: dict[str, str],
    session_id: str,
    max_context_turns: int,
    max_context_tokens: int,
    context_backend: str,
    user_text: str,
    input_type: str,
    ocr_text: str | None,
    answer: str,
    rewritten_query: str,
    sources: list[dict],
) -> tuple[int, list[dict]]:
    backend = _normalize_context_backend(context_backend)
    turn_query = _build_turn_query_for_storage(user_text=user_text, ocr_text=ocr_text)
    record = await create_chat_turn(
        session,
        owner_id=user["user_id"],
        owner_type=user["user_type"],
        session_id=session_id,
        query=turn_query,
        input_type=input_type,
        ocr_text=ocr_text,
        answer=answer,
        rewritten_query=rewritten_query,
        sources=sources,
        tokens=max(_estimate_turn_tokens({"query": turn_query, "answer": answer}), 1),
    )
    log_chat_context_store_call(
        "chat_context_persist",
        status="ok",
        backend="mysql",
        session_id=session_id,
        extra={"turn_no": record.turn_no},
    )
    turn_no = record.turn_no

    current_context = await _load_context_items(
        session=session,
        user_id=user["user_id"],
        user_type=user["user_type"],
        session_id=session_id,
        max_context_turns=max_context_turns,
        context_backend=backend,
    )
    latest_item = _serialize_turn_item(record)
    if not current_context or current_context[-1].get("turn_no") != latest_item["turn_no"]:
        current_context = (current_context + [latest_item])[-max_context_turns:]
        current_context = _trim_context_by_limits(
            items=current_context,
            max_turns=max_context_turns,
            max_tokens=max_context_tokens,
            session_id=session_id,
        )
        if backend in {"auto", "redis"}:
            await set_cached_chat_context(
                user_type=user["user_type"],
                user_id=user["user_id"],
                session_id=session_id,
                items=current_context,
            )
    return turn_no, current_context


def _normalize_orchestrator_mode(value: str | None) -> str:
    selected = (value or "legacy").strip().lower()
    if selected in {"legacy", "graph", "shadow"}:
        return selected
    return "legacy"


def _build_general_chat_messages(history_items: list[dict], query: str) -> list[tuple[str, str]]:
    messages: list[tuple[str, str]] = [
        ("system", "你是一个幽默、友好的 AI 助手，请自由回答用户的日常问题或闲聊，不需要拘泥于特定的业务领域。")
    ]
    for item in history_items:
        if item.get("query"):
            messages.append(("user", str(item["query"])))
        if item.get("answer"):
            messages.append(("assistant", str(item["answer"])))
    messages.append(("user", query))
    return messages


def _finalize_policy_message(answer: str) -> tuple[str, str | None, list[dict] | None]:
    if "抱歉，您的问题涉及非业务范围或包含不当内容" not in answer:
        return answer, None, None
    return (
        "抱歉，您的问题涉及非业务范围或包含不当内容。我是 ReviewPulse Agent，仅负责解答与商家运营、平台规范及知识库相关的问题，请换个问题试试。",
        None,
        [],
    )


async def _create_completion_with_langgraph(
    *,
    payload: ChatCompletionRequest,
    session: DBSession,
    user: CurrentUser,
) -> dict | StreamingResponse:
    request_started = time.monotonic()
    latency_ms: dict[str, int] = {}
    settings = get_settings()
    _ensure_chat_actor_allowed(user)

    prepared_input = await _prepare_chat_input(payload)
    user_text = str(prepared_input.get("user_text") or "")
    last_message = str(prepared_input.get("last_message") or "")
    input_type = str(prepared_input.get("input_type") or "text")
    ocr_text = prepared_input.get("ocr_text")
    image_id = prepared_input.get("image_id")
    image_url = prepared_input.get("image_url")
    session_id = payload.session_id or uuid4().hex

    runtime_params = await _resolve_chat_runtime_params(
        session=session,
        user=user,
        session_id=session_id,
        request_max_context_turns=payload.max_context_turns,
    )
    max_context_turns = int(runtime_params["max_context_turns"])
    max_context_tokens = int(runtime_params["max_context_tokens"])
    retrieval_top_k = int(runtime_params["retrieval_top_k"])
    similarity_threshold = float(runtime_params["similarity_threshold"])
    hybrid_vector_weight = float(runtime_params["hybrid_vector_weight"])
    hybrid_bm25_weight = float(runtime_params["hybrid_bm25_weight"])
    hybrid_candidate_k = int(runtime_params["hybrid_candidate_k"])
    hybrid_rrf_k = int(runtime_params["hybrid_rrf_k"])
    answer_max_chars = int(runtime_params["answer_max_chars"])
    retrieval_timeout_seconds = int(runtime_params["retrieval_timeout_ms"]) / 1000
    generation_timeout_seconds = int(runtime_params["generation_timeout_ms"]) / 1000
    embedding_model_path = str(runtime_params["embedding_model_path"])
    embedding_device = str(runtime_params["embedding_device"])
    vector_cache_enabled = bool(runtime_params["vector_cache_enabled"])
    vector_cache_backend = str(runtime_params["vector_cache_backend"])
    vector_cache_ttl_seconds = int(runtime_params["vector_cache_ttl_seconds"])
    context_backend = str(runtime_params["context_backend"])

    rewrite_model = settings.llm_rewrite_model_name or settings.llm_model_name
    generation_model = payload.model or settings.llm_generation_model_name or settings.llm_model_name
    called_models = {
        "rewrite": rewrite_model,
        "generation": generation_model,
        "request": payload.model,
    }
    
    sse_queue = asyncio.Queue()
    def emit_sse_progress(msg: str):
        if payload.stream:
            try:
                sse_queue.put_nowait(msg)
            except Exception:
                pass

    async def node_input_process(state: ChatGraphState) -> dict:
        return {
            "user_text": str(state.get("user_text") or ""),
            "last_message": str(state.get("last_message") or ""),
            "input_type": str(state.get("input_type") or "text"),
            "ocr_text": state.get("ocr_text"),
            "image_id": state.get("image_id"),
            "image_url": state.get("image_url"),
            "answer": state.get("answer") or "欢迎使用 ReviewPulse Agent。",
            "sources": state.get("sources") or [],
        }

    async def node_guardrails(state: ChatGraphState) -> dict:
        return {}

    async def node_history(state: ChatGraphState) -> dict:
        items = await _load_context_items(
            session=session,
            user_id=user["user_id"],
            user_type=user["user_type"],
            session_id=session_id,
            max_context_turns=max_context_turns,
            context_backend=context_backend,
        )
        items = _trim_context_by_limits(
            items=items,
            max_turns=max_context_turns,
            max_tokens=max_context_tokens,
            session_id=session_id,
        )
        return {"history_items": items}

    async def node_rewrite(state: ChatGraphState) -> dict:
        rewrite_started = time.monotonic()
        rewritten = str(state.get("last_message") or "")
        try:
            rewritten = await rewrite_question(
                str(state.get("last_message") or ""),
                state.get("history_items") or [],
                model_name=rewrite_model,
            )
        finally:
            latency_ms["rewrite"] = int((time.monotonic() - rewrite_started) * 1000)
        return {"rewritten_query": rewritten}

    async def node_router(state: ChatGraphState) -> dict:
        uploaded_file_ids = state.get("file_ids") or []
        if uploaded_file_ids:
            logger.info(f"检测到上传文件 file_ids={uploaded_file_ids}，强制路由到 complex_planning")
            return {"intent": "complex_planning", "direct_response": None, "is_complex_task": True}

        intent, direct_response = await master_router.determine_intent(
            query=str(state.get("rewritten_query") or ""),
            model_name=rewrite_model,
            user_type=user.get("user_type", "user"),
        )
        return {"intent": intent, "direct_response": direct_response, "is_complex_task": intent == "complex_planning"}

    async def node_retrieve(state: ChatGraphState) -> dict:
        if not payload.messages:
            return {}
        retrieval_started = time.monotonic()
        timeout_stage: str | None = None
        answer = state.get("answer") or "欢迎使用 ReviewPulse Agent。"
        sources: list[dict] = []
        try:
            try:
                sources = await asyncio.wait_for(
                    _search_across_knowledge_bases(
                        session=session,
                        actor=user,
                        query=str(state.get("rewritten_query") or ""),
                        top_k=retrieval_top_k,
                        similarity_threshold=similarity_threshold,
                        session_id=session_id,
                        vector_weight=hybrid_vector_weight,
                        bm25_weight=hybrid_bm25_weight,
                        hybrid_candidate_k=hybrid_candidate_k,
                        hybrid_rrf_k=hybrid_rrf_k,
                        embedding_model_path=embedding_model_path,
                        embedding_device=embedding_device,
                        vector_cache_enabled=vector_cache_enabled,
                        vector_cache_backend=vector_cache_backend,
                        vector_cache_ttl_seconds=vector_cache_ttl_seconds,
                    ),
                    timeout=retrieval_timeout_seconds,
                )
            except asyncio.TimeoutError:
                timeout_stage = "retrieval"
                answer = "检索超时，请稍后重试。"
                sources = []
        except Exception:
            answer = _fallback_answer(str(state.get("rewritten_query") or ""), sources)
        finally:
            latency_ms["retrieval"] = int((time.monotonic() - retrieval_started) * 1000)

        return {"sources": sources, "timeout_stage": timeout_stage, "answer": answer}

    async def node_rerank(state: ChatGraphState) -> dict:
        return {"sources": state.get("sources") or []}

    async def node_chat_gen(state: ChatGraphState) -> dict:
        if payload.stream:
            return {}
        generation_started = time.monotonic()
        timeout_stage = state.get("timeout_stage")
        answer = state.get("answer") or "欢迎使用 ReviewPulse Agent。"
        try:
            answer = await asyncio.wait_for(
                invoke_chat(
                    messages=_build_general_chat_messages(state.get("history_items") or [], str(state.get("rewritten_query") or "")),
                    model_name=generation_model,
                ),
                timeout=generation_timeout_seconds,
            )
            answer = sensitive_filter.filter(answer)
        except asyncio.TimeoutError:
            timeout_stage = "generation"
            answer = "答案生成超时，请稍后重试。"
        finally:
            latency_ms["generation"] = int((time.monotonic() - generation_started) * 1000)
        return {"answer": answer, "timeout_stage": timeout_stage}

    async def node_rag_gen(state: ChatGraphState) -> dict:
        if payload.stream or state.get("timeout_stage") is not None:
            return {}
        generation_started = time.monotonic()
        timeout_stage = state.get("timeout_stage")
        answer = state.get("answer") or "欢迎使用 ReviewPulse Agent。"
        try:
            answer = await asyncio.wait_for(
                answer_with_context(
                    question=str(state.get("rewritten_query") or ""),
                    history_turns=state.get("history_items") or [],
                    retrieved_items=state.get("sources") or [],
                    model_name=generation_model,
                    answer_max_chars=answer_max_chars,
                ),
                timeout=generation_timeout_seconds,
            )
            answer = sensitive_filter.filter(answer)
        except asyncio.TimeoutError:
            timeout_stage = "generation"
            answer = "答案生成超时，请稍后重试。"
        finally:
            latency_ms["generation"] = int((time.monotonic() - generation_started) * 1000)
        return {"answer": answer, "timeout_stage": timeout_stage}

    async def node_direct_rep(state: ChatGraphState) -> dict:
        return {"answer": str(state.get("direct_response") or state.get("answer") or "欢迎使用 ReviewPulse Agent。"), "sources": []}

    async def node_tool_agent(state: ChatGraphState) -> dict:
        tool_chat_messages = await process_tool_use_intent(
            query=str(state.get("rewritten_query") or ""),
            user=user,
            session=session,
            model_name=generation_model,
        )
        return {
            "answer": state.get("answer") or "欢迎使用 ReviewPulse Agent。",
            "sources": [],
            "tool_needs_explain": False,
            "tool_chat_messages": tool_chat_messages,
        }

    async def node_tool_output(state: ChatGraphState) -> dict:
        if payload.stream:
            return {"tool_needs_explain": bool(state.get("tool_needs_explain"))}

        generation_started = time.monotonic()
        timeout_stage = state.get("timeout_stage")
        answer = state.get("answer") or "欢迎使用 ReviewPulse Agent。"
        try:
            answer = await asyncio.wait_for(
                invoke_chat(
                    messages=state.get("tool_chat_messages") or [],
                    model_name=generation_model,
                ),
                timeout=generation_timeout_seconds,
            )
            answer = sensitive_filter.filter(answer)
        except asyncio.TimeoutError:
            timeout_stage = "generation"
            answer = "答案生成超时，请稍后重试。"
        finally:
            latency_ms["generation"] = int((time.monotonic() - generation_started) * 1000)
        return {
            "tool_needs_explain": bool(state.get("tool_needs_explain")),
            "answer": answer,
            "timeout_stage": timeout_stage,
        }

    async def node_planner(state: ChatGraphState) -> dict:
        loop_count = (state.get("loop_count") or 0) + 1
        past_steps = state.get("past_steps") or []
        
        emit_sse_progress(f"> 第 {loop_count} 轮迭代：Kimi-k2.5 正在评估进度并规划下一步...\n\n")
        target_model = "kimi-k2.5"
        called_models["planner"] = target_model

        history_context = "无"
        if past_steps:
            history_context = ""
            for i, (s, r) in enumerate(past_steps):
                history_context += f"- 步骤 {i+1}: {s}\n  结果摘要: {r[:300]}...\n"

        uploaded_file_ids = state.get("file_ids") or []
        file_hint = "未上传文件。"
        if uploaded_file_ids:
            file_hint = f"用户上传了数据文件（doc_id: {', '.join(uploaded_file_ids)}），支持使用 [数据分析] 动作。"

        prompt = f"""你是一个具备自我反思能力的高级任务规划器。你的目标是解析用户的复合需求，并逐步引导执行器完成所有子任务。

{state.get("rewritten_query")}

{file_hint}

{history_context}

请严格按以下步骤思考并输出：
1. **[Thinking]**：口语化地分析：用户问了哪几个事？哪些已经查到了？哪些还没查？接下来最该干什么？（注意：严禁重复执行已经获得有效结果的步骤）。
2. **[Next Action]**：
   - 如果所有子任务都已完成，或者历史结果已经足够回答原始请求，请输出：`[任务完成]`
   - 否则，请从以下三个动作中选择**一个**最紧迫的下一步：
     - `[数据分析] <具体分析描述>` (针对上传文件的统计/聚合)
     - `[知识检索] <具体检索词>` (针对规章制度/流程文档)
     - `[工具调用] <具体查询业务描述>` (针对商户、评论、退款等实时系统工具)

[Thinking] 用户问了文件分析和评论违规，我已经分析了文件，但还没查评论。
[工具调用] 查询该商户的最新用户评论记录
"""
        try:
            plan_full_text = await invoke_chat([("user", prompt)], model_name=target_model)
            lines = [l.strip() for l in plan_full_text.split("\n") if l.strip()]
            plan = []
            if lines:
                for line in reversed(lines):
                    if any(tag in line for tag in ["[数据分析]", "[知识检索]", "[工具调用]", "[任务完成]"]):
                        plan = [line]
                        break
            
            if not plan:
                plan = ["[任务完成]"]
                
        except Exception as e:
            logger.error(f"Planner error: {e}")
            plan = ["[任务完成]"]
            
        return {"plan": plan, "past_steps": past_steps, "loop_count": loop_count}

    async def node_executor(state: ChatGraphState) -> dict:
        plan = state.get("plan") or []
        if not plan:
            return {}
            
        step_desc = plan[0]
        past_steps = state.get("past_steps") or []
        current_sources = list(state.get("sources") or [])
        loop_count = state.get("loop_count") or 1
        
        if "[数据分析]" in step_desc:
            step_intent = "data_analysis"
            clean_desc = step_desc.replace("[数据分析]", "").strip()
            emit_sse_progress(f"> 执行器 (轮次 {loop_count}): 正在进行数据分析 [{clean_desc}]...\n\n")
        elif "[知识检索]" in step_desc:
            step_intent = "knowledge_query"
            clean_desc = step_desc.replace("[知识检索]", "").strip()
            emit_sse_progress(f"> 执行器 (轮次 {loop_count}): 正在检索知识库 [{clean_desc}]...\n\n")
        else:
            step_intent = "tool_use"
            clean_desc = step_desc.replace("[工具调用]", "").strip()
            emit_sse_progress(f"> 执行器 (轮次 {loop_count}): 正在调用系统工具 [{clean_desc}]...\n\n")

        result = "获取数据失败或无匹配动作。"
        
        if step_intent == "data_analysis":
            try:
                from app.services.pandas_analyzer import PandasAnalyzer, AnalysisRequest
                analyzer = PandasAnalyzer()
                analysis_file_ids = state.get("file_ids") or []
                if analysis_file_ids:
                    doc_id_str = analysis_file_ids[0]
                    analysis_result = await analyzer.analyze(AnalysisRequest(
                        dataset_reference=doc_id_str,
                        analysis_query=clean_desc,
                        user_instruction=str(state.get("rewritten_query") or ""),
                    ))
                    if analysis_result.status == "success":
                        result = str(analysis_result.data or analysis_result.text_summary or "分析完成，未返回数据。")
                        if analysis_result.generated_code:
                            result += f"\n\n执行代码:\n```python\n{analysis_result.generated_code}\n```"
                    else:
                        result = f"数据分析失败: {analysis_result.error_message}"
                else:
                    result = "未找到上传的数据文件，无法执行分析。"
            except Exception as e:
                logger.error(f"Executor data_analysis error: {e}")
                result = f"数据分析执行异常: {str(e)}"

        elif step_intent == "knowledge_query":
            try:
                step_sources = await asyncio.wait_for(
                    _search_across_knowledge_bases(
                        session=session,
                        actor=user,
                        query=f"{clean_desc} {state.get('rewritten_query')}",
                        top_k=retrieval_top_k,
                        similarity_threshold=similarity_threshold,
                        session_id=session_id,
                        vector_weight=hybrid_vector_weight,
                        bm25_weight=hybrid_bm25_weight,
                        hybrid_candidate_k=hybrid_candidate_k,
                        hybrid_rrf_k=hybrid_rrf_k,
                        embedding_model_path=embedding_model_path,
                        embedding_device=embedding_device,
                        vector_cache_enabled=vector_cache_enabled,
                        vector_cache_backend=vector_cache_backend,
                        vector_cache_ttl_seconds=vector_cache_ttl_seconds,
                    ),
                    timeout=retrieval_timeout_seconds,
                )
                if step_sources:
                    current_sources.extend(step_sources)
                    formatted_sources = []
                    for s in step_sources:
                        formatted_sources.append(f"文档标题【{s.get('source', '未知')}】:\n{s.get('content', '')}\n")
                    result = "\n".join(formatted_sources)
                else:
                    result = "未检索到相关的知识库文档片段。"
            except Exception as e:
                logger.error(f"Executor RAG error: {e}")
                result = "检索知识库超时或发生错误。"

        else: 
            tool_chat_messages = await process_tool_use_intent(
                query=f"根据规划步骤: '{clean_desc}'，并结合原始问题: '{state.get('rewritten_query')}' 进行处理。",
                user=user,
                session=session,
                model_name=generation_model,
            )
            if tool_chat_messages:
                result = str(tool_chat_messages[-1][1])

        if len(result) > 4000:
            result = result[:4000] + "\n...[内容过长已截断]"
        
        past_steps.append((step_desc, result))
        unique_sources = {str(src.get("id", src.get("source"))): src for src in current_sources}.values()
        
        return {
            "past_steps": past_steps, 
            "sources": list(unique_sources)
        }

    async def node_synthesizer(state: ChatGraphState) -> dict:
        emit_sse_progress("> 所有的协同分析完毕，Qwen-Turbo 正在为您起草综合报告：\n\n")
        past_steps = state.get("past_steps") or []
        context = ""
        for s, r in past_steps:
            context += f"步骤: {s}\n执行结果: {r}\n\n"
            
        synthesizer_messages = [
            ("system", "你是一个最终结论总结代理(Synthesizer)，请根据历史执行报告直接回答用户的原始问题，保持专业、有条理且语气温和。"),
            ("user", f"原始请求: {state.get('rewritten_query')}\n\n执行报告合集:\n{context}")
        ]
        
        answer = "等待合成最终回答"
        timeout_stage = None
        if not payload.stream:
            generation_started = time.monotonic()
            try:
                answer = await asyncio.wait_for(
                    invoke_chat(messages=synthesizer_messages, model_name=generation_model),
                    timeout=generation_timeout_seconds,
                )
                answer = sensitive_filter.filter(answer)
            except asyncio.TimeoutError:
                timeout_stage = "generation"
                answer = "总结生成超时，请稍后重试。"
            finally:
                latency_ms["generation"] = int((time.monotonic() - generation_started) * 1000)
                
        return {"answer": answer, "tool_chat_messages": synthesizer_messages, "timeout_stage": timeout_stage}

    async def node_audit(state: ChatGraphState) -> dict:
        ans = str(state.get("answer") or "")
        if state.get("is_complex_task"):
            return {"answer": ans}
        return {"answer": _limit_answer_length(ans, answer_max_chars)}

    callbacks = ChatGraphCallbacks(
        input_process=node_input_process,
        guardrails=node_guardrails,
        history=node_history,
        rewrite=node_rewrite,
        router=node_router,
        retrieve=node_retrieve,
        rerank=node_rerank,
        rag_gen=node_rag_gen,
        chat_gen=node_chat_gen,
        direct_rep=node_direct_rep,
        tool_agent=node_tool_agent,
        tool_output=node_tool_output,
        audit=node_audit,
        planner=node_planner,
        executor=node_executor,
        synthesizer=node_synthesizer,
    )
    orchestrator = create_orchestrator(callbacks)

    graph_path = settings.log_path / "chat_graph.mmd"
    if not graph_path.exists():
        try:
            orchestrator.export_mermaid_to_file(graph_path)
        except Exception:
            logger.debug("Failed to export chat graph mermaid", exc_info=True)

    state: ChatGraphState = {
        "stream": payload.stream,
        "has_messages": bool(payload.messages),
        "session_id": session_id,
        "user": dict(user),
        "payload_model": payload.model,
        "user_text": user_text,
        "last_message": last_message,
        "input_type": input_type,
        "ocr_text": ocr_text,
        "image_id": image_id,
        "image_url": image_url,
        "rewritten_query": last_message,
        "history_items": [],
        "intent": "knowledge_query",
        "direct_response": None,
        "sources": [],
        "answer": "欢迎使用 ReviewPulse Agent。",
        "timeout_stage": None,
        "tool_needs_explain": False,
        "tool_chat_messages": [],
        "tool_error": None,
        "latency_ms": latency_ms,
        "called_models": called_models,
        "file_ids": list(payload.file_ids or []),
        "past_steps": [],
        "loop_count": 0,

    }
    if payload.stream:
        async def stream_events() -> AsyncIterator[str]:
            run_task = asyncio.create_task(orchestrator.run(state))
            while not run_task.done() or not sse_queue.empty():
                try:
                    msg = await asyncio.wait_for(sse_queue.get(), timeout=0.1)
                    yield _sse_payload({"content": msg})
                except asyncio.TimeoutError:
                    pass
            
            final_state = run_task.result()
            answer = str(final_state.get("answer") or "欢迎使用 ReviewPulse Agent。")
            user_text_res = str(final_state.get("user_text") or user_text)
            input_type_res = str(final_state.get("input_type") or input_type)
            ocr_text_res = final_state.get("ocr_text")
            rewritten_query_res = final_state.get("rewritten_query")
            sources_res = list(final_state.get("sources") or [])
            timeout_stage_res = final_state.get("timeout_stage")
            intent_res = str(final_state.get("intent") or "knowledge_query")
            direct_response_res = final_state.get("direct_response")
            history_items_res = list(final_state.get("history_items") or [])
            tool_chat_messages_res = list(final_state.get("tool_chat_messages") or [])
            
            streamed_answer_parts: list[str] = []

            if direct_response_res:
                streamed_answer_parts.append(str(direct_response_res))
                yield _sse_payload({"content": str(direct_response_res)})
            elif payload.messages and timeout_stage_res is None:
                generation_started = time.monotonic()
                try:
                    async with asyncio.timeout(generation_timeout_seconds):
                        buffer = ""
                        max_len = sensitive_filter.max_word_len

                        if intent_res == "general_chat":
                            stream_generator = invoke_chat_stream(
                                messages=_build_general_chat_messages(history_items_res, str(rewritten_query_res or "")),
                                model_name=generation_model,
                            )
                        elif intent_res in {"tool_use", "complex_planning"}:
                            stream_generator = invoke_chat_stream(
                                messages=tool_chat_messages_res,
                                model_name=generation_model,
                            )
                        else:
                            stream_generator = answer_with_context_stream(
                                question=str(rewritten_query_res or ""),
                                history_turns=history_items_res,
                                retrieved_items=sources_res,
                                model_name=generation_model,
                                answer_max_chars=answer_max_chars,
                            )

                        async for chunk in stream_generator:
                            if max_len == 0:
                                streamed_answer_parts.append(chunk)
                                yield _sse_payload({"content": chunk})
                                continue

                            buffer += chunk
                            if len(buffer) > max_len:
                                safe_part = buffer[:-max_len]
                                buffer = buffer[-max_len:]
                                filtered_safe = sensitive_filter.filter(safe_part)
                                if filtered_safe:
                                    streamed_answer_parts.append(filtered_safe)
                                    yield _sse_payload({"content": filtered_safe})

                        if buffer:
                            filtered_rem = sensitive_filter.filter(buffer)
                            if filtered_rem:
                                streamed_answer_parts.append(filtered_rem)
                                yield _sse_payload({"content": filtered_rem})
                except TimeoutError:
                    timeout_stage_res = "generation"
                    timeout_hint = "\n\n[生成超时，以下为部分回答]"
                    if streamed_answer_parts:
                        streamed_answer_parts.append(timeout_hint)
                        yield _sse_payload({"content": timeout_hint})
                    else:
                        streamed_answer_parts = ["答案生成超时，请稍后重试。"]
                        yield _sse_payload({"content": streamed_answer_parts[0]})
                finally:
                    latency_ms["generation"] = int((time.monotonic() - generation_started) * 1000)

            answer = "".join(streamed_answer_parts) if streamed_answer_parts else answer
            if intent_res != "complex_planning":
                answer = _limit_answer_length(answer, answer_max_chars)
            latency_ms["total"] = int((time.monotonic() - request_started) * 1000)
            final_answer, normalized_rewrite, normalized_sources = _finalize_policy_message(answer)
            if normalized_sources is not None:
                sources_res = normalized_sources
                rewritten_query_res = normalized_rewrite
                answer = final_answer

            turn_no_local, current_context = await _persist_turn_and_context(
                session=session,
                user=user,
                session_id=session_id,
                max_context_turns=max_context_turns,
                max_context_tokens=max_context_tokens,
                context_backend=context_backend,
                user_text=user_text_res,
                input_type=input_type_res,
                ocr_text=ocr_text_res,
                answer=answer,
                rewritten_query=rewritten_query_res,
                sources=sources_res,
            )

            metadata = {
                "done": True,
                "session_id": session_id,
                "turn_no": turn_no_local,
                "input_type": input_type_res,
                "ocr_text": ocr_text_res,
                "sources": sources_res,
                "rewritten_query": rewritten_query_res,
                "timeout_stage": timeout_stage_res,
                "latency_ms": latency_ms,
                "called_models": called_models,
                "model": generation_model,
                "context_turns": len(current_context),
                "user": user,
            }
            logger.info("Chat completion models: session_id=%s rewrite_model=%s generation_model=%s request_model=%s",
                        session_id, rewrite_model, generation_model, payload.model)
            logger.info("Chat completion latency: session_id=%s rewrite_ms=%s retrieval_ms=%s generation_ms=%s total_ms=%s",
                        session_id, latency_ms.get("rewrite"), latency_ms.get("retrieval"), latency_ms.get("generation"), latency_ms.get("total"))
            yield _sse_payload(metadata)

        return StreamingResponse(stream_events(), media_type="text/event-stream")

    final_state = await orchestrator.run(state)
    
    answer = str(final_state.get("answer") or "欢迎使用 ReviewPulse Agent。")
    user_text = str(final_state.get("user_text") or user_text)
    input_type = str(final_state.get("input_type") or input_type)
    ocr_text = final_state.get("ocr_text")
    rewritten_query = final_state.get("rewritten_query")
    sources = list(final_state.get("sources") or [])
    timeout_stage = final_state.get("timeout_stage")

    latency_ms["total"] = int((time.monotonic() - request_started) * 1000)
    final_answer, normalized_rewrite, normalized_sources = _finalize_policy_message(answer)
    if normalized_sources is not None:
        sources = normalized_sources
        rewritten_query = normalized_rewrite
        answer = final_answer

    turn_no, current_context = await _persist_turn_and_context(
        session=session,
        user=user,
        session_id=session_id,
        max_context_turns=max_context_turns,
        max_context_tokens=max_context_tokens,
        context_backend=context_backend,
        user_text=user_text,
        input_type=input_type,
        ocr_text=ocr_text,
        answer=answer,
        rewritten_query=rewritten_query,
        sources=sources,
    )

    logger.info(
        "Chat completion models: session_id=%s rewrite_model=%s generation_model=%s request_model=%s",
        session_id,
        rewrite_model,
        generation_model,
        payload.model,
    )
    logger.info(
        "Chat completion latency: session_id=%s rewrite_ms=%s retrieval_ms=%s generation_ms=%s total_ms=%s",
        session_id,
        latency_ms.get("rewrite"),
        latency_ms.get("retrieval"),
        latency_ms.get("generation"),
        latency_ms.get("total"),
    )
    return {
        "model": generation_model,
        "called_models": called_models,
        "message": {"role": "assistant", "content": answer},
        "answer": answer,
        "session_id": session_id,
        "turn_no": turn_no,
        "input_type": input_type,
        "ocr_text": ocr_text,
        "rewritten_query": rewritten_query,
        "sources": sources,
        "timeout_stage": timeout_stage,
        "latency_ms": latency_ms,
        "context_turns": len(current_context),
        "user": user,
    }


@router.post(
    "/images/upload",
    summary="upload_chat_image          上传聊天图片并返回 image_id 与访问地址。",
    operation_id="uploadChatImage",
)
async def upload_chat_image(
    user: CurrentUser,
    file: UploadFile = File(...),
):
    _ensure_chat_actor_allowed(user)
    settings = get_settings()
    stored_path = await save_upload_file(
        file,
        allowed_suffixes=settings.chat_allowed_image_suffixes,
    )
    image_id = stored_path.name.split("_", 1)[0].strip().lower()
    return {
        "image_id": image_id,
        "image_url": f"/api/v1/chat/images/{image_id}",
        "filename": file.filename or stored_path.name,
        "size": stored_path.stat().st_size,
    }


@router.get(
    "/images/{image_id}",
    summary="get_chat_image          按 image_id 获取上传图片文件。",
    operation_id="getChatImage",
    responses={404: {"description": "图片不存在或已过期"}},
)
async def get_chat_image(image_id: str, user: CurrentUser):
    _ensure_chat_actor_allowed(user)
    target = _resolve_chat_image_path(image_id=image_id, image_url=None)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在或已过期。")
    return FileResponse(path=target, filename=target.name)


@router.post(
    "/completions",
    summary="create_completion          处理聊天请求，支持流式与非流式输出。",
    operation_id="createChatCompletion",
)
async def create_completion(
    payload: ChatCompletionRequest,
    session: DBSession,
    user: CurrentUser,
):
    mode = _normalize_orchestrator_mode(get_settings().chat_orchestrator_mode)
    if mode in {"graph", "shadow"}:
        return await _create_completion_with_langgraph(payload=payload, session=session, user=user)

    request_started = time.monotonic()
    latency_ms: dict[str, int] = {}
    settings = get_settings()
    _ensure_chat_actor_allowed(user)
    prepared_input = await _prepare_chat_input(payload)
    user_text = str(prepared_input.get("user_text") or "")
    last_message = str(prepared_input.get("last_message") or "")
    input_type = str(prepared_input.get("input_type") or "text")
    ocr_text = prepared_input.get("ocr_text")
    session_id = payload.session_id or uuid4().hex
    runtime_params = await _resolve_chat_runtime_params(
        session=session,
        user=user,
        session_id=session_id,
        request_max_context_turns=payload.max_context_turns,
    )
    max_context_turns = int(runtime_params["max_context_turns"])
    max_context_tokens = int(runtime_params["max_context_tokens"])
    retrieval_top_k = int(runtime_params["retrieval_top_k"])
    similarity_threshold = float(runtime_params["similarity_threshold"])
    hybrid_vector_weight = float(runtime_params["hybrid_vector_weight"])
    hybrid_bm25_weight = float(runtime_params["hybrid_bm25_weight"])
    hybrid_candidate_k = int(runtime_params["hybrid_candidate_k"])
    hybrid_rrf_k = int(runtime_params["hybrid_rrf_k"])
    answer_max_chars = int(runtime_params["answer_max_chars"])
    retrieval_timeout_seconds = int(runtime_params["retrieval_timeout_ms"]) / 1000
    generation_timeout_seconds = int(runtime_params["generation_timeout_ms"]) / 1000
    embedding_model_path = str(runtime_params["embedding_model_path"])
    embedding_device = str(runtime_params["embedding_device"])
    vector_cache_enabled = bool(runtime_params["vector_cache_enabled"])
    vector_cache_backend = str(runtime_params["vector_cache_backend"])
    vector_cache_ttl_seconds = int(runtime_params["vector_cache_ttl_seconds"])
    context_backend = str(runtime_params["context_backend"])

    answer = "欢迎使用 ReviewPulse Agent。"
    rewritten_query = last_message
    sources: list[dict] = []
    turn_no = 1
    timeout_stage: str | None = None
    rewrite_model = settings.llm_rewrite_model_name or settings.llm_model_name
    generation_model = payload.model or settings.llm_generation_model_name or settings.llm_model_name
    called_models = {
        "rewrite": rewrite_model,
        "generation": generation_model,
        "request": payload.model,
    }

    history_items = await _load_context_items(
        session=session,
        user_id=user["user_id"],
        user_type=user["user_type"],
        session_id=session_id,
        max_context_turns=max_context_turns,
        context_backend=context_backend,
    )
    history_items = _trim_context_by_limits(
        items=history_items,
        max_turns=max_context_turns,
        max_tokens=max_context_tokens,
        session_id=session_id
    )

    rewrite_started = time.monotonic()
    try:
        rewritten_query = await rewrite_question(
            last_message,
            history_items,
            model_name=rewrite_model,
        )
    finally:
        latency_ms["rewrite"] = int((time.monotonic() - rewrite_started) * 1000)

    intent, direct_response = await master_router.determine_intent(
        query=rewritten_query,
        model_name=rewrite_model,
        user_type=user.get("user_type", "user")
    )

    if intent == "system_action":
        answer = direct_response
        sources = []

    elif intent == "general_chat":
        sources = []

        chat_messages = [
            ("system", "你是一个幽默、友好的 AI 助手，请自由回答用户的日常问题或闲聊，不需要拘泥于特定的业务领域。")
        ]
        for item in history_items:
            if "query" in item and item["query"]:
                chat_messages.append(("user", item["query"]))
            if "answer" in item and item["answer"]:
                chat_messages.append(("assistant", item["answer"]))
        chat_messages.append(("user", rewritten_query))

        if not payload.stream:
            generation_started = time.monotonic()
            try:
                answer = await asyncio.wait_for(
                    invoke_chat(
                        messages=chat_messages,
                        model_name=generation_model,
                    ),
                    timeout=generation_timeout_seconds,
                )
                answer = sensitive_filter.filter(answer)
            except asyncio.TimeoutError:
                timeout_stage = "generation"
                answer = "答案生成超时，请稍后重试。"
            finally:
                latency_ms["generation"] = int((time.monotonic() - generation_started) * 1000)

    elif intent == "tool_use":
        sources = []
        tool_chat_messages = await process_tool_use_intent(
            query=rewritten_query,
            user=user,
            session=session,
            model_name=generation_model
        )

        if not payload.stream:
            generation_started = time.monotonic()
            try:
                answer = await asyncio.wait_for(
                    invoke_chat(messages=tool_chat_messages, model_name=generation_model),
                    timeout=generation_timeout_seconds,
                )
                answer = sensitive_filter.filter(answer)
            except asyncio.TimeoutError:
                timeout_stage = "generation"
                answer = "答案生成超时，请稍后重试。"
            finally:
                latency_ms["generation"] = int((time.monotonic() - generation_started) * 1000)
    elif intent == "knowledge_query" and payload.messages:

        try:
            retrieval_started = time.monotonic()
            try:
                sources = await asyncio.wait_for(
                    _search_across_knowledge_bases(
                        session=session,
                        actor=user,
                        query=rewritten_query,
                        top_k=retrieval_top_k,
                        similarity_threshold=similarity_threshold,
                        session_id=session_id,
                        vector_weight=hybrid_vector_weight,
                        bm25_weight=hybrid_bm25_weight,
                        hybrid_candidate_k=hybrid_candidate_k,
                        hybrid_rrf_k=hybrid_rrf_k,
                        embedding_model_path=embedding_model_path,
                        embedding_device=embedding_device,
                        vector_cache_enabled=vector_cache_enabled,
                        vector_cache_backend=vector_cache_backend,
                        vector_cache_ttl_seconds=vector_cache_ttl_seconds,
                    ),
                    timeout=retrieval_timeout_seconds,
                )
            except asyncio.TimeoutError:
                timeout_stage = "retrieval"
                answer = "检索超时，请稍后重试。"
                sources = []
            finally:
                latency_ms["retrieval"] = int((time.monotonic() - retrieval_started) * 1000)

            if timeout_stage is None and not payload.stream:
                generation_started = time.monotonic()
                try:
                    answer = await asyncio.wait_for(
                        answer_with_context(
                            question=rewritten_query,
                            history_turns=history_items,
                            retrieved_items=sources,
                            model_name=generation_model,
                            answer_max_chars=answer_max_chars,
                        ),
                        timeout=generation_timeout_seconds,
                    )
                    answer = sensitive_filter.filter(answer)
                except asyncio.TimeoutError:
                    timeout_stage = "generation"
                    answer = "答案生成超时，请稍后重试。"
                finally:
                    latency_ms["generation"] = int((time.monotonic() - generation_started) * 1000)
        except Exception:
            answer = _fallback_answer(rewritten_query, sources)

        answer = _limit_answer_length(answer, answer_max_chars)

    if payload.stream:
        async def stream_events() -> AsyncIterator[str]:
            streamed_answer_parts: list[str] = []
            nonlocal answer, timeout_stage, turn_no, sources, rewritten_query

            if direct_response:
                streamed_answer_parts.append(direct_response)
                yield _sse_payload({"content": direct_response})
            elif payload.messages and timeout_stage is None:
                generation_started = time.monotonic()
                try:
                    async with asyncio.timeout(generation_timeout_seconds):

                        buffer = ""
                        max_len = sensitive_filter.max_word_len

                        if intent == "general_chat":
                            chat_messages = [
                                ("system",
                                 "你是一个幽默、友好的 AI 助手，请自由回答用户的日常问题或闲聊，不需要拘泥于特定的业务领域。")
                            ]
                            for item in history_items:
                                if item.get("query"):
                                    chat_messages.append(("user", item["query"]))
                                if item.get("answer"):
                                    chat_messages.append(("assistant", item["answer"]))
                            chat_messages.append(("user", rewritten_query))

                            stream_generator = invoke_chat_stream(
                                messages=chat_messages,
                                model_name=generation_model,
                            )
                        elif intent == "tool_use":
                            stream_generator = invoke_chat_stream(
                                messages=tool_chat_messages,
                                model_name=generation_model,
                            )
                        else:
                            stream_generator = answer_with_context_stream(
                                question=rewritten_query,
                                history_turns=history_items,
                                retrieved_items=sources,
                                model_name=generation_model,
                                answer_max_chars=answer_max_chars,
                            )

                        async for chunk in stream_generator:
                            if max_len == 0:
                                streamed_answer_parts.append(chunk)
                                yield _sse_payload({"content": chunk})
                                continue

                            buffer += chunk
                            if len(buffer) > max_len:
                                safe_part = buffer[:-max_len]
                                buffer = buffer[-max_len:]
                                filtered_safe = sensitive_filter.filter(safe_part)
                                if filtered_safe:
                                    streamed_answer_parts.append(filtered_safe)
                                    yield _sse_payload({"content": filtered_safe})

                        if buffer:
                            filtered_rem = sensitive_filter.filter(buffer)
                            if filtered_rem:
                                streamed_answer_parts.append(filtered_rem)
                                yield _sse_payload({"content": filtered_rem})

                except TimeoutError:
                    timeout_stage = "generation"
                    timeout_hint = "\n\n[生成超时，以下为部分回答]"
                    if streamed_answer_parts:
                        streamed_answer_parts.append(timeout_hint)
                        yield _sse_payload({"content": timeout_hint})
                    else:
                        streamed_answer_parts = ["答案生成超时，请稍后重试。"]
                        yield _sse_payload({"content": streamed_answer_parts[0]})
                finally:
                    latency_ms["generation"] = int((time.monotonic() - generation_started) * 1000)

            answer = "".join(streamed_answer_parts) if streamed_answer_parts else answer
            answer = _limit_answer_length(answer, answer_max_chars)
            latency_ms["total"] = int((time.monotonic() - request_started) * 1000)

            if "抱歉，您的问题涉及非业务范围或包含不当内容" in answer:
                sources = []
                rewritten_query = None
                answer = "抱歉，您的问题涉及非业务范围或包含不当内容。我是 ReviewPulse Agent，仅负责解答与商家运营、平台规范及知识库相关的问题，请换个问题试试。"

            turn_no_local, current_context = await _persist_turn_and_context(
                session=session,
                user=user,
                session_id=session_id,
                max_context_turns=max_context_turns,
                max_context_tokens=max_context_tokens,
                context_backend=context_backend,
                user_text=user_text,
                input_type=input_type,
                ocr_text=ocr_text,
                answer=answer,
                rewritten_query=rewritten_query,
                sources=sources,
            )
            turn_no = turn_no_local

            metadata = {
                "done": True,
                "session_id": session_id,
                "turn_no": turn_no,
                "input_type": input_type,
                "ocr_text": ocr_text,
                "sources": sources,
                "rewritten_query": rewritten_query,
                "timeout_stage": timeout_stage,
                "latency_ms": latency_ms,
                "called_models": called_models,
                "model": generation_model,
                "context_turns": len(current_context),
                "user": user,
            }

            logger.info(
                "Chat completion models: session_id=%s rewrite_model=%s generation_model=%s request_model=%s",
                session_id,
                rewrite_model,
                generation_model,
                payload.model,
            )
            logger.info(
                "Chat completion latency: session_id=%s rewrite_ms=%s retrieval_ms=%s generation_ms=%s total_ms=%s",
                session_id,
                latency_ms.get("rewrite"),
                latency_ms.get("retrieval"),
                latency_ms.get("generation"),
                latency_ms.get("total"),
            )
            yield _sse_payload(metadata)

        return StreamingResponse(stream_events(), media_type="text/event-stream")

    latency_ms["total"] = int((time.monotonic() - request_started) * 1000)

    if "抱歉，您的问题涉及非业务范围或包含不当内容" in answer:
        sources = []
        rewritten_query = None
        answer = "抱歉，您的问题涉及非业务范围或包含不当内容。我是 ReviewPulse Agent，仅负责解答与商家运营、平台规范及知识库相关的问题，请换个问题试试。"

    turn_no, current_context = await _persist_turn_and_context(
        session=session,
        user=user,
        session_id=session_id,
        max_context_turns=max_context_turns,
        max_context_tokens=max_context_tokens,
        context_backend=context_backend,
        user_text=user_text,
        input_type=input_type,
        ocr_text=ocr_text,
        answer=answer,
        rewritten_query=rewritten_query,
        sources=sources,
    )

    logger.info(
        "Chat completion models: session_id=%s rewrite_model=%s generation_model=%s request_model=%s",
        session_id,
        rewrite_model,
        generation_model,
        payload.model,
    )
    logger.info(
        "Chat completion latency: session_id=%s rewrite_ms=%s retrieval_ms=%s generation_ms=%s total_ms=%s",
        session_id,
        latency_ms.get("rewrite"),
        latency_ms.get("retrieval"),
        latency_ms.get("generation"),
        latency_ms.get("total"),
    )

    return {
        "model": generation_model,
        "called_models": called_models,
        "message": {"role": "assistant", "content": answer},
        "answer": answer,
        "session_id": session_id,
        "turn_no": turn_no,
        "input_type": input_type,
        "ocr_text": ocr_text,
        "rewritten_query": rewritten_query,
        "sources": sources,
        "timeout_stage": timeout_stage,
        "latency_ms": latency_ms,
        "context_turns": len(current_context),
        "user": user,
    }


@router.get(
    "/sessions/{session_id}/history",
    summary="get_session_history          返回指定会话的对话轮次历史。",
    operation_id="getChatSessionHistory",
)
async def get_session_history(
    session_id: str,
    session: DBSession,
    user: CurrentUser,
    include_inactive: bool = False,
    limit: int | None = None,
):
    _ensure_chat_actor_allowed(user)
    await _ensure_session_exists(session=session, user=user, session_id=session_id)
    items = await list_chat_turns(
        session,
        owner_id=user["user_id"],
        owner_type=user["user_type"],
        session_id=session_id,
        include_inactive=include_inactive,
        limit=limit,
        ascending=True,
    )
    return {
        "session_id": session_id,
        "items": [_serialize_turn_item(item) for item in items],
    }


@router.get(
    "/sessions",
    summary="get_sessions          返回当前用户可访问的会话列表。",
    operation_id="getChatSessions",
)
async def get_sessions(session: DBSession, user: CurrentUser):
    _ensure_chat_actor_allowed(user)
    items = await list_chat_sessions(
        session,
        owner_id=user["user_id"],
        owner_type=user["user_type"],
    )
    return {"items": [_serialize_session_item(item) for item in items]}


@router.get(
    "/sessions/{session_id}/retrieval-config",
    summary="get_session_retrieval_config          返回会话级检索配置覆盖值与生效值。",
    operation_id="getChatSessionRetrievalConfig",
)
async def get_session_retrieval_config(session_id: str, session: DBSession, user: CurrentUser):
    _ensure_chat_actor_allowed(user)
    await _ensure_session_exists(session=session, user=user, session_id=session_id)
    runtime_params = await _resolve_chat_runtime_params(
        session=session,
        user=user,
        session_id=session_id,
        request_max_context_turns=None,
    )
    record = await get_chat_session_for_actor(
        session,
        owner_id=user["user_id"],
        owner_type=user["user_type"],
        session_id=session_id,
    )
    return {
        "session_id": session_id,
        "overrides": {
            "top_k": None if record is None else record.retrieval_top_k,
            "similarity_threshold": None if record is None else record.similarity_threshold,
        },
        "effective": {
            "top_k": int(runtime_params["retrieval_top_k"]),
            "similarity_threshold": float(runtime_params["similarity_threshold"]),
        },
    }


@router.put(
    "/sessions/{session_id}/retrieval-config",
    summary="update_session_retrieval_config          更新会话级 top_k 与相似度阈值覆盖参数。",
    operation_id="updateChatSessionRetrievalConfig",
)
async def update_session_retrieval_config(
    session_id: str,
    payload: SessionRetrievalConfigPayload,
    session: DBSession,
    user: CurrentUser,
):
    _ensure_chat_actor_allowed(user)
    await _ensure_session_exists(session=session, user=user, session_id=session_id)
    record = await update_chat_session_retrieval_config(
        session,
        owner_id=user["user_id"],
        owner_type=user["user_type"],
        session_id=session_id,
        retrieval_top_k=payload.top_k,
        similarity_threshold=payload.similarity_threshold,
    )
    await clear_cached_chat_context(user_type=user["user_type"], user_id=user["user_id"], session_id=session_id)
    return {
        "session_id": session_id,
        "overrides": {
            "top_k": None if record is None else record.retrieval_top_k,
            "similarity_threshold": None if record is None else record.similarity_threshold,
        },
    }


@router.delete(
    "/sessions/{session_id}/context",
    summary="delete_session_context          清空指定会话的上下文记录并同步缓存。",
    operation_id="deleteChatSessionContext",
)
async def delete_session_context(session_id: str, session: DBSession, user: CurrentUser):
    _ensure_chat_actor_allowed(user)
    await _ensure_session_exists(session=session, user=user, session_id=session_id)
    runtime_params = await _resolve_chat_runtime_params(
        session=session,
        user=user,
        session_id=session_id,
        request_max_context_turns=None,
    )
    context_backend = str(runtime_params["context_backend"])
    cleared = await clear_chat_context(
        session,
        owner_id=user["user_id"],
        owner_type=user["user_type"],
        session_id=session_id,
    )
    log_chat_context_store_call(
        "chat_context_clear",
        status="ok",
        backend="mysql",
        session_id=session_id,
        extra={"cleared_turns": int(cleared)},
    )
    if _normalize_context_backend(context_backend) in {"auto", "redis"}:
        await clear_cached_chat_context(user_type=user["user_type"], user_id=user["user_id"], session_id=session_id)
    return {
        "session_id": session_id,
        "cleared_turns": cleared,
    }


@router.patch(
    "/sessions/{session_id}",
    summary="update_session_title          更新指定会话的标题。",
    operation_id="updateChatSessionTitle",
)
async def update_session_title(
    session_id: str,
    payload: RenameSessionRequest,
    session: DBSession,
    user: CurrentUser,
):
    _ensure_chat_actor_allowed(user)
    record = await rename_chat_session(
        session,
        owner_id=user["user_id"],
        owner_type=user["user_type"],
        session_id=session_id,
        title=payload.title,
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在。")
    return _serialize_session_item(record)


@router.delete(
    "/sessions/{session_id}",
    summary="remove_session          删除指定会话并清理对应缓存上下文。",
    operation_id="deleteChatSession",
)
async def remove_session(session_id: str, session: DBSession, user: CurrentUser):
    _ensure_chat_actor_allowed(user)
    runtime_params = await _resolve_chat_runtime_params(
        session=session,
        user=user,
        session_id=session_id,
        request_max_context_turns=None,
    )
    context_backend = str(runtime_params["context_backend"])
    record = await delete_chat_session(
        session,
        owner_id=user["user_id"],
        owner_type=user["user_type"],
        session_id=session_id,
    )
    if _normalize_context_backend(context_backend) in {"auto", "redis"}:
        await clear_cached_chat_context(user_type=user["user_type"], user_id=user["user_id"], session_id=session_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在。")
    return {"session_id": session_id, "deleted": True}


@router.post(
    "/sessions/{session_id}/rollback",
    summary="rollback_session_context          将会话上下文回滚到指定轮次。",
    operation_id="rollbackChatSessionContext",
)
async def rollback_session_context(
    session_id: str,
    payload: RollbackRequest,
    session: DBSession,
    user: CurrentUser,
):
    _ensure_chat_actor_allowed(user)
    await _ensure_session_exists(session=session, user=user, session_id=session_id)
    runtime_params = await _resolve_chat_runtime_params(
        session=session,
        user=user,
        session_id=session_id,
        request_max_context_turns=None,
    )
    context_backend = str(runtime_params["context_backend"])
    rolled_back = await rollback_chat_context(
        session,
        owner_id=user["user_id"],
        owner_type=user["user_type"],
        session_id=session_id,
        turn_no=payload.turn_no,
    )
    active_items = await get_chat_context(
        session,
        owner_id=user["user_id"],
        owner_type=user["user_type"],
        session_id=session_id,
        max_turns=get_settings().chat_max_context_turns,
    )
    log_chat_context_store_call(
        "chat_context_rollback",
        status="ok",
        backend="mysql",
        session_id=session_id,
        extra={"rolled_back_turns": int(rolled_back), "active_turns": len(active_items)},
    )
    if _normalize_context_backend(context_backend) in {"auto", "redis"}:
        await set_cached_chat_context(
            user_type=user["user_type"],
            user_id=user["user_id"],
            session_id=session_id,
            items=[_serialize_turn_item(item) for item in active_items],
        )
    return {
        "session_id": session_id,
        "rolled_back_turns": rolled_back,
        "active_turns": [_serialize_turn_item(item) for item in active_items],
    }


@router.put(
    "/turn/rating",
    summary="update_chat_turn_rating_endpoint          为指定会话轮次设置点赞、点踩或取消评分。",
    operation_id="updateChatTurnRating",
)
async def update_chat_turn_rating_endpoint(
    payload: ChatTurnRatingUpdate,
    session: DBSession,
    user: CurrentUser,
):
    """
    更新聊天回合评分
    """
    _ensure_chat_actor_allowed(user)

    await _ensure_session_exists(session=session, user=user, session_id=payload.session_id)

    updated = await update_chat_turn_rating(
        session,
        owner_id=user["user_id"],
        owner_type=user["user_type"],
        session_id=payload.session_id,
        turn_no=payload.turn_no,
        rating=payload.rating,
    )

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="聊天回合不存在")

    return {"updated": True, "session_id": payload.session_id, "turn_no": payload.turn_no, "rating": payload.rating}


ALLOWED_DATA_FILE_EXTENSIONS = {".csv", ".xlsx", ".xls", ".txt", ".md", ".pdf", ".docx"}
MAX_DATA_FILE_SIZE = 50 * 1024 * 1024  


@router.post(
    "/files/upload",
    summary="upload_chat_file          上传聊天分析文件并落库为 chat 类型文档，返回 doc_id 与文件元数据。",
    operation_id="uploadChatFile",
)
async def upload_chat_file(
    file: UploadFile = File(...),
    session: DBSession = ...,
    user: CurrentUser = ...,
):
    """
    上传数据文件用于聊天中的 Pandas 分析。
    文件存储到 Document 表，uploader_type='chat'，与其他文档隔离。
    """
    from app.db.models import Document as DocumentModel

    _ensure_chat_actor_allowed(user)

    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="缺少文件名")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_DATA_FILE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {ext}，仅支持 {', '.join(ALLOWED_DATA_FILE_EXTENSIONS)}",
        )

    file_path = await save_upload_file(
        file,
        max_upload_size_mb=50,
        allowed_suffixes=ALLOWED_DATA_FILE_EXTENSIONS,
    )

    file_size = file_path.stat().st_size

    doc = DocumentModel(
        uploader_type="chat",
        uploader_id=user["user_id"],
        doc_name=file.filename,
        doc_type=ext.lstrip("."),
        doc_size=file_size,
        file_path=str(file_path),
        status="approved",  
    )
    session.add(doc)
    await session.flush()
    await session.commit()
    await session.refresh(doc)

    return {
        "doc_id": str(doc.doc_id),
        "doc_name": doc.doc_name,
        "doc_type": doc.doc_type,
        "doc_size": doc.doc_size,
    }
