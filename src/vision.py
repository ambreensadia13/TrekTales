````python
import base64
import json
import re

import streamlit as st
from openai import OpenAI


# ============================================================
# DEFAULT SETTINGS
# ============================================================

DEFAULT_GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_VISION_MODEL = "qwen/qwen3.8-27b"


# ============================================================
# SECRET HELPERS
# ============================================================

def _get_secret(name, default=""):
    """Read a value directly from Streamlit Secrets."""

    try:
        value = st.secrets.get(name, default)

        if value is None:
            return default

        return str(value).strip()

    except Exception:
        return default


def _get_groq_settings():
    """Get the current Groq configuration from Streamlit Secrets."""

    api_key = _get_secret("GROQ_API_KEY", "")

    base_url = _get_secret(
        "GROQ_BASE_URL",
        DEFAULT_GROQ_BASE_URL,
    )

    vision_model = _get_secret(
        "GROQ_VISION_MODEL",
        DEFAULT_VISION_MODEL,
    )

    return api_key, base_url, vision_model


# ============================================================
# JSON EXTRACTION
# ============================================================

def _extract_json(text):
    """Safely extract a JSON object from model output."""

    if not text:
        return {}

    cleaned = str(text).strip()

    # Remove markdown JSON fences.
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

    # Try direct JSON parsing first.
    try:
        value = json.loads(cleaned)

        if isinstance(value, dict):
            return value

    except Exception:
        pass

    # Try extracting JSON from surrounding text.
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
    Convert values such as:

        199
        "199"
        "Rs. 199"
        "PKR 199"
        "1,199"

    into a numeric value.
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
# IMAGE BYTES
# ============================================================

def _get_image_bytes(uploaded_file):
    """Convert an uploaded file or bytes object into image bytes."""

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

def _detect_image_mime(image_bytes):
    """Detect supported image type from its file signature."""

    if not image_bytes:
        return None

    # JPEG
    if image_bytes.startswith(b"\xff\xd8\xff"):
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
You are the Vision Agent for a travel application.

Your task is ONLY to extract information visibly present
in a payment or transaction screenshot.

First determine whether the uploaded image appears to be
a payment or transaction confirmation screenshot.

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


# ============================================================
# MAIN VISION FUNCTION
# ============================================================

def analyze_payment_screenshot(image_bytes):
    """
    Analyze a payment screenshot using the configured
    Groq Vision model.

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
    # LOAD CURRENT SECRETS
    # --------------------------------------------------------

    (
        groq_api_key,
        groq_base_url,
        groq_vision_model,
    ) = _get_groq_settings()

    if not groq_api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing from Streamlit Secrets. "
            "Add your current Groq API key under Settings → Secrets."
        )

    if not groq_base_url:
        groq_base_url = DEFAULT_GROQ_BASE_URL

    if not groq_vision_model:
        groq_vision_model = DEFAULT_VISION_MODEL

    # --------------------------------------------------------
    # READ IMAGE
    # --------------------------------------------------------

    image_bytes = _get_image_bytes(image_bytes)

    if not image_bytes:
        raise ValueError(
            "Payment screenshot is empty."
        )

    # --------------------------------------------------------
    # DETECT IMAGE TYPE
    # --------------------------------------------------------

    mime_type = _detect_image_mime(image_bytes)

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
    # CREATE GROQ CLIENT
    # --------------------------------------------------------

    try:
        client = OpenAI(
            api_key=groq_api_key,
            base_url=groq_base_url,
        )

    except Exception as exc:
        raise RuntimeError(
            f"Could not initialize the Groq Vision client: {exc}"
        ) from exc

    # --------------------------------------------------------
    # ENCODE IMAGE
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
                "type": "json_object"
            },
        )

    except Exception as exc:
        error_text = str(exc)
        error_lower = error_text.lower()

        # ----------------------------------------------------
        # AUTHENTICATION ERROR
        # ----------------------------------------------------

        if (
            "401" in error_text
            or "invalid api key" in error_lower
            or "invalid_api_key" in error_lower
            or "authentication" in error_lower
            or "unauthorized" in error_lower
        ):
            raise RuntimeError(
                "Groq authentication failed for the Vision Agent. "
                "Your GROQ_API_KEY in Streamlit Secrets is invalid, "
                "expired, revoked, or not being accepted by Groq. "
                "Create a new Groq API key, update Streamlit Secrets, "
                "and restart/redeploy the app."
            ) from exc

        # ----------------------------------------------------
        # MODEL ERROR
        # ----------------------------------------------------

        if (
            "404" in error_text
            or "model_not_found" in error_lower
            or "does not exist" in error_lower
            or "not found" in error_lower
        ):
            raise RuntimeError(
                "The configured Groq Vision model is unavailable. "
                "Check GROQ_VISION_MODEL in Streamlit Secrets. "
                f"Current configured model: {groq_vision_model}"
            ) from exc

        # ----------------------------------------------------
        # RATE LIMIT ERROR
        # ----------------------------------------------------

        if (
            "429" in error_text
            or "rate limit" in error_lower
            or "rate_limit" in error_lower
            or "too many requests" in error_lower
        ):
            raise RuntimeError(
                "Groq Vision is temporarily rate-limited. "
                "Please wait a few seconds and try again."
            ) from exc

        # ----------------------------------------------------
        # BAD REQUEST
        # ----------------------------------------------------

        if (
            "400" in error_text
            or "bad request" in error_lower
        ):
            raise RuntimeError(
                "Groq rejected the Vision Agent request. "
                "Check the configured Vision model and "
                "the uploaded image format."
            ) from exc

        # ----------------------------------------------------
        # OTHER ERROR
        # ----------------------------------------------------

        raise RuntimeError(
            f"Vision analysis failed: {error_text}"
        ) from exc

    # --------------------------------------------------------
    # CHECK RESPONSE
    # --------------------------------------------------------

    if not response:
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

    data = _extract_json(content)

    if not data:
        raise RuntimeError(
            "Vision model returned invalid JSON."
        )

    # --------------------------------------------------------
    # NORMALIZE RESULT
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
        is_payment = bool(is_payment)

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

    message_text = str(
        data.get(
            "message",
            "",
        )
    ).strip()

    # --------------------------------------------------------
    # NORMALIZE CONFIDENCE
    # --------------------------------------------------------

    if confidence not in {
        "low",
        "medium",
        "high",
    }:
        confidence = "low"

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
    vision_result,
    required_amount=199,
    expected_recipient="TrekTales",
):
    """
    Validate information extracted from the screenshot.

    This does NOT prove that money was actually received.
    It only checks the information extracted by the Vision Agent.
    """

    if not isinstance(vision_result, dict):
        return False

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
        required_amount = 199

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

    successful_statuses = {
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
        value in status
        for value in successful_statuses
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
````
