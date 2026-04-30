from pathlib import Path

from app.core.config import get_settings
from app.rag.embeddings import (
    discover_embedding_model_dirs,
    resolve_embedding_device,
    resolve_local_embedding_model_path,
)


def test_bge_model_path_points_to_specific_local_directory() -> None:
    settings = get_settings()
    assert "bge-large-zh-v1.5" in settings.bge_model_path.replace("\\", "/")


def test_resolve_embedding_device_prefers_known_values() -> None:
    assert resolve_embedding_device("cpu") == "cpu"
    assert resolve_embedding_device("auto") in {"cpu", "cuda"}


def test_discovery_finds_valid_models_from_root_and_nested(tmp_path: Path) -> None:
    direct_model = tmp_path / "direct-model"
    direct_model.mkdir(parents=True)
    (direct_model / "config.json").write_text("{}", encoding="utf-8")
    (direct_model / "modules.json").write_text("{}", encoding="utf-8")

    nested_model = tmp_path / "vendor" / "bge-test"
    nested_model.mkdir(parents=True)
    (nested_model / "config.json").write_text("{}", encoding="utf-8")
    (nested_model / "tokenizer_config.json").write_text("{}", encoding="utf-8")

    discovered = discover_embedding_model_dirs(tmp_path)
    discovered_set = {str(item) for item in discovered}

    assert str(direct_model.resolve()) in discovered_set
    assert str(nested_model.resolve()) in discovered_set


def test_resolver_accepts_models_root_with_subfolders(tmp_path: Path) -> None:
    model_root = tmp_path / "bge-model"
    target_model = model_root / "BAAI" / "bge-large-zh-v1.5"
    target_model.mkdir(parents=True)
    (target_model / "config.json").write_text("{}", encoding="utf-8")
    (target_model / "modules.json").write_text("{}", encoding="utf-8")

    resolved = resolve_local_embedding_model_path(
        model_path=str(model_root),
        models_root=str(model_root),
        model_name="BAAI/bge-large-zh-v1.5",
    )

    assert resolved == target_model.resolve()
