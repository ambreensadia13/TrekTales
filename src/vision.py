import base64
import json
from pathlib import Path
from typing import Any, Dict

from groq import Groq

from .config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    EXPECTED_PAYMENT_RECIPIENT,
    UNLOCK_PRICE,
)


def _get_client() -> Groq:
    """Create the Groq client."""

    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add GROQ_API_KEY "
            "to Streamlit Secrets."
        )

    return Groq(api_key=GROQ_API_KEY)


def _encode_image(image_path: str) -> str:
    """Convert an image file to base64."""

    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Payment screenshot not found: {image_path}"
        )

    with path.open("rb") as image_file:
        return base64.b64encode(
            image_file.read()
        ).decode("utf-8")


def _image_mime_type(image_path: str) -> str:
    """Return the MIME type for a supported image."""

    suffix = Path(image_path).suffix.lower()

    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }

    return mime_types.get(
        suffix,
        "image/png",
    )


def _clean_json_response(text: str) -> Dict[str, Any]:
    """Safely convert the model response into a dictionary."""

    if not text:
        return {
            "recipient": "",
            "amount": 0,
            "status": "",
            "confidence": 0,
        }

    text = text.strip()

    # Remove markdown code fences if the model returns them.
    if text.startswith("```"):
        text = text.replace("```json", "", 1)
        text = text.replace("```", "")
        text = text.strip()

    try:
        result = json.loads(text)

        if isinstance(result, dict):
            return result

    except json.JSONDecodeError:
        pass

    return {
        "recipient": "",
        "amount": 0,
        "status": "",
        "confidence": 0,
    }


def analyze_payment_screenshot(
    image_path: str,
) -> Dict[str, Any]:
    """
    Analyze a JazzCash payment screenshot using Groq.

    This function only extracts information visible in the screenshot.
    It does NOT independently verify that a real payment occurred.
    """

    encoded_image = _encode_image(image_path)
    mime_type = _image_mime_type(image_path)

    client = _get_client()

    prompt = f"""
Analyze this payment screenshot.

Extract ONLY information that is visibly present.

Return ONLY valid JSON in exactly this structure:

{{
  "recipient": "",
  "amount": 0,
  "status": "",
  "confidence": 0
}}

Rules:

1. recipient:
   Extract the visible payment recipient/name.
   Do not guess.

2. amount:
   Extract the visible payment amount as a number.
   If it cannot be read, use 0.

3. status:
   Extract the visible payment status.
   Examples may include:
   sent
   successful
   completed
   pending
   failed

4. confidence:
   A number from 0 to 1 representing confidence
   in the extraction.

Important:
- Do not claim that the payment is genuine.
- Do not claim that the payment was actually received.
- Do not invent missing information.
- Do not use the expected recipient or expected amount
  to fill missing screenshot information.
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
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
                                f"data:{mime_type};base64,"
                                f"{encoded_image}"
                            )
                        },
                    },
                ],
            }
        ],
        temperature=0,
        max_tokens=500,
    )

    content = response.choices[0].message.content or ""

    result = _clean_json_response(content)

    return {
        "recipient": result.get(
            "recipient",
            "",
        ),
        "amount": result.get(
            "amount",
            0,
        ),
        "status": result.get(
            "status",
            "",
        ),
        "confidence": result.get(
            "confidence",
            0,
        ),
        "verification_label": (
            "AI Screenshot Verification — Demo"
        ),
    }


def analyze_payment_image(
    image_path: str,
) -> Dict[str, Any]:
    """Compatibility alias."""

    return analyze_payment_screenshot(
        image_path
    )


def extract_payment_details(
    image_path: str,
) -> Dict[str, Any]:
    """Compatibility alias."""

    return analyze_payment_screenshot(
        image_path
    )
