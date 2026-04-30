from __future__ import annotations

import asyncio
import pytest

pytest.importorskip("langgraph")

from app.agents.chat.graph import ChatGraphCallbacks
from app.agents.chat.orchestrator import create_orchestrator
from app.agents.chat.state import ChatGraphState


def test_langgraph_routes_knowledge_query_path() -> None:
    async def input_process(state: dict) -> dict:
        return {"trace": ["input_process"]}

    async def guardrails(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "guardrails"]}

    async def history(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "history"]}

    async def rewrite(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "rewrite"], "rewritten_query": "q"}

    async def router(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "router"], "intent": "knowledge_query"}

    async def retrieve(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "retrieve"]}

    async def rerank(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "rerank"]}

    async def rag_gen(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "rag_gen"], "answer": "ok"}

    async def chat_gen(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "chat_gen"]}

    async def direct_rep(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "direct_rep"]}

    async def tool_agent(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "tool_agent"]}

    async def tool_output(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "tool_output"], "tool_needs_explain": False}

    async def audit(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "audit"]}

    async def planner(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "planner"]}

    async def executor(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "executor"]}

    async def synthesizer(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "synthesizer"]}

    orchestrator = create_orchestrator(
        ChatGraphCallbacks(
            input_process=input_process,
            guardrails=guardrails,
            history=history,
            rewrite=rewrite,
            router=router,
            retrieve=retrieve,
            rerank=rerank,
            rag_gen=rag_gen,
            chat_gen=chat_gen,
            direct_rep=direct_rep,
            tool_agent=tool_agent,
            tool_output=tool_output,
            audit=audit,
            planner=planner,
            executor=executor,
            synthesizer=synthesizer,
        )
    )

    result = dict(asyncio.run(orchestrator.run(ChatGraphState())))
    assert result["trace"] == [
        "input_process",
        "guardrails",
        "history",
        "rewrite",
        "router",
        "retrieve",
        "rerank",
        "rag_gen",
        "audit",
    ]


def test_langgraph_mermaid_export_contains_router() -> None:
    async def noop(state: dict) -> dict:
        return {}

    orchestrator = create_orchestrator(
        ChatGraphCallbacks(
            input_process=noop,
            guardrails=noop,
            history=noop,
            rewrite=noop,
            router=noop,
            retrieve=noop,
            rerank=noop,
            rag_gen=noop,
            chat_gen=noop,
            direct_rep=noop,
            tool_agent=noop,
            tool_output=noop,
            audit=noop,
            planner=noop,
            executor=noop,
            synthesizer=noop,
        )
    )

    mermaid = orchestrator.export_mermaid()
    assert "router" in mermaid
    assert "tool_agent" in mermaid


def test_langgraph_routes_tool_use_to_end_when_no_explain() -> None:
    async def input_process(state: dict) -> dict:
        return {"trace": ["input_process"]}

    async def guardrails(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "guardrails"]}

    async def history(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "history"]}

    async def rewrite(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "rewrite"], "rewritten_query": "q"}

    async def router(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "router"], "intent": "tool_use"}

    async def retrieve(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "retrieve"]}

    async def rerank(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "rerank"]}

    async def rag_gen(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "rag_gen"]}

    async def chat_gen(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "chat_gen"]}

    async def direct_rep(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "direct_rep"]}

    async def tool_agent(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "tool_agent"]}

    async def tool_output(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "tool_output"], "tool_needs_explain": False}

    async def audit(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "audit"]}

    async def planner(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "planner"]}

    async def executor(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "executor"]}

    async def synthesizer(state: dict) -> dict:
        return {"trace": [*state.get("trace", []), "synthesizer"]}

    orchestrator = create_orchestrator(
        ChatGraphCallbacks(
            input_process=input_process,
            guardrails=guardrails,
            history=history,
            rewrite=rewrite,
            router=router,
            retrieve=retrieve,
            rerank=rerank,
            rag_gen=rag_gen,
            chat_gen=chat_gen,
            direct_rep=direct_rep,
            tool_agent=tool_agent,
            tool_output=tool_output,
            audit=audit,
            planner=planner,
            executor=executor,
            synthesizer=synthesizer,
        )
    )

    result = dict(asyncio.run(orchestrator.run(ChatGraphState())))
    assert result["trace"] == [
        "input_process",
        "guardrails",
        "history",
        "rewrite",
        "router",
        "tool_agent",
        "tool_output",
    ]



