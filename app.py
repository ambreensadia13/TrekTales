from pathlib import Path
import json
import re

import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="TrekTales AI",
    page_icon="🥾",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent

SRC_DIR = ROOT_DIR / "src"
ASSETS_DIR = ROOT_DIR / "assets"
KNOWLEDGE_BASE_DIR = ROOT_DIR / "tourism_knowledge_base"

FAISS_DIR = ROOT_DIR / "faiss_db"
FAISS_INDEX_PATH = FAISS_DIR / "index.faiss"
METADATA_PATH = FAISS_DIR / "metadata.json"
FAISS_CONFIG_PATH = FAISS_DIR / "config.json"

PAYMENT_QR_PATH = ASSETS_DIR / "jazzcash_qr.jpg"


# ============================================================
# IMPORT CONFIG
# ============================================================

try:
    from src.config import (
        FREE_DAYS,
        MAX_TRIP_DAYS,
        UNLOCK_PRICE,
        GROQ_API_KEY,
        GROQ_MODEL,
        GROQ_VISION_MODEL,
        GROQ_BASE_URL,
        EXPECTED_PAYMENT_RECIPIENT,
        TOP_K,
        validate_trip_days,
        get_accessible_days,
        payment_required,
        faiss_files_exist,
        get_faiss_status,
    )
except Exception as config_error:
    st.error("TrekTales configuration could not be loaded.")
    st.code(str(config_error))
    st.stop()


# ============================================================
# OPTIONAL IMPORTS
# ============================================================

try:
    from groq import Groq
except Exception:
    Groq = None


# ============================================================
# SESSION STATE
# ============================================================

if "payment_verified" not in st.session_state:
    st.session_state.payment_verified = False

if "payment_data" not in st.session_state:
    st.session_state.payment_data = None

if "trip_result" not in st.session_state:
    st.session_state.trip_result = None

if "retriever_error" not in st.session_state:
    st.session_state.retriever_error = None


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    :root {
        --red: #DA2C38;
        --green: #226F54;
        --light-green: #87C38F;
        --cream: #F4F0BB;
        --brown: #43291F;
        --dark: #17231D;
        --white: #FFFFFF;
    }

    .stApp {
        background:
            radial-gradient(
                circle at top right,
                rgba(135, 195, 143, 0.18),
                transparent 30%
            ),
            linear-gradient(
                135deg,
                #17231D 0%,
                #226F54 55%,
                #43291F 100%
            );
        color: white;
    }

    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3, h4 {
        color: white !important;
    }

    p, li, label {
        color: #F4F0BB !important;
    }

    .hero {
        padding: 2.5rem;
        border-radius: 28px;
        background:
            linear-gradient(
                135deg,
                rgba(218, 44, 56, 0.95),
                rgba(34, 111, 84, 0.95)
            );
        box-shadow:
            0 20px 60px rgba(0,0,0,0.25);
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255,255,255,0.15);
    }

    .hero h1 {
        font-size: 3.2rem;
        margin-bottom: 0.4rem;
        font-weight: 800;
    }

    .hero p {
        font-size: 1.15rem;
        color: white !important;
        margin-bottom: 0;
    }

    .card {
        background: rgba(255,255,255,0.10);
        border: 1px solid rgba(255,255,255,0.14);
        border-radius: 20px;
        padding: 1.4rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(12px);
    }

    .result-card {
        background: #FFFFFF;
        color: #43291F;
        border-radius: 22px;
        padding: 2rem;
        margin-top: 1rem;
        box-shadow: 0 18px 45px rgba(0,0,0,0.18);
    }

    .result-card h2,
    .result-card h3,
    .result-card h4 {
        color: #43291F !important;
    }

    .result-card p,
    .result-card li {
        color: #43291F !important;
    }

    .day-card {
        background: #F4F0BB;
        color: #43291F;
        border-left: 7px solid #DA2C38;
        border-radius: 16px;
        padding: 1.25rem;
        margin: 1rem 0;
    }

    .day-card h3 {
        color: #226F54 !important;
        margin-top: 0;
    }

    .source-card {
        background: rgba(135,195,143,0.14);
        border: 1px solid rgba(135,195,143,0.35);
        border-radius: 14px;
        padding: 0.9rem 1rem;
        margin-top: 0.5rem;
    }

    .source-card p {
        margin: 0;
        color: #F4F0BB !important;
        font-size: 0.9rem;
    }

    .status-ok {
        background: rgba(135,195,143,0.18);
        border: 1px solid #87C38F;
        color: #F4F0BB;
        border-radius: 14px;
        padding: 0.9rem;
    }

    .status-warning {
        background: rgba(218,44,56,0.18);
        border: 1px solid #DA2C38;
        color: #F4F0BB;
        border-radius: 14px;
        padding: 0.9rem;
    }

    .premium-box {
        background:
            linear-gradient(
                135deg,
                rgba(218,44,56,0.24),
                rgba(67,41,31,0.45)
            );
        border: 1px solid rgba(218,44,56,0.65);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
    }

    .stButton > button {
        width: 100%;
        border: none;
        border-radius: 12px;
        font-weight: 700;
        padding: 0.75rem 1rem;
        background: #DA2C38;
        color: white;
    }

    .stButton > button:hover {
        background: #226F54;
        color: white;
    }

    div[data-testid="stSidebar"] {
        background: #17231D;
    }

    div[data-testid="stSidebar"] * {
        color: #F4F0BB;
    }

    .small-muted {
        font-size: 0.85rem;
        opacity: 0.8;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

def clean_text(text):
    """Clean common markdown artifacts from model output."""
    if text is None:
        return ""

    text = str(text)

    text = text.replace("**", "")
    text = text.replace("###", "")
    text = text.replace("##", "")
    text = text.replace("# ", "")

    return text.strip()


def safe_json_load(path):
    """Safely load JSON."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return None


def normalize_record(record):
    """Normalize one RAG record."""
    if not isinstance(record, dict):
        return {
            "text": str(record),
            "source": "Unknown source",
            "page": "N/A",
        }

    metadata = record.get("metadata", {})

    if not isinstance(metadata, dict):
        metadata = {}

    text = (
        record.get("text")
        or record.get("content")
        or record.get("page_content")
        or ""
    )

    source = (
        record.get("source")
        or metadata.get("source")
        or "Unknown source"
    )

    page = (
        record.get("page")
        or metadata.get("page")
        or "N/A"
    )

    return {
        "text": str(text),
        "source": str(source),
        "page": str(page),
        "department": str(
            record.get(
                "department",
                metadata.get("department", ""),
            )
        ),
        "record_id": str(
            record.get(
                "record_id",
                metadata.get("record_id", ""),
            )
        ),
    }


def get_metadata_records():
    """Load metadata for emergency fallback retrieval."""
    data = safe_json_load(METADATA_PATH)

    if isinstance(data, list):
        return [normalize_record(x) for x in data]

    if isinstance(data, dict):

        for key in (
            "metadata",
            "documents",
            "items",
            "records",
        ):
            value = data.get(key)

            if isinstance(value, list):
                return [
                    normalize_record(x)
                    for x in value
                ]

    return []


def keyword_fallback_search(query, records, top_k=6):
    """
    Emergency fallback when the semantic retriever cannot load.

    This is only a fallback. The normal application uses FAISS.
    """

    if not query or not records:
        return []

    words = set(
        re.findall(
            r"[a-zA-Z0-9]+",
            query.lower(),
        )
    )

    words = {
        word
        for word in words
        if len(word) >= 3
    }

    scored = []

    for record in records:

        text = record.get(
            "text",
            "",
        ).lower()

        if not text:
            continue

        score = sum(
            1
            for word in words
            if word in text
        )

        if score > 0:
            scored.append(
                (
                    score,
                    record,
                )
            )

    scored.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return [
        record
        for _, record in scored[:top_k]
    ]


# ============================================================
# RETRIEVER
# ============================================================

@st.cache_resource(
    show_spinner="Loading TrekTales knowledge base..."
)
def load_retriever():

    from src.retriever import HybridRetriever

    return HybridRetriever(
        index_path=FAISS_INDEX_PATH,
        metadata_path=METADATA_PATH,
        config_path=FAISS_CONFIG_PATH,
    )


def retrieve_context(query):

    if not faiss_files_exist():
        raise FileNotFoundError(
            "FAISS files are missing. "
            "Required: index.faiss, metadata.json and config.json."
        )

    retriever = load_retriever()

    results = retriever.search(
        query,
        top_k=TOP_K,
    )

    return results


# ============================================================
# GROQ
# ============================================================

@st.cache_resource(show_spinner=False)
def get_groq_client():

    if Groq is None:
        raise RuntimeError(
            "The groq package is not installed."
        )

    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not configured in Streamlit Secrets."
        )

    return Groq(
        api_key=GROQ_API_KEY
    )


def generate_itinerary(
    destination,
    days,
    travelers,
    interests,
    budget,
    retrieved_records,
):

    if not retrieved_records:
        return (
            "I could not find enough information in the "
            "TrekTales knowledge base to build this itinerary."
        )

    context_parts = []

    for number, record in enumerate(
        retrieved_records,
        start=1,
    ):

        source = record.get(
            "source",
            "Unknown source",
        )

        page = record.get(
            "page",
            "N/A",
        )

        text = record.get(
            "text",
            "",
        )

        context_parts.append(
            f"""
SOURCE {number}
File: {source}
Page: {page}

CONTENT:
{text}
"""
        )

    context = "\n".join(
        context_parts
    )

    prompt = f"""
You are TrekTales, a grounded tourism itinerary assistant.

IMPORTANT RULES:

1. Use ONLY the supplied knowledge-base context.
2. Do NOT invent hotels, restaurants, attractions,
   prices, opening hours, distances, transport details,
   phone numbers, addresses or other tourism facts.
3. If something is not present in the context,
   clearly say that it is not available in the
   TrekTales knowledge base.
4. The requested number of days is exactly {days}.
5. Create exactly {days} day sections.
6. Do not create extra days.
7. Do not mention hidden or locked days.
8. Do not fabricate activities just to fill a day.
9. Clearly distinguish information from the knowledge base
   from suggestions.
10. Since the knowledge base may contain demo/fictitious
    records, do not claim that the information has been
    independently verified in the real world.
11. Keep the itinerary practical and easy to read.

TRIP REQUEST

Destination:
{destination}

Number of days:
{days}

Travelers:
{travelers}

Interests:
{interests}

Budget:
{budget}

KNOWLEDGE BASE:

{context}

OUTPUT FORMAT

Create:

# TrekTales Itinerary

## Day 1
Morning:
Afternoon:
Evening:

## Day 2
Morning:
Afternoon:
Evening:

Continue only until Day {days}.

At the end provide:

## Important Notes

Keep the response concise and useful.
"""

    client = get_groq_client()

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a grounded tourism "
                    "planning assistant. "
                    "Never invent facts."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
        max_tokens=2500,
    )

    if not response.choices:
        raise RuntimeError(
            "Groq returned no response."
        )

    content = (
        response.choices[0]
        .message
        .content
    )

    return clean_text(content)


# ============================================================
# PAYMENT
# ============================================================

def process_payment_screenshot(uploaded_file):

    if uploaded_file is None:
        return

    try:

        from src.vision import (
            analyze_payment_screenshot,
        )

        from src.payment import (
            verify_payment,
        )

        image_bytes = uploaded_file.getvalue()

        with st.spinner(
            "Reading the payment screenshot..."
        ):

            extracted = analyze_payment_screenshot(
                image_bytes
            )

        verification = verify_payment(
            extracted
        )

        st.session_state.payment_data = {
            "extracted": extracted,
            "verification": verification,
        }

        if verification.get(
            "verified",
            False,
        ):

            st.session_state.payment_verified = True

            st.success(
                "Payment information passed the required checks. "
                "Premium itinerary access is unlocked."
            )

        else:

            st.session_state.payment_verified = False

            st.error(
                verification.get(
                    "reason",
                    "Payment could not be verified.",
                )
            )

    except Exception as error:

        st.session_state.payment_verified = False

        st.error(
            "Payment verification could not be completed."
        )

        with st.expander(
            "Technical details"
        ):
            st.code(str(error))


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "## 🥾 TrekTales"
    )

    st.caption(
        "AI-powered tourism itinerary planner"
    )

    st.divider()

    st.markdown(
        "### Knowledge Base"
    )

    status = get_faiss_status()

    if status["ready"]:

        st.success(
            "FAISS database ready"
        )

    else:

        st.warning(
            "FAISS database is incomplete"
        )

    st.write(
        f"Index: {'✓' if status['index'] else '✗'}"
    )

    st.write(
        f"Metadata: {'✓' if status['metadata'] else '✗'}"
    )

    st.write(
        f"Config: {'✓' if status['config'] else '✗'}"
    )

    st.divider()

    st.markdown(
        "### Access"
    )

    if st.session_state.payment_verified:

        st.success(
            "Premium unlocked"
        )

    else:

        st.info(
            f"Day 1 is free. Days 2–{MAX_TRIP_DAYS} "
            f"require Rs. {UNLOCK_PRICE}."
        )


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="hero">

        <h1>🥾 TrekTales AI</h1>

        <p>
            Build grounded travel itineraries using
            your TrekTales tourism knowledge base.
        </p>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# INPUT CARD
# ============================================================

st.markdown(
    "## ✈️ Plan Your Trip"
)

with st.container():

    col1, col2 = st.columns(
        2
    )

    with col1:

        destination = st.text_input(
            "Destination",
            placeholder="Example: Rawalpindi",
        )

        travelers = st.number_input(
            "Number of Travelers",
            min_value=1,
            max_value=20,
            value=2,
            step=1,
        )

        budget = st.selectbox(
            "Budget",
            [
                "Budget",
                "Moderate",
                "Premium",
            ],
        )

    with col2:

        requested_days = st.slider(
            "Trip Duration",
            min_value=1,
            max_value=MAX_TRIP_DAYS,
            value=1,
        )

        interests = st.multiselect(
            "Interests",
            [
                "Adventure",
                "Food",
                "Culture",
                "Sports",
                "Nature",
                "Shopping",
                "Family",
                "Relaxation",
            ],
            default=[
                "Culture"
            ],
        )


# ============================================================
# PAYMENT SECTION
# ============================================================

requires_payment = payment_required(
    requested_days,
    st.session_state.payment_verified,
)


if requires_payment:

    st.markdown(
        """
        <div class="premium-box">

        <h3>🔐 Premium Days Locked</h3>

        <p>
        Your selected trip requires access beyond the
        free Day 1. Unlock the premium itinerary for
        <strong>Rs. 199</strong>.
        </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    payment_col1, payment_col2 = st.columns(
        2
    )

    with payment_col1:

        st.markdown(
            "### 📱 Payment"
        )

        if PAYMENT_QR_PATH.exists():

            st.image(
                str(PAYMENT_QR_PATH),
                caption=(
                    "Scan the TrekTales payment QR"
                ),
                width=280,
            )

        else:

            st.warning(
                "Payment QR image was not found."
            )

        st.write(
            f"Amount: Rs. {UNLOCK_PRICE}"
        )

        st.write(
            "Recipient is configured through "
            "Streamlit Secrets."
        )

    with payment_col2:

        st.markdown(
            "### 🧾 Verify Payment"
        )

        uploaded_payment = st.file_uploader(
            "Upload your payment screenshot",
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp",
            ],
            key="payment_upload",
        )

        if st.button(
            "🔎 Verify Payment",
            key="verify_payment",
        ):

            if uploaded_payment is None:

                st.warning(
                    "Please upload a payment screenshot first."
                )

            else:

                process_payment_screenshot(
                    uploaded_payment
                )


# ============================================================
# PAYMENT STATUS
# ============================================================

if st.session_state.payment_verified:

    st.markdown(
        """
        <div class="status-ok">

        <strong>✓ Premium access unlocked</strong>

        <br>

        You can now generate the complete
        requested itinerary.

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# GENERATION BUTTON
# ============================================================

st.markdown(
    ""
)

generate_clicked = st.button(
    "🥾 Generate TrekTales Itinerary",
    type="primary",
)


# ============================================================
# GENERATE ITINERARY
# ============================================================

if generate_clicked:

    if not destination.strip():

        st.warning(
            "Please enter a destination."
        )
        st.stop()

    requested_days = validate_trip_days(
        requested_days
    )

    accessible_days = get_accessible_days(
        requested_days,
        st.session_state.payment_verified,
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # Do not generate locked days.
    # --------------------------------------------------------

    if (
        requested_days > accessible_days
        and not st.session_state.payment_verified
    ):

        st.info(
            "Only Day 1 is available until premium access "
            "is unlocked. Generate Day 1 now or verify "
            "your payment above for the complete trip."
        )

        days_to_generate = accessible_days

    else:

        days_to_generate = requested_days

    query_parts = [
        destination,
        "tourism",
    ]

    if interests:
        query_parts.extend(
            interests
        )

    if budget:
        query_parts.append(
            budget
        )

    query = " ".join(
        query_parts
    )

    # --------------------------------------------------------
    # RAG
    # --------------------------------------------------------

    try:

        with st.spinner(
            "Searching the TrekTales knowledge base..."
        ):

            try:

                records = retrieve_context(
                    query
                )

                st.session_state.retriever_error = None

            except Exception as rag_error:

                st.session_state.retriever_error = str(
                    rag_error
                )

                fallback_records = (
                    get_metadata_records()
                )

                records = keyword_fallback_search(
                    query,
                    fallback_records,
                    top_k=TOP_K,
                )

        if not records:

            st.error(
                "No relevant information was found "
                "in the TrekTales knowledge base."
            )

            if st.session_state.retriever_error:

                with st.expander(
                    "Retrieval diagnostic"
                ):
                    st.code(
                        st.session_state.retriever_error
                    )

            st.stop()

        # ----------------------------------------------------
        # GROQ
        # ----------------------------------------------------

        with st.spinner(
            "Creating your grounded itinerary..."
        ):

            result = generate_itinerary(
                destination=destination,
                days=days_to_generate,
                travelers=travelers,
                interests=", ".join(
                    interests
                )
                if interests
                else "General sightseeing",
                budget=budget,
                retrieved_records=records,
            )

        st.session_state.trip_result = {
            "text": result,
            "records": records,
            "requested_days": requested_days,
            "generated_days": days_to_generate,
        }

    except Exception as error:

        st.error(
            "TrekTales could not generate the itinerary."
        )

        with st.expander(
            "Technical details"
        ):
            st.code(
                str(error)
            )


# ============================================================
# DISPLAY RESULT
# ============================================================

trip_result = st.session_state.trip_result


if trip_result:

    st.markdown(
        "---"
    )

    st.markdown(
        "## 🗺️ Your TrekTales Itinerary"
    )

    generated_days = trip_result.get(
        "generated_days",
        1,
    )

    requested_days_result = trip_result.get(
        "requested_days",
        generated_days,
    )

    if (
        requested_days_result
        > generated_days
        and not st.session_state.payment_verified
    ):

        st.warning(
            f"Day 1 is shown because your requested "
            f"{requested_days_result}-day trip includes "
            f"premium days that are still locked."
        )

    st.markdown(
        '<div class="result-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        trip_result.get(
            "text",
            "",
        )
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # SOURCES
    # --------------------------------------------------------

    st.markdown(
        "### 📚 Knowledge Sources"
    )

    displayed_sources = set()

    for record in trip_result.get(
        "records",
        [],
    ):

        source = str(
            record.get(
                "source",
                "Unknown source",
            )
        )

        page = str(
            record.get(
                "page",
                "N/A",
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

        st.markdown(
            f"""
            <div class="source-card">

            <p>
            📄 <strong>{source}</strong>
            &nbsp; | &nbsp;
            Page: {page}
            </p>

            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    "---"
)

st.caption(
    "TrekTales AI • Grounded in your tourism knowledge base • "
    "AI-generated information should be independently verified."
)
