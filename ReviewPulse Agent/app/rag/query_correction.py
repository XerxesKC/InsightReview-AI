from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.core.config import get_settings

CorrectorCallable = Callable[[str], tuple[str, Any] | list[Any] | str]
_PYCORRECTOR_CALLABLE: CorrectorCallable | None | bool = None


def correct_query_typos(query: str) -> str:
    """Use pycorrector-like libraries to fix common typos in retrieval queries."""

    if not query:
        return query

    settings = get_settings()
    if not settings.query_spell_correction_enabled:
        return query

    corrector = _load_pycorrector_callable()
    if corrector is None:
        return query

    try:
        corrected = corrector(query)
    except Exception:
        return query

    normalized = _extract_corrected_text(corrected)
    return normalized or query


def _load_pycorrector_callable() -> CorrectorCallable | None:
    global _PYCORRECTOR_CALLABLE
    if _PYCORRECTOR_CALLABLE is False:
        return None
    if callable(_PYCORRECTOR_CALLABLE):
        return _PYCORRECTOR_CALLABLE

    try:
        import pycorrector  # type: ignore

        _PYCORRECTOR_CALLABLE = pycorrector.correct
    except Exception:
        _PYCORRECTOR_CALLABLE = False
        return None

    return _PYCORRECTOR_CALLABLE


def _extract_corrected_text(result: tuple[str, Any] | list[Any] | str) -> str:
    if isinstance(result, str):
        return result.strip()
    if isinstance(result, tuple) and result:
        return str(result[0]).strip()
    if isinstance(result, list) and result:
        return str(result[0]).strip()
    return ""

