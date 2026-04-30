from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.agents.chat.state import ChatGraphState

NodeFn = Callable[[ChatGraphState], Awaitable[dict[str, Any]]]


class ChatGraphCallbacks:
    """Typed callback container used to wire app-specific node logic into the graph."""

    def __init__(
        self,
        *,
        input_process: NodeFn,
        guardrails: NodeFn,
        history: NodeFn,
        rewrite: NodeFn,
        router: NodeFn,
        retrieve: NodeFn,
        rerank: NodeFn,
        rag_gen: NodeFn,
        chat_gen: NodeFn,
        direct_rep: NodeFn,
        tool_agent: NodeFn,
        tool_output: NodeFn,
        audit: NodeFn,
        planner: NodeFn,
        executor: NodeFn,
        synthesizer: NodeFn,
    ) -> None:
        self.input_process = input_process
        self.guardrails = guardrails
        self.history = history
        self.rewrite = rewrite
        self.router = router
        self.retrieve = retrieve
        self.rerank = rerank
        self.rag_gen = rag_gen
        self.chat_gen = chat_gen
        self.direct_rep = direct_rep
        self.tool_agent = tool_agent
        self.tool_output = tool_output
        self.audit = audit
        self.planner = planner
        self.executor = executor
        self.synthesizer = synthesizer


def _route_by_intent(state: ChatGraphState) -> str:
    intent = (state.get("intent") or "knowledge_query").strip().lower()
    if intent in {"knowledge_query", "tool_use", "general_chat", "system_action"}:
        return intent
    return "knowledge_query"


def _route_dispatcher(state: ChatGraphState) -> str:
    if state.get("is_complex_task"):
        return "planner"
    return _route_by_intent(state)


def _route_tool_output(state: ChatGraphState) -> str:
    return "need_rag" if bool(state.get("tool_needs_explain")) else "done"


def _route_planner(state: ChatGraphState) -> str:
    plan = state.get("plan") or []
    if (plan and "[任务完成]" in plan[0]) or (state.get("loop_count") or 0) >= 10:
        return "synthesizer"
    return "executor"




def build_chat_graph(callbacks: ChatGraphCallbacks):
    """Build the chat orchestration graph with explicit branch routing."""

    from langgraph.graph import END, START, StateGraph

    graph = StateGraph(ChatGraphState)

    graph.add_node("input_process", callbacks.input_process)
    graph.add_node("guardrails", callbacks.guardrails)
    graph.add_node("history", callbacks.history)
    graph.add_node("rewrite", callbacks.rewrite)
    graph.add_node("router", callbacks.router)
    graph.add_node("retrieve", callbacks.retrieve)
    graph.add_node("rerank", callbacks.rerank)
    graph.add_node("rag_gen", callbacks.rag_gen)
    graph.add_node("chat_gen", callbacks.chat_gen)
    graph.add_node("direct_rep", callbacks.direct_rep)
    graph.add_node("tool_agent", callbacks.tool_agent)
    graph.add_node("tool_output", callbacks.tool_output)
    graph.add_node("audit", callbacks.audit)
    
    graph.add_node("planner", callbacks.planner)
    graph.add_node("executor", callbacks.executor)
    graph.add_node("synthesizer", callbacks.synthesizer)

    graph.add_edge(START, "input_process")
    graph.add_edge("input_process", "guardrails")
    graph.add_edge("guardrails", "history")
    graph.add_edge("history", "rewrite")
    graph.add_edge("rewrite", "router")

    graph.add_conditional_edges(
        "router",
        _route_dispatcher,
        {
            "knowledge_query": "retrieve",
            "tool_use": "tool_agent",
            "general_chat": "chat_gen",
            "system_action": "direct_rep",
            "planner": "planner",
        },
    )

    graph.add_edge("retrieve", "rerank")
    graph.add_edge("rerank", "rag_gen")

    graph.add_edge("tool_agent", "tool_output")
    graph.add_conditional_edges(
        "tool_output",
        _route_tool_output,
        {
            "need_rag": "rag_gen",
            "done": END,
        },
    )

    graph.add_conditional_edges(
        "planner",
        _route_planner,
        {
            "executor": "executor",
            "synthesizer": "synthesizer",
        }
    )
    graph.add_edge("executor", "planner")
    graph.add_edge("synthesizer", "audit")

    graph.add_edge("rag_gen", "audit")
    graph.add_edge("chat_gen", "audit")
    graph.add_edge("audit", END)
    graph.add_edge("direct_rep", END)

    return graph.compile()


