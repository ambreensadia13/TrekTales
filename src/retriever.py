from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from .config import (
    EMBEDDING_MODEL,
    FAISS_CONFIG_PATH,
    FAISS_DIR,
    FAISS_INDEX_PATH,
    METADATA_PATH,
    TOP_K_BM25,
    TOP_K_FAISS,
    TOP_K_FINAL,
)


class HybridRetriever:
    """Hybrid FAISS + BM25 retriever for TrekTales metadata.

    The existing metadata schema is:
        text, source, page, department, record_id

    The retriever always returns a normalized schema with:
        content, source, page, department, record_id, score, metadata
    """

    def __init__(self) -> None:
        self.faiss_dir = FAISS_DIR
        self.index_path = FAISS_INDEX_PATH
        self.metadata_path = METADATA_PATH
        self.config_path = FAISS_CONFIG_PATH
        self.index = None
        self.metadata: list[dict[str, Any]] = []
        self.config: dict[str, Any] = {}
        self.embedding_model = None
        self.bm25 = None
        self._load_index()
        self._build_bm25()
        self._load_embedding_model()

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return re.findall(r"[a-z0-9]+", str(text).lower())

    def _load_index(self) -> None:
        if not self.faiss_dir.exists():
            raise FileNotFoundError(f"FAISS directory not found: {self.faiss_dir}")
        if not self.index_path.exists():
            raise FileNotFoundError(f"FAISS index not found: {self.index_path}")
        if not self.metadata_path.exists():
            raise FileNotFoundError(f"FAISS metadata not found: {self.metadata_path}")

        self.index = faiss.read_index(str(self.index_path))

        with open(self.metadata_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)

        if not isinstance(data, list):
            raise ValueError("faiss_db/metadata.json must contain a JSON list.")

        self.metadata = [item for item in data if isinstance(item, dict)]

        if self.index.ntotal != len(self.metadata):
            raise ValueError(
                "FAISS/metadata size mismatch: "
                f"index contains {self.index.ntotal} vectors but metadata contains "
                f"{len(self.metadata)} records. Rebuild the FAISS database so both "
                "files are generated together."
            )

        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as handle:
                loaded = json.load(handle)
                if isinstance(loaded, dict):
                    self.config = loaded

    def _build_bm25(self) -> None:
        corpus = [
            self._tokens(self._text(item))
            for item in self.metadata
        ]
        if not corpus:
            raise ValueError("FAISS metadata contains no usable records.")
        self.bm25 = BM25Okapi(corpus)

    def _load_embedding_model(self) -> None:
        model_name = str(self.config.get("embedding_model") or EMBEDDING_MODEL)
        if model_name != EMBEDDING_MODEL:
            # The existing index was built with all-MiniLM-L6-v2. Do not silently
            # switch models because that would make query vectors incompatible.
            model_name = EMBEDDING_MODEL
        self.embedding_model = SentenceTransformer(model_name)

        dimension = int(self.embedding_model.get_sentence_embedding_dimension())
        if int(self.index.d) != dimension:
            raise ValueError(
                "Embedding dimension mismatch. "
                f"FAISS index dimension={self.index.d}, "
                f"embedding model dimension={dimension}. "
                "Use the same embedding model that created the index."
            )

    @staticmethod
    def _text(item: dict[str, Any]) -> str:
        return str(item.get("text") or item.get("content") or "").strip()

    @staticmethod
    def _normalize(values: np.ndarray) -> np.ndarray:
        values = np.asarray(values, dtype="float32")
        norms = np.linalg.norm(values, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return values / norms

    def _normalized_record(self, index: int, score: float) -> dict[str, Any]:
        item = self.metadata[index]
        content = self._text(item)
        source = str(item.get("source") or "Unknown source")
        page = item.get("page", "N/A")
        department = str(item.get("department") or "General")
        record_id = str(item.get("record_id") or "")

        metadata = {
            "source": source,
            "page": page,
            "department": department,
            "record_id": record_id,
        }

        return {
            "content": content,
            "text": content,
            "source": source,
            "page": page,
            "department": department,
            "record_id": record_id,
            "score": float(score),
            "metadata": metadata,
        }

    def search(self, query: str, top_k: int = TOP_K_FINAL) -> list[dict[str, Any]]:
        query = str(query or "").strip()
        if not query:
            return []

        requested_k = max(1, min(int(top_k), len(self.metadata)))

        query_vector = self.embedding_model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")

        faiss_scores, faiss_ids = self.index.search(
            query_vector,
            min(TOP_K_FAISS, len(self.metadata)),
        )

        bm25_scores = np.asarray(
            self.bm25.get_scores(self._tokens(query)),
            dtype="float32",
        )
        bm25_order = np.argsort(bm25_scores)[::-1][:TOP_K_BM25]

        candidates: set[int] = set()
        semantic_score: dict[int, float] = {}
        keyword_score: dict[int, float] = {}

        for idx, score in zip(faiss_ids[0], faiss_scores[0]):
            idx = int(idx)
            if idx < 0 or idx >= len(self.metadata):
                continue
            candidates.add(idx)
            semantic_score[idx] = float(score)

        for idx in bm25_order:
            idx = int(idx)
            candidates.add(idx)
            keyword_score[idx] = float(bm25_scores[idx])

        if not candidates:
            return []

        semantic_values = np.array(
            [semantic_score.get(idx, 0.0) for idx in candidates],
            dtype="float32",
        )
        keyword_values = np.array(
            [keyword_score.get(idx, 0.0) for idx in candidates],
            dtype="float32",
        )

        # Convert both rankings to 0..1 before combining them.
        def minmax(values: np.ndarray) -> np.ndarray:
            if len(values) == 0:
                return values
            low = float(values.min())
            high = float(values.max())
            if high - low < 1e-8:
                return np.ones_like(values) if high > 0 else np.zeros_like(values)
            return (values - low) / (high - low)

        semantic_norm = minmax(semantic_values)
        keyword_norm = minmax(keyword_values)

        combined = 0.70 * semantic_norm + 0.30 * keyword_norm
        ranked = sorted(
            zip(candidates, combined),
            key=lambda pair: float(pair[1]),
            reverse=True,
        )[:requested_k]

        return [
            self._normalized_record(idx, float(score))
            for idx, score in ranked
        ]

    def retrieve(self, query: str, top_k: int = TOP_K_FINAL) -> list[dict[str, Any]]:
        return self.search(query, top_k=top_k)
