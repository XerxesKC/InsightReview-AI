from __future__ import annotations

from pathlib import Path
from uuid import uuid4
from typing import Any
import asyncio

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.db.crud import get_system_config_map
from app.rag.vector_store import get_vector_store
from app.services.etl_pipeline import build_document_chunks
from app.rag.embeddings import get_embeddings, resolve_embedding_device, resolve_local_embedding_model_path

async def _load_runtime_system_config() -> dict[str, str]:
    """
    每次任务执行时读取最新系统配置，确保前端切换后端参数可立即生效。
    """
    keys = [
        "embedding_model_path",
        "embedding_device",
        "vector_store_path",
        "chunk_size",
        "chunk_overlap",
    ]
    async with AsyncSessionLocal() as session:
        return await get_system_config_map(session, keys=keys)


async def enqueue_ingest_document(file_path: str) -> str:
    """Return a mock task id for the scaffold stage.

    Later this can be replaced with Arq enqueue logic.
    """
    return f"mock-task-{uuid4().hex}"


async def task_ingest_document(ctx: dict, file_path: str) -> dict:
    settings = get_settings()
    runtime_cfg = await _load_runtime_system_config()

    model_path = str(
        resolve_local_embedding_model_path(
            model_path=runtime_cfg.get("embedding_model_path") or ctx.get("embedding_model_path") or settings.bge_model_path,
            models_root=settings.embedding_models_root,
            model_name=settings.bge_model_name,
        )
    )
    embedding_device = resolve_embedding_device(
        runtime_cfg.get("embedding_device") or ctx.get("embedding_device", settings.embedding_device)
    )
    persist_directory = runtime_cfg.get("vector_store_path") or settings.chroma_path

    chunks = build_document_chunks(file_path)
    collection_name = Path(file_path).stem.replace(" ", "_").lower() or "default"

    vector_store = get_vector_store(
        collection_name=collection_name,
        persist_directory=persist_directory,
        embedding_device=embedding_device,
        model_path=model_path,
    )
    inserted = vector_store.add_documents(chunks)

    return {
        "file_path": file_path,
        "chunks": len(chunks),
        "inserted": inserted,
        "collection_name": collection_name,
        "embedding_model_path": model_path,
        "embedding_device": embedding_device,
        "vector_store_path": persist_directory,
    }

async def generate_document_embeddings(texts: list[str], model_path: str = None, device: str = "auto") -> dict[
    str, Any]:
    """
    生成文档的嵌入向量（批量处理）

    参数:
        texts: 文本列表
        model_path: 模型路径，如果为None则使用配置的路径
        device: 计算设备

    返回:
        嵌入向量列表，每个向量对应一个文本
    """
    try:
        settings = get_settings()



        resolved_device = resolve_embedding_device(device)
        embeddings_model = get_embeddings(
            model_path=model_path or settings.bge_model_path,
            device=resolved_device,
            model_name=settings.bge_model_name,
        )

        valid_texts = [text.strip() for text in texts if text and text.strip()]

        if not valid_texts:
            return {
                "status": "success",
                "message": "没有有效的文本需要处理",
                "embeddings": [],
                "texts_count": 0,
                "embeddings_count": 0
            }

        embeddings = embeddings_model.embed_documents(valid_texts)

        print(f"成功为 {len(valid_texts)} 个文本生成嵌入向量，向量维度: {len(embeddings[0]) if embeddings else 0}")

        return {
            "status": "success",
            "texts_count": len(valid_texts),
            "embeddings_count": len(embeddings),
            "embedding_dim": len(embeddings[0]) if embeddings else 0,
            "embedding_model_path": str(embeddings_model.model_path),
            "embedding_device": resolved_device,
            "embeddings": embeddings
        }

    except Exception as e:
        print(f"生成文档嵌入向量失败: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "texts_count": len(texts) if texts else 0
        }

async def task_agent_reasoning(ctx: dict, prompt: str) -> dict:
    return {"prompt": prompt, "status": "queued"}

async def main():
    texts = ["你好啊!", "你好!", "你是谁?", "我是张三", "你好，我是李四!"]
    model_path = r"C:\Users\12550\Desktop\homework\实习\project\小众点评\review-pulse-agent\data\bge-model\BAAI\bge-large-zh-v1.5"
    result = await generate_document_embeddings(texts, model_path)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
