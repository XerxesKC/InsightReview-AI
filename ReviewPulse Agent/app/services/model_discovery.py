from __future__ import annotations

import json
from pathlib import Path

from sentence_transformers import SentenceTransformer

from app.rag.embeddings import discover_embedding_model_dirs, resolve_local_embedding_model_path


def _try_read_json(file_path: Path) -> dict:
    if not file_path.exists():
        return {}
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _try_read_dimension(model_dir: Path) -> int | None:
    data = _try_read_json(model_dir / "config.json")
    for key in ("sentence_embedding_dimension", "hidden_size", "d_model", "dim"):
        val = data.get(key)
        if isinstance(val, int) and val > 0:
            return val
    return None


def _is_model_loadable(model_dir: Path) -> bool:
    try:
        model = SentenceTransformer(str(model_dir), device="cpu")
    except Exception:
        return False
    del model
    return True


def list_local_embedding_models(root_dir: str | Path, *, validate_loadable: bool = True) -> list[dict]:
    root = Path(root_dir).resolve()
    if not root.exists():
        return []

    model_dirs = discover_embedding_model_dirs(root)
    if not model_dirs:
        return []

    default_model_path: str | None = None
    try:
        default_model_path = str(resolve_local_embedding_model_path(models_root=root))
    except Exception:
        default_model_path = None

    models: list[dict] = []
    for model_dir in model_dirs:
        if validate_loadable and not _is_model_loadable(model_dir):
            continue

        try:
            rel_name = str(model_dir.relative_to(root)).replace("\\", "/")
        except ValueError:
            rel_name = model_dir.name
        models.append(
            {
                "name": rel_name if rel_name != "." else model_dir.name,
                "path": str(model_dir.resolve()),
                "dimension": _try_read_dimension(model_dir),
                "description": "",
                "is_default": str(model_dir.resolve()) == str(default_model_path),
            }
        )

    return models
