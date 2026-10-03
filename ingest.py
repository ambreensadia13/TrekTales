import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from src.config import (
    EMBEDDING_MODEL,
    FAISS_DIR,
    FAISS_INDEX_PATH,
    KNOWLEDGE_BASE_DIR,
    METADATA_PATH,
)
from src.rag import load_all_pdfs


def main() -> None:
    print("=" * 60)
    print("TrekTales Knowledge Base Ingestion")
    print("=" * 60)

    KNOWLEDGE_BASE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    FAISS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    chunks = load_all_pdfs(KNOWLEDGE_BASE_DIR)

    if not chunks:
        raise RuntimeError(
            "No readable PDF content was found in "
            f"{KNOWLEDGE_BASE_DIR}"
        )

    print(f"Extracted chunks: {len(chunks)}")

    texts = [
        chunk["content"]
        for chunk in chunks
    ]

    print("Loading embedding model...")

    model = SentenceTransformer(EMBEDDING_MODEL)

    print("Creating embeddings...")

    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype("float32")

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    faiss.write_index(
        index,
        str(FAISS_INDEX_PATH),
    )

    with open(
        METADATA_PATH,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            chunks,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("SUCCESS")
    print(f"FAISS index: {FAISS_INDEX_PATH}")
    print(f"Metadata:    {METADATA_PATH}")
    print(f"Vectors:     {len(chunks)}")


if __name__ == "__main__":
    main()
