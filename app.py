from pathlib import Path
import base64
import json
import re

import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="TrekTales",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent

FAISS_DIR = ROOT_DIR / "faiss_db"
FAISS_INDEX_PATH = FAISS_DIR / "index.faiss"
METADATA_PATH = FAISS_DIR / "metadata.json"
FAISS_CONFIG_PATH = FAISS_DIR / "config.json"

ASSETS_DIR = ROOT_DIR / "assets"
QR_PATH = ASSETS_DIR / "jazzcash_qr.jpg"


# ============================================================
# TREKTALES SETTINGS
# ============================================================

FREE_DAYS = 1
MAX_TRIP_DAYS = 10
UNLOCK_PRICE = 199

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"
DEFAULT_GROQ_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
DEFAULT_GROQ_BASE_URL = "https://api.groq.com/openai/v1"

TOP_K = 6


# ============================================================
# COLORS
# ============================================================

RED = "#DA2C38"
GREEN = "#226F54"
LIGHT_GREEN = "#87C38F"
CREAM = "#F4F0BB"
BROWN = "#43291F"
WHITE = "#FFFFFF"
DARK_GREEN = "#174936"
BLACK = "#111111"
SOFT_WHITE = "#FFFDF4"
LIGHT_GREY = "#F5F5F5"


# ============================================================
# CSS
# ============================================================

st.markdown(
    f"""
<style>

html, body, [class*="css"] {{
    font-family: Arial, Helvetica, sans-serif;
}}

.stApp {{
    background:
        linear-gradient(
            135deg,
            {SOFT_WHITE} 0%,
            {CREAM} 45%,
            #ffffff 100%
        );
    color: {BLACK};
}}

.main .block-container {{
    max-width: 1250px;
    padding-top: 1.2rem;
    padding-bottom: 3rem;
}}


/* ==========================================================
   SIDEBAR
   ========================================================== */

[data-testid="stSidebar"] {{
    background: {GREEN} !important;
}}

[data-testid="stSidebar"] > div:first-child {{
    background: {GREEN} !important;
}}

[data-testid="stSidebar"] * {{
    color: {WHITE} !important;
}}

.sidebar-brand {{
    text-align: center;
    padding: 10px 5px 20px 5px;
}}

.sidebar-brand-title {{
    font-size: 28px;
    font-weight: 900;
    color: {CREAM} !important;
}}

.sidebar-brand-subtitle {{
    color: {WHITE} !important;
    font-size: 13px;
    opacity: 0.9;
}}

.sidebar-card {{
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 15px;
    padding: 14px;
    margin: 10px 0;
}}

.sidebar-card-title {{
    font-size: 13px;
    font-weight: 800;
    color: {CREAM} !important;
    margin-bottom: 5px;
}}

.sidebar-card-text {{
    font-size: 12px;
    color: {WHITE} !important;
    line-height: 1.5;
}}


/* ==========================================================
   BRAND
   ========================================================== */

.brand-wrapper {{
    text-align: center;
    padding: 5px 0 20px 0;
}}

.brand-title {{
    font-size: clamp(2rem, 5vw, 3.5rem);
    font-weight: 900;
    letter-spacing: -2px;
    color: {GREEN};
    margin: 0;
}}

.brand-title span {{
    color: {RED};
}}

.brand-subtitle {{
    color: {BROWN};
    font-size: clamp(0.9rem, 2vw, 1.1rem);
    margin-top: 5px;
}}


/* ==========================================================
   HERO
   ========================================================== */

.hero-card {{
    background:
        linear-gradient(
            135deg,
            {GREEN},
            {DARK_GREEN}
        );
    border-radius: 25px;
    padding: clamp(25px, 5vw, 50px);
    color: {WHITE};
    box-shadow: 0 15px 45px rgba(34,111,84,0.25);
    margin-bottom: 25px;
    overflow: hidden;
}}

.hero-card h1 {{
    color: {WHITE} !important;
    font-size: clamp(2rem, 5vw, 3.4rem);
    line-height: 1.1;
    margin-bottom: 15px;
    font-weight: 900;
}}

.hero-card p {{
    color: {WHITE} !important;
    font-size: clamp(0.95rem, 2vw, 1.15rem);
    line-height: 1.7;
    max-width: 800px;
}}


/* ==========================================================
   SECTION HEADINGS
   ========================================================== */

.section-title {{
    color: {BROWN};
    font-size: 1.65rem;
    font-weight: 900;
    margin-top: 30px;
    margin-bottom: 15px;
}}

.section-subtitle {{
    color: {GREEN};
    font-size: 0.95rem;
    margin-bottom: 18px;
}}


/* ==========================================================
   FEATURE CARDS
   ========================================================== */

.feature-card {{
    background: {WHITE};
    border: 1px solid rgba(67,41,31,0.12);
    border-radius: 18px;
    padding: 22px;
    min-height: 170px;
    box-shadow: 0 7px 22px rgba(67,41,31,0.08);
}}

.feature-icon {{
    font-size: 30px;
    margin-bottom: 8px;
}}

.feature-card h3 {{
    color: {BROWN} !important;
    font-size: 1.05rem;
    margin-bottom: 8px;
}}

.feature-card p {{
    color: {BLACK} !important;
    font-size: 0.9rem;
    line-height: 1.6;
}}


/* ==========================================================
   INPUTS
   ========================================================== */

label {{
    color: {BROWN} !important;
    font-weight: 700 !important;
}}

.stTextInput input,
.stTextArea textarea,
.stNumberInput input {{
    background: {WHITE} !important;
    color: {BLACK} !important;
    border: 2px solid rgba(34,111,84,0.25) !important;
    border-radius: 11px !important;
}}

.stTextInput input:focus,
.stTextArea textarea:focus,
.stNumberInput input:focus {{
    border-color: {GREEN} !important;
    box-shadow: 0 0 0 2px rgba(135,195,143,0.25) !important;
}}


/* Select boxes */

div[data-baseweb="select"] > div {{
    background: {WHITE} !important;
    color: {BLACK} !important;
    border: 2px solid rgba(34,111,84,0.25) !important;
    border-radius: 11px !important;
}}

div[data-baseweb="select"] span {{
    color: {BLACK} !important;
}}

ul[role="listbox"] {{
    background: {WHITE} !important;
}}

li[role="option"] {{
    color: {BLACK} !important;
}}

li[role="option"]:hover {{
    background: {LIGHT_GREEN} !important;
    color: {BLACK} !important;
}}


/* ==========================================================
   BUTTONS
   ========================================================== */

.stButton > button {{
    background: {RED} !important;
    color: {WHITE} !important;
    border: none !important;
    border-radius: 12px !important;
    min-height: 48px !important;
    font-weight: 800 !important;
    font-size: 15px !important;
    transition: 0.2s ease;
}}

.stButton > button:hover {{
    background: {BROWN} !important;
    color: {WHITE} !important;
    transform: translateY(-1px);
}}


/* ==========================================================
   RESPONSE CARD
   ========================================================== */

.response-card {{
    background: {WHITE};
    border-left: 6px solid {GREEN};
    border-radius: 18px;
    padding: 25px;
    margin: 15px 0;
    box-shadow: 0 8px 25px rgba(67,41,31,0.10);
    overflow-wrap: anywhere;
}}

.response-card,
.response-card *,
.response-card p,
.response-card li,
.response-card span {{
    color: {BLACK} !important;
}}

.response-card h1,
.response-card h2,
.response-card h3,
.response-card h4 {{
    color: {BROWN} !important;
}}

.response-card strong {{
    color: {BROWN} !important;
}}


/* ==========================================================
   SOURCE CARDS
   ========================================================== */

.source-card {{
    background: {CREAM};
    border-left: 4px solid {GREEN};
    padding: 12px 15px;
    border-radius: 10px;
    margin: 7px 0;
}}

.source-card-title {{
    color: {BROWN} !important;
    font-weight: 800;
    font-size: 13px;
}}

.source-card-text {{
    color: {BLACK} !important;
    font-size: 12px;
    line-height: 1.5;
}}


/* ==========================================================
   STATUS
   ========================================================== */

.status-card {{
    background: {WHITE};
    border-radius: 15px;
    padding: 15px;
    border: 1px solid rgba(67,41,31,0.10);
    box-shadow: 0 5px 18px rgba(67,41,31,0.06);
}}

.status-ready {{
    color: {GREEN} !important;
    font-weight: 800;
}}

.status-warning {{
    color: {RED} !important;
    font-weight: 800;
}}


/* ==========================================================
   PAYMENT
   ========================================================== */

.payment-card {{
    background: {WHITE};
    border: 2px solid {LIGHT_GREEN};
    border-radius: 20px;
    padding: 25px;
    box-shadow: 0 8px 25px rgba(34,111,84,0.10);
}}

.payment-title {{
    color: {BROWN} !important;
    font-size: 1.4rem;
    font-weight: 900;
}}

.payment-price {{
    color: {RED} !important;
    font-size: 2rem;
    font-weight: 900;
}}


/* ==========================================================
   FILE UPLOADER — LIGHT GREEN
   ========================================================== */

.stFileUploader {{
    background: {LIGHT_GREEN} !important;
    border: 2px solid {GREEN} !important;
    border-radius: 15px !important;
    padding: 8px !important;
}}

.stFileUploader section {{
    background: {LIGHT_GREEN} !important;
    border-radius: 12px !important;
}}

.stFileUploader section > div {{
    color: {BLACK} !important;
}}

.stFileUploader label,
.stFileUploader label * {{
    color: {BLACK} !important;
}}

.stFileUploader button {{
    background: {LIGHT_GREEN} !important;
    color: {BLACK} !important;
    border: 2px solid {GREEN} !important;
    border-radius: 10px !important;
    font-weight: 800 !important;
}}

.stFileUploader button:hover {{
    background: {GREEN} !important;
    color: {WHITE} !important;
}}


/* ==========================================================
   ALERTS
   ========================================================== */

div[data-testid="stAlert"] {{
    border-radius: 12px !important;
}}


/* ==========================================================
   FOOTER
   ========================================================== */

.footer {{
    text-align: center;
    color: {BROWN};
    opacity: 0.75;
    font-size: 12px;
    padding: 30px 10px 10px;
}}


/* ==========================================================
   MOBILE RESPONSIVE
   ========================================================== */

@media screen and (max-width: 768px) {{

    .main .block-container {{
        padding: 0.8rem 0.75rem 2rem !important;
        max-width: 100% !important;
    }}

    .brand-wrapper {{
        padding-bottom: 15px;
    }}

    .brand-title {{
        font-size: 2.25rem !important;
        letter-spacing: -1px;
    }}

    .brand-subtitle {{
        font-size: 0.85rem !important;
    }}

    .hero-card {{
        padding: 25px 18px !important;
        border-radius: 18px !important;
    }}

    .hero-card h1 {{
        font-size: 2rem !important;
    }}

    .hero-card p {{
        font-size: 0.9rem !important;
    }}

    .feature-card {{
        min-height: auto !important;
        padding: 18px !important;
        margin-bottom: 12px !important;
    }}

    .section-title {{
        font-size: 1.35rem !important;
    }}

    .response-card {{
        padding: 17px !important;
        border-radius: 15px !important;
    }}

    .response-card p,
    .response-card li {{
        font-size: 0.92rem !important;
        line-height: 1.65 !important;
    }}

    .payment-card {{
        padding: 18px !important;
        border-radius: 16px !important;
    }}

    .payment-price {{
        font-size: 1.7rem !important;
    }}

    .stButton > button {{
        min-height: 48px !important;
        width: 100% !important;
    }}

    .stFileUploader,
    .stFileUploader section {{
        background: {LIGHT_GREEN} !important;
        border-color: {GREEN} !important;
    }}

    .stFileUploader button {{
        background: {LIGHT_GREEN} !important;
        color: {BLACK} !important;
        border-color: {GREEN} !important;
    }}

    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input {{
        min-height: 44px !important;
    }}

    [data-testid="stSidebar"] {{
        background: {GREEN} !important;
    }}

    img {{
        max-width: 100% !important;
        height: auto !important;
    }}

    .response-card,
    .source-card,
    .payment-card {{
        overflow-wrap: anywhere !important;
        word-break: normal !important;
    }}

    .main,
    .main > div,
    section.main,
    .block-container {{
        max-width: 100% !important;
        overflow-x: hidden !important;
    }}
}}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_secret(name, default=""):
    """Safely read a Streamlit secret."""
    try:
        value = st.secrets.get(name, default)
    except Exception:
        value = default

    if value is None:
        return default

    return str(value)


def clean_text(value):
    """Clean text without destroying useful Markdown."""
    if value is None:
        return ""

    value = str(value)

    value = value.replace("\x00", "")
    value = value.replace("<script", "")
    value = value.replace("</script>", "")

    return value.strip()


def normalize_metadata(raw):
    """Convert different metadata JSON structures into a list."""
    if isinstance(raw, list):
        return raw

    if isinstance(raw, dict):
        for key in ["records", "metadata", "chunks", "documents", "data"]:
            value = raw.get(key)

            if isinstance(value, list):
                return value

    return []


def record_text(record):
    """Extract text from a metadata record."""
    if not isinstance(record, dict):
        return ""

    for key in [
        "text",
        "content",
        "chunk",
        "document",
        "page_content",
    ]:
        value = record.get(key)

        if value:
            return clean_text(value)

    return ""


def record_source(record):
    """Extract source filename."""
    if not isinstance(record, dict):
        return "Unknown source"

    for key in [
        "source",
        "filename",
        "file_name",
        "file",
        "document_name",
    ]:
        value = record.get(key)

        if value:
            value = str(value)

            # Only show filename rather than full path.
            return Path(value).name

    return "Unknown source"


def record_page(record):
    """Extract page if available."""
    if not isinstance(record, dict):
        return ""

    for key in ["page", "page_number", "page_num"]:
        value = record.get(key)

        if value not in [None, ""]:
            return str(value)

    return ""


@st.cache_data(show_spinner=False)
def load_metadata():
    """Load FAISS metadata."""
    if not METADATA_PATH.exists():
        return []

    try:
        with open(METADATA_PATH, "r", encoding="utf-8") as file:
            raw = json.load(file)

        return normalize_metadata(raw)

    except Exception:
        return []


@st.cache_resource(show_spinner=False)
def load_faiss_resources():
    """
    Load FAISS and SentenceTransformer lazily.

    Heavy dependencies are imported only when the user
    generates a trip, preventing startup failures.
    """

    import faiss
    from sentence_transformers import SentenceTransformer

    if not FAISS_INDEX_PATH.exists():
        raise FileNotFoundError(
            f"FAISS index not found: {FAISS_INDEX_PATH}"
        )

    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            f"Metadata file not found: {METADATA_PATH}"
        )

    index = faiss.read_index(str(FAISS_INDEX_PATH))

    metadata = load_metadata()

    if index.ntotal == 0:
        raise RuntimeError("The FAISS index is empty.")

    if len(metadata) == 0:
        raise RuntimeError("The metadata file contains no records.")

    if index.ntotal != len(metadata):
        raise RuntimeError(
            f"FAISS/metadata mismatch: "
            f"index contains {index.ntotal} vectors but "
            f"metadata contains {len(metadata)} records."
        )

    model = SentenceTransformer(DEFAULT_EMBEDDING_MODEL)

    return index, metadata, model


def keyword_score(query, text):
    """Small keyword score used to improve retrieval."""
    query_words = set(
        re.findall(r"\b[a-zA-Z0-9]{3,}\b", query.lower())
    )

    if not query_words:
        return 0.0

    text_words = set(
        re.findall(r"\b[a-zA-Z0-9]{3,}\b", text.lower())
    )

    if not text_words:
        return 0.0

    overlap = query_words.intersection(text_words)

    return len(overlap) / max(len(query_words), 1)


def retrieve_context(query, top_k=TOP_K):
    """Retrieve relevant knowledge-base chunks."""

    index, metadata, model = load_faiss_resources()

    import numpy as np

    embedding = model.encode(
        [query],
        normalize_embeddings=True,
    )

    embedding = np.asarray(
        embedding,
        dtype="float32",
    )

    k = min(top_k, index.ntotal)

    scores, indices = index.search(
        embedding,
        k,
    )

    candidates = []

    for semantic_score, index_id in zip(
        scores[0],
        indices[0],
    ):
        if index_id < 0:
            continue

        if index_id >= len(metadata):
            continue

        record = metadata[index_id]

        text = record_text(record)

        if not text:
            continue

        source = record_source(record)
        page = record_page(record)

        semantic = float(semantic_score)

        keyword = keyword_score(
            query,
            text,
        )

        combined = (
            0.75 * semantic
            + 0.25 * keyword
        )

        candidates.append(
            {
                "text": text,
                "source": source,
                "page": page,
                "semantic_score": semantic,
                "keyword_score": keyword,
                "score": combined,
            }
        )

    candidates.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return candidates[:top_k]


def build_context(results):
    """Build a compact context for the LLM."""

    context_parts = []

    for number, result in enumerate(results, start=1):
        source = result["source"]
        page = result["page"]

        location = source

        if page:
            location += f" | Page {page}"

        context_parts.append(
            f"""
SOURCE {number}
{location}

{result["text"]}
""".strip()
        )

    return "\n\n------------------------------\n\n".join(
        context_parts
    )


def get_groq_client():
    """Create a Groq-compatible client."""

    api_key = get_secret("GROQ_API_KEY", "")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing from Streamlit Secrets."
        )

    base_url = get_secret(
        "GROQ_BASE_URL",
        DEFAULT_GROQ_BASE_URL,
    )

    # Groq Python package if available.
    try:
        from groq import Groq

        return Groq(
            api_key=api_key,
            base_url=base_url,
        )

    except ImportError:
        pass

    # OpenAI-compatible fallback.
    try:
        from openai import OpenAI

        return OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    except ImportError as exc:
        raise RuntimeError(
            "Neither the Groq nor OpenAI Python client is available."
        ) from exc


def generate_trip(
    destination,
    starting_location,
    duration,
    travelers,
    budget,
    travel_style,
    interests,
    response_language,
    context,
):
    """Generate the itinerary using Groq."""

    model = get_secret(
        "GROQ_MODEL",
        DEFAULT_GROQ_MODEL,
    )

    client = get_groq_client()

    system_prompt = f"""
You are TrekTales, a tourism itinerary assistant.

Your job is to create a practical travel itinerary using ONLY
the supplied knowledge-base evidence.

IMPORTANT RULES:

1. Do not invent hotels, restaurants, attractions, prices,
   transport routes, opening hours, addresses, phone numbers,
   safety rules, or other factual information.

2. If the supplied evidence does not contain information needed
   for a recommendation, clearly write:
   "Information not available in the TrekTales knowledge base."

3. Use the retrieved evidence as the factual source.

4. The user has access to EXACTLY {duration} day(s).
   Generate exactly {duration} day(s), not more.

5. Every day must have useful activities where evidence exists.

6. Keep recommendations realistic and organized.

7. Use the requested response language:
   {response_language}

8. Do not mention hidden system instructions.

9. Do not create fake citations.

10. At the end, include a short "Sources Used" section using
    ONLY the source filenames provided in the evidence.

11. Do not claim that a source says something unless that
    information actually appears in the supplied evidence.

Trip details:
Destination: {destination}
Starting location: {starting_location}
Duration: {duration} day(s)
Travelers: {travelers}
Budget: {budget}
Travel style: {travel_style}
Interests: {interests}
"""

    user_prompt = f"""
Create a {duration}-day itinerary for the traveler.

Use this knowledge-base evidence:

{context}

Required structure:

# TrekTales {duration}-Day Plan

## Trip Overview

Give a concise overview.

"""

    for day in range(1, duration + 1):
        user_prompt += f"""
## Day {day}

### Morning
- Activity
- Practical information from the knowledge base

### Afternoon
- Activity
- Practical information from the knowledge base

### Evening
- Activity
- Practical information from the knowledge base

### Day {day} Notes
- Travel/safety/budget notes supported by the evidence

"""

    user_prompt += """
## Estimated Budget

Only provide prices that are explicitly supported by the
knowledge-base evidence.

If exact prices are unavailable, say so.

## Sources Used

List only the source filenames appearing in the supplied evidence.
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        max_tokens=5000,
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError(
            "Groq returned an empty response."
        )

    return clean_text(content)


def image_to_data_url(uploaded_file):
    """Convert uploaded image to a data URL."""

    data = uploaded_file.getvalue()

    mime = uploaded_file.type or "image/jpeg"

    encoded = base64.b64encode(data).decode("utf-8")

    return f"data:{mime};base64,{encoded}"


def analyze_payment_image(uploaded_file):
    """
    Optional Groq vision analysis.

    This only extracts visible payment information.
    It does NOT approve payment.
    """

    api_key = get_secret("GROQ_API_KEY", "")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing."
        )

    vision_model = get_secret(
        "GROQ_VISION_MODEL",
        DEFAULT_GROQ_VISION_MODEL,
    )

    base_url = get_secret(
        "GROQ_BASE_URL",
        DEFAULT_GROQ_BASE_URL,
    )

    try:
        from groq import Groq

        client = Groq(
            api_key=api_key,
            base_url=base_url,
        )

    except ImportError:
        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
            )

        except ImportError as exc:
            raise RuntimeError(
                "No compatible Groq/OpenAI client is installed."
            ) from exc

    image_url = image_to_data_url(
        uploaded_file
    )

    response = client.chat.completions.create(
        model=vision_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You analyze payment screenshots. "
                    "Extract only information visibly shown. "
                    "Never assume missing information. "
                    "Return JSON only."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """
Extract these visible fields:

{
  "recipient": "",
  "amount": "",
  "status": "",
  "transaction_id": "",
  "confidence": ""
}

Do not approve or verify the payment.
Only report what is visibly present.
""",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                        },
                    },
                ],
            },
        ],
        max_tokens=800,
    )

    content = response.choices[0].message.content

    if not content:
        return {}

    # Try JSON extraction.
    try:
        cleaned = content.strip()

        cleaned = re.sub(
            r"^```json",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r"^```",
            "",
            cleaned,
        )

        cleaned = re.sub(
            r"```$",
            "",
            cleaned,
        )

        return json.loads(
            cleaned.strip()
        )

    except Exception:
        return {
            "raw_analysis": content
        }


def verify_payment_data(payment_data):
    """
    Deterministic payment verification.

    Vision never decides whether payment is valid.
    """

    if not isinstance(payment_data, dict):
        return False, "Payment information could not be read."

    expected_recipient = get_secret(
        "EXPECTED_PAYMENT_RECIPIENT",
        "",
    ).strip()

    recipient = str(
        payment_data.get(
            "recipient",
            "",
        )
    ).strip()

    amount_raw = str(
        payment_data.get(
            "amount",
            "",
        )
    )

    status = str(
        payment_data.get(
            "status",
            "",
        )
    ).strip().lower()

    # Extract numeric amount.
    numbers = re.findall(
        r"\d+(?:\.\d+)?",
        amount_raw,
    )

    amount = None

    if numbers:
        try:
            amount = float(numbers[0])
        except Exception:
            amount = None

    valid_statuses = {
        "successful",
        "success",
        "completed",
        "complete",
        "paid",
        "sent",
    }

    if amount is None:
        return False, "Payment amount could not be verified."

    if amount < UNLOCK_PRICE:
        return (
            False,
            f"Payment amount must be at least Rs. {UNLOCK_PRICE}.",
        )

    if status not in valid_statuses:
        return (
            False,
            "Payment status was not shown as successful.",
        )

    if expected_recipient:
        if recipient.lower() != expected_recipient.lower():
            return (
                False,
                "Payment recipient does not match the configured recipient.",
            )

    return True, "Payment passed the deterministic checks."


def calculate_accessible_days(
    requested_days,
    payment_verified,
):
    """Enforce the free/premium day limit."""

    requested_days = max(
        1,
        min(
            int(requested_days),
            MAX_TRIP_DAYS,
        ),
    )

    if requested_days <= FREE_DAYS:
        return requested_days

    if payment_verified:
        return requested_days

    return FREE_DAYS


def show_sources(results):
    """Display deterministic sources."""

    if not results:
        return

    st.markdown(
        '<div class="section-title">📚 Knowledge Sources</div>',
        unsafe_allow_html=True,
    )

    seen = set()

    for result in results:
        source = result["source"]
        page = result["page"]

        key = (
            source,
            page,
        )

        if key in seen:
            continue

        seen.add(key)

        location = source

        if page:
            location += f" — Page {page}"

        st.markdown(
            f"""
            <div class="source-card">
                <div class="source-card-title">
                    📄 {source}
                </div>
                <div class="source-card-text">
                    {location}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# SESSION STATE
# ============================================================

if "payment_verified" not in st.session_state:
    st.session_state.payment_verified = False

if "payment_analysis" not in st.session_state:
    st.session_state.payment_analysis = None

if "trip_result" not in st.session_state:
    st.session_state.trip_result = None

if "trip_sources" not in st.session_state:
    st.session_state.trip_sources = []

if "generated_days" not in st.session_state:
    st.session_state.generated_days = 0


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-brand-title">🌿 TrekTales</div>
            <div class="sidebar-brand-subtitle">
                AI Travel Planner
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="sidebar-card">
            <div class="sidebar-card-title">
                🔓 ACCESS MODEL
            </div>
            <div class="sidebar-card-text">
                Day 1 is free.<br>
                Days 2–10 require a one-time unlock.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    response_language = st.selectbox(
        "Response Language",
        [
            "English",
            "Urdu",
            "Roman Urdu",
        ],
        index=0,
    )

    st.markdown(
        """
        <div class="sidebar-card">
            <div class="sidebar-card-title">
                🤖 AI AGENTS
            </div>
            <div class="sidebar-card-text">
                🧭 Itinerary Planner<br>
                🔎 Knowledge Retriever<br>
                🛡️ Safety Assistant<br>
                💳 Payment Vision
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    model_name = get_secret(
        "GROQ_MODEL",
        DEFAULT_GROQ_MODEL,
    )

    st.markdown(
        f"""
        <div class="sidebar-card">
            <div class="sidebar-card-title">
                ⚡ AI MODEL
            </div>
            <div class="sidebar-card-text">
                {model_name}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# BRAND
# ============================================================

st.markdown(
    """
    <div class="brand-wrapper">
        <div class="brand-title">
            Trek<span>Tales</span> 🌿
        </div>
        <div class="brand-subtitle">
            AI-powered travel planning grounded in your knowledge base
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="hero-card">
        <h1>Plan your journey.<br>Explore with confidence.</h1>
        <p>
            TrekTales creates personalized travel itineraries using
            your tourism knowledge base and Groq-powered AI.
            Recommendations are grounded in retrieved evidence
            rather than invented travel information.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# FEATURES
# ============================================================

feature_col1, feature_col2, feature_col3 = st.columns(3)

with feature_col1:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">🧠</div>
            <h3>Knowledge-Grounded AI</h3>
            <p>
                TrekTales retrieves relevant information from
                the tourism knowledge base before generating
                your itinerary.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with feature_col2:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">🗺️</div>
            <h3>Personalized Trips</h3>
            <p>
                Choose your destination, duration, travelers,
                budget and interests to build a customized plan.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with feature_col3:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">🛡️</div>
            <h3>Evidence First</h3>
            <p>
                TrekTales avoids inventing tourism facts when
                the required information is not available.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# TRIP PLANNER
# ============================================================

st.markdown(
    '<div class="section-title">🧭 Build Your Trip</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-subtitle">Tell TrekTales what kind of journey you want.</div>',
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)

with col1:

    destination = st.text_input(
        "Destination",
        placeholder="e.g. Rawalpindi",
    )

with col2:

    starting_location = st.text_input(
        "Starting Location",
        placeholder="e.g. Islamabad",
    )


col3, col4, col5 = st.columns(3)

with col3:

    duration = st.number_input(
        "Trip Duration",
        min_value=1,
        max_value=MAX_TRIP_DAYS,
        value=1,
        step=1,
        help="Choose between 1 and 10 days.",
    )

    st.caption(
        f"🗓️ {int(duration)} day"
        f"{'s' if int(duration) != 1 else ''} selected"
    )

with col4:

    travelers = st.number_input(
        "Travelers",
        min_value=1,
        max_value=20,
        value=2,
        step=1,
    )

with col5:

    budget = st.selectbox(
        "Budget Level",
        [
            "Budget — Rs. 3,000–7,000/day",
            "Standard — Rs. 7,000–15,000/day",
            "Comfort — Rs. 15,000–30,000/day",
            "Premium — Rs. 30,000+/day",
        ],
        index=1,
    )


travel_style = st.selectbox(
    "Travel Style",
    [
        "Balanced",
        "Adventure",
        "Relaxed",
        "Family",
        "Cultural",
        "Nature",
        "Food & Exploration",
        "Budget Friendly",
        "Luxury",
    ],
)


interests = st.text_area(
    "Interests",
    placeholder=(
        "e.g. historical places, food, nature, "
        "photography, hiking, family activities"
    ),
    height=100,
)


# ============================================================
# SYSTEM STATUS
# ============================================================

st.markdown(
    '<div class="section-title">⚙️ System Status</div>',
    unsafe_allow_html=True,
)

status1, status2, status3 = st.columns(3)

groq_key_exists = bool(
    get_secret("GROQ_API_KEY", "").strip()
)

with status1:

    if groq_key_exists:
        st.markdown(
            f"""
            <div class="status-card">
                <div class="status-ready">
                    🟢 Groq API Key Ready
                </div>
                <small>GroqCloud connection configured.</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="status-card">
                <div class="status-warning">
                    🔴 Groq API Key Missing
                </div>
                <small>Add GROQ_API_KEY to Streamlit Secrets.</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

with status2:

    faiss_ready = (
        FAISS_INDEX_PATH.exists()
        and METADATA_PATH.exists()
    )

    if faiss_ready:
        st.markdown(
            """
            <div class="status-card">
                <div class="status-ready">
                    🟢 FAISS Ready
                </div>
                <small>Knowledge base index detected.</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="status-card">
                <div class="status-warning">
                    🔴 FAISS Missing
                </div>
                <small>
                    Check the faiss_db folder.
                </small>
            </div>
            """,
            unsafe_allow_html=True,
        )

with status3:

    st.markdown(
        """
        <div class="status-card">
            <div class="status-ready">
                🟢 Agent System
            </div>
            <small>Planner + RAG + payment workflow.</small>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# PAYMENT STATE MESSAGE
# ============================================================

requested_days = int(duration)

if requested_days > FREE_DAYS:

    if st.session_state.payment_verified:

        st.success(
            f"🔓 Premium unlocked — your {requested_days}-day "
            "trip can now be generated."
        )

    else:

        st.info(
            f"🔒 You selected {requested_days} days. "
            f"Day 1 is free. Days 2–{requested_days} require "
            f"the Rs. {UNLOCK_PRICE} unlock."
        )


# ============================================================
# GENERATE TRIP
# ============================================================

st.markdown(
    '<div class="section-title">✨ Generate Your Journey</div>',
    unsafe_allow_html=True,
)

generate_button = st.button(
    "🌿 Generate My Trip",
    use_container_width=True,
)


if generate_button:

    if not destination.strip():

        st.error(
            "Please enter a destination."
        )

    elif not starting_location.strip():

        st.error(
            "Please enter your starting location."
        )

    elif not interests.strip():

        st.warning(
            "Please enter at least one interest."
        )

    elif not groq_key_exists:

        st.error(
            "GROQ_API_KEY is missing. "
            "Add your GroqCloud API key in Streamlit Secrets."
        )

    elif not faiss_ready:

        st.error(
            "FAISS knowledge base files are missing. "
            "Expected faiss_db/index.faiss and faiss_db/metadata.json."
        )

    else:

        payment_verified = (
            st.session_state.payment_verified
        )

        accessible_days = calculate_accessible_days(
            requested_days,
            payment_verified,
        )

        # ----------------------------------------------------
        # IMPORTANT:
        # The AI receives accessible_days, not requested_days.
        # Therefore it cannot generate hidden premium days.
        # ----------------------------------------------------

        with st.spinner(
            f"🔎 Searching the TrekTales knowledge base "
            f"for your {accessible_days}-day trip..."
        ):

            try:

                retrieval_query = f"""
                Destination: {destination}
                Starting location: {starting_location}
                Duration: {accessible_days} days
                Travelers: {travelers}
                Budget: {budget}
                Travel style: {travel_style}
                Interests: {interests}
                """

                results = retrieve_context(
                    retrieval_query,
                    top_k=TOP_K,
                )

                if not results:

                    st.error(
                        "No relevant information was found in "
                        "the TrekTales knowledge base."
                    )

                else:

                    context = build_context(
                        results
                    )

                    with st.spinner(
                        "🤖 Groq is creating your itinerary..."
                    ):

                        trip = generate_trip(
                            destination=destination,
                            starting_location=starting_location,
                            duration=accessible_days,
                            travelers=travelers,
                            budget=budget,
                            travel_style=travel_style,
                            interests=interests,
                            response_language=response_language,
                            context=context,
                        )

                    st.session_state.trip_result = trip
                    st.session_state.trip_sources = results
                    st.session_state.generated_days = accessible_days

                    if (
                        requested_days > FREE_DAYS
                        and not payment_verified
                    ):

                        st.success(
                            f"Day 1 generated successfully. "
                            f"Unlock the remaining days for "
                            f"Rs. {UNLOCK_PRICE}."
                        )

                    else:

                        st.success(
                            f"Your complete {accessible_days}-day "
                            "TrekTales itinerary is ready!"
                        )

            except Exception as exc:

                st.error(
                    "The trip could not be generated."
                )

                st.code(
                    str(exc),
                    language="text",
                )


# ============================================================
# DISPLAY TRIP RESULT
# ============================================================

if st.session_state.trip_result:

    st.markdown(
        '<div class="section-title">🗺️ Your TrekTales Journey</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="response-card">
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        st.session_state.trip_result
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    show_sources(
        st.session_state.trip_sources
    )


# ============================================================
# PREMIUM PAYMENT
# ============================================================

if requested_days >= 2:

    st.markdown(
        '<div class="section-title">🔓 Unlock Premium Days</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.payment_verified:

        st.markdown(
            f"""
            <div class="payment-card">
                <div class="payment-title">
                    ✅ Premium Access Active
                </div>

                <p style="color:{BLACK};">
                    Payment has passed the deterministic
                    verification checks.
                </p>

                <div class="payment-price">
                    Rs. {UNLOCK_PRICE}
                </div>

                <p style="color:{BLACK};">
                    You can now generate all requested days.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        payment_left, payment_right = st.columns(
            [1, 1.3]
        )

        with payment_left:

            st.markdown(
                f"""
                <div class="payment-card">
                    <div class="payment-title">
                        🌿 TrekTales Premium
                    </div>

                    <p style="color:{BLACK};">
                        Unlock Days 2–10 for:
                    </p>

                    <div class="payment-price">
                        Rs. {UNLOCK_PRICE}
                    </div>

                    <p style="color:{BLACK};">
                        One-time unlock for your selected trip.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if QR_PATH.exists():

                st.image(
                    str(QR_PATH),
                    caption="Scan to make your payment",
                    use_container_width=True,
                )

            else:

                st.warning(
                    "Payment QR image was not found at "
                    "assets/jazzcash_qr.jpg"
                )

        with payment_right:

            st.markdown(
                f"""
                <div class="payment-card">
                    <div class="payment-title">
                        📤 Upload Payment Screenshot
                    </div>

                    <p style="color:{BLACK};">
                        Pay Rs. {UNLOCK_PRICE} and upload the
                        payment screenshot below.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            payment_file = st.file_uploader(
                "Upload payment screenshot",
                type=[
                    "jpg",
                    "jpeg",
                    "png",
                    "webp",
                ],
                key="payment_upload",
            )

            if payment_file is not None:

                analyze_button = st.button(
                    "🔍 Analyze Payment Screenshot",
                    use_container_width=True,
                )

                if analyze_button:

                    with st.spinner(
                        "🔎 Reading payment screenshot..."
                    ):

                        try:

                            analysis = analyze_payment_image(
                                payment_file
                            )

                            st.session_state.payment_analysis = analysis

                            if analysis:

                                st.markdown(
                                    f"""
                                    <div class="response-card">
                                        <h3>
                                            Payment Screenshot Analysis
                                        </h3>
                                        <p>
                                            The AI has extracted
                                            the visible payment
                                            information.
                                        </p>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                                st.json(
                                    analysis
                                )

                                verified, message = (
                                    verify_payment_data(
                                        analysis
                                    )
                                )

                                if verified:

                                    st.session_state.payment_verified = True

                                    st.success(
                                        "✅ Payment passed the "
                                        "deterministic verification checks."
                                    )

                                    st.rerun()

                                else:

                                    st.error(
                                        f"❌ Payment was not verified: "
                                        f"{message}"
                                    )

                                    st.info(
                                        "The AI screenshot analysis "
                                        "does not automatically approve "
                                        "payment."
                                    )

                            else:

                                st.error(
                                    "No payment information could "
                                    "be extracted."
                                )

                        except Exception as exc:

                            st.error(
                                "Payment screenshot analysis failed."
                            )

                            st.code(
                                str(exc),
                                language="text",
                            )


# ============================================================
# PREMIUM NOTICE
# ============================================================

if (
    requested_days > FREE_DAYS
    and not st.session_state.payment_verified
):

    st.markdown(
        f"""
        <div class="payment-card" style="margin-top:20px;">
            <div class="payment-title">
                🔒 Premium Days Locked
            </div>

            <p style="color:{BLACK};">
                You requested <strong>{requested_days} days</strong>.
                TrekTales currently gives you Day 1 for free.
            </p>

            <p style="color:{BLACK};">
                Complete the Rs. {UNLOCK_PRICE} payment verification
                to generate Days 2–{requested_days}.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# DISCLAIMER
# ============================================================

st.markdown(
    f"""
    <div style="
        background:{CREAM};
        border-left:5px solid {RED};
        border-radius:12px;
        padding:15px;
        margin-top:30px;
    ">
        <strong style="color:{BROWN};">
            ⚠️ TrekTales Information Notice
        </strong>

        <p style="
            color:{BLACK};
            margin-bottom:0;
            font-size:13px;
            line-height:1.6;
        ">
            TrekTales generates travel suggestions from its
            available knowledge base. Information may be incomplete
            or change over time. Always independently confirm
            important prices, availability, safety conditions,
            transport schedules and local requirements before travel.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        🌿 TrekTales — AI-Powered Tourism Planner
        <br>
        Built with Streamlit • FAISS • Sentence Transformers • Groq
    </div>
    """,
    unsafe_allow_html=True,
)
