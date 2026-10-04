def build_context(
    evidence,
    max_items=8,
):
    """
    Convert structured retrieval evidence into a grounded
    context block for Groq.

    Every source remains attached to its evidence.
    """

    if not evidence:
        return ""

    context_parts = []

    for index, item in enumerate(
        evidence[:max_items],
        start=1,
    ):

        if not isinstance(item, dict):
            continue

        text = str(
            item.get(
                "text",
                "",
            )
        ).strip()

        if not text:
            continue

        source = str(
            item.get(
                "source",
                item.get(
                    "metadata",
                    {},
                ).get(
                    "source",
                    "Unknown source",
                ),
            )
        )

        page = str(
            item.get(
                "page",
                item.get(
                    "metadata",
                    {},
                ).get(
                    "page",
                    "N/A",
                ),
            )
        )

        department = str(
            item.get(
                "department",
                item.get(
                    "metadata",
                    {},
                ).get(
                    "department",
                    "",
                ),
            )
        )

        record_id = str(
            item.get(
                "record_id",
                item.get(
                    "metadata",
                    {},
                ).get(
                    "record_id",
                    "",
                ),
            )
        )


        context_parts.append(
            f"""
KNOWLEDGE RECORD {index}

SOURCE: {source}
PAGE: {page}
CATEGORY: {department}
RECORD ID: {record_id}

CONTENT:
{text}
""".strip()
        )


    return "\n\n".join(
        context_parts
    )


def has_grounded_evidence(evidence):
    """Return True only when usable evidence exists."""

    if not evidence:
        return False

    for item in evidence:

        if not isinstance(item, dict):
            continue

        if str(
            item.get(
                "text",
                "",
            )
        ).strip():

            return True

    return False
