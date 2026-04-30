from __future__ import annotations

from dataclasses import dataclass
import json

from app.core.config import get_settings
from app.rag.embeddings import get_embeddings, resolve_embedding_device, resolve_local_embedding_model_path
from app.worker import tasks
from app.worker.tasks import generate_document_embeddings


@dataclass(slots=True)
class WorkerSettings:
    functions: list
    redis_settings: str
    max_jobs: int = 5


async def on_startup(ctx: dict) -> None:
    settings = get_settings()
    resolved_device = resolve_embedding_device(settings.embedding_device)
    resolved_model_path = str(
        resolve_local_embedding_model_path(
            model_path=settings.bge_model_path,
            models_root=settings.embedding_models_root,
            model_name=settings.bge_model_name,
        )
    )
    ctx["embedding_device"] = resolved_device
    ctx["embedding_model_path"] = resolved_model_path
    ctx["embeddings"] = get_embeddings(resolved_model_path, resolved_device)


async def on_shutdown(ctx: dict) -> None:
    ctx.clear()


worker_settings = WorkerSettings(
    functions=[tasks.task_ingest_document, tasks.task_agent_reasoning, generate_document_embeddings],
    redis_settings=get_settings().redis_url,
    max_jobs=5,
)


def main() -> None:
    settings = get_settings()
    print(
        json.dumps(
            {
                "redis": worker_settings.redis_settings,
                "max_jobs": worker_settings.max_jobs,
                "functions": [func.__name__ for func in worker_settings.functions],
                "embedding_device": resolve_embedding_device(settings.embedding_device),
                "bge_model_path": settings.bge_model_path,
                "chroma_path": settings.chroma_path,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
