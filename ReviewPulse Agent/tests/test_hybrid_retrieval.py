from app.rag.vector_store import (
    _compute_bm25_scores,
    _compute_rrf_scores,
    _normalize_weights,
    _tokenize_for_bm25,
)


def test_normalize_weights_handles_negative_and_zero() -> None:
    assert _normalize_weights(0, 0) == (0.5, 0.5)
    assert _normalize_weights(-1, 1) == (0.0, 1.0)


def test_tokenizer_uses_jieba_for_chinese_terms() -> None:
    tokens = _tokenize_for_bm25("会员等级权益说明 v2 有哪些")
    assert any(token in tokens for token in ("会员", "等级", "权益", "说明"))
    assert "v2" in tokens
    assert "有" not in tokens


def test_bm25_scores_rank_term_overlap_higher() -> None:
    docs = [
        "川香居 菜单 包含 水煮鱼 和 宫保鸡丁",
        "会员 充值 规则 与 积分 说明",
    ]
    scores = _compute_bm25_scores("宫保鸡丁 菜单", docs)
    assert len(scores) == 2
    assert scores[0] > scores[1]


def test_bm25_uses_source_and_synonyms_for_menu_intent() -> None:
    docs = [
        "本文件介绍品牌环境与服务流程",
        "今日推荐包含水煮鱼、毛血旺、回锅肉",
    ]
    sources = ["川香居环境描述.md", "川香居菜单.csv"]
    scores = _compute_bm25_scores("川香居的菜品有哪些", docs, sources=sources)
    assert len(scores) == 2
    assert scores[1] > scores[0]


def test_rrf_scores_respect_rank_fusion() -> None:
    fused = _compute_rrf_scores(
        vector_scores=[0.95, 0.80, 0.50],
        bm25_scores=[0.10, 0.90, 0.30],
        vector_weight=0.7,
        bm25_weight=0.3,
        rrf_k=60,
    )
    assert len(fused) == 3
    assert fused[0] >= fused[2]


