from pathlib import Path
import json

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader


# ============================================================
# PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent

KNOWLEDGE_BASE_DIR = (
    ROOT_DIR
    / "tourism_knowledge_base"
)

FAISS_DIR = (
    ROOT_DIR
    / "faiss_db"
)

INDEX_PATH = (
    FAISS_DIR
    / "index.faiss"
)

METADATA_PATH = (
    FAISS_DIR
    / "metadata.json"
)

CONFIG_PATH = (
    FAISS_DIR
    / "config.json"
)


# ============================================================
# CONFIG
# ============================================================

EMBEDDING_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)

CHUNK_SIZE = 900

CHUNK_OVERLAP = 150


# ============================================================
# READ PDF
# ============================================================

def read_pdf(
    pdf_path,
):
    records = []

    reader = PdfReader(
        str(pdf_path)
    )

    for page_number, page in enumerate(
        reader.pages,
        start=1,
    ):

        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""

        text = text.strip()

        if not text:
            continue

        records.append(
            {
                "source": pdf_path.name,
                "page": page_number,
                "text": text,
            }
        )

    return records


# ============================================================
# CHUNK TEXT
# ============================================================

def chunk_text(
    text,
    chunk_size=CHUNK_SIZE,
    overlap=CHUNK_OVERLAP,
):

    text = text.strip()

    if not text:
        return []

    chunks = []

    start = 0

    while start < len(text):

        end = min(
            start + chunk_size,
            len(text),
        )

        chunk = text[
            start:end
        ].strip()

        if chunk:
            chunks.append(
                chunk
            )

        if end >= len(text):
            break

        start = (
            end
            - overlap
        )

        if start < 0:
            start = 0

    return chunks


# ============================================================
# MAIN
# ============================================================

def main():

    if not KNOWLEDGE_BASE_DIR.exists():

        raise FileNotFoundError(
            "Knowledge base folder not found: "
            f"{KNOWLEDGE_BASE_DIR}"
        )


    pdf_files = sorted(
        KNOWLEDGE_BASE_DIR.glob(
            "*.pdf"
        )
    )


    if not pdf_files:

        raise FileNotFoundError(
            "No PDF files were found in "
            f"{KNOWLEDGE_BASE_DIR}"
        )


    all_records = []


    for pdf_path in pdf_files:

        print(
            f"Reading {pdf_path.name}..."
        )

        pages = read_pdf(
            pdf_path
        )

        for page_record in pages:

            chunks = chunk_text(
                page_record["text"]
            )

            for chunk in chunks:

                all_records.append(
                    {
                        "text": chunk,
                        "source": page_record[
                            "source"
                        ],
                        "page": page_record[
                            "page"
                        ],
                        "department": (
                            pdf_path.stem
                        ),
                    }
                )


    if not all_records:

        raise RuntimeError(
            "No text could be extracted "
            "from the tourism PDFs."
        )


    print(
        f"Creating embeddings for "
        f"{len(all_records)} chunks..."
    )


    model = SentenceTransformer(
        EMBEDDING_MODEL
    )


    texts = [
        item["text"]
        for item in all_records
    ]


    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )


    embeddings = np.asarray(
        embeddings,
        dtype="float32",
    )


    dimension = embeddings.shape[1]


    index = faiss.IndexFlatIP(
        dimension
    )


    index.add(
        embeddings
    )


    FAISS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


    faiss.write_index(
        index,
        str(INDEX_PATH),
    )


    with open(
        METADATA_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            all_records,
            file,
            ensure_ascii=False,
            indent=2,
        )


    config = {
        "embedding_model": EMBEDDING_MODEL,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "total_chunks": len(
            all_records
        ),
    }


    with open(
        CONFIG_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            config,
            file,
            ensure_ascii=False,
            indent=2,
        )


    print()
    print(
        "======================================"
    )

    print(
        "TrekTales FAISS database created."
    )

    print(
        f"Chunks: {len(all_records)}"
    )

    print(
        f"Index: {INDEX_PATH}"
    )

    print(
        f"Metadata: {METADATA_PATH}"
    )

    print(
        f"Config: {CONFIG_PATH}"
    )

    print(
        "======================================"
    )


if __name__ == "__main__":
    main()
