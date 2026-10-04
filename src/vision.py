from __future__ import annotations

import base64
import json
import re
from typing import Any

from groq import Groq

from .config import (
    EXPECTED_PAYMENT_RECIPIENT,
    GROQ_API_KEY,
    GROQ_VISION_MODEL,
    UNLOCK_PRICE,
)

MAX_IMAGE_BYTES = 20 * 1024 * 1024


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = str(text or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        value = json.loads(cleaned)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        try:
            value = json.loads(cleaned[start : end + 1])
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            pass

    return {}


def analyze_payment_screenshot(uploaded_file) -> dict[str, Any]:
    """Extract visible payment fields from a screenshot using a Groq vision model.

    This function only extracts what the screenshot appears to show. It does not
    decide that a payment is genuine. The application performs deterministic
    recipient/amount/status checks afterward.
    """

    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is missing from Streamlit Secrets.")

    if uploaded_file is None:
        raise ValueError("No payment screenshot was provided.")

    image_bytes = uploaded_file.getvalue()
    if not image_bytes:
        raise ValueError("The uploaded payment screenshot is empty.")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise ValueError("The payment screenshot exceeds the 20 MB limit.")

    mime_type = getattr(uploaded_file, "type", None) or "image/jpeg"
    encoded = base64.b64encode(image_bytes).decode("utf-8")

    prompt = f"""
Read this payment screenshot carefully and extract only visibly supported fields.

Expected demo recipient: {EXPECTED_PAYMENT_RECIPIENT}
Expected demo amount: Rs. {UNLOCK_PRICE}

Return ONLY valid JSON with these keys:
{{
  "recipient": "string or empty",
  "amount": number or 0,
  "status": "string or empty",
  "confidence": number from 0 to 1
}}

Rules:
- Do not guess text that is not visible.
- If the amount is unclear, return 0.
- If the recipient is unclear, return an empty string.
- If payment status is unclear, return an empty string.
- Do not claim that the transaction is genuine or verified.
"""

    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model=GROQ_VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{encoded}"
                        },
                    },
                ],
            }
        ],
        temperature=0,
        max_tokens=500,
    )

    content = response.choices[0].message.content or ""
    result = _extract_json(content)

    return {
        "recipient": str(result.get("recipient") or "").strip(),
        "amount": result.get("amount", 0),
        "status": str(result.get("status") or "").strip(),
        "confidence": result.get("confidence", 0),
        "verification_type": "AI Screenshot Extraction — Demo",
        "model": GROQ_VISION_MODEL,
        "verified_by_vision": False,
    }
