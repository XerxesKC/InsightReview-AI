from __future__ import annotations

from pathlib import Path

from app.agents.chat.graph import ChatGraphCallbacks, build_chat_graph
from app.agents.chat.state import ChatGraphState


class LangGraphChatOrchestrator:
    """Thin wrapper around the compiled chat graph."""

    def __init__(self, callbacks: ChatGraphCallbacks) -> None:
        self._app = build_chat_graph(callbacks)

    async def run(self, state: ChatGraphState) -> ChatGraphState:
        result = await self._app.ainvoke(state)
        return result

    def export_mermaid(self) -> str:
        return self._app.get_graph().draw_mermaid()

    def export_mermaid_to_file(self, file_path: str | Path) -> None:
        target = Path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.export_mermaid(), encoding="utf-8")


class NoopLangGraphChatOrchestrator:
    """Fallback orchestrator used when graph dependencies are unavailable."""

    async def run(self, state: ChatGraphState) -> ChatGraphState:
        return state

    def export_mermaid(self) -> str:
        return "graph TD\n    Start([fallback]) --> End([fallback])\n"

    def export_mermaid_to_file(self, file_path: str | Path) -> None:
        Path(file_path).write_text(self.export_mermaid(), encoding="utf-8")


def create_orchestrator(callbacks: ChatGraphCallbacks) -> LangGraphChatOrchestrator | NoopLangGraphChatOrchestrator:
    """Build a LangGraph orchestrator; fallback to no-op if import/runtime fails."""

    try:
        return LangGraphChatOrchestrator(callbacks)
    except Exception:
        return NoopLangGraphChatOrchestrator()


