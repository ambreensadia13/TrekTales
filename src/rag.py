from pathlib import Path
import json
import re

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from src.config import (
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_TOP_K,
    KEYWORD_WEIGHT,
    SEMANTIC_WEIGHT,
)


class HybridRetriever:
    """
    Hybrid tourism retriever.

    FAISS provides semantic similarity.

    A lightweight keyword score improves retrieval for
    exact tourism terms such as hotel, food, park, stadium,
    budget, transport and area names.
    """

    def __init__(
        self,
        index_path,
        metadata_path,
        config_path=None,
    ):

        self.index_path = Path(index_path)

        self.metadata_path = Path(
            metadata_path
        )

        self.config_path = (
            Path(config_path)
            if config_path
            else None
        )

        self.index = None

        self.metadata = []

        self.embedding_model = None

        self.embedding_model_name = (
            DEFAULT_EMBEDDING_MODEL
        )

        self._load_config()

        self._load_metadata()

        self._load_index()

        self._load_embedding_model()


    # ========================================================
    # CONFIG
    # ========================================================

    def _load_config(self):

        if not self.config_path:
            return

        if not self.config_path.exists():
            return

        try:

            with open(
                self.config_path,
                "r",
                encoding="utf-8",
            ) as file:

                config = json.load(file)

            model_name = (
                config.get("embedding_model")
                or config.get("embedding_model_name")
            )

            if model_name:
                self.embedding_model_name = str(
                    model_name
                )

        except Exception:
            # Do not crash because config.json is optional.
            self.embedding_model_name = (
                DEFAULT_EMBEDDING_MODEL
            )


    # ========================================================
    # METADATA
    # ========================================================

    def _load_metadata(self):

        if not self.metadata_path.exists():

            raise FileNotFoundError(
                "FAISS metadata file was not found: "
                f"{self.metadata_path}"
            )

        with open(
            self.metadata_path,
            "r",
            encoding="utf-8",
        ) as file:

            raw = json.load(file)


        if isinstance(raw, list):

            self.metadata = raw

        elif isinstance(raw, dict):

            if isinstance(
                raw.get("metadata"),
                list,
            ):

                self.metadata = raw["metadata"]

            elif isinstance(
                raw.get("documents"),
                list,
            ):

                self.metadata = raw["documents"]

            elif isinstance(
                raw.get("items"),
                list,
            ):

                self.metadata = raw["items"]

            else:

                self.metadata = []

        else:

            self.metadata = []


        if not self.metadata:

            raise ValueError(
                "metadata.json was loaded, but it contains "
                "no usable records."
            )


    # ========================================================
    # FAISS
    # ========================================================

    def _load_index(self):

        if not self.index_path.exists():

            raise FileNotFoundError(
                "FAISS index not found: "
                f"{self.index_path}"
            )

        self.index = faiss.read_index(
            str(self.index_path)
        )

        if self.index.ntotal == 0:

            raise ValueError(
                "The FAISS index is empty."
            )

        if self.index.ntotal != len(
            self.metadata
        ):

            raise ValueError(
                "FAISS/metadata mismatch: "
                f"index contains {self.index.ntotal} "
                f"vectors but metadata contains "
                f"{len(self.metadata)} records."
            )


    # ========================================================
    # EMBEDDING MODEL
    # ========================================================

    def _load_embedding_model(self):

        self.embedding_model = (
            SentenceTransformer(
                self.embedding_model_name
            )
        )


    # ========================================================
    # TEXT NORMALIZATION
    # ========================================================

    @staticmethod
    def _normalize_text(value):

        if value is None:
            return ""

        text = str(value)

        text = text.lower()

        text = re.sub(
            r"[^a-z0-9\s]",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()


    # ========================================================
    # KEYWORDS
    # ========================================================

    def _keywords(self, query):

        normalized = self._normalize_text(
            query
        )

        return set(
            word
            for word in normalized.split()
            if len(word) >= 3
        )


    def _keyword_score(
        self,
        query,
        record,
    ):

        query_words = self._keywords(
            query
        )

        if not query_words:
            return 0.0

        text = record.get(
            "text",
            "",
        )

        normalized_text = (
            self._normalize_text(text)
        )

        text_words = set(
            normalized_text.split()
        )

        if not text_words:
            return 0.0

        overlap = (
            query_words
            & text_words
        )

        return (
            len(overlap)
            / len(query_words)
        )


    # ========================================================
    # RECORD NORMALIZATION
    # ========================================================

    @staticmethod
    def _normalize_record(
        record,
        score=None,
        keyword_score=None,
    ):

        if not isinstance(
            record,
            dict,
        ):

            record = {
                "text": str(record)
            }

        metadata = record.get(
            "metadata",
            {},
        )

        if not isinstance(
            metadata,
            dict,
        ):

            metadata = {}


        text = (
            record.get("text")
            or record.get("content")
            or record.get("page_content")
            or ""
        )


        source = (
            record.get("source")
            or metadata.get("source")
            or "Unknown source"
        )


        page = (
            record.get("page")
            or metadata.get("page")
            or "N/A"
        )


        department = (
            record.get("department")
            or metadata.get("department")
            or ""
        )


        record_id = (
            record.get("record_id")
            or metadata.get("record_id")
            or ""
        )


        normalized_metadata = {
            **metadata,
            "source": str(source),
            "page": str(page),
            "department": str(department),
            "record_id": str(record_id),
        }


        result = {
            "text": str(text),
            "source": str(source),
            "page": str(page),
            "department": str(department),
            "record_id": str(record_id),
            "metadata": normalized_metadata,
        }


        if score is not None:
            result["semantic_score"] = float(
                score
            )

        if keyword_score is not None:
            result["keyword_score"] = float(
                keyword_score
            )

        return result


    # ========================================================
    # SEARCH
    # ========================================================

    def search(
        self,
        query,
        top_k=DEFAULT_TOP_K,
    ):

        query = str(query).strip()

        if not query:
            return []

        if not self.metadata:
            return []

        if self.index.ntotal == 0:
            return []


        candidate_k = min(
            max(top_k * 4, top_k),
            self.index.ntotal,
        )


        query_embedding = (
            self.embedding_model.encode(
                [query],
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
        )


        query_embedding = np.asarray(
            query_embedding,
            dtype="float32",
        )


        semantic_scores, indices = (
            self.index.search(
                query_embedding,
                candidate_k,
            )
        )


        candidates = []


        for score, index_id in zip(
            semantic_scores[0],
            indices[0],
        ):

            if index_id < 0:
                continue

            if index_id >= len(
                self.metadata
            ):
                continue

            record = self.metadata[
                int(index_id)
            ]

            keyword_score = (
                self._keyword_score(
                    query,
                    record,
                )
            )


            # FAISS IndexFlatIP with normalized
            # embeddings gives cosine similarity.
            semantic_normalized = max(
                0.0,
                min(
                    1.0,
                    (float(score) + 1.0) / 2.0,
                ),
            )


            combined_score = (
                SEMANTIC_WEIGHT
                * semantic_normalized
                +
                KEYWORD_WEIGHT
                * keyword_score
            )


            candidates.append(
                (
                    combined_score,
                    semantic_normalized,
                    keyword_score,
                    record,
                )
            )


        candidates.sort(
            key=lambda item: item[0],
            reverse=True,
        )


        results = []


        for (
            combined_score,
            semantic_score,
            keyword_score,
            record,
        ) in candidates[:top_k]:

            normalized = (
                self._normalize_record(
                    record,
                    score=combined_score,
                    keyword_score=keyword_score,
                )
            )

            normalized[
                "combined_score"
            ] = float(
                combined_score
            )

            normalized[
                "semantic_score"
            ] = float(
                semantic_score
            )

            results.append(
                normalized
            )


        return results


    # ========================================================
    # COMPATIBILITY ALIAS
    # ========================================================

    def retrieve(
        self,
        query,
        top_k=DEFAULT_TOP_K,
    ):

        return self.search(
            query,
            top_k=top_k,
        )
