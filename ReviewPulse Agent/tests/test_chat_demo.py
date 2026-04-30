from app.rag.prompts import format_history_for_prompt, format_retrieval_context
from app.rag.vector_store import distance_to_score


def test_distance_to_score_returns_frontend_friendly_value() -> None:
    assert distance_to_score(None) is None
    assert distance_to_score(0) == 1.0
    assert distance_to_score(1) == 0.5
    assert distance_to_score(3) == 0.25


def test_prompt_formatters_keep_turns_and_sources_readable() -> None:
    history_text = format_history_for_prompt(
        [
            {"turn_no": 1, "query": "这个文档是什么？", "answer": "是用户手册。"},
            {"turn_no": 2, "query": "发布时间呢？", "answer": "2024-01-01"},
        ]
    )
    retrieval_text = format_retrieval_context(
        [
            {
                "source": "用户手册.pdf",
                "score": 0.9123,
                "content": "该文档发布时间为 2024-01-01。",
            }
        ]
    )

    assert "第1轮用户：这个文档是什么？" in history_text
    assert "第2轮助手：2024-01-01" in history_text
    assert "来源：用户手册.pdf" in retrieval_text
    assert "score=0.9123" in retrieval_text

