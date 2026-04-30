from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.deps import DBSession
from app.core.config import get_settings
from app.core.redis_client import get_redis_client
from app.db.crud import (
    get_system_config_map,
    get_system_config_value,
    upsert_system_config,
    upsert_system_config_map,
)
from app.services.model_discovery import list_local_embedding_models

router = APIRouter(prefix="/admin", tags=["admin"])


class ConfigPayload(BaseModel):
    key: str
    value: str


class FineTunePayload(BaseModel):
    model_name: str = Field(
        default_factory=lambda: get_settings().llm_generation_model_name or get_settings().llm_model_name
    )
    dataset_path: str


class SetEmbeddingModelPayload(BaseModel):
    modelName: str = Field(..., min_length=1)
    modelPath: str = Field(..., min_length=1)


class SystemParamsPayload(BaseModel):
    chunkSize: int = Field(..., ge=1)
    chunkOverlap: int = Field(..., ge=0)
    fileUploadMaxSizeMB: int = Field(..., ge=1)
    vectorStorePath: str = Field(..., min_length=1)
    requestTimeoutMs: int = Field(..., ge=1000)
    chatMaxContextTurns: int = Field(default=10, ge=1, le=50)
    chatMaxContextTokens: int = Field(default=3000, ge=200, le=50000)
    chatRetrievalTopK: int = Field(default=4, ge=1, le=20)
    chatSimilarityThreshold: float = Field(default=0.2, ge=0, le=1)
    chatAnswerMaxChars: int = Field(default=500, ge=50, le=5000)
    chatRetrievalTimeoutMs: int = Field(default=8000, ge=1000, le=600000)
    chatGenerationTimeoutMs: int = Field(default=15000, ge=1000, le=600000)
    chatVectorCacheEnabled: bool = Field(default=True)
    chatVectorCacheBackend: str = Field(default="auto", min_length=1)
    chatVectorCacheTtlSeconds: int = Field(default=300, ge=1, le=86400)
    chatContextBackend: str = Field(default="auto", min_length=1)


@router.post(
    "/config",
    summary="save_config          按 key/value 保存或更新单个系统配置。",
    operation_id="saveSystemConfig",
)
async def save_config(payload: ConfigPayload, session: DBSession):
    config = await upsert_system_config(session, key=payload.key, value=payload.value)
    return {"id": config.config_id, "key": config.config_key, "value": config.config_value}


@router.post(
    "/fine-tune",
    summary="trigger_fine_tune          提交模型微调任务参数（当前为占位实现）。",
    operation_id="triggerFineTuneTask",
)
async def trigger_fine_tune(payload: FineTunePayload):
    return {
        "status": "accepted",
        "model_name": payload.model_name,
        "dataset_path": payload.dataset_path,
        "message": "微调任务入口已预留，后续接入实际调度。",
    }


@router.get(
    "/system/embedding-models",
    summary="get_embedding_models          返回当前生效模型与本地可选 Embedding 模型列表。",
    operation_id="getSystemEmbeddingModels",
)
async def get_embedding_models(session: DBSession):
    settings = get_settings()
    models = list_local_embedding_models(settings.embedding_models_root)
    active_model_name = await get_system_config_value(session, key="embedding_model_name")
    active_model_path = await get_system_config_value(session, key="embedding_model_path")
    return {
        "activeModelName": active_model_name or settings.bge_model_name,
        "activeModelPath": active_model_path or settings.bge_model_path,
        "models": models,
    }


@router.put(
    "/system/embedding-model",
    summary="set_embedding_model          设置系统使用的 Embedding 模型名称与路径。",
    operation_id="setSystemEmbeddingModel",
)
async def set_embedding_model(payload: SetEmbeddingModelPayload, session: DBSession):
    settings = get_settings()
    models = list_local_embedding_models(settings.embedding_models_root)
    valid_paths = {item["path"] for item in models}
    if payload.modelPath not in valid_paths:
        return {"success": False, "message": "模型路径不在可选列表中"}

    await upsert_system_config_map(
        session,
        items={
            "embedding_model_name": payload.modelName,
            "embedding_model_path": payload.modelPath,
        },
    )
    return {"success": True, "message": "Embedding 模型已更新"}


@router.get(
    "/system/params",
    summary="get_system_params          读取分块、超时、上下文与缓存等系统运行参数。",
    operation_id="getSystemParams",
)
async def get_system_params(session: DBSession):
    settings = get_settings()
    keys = [
        "chunk_size",
        "chunk_overlap",
        "file_upload_max_size_mb",
        "vector_store_path",
        "request_timeout_ms",
        "chat_max_context_turns",
        "chat_max_context_tokens",
        "chat_retrieval_top_k",
        "chat_similarity_threshold",
        "chat_answer_max_chars",
        "chat_retrieval_timeout_ms",
        "chat_generation_timeout_ms",
        "chat_vector_cache_enabled",
        "chat_vector_cache_backend",
        "chat_vector_cache_ttl_seconds",
        "chat_context_backend",
    ]
    config_map = await get_system_config_map(session, keys=keys)

    return {
        "chunkSize": int(config_map.get("chunk_size", 500)),
        "chunkOverlap": int(config_map.get("chunk_overlap", 50)),
        "fileUploadMaxSizeMB": int(config_map.get("file_upload_max_size_mb", settings.max_upload_size_mb)),
        "vectorStorePath": config_map.get("vector_store_path", settings.chroma_path),
        "requestTimeoutMs": int(config_map.get("request_timeout_ms", 30000)),
        "chatMaxContextTurns": int(config_map.get("chat_max_context_turns", settings.chat_max_context_turns)),
        "chatMaxContextTokens": int(config_map.get("chat_max_context_tokens", settings.chat_max_context_tokens)),
        "chatRetrievalTopK": int(config_map.get("chat_retrieval_top_k", settings.chat_retrieval_top_k)),
        "chatSimilarityThreshold": float(config_map.get("chat_similarity_threshold", settings.chat_similarity_threshold)),
        "chatAnswerMaxChars": int(config_map.get("chat_answer_max_chars", settings.chat_answer_max_chars)),
        "chatRetrievalTimeoutMs": int(config_map.get("chat_retrieval_timeout_ms", settings.chat_retrieval_timeout_ms)),
        "chatGenerationTimeoutMs": int(config_map.get("chat_generation_timeout_ms", settings.chat_generation_timeout_ms)),
        "chatVectorCacheEnabled": str(
            config_map.get("chat_vector_cache_enabled", str(settings.chat_vector_cache_enabled))
        ).strip().lower() in {"1", "true", "yes", "on"},
        "chatVectorCacheBackend": (
            config_map.get("chat_vector_cache_backend", settings.chat_vector_cache_backend)
            or "auto"
        ).strip().lower(),
        "chatVectorCacheTtlSeconds": int(
            config_map.get("chat_vector_cache_ttl_seconds", settings.chat_vector_cache_ttl_seconds)
        ),
        "chatContextBackend": (
            config_map.get("chat_context_backend", settings.chat_context_backend)
            or "auto"
        ).strip().lower(),
    }


@router.put(
    "/system/params",
    summary="update_system_params          更新分块、检索、上下文及缓存等参数配置。",
    operation_id="updateSystemParams",
)
async def update_system_params(payload: SystemParamsPayload, session: DBSession):
    if payload.chunkOverlap >= payload.chunkSize:
        return {"success": False, "message": "chunkOverlap 必须小于 chunkSize"}

    backend = (payload.chatVectorCacheBackend or "auto").strip().lower()
    if backend not in {"auto", "redis", "memory", "none", "off", "disabled"}:
        return {"success": False, "message": "chatVectorCacheBackend 仅支持 auto/redis/memory/none"}

    context_backend = (payload.chatContextBackend or "auto").strip().lower()
    if context_backend not in {"auto", "redis", "mysql"}:
        return {"success": False, "message": "chatContextBackend 仅支持 auto/redis/mysql"}
    if context_backend == "redis":
        redis_client = await get_redis_client()
        if redis_client is None:
            return {"success": False, "message": "Redis 当前不可用，无法切换到 redis 模式"}

    await upsert_system_config_map(
        session,
        items={
            "chunk_size": str(payload.chunkSize),
            "chunk_overlap": str(payload.chunkOverlap),
            "file_upload_max_size_mb": str(payload.fileUploadMaxSizeMB),
            "vector_store_path": payload.vectorStorePath,
            "request_timeout_ms": str(payload.requestTimeoutMs),
            "chat_max_context_turns": str(payload.chatMaxContextTurns),
            "chat_max_context_tokens": str(payload.chatMaxContextTokens),
            "chat_retrieval_top_k": str(payload.chatRetrievalTopK),
            "chat_similarity_threshold": str(payload.chatSimilarityThreshold),
            "chat_answer_max_chars": str(payload.chatAnswerMaxChars),
            "chat_retrieval_timeout_ms": str(payload.chatRetrievalTimeoutMs),
            "chat_generation_timeout_ms": str(payload.chatGenerationTimeoutMs),
            "chat_vector_cache_enabled": str(payload.chatVectorCacheEnabled),
            "chat_vector_cache_backend": backend,
            "chat_vector_cache_ttl_seconds": str(payload.chatVectorCacheTtlSeconds),
            "chat_context_backend": context_backend,
        },
    )
    return {"success": True, "message": "系统参数已更新"}
