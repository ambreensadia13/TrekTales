def extract_sources(evidence):
    """
    Convert retrieval evidence into clean source records.
    """

    sources = []

    seen = set()

    for item in evidence or []:

        if not isinstance(item, dict):
            continue

        metadata = item.get(
            "metadata",
            {},
        )

        if not isinstance(
            metadata,
            dict,
        ):
            metadata = {}


        source = (
            item.get("source")
            or metadata.get("source")
            or "Unknown source"
        )

        page = (
            item.get("page")
            or metadata.get("page")
            or "N/A"
        )

        department = (
            item.get("department")
            or metadata.get("department")
            or ""
        )

        record_id = (
            item.get("record_id")
            or metadata.get("record_id")
            or ""
        )


        key = (
            str(source),
            str(page),
            str(record_id),
        )


        if key in seen:
            continue

        seen.add(key)


        sources.append(
            {
                "source": str(source),
                "page": str(page),
                "department": str(department),
                "record_id": str(record_id),
            }
        )


    return sources
