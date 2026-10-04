import base64
import json
import re

from openai import OpenAI

from src.config import (
    GROQ_API_KEY,
    GROQ_BASE_URL,
    GROQ_VISION_MODEL,
)


# ============================================================
# JSON EXTRACTION
# ============================================================

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
        value = json.loads(cleaned)

        if isinstance(value, dict):
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
        value = json.loads(match.group(0))

        if isinstance(value, dict):
            return value

    except Exception:
        pass

    return {}


# ============================================================
# AMOUNT NORMALIZATION
# ============================================================

def _normalize_amount(value):
    """
    Convert a visible amount into a numeric value.
    """

    if value is None:
        return 0

    if isinstance(value, (int, float)):
        return value

    text = str(value).strip()

    match = re.search(
        r"\d+(?:[,.]\d+)*",
        text,
    )

    if not match:
        return 0

    number = match.group(0).replace(",", "")

    try:
        return float(number)

    except ValueError:
        return 0


# ============================================================
# CONVERT UPLOADED FILE TO BYTES
# ============================================================

def _get_image_bytes(uploaded_file):
    """
    Convert a Streamlit UploadedFile or bytes-like object
    into raw bytes.
    """

    if uploaded_file is None:
        return b""

    # Already raw bytes
    if isinstance(uploaded_file, bytes):
        return uploaded_file

    # bytearray
    if isinstance(uploaded_file, bytearray):
        return bytes(uploaded_file)

    # Streamlit UploadedFile
    if hasattr(uploaded_file, "getvalue"):
        data = uploaded_file.getvalue()

        if isinstance(data, bytes):
            return data

    # File-like object
    if hasattr(uploaded_file, "read"):
        data = uploaded_file.read()

        if isinstance(data, bytes):
            return data

    raise ValueError(
        "The uploaded payment file could not be read."
    )


# ============================================================
# IMAGE MIME TYPE
# ============================================================

def _detect_image_mime(image_bytes):
    """
    Detect image type from raw bytes.

    Supported:
    - JPEG
    - PNG
    - WEBP
    """

    if not image_bytes:
        return None

    # JPEG
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"

    # PNG
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
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
# PAYMENT SCREENSHOT ANALYSIS
# ============================================================

def analyze_payment_screenshot(image_bytes):
    """
    Analyze an uploaded payment screenshot using Groq Vision.

    This function only extracts information visible in the image.

    It does NOT:
    - approve payment
    - verify payment authenticity
    - contact a bank
    - contact JazzCash
    - contact Easypaisa
    - guarantee that money was received
    """

    # --------------------------------------------------------
    # API KEY
    # --------------------------------------------------------

    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is missing."
        )

    # --------------------------------------------------------
    # CONVERT STREAMLIT UPLOADED FILE TO BYTES
    # --------------------------------------------------------

    image_bytes = _get_image_bytes(
        image_bytes
    )

    # --------------------------------------------------------
    # EMPTY FILE
    # --------------------------------------------------------

    if not image_bytes:
        raise ValueError(
            "Payment screenshot is empty."
        )

    # --------------------------------------------------------
    # IMAGE TYPE
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
                "Please upload a clear payment screenshot."
            ),
        }

    # --------------------------------------------------------
    # GROQ CLIENT
    # --------------------------------------------------------

    client = OpenAI(
        api_key=GROQ_API_KEY,
        base_url=GROQ_BASE_URL,
    )

    # --------------------------------------------------------
    # ENCODE IMAGE
    # --------------------------------------------------------

    encoded_image = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    image_url = (
        f"data:{mime_type};base64,"
        f"{encoded_image}"
    )

    # --------------------------------------------------------
    # VISION PROMPT
    # --------------------------------------------------------

    prompt = """
You are a payment screenshot information extractor.

Analyze the uploaded image carefully.

First determine whether the image appears to be a
payment or transaction confirmation screenshot.

A payment screenshot may contain visible information such as:

- payment successful
- payment completed
- transaction successful
- amount paid
- recipient or merchant name
- transaction/reference ID
- date/time
- wallet or payment service information

The uploaded image may NOT be a payment screenshot.

It could instead be:

- a GitHub screenshot
- a website screenshot
- a random photograph
- a document
- a social media screenshot
- an unrelated image
- an error screen

If it is not clearly a payment or transaction screenshot,
set:

"is_payment_screenshot": false

Do NOT invent payment information.

Return ONLY valid JSON using exactly this structure:

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

2. Do not guess.

3. Do not infer information that is not visible.

4. If the image is not a payment screenshot:
   - is_payment_screenshot = false
   - recipient = ""
   - amount = 0
   - status = ""
   - confidence = "low"
   - message = "The uploaded image does not appear to be a payment screenshot."

5. If the image clearly appears to be a payment screenshot:
   - is_payment_screenshot = true

6. If recipient is not visible:
   return an empty string.

7. If amount is not visible:
   return 0.

8. If payment status is not visible:
   return an empty string.

9. Confidence must be one of:
   - low
   - medium
   - high

10. Do NOT decide whether the payment is genuine.

11. Do NOT claim that money was actually received.

12. Do NOT approve the payment.

13. Do NOT invent transaction IDs.

14. Do NOT invent dates.

15. Do NOT invent recipient names.

16. Do NOT invent amounts.

17. Return JSON only.
"""

    # --------------------------------------------------------
    # GROQ VISION REQUEST
    # --------------------------------------------------------

    try:
        response = client.chat.completions.create(
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
                                "url": image_url,
                            },
                        },
                    ],
                }
            ],
            temperature=0,
            max_tokens=500,
            response_format={
                "type": "json_object"
            },
        )

    except Exception as exc:

        error_text = str(exc)
        error_lower = error_text.lower()

        # Model unavailable
        if (
            "model_not_found" in error_lower
            or "does not exist" in error_lower
            or "404" in error_text
        ):
            raise RuntimeError(
                "The configured Groq Vision model is unavailable. "
                "Set GROQ_VISION_MODEL to "
                "'qwen/qwen3.8-27b'."
            ) from exc

        # Rate limit
        if (
            "rate_limit" in error_lower
            or "rate limit" in error_lower
            or "429" in error_text
        ):
            raise RuntimeError(
                "Groq Vision is temporarily rate-limited. "
                "Please wait a few seconds and try again."
            ) from exc

        raise RuntimeError(
            f"Vision analysis failed: {error_text}"
        ) from exc

    # --------------------------------------------------------
    # RESPONSE CHECK
    # --------------------------------------------------------

    if not response.choices:
        raise RuntimeError(
            "Vision model returned no response."
        )

    content = (
        response.choices[0]
        .message
        .content
    )

    # --------------------------------------------------------
    # JSON PARSING
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

    if isinstance(
        is_payment,
        str,
    ):
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
    # NORMALIZE VALUES
    # --------------------------------------------------------

    recipient = str(
        data.get(
            "recipient",
            "",
        )
    ).strip()

    amount = _normalize_amount(
        data.get(
            "amount",
            0,
        )
    )

    status = str(
        data.get(
            "status",
            "",
        )
    ).strip()

    confidence = str(
        data.get(
            "confidence",
            "",
        )
    ).strip().lower()

    message = str(
        data.get(
            "message",
            "",
        )
    ).strip()

    # --------------------------------------------------------
    # INVALID PAYMENT IMAGE
    # --------------------------------------------------------

    if not is_payment:

        recipient = ""
        amount = 0
        status = ""
        confidence = "low"

        if not message:
            message = (
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
        "message": message,
    }
