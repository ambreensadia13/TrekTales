from pathlib import Path
import base64
import html
import json
import re

import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="TrekTales AI",
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
CONFIG_PATH = FAISS_DIR / "config.json"

ASSETS_DIR = ROOT_DIR / "assets"
QR_PATH = ASSETS_DIR / "jazzcash_qr.jpg"


# ============================================================
# SETTINGS
# ============================================================

FREE_DAYS = 1
MAX_TRIP_DAYS = 10
PREMIUM_PRICE = 199
TOP_K = 6

DEFAULT_EMBEDDING_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)

DEFAULT_GROQ_MODEL = (
    "openai/gpt-oss-120b"
)

DEFAULT_VISION_MODEL = (
    "meta-llama/llama-4-scout-17b-16e-instruct"
)

DEFAULT_GROQ_BASE_URL = (
    "https://api.groq.com/openai/v1"
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


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    f"""
<style>
.stApp {{
    background: linear-gradient(
        135deg,
        #fffdf4 0%,
        {CREAM} 45%,
        #ffffff 100%
    );
    color: {BLACK};
}}

.main .block-container {{
    max-width: 1250px;
    padding-top: 1rem;
    padding-bottom: 3rem;
}}

[data-testid="stSidebar"] {{
    background: {GREEN} !important;
}}

[data-testid="stSidebar"] * {{
    color: {WHITE} !important;
}}

h1, h2, h3, h4, h5, h6 {{
    color: {BROWN} !important;
}}

p, li, label {{
    color: {BLACK};
}}

.stTextInput input,
.stTextArea textarea,
.stNumberInput input {{
    background: {WHITE} !important;
    color: {BLACK} !important;
    border: 2px solid rgba(34,111,84,0.25) !important;
    border-radius: 10px !important;
}}

div[data-baseweb="select"] > div {{
    background: {WHITE} !important;
    color: {BLACK} !important;
    border-radius: 10px !important;
}}

div[data-baseweb="select"] span {{
    color: {BLACK} !important;
}}

.stButton > button {{
    background: {RED} !important;
    color: {WHITE} !important;
    border: none !important;
    border-radius: 11px !important;
    min-height: 46px !important;
    font-weight: 800 !important;
}}

.stButton > button:hover {{
    background: {BROWN} !important;
    color: {WHITE} !important;
}}

div[data-testid="stMetric"] {{
    background: {WHITE};
    border-radius: 14px;
    padding: 12px;
    border: 1px solid rgba(67,41,31,0.10);
}}

.trip-card {{
    background: {WHITE};
    border-left: 5px solid {GREEN};
    border-radius: 15px;
    padding: 20px;
    box-shadow: 0 6px 20px rgba(67,41,31,0.08);
}}

@media screen and (max-width: 768px) {{
    .main .block-container {{
        padding-left: 0.7rem !important;
        padding-right: 0.7rem !important;
    }}

    .stButton > button {{
        width: 100% !important;
    }}
}}
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SECRET HELPER
# ============================================================

def get_secret(name, default=""):
    try:
        value = st.secrets.get(name, default)
    except Exception:
        value = default

    if value is None:
        return default

    return str(value).strip()


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(value):
    """
    Removes HTML/XML tags from text before displaying it.
    Markdown remains usable.
    """

    if value is None:
        return ""

    text = str(value)

    text = text.replace("\x00", "")

    text = html.unescape(text)

    text = re.sub(
        r"<!--.*?-->",
        "",
        text,
        flags=re.DOTALL,
    )

    text = re.sub(
        r"<[^>]*>",
        "",
        text,
    )

    return text.strip()


def clean_ai_response(value):
    text = clean_text(value)

    text = re.sub(
        r"```html",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"```",
        "",
        text,
    )

    return text.strip()


# ============================================================
# CONFIG FILE
# ============================================================

@st.cache_data(show_spinner=False)
def load_config():

    if not CONFIG_PATH.exists():
        return {}

    try:
        with open(
            CONFIG_PATH,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if isinstance(data, dict):
            return data

    except Exception:
        pass

    return {}


def get_embedding_model_name():

    configured = get_secret(
        "EMBEDDING_MODEL",
        "",
    )

    if configured:
        return configured

    config = load_config()

    possible_keys = [
        "embedding_model",
        "embedding_model_name",
        "model",
    ]

    for key in possible_keys:

        value = config.get(key)

        if isinstance(value, str) and value.strip():
            return value.strip()

    return DEFAULT_EMBEDDING_MODEL


# ============================================================
# METADATA
# ============================================================

def normalize_metadata(data):

    if isinstance(data, list):
        return data

    if isinstance(data, dict):

        for key in [
            "metadata",
            "records",
            "chunks",
            "documents",
            "data",
        ]:

            value = data.get(key)

            if isinstance(value, list):
                return value

    return []


@st.cache_data(show_spinner=False)
def load_metadata():

    if not METADATA_PATH.exists():
        return []

    try:

        with open(
            METADATA_PATH,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        return normalize_metadata(data)

    except Exception:

        return []


def record_text(record):

    if not isinstance(record, dict):
        return ""

    for key in [
        "text",
        "content",
        "chunk",
        "page_content",
        "document",
    ]:

        value = record.get(key)

        if value:
            return clean_text(value)

    return ""


def record_source(record):

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

            return Path(
                str(value)
            ).name

    return "Unknown source"


def record_page(record):

    if not isinstance(record, dict):
        return ""

    for key in [
        "page",
        "page_number",
        "page_num",
    ]:

        value = record.get(key)

        if value not in [None, ""]:
            return clean_text(value)

    return ""


# ============================================================
# FAISS
# ============================================================

@st.cache_resource(show_spinner=False)
def load_faiss():

    if not FAISS_INDEX_PATH.exists():

        raise FileNotFoundError(
            "FAISS index not found. "
            f"Expected: {FAISS_INDEX_PATH}"
        )

    if not METADATA_PATH.exists():

        raise FileNotFoundError(
            "FAISS metadata not found. "
            f"Expected: {METADATA_PATH}"
        )

    try:

        import faiss

    except ImportError as exc:

        raise RuntimeError(
            "faiss-cpu is not installed."
        ) from exc

    try:

        from sentence_transformers import (
            SentenceTransformer
        )

    except ImportError as exc:

        raise RuntimeError(
            "sentence-transformers is not installed."
        ) from exc

    try:

        index = faiss.read_index(
            str(FAISS_INDEX_PATH)
        )

    except Exception as exc:

        raise RuntimeError(
            f"Could not read FAISS index: {exc}"
        ) from exc

    metadata = load_metadata()

    if not metadata:

        raise RuntimeError(
            "metadata.json contains no records."
        )

    if index.ntotal == 0:

        raise RuntimeError(
            "FAISS index contains zero vectors."
        )

    if index.ntotal != len(metadata):

        raise RuntimeError(
            "FAISS/metadata mismatch. "
            f"FAISS vectors: {index.ntotal}. "
            f"Metadata records: {len(metadata)}."
        )

    model_name = get_embedding_model_name()

    try:

        embedding_model = (
            SentenceTransformer(model_name)
        )

    except Exception as exc:

        raise RuntimeError(
            "Could not load embedding model "
            f"'{model_name}': {exc}"
        ) from exc

    return (
        index,
        metadata,
        embedding_model,
    )


# ============================================================
# KEYWORD MATCHING
# ============================================================

def keyword_score(query, text):

    query_words = set(
        re.findall(
            r"\b[a-zA-Z0-9]{3,}\b",
            query.lower(),
        )
    )

    text_words = set(
        re.findall(
            r"\b[a-zA-Z0-9]{3,}\b",
            text.lower(),
        )
    )

    if not query_words:
        return 0.0

    matched = query_words.intersection(
        text_words
    )

    return len(matched) / len(query_words)


# ============================================================
# RETRIEVAL
# ============================================================

def retrieve(query, top_k=TOP_K):

    import numpy as np

    (
        index,
        metadata,
        embedding_model,
    ) = load_faiss()

    embedding = embedding_model.encode(
        [query],
        normalize_embeddings=True,
    )

    embedding = np.asarray(
        embedding,
        dtype="float32",
    )

    k = min(
        top_k,
        index.ntotal,
    )

    distances, indices = index.search(
        embedding,
        k,
    )

    results = []

    for distance, index_id in zip(
        distances[0],
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

        source = record_source(
            record
        )

        page = record_page(
            record
        )

        semantic_score = float(
            distance
        )

        keyword = keyword_score(
            query,
            text,
        )

        final_score = (
            0.75 * semantic_score
            + 0.25 * keyword
        )

        results.append(
            {
                "text": text,
                "source": source,
                "page": page,
                "score": final_score,
            }
        )

    results.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    return results[:top_k]


# ============================================================
# CONTEXT
# ============================================================

def make_context(results):

    context_parts = []

    for number, result in enumerate(
        results,
        start=1,
    ):

        source = clean_text(
            result["source"]
        )

        page = clean_text(
            result["page"]
        )

        text = clean_text(
            result["text"]
        )

        location = source

        if page:
            location += (
                f" | Page {page}"
            )

        context_parts.append(
            f"""
SOURCE {number}
SOURCE FILE: {location}

CONTENT:
{text}
""".strip()
        )

    return "\n\n--------------------\n\n".join(
        context_parts
    )


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
            "GROQ_API_KEY is missing from "
            "Streamlit Secrets."
        )

    base_url = get_secret(
        "GROQ_BASE_URL",
        DEFAULT_GROQ_BASE_URL,
    )

    if not base_url.startswith("http"):

        base_url = DEFAULT_GROQ_BASE_URL

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

        except ImportError as exc:

            raise RuntimeError(
                "Install either groq or openai."
            ) from exc


# ============================================================
# ITINERARY GENERATION
# ============================================================

def generate_itinerary(
    destination,
    starting_location,
    days,
    travelers,
    budget,
    travel_style,
    interests,
    language,
    context,
):

    client = get_groq_client()

    model = get_secret(
        "GROQ_MODEL",
        DEFAULT_GROQ_MODEL,
    )

    system_prompt = f"""
You are the TrekTales tourism planning AI.

You must follow strict knowledge-grounding rules.

The supplied context is the only factual tourism
source you may use.

DO NOT invent:
- attractions
- restaurants
- hotels
- prices
- opening hours
- addresses
- phone numbers
- transport schedules
- event dates
- ticket prices
- distances
- safety rules

If required information is not present in the
knowledge base, say:

"Information not available in the TrekTales knowledge base."

Never fill missing information with guesses.

Generate exactly {days} day(s).

Never generate Day {days + 1}.

Use the requested language:
{language}

Do not output HTML.

Use normal Markdown only.

Do not use:
<p>
</p>
<div>
</div>
<span>
</span>
<section>
</section>
<style>
<script>
"""

    user_prompt = f"""
Create a TrekTales itinerary.

Destination:
{clean_text(destination)}

Starting location:
{clean_text(starting_location)}

Number of days:
{days}

Travelers:
{travelers}

Budget:
{clean_text(budget)}

Travel style:
{clean_text(travel_style)}

Interests:
{clean_text(interests)}

KNOWLEDGE BASE:

{context}

RESPONSE FORMAT:

# TrekTales {days}-Day Itinerary

## Trip Overview

Provide a short overview using supported information only.

"""

    for day in range(
        1,
        days + 1,
    ):

        user_prompt += f"""

## Day {day}

### Morning

Use only supported information.

### Afternoon

Use only supported information.

### Evening

Use only supported information.

### Notes

Use only supported information.

"""

    user_prompt += """

## Budget Notes

Only mention prices explicitly present
in the knowledge base.

## Safety Notes

Only mention safety information explicitly
present in the knowledge base.

## Sources

List the source filenames used.

Do not invent filenames.
"""

    try:

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
            max_tokens=6000,
            temperature=0.1,
        )

    except TypeError:

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
            max_tokens=6000,
        )

    if not response.choices:

        raise RuntimeError(
            "Groq returned no response."
        )

    content = getattr(
        response.choices[0].message,
        "content",
        None,
    )

    if not content:

        raise RuntimeError(
            "Groq returned an empty response."
        )

    return clean_ai_response(
        content
    )


# ============================================================
# PAYMENT IMAGE
# ============================================================

def image_to_data_url(uploaded_file):

    file_bytes = uploaded_file.getvalue()

    mime_type = (
        uploaded_file.type
        or "image/jpeg"
    )

    encoded = base64.b64encode(
        file_bytes
    ).decode("utf-8")

    return (
        f"data:{mime_type};base64,{encoded}"
    )


# ============================================================
# PAYMENT ANALYSIS
# ============================================================

def analyze_payment(uploaded_file):

    client = get_groq_client()

    model = get_secret(
        "GROQ_VISION_MODEL",
        DEFAULT_VISION_MODEL,
    )

    image_url = image_to_data_url(
        uploaded_file
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Read only information visibly "
                    "present in the payment screenshot. "
                    "Do not invent missing values. "
                    "Return valid JSON only."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Extract these visible "
                            "payment fields:\n"
                            "{\n"
                            '  "recipient": "",\n'
                            '  "amount": "",\n'
                            '  "status": "",\n'
                            '  "transaction_id": "",\n'
                            '  "confidence": ""\n'
                            "}\n"
                            "Leave unavailable fields empty."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        },
                    },
                ],
            },
        ],
        max_tokens=800,
    )

    if not response.choices:
        return {}

    content = getattr(
        response.choices[0].message,
        "content",
        "",
    )

    if not content:
        return {}

    content = content.strip()

    content = re.sub(
        r"^```json\s*",
        "",
        content,
        flags=re.IGNORECASE,
    )

    content = re.sub(
        r"^```\s*",
        "",
        content,
    )

    content = re.sub(
        r"\s*```$",
        "",
        content,
    )

    try:

        data = json.loads(
            content
        )

        if isinstance(data, dict):
            return data

    except Exception:
        pass

    return {
        "raw_analysis": clean_text(
            content
        )
    }


# ============================================================
# PAYMENT VERIFICATION
# ============================================================

def verify_payment(data):

    if not isinstance(data, dict):

        return (
            False,
            "Payment information could not be read.",
        )

    amount_text = str(
        data.get(
            "amount",
            "",
        )
    )

    status = str(
        data.get(
            "status",
            "",
        )
    ).lower().strip()

    recipient = str(
        data.get(
            "recipient",
            "",
        )
    ).strip()

    amount_matches = re.findall(
        r"\d+(?:\.\d+)?",
        amount_text,
    )

    if not amount_matches:

        return (
            False,
            "Payment amount was not detected.",
        )

    try:

        amount = float(
            amount_matches[0]
        )

    except Exception:

        return (
            False,
            "Payment amount could not be read.",
        )

    if amount < PREMIUM_PRICE:

        return (
            False,
            f"Detected amount is below "
            f"Rs. {PREMIUM_PRICE}.",
        )

    successful_statuses = {
        "success",
        "successful",
        "completed",
        "complete",
        "paid",
        "sent",
    }

    if status not in successful_statuses:

        return (
            False,
            "Payment status is not shown as successful.",
        )

    expected_recipient = get_secret(
        "EXPECTED_PAYMENT_RECIPIENT",
        "",
    )

    if expected_recipient:

        if (
            recipient.lower()
            != expected_recipient.lower()
        ):

            return (
                False,
                "Payment recipient does not match "
                "the configured recipient.",
            )

    return (
        True,
        "Payment verification checks passed.",
    )


# ============================================================
# ACCESS
# ============================================================

def allowed_days(
    requested_days,
    payment_verified,
):

    requested_days = max(
        1,
        min(
            int(requested_days),
            MAX_TRIP_DAYS,
        ),
    )

    if requested_days == 1:
        return 1

    if payment_verified:
        return requested_days

    return 1


# ============================================================
# SESSION STATE
# ============================================================

if "payment_verified" not in st.session_state:
    st.session_state.payment_verified = False

if "trip_result" not in st.session_state:
    st.session_state.trip_result = ""

if "trip_sources" not in st.session_state:
    st.session_state.trip_sources = []

if "payment_result" not in st.session_state:
    st.session_state.payment_result = None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "# 🌿 TrekTales"
    )

    st.caption(
        "AI-Powered Tourism Planner"
    )

    st.divider()

    st.markdown(
        "### 🔓 Access"
    )

    if st.session_state.payment_verified:

        st.success(
            "Premium unlocked"
        )

    else:

        st.info(
            f"Day 1 free\n\n"
            f"Days 2–10: Rs. {PREMIUM_PRICE}"
        )

    st.divider()

    response_language = st.selectbox(
        "Response Language",
        [
            "English",
            "Urdu",
            "Roman Urdu",
        ],
    )

    st.divider()

    st.markdown(
        "### 🤖 8-Agent Architecture"
    )

    for number, name, role in [
        ("01", "Master Orchestrator", "Coordinates workflow."),
        ("02", "Knowledge Agent", "Retrieves FAISS evidence."),
        ("03", "Planner Agent", "Creates itinerary."),
        ("04", "Budget Agent", "Handles supported budget data."),
        ("05", "Safety Agent", "Handles supported safety data."),
        ("06", "Summarizer Agent", "Organizes final answer."),
        ("07", "Payment Agent", "Controls premium access."),
        ("08", "Vision Agent", "Reads payment screenshots."),
    ]:

        st.markdown(
            f"**{number}. {name}**"
        )

        st.caption(
            role
        )

    st.divider()

    st.markdown(
        "### ⚡ Groq"
    )

    st.code(
        get_secret(
            "GROQ_MODEL",
            DEFAULT_GROQ_MODEL,
        ),
        language="text",
    )


# ============================================================
# MAIN HEADER
# ============================================================

st.title(
    "🌿 TrekTales"
)

st.subheader(
    "Plan smarter. Travel better."
)

st.write(
    "Create personalized travel itineraries "
    "using your tourism knowledge base and "
    "Groq-powered AI."
)


# ============================================================
# METRICS
# ============================================================

metric1, metric2, metric3, metric4 = st.columns(4)

with metric1:
    st.metric(
        "Free",
        "Day 1",
    )

with metric2:
    st.metric(
        "Premium",
        f"Rs. {PREMIUM_PRICE}",
    )

with metric3:
    st.metric(
        "Maximum Trip",
        "10 Days",
    )

with metric4:
    st.metric(
        "AI Agents",
        "8",
    )


# ============================================================
# FEATURES
# ============================================================

st.markdown(
    "## ✨ TrekTales Features"
)

feature1, feature2, feature3 = st.columns(3)

with feature1:

    st.markdown(
        "### 🧠 Knowledge Grounding"
    )

    st.write(
        "The itinerary is generated from "
        "retrieved FAISS knowledge-base content."
    )

with feature2:

    st.markdown(
        "### 🗺️ Personalized Plans"
    )

    st.write(
        "Choose destination, duration, travelers, "
        "budget, style and interests."
    )

with feature3:

    st.markdown(
        "### 🛡️ Anti-Hallucination Rules"
    )

    st.write(
        "The AI is instructed not to invent "
        "unsupported tourism information."
    )


# ============================================================
# SYSTEM STATUS
# ============================================================

st.markdown(
    "## ⚙️ System Status"
)

status1, status2, status3 = st.columns(3)

groq_available = bool(
    get_secret(
        "GROQ_API_KEY",
        "",
    )
)

faiss_available = (
    FAISS_INDEX_PATH.exists()
    and METADATA_PATH.exists()
)

with status1:

    if groq_available:
        st.success(
            "🟢 Groq API configured"
        )
    else:
        st.error(
            "🔴 GROQ_API_KEY missing"
        )

with status2:

    if faiss_available:
        st.success(
            "🟢 FAISS files found"
        )
    else:
        st.error(
            "🔴 FAISS files missing"
        )

with status3:

    st.success(
        "🟢 TrekTales ready"
    )


# ============================================================
# TRIP INPUTS
# ============================================================

st.markdown(
    "## 🧭 Build Your Trip"
)

col1, col2 = st.columns(2)

with col1:

    destination = st.text_input(
        "Destination",
        placeholder="Example: Rawalpindi",
    )

with col2:

    starting_location = st.text_input(
        "Starting Location",
        placeholder="Example: Islamabad",
    )


col3, col4, col5 = st.columns(3)

with col3:

    trip_days = st.number_input(
        "Number of Days",
        min_value=1,
        max_value=MAX_TRIP_DAYS,
        value=1,
        step=1,
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
        "Budget",
        [
            "Budget",
            "Standard",
            "Comfort",
            "Premium",
        ],
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


interest_options = [
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
    "Road Trips",
]


interests_selected = st.multiselect(
    "Interests",
    interest_options,
)

other_interest = st.text_input(
    "Other Interests",
    placeholder="Example: local markets",
)


interests = list(
    interests_selected
)

if other_interest.strip():

    interests.append(
        clean_text(
            other_interest
        )
    )

if interests:

    interests_text = ", ".join(
        interests
    )

else:

    interests_text = (
        "General sightseeing and exploration"
    )


# ============================================================
# PREMIUM STATUS
# ============================================================

requested_days = int(
    trip_days
)

if requested_days > FREE_DAYS:

    if st.session_state.payment_verified:

        st.success(
            f"🔓 Premium unlocked for "
            f"{requested_days} days."
        )

    else:

        st.warning(
            f"🔒 Day 1 is free. "
            f"Days 2–{requested_days} are locked. "
            f"Premium verification costs "
            f"Rs. {PREMIUM_PRICE}."
        )


# ============================================================
# GENERATE
# ============================================================

st.markdown(
    "## 🚀 Generate Itinerary"
)

generate = st.button(
    "🌿 Generate My TrekTales Plan",
    use_container_width=True,
)


if generate:

    if not destination.strip():

        st.error(
            "Please enter a destination."
        )

    elif not starting_location.strip():

        st.error(
            "Please enter a starting location."
        )

    elif not groq_available:

        st.error(
            "GROQ_API_KEY is missing. "
            "Add it to Streamlit Secrets."
        )

    elif not faiss_available:

        st.error(
            "FAISS files were not found. "
            "Make sure faiss_db contains "
            "index.faiss and metadata.json."
        )

    else:

        days_to_generate = allowed_days(
            requested_days,
            st.session_state.payment_verified,
        )

        try:

            retrieval_query = (
                f"Destination: {destination}\n"
                f"Starting location: {starting_location}\n"
                f"Trip length: {days_to_generate} days\n"
                f"Travelers: {travelers}\n"
                f"Budget: {budget}\n"
                f"Travel style: {travel_style}\n"
                f"Interests: {interests_text}"
            )

            with st.spinner(
                "🔎 Searching the TrekTales knowledge base..."
            ):

                retrieved = retrieve(
                    retrieval_query,
                    TOP_K,
                )

            if not retrieved:

                st.error(
                    "No relevant information was found "
                    "in the TrekTales knowledge base. "
                    "The app will not invent an itinerary."
                )

            else:

                context = make_context(
                    retrieved
                )

                with st.spinner(
                    "🤖 TrekTales AI agents are preparing your plan..."
                ):

                    result = generate_itinerary(
                        destination=destination,
                        starting_location=starting_location,
                        days=days_to_generate,
                        travelers=int(travelers),
                        budget=budget,
                        travel_style=travel_style,
                        interests=interests_text,
                        language=response_language,
                        context=context,
                    )

                if not result.strip():

                    st.error(
                        "The AI returned an empty response."
                    )

                else:

                    st.session_state.trip_result = (
                        result
                    )

                    st.session_state.trip_sources = (
                        retrieved
                    )

                    if (
                        requested_days > FREE_DAYS
                        and not st.session_state.payment_verified
                    ):

                        st.info(
                            f"Only Day 1 is available "
                            f"without premium verification. "
                            f"Days 2–{requested_days} remain locked."
                        )

                    else:

                        st.success(
                            f"Your {days_to_generate}-day "
                            "itinerary is ready."
                        )

        except FileNotFoundError as exc:

            st.error(
                str(exc)
            )

        except RuntimeError as exc:

            st.error(
                str(exc)
            )

        except Exception as exc:

            st.error(
                "The itinerary could not be generated."
            )

            with st.expander(
                "Technical details"
            ):

                st.code(
                    str(exc),
                    language="text",
                )


# ============================================================
# DISPLAY ITINERARY
# ============================================================

if st.session_state.trip_result:

    st.markdown(
        "## 🗺️ Your TrekTales Itinerary"
    )

    result = clean_ai_response(
        st.session_state.trip_result
    )

    st.markdown(
        result
    )

    st.markdown(
        "## 📚 Knowledge Sources"
    )

    displayed_sources = set()

    for item in st.session_state.trip_sources:

        source = clean_text(
            item.get(
                "source",
                "Unknown source",
            )
        )

        page = clean_text(
            item.get(
                "page",
                "",
            )
        )

        source_key = (
            source,
            page,
        )

        if source_key in displayed_sources:
            continue

        displayed_sources.add(
            source_key
        )

        if page:

            st.write(
                f"📄 {source} — Page {page}"
            )

        else:

            st.write(
                f"📄 {source}"
            )


# ============================================================
# PREMIUM PAYMENT
# ============================================================

if requested_days >= 2:

    st.markdown(
        "## 🔓 Unlock Premium Days"
    )

    if st.session_state.payment_verified:

        st.success(
            "✅ Premium access is already unlocked."
        )

    else:

        payment_col1, payment_col2 = st.columns(
            [1, 1.4]
        )

        with payment_col1:

            st.markdown(
                "### TrekTales Premium"
            )

            st.write(
                f"Unlock Days 2–{requested_days}."
            )

            st.markdown(
                f"### Rs. {PREMIUM_PRICE}"
            )

            if QR_PATH.exists():

                st.image(
                    str(QR_PATH),
                    caption="JazzCash Payment QR",
                    use_container_width=True,
                )

            else:

                st.warning(
                    "JazzCash QR image was not found."
                )

        with payment_col2:

            st.markdown(
                "### 📤 Payment Verification"
            )

            st.write(
                "Upload your payment screenshot. "
                "The Vision Agent will read the visible "
                "payment information."
            )

            payment_image = st.file_uploader(
                "Upload payment screenshot",
                type=[
                    "png",
                    "jpg",
                    "jpeg",
                    "webp",
                ],
                key="payment_image",
            )

            if payment_image:

                verify_button = st.button(
                    "🔍 Verify Payment",
                    use_container_width=True,
                )

                if verify_button:

                    try:

                        with st.spinner(
                            "👁️ Reading payment screenshot..."
                        ):

                            payment_data = (
                                analyze_payment(
                                    payment_image
                                )
                            )

                        if not payment_data:

                            st.error(
                                "No payment information "
                                "could be extracted."
                            )

                        else:

                            st.session_state.payment_result = (
                                payment_data
                            )

                            st.write(
                                "Detected payment information:"
                            )

                            st.json(
                                payment_data
                            )

                            verified, message = (
                                verify_payment(
                                    payment_data
                                )
                            )

                            if verified:

                                st.session_state.payment_verified = (
                                    True
                                )

                                st.success(
                                    "✅ Payment verification "
                                    "checks passed."
                                )

                                st.rerun()

                            else:

                                st.error(
                                    f"❌ {message}"
                                )

                    except Exception as exc:

                        st.error(
                            "Payment verification failed."
                        )

                        with st.expander(
                            "Technical details"
                        ):

                            st.code(
                                str(exc),
                                language="text",
                            )


# ============================================================
# LOCK MESSAGE
# ============================================================

if (
    requested_days > FREE_DAYS
    and not st.session_state.payment_verified
):

    st.warning(
        f"Days 2–{requested_days} are locked. "
        f"Complete the Rs. {PREMIUM_PRICE} "
        "premium verification to unlock them."
    )


# ============================================================
# DISCLAIMER
# ============================================================

st.markdown(
    "## ⚠️ Travel Information Notice"
)

st.info(
    "TrekTales uses the available tourism knowledge base "
    "to generate travel suggestions. Information such as "
    "prices, availability, schedules, weather and local "
    "conditions can change. Verify important details before "
    "travelling."
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🌿 TrekTales AI • FAISS • Sentence Transformers • Groq"
)
