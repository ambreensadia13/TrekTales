import base64
import json
import re

from openai import OpenAI

from src.config import (
    GROQ_API_KEY,
    GROQ_BASE_URL,
    GROQ_VISION_MODEL,
)


def _extract_json(text):
    """
    Extract a JSON object from model output.
    """

    if not text:
        return {}

    cleaned = str(text).strip()

    cleaned = re.sub(
        r"^```(?:json)?",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"```$",
        "",
        cleaned,
    )

    cleaned = cleaned.strip()


    try:

        value = json.loads(
            cleaned
        )

        if isinstance(
            value,
            dict,
        ):
            return value

    except Exception:
        pass


    match = re.search(
        r"\{.*\}",
        cleaned,
        flags=re.DOTALL,
    )

    if not match:
        return {}

    try:

        value = json.loads(
            match.group(0)
        )

        if isinstance(
            value,
            dict,
        ):
            return value

    except Exception:
        pass


    return {}


def _normalize_amount(value):

    if value is None:
        return 0

    if isinstance(
        value,
        (int, float),
    ):

        return value

    text = str(value)

    match = re.search(
        r"\d+(?:[,.]\d+)*",
        text,
    )

    if not match:
        return 0

    number = (
        match.group(0)
        .replace(
            ",",
            "",
        )
    )

    try:

        return float(
            number
        )

    except ValueError:

        return 0


def analyze_payment_screenshot(
    image_bytes,
):
    """
    Use Groq vision to extract visible payment information.

    This function only extracts information.

    It does NOT approve payment.
    """

    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is missing."
        )

    if not image_bytes:
        raise ValueError(
            "Payment screenshot is empty."
        )


    client = OpenAI(
        api_key=GROQ_API_KEY,
        base_url=GROQ_BASE_URL,
    )


    encoded_image = base64.b64encode(
        image_bytes
    ).decode(
        "utf-8"
    )


    prompt = """
Analyze this payment screenshot.

Extract ONLY information visibly present in the image.

Return ONLY valid JSON using this exact structure:

{
  "recipient": "",
  "amount": 0,
  "status": "",
  "confidence": ""
}

Rules:

1. Do not guess missing information.
2. If recipient is not visible, return an empty string.
3. If amount is not visible, return 0.
4. If payment status is not visible, return an empty string.
5. Do not decide whether the payment is valid.
6. Do not claim that the payment is genuine.
7. Do not invent transaction information.
"""


    response = (
        client.chat.completions.create(
            model=GROQ_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": (
                                    "data:image/jpeg;base64,"
                                    + encoded_image
                                )
                            },
                        },
                    ],
                }
            ],
            temperature=0,
            max_tokens=500,
        )
    )


    if not response.choices:
        raise RuntimeError(
            "Vision model returned no response."
        )


    content = (
        response.choices[0]
        .message
        .content
    )


    data = _extract_json(
        content
    )


    return {
        "recipient": str(
            data.get(
                "recipient",
                "",
            )
        ).strip(),

        "amount": _normalize_amount(
            data.get(
                "amount",
                0,
            )
        ),

        "status": str(
            data.get(
                "status",
                "",
            )
        ).strip(),

        "confidence": str(
            data.get(
                "confidence",
                "",
            )
        ).strip(),
    }
