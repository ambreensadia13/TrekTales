import base64
import json
import re
from typing import Any

import requests

from .config import XAI_API_KEY, XAI_BASE_URL, VISION_MODEL


def _extract_json(text: str) -> dict[str, Any]:
    """
    Extract a JSON object from Grok's response.
    """
    if not text:
        return {
            "recipient": "",
            "amount": None,
            "status": "",
            "confidence": 0,
        }

    cleaned = text.strip()

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
        data = json.loads(cleaned)

        if isinstance(data, dict):
            return data

    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start != -1 and end != -1:
        try:
            data = json.loads(
                cleaned[start:end + 1]
            )

            if isinstance(data, dict):
                return data

        except json.JSONDecodeError:
            pass

    return {
        "recipient": "",
        "amount": None,
        "status": "",
        "confidence": 0,
    }


def analyze_payment_screenshot(
    image_bytes: bytes,
    mime_type: str = "image/png",
) -> dict[str, Any]:
    """
    Ask Grok Vision to extract payment-screen information.

    IMPORTANT:
    This does NOT prove that a real payment occurred.
    It only extracts information visible in the screenshot.
    """

    if not XAI_API_KEY:
        raise RuntimeError(
            "XAI_API_KEY is missing."
        )

    if not image_bytes:
        raise ValueError(
            "The uploaded image is empty."
        )

    encoded = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    data_url = (
        f"data:{mime_type};base64,{encoded}"
    )

    prompt = """
Analyze this payment screenshot ONLY for visible text.

Return ONLY valid JSON using exactly these keys:

{
  "recipient": "",
  "amount": null,
  "status": "",
  "confidence": 0
}

Rules:
- recipient = the visible recipient/payee name.
- amount = numeric transaction amount if clearly visible.
- status = visible transaction status such as Sent, Successful,
  Completed, Pending, Failed, or Unknown.
- confidence = your confidence from 0 to 100.
- Do not invent missing information.
- If a field is not readable, use an empty string, null, or Unknown.
- Do not claim that the screenshot proves a real bank/payment transaction.
"""

    payload = {
        "model": VISION_MODEL,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_image",
                        "image_url": data_url,
                        "detail": "high",
                    },
                    {
                        "type": "input_text",
                        "text": prompt,
                    },
                ],
            }
        ],
    }

    response = requests.post(
        f"{XAI_BASE_URL}/responses",
        headers={
            "Authorization": f"Bearer {XAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120,
    )

    response.raise_for_status()

    data = response.json()

    text = extract_response_text(data)

    result = _extract_json(text)

    return normalize_vision_result(result)


def extract_response_text(data: dict[str, Any]) -> str:
    """
    Extract text from the xAI Responses API response.
    """
    output = data.get("output", [])

    texts = []

    for item in output:
        content = item.get("content", [])

        for content_item in content:
            if content_item.get("type") in {
                "output_text",
                "text",
            }:
                value = content_item.get("text")

                if value:
                    texts.append(str(value))

    if texts:
        return "\n".join(texts)

    # Defensive fallback for different response shapes.
    if isinstance(data.get("output_text"), str):
        return data["output_text"]

    return ""


def normalize_vision_result(
    result: dict[str, Any]
) -> dict[str, Any]:
    """
    Normalize extracted fields.
    """
    recipient = str(
        result.get("recipient", "")
    ).strip()

    status = str(
        result.get("status", "")
    ).strip()

    amount = result.get("amount")

    try:
        if amount is not None:
            amount = int(
                float(
                    str(amount)
                    .replace(",", "")
                    .replace("Rs.", "")
                    .replace("PKR", "")
                    .strip()
                )
            )
    except (TypeError, ValueError):
        amount = None

    try:
        confidence = int(
            float(
                result.get("confidence", 0)
            )
        )
    except (TypeError, ValueError):
        confidence = 0

    confidence = max(
        0,
        min(100, confidence),
    )

    return {
        "recipient": recipient,
        "amount": amount,
        "status": status,
        "confidence": confidence,
    }
