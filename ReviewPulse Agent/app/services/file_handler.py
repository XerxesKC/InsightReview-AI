from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings


async def save_upload_file(
    upload_file: UploadFile,
    *,
    max_upload_size_mb: int | None = None,
    allowed_suffixes: set[str] | None = None,
) -> Path:
    settings = get_settings()
    suffix = Path(upload_file.filename or "").suffix.lower()
    effective_allowed = allowed_suffixes if allowed_suffixes is not None else settings.allowed_upload_suffixes
    if suffix not in effective_allowed:
        allowed = ", ".join(ext.lstrip(".") for ext in sorted(effective_allowed))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件格式: {suffix or '未知'}。目前仅支持: {allowed}。",
        )

    content = await upload_file.read()
    effective_max_mb = max_upload_size_mb if max_upload_size_mb is not None else settings.max_upload_size_mb
    max_bytes = effective_max_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件过大。最大允许上传体积为 {settings.max_upload_size_mb} MB。",
        )

    target = settings.upload_path / f"{uuid4().hex}_{upload_file.filename}"
    target.write_bytes(content)
    await upload_file.close()
    return target


def read_file_bytes(file_path: str | Path) -> bytes:
    return Path(file_path).read_bytes()
