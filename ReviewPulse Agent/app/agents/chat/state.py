from __future__ import annotations

from typing import Any, TypedDict


class ChatGraphState(TypedDict, total=False):
    """Mutable state shared across LangGraph chat nodes."""

    stream: bool
    has_messages: bool
    session_id: str
    user: dict[str, str]
    payload_model: str | None

    user_text: str
    last_message: str
    input_type: str
    ocr_text: str | None
    image_id: str | None
    image_url: str | None
    rewritten_query: str | None
    history_items: list[dict[str, Any]]

    intent: str
    direct_response: str | None
    sources: list[dict[str, Any]]
    answer: str
    timeout_stage: str | None
    tool_needs_explain: bool
    tool_chat_messages: list[tuple[str, str]]
    tool_error: str | None
    trace: list[str]

    latency_ms: dict[str, int]
    called_models: dict[str, Any]

    is_complex_task: bool
    plan: list[str]
    past_steps: list[tuple[str, str]]
    loop_count: int

    file_ids: list[str]
