import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from .config import CHUNK_OVERLAP, CHUNK_SIZE


def clean_text(text: str) -> str:
    """
    Clean extracted PDF text while preserving useful content.
    """
    if not text:
        return ""

    text = text.replace("\x00", " ")
    text = text.replace("\r", "\n")

    # Remove excessive spaces but preserve paragraphs.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """
    Character-based chunking with overlap.
    """
    text = clean_text(text)

    if not text:
        return []

    if overlap >= chunk_size:
        overlap = max(0, chunk_size // 5)

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - overlap

    return chunks


def extract_pdf_chunks(pdf_path: Path) -> list[dict[str, Any]]:
    """
    Extract page-aware chunks from one PDF.
    """
    results: list[dict[str, Any]] = []

    reader = PdfReader(str(pdf_path))

    for page_number, page in enumerate(reader.pages, start=1):
        try:
            raw_text = page.extract_text() or ""
        except Exception:
            raw_text = ""

        cleaned = clean_text(raw_text)

        if not cleaned:
            continue

        chunks = chunk_text(cleaned)

        for chunk_number, chunk in enumerate(chunks, start=1):
            results.append(
                {
                    "source": pdf_path.name,
                    "page": page_number,
                    "department": infer_department(pdf_path.name),
                    "chunk_id": f"{pdf_path.stem}_{page_number}_{chunk_number}",
                    "content": chunk,
                }
            )

    return results


def infer_department(filename: str) -> str:
    """
    Infer the department/category from the expected PDF filename.
    """
    name = filename.lower()

    mapping = {
        "places": "Places",
        "hotels": "Hotels",
        "transport": "Transport",
        "safety": "Safety",
        "food": "Food",
        "activities": "Activities",
    }

    for key, value in mapping.items():
        if key in name:
            return value

    return "General Tourism"


def load_all_pdfs(knowledge_base_dir: Path) -> list[dict[str, Any]]:
    """
    Extract chunks from every PDF in the knowledge base.
    """
    if not knowledge_base_dir.exists():
        return []

    pdf_files = sorted(knowledge_base_dir.glob("*.pdf"))

    all_chunks: list[dict[str, Any]] = []

    for pdf_path in pdf_files:
        try:
            all_chunks.extend(extract_pdf_chunks(pdf_path))
        except Exception:
            # Skip a damaged/unreadable PDF instead of crashing
            # the complete ingestion process.
            continue

    return all_chunks
