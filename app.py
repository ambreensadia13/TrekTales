from pathlib import Path
import json
import re

import streamlit as st


# ============================================================
# TREKTALES PROJECT PATH
# ============================================================

# app.py is located directly inside the repository root.
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
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="TrekTales AI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* Main application */
    .stApp {
        background:
            radial-gradient(
                circle at top left,
                rgba(135, 195, 143, 0.16),
                transparent 32%
            ),
            linear-gradient(
                135deg,
                #43291F 0%,
                #226F54 48%,
                #43291F 100%
            );
        color: #F4F0BB;
    }

    /* Hide Streamlit chrome */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        visibility: hidden;
    }

    /* Main content */
    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Hero */
    .hero {
        padding: 2.5rem;
        border-radius: 28px;
        background:
            linear-gradient(
                135deg,
                rgba(67, 41, 31, 0.94),
                rgba(34, 111, 84, 0.92)
            );
        border: 1px solid rgba(244, 240, 187, 0.18);
        box-shadow:
            0 20px 60px rgba(0, 0, 0, 0.30);
        margin-bottom: 1.5rem;
    }

    .hero h1 {
        color: #F4F0BB;
        font-size: 3.2rem;
        margin-bottom: 0.4rem;
        font-weight: 800;
    }

    .hero p {
        color: #F4F0BB;
        opacity: 0.9;
        font-size: 1.1rem;
        margin: 0;
    }

    /* Cards */
    .card {
        background: rgba(67, 41, 31, 0.82);
        border: 1px solid rgba(135, 195, 143, 0.28);
        border-radius: 20px;
        padding: 1.4rem;
        margin: 0.7rem 0;
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.18);
    }

    .card h3 {
        color: #F4F0BB;
        margin-top: 0;
    }

    .card p {
        color: #F4F0BB;
    }

    /* Day cards */
    .day-card {
        background: #F4F0BB;
        color: #43291F;
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.18);
    }

    .day-card h2 {
        color: #226F54;
        margin-top: 0;
    }

    .day-card p {
        color: #43291F;
    }

    /* Status */
    .status-good {
        background: rgba(135, 195, 143, 0.18);
        border: 1px solid #87C38F;
        color: #F4F0BB;
        padding: 0.8rem 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
    }

    .status-warning {
        background: rgba(218, 44, 56, 0.15);
        border: 1px solid #DA2C38;
        color: #F4F0BB;
        padding: 0.8rem 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #43291F;
    }

    section[data-testid="stSidebar"] * {
        color: #F4F0BB !important;
    }

    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        border: none;
        background: #DA2C38;
        color: #F4F0BB;
        font-weight: 700;
        padding: 0.7rem 1rem;
    }

    .stButton > button:hover {
        background: #226F54;
        color: #F4F0BB;
    }

    /* Inputs */
    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input {
        background: #F4F0BB !important;
        color: #43291F !important;
        border-radius: 10px !important;
    }

    /* Selectboxes */
    div[data-baseweb="select"] > div {
        background: #F4F0BB !important;
        color: #43291F !important;
        border-radius: 10px !important;
    }

    /* Divider */
    hr {
        border-color: rgba(244, 240, 187, 0.2);
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SAFE IMPORT OF CONFIG
# ============================================================

try:
    from src.config import (
        GROQ_API_KEY,
        GROQ_MODEL,
        GROQ_VISION_MODEL,
        EMBEDDING_MODEL,
        TOP_K,
        FREE_DAYS,
        MAX_TRIP_DAYS,
        UNLOCK_PRICE,
        get_faiss_status,
        validate_trip_days,
        get_accessible_days,
        payment_required,
    )

    CONFIG_ERROR = None

except Exception as exc:
    CONFIG_ERROR = str(exc)

    # Safe fallbacks so the UI can still start.
    GROQ_API_KEY = ""
    GROQ_MODEL = "openai/gpt-oss-120b"
    GROQ_VISION_MODEL = "qwen/qwen3.6-27b"
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    TOP_K = 6
    FREE_DAYS = 1
    MAX_TRIP_DAYS = 3
    UNLOCK_PRICE = 199

    def get_faiss_status():
        return {
            "directory": str(FAISS_DIR),
            "index": FAISS_INDEX_PATH.is_file(),
            "metadata": METADATA_PATH.is_file(),
            "config": FAISS_CONFIG_PATH.is_file(),
            "ready": (
                FAISS_INDEX_PATH.is_file()
                and METADATA_PATH.is_file()
                and FAISS_CONFIG_PATH.is_file()
            ),
        }

    def validate_trip_days(days):
        try:
            days = int(days)
        except Exception:
            days = 1

        return max(1, min(days, MAX_TRIP_DAYS))

    def get_accessible_days(
        requested_days,
        payment_verified=False,
    ):
        requested_days = validate_trip_days(requested_days)

        if requested_days == 1:
            return 1

        if payment_verified:
            return requested_days

        return 1

    def payment_required(
        requested_days,
        payment_verified=False,
    ):
        requested_days = validate_trip_days(requested_days)

        return requested_days > 1 and not payment_verified


# ============================================================
# SESSION STATE
# ============================================================

if "payment_verified" not in st.session_state:
    st.session_state.payment_verified = False

if "generated_plan" not in st.session_state:
    st.session_state.generated_plan = None

if "sources" not in st.session_state:
    st.session_state.sources = []

if "last_query" not in st.session_state:
    st.session_state.last_query = ""


# ============================================================
# LOAD FAISS METADATA
# ============================================================

@st.cache_data(show_spinner=False)
def load_metadata():
    """
    Load the existing FAISS metadata.json.

    This function does not create a new database.
    """

    if not METADATA_PATH.is_file():
        return []

    try:
        with open(
            METADATA_PATH,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            if isinstance(data.get("metadata"), list):
                return data["metadata"]

            if isinstance(data.get("documents"), list):
                return data["documents"]

            if isinstance(data.get("data"), list):
                return data["data"]

        return []

    except Exception:
        return []


# ============================================================
# NORMALIZE METADATA
# ============================================================

def normalize_metadata_item(item):
    """
    Convert different possible metadata formats into one
    predictable dictionary.
    """

    if isinstance(item, str):
        return {
            "text": item,
            "source": "Unknown",
            "page": None,
        }

    if not isinstance(item, dict):
        return {
            "text": "",
            "source": "Unknown",
            "page": None,
        }

    text = (
        item.get("text")
        or item.get("content")
        or item.get("document")
        or item.get("page_content")
        or ""
    )

    source = (
        item.get("source")
        or item.get("filename")
        or item.get("file")
        or item.get("file_name")
        or "Unknown"
    )

    page = (
        item.get("page")
        or item.get("page_number")
        or item.get("page_num")
    )

    return {
        "text": str(text),
        "source": str(source),
        "page": page,
    }


# ============================================================
# SIMPLE LOCAL RETRIEVAL
# ============================================================

def tokenize(text):
    return set(
        re.findall(
            r"[a-zA-Z0-9]+",
            text.lower(),
        )
    )


def keyword_score(query, document):
    """
    Lightweight keyword overlap.

    This is only a fallback display/search mechanism.
    The actual FAISS retriever can be connected later without
    changing the UI.
    """

    query_words = tokenize(query)
    document_words = tokenize(document)

    if not query_words or not document_words:
        return 0.0

    overlap = query_words.intersection(
        document_words
    )

    return len(overlap) / len(query_words)


def retrieve_local_context(
    query,
    top_k=6,
):
    """
    Retrieve relevant records from metadata.json.

    This prevents the interface from becoming unusable if the
    older src/retriever.py has an import mismatch.
    """

    metadata = load_metadata()

    if not metadata:
        return []

    normalized = [
        normalize_metadata_item(item)
        for item in metadata
    ]

    scored = []

    for item in normalized:
        text = item["text"]

        if not text.strip():
            continue

        score = keyword_score(
            query,
            text,
        )

        scored.append(
            (
                score,
                item,
            )
        )

    scored.sort(
        key=lambda value: value[0],
        reverse=True,
    )

    results = [
        item
        for score, item in scored[:top_k]
        if score > 0
    ]

    # If no keywords matched, return a small amount of context
    # rather than inventing information.
    if not results:
        results = [
            item
            for _, item in scored[: min(3, top_k)]
        ]

    return results


# ============================================================
# GROQ CLIENT
# ============================================================

@st.cache_resource(show_spinner=False)
def get_groq_client():
    """
    Create a Groq client only when a key exists.
    """

    if not GROQ_API_KEY:
        return None

    try:
        from groq import Groq

        return Groq(
            api_key=GROQ_API_KEY
        )

    except Exception:
        return None


# ============================================================
# ITINERARY GENERATION
# ============================================================

def generate_itinerary(
    destination,
    days,
    preferences,
):
    """
    Generate an itinerary using ONLY retrieved knowledge-base
    information.

    The number of days is controlled by Python, not by the LLM.
    """

    client = get_groq_client()

    if client is None:
        return None, (
            "Groq API key is not configured or the Groq "
            "client could not be initialized."
        )

    context_items = retrieve_local_context(
        f"{destination} {preferences}",
        top_k=TOP_K,
    )

    if not context_items:
        return None, (
            "No relevant information was found in the "
            "TrekTales knowledge base. I will not invent "
            "tourism information."
        )

    context_parts = []

    for item in context_items:
        source = item["source"]
        page = item["page"]

        location = source

        if page is not None:
            location = f"{source}, page {page}"

        context_parts.append(
            f"SOURCE: {location}\n"
            f"CONTENT:\n{item['text']}"
        )

    context = "\n\n---\n\n".join(
        context_parts
    )

    prompt = f"""
You are TrekTales, a tourism itinerary assistant.

IMPORTANT RULES:

1. Use ONLY the supplied knowledge-base context.
2. Do NOT invent hotels, restaurants, prices,
   opening hours, distances, travel times, attractions,
   safety claims, or other facts.
3. If something is not in the context, say:
   "Not available in the TrekTales knowledge base."
4. Produce EXACTLY {days} itinerary day sections.
5. Do not create extra days.
6. Do not mention hidden or locked days.
7. Keep recommendations practical and concise.
8. Use the user's preferences when supported by the context.
9. Treat source content as the authority.

Destination:
{destination}

Preferences:
{preferences}

Knowledge-base context:
{context}

Return the itinerary with headings:

Day 1
Day 2
Day 3

Only include headings up to Day {days}.
"""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a grounded tourism planning "
                        "assistant. Never invent facts."
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

        answer = (
            response.choices[0]
            .message
            .content
        )

        if not answer:
            return None, "Groq returned an empty response."

        return answer, None

    except Exception as exc:
        return None, (
            "Groq request failed. "
            f"Details: {exc}"
        )


# ============================================================
# EXTRACT SOURCES
# ============================================================

def get_sources(
    destination,
    preferences,
):
    """
    Return sources directly from metadata rather than allowing
    the LLM to manufacture citations.
    """

    results = retrieve_local_context(
        f"{destination} {preferences}",
        top_k=TOP_K,
    )

    sources = []

    for item in results:
        source = item["source"]

        if not source:
            continue

        source = Path(
            str(source)
        ).name

        if source not in sources:
            sources.append(source)

    return sources


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <h1>🌿 TrekTales</h1>
        <p>
            AI-powered travel planning grounded in your
            TrekTales tourism knowledge base.
        </p>
    </div>
    """,
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

    destination = st.text_input(
        "Destination",
        placeholder="e.g. Rawalpindi",
    )

    days = st.selectbox(
        "Trip duration",
        options=[1, 2, 3],
        index=0,
    )

    preferences = st.text_area(
        "Travel preferences",
        placeholder=(
            "e.g. family activities, culture, "
            "food, adventure..."
        ),
        height=120,
    )

    st.divider()

    st.markdown(
        "### Access"
    )

    if st.session_state.payment_verified:
        st.success(
            "Premium access unlocked"
        )
    else:
        st.info(
            "Day 1 is free.\n\n"
            "Days 2–3 require Rs. 199."
        )

    st.divider()

    st.markdown(
        "### Knowledge Base"
    )

    status = get_faiss_status()

    if status["ready"]:
        st.success(
            "FAISS database detected"
        )
    else:
        st.warning(
            "FAISS database is incomplete"
        )

    st.caption(
        f"Index: {'✓' if status['index'] else '✗'}"
    )

    st.caption(
        f"Metadata: {'✓' if status['metadata'] else '✗'}"
    )

    st.caption(
        f"Config: {'✓' if status['config'] else '✗'}"
    )


# ============================================================
# MAIN INFORMATION CARDS
# ============================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class="card">
            <h3>🗺️ Grounded Planning</h3>
            <p>
                TrekTales uses its tourism knowledge base
                instead of freely inventing destination facts.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="card">
            <h3>🤖 Groq AI</h3>
            <p>
                Itinerary generation uses your configured
                Groq model through Streamlit Secrets.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
        <div class="card">
            <h3>🔐 Premium Days</h3>
            <p>
                Day 1 is free. Days 2 and 3 become available
                after the premium unlock.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.divider()


# ============================================================
# CONFIG ERROR
# ============================================================

if CONFIG_ERROR:
    st.warning(
        "The TrekTales configuration module could not be "
        "loaded completely."
    )

    with st.expander(
        "Show configuration error"
    ):
        st.code(CONFIG_ERROR)


# ============================================================
# GROQ STATUS
# ============================================================

if not GROQ_API_KEY:

    st.warning(
        "⚠️ GROQ_API_KEY is not configured. "
        "The TrekTales interface is working, but AI generation "
        "will remain disabled until the key is added to "
        "Streamlit Secrets."
    )


# ============================================================
# PAYMENT LOCK
# ============================================================

requested_days = validate_trip_days(days)

if requested_days > 1 and not st.session_state.payment_verified:

    st.markdown(
        f"""
        <div class="status-warning">
            🔒 <strong>Premium itinerary locked</strong><br>
            Day 1 is available for free.
            Days 2–{requested_days} require a
            Rs. {UNLOCK_PRICE} unlock.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "### 🔐 Unlock Premium Itinerary"
    )

    if PAYMENT_QR_PATH.is_file():

        qr_col1, qr_col2 = st.columns(
            [1, 1]
        )

        with qr_col1:
            st.image(
                str(PAYMENT_QR_PATH),
                caption=(
                    f"Pay Rs. {UNLOCK_PRICE} "
                    "to unlock premium days."
                ),
                width=300,
            )

        with qr_col2:
            st.markdown(
                f"""
                <div class="card">
                    <h3>Premium Access</h3>
                    <p>
                        Requested trip:
                        <strong>{requested_days} days</strong>
                    </p>
                    <p>
                        Free access:
                        <strong>Day 1</strong>
                    </p>
                    <p>
                        Unlock price:
                        <strong>Rs. {UNLOCK_PRICE}</strong>
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            payment_file = st.file_uploader(
                "Upload payment screenshot",
                type=[
                    "png",
                    "jpg",
                    "jpeg",
                    "webp",
                ],
                key="payment_screenshot",
            )

            if payment_file is not None:

                st.info(
                    "Payment screenshot uploaded. "
                    "Automatic verification will be connected "
                    "through the TrekTales vision module."
                )

                if st.button(
                    "Verify Payment",
                    key="verify_payment",
                ):
                    st.warning(
                        "Payment verification module is not "
                        "being bypassed. The premium days remain "
                        "locked until verification succeeds."
                    )

    else:
        st.warning(
            "Payment QR image was not found at: "
            f"{PAYMENT_QR_PATH}"
        )


# ============================================================
# GENERATE BUTTON
# ============================================================

st.markdown(
    "### 🧭 Create Your Itinerary"
)

generate = st.button(
    "✨ Generate TrekTales Itinerary",
    type="primary",
)


# ============================================================
# GENERATE ACTION
# ============================================================

if generate:

    if not destination.strip():
        st.error(
            "Please enter a destination."
        )
        st.stop()

    # IMPORTANT:
    # Python determines the number of accessible days.
    accessible_days = get_accessible_days(
        requested_days,
        st.session_state.payment_verified,
    )

    if accessible_days < requested_days:

        st.warning(
            f"Only Day 1 is currently available. "
            f"Days 2–{requested_days} are locked until "
            f"payment verification."
        )

    with st.spinner(
        "Searching the TrekTales knowledge base..."
    ):

        itinerary, error = generate_itinerary(
            destination=destination.strip(),
            days=accessible_days,
            preferences=preferences.strip(),
        )

    if error:

        st.error(error)

    elif itinerary:

        st.session_state.generated_plan = itinerary

        st.session_state.sources = get_sources(
            destination.strip(),
            preferences.strip(),
        )

        st.session_state.last_query = (
            destination.strip()
        )


# ============================================================
# DISPLAY ITINERARY
# ============================================================

if st.session_state.generated_plan:

    st.divider()

    st.markdown(
        "## 🗺️ Your TrekTales Itinerary"
    )

    st.markdown(
        f"""
        <div class="status-good">
            📍 Destination:
            <strong>
                {st.session_state.last_query}
            </strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Remove accidental markdown code fences.
    clean_plan = (
        st.session_state.generated_plan
        .replace("```markdown", "")
        .replace("```", "")
        .strip()
    )

    # Display the grounded result.
    st.markdown(
        clean_plan
    )

    # --------------------------------------------------------
    # SOURCES
    # --------------------------------------------------------

    if st.session_state.sources:

        st.divider()

        st.markdown(
            "### 📚 Knowledge Sources"
        )

        st.caption(
            "Sources are taken directly from the "
            "TrekTales knowledge-base metadata."
        )

        for source in st.session_state.sources:
            st.markdown(
                f"- `{source}`"
            )

    else:

        st.info(
            "No source filenames were available in the "
            "retrieved metadata."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div style="
        text-align:center;
        opacity:0.8;
        padding:1rem;
    ">
        🌿 TrekTales AI · Grounded travel planning
        <br>
        <small>
            Recommendations are generated from the
            configured TrekTales knowledge base.
        </small>
    </div>
    """,
    unsafe_allow_html=True,
)
