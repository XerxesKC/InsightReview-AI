from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_OCR_ENGINE = None
_OCR_ENGINE_INIT_FAILED = False


def _build_ocr_engine():
    from paddleocr import PaddleOCR

    settings = get_settings()
    return PaddleOCR(
        use_angle_cls=True,
        lang=settings.chat_ocr_lang,
        use_gpu=settings.chat_ocr_gpu_enabled,
    )


def _get_ocr_engine():
    global _OCR_ENGINE, _OCR_ENGINE_INIT_FAILED
    if _OCR_ENGINE is not None:
        return _OCR_ENGINE
    if _OCR_ENGINE_INIT_FAILED:
        return None

    try:
        _OCR_ENGINE = _build_ocr_engine()
    except Exception:
        _OCR_ENGINE_INIT_FAILED = True
        logger.exception("Failed to initialize PaddleOCR engine")
        return None
    return _OCR_ENGINE


async def extract_text_from_image(image_path: str | Path) -> str:
    settings = get_settings()
    if not settings.chat_ocr_enabled:
        return ""

    engine = _get_ocr_engine()
    if engine is None:
        return ""

    try:
        result = await asyncio.to_thread(engine.ocr, str(Path(image_path)), cls=True)
    except Exception:
        logger.exception("PaddleOCR failed for image path: %s", image_path)
        return ""

    lines: list[str] = []
    for page in result or []:
        if not page:
            continue
        for row in page:
            if not isinstance(row, (list, tuple)) or len(row) < 2:
                continue
            text_meta = row[1]
            if not isinstance(text_meta, (list, tuple)) or not text_meta:
                continue
            text = str(text_meta[0]).strip()
            if text:
                lines.append(text)

    return "\n".join(lines).strip()

