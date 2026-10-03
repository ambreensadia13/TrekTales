from typing import Any


def format_citations(
    evidence: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Convert retrieved evidence into clean citation objects.
    """
    citations = []

    seen = set()

    for item in evidence:
        source = str(item.get("source", "Unknown"))
        page = item.get("page", "N/A")
        department = str(
            item.get("department", "General Tourism")
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


def evidence_to_prompt(
    evidence: list[dict[str, Any]]
) -> str:
    """
    Format evidence for Grok.
    """
    if not evidence:
        return (
            "NO TOURISM KNOWLEDGE-BASE EVIDENCE WAS FOUND.\n"
            "Do not invent factual tourism information."
        )

    blocks = []

    for item in evidence:
        blocks.append(
            "\n".join(
                [
                    "SOURCE:",
                    str(item.get("source", "Unknown")),
                    "PAGE:",
                    str(item.get("page", "N/A")),
                    "DEPARTMENT:",
                    str(
                        item.get(
                            "department",
                            "General Tourism",
                        )
                    ),
                    "",
                    "CONTENT:",
                    str(item.get("content", "")),
                ]
            )
        )

    return "\n\n-----------------------------\n\n".join(blocks)
