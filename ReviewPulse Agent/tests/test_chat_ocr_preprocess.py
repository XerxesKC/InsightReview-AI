from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException

from app.api.v1 import chat
from app.core.config import get_settings


class _SettingsGuard:
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.original_upload_dir = settings.upload_dir
        self.original_chat_allowed_image_extensions = settings.chat_allowed_image_extensions

    def restore(self) -> None:
        self.settings.upload_dir = self.original_upload_dir
        self.settings.chat_allowed_image_extensions = self.original_chat_allowed_image_extensions


def test_extract_image_id_from_url() -> None:
    image_id = "0123456789abcdef0123456789abcdef"
    assert chat._extract_image_id_from_url(f"/api/v1/chat/images/{image_id}") == image_id
    assert chat._extract_image_id_from_url("/api/v1/chat/images/not-valid") is None


def test_compose_chat_query_with_ocr() -> None:
    assert chat._compose_chat_query_with_ocr(user_text="", ocr_text="识别内容") == "识别内容"
    assert "[OCR文本]" in chat._compose_chat_query_with_ocr(user_text="用户问题", ocr_text="识别内容")


def test_detect_chat_input_type() -> None:
    assert chat._detect_chat_input_type(user_text="hello", ocr_text=None, has_image=False) == "text"
    assert chat._detect_chat_input_type(user_text="", ocr_text="识别内容", has_image=True) == "image_ocr"
    assert chat._detect_chat_input_type(user_text="用户问题", ocr_text="识别内容", has_image=True) == "mixed"


def test_resolve_chat_image_path_by_image_id(tmp_path) -> None:
    guard = _SettingsGuard()
    settings = guard.settings
    settings.upload_dir = str(tmp_path)
    settings.chat_allowed_image_extensions = "png"

    image_id = "0123456789abcdef0123456789abcdef"
    target = Path(tmp_path) / f"{image_id}_demo.png"
    target.write_bytes(b"fake")

    try:
        resolved = chat._resolve_chat_image_path(image_id=image_id, image_url=None)
        assert resolved == target
    finally:
        guard.restore()


def test_resolve_chat_image_path_rejects_bad_suffix(tmp_path) -> None:
    guard = _SettingsGuard()
    settings = guard.settings
    settings.upload_dir = str(tmp_path)
    settings.chat_allowed_image_extensions = "png"

    image_id = "0123456789abcdef0123456789abcdef"
    target = Path(tmp_path) / f"{image_id}_demo.txt"
    target.write_bytes(b"fake")

    try:
        try:
            chat._resolve_chat_image_path(image_id=image_id, image_url=None)
            assert False, "expected HTTPException"
        except HTTPException as exc:
            assert exc.status_code == 400
    finally:
        guard.restore()

