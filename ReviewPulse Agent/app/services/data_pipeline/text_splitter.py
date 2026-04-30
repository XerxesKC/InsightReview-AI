"""
独立的文本切分模块 - 支持递归切分和语义切分
"""

from __future__ import annotations

import re
import logging
from typing import List, Dict, Any, Optional
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    import sklearn.metrics.pairwise
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    logger.warning("sentence-transformers 未安装，语义切分不可用")


class TextSplitter:
    def __init__(
            self,
            chunk_size: int = 500,
            chunk_overlap: int = 50,
            splitter_type: str = "recursive",
            separators: Optional[List[str]] = None,
            model_name: str = "data/bge-model/BAAI/bge-base-zh-v1.5",
            similarity_threshold: float = 0.7
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter_type = splitter_type.lower()
        self.separators = separators or ["\n\n", "\n", "。", "；", "，", " ", ""]
        self.model_name = model_name
        self.similarity_threshold = similarity_threshold
        self.max_chunk_size = chunk_size * 2
        self.min_chunk_size = max(50, chunk_size // 2)
        self.stats = {}
        self.model = None

        if self.splitter_type == "semantic":
            self._init_model()

    def _init_model(self):
        if not SEMANTIC_AVAILABLE:
            raise ImportError("请安装: pip install sentence-transformers scikit-learn")

        import os
        from pathlib import Path

        model_path = str(Path(__file__).parent.parent.parent.parent / self.model_name)
        if os.path.exists(model_path):
            self.model = SentenceTransformer(model_path)
            logger.info(f"本地模型加载成功")
        else:
            self.model = SentenceTransformer("BAAI/bge-base-zh-v1.5")
            logger.info(f"在线模型加载成功")

    def split_text(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []

        chunks = self._semantic_split(text) if self.splitter_type == "semantic" else self._recursive_split(text)
        self._update_stats(text, chunks)
        return chunks

    def _recursive_split(self, text: str) -> List[str]:
        chunks, start = [], 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.chunk_size, text_len)

            if end < text_len:
                for sep in self.separators:
                    if not sep:
                        continue
                    pos = text.rfind(sep, start, end)
                    if pos > start:
                        end = pos
                        break

            if text[start:end].strip():
                chunks.append(text[start:end].strip())

            start = end - self.chunk_overlap if end < text_len else text_len

        return chunks

    def _split_sentences(self, text: str) -> List[str]:
        parts = re.split(r'([。！？!?]+)', text)
        sentences = []

        for i in range(0, len(parts), 2):
            if i + 1 < len(parts):
                sent = parts[i] + parts[i+1]
            else:
                sent = parts[i]
            if sent.strip():
                sentences.append(sent.strip())

        return sentences if len(sentences) > 1 else [text]

    def _semantic_split(self, text: str) -> List[str]:
        if not self.model:
            return self._recursive_split(text)

        sentences = self._split_sentences(text)
        if len(sentences) <= 1:
            return [text]

        embeddings = self.model.encode(sentences, show_progress_bar=False)
        similarities = [sklearn.metrics.pairwise.cosine_similarity([embeddings[i]], [embeddings[i+1]])[0][0]
                       for i in range(len(embeddings)-1)]

        chunks, current, length = [], [sentences[0]], len(sentences[0])

        for i in range(1, len(sentences)):
            if similarities[i-1] < self.similarity_threshold or length + len(sentences[i]) > self.max_chunk_size:
                chunks.append("".join(current))
                current, length = [sentences[i]], len(sentences[i])
            else:
                current.append(sentences[i])
                length += len(sentences[i])

        if current:
            chunks.append("".join(current))

        return chunks

    def _update_stats(self, text: str, chunks: List[str]):
        if not chunks:
            self.stats = {"num_chunks": 0, "avg_size": 0}
            return

        sizes = [len(c) for c in chunks]
        self.stats = {
            "num_chunks": len(chunks),
            "avg_size": sum(sizes) / len(sizes),
            "min_size": min(sizes),
            "max_size": max(sizes)
        }


def split_dataframe_text(df, text_column: str = "natural_language_description", **kwargs):
    try:
        import pandas as pd
    except ImportError:
        return df

    if df.empty:
        return df

    splitter = TextSplitter(**kwargs)
    rows = []

    for _, row in df.iterrows():
        text = str(row.get(text_column, ""))
        if not text.strip():
            rows.append({**row.to_dict(), "chunk_text": text, "chunk_index": 0, "chunk_count": 1})
            continue

        chunks = splitter.split_text(text)
        for i, chunk in enumerate(chunks):
            rows.append({**row.to_dict(), "chunk_text": chunk, "chunk_index": i, "chunk_count": len(chunks)})

    return pd.DataFrame(rows)


if __name__ == "__main__":
    sample = "这是第一句。这是第二句。这是第三句。"
    splitter = TextSplitter(chunk_size=10, splitter_type="recursive")
    print(splitter.split_text(sample))