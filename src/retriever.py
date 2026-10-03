import json
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder

from .config import (
    EMBEDDING_MODEL,
    FAISS_INDEX_PATH,
    METADATA_PATH,
    RERANKER_MODEL,
    TOP_K_BM25,
    TOP_K_FAISS,
    TOP_K_FINAL,
)
from .rag import load_all_pdfs


class HybridRetriever:
    """
    Hybrid tourism retriever.

    Retrieval:
        FAISS semantic search
        +
        BM25 lexical search
        +
        optional CrossEncoder reranking
    """

    def __init__(self):
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)

        self.index = None
        self.metadata: list[dict[str, Any]] = []
        self.documents: list[str] = []
        self.bm25 = None

        self.reranker = None

        self._load_reranker()
        self._load_index()

    def _load_reranker(self) -> None:
        """
        Load CrossEncoder if possible.
        """
        try:
            self.reranker = CrossEncoder(RERANKER_MODEL)
        except Exception:
            self.reranker = None

    def _load_index(self) -> None:
        """
        Load the existing FAISS index and metadata.
        """
        if not FAISS_INDEX_PATH.exists():
            raise FileNotFoundError(
                "FAISS index not found. Run `python ingest.py` first."
            )

        if not METADATA_PATH.exists():
            raise FileNotFoundError(
                "Metadata file not found. Run `python ingest.py` first."
            )

        self.index = faiss.read_index(str(FAISS_INDEX_PATH))

        with open(METADATA_PATH, "r", encoding="utf-8") as file:
            self.metadata = json.load(file)

        self.documents = [
            item.get("content", "")
            for item in self.metadata
        ]

        tokenized_documents = [
            self._tokenize(document)
            for document in self.documents
        ]

        self.bm25 = BM25Okapi(tokenized_documents)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return text.lower().split()

    def _semantic_search(self, query: str) -> list[tuple[int, float]]:
        """
        FAISS cosine-style search using normalized embeddings.
        """
        if self.index is None:
            return []

        query_vector = self.embedding_model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")

        scores, indices = self.index.search(
            query_vector,
            min(TOP_K_FAISS, len(self.metadata)),
        )

        results = []

        for score, index in zip(scores[0], indices[0]):
            if index < 0:
                continue

            results.append((int(index), float(score)))

        return results

    def _bm25_search(self, query: str) -> list[tuple[int, float]]:
        """
        BM25 lexical retrieval.
        """
        if self.bm25 is None:
            return []

        query_tokens = self._tokenize(query)

        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)

        ranked_indices = np.argsort(scores)[::-1]

        results = []

        for index in ranked_indices[:TOP_K_BM25]:
            score = float(scores[index])

            if score <= 0:
                continue

            results.append((int(index), score))

        return results

    @staticmethod
    def _normalize_scores(
        values: list[tuple[int, float]]
    ) -> dict[int, float]:
        if not values:
            return {}

        scores = [score for _, score in values]

        minimum = min(scores)
        maximum = max(scores)

        if maximum == minimum:
            return {
                index: 1.0
                for index, _ in values
            }

        return {
            index: (score - minimum) / (maximum - minimum)
            for index, score in values
        }

    def search(self, query: str) -> list[dict[str, Any]]:
        """
        Perform hybrid retrieval and reranking.
        """
        if not query.strip():
            return []

        semantic_results = self._semantic_search(query)
        bm25_results = self._bm25_search(query)

        semantic_scores = self._normalize_scores(semantic_results)
        bm25_scores = self._normalize_scores(bm25_results)

        combined_scores: dict[int, float] = {}

        all_indices = set(semantic_scores) | set(bm25_scores)

        for index in all_indices:
            semantic = semantic_scores.get(index, 0.0)
            lexical = bm25_scores.get(index, 0.0)

            # Balanced hybrid score.
            combined_scores[index] = (
                0.60 * semantic +
                0.40 * lexical
            )

        ranked = sorted(
            combined_scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        candidates = ranked[: max(TOP_K_FINAL * 2, TOP_K_FINAL)]

        if self.reranker is not None and candidates:
            pairs = [
                [query, self.documents[index]]
                for index, _ in candidates
            ]

            try:
                rerank_scores = self.reranker.predict(pairs)

                reranked = sorted(
                    zip(candidates, rerank_scores),
                    key=lambda item: float(item[1]),
                    reverse=True,
                )

                candidates = [
                    (index, float(score))
                    for ((index, _), score) in reranked[:TOP_K_FINAL]
                ]

            except Exception:
                candidates = candidates[:TOP_K_FINAL]

        else:
            candidates = candidates[:TOP_K_FINAL]

        results = []

        for index, score in candidates:
            item = dict(self.metadata[index])

            item["retrieval_score"] = round(float(score), 4)

            results.append(item)

        return results


def build_retriever() -> HybridRetriever:
    return HybridRetriever()
