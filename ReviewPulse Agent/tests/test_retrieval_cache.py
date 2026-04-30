from __future__ import annotations

import asyncio

from app.core import retrieval_cache


def test_build_vector_cache_key_is_stable_for_same_payload() -> None:
    payload = {
        "query": "川香居的菜品有哪些？",
        "top_k": 4,
        "threshold": 0.25,
    }
    key1 = retrieval_cache.build_vector_cache_key(payload=payload)
    key2 = retrieval_cache.build_vector_cache_key(payload=dict(payload))
    assert key1 == key2


def test_memory_vector_cache_set_get_and_expire() -> None:
    retrieval_cache._memory_cache.clear()
    key = retrieval_cache.build_vector_cache_key(payload={"query": "test", "top_k": 2})
    items = [{"source": "doc.txt", "score": 0.88, "content": "hello"}]

    asyncio.run(
        retrieval_cache.set_vector_cache_items(
            key=key,
            items=items,
            ttl_seconds=1,
            backend="memory",
        )
    )
    loaded = asyncio.run(retrieval_cache.get_vector_cache_items(key=key, backend="memory"))
    assert loaded == items

    asyncio.run(asyncio.sleep(1.1))
    expired = asyncio.run(retrieval_cache.get_vector_cache_items(key=key, backend="memory"))
    assert expired is None

