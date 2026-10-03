import json
import re
from pathlib import Path
from typing import List, Dict

import faiss
import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

from src.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    EMBEDDING_MODEL,
    FAISS_DIR,
    KNOWLEDGE_BASE_DIR,
)


# ============================================================
# PDF EXTRACTION
# ============================================================

def extract_pdf_text(pdf_path: Path) -> str:

    reader = PdfReader(str(pdf_path))

    pages = []

    for page in reader.pages:

        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""

        if text.strip():
            pages.append(text)

    return "\n".join(pages)


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_text(text: str) -> str:

    text = text.replace("\x00", " ")

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


# ============================================================
# CHUNKING
# ============================================================

def create_chunks(
    text: str,
    source: str,
) -> List[Dict]:

    text = clean_text(text)

    if not text:
        return []

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:

        end = min(
            start + CHUNK_SIZE,
            text_length,
        )

        chunk = text[start:end].strip()

        if chunk:

            chunks.append(
                {
                    "text": chunk,
                    "source": source,
                }
            )

        if end >= text_length:
            break

        next_start = end - CHUNK_OVERLAP

        if next_start <= start:
            next_start = end

        start = next_start

    return chunks


# ============================================================
# MAIN INGESTION
# ============================================================

def main():

    print("=" * 60)
    print("TrekTales AI - Tourism Knowledge Base Ingestion")
    print("=" * 60)

    if not KNOWLEDGE_BASE_DIR.exists():

        raise FileNotFoundError(
            f"Knowledge base directory not found:\n"
            f"{KNOWLEDGE_BASE_DIR}"
        )

    pdf_files = sorted(
        KNOWLEDGE_BASE_DIR.glob("*.pdf")
    )

    if not pdf_files:

        raise FileNotFoundError(
            "No PDF files were found in "
            "tourism_knowledge_base/"
        )

    print(
        f"\nFound {len(pdf_files)} PDF files."
    )

    all_chunks = []

    for pdf_path in pdf_files:

        print(
            f"\nReading: {pdf_path.name}"
        )

        text = extract_pdf_text(pdf_path)

        if not text.strip():

            print(
                "  WARNING: No extractable text found."
            )

            continue

        chunks = create_chunks(
            text=text,
            source=pdf_path.name,
        )

        print(
            f"  Created {len(chunks)} chunks."
        )

        all_chunks.extend(chunks)

    if not all_chunks:

        raise RuntimeError(
            "No text chunks were created from the PDFs."
        )

    print(
        f"\nTotal chunks: {len(all_chunks)}"
    )

    print(
        "\nLoading embedding model..."
    )

    model = SentenceTransformer(
        EMBEDDING_MODEL
    )

    texts = [
        item["text"]
        for item in all_chunks
    ]

    print(
        "Creating embeddings..."
    )

    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    embeddings = embeddings.astype(
        "float32"
    )

    dimension = embeddings.shape[1]

    print(
        f"Embedding dimension: {dimension}"
    )

    # Inner-product FAISS index.
    # Because embeddings are normalized,
    # inner product behaves like cosine similarity.
    index = faiss.IndexFlatIP(
        dimension
    )

    index.add(embeddings)

    FAISS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    index_path = FAISS_DIR / "index.faiss"

    metadata_path = FAISS_DIR / "metadata.json"

    config_path = FAISS_DIR / "config.json"

    print(
        "\nSaving FAISS index..."
    )

    faiss.write_index(
        index,
        str(index_path),
    )

    with open(
        metadata_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            all_chunks,
            file,
            ensure_ascii=False,
            indent=2,
        )

    config = {
        "embedding_model": EMBEDDING_MODEL,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "dimension": dimension,
        "documents": len(pdf_files),
        "chunks": len(all_chunks),
        "similarity": "cosine_via_inner_product",
    }

    with open(
        config_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            config,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)

    print(
        f"\nIndex: {index_path}"
    )

    print(
        f"Metadata: {metadata_path}"
    )

    print(
        f"Config: {config_path}"
    )

    print(
        f"\nDocuments: {len(pdf_files)}"
    )

    print(
        f"Chunks: {len(all_chunks)}"
    )


if __name__ == "__main__":
    main()
