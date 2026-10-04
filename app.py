from pathlib import Path
import json
import re
import html
import base64
from typing import Any, Dict, List, Tuple

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
# COLORS
# ============================================================

RED = "#DA2C38"
GREEN = "#226F54"
LIGHT_GREEN = "#87C38F"
CREAM = "#F4F0BB"
BROWN = "#43291F"
WHITE = "#FFFFFF"
BLACK = "#111111"
DARK_GREEN = "#174936"
LIGHT_BACKGROUND = "#FAF9F1"


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
# APP SETTINGS
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
# EXACT 8-AGENT ARCHITECTURE
# ============================================================

AGENTS = [
    (
        "01",
        "🎯 Master Orchestrator",
        "Coordinates the complete TrekTales workflow and controls the agent sequence.",
    ),
    (
        "02",
        "🔎 Knowledge Agent",
        "Retrieves tourism evidence from the FAISS knowledge base.",
    ),
    (
        "03",
        "🗺️ Planner Agent",
        "Builds the day-by-day itinerary from retrieved evidence.",
    ),
    (
        "04",
        "💰 Budget Agent",
        "Handles budget-level planning and supported cost information.",
    ),
    (
        "05",
        "🛡️ Safety Agent",
        "Adds travel and safety information supported by the knowledge base.",
    ),
    (
        "06",
        "📝 Summarizer Agent",
        "Organizes the final response and source information.",
    ),
    (
        "07",
        "💳 Payment Agent",
        "Controls premium access and payment verification state.",
    ),
    (
        "08",
        "👁️ Vision Agent",
        "Extracts visible payment information from uploaded screenshots.",
    ),
]


# ============================================================
# SESSION STATE
# ============================================================

if "payment_verified" not in st.session_state:
    st.session_state.payment_verified = False

if "payment_result" not in st.session_state:
    st.session_state.payment_result = None

if "last_plan" not in st.session_state:
    st.session_state.last_plan = ""

if "last_sources" not in st.session_state:
    st.session_state.last_sources = []

if "generate_clicked" not in st.session_state:
    st.session_state.generate_clicked = False


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
                {LIGHT_BACKGROUND} 0%,
                {CREAM} 48%,
                #ffffff 100%
            );
        color: {BLACK};
    }}

    /* Main text */
    p, span, label, div {{
        color: {BLACK};
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background: {GREEN};
    }}

    [data-testid="stSidebar"] * {{
        color: {WHITE} !important;
    }}

    /* Main title */
    .main-title {{
        font-size: 3.2rem;
        font-weight: 900;
        color: {BROWN};
        margin-bottom: 0.15rem;
        line-height: 1.05;
    }}

    .main-subtitle {{
        font-size: 1.05rem;
        color: {BLACK};
        line-height: 1.6;
        max-width: 850px;
        margin-bottom: 1.2rem;
    }}

    /* Native Streamlit inputs */
    div[data-baseweb="input"] {{
        background: {WHITE};
        border-radius: 10px;
    }}

    div[data-baseweb="select"] > div {{
        background: {WHITE};
        color: {BLACK};
        border-radius: 10px;
    }}

    div[data-baseweb="select"] span {{
        color: {BLACK} !important;
    }}

    input {{
        color: {BLACK} !important;
    }}

    textarea {{
        color: {BLACK} !important;
        background: {WHITE} !important;
    }}

    /* Buttons */
    .stButton > button {{
        background: {RED};
        color: {WHITE};
        border: 2px solid {RED};
        border-radius: 10px;
        font-weight: 800;
        min-height: 46px;
        transition: 0.2s ease;
    }}

    .stButton > button:hover {{
        background: {BROWN};
        border-color: {BROWN};
        color: {WHITE};
    }}

    /* File uploader */
    [data-testid="stFileUploader"] {{
        background: {LIGHT_GREEN};
        border: 2px dashed {GREEN};
        border-radius: 12px;
        padding: 8px;
    }}

    [data-testid="stFileUploader"] section {{
        background: {LIGHT_GREEN};
    }}

    [data-testid="stFileUploader"] * {{
        color: {BLACK} !important;
    }}

    /* Cards */
    .trek-card {{
        background: rgba(255, 255, 255, 0.94);
        border: 1px solid rgba(34, 111, 84, 0.25);
        border-radius: 16px;
        padding: 20px;
        margin: 12px 0;
        box-shadow: 0 8px 24px rgba(67, 41, 31, 0.08);
    }}

    .section-card {{
        background: {WHITE};
        border-left: 6px solid {GREEN};
        border-radius: 14px;
        padding: 18px;
        margin: 12px 0;
    }}

    .response-card {{
        background: {WHITE};
        border: 1px solid {LIGHT_GREEN};
        border-radius: 16px;
        padding: 24px;
        margin-top: 20px;
        color: {BLACK};
    }}

    .response-card * {{
        color: {BLACK};
    }}

    .source-card {{
        background: {CREAM};
        border-left: 5px solid {GREEN};
        border-radius: 10px;
        padding: 12px 15px;
        margin: 7px 0;
        color: {BLACK};
    }}

    .payment-card {{
        background: {WHITE};
        border: 2px solid {LIGHT_GREEN};
        border-radius: 16px;
        padding: 20px;
        margin: 10px 0 18px 0;
        color: {BLACK};
    }}

    .success-card {{
        background: #E8F5E9;
        border: 2px solid {GREEN};
        border-radius: 12px;
        padding: 14px;
        color: {BLACK};
        font-weight: 700;
    }}

    .locked-card {{
        background: {CREAM};
        border: 1px solid {LIGHT_GREEN};
        border-radius: 12px;
        padding: 14px 16px;
        color: {BLACK};
        font-weight: 700;
        margin: 10px 0;
    }}

    .status-ready {{
        color: {GREEN};
        font-weight: 800;
    }}

    .status-missing {{
        color: {RED};
        font-weight: 800;
    }}

    .small-note {{
        font-size: 0.88rem;
        color: {BLACK};
    }}

    /* Remove Streamlit decoration */
    #MainMenu {{
        visibility: hidden;
    }}

    footer {{
        visibility: hidden;
    }}

    header {{
        background: transparent !important;
    }}

    /* Mobile */
    @media (max-width: 768px) {{

        .main-title {{
            font-size: 2.25rem;
        }}

        .main-subtitle {{
            font-size: 0.95rem;
        }}

        .trek-card,
        .section-card,
        .payment-card,
        .response-card {{
            padding: 15px;
            border-radius: 12px;
        }}

        .stButton > button {{
            width: 100%;
        }}

        [data-testid="stFileUploader"] {{
            background: {LIGHT_GREEN} !important;
        }}

        [data-testid="stFileUploader"] section {{
            background: {LIGHT_GREEN} !important;
        }}
    }}

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

def clean_text(value: Any) -> str:
    """
    Removes accidental HTML from model-generated text.
    """
    if value is None:
        return ""

    text = str(value)
    text = text.replace("\x00", "")

    # Remove HTML tags.
    text = re.sub(r"<[^>]+>", "", text)

    # Decode HTML entities.
    text = html.unescape(text)

    return text.strip()


def get_secret(name: str, default: Any = None) -> Any:
    try:
        value = st.secrets.get(name, default)
        if value is None:
            return default
        return value
    except Exception:
        return default


def safe_filename(value: str) -> str:
    value = clean_text(value)
    return Path(value).name


def normalize_metadata(raw: Any) -> List[Dict[str, Any]]:
    """
    Supports common metadata.json structures.
    """

    if isinstance(raw, list):
        records = raw

    elif isinstance(raw, dict):
        for key in ["records", "metadata", "chunks", "documents", "data"]:
            if isinstance(raw.get(key), list):
                records = raw[key]
                break
        else:
            records = []

    else:
        records = []

    normalized = []

    for item in records:
        if isinstance(item, dict):
            normalized.append(item)
        else:
            normalized.append({"text": str(item)})

    return normalized


# ============================================================
# LOAD METADATA
# ============================================================

@st.cache_data(show_spinner=False)
def load_metadata() -> List[Dict[str, Any]]:
    if not METADATA_PATH.exists():
        return []

    try:
        with open(METADATA_PATH, "r", encoding="utf-8") as file:
            raw = json.load(file)

        return normalize_metadata(raw)

    except Exception:
        return []


# ============================================================
# METADATA TEXT EXTRACTION
# ============================================================

def get_record_text(record: Dict[str, Any]) -> str:
    possible_keys = [
        "text",
        "content",
        "chunk",
        "document",
        "page_content",
    ]

    for key in possible_keys:
        value = record.get(key)

        if value:
            return clean_text(value)

    return ""


def get_record_source(record: Dict[str, Any]) -> str:
    """
    Returns only the knowledge-base filename.
    """

    metadata = record.get("metadata")

    if isinstance(metadata, dict):
        candidates = [
            metadata.get("source"),
            metadata.get("file"),
            metadata.get("filename"),
            metadata.get("file_name"),
        ]

        for candidate in candidates:
            if candidate:
                return safe_filename(str(candidate))

    candidates = [
        record.get("source"),
        record.get("file"),
        record.get("filename"),
        record.get("file_name"),
    ]

    for candidate in candidates:
        if candidate:
            return safe_filename(str(candidate))

    return "Knowledge base source unavailable"


# ============================================================
# FAISS RESOURCES
# ============================================================

@st.cache_resource(show_spinner=False)
def load_faiss_resources():

    if not FAISS_INDEX_PATH.exists():
        raise FileNotFoundError(
            "FAISS index not found. Expected faiss_db/index.faiss."
        )

    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            "FAISS metadata not found. Expected faiss_db/metadata.json."
        )

    import faiss
    from sentence_transformers import SentenceTransformer

    index = faiss.read_index(str(FAISS_INDEX_PATH))

    metadata = load_metadata()

    if not metadata:
        raise RuntimeError(
            "metadata.json exists but contains no usable records."
        )

    if index.ntotal != len(metadata):
        raise RuntimeError(
            f"FAISS and metadata mismatch: "
            f"index contains {index.ntotal} vectors, "
            f"metadata contains {len(metadata)} records."
        )

    embedding_model = DEFAULT_EMBEDDING_MODEL

    if FAISS_CONFIG_PATH.exists():
        try:
            with open(
                FAISS_CONFIG_PATH,
                "r",
                encoding="utf-8",
            ) as file:
                config = json.load(file)

            embedding_model = config.get(
                "embedding_model",
                DEFAULT_EMBEDDING_MODEL,
            )

        except Exception:
            embedding_model = DEFAULT_EMBEDDING_MODEL

    model = SentenceTransformer(embedding_model)

    return index, metadata, model


# ============================================================
# KEYWORD SCORING
# ============================================================

def keyword_score(query: str, text: str) -> float:

    query_words = set(
        re.findall(
            r"[A-Za-z0-9\u0600-\u06FF]+",
            query.lower(),
        )
    )

    text_words = set(
        re.findall(
            r"[A-Za-z0-9\u0600-\u06FF]+",
            text.lower(),
        )
    )

    if not query_words:
        return 0.0

    overlap = len(query_words.intersection(text_words))

    return overlap / max(len(query_words), 1)


# ============================================================
# FAISS RETRIEVAL
# ============================================================

def retrieve_context(
    query: str,
    top_k: int = TOP_K,
) -> Tuple[str, List[str]]:

    index, metadata, embedding_model = load_faiss_resources()

    query = clean_text(query)

    if not query:
        return "", []

    query_embedding = embedding_model.encode(
        [query],
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    scores, indices = index.search(
        query_embedding,
        min(top_k, index.ntotal),
    )

    candidates = []

    for score, idx in zip(scores[0], indices[0]):

        if idx < 0 or idx >= len(metadata):
            continue

        record = metadata[idx]

        text = get_record_text(record)

        if not text:
            continue

        source = get_record_source(record)

        semantic_score = float(score)

        keyword = keyword_score(
            query,
            text,
        )

        combined_score = (
            0.75 * semantic_score
            + 0.25 * keyword
        )

        candidates.append(
            {
                "score": combined_score,
                "text": text,
                "source": source,
            }
        )

    candidates.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    selected = candidates[:top_k]

    context_parts = []
    sources = []

    for item in selected:

        context_parts.append(
            f"SOURCE: {item['source']}\n"
            f"CONTENT:\n{item['text']}"
        )

        if item["source"] not in sources:
            sources.append(item["source"])

    context = "\n\n---\n\n".join(context_parts)

    return context, sources


# ============================================================
# GROQ CLIENT
# ============================================================

def get_groq_client():

    api_key = get_secret(
        "GROQ_API_KEY",
        "",
    )

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing from Streamlit Secrets."
        )

    base_url = get_secret(
        "GROQ_BASE_URL",
        DEFAULT_GROQ_BASE_URL,
    )

    try:
        from groq import Groq

        return Groq(
            api_key=api_key,
            base_url=base_url,
        )

    except ImportError:

        try:
            from openai import OpenAI

            return OpenAI(
                api_key=api_key,
                base_url=base_url,
            )

        except ImportError:
            raise RuntimeError(
                "Neither groq nor openai package is installed."
            )


# ============================================================
# GROQ TEXT GENERATION
# ============================================================

def generate_with_groq(
    system_prompt: str,
    user_prompt: str,
) -> str:

    client = get_groq_client()

    model = get_secret(
        "GROQ_MODEL",
        DEFAULT_GROQ_MODEL,
    )

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
        temperature=0.2,
        max_tokens=6000,
    )

    content = response.choices[0].message.content

    return clean_text(content)


# ============================================================
# PAYMENT VISION
# ============================================================

def image_to_base64(uploaded_file) -> str:

    image_bytes = uploaded_file.getvalue()

    return base64.b64encode(image_bytes).decode("utf-8")


def analyze_payment_screenshot(
    uploaded_file,
) -> Dict[str, Any]:

    api_key = get_secret(
        "GROQ_API_KEY",
        "",
    )

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing."
        )

    try:
        from groq import Groq
    except ImportError:
        raise RuntimeError(
            "The groq package is required for payment screenshot verification."
        )

    client = Groq(
        api_key=api_key,
        base_url=get_secret(
            "GROQ_BASE_URL",
            DEFAULT_GROQ_BASE_URL,
        ),
    )

    model = get_secret(
        "GROQ_VISION_MODEL",
        DEFAULT_GROQ_VISION_MODEL,
    )

    image_base64 = image_to_base64(
        uploaded_file
    )

    prompt = """
Analyze this payment screenshot.

Extract ONLY information visibly present in the screenshot.

Return valid JSON with these fields:

{
  "amount": null,
  "status": "",
  "recipient": "",
  "transaction_id": "",
  "summary": ""
}

Rules:
- Do not guess missing values.
- Use null for an unreadable amount.
- Use an empty string for unreadable text.
- Do not claim payment is successful unless the screenshot visibly shows a successful/completed/paid status.
"""

    response = client.chat.completions.create(
        model=model,
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
                                + image_base64
                            )
                        },
                    },
                ],
            }
        ],
        temperature=0,
        max_tokens=800,
    )

    raw = response.choices[0].message.content

    raw = clean_text(raw)

    # Extract JSON even if model surrounds it with text.
    match = re.search(
        r"\{.*\}",
        raw,
        re.DOTALL,
    )

    if not match:
        return {
            "amount": None,
            "status": "",
            "recipient": "",
            "transaction_id": "",
            "summary": raw,
        }

    try:
        data = json.loads(match.group(0))

        if not isinstance(data, dict):
            raise ValueError

        return data

    except Exception:
        return {
            "amount": None,
            "status": "",
            "recipient": "",
            "transaction_id": "",
            "summary": raw,
        }


# ============================================================
# PAYMENT VERIFICATION
# ============================================================

def verify_payment(
    payment_data: Dict[str, Any],
) -> Tuple[bool, str]:

    if not isinstance(payment_data, dict):
        return False, "Payment information could not be read."

    amount = payment_data.get("amount")
    status = clean_text(
        payment_data.get("status", "")
    ).lower()

    recipient = clean_text(
        payment_data.get("recipient", "")
    ).lower()

    if amount is None:
        return (
            False,
            "The payment amount could not be verified from the screenshot.",
        )

    try:
        numeric_amount = float(
            str(amount).replace(",", "").replace("Rs.", "").strip()
        )
    except Exception:
        return (
            False,
            "The payment amount could not be verified.",
        )

    if numeric_amount < UNLOCK_PRICE:
        return (
            False,
            f"The screenshot does not show a payment of at least Rs. {UNLOCK_PRICE}.",
        )

    accepted_statuses = {
        "successful",
        "success",
        "completed",
        "complete",
        "paid",
        "sent",
    }

    if status not in accepted_statuses:
        return (
            False,
            "The payment status could not be verified as successful.",
        )

    expected_recipient = clean_text(
        get_secret(
            "EXPECTED_PAYMENT_RECIPIENT",
            "",
        )
    ).lower()

    if expected_recipient:
        if expected_recipient not in recipient:
            return (
                False,
                "The payment recipient could not be verified.",
            )

    return (
        True,
        f"Premium access verified for Rs. {numeric_amount:.0f}.",
    )


# ============================================================
# TRIP ACCESS
# ============================================================

def get_accessible_days(
    requested_days: int,
) -> int:

    if requested_days <= FREE_DAYS:
        return requested_days

    if st.session_state.payment_verified:
        return requested_days

    return FREE_DAYS


# ============================================================
# ITINERARY PROMPT
# ============================================================

def build_system_prompt() -> str:

    return """
You are TrekTales, a tourism itinerary assistant.

TrekTales uses exactly eight specialized agents:

1. Master Orchestrator
2. Knowledge Agent
3. Planner Agent
4. Budget Agent
5. Safety Agent
6. Summarizer Agent
7. Payment Agent
8. Vision Agent

The application controls access to premium days separately.

IMPORTANT KNOWLEDGE RULES:

Use ONLY the supplied TrekTales tourism knowledge-base context.

Never invent:
- hotels
- restaurants
- attractions
- activities
- prices
- opening hours
- addresses
- transport schedules
- contact information
- safety facts
- travel facts

If the requested information is not supported by the supplied context, write:

"Information not available in the TrekTales knowledge base."

Do not use outside knowledge.

Do not hallucinate.

Do not create fake sources.

Do not create HTML.

Do not output:
<p>
</p>
<div>
</div>
<span>
</span>

Use normal Markdown only.

The Python application determines how many days the user is allowed to receive.
Generate EXACTLY the number of accessible days provided by the application.

For each day:
- Keep the itinerary practical.
- Use evidence from the supplied knowledge base.
- Respect traveler count.
- Respect budget level.
- Respect travel style.
- Respect interests.
- Include supported activities.
- Mention unavailable information instead of guessing.

At the end include a "Sources" section containing only the source filenames supplied in the context.
"""


# ============================================================
# GENERATE ITINERARY
# ============================================================

def generate_itinerary(
    destination: str,
    starting_location: str,
    requested_days: int,
    travelers: int,
    budget: str,
    travel_style: str,
    interests: List[str],
    custom_interests: str,
) -> Tuple[str, List[str]]:

    accessible_days = get_accessible_days(
        requested_days
    )

    retrieval_query = f"""
Destination: {destination}

Starting location: {starting_location}

Trip duration: {accessible_days} days

Travelers: {travelers}

Budget: {budget}

Travel style: {travel_style}

Interests: {", ".join(interests)}

Additional interests: {custom_interests}

Create an itinerary using tourism knowledge about:
{destination}
"""

    context, sources = retrieve_context(
        retrieval_query,
        top_k=TOP_K,
    )

    if not context:
        return (
            "Information not available in the TrekTales knowledge base.",
            [],
        )

    user_prompt = f"""
Create a personalized TrekTales itinerary.

REQUESTED TRIP:

Destination:
{destination}

Starting location:
{starting_location}

Requested duration:
{requested_days} days

ACCESSIBLE DURATION:
{accessible_days} days

Travelers:
{travelers}

Budget:
{budget}

Travel style:
{travel_style}

Interests:
{", ".join(interests)}

Additional interests:
{custom_interests}

IMPORTANT ACCESS RULE:

The user is allowed to receive exactly {accessible_days} day(s).

Do not generate Day {accessible_days + 1} or any later day.

KNOWLEDGE BASE CONTEXT:

{context}

OUTPUT FORMAT:

# TrekTales Itinerary

Brief trip overview.

## Day 1
Morning:
...

Afternoon:
...

Evening:
...

## Day 2
...

Continue ONLY until Day {accessible_days}.

## Budget Notes

Only include supported information.

## Safety Notes

Only include safety information supported by the knowledge base.

## Sources

List only the actual filenames supplied in the knowledge context.

Do not use HTML.
Do not invent information.
"""

    response = generate_with_groq(
        build_system_prompt(),
        user_prompt,
    )

    return response, sources


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🌿 TrekTales</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-subtitle">'
    'TrekTales creates personalized travel itineraries '
    'using your tourism knowledge base and Groq-powered AI.'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "## 🌿 TrekTales"
    )

    st.markdown(
        "### Trip Planner"
    )

    if st.session_state.payment_verified:
        st.success(
            "Premium Verified"
        )
    else:
        st.info(
            "Day 1 is free"
        )

    st.markdown("---")

    st.markdown(
        "### Knowledge Base"
    )

    if FAISS_INDEX_PATH.exists():
        st.markdown(
            "🟢 FAISS index found"
        )
    else:
        st.markdown(
            "🔴 FAISS index missing"
        )

    if METADATA_PATH.exists():
        st.markdown(
            "🟢 Metadata found"
        )
    else:
        st.markdown(
            "🔴 Metadata missing"
        )

    st.markdown("---")

    st.markdown(
        "### Premium"
    )

    st.markdown(
        f"Unlock Days 2–{MAX_TRIP_DAYS} for **Rs. {UNLOCK_PRICE}**."
    )

    st.markdown("---")

    st.caption(
        "TrekTales uses evidence from its configured tourism knowledge base."
    )


# ============================================================
# TRIP PLANNER
# ============================================================

st.markdown(
    "## 🧭 Plan Your Trip"
)

col1, col2 = st.columns(2)

with col1:

    destination = st.text_input(
        "📍 Destination",
        placeholder="Example: Rawalpindi",
    )

    starting_location = st.text_input(
        "🚗 Starting Location",
        placeholder="Example: Islamabad",
    )

    requested_days = st.slider(
        "📅 Trip Duration",
        min_value=1,
        max_value=MAX_TRIP_DAYS,
        value=2,
        step=1,
    )

    travelers = st.number_input(
        "👥 Number of Travelers",
        min_value=1,
        max_value=20,
        value=2,
        step=1,
    )


with col2:

    budget = st.selectbox(
        "💰 Budget Level",
        [
            "Budget — Rs. 3,000–7,000/day",
            "Standard — Rs. 7,000–15,000/day",
            "Comfort — Rs. 15,000–30,000/day",
            "Premium — Rs. 30,000+/day",
        ],
    )

    travel_style = st.selectbox(
        "🧳 Travel Style",
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

    interests = st.multiselect(
        "❤️ Interests",
        [
            "History & Heritage",
            "Nature",
            "Hiking & Trekking",
            "Food & Local Cuisine",
            "Photography",
            "Culture & Architecture",
            "Family Activities",
            "Arts & Creativity",
            "Shopping",
            "Sports",
            "Scenic Views",
            "Relaxation",
            "Wildlife",
            "Camping",
            "Local Events",
            "Road Trips",
        ],
        default=[],
    )

    custom_interests = st.text_input(
        "✨ Other Interests",
        placeholder="Add any other interests...",
    )


# ============================================================
# PREMIUM LOCK MESSAGE
# ============================================================

if requested_days > FREE_DAYS and not st.session_state.payment_verified:

    st.markdown(
        f"""
        <div class="locked-card">
            Days 2–{requested_days} are locked.
            Complete the Rs. {UNLOCK_PRICE} premium verification to unlock them.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# GENERATE BUTTON
# ============================================================

generate_button = st.button(
    "✨ Generate TrekTales Itinerary",
    use_container_width=True,
)


# ============================================================
# PREMIUM ACCESS
# ============================================================

if requested_days > FREE_DAYS and not st.session_state.payment_verified:

    st.markdown(
        "## 🔓 Premium Access"
    )

    st.markdown(
        f"""
        <div class="payment-card">
            <strong>Unlock Days 2–{MAX_TRIP_DAYS}</strong><br><br>
            Premium access costs <strong>Rs. {UNLOCK_PRICE}</strong>.<br>
            Upload your payment screenshot below for verification.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if QR_PATH.exists():

        st.image(
            str(QR_PATH),
            caption="TrekTales Premium Payment QR",
            width=280,
        )

    else:

        st.warning(
            "Payment QR image was not found at assets/jazzcash_qr.jpg."
        )

    payment_upload = st.file_uploader(
        "📤 Upload Payment Screenshot",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp",
        ],
        key="payment_upload",
    )

    verify_button = st.button(
        "🔍 Verify Premium Payment",
        use_container_width=True,
    )

    if verify_button:

        if payment_upload is None:

            st.error(
                "Please upload a payment screenshot first."
            )

        else:

            try:

                with st.spinner(
                    "Vision Agent is reading the payment screenshot..."
                ):

                    payment_data = analyze_payment_screenshot(
                        payment_upload
                    )

                verified, message = verify_payment(
                    payment_data
                )

                st.session_state.payment_result = {
                    "verified": verified,
                    "message": message,
                    "data": payment_data,
                }

                if verified:

                    st.session_state.payment_verified = True

                    st.markdown(
                        f"""
                        <div class="success-card">
                            ✅ {clean_text(message)}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.rerun()

                else:

                    st.error(
                        clean_text(message)
                    )

            except Exception as error:

                st.error(
                    "Payment verification could not be completed."
                )

                st.caption(
                    clean_text(error)
                )


elif st.session_state.payment_verified:

    st.markdown(
        f"""
        <div class="success-card">
            🔓 Premium access is active. Days 2–{MAX_TRIP_DAYS} are unlocked.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# GENERATE ITINERARY
# ============================================================

if generate_button:

    if not destination.strip():

        st.error(
            "Please enter a destination."
        )

    elif not starting_location.strip():

        st.error(
            "Please enter your starting location."
        )

    elif not FAISS_INDEX_PATH.exists():

        st.error(
            "FAISS index not found. Please make sure faiss_db/index.faiss exists."
        )

    elif not METADATA_PATH.exists():

        st.error(
            "FAISS metadata not found. Please make sure faiss_db/metadata.json exists."
        )

    else:

        accessible_days = get_accessible_days(
            requested_days
        )

        if requested_days > FREE_DAYS and not st.session_state.payment_verified:

            st.info(
                f"Only Day 1 will be generated because premium access is not verified."
            )

        with st.spinner(
            "TrekTales agents are creating your itinerary..."
        ):

            try:

                plan, sources = generate_itinerary(
                    destination=destination.strip(),
                    starting_location=starting_location.strip(),
                    requested_days=requested_days,
                    travelers=int(travelers),
                    budget=budget,
                    travel_style=travel_style,
                    interests=interests,
                    custom_interests=custom_interests.strip(),
                )

                st.session_state.last_plan = plan
                st.session_state.last_sources = sources

            except Exception as error:

                st.error(
                    "TrekTales could not generate the itinerary."
                )

                st.caption(
                    clean_text(error)
                )


# ============================================================
# DISPLAY GENERATED PLAN
# ============================================================

if st.session_state.last_plan:

    st.markdown(
        "## 🗺️ Your TrekTales Itinerary"
    )

    # Important:
    # Model output is cleaned before rendering.
    # No raw HTML is allowed into the response area.

    cleaned_plan = clean_text(
        st.session_state.last_plan
    )

    st.markdown(
        f"""
        <div class="response-card">
        {html.escape(cleaned_plan).replace(chr(10), "<br>")}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ========================================================
    # SOURCES
    # ========================================================

    sources = st.session_state.last_sources

    if sources:

        st.markdown(
            "### 📚 Sources"
        )

        unique_sources = []

        for source in sources:

            source = safe_filename(source)

            if source not in unique_sources:
                unique_sources.append(source)

        for source in unique_sources:

            st.markdown(
                f"""
                <div class="source-card">
                    📄 {html.escape(source)}
                </div>
                """,
                unsafe_allow_html=True,
            )

    else:

        st.caption(
            "No source filenames were returned from the knowledge base."
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "TrekTales • Evidence-based tourism planning • Powered by Groq"
)
