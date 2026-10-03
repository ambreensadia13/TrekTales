import json
import re
from pathlib import Path

import faiss
import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent

PDF_FOLDER = BASE_DIR / "tourism_knowledge_base"

OUTPUT_FOLDER = BASE_DIR / "faiss_db"

EMBEDDING_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150


OUTPUT_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)


def get_department(filename):

    name = filename.lower()

    mapping = {
        "places": "Places",
        "hotels": "Hotels",
        "transport": "Transport",
        "food": "Food",
        "activities": "Activities",
        "safety": "Safety"
    }

    for key, value in mapping.items():

        if key in name:
            return value

    return "General"


def get_record_id(text):

    pattern = (
        r"\b(?:PL|HT|TR|FD|AC|SF)-\d{3}\b"
    )

    match = re.search(
        pattern,
        text
    )

    if match:
        return match.group(0)

    return None


def clean_text(text):

    if not text:
        return ""

    text = text.replace(
        "\x00",
        " "
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


def chunk_text(
    text,
    chunk_size=CHUNK_SIZE,
    overlap=CHUNK_OVERLAP
):

    if not text:
        return []

    if overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size."
        )

    chunks = []

    start = 0

    while start < len(text):

        end = min(
            start + chunk_size,
            len(text)
        )

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap

    return chunks


def extract_pdf(pdf_path):

    pages = []

    reader = PdfReader(
        str(pdf_path)
    )

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):

        text = page.extract_text() or ""

        text = clean_text(text)

        if text:

            pages.append(
                {
                    "page": page_number,
                    "text": text
                }
            )

    return pages


def build_chunks():

    if not PDF_FOLDER.exists():

        raise FileNotFoundError(
            "tourism_knowledge_base folder "
            "does not exist."
        )

    pdf_files = sorted(
        PDF_FOLDER.glob("*.pdf")
    )

    if not pdf_files:

        raise FileNotFoundError(
            "No PDF files were found inside "
            "tourism_knowledge_base."
        )

    all_chunks = []

    for pdf_path in pdf_files:

        department = get_department(
            pdf_path.name
        )

        pages = extract_pdf(
            pdf_path
        )

        print(
            f"{pdf_path.name}: "
            f"{len(pages)} pages"
        )

        for page_data in pages:

            page_number = page_data["page"]

            chunks = chunk_text(
                page_data["text"]
            )

            for chunk in chunks:

                all_chunks.append(
                    {
                        "text": chunk,
                        "source": pdf_path.name,
                        "page": page_number,
                        "department": department,
                        "record_id": get_record_id(
                            chunk
                        )
                    }
                )

    return all_chunks


def create_embeddings(chunks):

    model = SentenceTransformer(
        EMBEDDING_MODEL
    )

    texts = [
        item["text"]
        for item in chunks
    ]

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    return embeddings.astype(
        "float32"
    )


def create_faiss(embeddings):

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(
        dimension
    )

    index.add(
        embeddings
    )

    faiss.write_index(
        index,
        str(
            OUTPUT_FOLDER / "index.faiss"
        )
    )


def save_metadata(chunks):

    with open(
        OUTPUT_FOLDER / "metadata.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            chunks,
            file,
            ensure_ascii=False,
            indent=2
        )


def save_config():

    config = {
        "embedding_model": EMBEDDING_MODEL,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "similarity": "cosine",
        "index": "IndexFlatIP"
    }

    with open(
        OUTPUT_FOLDER / "config.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            config,
            file,
            indent=2
        )


def main():

    print("=" * 60)
    print("TREKTALES FAISS INGESTION")
    print("=" * 60)

    chunks = build_chunks()

    print(
        f"Total chunks: {len(chunks)}"
    )

    if not chunks:
        raise RuntimeError(
            "No text chunks were created."
        )

    embeddings = create_embeddings(
        chunks
    )

    create_faiss(
        embeddings
    )

    save_metadata(
        chunks
    )

    save_config()

    print("\nFAISS database created successfully.")

    print(
        "faiss_db/index.faiss"
    )

    print(
        "faiss_db/metadata.json"
    )

    print(
        "faiss_db/config.json"
    )


if __name__ == "__main__":
    main()
