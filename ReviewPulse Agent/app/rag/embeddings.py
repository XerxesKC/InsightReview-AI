from __future__ import annotations

from collections.abc import Iterable
from functools import lru_cache
from pathlib import Path

from sentence_transformers import SentenceTransformer

from app.core.config import get_settings

_MODEL_MARKER_FILES = (
    "modules.json",
    "tokenizer_config.json",
    "sentence_bert_config.json",
    "model.safetensors",
    "pytorch_model.bin",
)


def resolve_embedding_device(preferred_device: str = "auto") -> str:
    import torch

    device = (preferred_device or "auto").strip().lower()
    if device in {"", "auto"}:
        return "cuda" if torch.cuda.is_available() else "cpu"
    if device.startswith("cuda") and not torch.cuda.is_available():
        return "cpu"
    return device


def is_valid_embedding_model_dir(model_dir: str | Path) -> bool:
    target = Path(model_dir)
    if not target.is_dir():
        return False
    if not (target / "config.json").exists():
        return False
    name = target.name
    if name.endswith("_Pooling") or name.startswith("1_"):
        return False
    return any((target / marker).exists() for marker in _MODEL_MARKER_FILES)


def discover_embedding_model_dirs(root_dir: str | Path) -> list[Path]:
    root = Path(root_dir)
    if not root.exists() or not root.is_dir():
        return []

    candidates = [root, *root.rglob("*")]
    model_dirs = sorted({p.resolve() for p in candidates if is_valid_embedding_model_dir(p)}, key=lambda p: str(p))
    return model_dirs


def _match_model_name(model_dir: Path, model_name: str | None) -> bool:
    if not model_name:
        return False
    normalized = model_name.replace("\\", "/").strip("/").lower()
    if not normalized:
        return False
    model_path = str(model_dir).replace("\\", "/").lower()
    return model_path.endswith(normalized) or f"/{normalized}/" in f"/{model_path}/"


def _pick_best_model_dir(model_dirs: list[Path], model_name: str | None) -> Path:
    if not model_dirs:
        raise RuntimeError("未找到可用的本地 Embedding 模型目录。")

    for model_dir in model_dirs:
        if _match_model_name(model_dir, model_name):
            return model_dir

    return model_dirs[0]


def resolve_local_embedding_model_path(
    model_path: str | Path | None = None,
    *,
    models_root: str | Path | None = None,
    model_name: str | None = None,
) -> Path:
    settings = get_settings()
    preferred_name = model_name or settings.bge_model_name

    direct_candidate = Path(model_path) if model_path else Path(settings.bge_model_path)
    if is_valid_embedding_model_dir(direct_candidate):
        return direct_candidate.resolve()

    nested_from_direct = discover_embedding_model_dirs(direct_candidate)
    if nested_from_direct:
        return _pick_best_model_dir(nested_from_direct, preferred_name)

    root_candidate = Path(models_root) if models_root else Path(settings.embedding_models_root)
    discovered = discover_embedding_model_dirs(root_candidate)
    if discovered:
        return _pick_best_model_dir(discovered, preferred_name)

    raise RuntimeError(
        f"未在本地找到可用 Embedding 模型。请检查目录：{direct_candidate} 或 {root_candidate}"
    )


class LocalBGEEmbeddings:
    def __init__(self, model_path: str | Path, model_name: str, device: str = "auto") -> None:
        self.model_name = model_name
        self.model_path = resolve_local_embedding_model_path(model_path=model_path, model_name=model_name)
        self.device = resolve_embedding_device(device)
        self.model = SentenceTransformer(str(self.model_path), device=self.device)

    def embed_documents(self, texts: Iterable[str]) -> list[list[float]]:
        items = [text.strip() for text in texts if text and text.strip()]
        if not items:
            return []
        vectors = self.model.encode(items, normalize_embeddings=True, convert_to_numpy=True)
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        vectors = self.model.encode([text], normalize_embeddings=True, convert_to_numpy=True)
        return vectors[0].tolist()


@lru_cache(maxsize=8)
def _get_embeddings_cached(model_path: str, model_name: str, device: str) -> LocalBGEEmbeddings:
    return LocalBGEEmbeddings(model_path=model_path, model_name=model_name, device=device)


def get_embeddings(
    model_path: str | None = None,
    device: str = "auto",
    model_name: str | None = None,
) -> LocalBGEEmbeddings:
    settings = get_settings()
    resolved_name = model_name or settings.bge_model_name
    resolved_path = resolve_local_embedding_model_path(model_path=model_path, model_name=resolved_name)
    resolved_device = resolve_embedding_device(device)
    return _get_embeddings_cached(str(resolved_path), resolved_name, resolved_device)
