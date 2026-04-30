from fastapi import HTTPException

from app.api.v1.chat import _rerank_merged_hybrid_items, _resolve_retrieval_owner_type, _sanitize_sources


def test_sanitize_sources_prefers_kb_name_from_db_annotation() -> None:
    items = [
        {
            "source": "顾客消费须知.txt",
            "content": "content",
            "score": 0.93,
            "distance": 0.07,
            "chunk_index": 0,
            "document_id": "17",
            "kb_name": "门店运营知识库",
            "metadata": {"kb_name": "merchant_1001", "document_id": "17"},
        }
    ]

    result = _sanitize_sources(items)

    assert result[0]["kb_name"] == "门店运营知识库"
    assert result[0]["source"] == "顾客消费须知.txt"


def test_sanitize_sources_falls_back_to_metadata_kb_name() -> None:
    items = [
        {
            "content": "content",
            "metadata": {
                "source": "会员等级与权益说明.csv",
                "kb_name": "默认知识库",
                "document_id": "18",
            },
        }
    ]

    result = _sanitize_sources(items)

    assert result[0]["kb_name"] == "默认知识库"
    assert result[0]["source"] == "会员等级与权益说明.csv"


def test_resolve_retrieval_owner_type_keeps_existing_mapping() -> None:
    assert _resolve_retrieval_owner_type("user") == "merchant"
    assert _resolve_retrieval_owner_type("merchant") == "admin"

    try:
        _resolve_retrieval_owner_type("admin")
        assert False, "admin should not be allowed"
    except HTTPException as exc:
        assert exc.status_code == 403


def test_rerank_merged_items_avoids_cross_kb_tie_bias() -> None:
    items = [
        {
            "kb_name": "不夜城KTV",
            "source": "顾客消费须知.txt",
            "vector_score": 0.4207,
            "bm25_score": 1.0,
        },
        {
            "kb_name": "川香居",
            "source": "川香居环境描述.md",
            "vector_score": 0.6133,
            "bm25_score": 0.697006,
        },
    ]

    reranked = _rerank_merged_hybrid_items(
        query="川香居的菜品有哪些？",
        items=items,
        vector_weight=0.65,
        bm25_weight=0.35,
        rrf_k=60,
    )

    assert reranked[0]["kb_name"] == "川香居"


