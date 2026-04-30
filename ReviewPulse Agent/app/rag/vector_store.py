from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
from typing import Any
from uuid import uuid4

import chromadb
import jieba
from rank_bm25 import BM25Okapi

from app.core.config import get_settings
from app.rag.embeddings import get_embeddings

_BM25_STOPWORDS = {
    "的", "了", "和", "与", "及", "在", "是", "有", "有哪些", "什么", "怎么", "如何", "吗", "呢",
    "请问", "一下", "一个", "可以", "是否", "这个", "那个", "以及", "并", "或", "等",
}

_BM25_QUERY_EXPANSIONS = {
    "菜品": ["菜单", "招牌菜", "推荐菜"],
    "菜单": ["菜品", "招牌菜", "推荐菜"],
}


def _safe_chunk_index(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


class LocalChromaStore:
    def __init__(
        self,
        *,
        collection_name: str,
        persist_directory: str,
        embedding_device: str = "auto",
        model_path: str | None = None,
    ) -> None:
        settings = get_settings()
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        if not Path(persist_directory).exists():
            raise ValueError(f"Persist directory {persist_directory} does not exist")
            
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embeddings = get_embeddings(model_path or settings.bge_model_path, embedding_device)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_documents(self, documents: list[dict[str, Any]]) -> int:
        if not documents:
            return 0

        texts = [str(item.get("content", "")) for item in documents]
        metadatas = [
            {
                "source": str(item.get("source", "")),
                "chunk_index": int(item.get("chunk_index", index)),
            }
            for index, item in enumerate(documents)
        ]
        ids = [str(item.get("id") or uuid4()) for item in documents]
        embeddings = self.embeddings.embed_documents(texts)
        self.collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        return len(documents)

    def add_document_chunks_to_knowledge_base(
            self,
            chunks: list[str],
            document_id: int,
            uploader_type: str,
            uploader_id: int,
            document_name: str,
            source_type: str = "document",
            source_location: str = "",
            precomputed_embeddings: list[list[float]] = None
    ) -> int:
        """
        将文档切分块存入对应的知识库向量库

        参数:
            chunks: 文本块列表
            document_id: 文档ID
            kb_id: 知识库ID
            document_name: 文档名称
            source_type: 源类型
            source_location: 源位置
            precomputed_embeddings: 预计算的向量（可选）

        返回:
            入库的向量数量
        """
        if not chunks:
            return 0

        kb_collection_name = f"{uploader_type}_{uploader_id}"
        kb_collection = self.client.get_or_create_collection(name=kb_collection_name)

        texts = [str(chunk) for chunk in chunks]
        metadatas = [
            {
                "source": document_name,
                "chunk_index": index,
                "chunk_id": f"doc_{document_id}_chunk_{index}",
                "kb_name": str(kb_collection_name),
                "document_id": str(document_id),
                "source_type": source_type,
                "source_location": source_location,
            }
            for index, chunk in enumerate(chunks)
        ]
        ids = [f"doc_{document_id}_chunk_{index}" for index in range(len(chunks))]

        if precomputed_embeddings and len(precomputed_embeddings) == len(chunks):
            embeddings = precomputed_embeddings
        else:
            embeddings = self.embeddings.embed_documents(texts)

        kb_collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )

        return len(chunks)

    def similarity_search(self, query: str, k: int = 4) -> list[dict[str, Any]]:
        query_embedding = self.embeddings.embed_query(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
        )
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0] if results.get("distances") else []
        items = []
        for index, document in enumerate(documents):
            metadata = metadatas[index] if index < len(metadatas) else {}
            distance = distances[index] if index < len(distances) else None
            items.append(
                {
                    "id": ids[index] if index < len(ids) else None,
                    "content": document,
                    "metadata": metadata,
                    "source": str(metadata.get("source", "")),
                    "chunk_index": int(metadata.get("chunk_index", index)),
                    "distance": distance,
                    "score": distance_to_score(distance),
                }
            )
        return items

    def hybrid_search(
        self,
        query: str,
        *,
        k: int = 4,
        vector_weight: float = 0.7,
        bm25_weight: float = 0.3,
        candidate_k: int = 200,
        rrf_k: int = 60,
    ) -> list[dict[str, Any]]:
        """Run vector and BM25 retrieval in parallel and fuse with weighted RRF."""

        safe_k = max(int(k), 1)
        safe_candidate_k = max(int(candidate_k), safe_k)

        with ThreadPoolExecutor(max_workers=2) as pool:
            vector_future = pool.submit(self.vector_search_candidates, query, safe_candidate_k)
            bm25_future = pool.submit(self.bm25_search_candidates, query, safe_candidate_k)
            vector_items = vector_future.result()
            bm25_items = bm25_future.result()

        if not vector_items and not bm25_items:
            return []

        merged_map: dict[str, dict[str, Any]] = {}

        def _item_key(item: dict[str, Any]) -> str:
            item_id = item.get("id")
            if item_id:
                return f"id:{item_id}"
            source = str(item.get("source") or "")
            chunk_index = item.get("chunk_index")
            return f"source:{source}|chunk:{chunk_index}"

        for row in vector_items:
            key = _item_key(row)
            merged = dict(row)
            merged.setdefault("bm25_score", 0.0)
            merged_map[key] = merged

        for row in bm25_items:
            key = _item_key(row)
            if key not in merged_map:
                merged = dict(row)
                merged.setdefault("vector_score", 0.0)
                merged_map[key] = merged
                continue

            current = merged_map[key]
            current["bm25_score"] = max(float(current.get("bm25_score") or 0.0), float(row.get("bm25_score") or 0.0))
            if not current.get("content") and row.get("content"):
                current["content"] = row.get("content")
            if not current.get("metadata") and row.get("metadata"):
                current["metadata"] = row.get("metadata")
            if not current.get("source") and row.get("source"):
                current["source"] = row.get("source")

        merged_items = list(merged_map.values())
        vector_scores = [float(item.get("vector_score") or 0.0) for item in merged_items]
        bm25_scores = [float(item.get("bm25_score") or 0.0) for item in merged_items]
        w_vector, w_bm25 = _normalize_weights(vector_weight, bm25_weight)
        rrf_scores = _compute_rrf_scores(
            vector_scores=vector_scores,
            bm25_scores=bm25_scores,
            vector_weight=w_vector,
            bm25_weight=w_bm25,
            rrf_k=max(int(rrf_k), 1),
        )

        items: list[dict[str, Any]] = []
        for index, row in enumerate(merged_items):
            metadata = row.get("metadata") or {}
            distance = row.get("distance")
            vector_score = float(vector_scores[index]) if index < len(vector_scores) else 0.0
            bm25_score = float(bm25_scores[index]) if index < len(bm25_scores) else 0.0
            hybrid_score = round(float(rrf_scores[index]) if index < len(rrf_scores) else 0.0, 6)
            items.append(
                {
                    "id": row.get("id"),
                    "content": row.get("content", ""),
                    "metadata": metadata,
                    "source": str(row.get("source") or metadata.get("source", "")),
                    "chunk_index": _safe_chunk_index(row.get("chunk_index", metadata.get("chunk_index", index)), index),
                    "distance": distance,
                    "vector_score": round(vector_score, 6),
                    "bm25_score": round(bm25_score, 6),
                    "hybrid_score": hybrid_score,
                    "score": hybrid_score,
                }
            )

        items.sort(key=lambda item: float(item.get("score") or 0), reverse=True)
        return items[:safe_k]

    def vector_search_candidates(self, query: str, k: int) -> list[dict[str, Any]]:
        safe_k = max(int(k), 1)
        query_embedding = self.embeddings.embed_query(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=safe_k,
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0] if results.get("distances") else []
        items: list[dict[str, Any]] = []
        for index, document in enumerate(documents):
            metadata = metadatas[index] if index < len(metadatas) else {}
            distance = distances[index] if index < len(distances) else None
            vector_score = float(distance_to_score(distance) or 0.0)
            items.append(
                {
                    "id": ids[index] if index < len(ids) else None,
                    "content": document,
                    "metadata": metadata,
                    "source": str(metadata.get("source", "")),
                    "chunk_index": _safe_chunk_index(metadata.get("chunk_index", index), index),
                    "distance": distance,
                    "vector_score": round(vector_score, 6),
                    "bm25_score": 0.0,
                    "score": round(vector_score, 6),
                }
            )
        return items

    def bm25_search_candidates(self, query: str, k: int) -> list[dict[str, Any]]:
        safe_k = max(int(k), 1)
        payload = self.collection.get(include=["documents", "metadatas"])
        documents = payload.get("documents") or []
        metadatas = payload.get("metadatas") or []
        ids = payload.get("ids") or []
        if not documents:
            return []

        sources = [str((metadatas[index] if index < len(metadatas) else {}).get("source", "")) for index in range(len(documents))]
        bm25_raw_scores = _compute_bm25_scores(query=query, documents=[str(doc) for doc in documents], sources=sources)
        bm25_scores = _normalize_scores(bm25_raw_scores)

        ranked_indexes = sorted(
            range(len(documents)),
            key=lambda idx: bm25_raw_scores[idx] if idx < len(bm25_raw_scores) else 0.0,
            reverse=True,
        )[:safe_k]
        items: list[dict[str, Any]] = []
        for rank_index in ranked_indexes:
            metadata = metadatas[rank_index] if rank_index < len(metadatas) else {}
            bm25_score = float(bm25_scores[rank_index]) if rank_index < len(bm25_scores) else 0.0
            items.append(
                {
                    "id": ids[rank_index] if rank_index < len(ids) else None,
                    "content": documents[rank_index],
                    "metadata": metadata,
                    "source": str(metadata.get("source", "")),
                    "chunk_index": _safe_chunk_index(metadata.get("chunk_index", rank_index), rank_index),
                    "distance": None,
                    "vector_score": 0.0,
                    "bm25_score": round(bm25_score, 6),
                    "score": round(bm25_score, 6),
                }
            )
        return items

    def delete_collection(self) -> None:
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

    def delete_document_chunks(self, document_id: int, uploader_type: str, uploader_id: int) -> int:
        """
        删除指定文档的所有文本块
        参数:
            document_id: 文档ID
            uploader_type: 上传者类型
            uploader_id: 上传者ID
        返回:
            删除的文本块数量
        """
        kb_collection_name = f"{uploader_type}_{uploader_id}"
        kb_collection = self.client.get_or_create_collection(name=kb_collection_name)
        id_prefix = f"doc_{document_id}_chunk_"
        results = kb_collection.get(
            where={"document_id": str(document_id)}
        )
        ids_to_delete = results.get("ids", [])
        if ids_to_delete:
            kb_collection.delete(ids=ids_to_delete)
            return len(ids_to_delete)
        return 0

def get_vector_store(
    collection_name: str,
    persist_directory: str,
    *,
    embedding_device: str = "auto",
    model_path: str | None = None,
) -> LocalChromaStore:
    Path(persist_directory).mkdir(parents=True, exist_ok=True)
    return LocalChromaStore(
        collection_name=collection_name,
        persist_directory=persist_directory,
        embedding_device=embedding_device,
        model_path=model_path,
    )


def distance_to_score(distance: float | None) -> float | None:
    if distance is None:
        return None
    if distance < 0:
        return 0.0
    return round(1 / (1 + float(distance)), 4)


def _normalize_weights(vector_weight: float, bm25_weight: float) -> tuple[float, float]:
    safe_vector = max(float(vector_weight), 0.0)
    safe_bm25 = max(float(bm25_weight), 0.0)
    total = safe_vector + safe_bm25
    if total <= 0:
        return 0.5, 0.5
    return safe_vector / total, safe_bm25 / total


def _normalize_scores(scores: list[float]) -> list[float]:
    if not scores:
        return []
    minimum = min(scores)
    maximum = max(scores)
    if maximum <= minimum:
        if maximum <= 0:
            return [0.0 for _ in scores]
        return [1.0 for _ in scores]
    return [(score - minimum) / (maximum - minimum) for score in scores]


def _sorted_rank_map(scores: list[float]) -> dict[int, int]:
    ordered = sorted(range(len(scores)), key=lambda idx: scores[idx], reverse=True)
    return {doc_index: rank + 1 for rank, doc_index in enumerate(ordered)}


def _compute_rrf_scores(
    *,
    vector_scores: list[float],
    bm25_scores: list[float],
    vector_weight: float,
    bm25_weight: float,
    rrf_k: int,
) -> list[float]:
    size = max(len(vector_scores), len(bm25_scores))
    if size == 0:
        return []

    vector_rank_map = _sorted_rank_map(vector_scores)
    bm25_rank_map = _sorted_rank_map(bm25_scores)
    fused: list[float] = []
    for idx in range(size):
        vector_rank = vector_rank_map.get(idx)
        bm25_rank = bm25_rank_map.get(idx)
        score = 0.0
        if vector_rank is not None:
            score += vector_weight / (rrf_k + vector_rank)
        if bm25_rank is not None:
            score += bm25_weight / (rrf_k + bm25_rank)
        fused.append(score)
    return _normalize_scores(fused)


def _tokenize_for_bm25(text: str) -> list[str]:
    normalized = (text or "").lower()
    chunks = [part.strip() for part in jieba.lcut(normalized, cut_all=False) if part and part.strip()]
    tokens: list[str] = []
    for chunk in chunks:
        if re.fullmatch(r"[a-z0-9]+", chunk):
            tokens.append(chunk)
            continue
        if re.search(r"[\u4e00-\u9fff]", chunk):
            tokens.append(chunk)
            continue
        tokens.extend(re.findall(r"[a-z0-9]+", chunk))
    return [token for token in tokens if token and token not in _BM25_STOPWORDS]


def _compute_bm25_scores(
    query: str,
    documents: list[str],
    *,
    sources: list[str] | None = None,
    k1: float = 1.5,
    b: float = 0.75,
) -> list[float]:
    source_list = sources or []
    corpus_for_bm25 = [
        f"{str(source_list[idx] if idx < len(source_list) else '').strip()} {str(source_list[idx] if idx < len(source_list) else '').strip()} {str(doc)}".strip()
        for idx, doc in enumerate(documents)
    ]
    tokenized_docs = [_tokenize_for_bm25(doc) for doc in corpus_for_bm25]
    if not tokenized_docs:
        return []
    if not any(tokenized_docs):
        return [0.0 for _ in documents]

    query_tokens = _tokenize_for_bm25(query)
    expanded_query_tokens = list(query_tokens)
    for token in query_tokens:
        expanded_query_tokens.extend(_BM25_QUERY_EXPANSIONS.get(token, []))
    expanded_query_tokens = [token for token in expanded_query_tokens if token]
    if not expanded_query_tokens:
        return [0.0 for _ in documents]

    model = BM25Okapi(tokenized_docs, k1=k1, b=b)
    raw_scores = model.get_scores(expanded_query_tokens)
    scores = [float(item) for item in raw_scores]
    if any(score > 0 for score in scores):
        return scores

    query_terms = set(expanded_query_tokens)
    if not query_terms:
        return scores
    fallback_scores: list[float] = []
    for doc_tokens in tokenized_docs:
        if not doc_tokens:
            fallback_scores.append(0.0)
            continue
        overlap = len(query_terms.intersection(doc_tokens))
        fallback_scores.append(overlap / len(query_terms))
    return fallback_scores


