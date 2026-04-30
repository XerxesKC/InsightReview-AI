import warnings
warnings.filterwarnings("ignore", category=UserWarning, message=".*pkg_resources is deprecated.*")
warnings.filterwarnings("ignore", module="jieba")

from app.core.config import get_settings
from app.core.redis_bootstrap import bootstrap_redis_for_local_run, format_bootstrap_messages
from app.rag.embeddings import get_embeddings, resolve_local_embedding_model_path
from app.services.model_discovery import list_local_embedding_models


def _validate_bge_model_or_exit() -> None:
    settings = get_settings()

    try:
        resolved_model_path = resolve_local_embedding_model_path(
            model_path=settings.bge_model_path,
            models_root=settings.embedding_models_root,
            model_name=settings.bge_model_name,
        )
    except Exception as exc:
        print(f"[BGE][Error] 模型路径校验失败：{exc}")
        raise SystemExit(1) from exc

    available_models = list_local_embedding_models(settings.embedding_models_root, validate_loadable=True)
    if not available_models:
        print(
            f"[BGE][Error] 在目录 {settings.embedding_models_root} 未检测到可用模型。"
            "请检查模型文件是否完整（config.json / tokenizer / 权重文件）。"
        )
        raise SystemExit(1)

    try:
        get_embeddings(model_path=str(resolved_model_path), device=settings.embedding_device, model_name=settings.bge_model_name)
    except Exception as exc:
        print(f"[BGE][Error] 模型加载失败：{resolved_model_path}，错误：{exc}")
        raise SystemExit(1) from exc

    print(f"[BGE][OK] 已检测到可用模型，当前使用：{resolved_model_path}")


def main() -> None:
    import uvicorn

    settings = get_settings()
    _validate_bge_model_or_exit()
    redis_status = bootstrap_redis_for_local_run()
    for line in format_bootstrap_messages(redis_status):
        print(line)
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=settings.app_port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
