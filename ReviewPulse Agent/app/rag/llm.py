from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
import os
from typing import Any

from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.config import get_settings
from app.rag.prompts import (
    SYSTEM_MESSAGE,
    build_chat_prompt,
    build_question_rewrite_prompt,
    format_history_for_prompt,
    format_retrieval_context,
)
from app.rag.query_correction import correct_query_typos


def get_llm(model_name: str | None = None, temperature: float | None = None) -> ChatOpenAI:
    settings = get_settings()
    api_key = os.environ.get("API_KEY") or settings.api_key
    if not api_key:
        raise RuntimeError("系统环境变量 API_KEY 未配置，无法调用大模型。")

    return ChatOpenAI(
        api_key=SecretStr(api_key),
        base_url=settings.llm_base_url,
        model=model_name or settings.llm_generation_model_name or settings.llm_model_name,
        temperature=settings.llm_temperature if temperature is None else temperature,
        max_tokens=settings.llm_max_tokens,
    )


async def invoke_chat(
    messages: Sequence[tuple[str, str]],
    *,
    model_name: str | None = None,
    temperature: float | None = None,
) -> str:
    llm = get_llm(model_name=model_name, temperature=temperature)
    response = await llm.ainvoke(list(messages))
    return _stringify_content(getattr(response, "content", response))

async def invoke_chat_stream(
    messages: Sequence[tuple[str, str]],
    *,
    model_name: str | None = None,
    temperature: float | None = None,
) -> AsyncIterator[str]:
    llm = get_llm(model_name=model_name, temperature=temperature)
    async for chunk in llm.astream(list(messages)):
        text = _stringify_content(getattr(chunk, "content", chunk))
        if text:
            yield text


async def rewrite_question(
    question: str,
    history_turns: Sequence[dict[str, Any]],
    *,
    model_name: str | None = None,
) -> str:
    """把追问改写成独立问题，并在检索前执行错别字纠正。"""

    if not history_turns:
        return correct_query_typos(question)

    history_text = format_history_for_prompt(history_turns)
    prompt = build_question_rewrite_prompt(history=history_text, question=question)
    settings = get_settings()
    rewritten = await invoke_chat(
        [("system", SYSTEM_MESSAGE), ("user", prompt)],
        model_name=model_name or settings.llm_rewrite_model_name,
        temperature=0,
    )
    normalized = rewritten.strip() or question
    return correct_query_typos(normalized)


async def answer_with_context(
    *,
    question: str,
    history_turns: Sequence[dict[str, Any]],
    retrieved_items: Sequence[dict[str, Any]],
    model_name: str | None = None,
    temperature: float | None = None,
    answer_max_chars: int | None = None,
) -> str:
    """把历史上下文和检索结果一起注入给大模型，生成最终回答。"""

    prompt = build_chat_prompt(
        history=format_history_for_prompt(history_turns),
        context=format_retrieval_context(retrieved_items),
        question=question,
        answer_max_chars=answer_max_chars,
    )
    return await invoke_chat(
        [("system", SYSTEM_MESSAGE), ("user", prompt)],
        model_name=model_name,
        temperature=temperature,
    )


async def answer_with_context_stream(
    *,
    question: str,
    history_turns: Sequence[dict[str, Any]],
    retrieved_items: Sequence[dict[str, Any]],
    model_name: str | None = None,
    temperature: float | None = None,
    answer_max_chars: int | None = None,
) -> AsyncIterator[str]:
    """Stream model output chunks for chat responses."""

    prompt = build_chat_prompt(
        history=format_history_for_prompt(history_turns),
        context=format_retrieval_context(retrieved_items),
        question=question,
        answer_max_chars=answer_max_chars,
    )
    llm = get_llm(model_name=model_name, temperature=temperature)
    async for chunk in llm.astream([("system", SYSTEM_MESSAGE), ("user", prompt)]):
        text = _stringify_content(getattr(chunk, "content", chunk))
        if text:
            yield text


def _stringify_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text") or item.get("content") or str(item)
                parts.append(str(text))
            else:
                parts.append(str(item))
        return "".join(parts).strip()
    return str(content)
