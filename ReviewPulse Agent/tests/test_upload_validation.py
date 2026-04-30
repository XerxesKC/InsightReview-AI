from __future__ import annotations

import asyncio
from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile

from app.core.config import get_settings
from app.services.file_handler import save_upload_file


class _SettingsGuard:
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.original_upload_dir = settings.upload_dir
        self.original_allowed_upload_extensions = settings.allowed_upload_extensions
        self.original_max_upload_size_mb = settings.max_upload_size_mb

    def restore(self) -> None:
        self.settings.upload_dir = self.original_upload_dir
        self.settings.allowed_upload_extensions = self.original_allowed_upload_extensions
        self.settings.max_upload_size_mb = self.original_max_upload_size_mb


def test_save_upload_file_accepts_allowed_suffix_within_size_limit(tmp_path) -> None:
    guard = _SettingsGuard()
    settings = guard.settings
    settings.upload_dir = str(tmp_path)
    settings.allowed_upload_extensions = "txt,md"
    settings.max_upload_size_mb = 1

    upload = UploadFile(filename="note.txt", file=BytesIO(b"hello review pulse"))
    try:
        stored_path = asyncio.run(save_upload_file(upload))
        assert stored_path.exists()
        assert stored_path.suffix == ".txt"
        assert stored_path.read_bytes() == b"hello review pulse"
    finally:
        guard.restore()


def test_save_upload_file_rejects_unsupported_extension(tmp_path) -> None:
    guard = _SettingsGuard()
    settings = guard.settings
    settings.upload_dir = str(tmp_path)
    settings.allowed_upload_extensions = "txt"
    settings.max_upload_size_mb = 1

    upload = UploadFile(filename="malware.exe", file=BytesIO(b"nope"))
    try:
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(save_upload_file(upload))
        assert exc_info.value.status_code == 400
        assert "Unsupported file type" in exc_info.value.detail
    finally:
        guard.restore()


def test_save_upload_file_rejects_file_over_size_limit(tmp_path) -> None:
    guard = _SettingsGuard()
    settings = guard.settings
    settings.upload_dir = str(tmp_path)
    settings.allowed_upload_extensions = "txt"
    settings.max_upload_size_mb = 1

    oversized_content = b"a" * (1024 * 1024 + 1)
    upload = UploadFile(filename="big.txt", file=BytesIO(oversized_content))
    try:
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(save_upload_file(upload))
        assert exc_info.value.status_code == 400
        assert "File too large" in exc_info.value.detail
    finally:
        guard.restore()

