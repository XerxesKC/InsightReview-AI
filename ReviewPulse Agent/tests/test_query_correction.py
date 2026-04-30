from __future__ import annotations

import asyncio
import pytest

from app.rag import llm
from app.rag.query_correction import correct_query_typos


def test_correct_query_typos_returns_original_when_library_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.rag.query_correction._PYCORRECTOR_CALLABLE", False)
    assert correct_query_typos("葡淘酒多少钱") == "葡淘酒多少钱"


def test_correct_query_typos_uses_pycorrector_style_return(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.rag.query_correction._PYCORRECTOR_CALLABLE",
        lambda text: (text.replace("葡淘", "葡萄"), [(1, "淘", "萄")]),
    )
    assert correct_query_typos("葡淘酒多少钱") == "葡萄酒多少钱"


def test_rewrite_question_applies_typo_correction_after_rewrite(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_invoke_chat(*args, **kwargs) -> str:  # noqa: ARG001
        return "葡淘酒有哪些"

    monkeypatch.setattr(llm, "invoke_chat", fake_invoke_chat)
    monkeypatch.setattr(llm, "correct_query_typos", lambda text: text.replace("葡淘", "葡萄"))

    rewritten = asyncio.run(
        llm.rewrite_question(
            "这个店有哪些葡淘酒",
            history_turns=[{"turn_no": 1, "query": "你们卖什么", "answer": "我们卖酒"}],
            model_name="qwen-turbo",
        )
    )

    assert rewritten == "葡萄酒有哪些"
