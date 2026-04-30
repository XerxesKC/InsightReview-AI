from __future__ import annotations


def search_web(query: str) -> dict[str, str]:
    return {
        "query": query,
        "status": "disabled",
        "message": "联网搜索工具尚未接入，当前返回占位结果。",
    }

