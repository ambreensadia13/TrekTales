import json
import re
from typing import Any


def extract_json(text: str) -> dict[str, Any] | None:
    """
    Safely extract the first JSON object from model output.
    """
    if not text:
        return None

    cleaned = text.strip()

    # Remove markdown fences.
    cleaned = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    try:
        value = json.loads(cleaned)

        if isinstance(value, dict):
            return value

    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1 or end <= start:
        return None

    try:
        value = json.loads(
            cleaned[start:end + 1]
        )

        if isinstance(value, dict):
            return value

    except json.JSONDecodeError:
        return None

    return None
