from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import torch

from app.core.config import get_settings
from app.rag.embeddings import get_embeddings, resolve_embedding_device
from app.rag.vector_store import get_vector_store


def main() -> None:
    settings = get_settings()
    resolved_device = resolve_embedding_device(settings.embedding_device)
    embeddings = get_embeddings(settings.bge_model_path, settings.embedding_device)

    store = get_vector_store(
        collection_name="runtime_smoke",
        persist_directory=settings.chroma_path,
        embedding_device=settings.embedding_device,
        model_path=settings.bge_model_path,
    )
    store.delete_collection()
    inserted = store.add_documents(
        [
            {"id": "doc-1", "content": "西安交通大学的智能评教系统支持知识库问答。", "source": "smoke", "chunk_index": 0},
            {"id": "doc-2", "content": "ReviewPulse 使用本地 BGE 模型和 Chroma 向量库。", "source": "smoke", "chunk_index": 1},
        ]
    )
    results = store.similarity_search("本地向量库使用什么", k=2)

    payload = {
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "resolved_device": resolved_device,
        "embedding_runtime_device": getattr(embeddings, "device", "unknown"),
        "model_path": str(Path(settings.bge_model_path).resolve()),
        "model_exists": Path(settings.bge_model_path, "config.json").exists(),
        "inserted": inserted,
        "results_count": len(results),
        "top_result": results[0] if results else None,
    }
    Path(PROJECT_ROOT / "rag_runtime_result.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
