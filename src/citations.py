from __future__ import annotations

from typing import Any


def format_citations(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    citations: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    for item in evidence or []:
        if not isinstance(item, dict):
            continue

        metadata = item.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}

        source = str(metadata.get("source") or item.get("source") or "Unknown source")
        page = str(metadata.get("page") or item.get("page") or "N/A")
        department = str(
            metadata.get("department")
            or item.get("department")
            or "General"
        )
        key = (source, page, department)
        if key in seen:
            continue
        seen.add(key)
        citations.append(
            {
                "source": source,
                "page": page,
                "department": department,
            }
        )

    return citations


def evidence_to_prompt(evidence: list[dict[str, Any]]) -> str:
    if not evidence:
        return (
            "NO TOURISM KNOWLEDGE-BASE EVIDENCE WAS RETRIEVED.\n"
            "Do not invent destination-specific facts."
        )

    blocks: list[str] = []
    for number, item in enumerate(evidence, start=1):
        metadata = item.get("metadata") if isinstance(item, dict) else {}
        if not isinstance(metadata, dict):
            metadata = {}

        source = metadata.get("source") or item.get("source") or "Unknown source"
        page = metadata.get("page") or item.get("page") or "N/A"
        department = metadata.get("department") or item.get("department") or "General"
        record_id = metadata.get("record_id") or item.get("record_id") or ""
        content = item.get("content") or item.get("text") or ""

        blocks.append(
            f"EVIDENCE {number}\n"
            f"SOURCE: {source}\n"
            f"PAGE: {page}\n"
            f"DEPARTMENT: {department}\n"
            f"RECORD ID: {record_id}\n"
            f"CONTENT:\n{content}"
        )

    return "\n\n-----------------------------\n\n".join(blocks)
