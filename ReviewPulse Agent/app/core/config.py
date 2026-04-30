from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DEFAULT_BGE_MODEL_DIR = DATA_DIR / "bge-model" / "BAAI" / "bge-large-zh-v1.5"


class Settings(BaseSettings):
    """Application settings loaded from environment variables and `.env`."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "ReviewPulse Agent"
    app_version: str = "0.1.0"
    app_port: int = 8001
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    allowed_origins: list[str] = Field(default_factory=lambda: ["*"])

    api_key: str = "dev-api-key"
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    database_url: str = "mysql+asyncmy://root:xjtuse@127.0.0.1:3306/review_pulse?charset=utf8mb4"
    database_auto_create: bool = False
    redis_url: str = "redis://localhost:6565/0"
    redis_auto_start_on_main: bool = True
    redis_docker_service_name: str = "redis"
    redis_compose_file: str = str(BASE_DIR / "docker-compose.yml")
    redis_start_timeout_seconds: int = 15
    chroma_path: str = str(DATA_DIR / "chroma")
    bge_model_name: str = "BAAI/bge-large-zh-v1.5"
    bge_model_path: str = str(DEFAULT_BGE_MODEL_DIR)
    embedding_models_root: str = str(DATA_DIR / "bge-model")
    upload_dir: str = str(DATA_DIR / "files")
    log_dir: str = str(DATA_DIR / "logs")

    llm_rewrite_model_name: str = "qwen-turbo"
    llm_generation_model_name: str = "qwen3.5-flash"
    llm_model_name: str = "qwen3.5-flash"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2048
    embedding_device: str = "auto"
    max_upload_size_mb: int = 50
    allowed_upload_extensions: str = "pdf,docx,txt,md,csv"
    chat_allowed_image_extensions: str = "jpg,jpeg,png,bmp,webp"
    chat_ocr_enabled: bool = True
    chat_ocr_gpu_enabled: bool = False
    chat_ocr_lang: str = "ch"
    chat_max_context_turns: int = 10
    chat_max_context_tokens: int = 3000
    chat_retrieval_top_k: int = 4
    chat_similarity_threshold: float = 0.25
    chat_hybrid_vector_weight: float = 0.5
    chat_hybrid_bm25_weight: float = 0.5
    chat_hybrid_candidate_k: int = 50
    chat_hybrid_rrf_k: int = 60
    chat_hybrid_log_enabled: bool = True
    chat_hybrid_log_filename: str = "hybrid_retrieval_scores.jsonl"
    chat_answer_max_chars: int = 1000
    chat_retrieval_timeout_ms: int = 30000
    chat_generation_timeout_ms: int = 300000
    chat_redis_prefix: str = "reviewpulse:chat"
    chat_context_ttl_seconds: int = 60 * 60 * 24 * 7
    chat_context_backend: str = "auto"
    chat_vector_cache_enabled: bool = True
    chat_vector_cache_backend: str = "auto"
    chat_vector_cache_prefix: str = "reviewpulse:retrieval"
    chat_vector_cache_ttl_seconds: int = 300
    query_spell_correction_enabled: bool = True
    chat_orchestrator_mode: str = "graph"

    @property
    def upload_path(self) -> Path:
        return Path(self.upload_dir)

    @property
    def log_path(self) -> Path:
        return Path(self.log_dir)

    @property
    def allowed_upload_suffixes(self) -> set[str]:
        return {
            f".{item.strip().lower().lstrip('.')}"
            for item in self.allowed_upload_extensions.split(",")
            if item.strip()
        }

    @property
    def chat_allowed_image_suffixes(self) -> set[str]:
        return {
            f".{item.strip().lower().lstrip('.')}"
            for item in self.chat_allowed_image_extensions.split(",")
            if item.strip()
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    for path in (
            DATA_DIR,
            settings.upload_path,
            Path(settings.chroma_path),
            Path(settings.bge_model_path),
            Path(settings.embedding_models_root),
            settings.log_path
    ):
        path.mkdir(parents=True, exist_ok=True)
    return settings
