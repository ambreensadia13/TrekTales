from __future__ import annotations

import base64
import json
import re
from typing import Any

import streamlit as st
from openai import OpenAI


# ============================================================
# DEFAULT SETTINGS
# ============================================================

DEFAULT_GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# Keep this as a fallback only.
# Prefer setting GROQ_VISION_MODEL in Streamlit Secrets.
DEFAULT_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


# ============================================================
# SECRET HELPERS
# ============================================================

def _get_secret(name: str, default: str = "") -> str:
    """Read a value from Streamlit Secrets."""

    try:
        value = st.secrets.get(name, default)

        if value is None:
            return default

        return str(value).strip()

    except Exception:
        return default


def _get_groq_settings() -> tuple[str, str, str]:
    """Load Groq API configuration."""

    api_key = _get_secret(
        "GROQ_API_KEY",
        "",
    )

    base_url = _get_secret(
        "GROQ_BASE_URL",
        DEFAULT_GROQ_BASE_URL,
    )

    vision_model = _get_secret(
        "GROQ_VISION_MODEL",
        DEFAULT_VISION_MODEL,
    )

    return (
        api_key,
        base_url.rstrip("/"),
        vision_model,
    )


# ============================================================
# JSON EXTRACTION
# ============================================================

def _extract_json(text: Any) -> dict:
    """Safely extract a JSON object from model output."""

    if not text:
        return {}

    cleaned = str(text).strip()

    # Remove opening markdown fence.
    cleaned = re.sub(
        r"^```(?:json|JSON)?\s*",
        "",
        cleaned,
    )

    # Remove closing markdown fence.
    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned,
    )

    cleaned = cleaned.strip()

    # Direct JSON.
    try:
        value = json.loads(cleaned)

        if isinstance(value, dict):
            return value

    except Exception:
        pass

    # JSON embedded inside surrounding text.
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

        if isinstance(value, dict):
            return value

    except Exception:
        pass

    return {}


# ============================================================
# AMOUNT NORMALIZATION
# ============================================================

def _normalize_amount(value: Any) -> float:
    """
    Convert values such as:

        199
        "199"
        "Rs. 199"
        "PKR 199"
        "1,199"

    into a numeric value.
    """

    if value is None:
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()

    match = re.search(
        r"\d+(?:[,.]\d+)*",
        text,
    )

    if not match:
        return 0.0

    number = match.group(0).replace(
        ",",
        "",
    )

    try:
        return float(number)

    except ValueError:
        return 0.0


# ============================================================
# IMAGE BYTES
# ============================================================

def _get_image_bytes(uploaded_file: Any) -> bytes:
    """Convert an uploaded file or bytes object into bytes."""

    if uploaded_file is None:
        return b""

    if isinstance(uploaded_file, bytes):
        return uploaded_file

    if isinstance(uploaded_file, bytearray):
        return bytes(uploaded_file)

    if hasattr(uploaded_file, "getvalue"):
        data = uploaded_file.getvalue()

        if isinstance(data, bytes):
            return data

    if hasattr(uploaded_file, "read"):
        data = uploaded_file.read()

        if isinstance(data, bytes):
            return data

    raise ValueError(
        "The uploaded payment file could not be read."
    )


# ============================================================
# IMAGE MIME DETECTION
# ============================================================

def _detect_image_mime(
    image_bytes: bytes,
) -> str | None:
    """Detect supported image type from file signature."""

    if not image_bytes:
        return None

    # JPEG
    if image_bytes.startswith(
        b"\xff\xd8\xff"
    ):
        return "image/jpeg"

    # PNG
    if image_bytes.startswith(
        b"\x89PNG\r\n\x1a\n"
    ):
        return "image/png"

    # WEBP
    if (
        len(image_bytes) >= 12
        and image_bytes[0:4] == b"RIFF"
        and image_bytes[8:12] == b"WEBP"
    ):
        return "image/webp"

    return None


# ============================================================
# PAYMENT EXTRACTION PROMPT
# ============================================================

PAYMENT_EXTRACTION_PROMPT = """
You are the Vision Agent for TrekTales.

Your ONLY task is to inspect the uploaded image and extract
information that is visibly present.

First determine whether the image appears to be a payment
or transaction confirmation screenshot.

A payment screenshot may visibly contain:

- Payment successful
- Payment completed
- Transaction successful
- Amount paid
- Recipient or merchant
- Transaction/reference information
- Date/time
- Wallet/payment service information

The image may NOT be a payment screenshot.

It may be:

- a website screenshot
- a GitHub screenshot
- a random photograph
- a document
- a social media screenshot
- an unrelated image
- an error screen

If it is not clearly a payment screenshot, return:

"is_payment_screenshot": false

Do NOT invent information.

Return ONLY valid JSON.

Use exactly this structure:

{
  "is_payment_screenshot": false,
  "recipient": "",
  "amount": 0,
  "status": "",
  "confidence": "low",
  "message": ""
}

Rules:

1. Extract ONLY information visibly present in the image.

2. Never guess.

3. Never infer information that is not visible.

4. If this is not clearly a payment screenshot:

   is_payment_screenshot = false
   recipient = ""
   amount = 0
   status = ""
   confidence = "low"

5. If it clearly appears to be a payment screenshot:

   is_payment_screenshot = true

6. If recipient is not visible:

   recipient = ""

7. If amount is not visible:

   amount = 0

8. If payment status is not visible:

   status = ""

9. Confidence must be exactly one of:

   low
   medium
   high

10. Do NOT decide whether the payment is genuine.

11. Do NOT claim that money was actually received.

12. Do NOT approve the payment.

13. Do NOT invent transaction IDs.

14. Do NOT invent dates.

15. Do NOT invent recipient names.

16. Do NOT invent amounts.

17. Return JSON only.
"""


# ============================================================
# ERROR MESSAGE HELPER
# ============================================================

def _format_api_error(
    exc: Exception,
    model: str,
) -> RuntimeError:
    """Convert common Groq/OpenAI errors into useful messages."""

    error_text = str(exc)
    error_lower = error_text.lower()

    # Authentication.
    if (
        "401" in error_text
        or "invalid api key" in error_lower
        or "invalid_api_key" in error_lower
        or "authentication" in error_lower
        or "unauthorized" in error_lower
    ):
        return RuntimeError(
            "Groq authentication failed for the Vision Agent. "
            "Check GROQ_API_KEY in Streamlit Secrets."
        )

    # Model.
    if (
        "404" in error_text
        or "model_not_found" in error_lower
        or "does not exist" in error_lower
        or "model not found" in error_lower
    ):
        return RuntimeError(
            "The configured Groq Vision model is unavailable. "
            f"Current model: {model}. "
            "Check GROQ_VISION_MODEL in Streamlit Secrets."
        )

    # Rate limit.
    if (
        "429" in error_text
        or "rate limit" in error_lower
        or "rate_limit" in error_lower
        or "too many requests" in error_lower
    ):
        return RuntimeError(
            "Groq Vision is temporarily rate-limited. "
            "Please wait for the rate limit to reset and try again."
        )

    # Bad request.
    if (
        "400" in error_text
        or "bad request" in error_lower
    ):
        return RuntimeError(
            "Groq rejected the Vision Agent request. "
            f"Check the Vision model ({model}) and uploaded image."
        )

    return RuntimeError(
        f"Vision analysis failed: {error_text}"
    )


# ============================================================
# MAIN VISION FUNCTION
# ============================================================

def analyze_payment_screenshot(
    image_bytes: Any,
) -> dict:
    """
    Analyze a payment screenshot with Groq Vision.

    Returns:

    {
        "is_payment_screenshot": bool,
        "recipient": str,
        "amount": number,
        "status": str,
        "confidence": str,
        "message": str
    }
    """

    # --------------------------------------------------------
    # LOAD SETTINGS
    # --------------------------------------------------------

    (
        groq_api_key,
        groq_base_url,
        groq_vision_model,
    ) = _get_groq_settings()

    if not groq_api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing from Streamlit Secrets. "
            "Add your Groq API key under Streamlit Cloud → "
            "Settings → Secrets."
        )

    if not groq_base_url:
        groq_base_url = DEFAULT_GROQ_BASE_URL

    if not groq_vision_model:
        groq_vision_model = DEFAULT_VISION_MODEL

    # --------------------------------------------------------
    # READ IMAGE
    # --------------------------------------------------------

    image_bytes = _get_image_bytes(
        image_bytes
    )

    if not image_bytes:
        raise ValueError(
            "Payment screenshot is empty."
        )

    # --------------------------------------------------------
    # DETECT IMAGE TYPE
    # --------------------------------------------------------

    mime_type = _detect_image_mime(
        image_bytes
    )

    if mime_type is None:
        return {
            "is_payment_screenshot": False,
            "recipient": "",
            "amount": 0,
            "status": "",
            "confidence": "low",
            "message": (
                "The uploaded file is not a supported image. "
                "Please upload a clear JPG, JPEG, PNG, or WEBP "
                "payment screenshot."
            ),
        }

    # --------------------------------------------------------
    # CREATE CLIENT
    # --------------------------------------------------------

    try:
        client = OpenAI(
            api_key=groq_api_key,
            base_url=groq_base_url,
        )

    except Exception as exc:
        raise RuntimeError(
            "Could not initialize the Groq Vision client."
        ) from exc

    # --------------------------------------------------------
    # BASE64 IMAGE
    # --------------------------------------------------------

    encoded_image = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    image_url = (
        f"data:{mime_type};base64,{encoded_image}"
    )

    # --------------------------------------------------------
    # CALL GROQ VISION
    # --------------------------------------------------------

    try:

        response = client.chat.completions.create(
            model=groq_vision_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": PAYMENT_EXTRACTION_PROMPT,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                            },
                        },
                    ],
                }
            ],
            temperature=0,
            max_tokens=500,
            response_format={
                "type": "json_object",
            },
        )

    except Exception as exc:

        raise _format_api_error(
            exc,
            groq_vision_model,
        ) from exc

    # --------------------------------------------------------
    # RESPONSE CHECK
    # --------------------------------------------------------

    if response is None:
        raise RuntimeError(
            "Vision model returned no response."
        )

    if not response.choices:
        raise RuntimeError(
            "Vision model returned no response choices."
        )

    message = response.choices[0].message

    content = message.content

    if not content:
        raise RuntimeError(
            "Vision model returned an empty response."
        )

    # --------------------------------------------------------
    # PARSE JSON
    # --------------------------------------------------------

    data = _extract_json(
        content
    )

    if not data:
        raise RuntimeError(
            "Vision model returned invalid JSON."
        )

    # --------------------------------------------------------
    # PAYMENT FLAG
    # --------------------------------------------------------

    is_payment = data.get(
        "is_payment_screenshot",
        False,
    )

    if isinstance(is_payment, str):

        is_payment = (
            is_payment.strip().lower()
            in {
                "true",
                "yes",
                "1",
            }
        )

    else:

        is_payment = bool(
            is_payment
        )

    # --------------------------------------------------------
    # RECIPIENT
    # --------------------------------------------------------

    recipient = str(
        data.get(
            "recipient",
            "",
        )
    ).strip()

    # --------------------------------------------------------
    # AMOUNT
    # --------------------------------------------------------

    amount = _normalize_amount(
        data.get(
            "amount",
            0,
        )
    )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    status = str(
        data.get(
            "status",
            "",
        )
    ).strip()

    # --------------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------------

    confidence = str(
        data.get(
            "confidence",
            "low",
        )
    ).strip().lower()

    if confidence not in {
        "low",
        "medium",
        "high",
    }:
        confidence = "low"

    # --------------------------------------------------------
    # MESSAGE
    # --------------------------------------------------------

    message_text = str(
        data.get(
            "message",
            "",
        )
    ).strip()

    # --------------------------------------------------------
    # NON-PAYMENT IMAGE
    # --------------------------------------------------------

    if not is_payment:

        recipient = ""
        amount = 0
        status = ""
        confidence = "low"

        if not message_text:

            message_text = (
                "The uploaded image does not appear "
                "to be a payment screenshot."
            )

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    return {
        "is_payment_screenshot": is_payment,
        "recipient": recipient,
        "amount": amount,
        "status": status,
        "confidence": confidence,
        "message": message_text,
    }


# ============================================================
# DETERMINISTIC PAYMENT VALIDATOR
# ============================================================

def verify_payment(
    vision_result: Any,
    required_amount: float = 199,
    expected_recipient: str = "TrekTales",
) -> bool:
    """
    Validate the information extracted by the Vision Agent.

    This does NOT prove that money was actually received.
    It only validates the extracted screenshot information.
    """

    if not isinstance(
        vision_result,
        dict,
    ):
        return False

    # --------------------------------------------------------
    # PAYMENT SCREENSHOT
    # --------------------------------------------------------

    if not vision_result.get(
        "is_payment_screenshot",
        False,
    ):
        return False

    # --------------------------------------------------------
    # AMOUNT
    # --------------------------------------------------------

    amount = _normalize_amount(
        vision_result.get(
            "amount",
            0,
        )
    )

    try:
        required_amount = float(
            required_amount
        )

    except Exception:
        required_amount = 199.0

    if amount < required_amount:
        return False

    # --------------------------------------------------------
    # RECIPIENT
    # --------------------------------------------------------

    recipient = str(
        vision_result.get(
            "recipient",
            "",
        )
    ).strip().lower()

    expected = str(
        expected_recipient
    ).strip().lower()

    if not recipient:
        return False

    if expected and expected not in recipient:
        return False

    # --------------------------------------------------------
    # PAYMENT STATUS
    # --------------------------------------------------------

    status = str(
        vision_result.get(
            "status",
            "",
        )
    ).strip().lower()

    successful_phrases = {
        "successful",
        "success",
        "completed",
        "complete",
        "paid",
        "payment successful",
        "transaction successful",
        "transaction completed",
    }

    if not any(
        phrase in status
        for phrase in successful_phrases
    ):
        return False

    return True


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "analyze_payment_screenshot",
    "verify_payment",
]
