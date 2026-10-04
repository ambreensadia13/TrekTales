from pathlib import Path
import re
import json
import inspect

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
DARK_GREEN = "#174936"
BLACK = "#111111"
SOFT_WHITE = "#FFFDF4"
LIGHT_GREY = "#F5F5F5"


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent

FAISS_DIR = ROOT_DIR / "faiss_db"
FAISS_INDEX_PATH = FAISS_DIR / "index.faiss"
FAISS_METADATA_PATH = FAISS_DIR / "metadata.json"
FAISS_CONFIG_PATH = FAISS_DIR / "config.json"

ASSETS_DIR = ROOT_DIR / "assets"
QR_PATH = ASSETS_DIR / "jazzcash_qr.jpg"

KNOWLEDGE_BASE_DIR = ROOT_DIR / "tourism_knowledge_base"


# ============================================================
# SAFE CONFIG VALUES
# ============================================================

DEFAULT_FREE_DAYS = 1
DEFAULT_PAID_DAYS = 3
DEFAULT_UNLOCK_PRICE = 199
DEFAULT_MODEL = "openai/gpt-oss-120b"
DEFAULT_VISION_MODEL = (
    "meta-llama/llama-4-scout-17b-16e-instruct"
)


# ============================================================
# SAFE SECRET READER
# ============================================================

def get_secret(name, default=""):
    try:
        value = st.secrets.get(name, default)

        if value is None:
            return default

        return str(value)

    except Exception:
        return default


# ============================================================
# CONFIGURATION
# ============================================================

GROQ_API_KEY = get_secret(
    "GROQ_API_KEY",
    "",
)

GROQ_MODEL = get_secret(
    "GROQ_MODEL",
    DEFAULT_MODEL,
)

GROQ_BASE_URL = get_secret(
    "GROQ_BASE_URL",
    "https://api.groq.com/openai/v1",
)

GROQ_VISION_MODEL = get_secret(
    "GROQ_VISION_MODEL",
    DEFAULT_VISION_MODEL,
)

EXPECTED_PAYMENT_RECIPIENT = get_secret(
    "EXPECTED_PAYMENT_RECIPIENT",
    "TrekTales",
)


# ============================================================
# TRY TO LOAD PROJECT CONFIG
# ============================================================

FREE_DAYS = DEFAULT_FREE_DAYS
PAID_DAYS = DEFAULT_PAID_DAYS
UNLOCK_PRICE = DEFAULT_UNLOCK_PRICE

try:

    from src.config import (
        FREE_DAYS as CONFIG_FREE_DAYS,
        PAID_DAYS as CONFIG_PAID_DAYS,
        UNLOCK_PRICE as CONFIG_UNLOCK_PRICE,
        EXPECTED_PAYMENT_RECIPIENT as CONFIG_PAYMENT_RECIPIENT,
        GROQ_MODEL as CONFIG_GROQ_MODEL,
    )

    FREE_DAYS = int(CONFIG_FREE_DAYS)
    PAID_DAYS = int(CONFIG_PAID_DAYS)
    UNLOCK_PRICE = int(CONFIG_UNLOCK_PRICE)

    if CONFIG_PAYMENT_RECIPIENT:
        EXPECTED_PAYMENT_RECIPIENT = str(
            CONFIG_PAYMENT_RECIPIENT
        )

    if CONFIG_GROQ_MODEL:
        GROQ_MODEL = str(CONFIG_GROQ_MODEL)

except Exception:
    # The UI can still start even if src/config.py has an issue.
    pass


# ============================================================
# SESSION STATE
# ============================================================

if "payment_verified" not in st.session_state:
    st.session_state.payment_verified = False

if "trip_result" not in st.session_state:
    st.session_state.trip_result = None

if "trip_evidence" not in st.session_state:
    st.session_state.trip_evidence = []

if "payment_result" not in st.session_state:
    st.session_state.payment_result = None

if "vision_result" not in st.session_state:
    st.session_state.vision_result = None

if "last_error" not in st.session_state:
    st.session_state.last_error = None


# ============================================================
# CSS
# ============================================================

st.markdown(
    f"""
<style>

.stApp {{
    background:
        linear-gradient(
            135deg,
            {SOFT_WHITE} 0%,
            {CREAM} 100%
        );
    color: {BLACK};
}}

.main .block-container {{
    max-width: 1250px;
    padding-top: 1.2rem;
    padding-bottom: 2rem;
}}

h1, h2, h3, h4, h5, h6 {{
    color: {BLACK} !important;
}}

p, li, label {{
    color: {BLACK};
}}

/* =========================================================
   BRAND
   ========================================================= */

div[class*="st-key-top_brand"] {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    text-align: center;
    padding: 0.2rem 0 0.5rem 0;
}}

div[class*="st-key-top_brand"] h1 {{
    color: {BROWN} !important;
    font-size: 3.2rem !important;
    font-weight: 900 !important;
    letter-spacing: -1px;
    margin: 0 !important;
}}

div[class*="st-key-top_brand"] p {{
    color: {GREEN} !important;
    font-size: 1rem;
    font-weight: 600;
    margin-top: 0 !important;
}}

/* =========================================================
   SIDEBAR
   ========================================================= */

section[data-testid="stSidebar"] {{
    background:
        linear-gradient(
            180deg,
            {DARK_GREEN} 0%,
            {GREEN} 100%
        );
}}

section[data-testid="stSidebar"] * {{
    color: {WHITE} !important;
}}

div[class*="st-key-sidebar_access"] {{
    background: rgba(255,255,255,0.10) !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
    border-radius: 16px !important;
    padding: 1rem !important;
}}

div[class*="st-key-agent_"] {{
    background: rgba(255,255,255,0.09) !important;
    border: 1px solid rgba(255,255,255,0.18) !important;
    border-left: 4px solid {LIGHT_GREEN} !important;
    border-radius: 12px !important;
    padding: 0.7rem !important;
    margin-bottom: 0.55rem !important;
}}

/* =========================================================
   HERO
   ========================================================= */

div[class*="st-key-hero"] {{
    background:
        linear-gradient(
            135deg,
            {DARK_GREEN} 0%,
            {GREEN} 60%,
            #2F7D60 100%
        ) !important;
    border: none !important;
    border-radius: 26px !important;
    padding: 2rem !important;
    box-shadow: 0 15px 35px rgba(34,111,84,0.20);
}}

div[class*="st-key-hero"] * {{
    color: {WHITE} !important;
}}

/* =========================================================
   FEATURE CARDS
   ========================================================= */

div[class*="st-key-feature_"] {{
    background: {WHITE} !important;
    border: 1px solid rgba(34,111,84,0.18) !important;
    border-radius: 18px !important;
    padding: 1.1rem !important;
    min-height: 175px;
    box-shadow: 0 7px 20px rgba(67,41,31,0.08);
}}

div[class*="st-key-feature_"] * {{
    color: {BLACK} !important;
}}

/* =========================================================
   CONTENT CARD
   ========================================================= */

div[class*="st-key-light_card"] {{
    background: {WHITE} !important;
    border: 1px solid rgba(34,111,84,0.18) !important;
    border-radius: 18px !important;
    padding: 1.2rem !important;
    box-shadow: 0 7px 20px rgba(67,41,31,0.07);
}}

div[class*="st-key-light_card"] * {{
    color: {BLACK} !important;
}}

/* =========================================================
   ANSWER CARD
   ========================================================= */

div[class*="st-key-answer_card"] {{
    background: {WHITE} !important;
    border: 2px solid {LIGHT_GREEN} !important;
    border-radius: 20px !important;
    padding: 1.4rem !important;
    box-shadow: 0 8px 25px rgba(34,111,84,0.10);
}}

div[class*="st-key-answer_card"] * {{
    color: {BLACK} !important;
}}

/* =========================================================
   LOCKED CARD
   ========================================================= */

div[class*="st-key-locked_card"] {{
    background:
        linear-gradient(
            135deg,
            {DARK_GREEN},
            {GREEN}
        ) !important;
    border: none !important;
    border-radius: 20px !important;
    padding: 1.4rem !important;
}}

div[class*="st-key-locked_card"] * {{
    color: {WHITE} !important;
}}

/* =========================================================
   PAYMENT CARD
   ========================================================= */

div[class*="st-key-payment_card"] {{
    background: {WHITE} !important;
    border: 2px solid {RED} !important;
    border-radius: 20px !important;
    padding: 1.4rem !important;
    box-shadow: 0 8px 25px rgba(218,44,56,0.12);
}}

div[class*="st-key-payment_card"] * {{
    color: {BLACK} !important;
}}

/* =========================================================
   DISCLAIMER
   ========================================================= */

div[class*="st-key-disclaimer_card"] {{
    background: {WHITE} !important;
    border: 1px solid {LIGHT_GREEN} !important;
    border-left: 5px solid {GREEN} !important;
    border-radius: 14px !important;
    padding: 1rem !important;
}}

div[class*="st-key-disclaimer_card"] * {{
    color: {BLACK} !important;
}}

/* =========================================================
   STATUS
   ========================================================= */

div[class*="st-key-status_"] {{
    background: {WHITE} !important;
    border: 1px solid rgba(34,111,84,0.20) !important;
    border-radius: 14px !important;
    padding: 0.8rem !important;
}}

div[class*="st-key-status_"] * {{
    color: {BLACK} !important;
}}

/* =========================================================
   SOURCES
   ========================================================= */

div[class*="st-key-source_"] {{
    background: {LIGHT_GREY} !important;
    border: 1px solid #DDDDDD !important;
    border-radius: 12px !important;
    padding: 0.8rem !important;
}}

div[class*="st-key-source_"] * {{
    color: {BLACK} !important;
}}

/* =========================================================
   BUTTONS
   ========================================================= */

.stButton > button {{
    background: {RED} !important;
    color: {WHITE} !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    min-height: 2.7rem;
}}

.stButton > button:hover {{
    background: {GREEN} !important;
    color: {WHITE} !important;
}}

.stButton > button p {{
    color: {WHITE} !important;
}}

/* =========================================================
   INPUTS
   ========================================================= */

input,
textarea {{
    color: {BLACK} !important;
    background: {WHITE} !important;
}}

div[data-baseweb="select"] > div {{
    background: {WHITE} !important;
    color: {BLACK} !important;
}}

div[data-baseweb="select"] * {{
    color: {BLACK} !important;
}}

 /* =========================================================
    LANGUAGE SELECTOR - FORCE SELECTED TEXT BLACK
    ========================================================= */

div[data-baseweb="select"] {{
    background: #FFFFFF !important;
    color: #111111 !important;
}}

div[data-baseweb="select"] > div {{
    background: #FFFFFF !important;
    color: #111111 !important;
}}

/* Selected language text */
div[data-baseweb="select"] [role="button"] {{
    color: #111111 !important;
    background: #FFFFFF !important;
}}

div[data-baseweb="select"] [role="button"] * {{
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
}}

/* BaseWeb selected value */
div[data-baseweb="select"] [class*="singleValue"] {{
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
}}

/* All text inside selector */
div[data-baseweb="select"] span {{
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
}}

div[data-baseweb="select"] input {{
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
}}

/* Dropdown options */
div[data-baseweb="popover"] {{
    background: #FFFFFF !important;
}}

div[data-baseweb="popover"] * {{
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
}}

/* Dropdown arrow */
div[data-baseweb="select"] svg {{
    color: #111111 !important;
    fill: #111111 !important;
}}

/* =========================================================
   RESPONSE LANGUAGE - FORCE BLACK TEXT
   ========================================================= */

section[data-testid="stSidebar"] div[data-baseweb="select"],
section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
section[data-testid="stSidebar"] div[data-baseweb="select"] span,
section[data-testid="stSidebar"] div[data-baseweb="select"] input {{
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
}}

section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
    background: #FFFFFF !important;
}}

section[data-testid="stSidebar"] div[data-baseweb="select"] * {{
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
}}

=========================================================
   FILE UPLOADER - LIGHT GREEN TEXT
   ========================================================= */

section[data-testid="stFileUploaderDropzone"] {{
    background: {WHITE} !important;
    border: 1px dashed {GREEN} !important;
    border-radius: 14px !important;
}}

section[data-testid="stFileUploaderDropzone"] * {{
    color: {LIGHT_GREEN} !important;
}}

div[data-testid="stFileUploader"] label {{
    color: {LIGHT_GREEN} !important;
}}

div[data-testid="stFileUploader"] label * {{
    color: {LIGHT_GREEN} !important;
}}

div[data-testid="stFileUploaderDropzoneInstructions"] {{
    color: {LIGHT_GREEN} !important;
}}

div[data-testid="stFileUploaderDropzoneInstructions"] * {{
    color: {LIGHT_GREEN} !important;
}}

/* =========================================================
   PREPARING TREKTALES STATUS - WHITE TEXT
   ========================================================= */

div[data-testid="stStatusWidget"] {{
    color: {WHITE} !important;
}}

div[data-testid="stStatusWidget"] * {{
    color: {WHITE} !important;
}}

div[data-testid="stStatusWidget"] svg {{
    color: {WHITE} !important;
}}

/* =========================================================
   METRICS
   ========================================================= */

div[data-testid="stMetric"] {{
    background: {WHITE};
    border: 1px solid rgba(34,111,84,0.18);
    border-radius: 14px;
    padding: 0.8rem;
}}

div[data-testid="stMetric"] * {{
    color: {BLACK} !important;
}}

/* =========================================================
   MOBILE
   ========================================================= */

@media (max-width: 768px) {{

    .main .block-container {{
        padding-left: 0.8rem;
        padding-right: 0.8rem;
        padding-top: 0.8rem;
    }}

    div[class*="st-key-top_brand"] h1 {{
        font-size: 2.4rem !important;
    }}

    div[class*="st-key-hero"] {{
        padding: 1.2rem !important;
        border-radius: 20px !important;
    }}

    div[class*="st-key-feature_"] {{
        min-height: auto;
        padding: 1rem !important;
    }}

}}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

def clean_text(text):
    """Remove accidental HTML from model output."""

    if text is None:
        return ""

    text = str(text)

    text = re.sub(
        r"<script.*?</script>",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(
        r"<style.*?</style>",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(
        r"<[^>]+>",
        "",
        text,
    )

    text = text.replace(
        "```html",
        "",
    )

    text = text.replace(
        "```HTML",
        "",
    )

    text = text.replace(
        "```",
        "",
    )

    return text.strip()


def safe_import_retriever():
    """Load retriever only when required."""

    from src.retriever import HybridRetriever

    return HybridRetriever


def safe_import_crew():
    """Load Crew only when required."""

    from src.crew import TrekTalesCrew

    return TrekTalesCrew


def safe_import_payment():
    """Load payment verifier only when required."""

    from src.payment import verify_payment

    return verify_payment


def safe_import_vision():
    """Load vision function only when required."""

    from src.vision import analyze_payment_screenshot

    return analyze_payment_screenshot


def extract_text_from_result(result):
    """Safely extract output from different CrewAI result formats."""

    if result is None:
        return ""

    if isinstance(result, str):
        return result

    if isinstance(result, dict):

        for key in (
            "answer",
            "result",
            "output",
            "raw",
            "plan",
            "response",
            "content",
        ):

            if key in result and result[key]:
                return str(result[key])

        return json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )

    # CrewAI CrewOutput commonly exposes .raw.
    for attribute in (
        "raw",
        "output",
        "result",
        "content",
    ):

        try:

            value = getattr(
                result,
                attribute,
                None,
            )

            if value:
                return str(value)

        except Exception:
            pass

    return str(result)


def extract_sources(evidence):
    """Extract source filenames without inventing citations."""

    sources = []

    if not evidence:
        return sources

    for item in evidence:

        if not isinstance(item, dict):
            continue

        metadata = item.get(
            "metadata",
            {},
        )

        if not isinstance(metadata, dict):
            metadata = {}

        source = (
            metadata.get("source")
            or item.get("source")
            or ""
        )

        page = (
            metadata.get("page")
            or item.get("page")
            or ""
        )

        if not source:
            continue

        source = str(source).replace(
            "\\",
            "/",
        )

        # Only show filename.
        source = source.split("/")[-1]

        # Remove accidental HTML artifacts.
        source = source.replace(
            ".html",
            "",
        )

        sources.append(
            {
                "source": source,
                "page": str(page),
            }
        )

    # Remove duplicates.
    unique = []
    seen = set()

    for source in sources:

        key = (
            source["source"],
            source["page"],
        )

        if key not in seen:

            seen.add(key)
            unique.append(source)

    return unique


def retrieve_with_retriever(retriever, query):
    """Support common retriever APIs."""

    # search(query, top_k=...)
    if hasattr(retriever, "search"):

        try:
            return retriever.search(
                query,
                top_k=6,
            )

        except TypeError:

            return retriever.search(query)

    # retrieve(query, top_k=...)
    if hasattr(retriever, "retrieve"):

        try:
            return retriever.retrieve(
                query,
                top_k=6,
            )

        except TypeError:

            return retriever.retrieve(query)

    raise AttributeError(
        "HybridRetriever does not provide "
        "search() or retrieve()."
    )


def run_crew(
    crew,
    destination,
    duration,
    budget,
    travelers,
    travel_style,
    language,
    interests,
    starting_location,
    evidence,
):
    """
    Try common TrekTalesCrew interfaces without
    hardcoding one incompatible signature.
    """

    request = {
        "destination": destination,
        "duration": duration,
        "days": duration,
        "budget": budget,
        "travelers": travelers,
        "travel_style": travel_style,
        "language": language,
        "interests": interests,
        "starting_location": starting_location,
        "evidence": evidence,
    }

    # --------------------------------------------------------
    # Preferred: run(request)
    # --------------------------------------------------------

    if hasattr(crew, "run"):

        try:
            return crew.run(request)

        except TypeError:
            pass

    # --------------------------------------------------------
    # kickoff(request)
    # --------------------------------------------------------

    if hasattr(crew, "kickoff"):

        try:
            return crew.kickoff(request)

        except TypeError:
            pass

    # --------------------------------------------------------
    # plan(...)
    # --------------------------------------------------------

    if hasattr(crew, "plan"):

        try:

            return crew.plan(
                destination=destination,
                duration=duration,
                budget=budget,
                travelers=travelers,
                travel_style=travel_style,
                language=language,
                interests=interests,
                starting_location=starting_location,
                evidence=evidence,
            )

        except TypeError:
            pass

    # --------------------------------------------------------
    # generate(...)
    # --------------------------------------------------------

    if hasattr(crew, "generate"):

        try:

            return crew.generate(
                destination=destination,
                duration=duration,
                budget=budget,
                travelers=travelers,
                travel_style=travel_style,
                language=language,
                interests=interests,
                starting_location=starting_location,
                evidence=evidence,
            )

        except TypeError:
            pass

    raise RuntimeError(
        "TrekTalesCrew could not be started. "
        "Your src/crew.py must expose run(), kickoff(), "
        "plan(), or generate()."
    )


def verify_payment_safely(
    payment_data,
):
    """Call the project's deterministic payment verifier."""

    verify_payment = safe_import_payment()

    # First try dictionary interface.
    try:

        return verify_payment(
            payment_data,
        )

    except TypeError:
        pass

    # Then keyword interface.
    return verify_payment(
        recipient=payment_data.get(
            "recipient",
            "",
        ),
        amount=payment_data.get(
            "amount",
            0,
        ),
        status=payment_data.get(
            "status",
            "",
        ),
    )


def is_payment_verified(result):
    """Normalize verifier output."""

    if isinstance(result, bool):
        return result

    if isinstance(result, dict):

        return bool(
            result.get(
                "verified",
                result.get(
                    "success",
                    False,
                ),
            )
        )

    return False


def validate_requested_days(days):
    try:
        days = int(days)
    except Exception:
        days = 1

    return max(
        1,
        min(
            days,
            PAID_DAYS,
        ),
    )


# ============================================================
# BRAND
# ============================================================

with st.container(key="top_brand"):

    st.markdown("# TrekTales")

    st.markdown(
        "AI Multi-Agent Travel Planner"
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🌿 TrekTales")

    st.markdown(
        "Plan smarter trips with AI-powered travel agents."
    )

    st.divider()

    with st.container(
        border=True,
        key="sidebar_access",
    ):

        st.markdown("### 🔐 Access Model")

        st.markdown(
            f"**Day {FREE_DAYS}:** Free"
        )

        st.markdown(
            f"**Days {FREE_DAYS + 1}–{PAID_DAYS}:** "
            f"Rs. {UNLOCK_PRICE}"
        )

        if st.session_state.payment_verified:

            st.success(
                "Premium unlocked"
            )

        else:

            st.info(
                "Premium locked"
            )

    st.divider()

    language = st.selectbox(
        "🌐 Response Language",
        [
            "English",
            "Urdu",
            "Roman Urdu",
        ],
    )

    st.markdown("### 🤖 AI Agents")

    agents = [
        (
            1,
            "Master Orchestrator",
            "Coordinates the travel workflow.",
        ),
        (
            2,
            "Knowledge Agent",
            "Retrieves information from FAISS.",
        ),
        (
            3,
            "Planner Agent",
            "Creates the itinerary.",
        ),
        (
            4,
            "Budget Agent",
            "Handles budget-aware planning.",
        ),
        (
            5,
            "Safety Agent",
            "Provides safety guidance.",
        ),
        (
            6,
            "Summarizer Agent",
            "Creates the final summary.",
        ),
        (
            7,
            "Payment Agent",
            "Handles payment verification.",
        ),
        (
            8,
            "Vision Agent",
            "Analyzes payment screenshots.",
        ),
    ]

    for number, name, description in agents:

        with st.container(
            border=True,
            key=f"agent_{number}",
        ):

            st.markdown(
                f"**AGENT {number:02d}**"
            )

            st.markdown(
                f"**{name}**"
            )

            st.caption(
                description
            )

    st.divider()

    st.caption(
        f"Groq model: {GROQ_MODEL}"
    )


# ============================================================
# HERO
# ============================================================

with st.container(
    border=True,
    key="hero",
):

    st.markdown(
        "## 🌍 Plan Your Next Adventure"
    )

    st.markdown(
        "Create personalized travel plans using a "
        "multi-agent AI system grounded in your tourism "
        "knowledge base."
    )

    st.markdown(
        "📚 Knowledge Grounding  •  "
        "🗺️ Smart Planning  •  "
        "💰 Budget Awareness  •  "
        "🛡️ Safety  •  "
        "👁️ Vision Verification"
    )


# ============================================================
# FEATURES
# ============================================================

st.markdown("## ✨ TrekTales Features")

feature_columns = st.columns(3)

with feature_columns[0]:

    with st.container(
        border=True,
        key="feature_knowledge",
    ):

        st.markdown(
            "### 🧠 Knowledge Grounding"
        )

        st.write(
            "Uses your tourism knowledge base and "
            "FAISS retrieval to ground recommendations."
        )

with feature_columns[1]:

    with st.container(
        border=True,
        key="feature_agents",
    ):

        st.markdown(
            "### 🤖 8 AI Agents"
        )

        st.write(
            "Specialized agents support research, "
            "planning, budgeting, safety and verification."
        )

with feature_columns[2]:

    with st.container(
        border=True,
        key="feature_payment",
    ):

        st.markdown(
            "### 💳 Premium Unlock"
        )

        st.write(
            f"Day 1 is free. Additional days "
            f"require the Rs. {UNLOCK_PRICE} unlock."
        )


st.divider()


# ============================================================
# TRIP INPUT
# ============================================================

st.markdown("## 🧭 Create Your Trip")

input_col1, input_col2 = st.columns(2)

with input_col1:

    destination = st.text_input(
        "📍 Destination",
        placeholder="e.g. Rawalpindi",
    )

    starting_location = st.text_input(
        "🚗 Starting Location",
        placeholder="e.g. Islamabad",
    )

    requested_duration = st.slider(
        "📅 Trip Duration",
        min_value=1,
        max_value=PAID_DAYS,
        value=1,
        step=1,
    )

    travelers = st.number_input(
        "👥 Number of Travelers",
        min_value=1,
        max_value=20,
        value=2,
        step=1,
    )


with input_col2:

    budget = st.selectbox(
        "💰 Budget Level",
        [
            "Budget",
            "Moderate",
            "Comfortable",
            "Premium",
        ],
    )

    travel_style = st.selectbox(
        "🎒 Travel Style",
        [
            "Adventure",
            "Relaxed",
            "Family",
            "Romantic",
            "Cultural",
            "Nature",
            "Photography",
            "Mixed",
        ],
    )

    interests = st.multiselect(
        "⭐ Interests",
        [
            "Mountains",
            "Nature",
            "Food",
            "Culture",
            "History",
            "Photography",
            "Adventure",
            "Shopping",
            "Family Activities",
            "Nightlife",
        ],
        default=[
            "Nature",
            "Photography",
        ],
    )


# ============================================================
# ACCESS CALCULATION
# ============================================================

requested_duration = validate_requested_days(
    requested_duration
)

if st.session_state.payment_verified:

    accessible_duration = requested_duration

else:

    accessible_duration = min(
        requested_duration,
        FREE_DAYS,
    )


# ============================================================
# PREMIUM NOTICE
# ============================================================

if (
    requested_duration > FREE_DAYS
    and not st.session_state.payment_verified
):

    st.warning(
        f"You selected {requested_duration} days. "
        f"Only Day 1 is currently available. "
        f"Unlock premium for Rs. {UNLOCK_PRICE} "
        f"to generate all requested days."
    )


st.divider()


# ============================================================
# SYSTEM STATUS
# ============================================================

st.markdown("## ⚙️ System Status")

status_col1, status_col2, status_col3 = st.columns(3)

with status_col1:

    with st.container(
        border=True,
        key="status_groq",
    ):

        st.markdown("### 🧠 AI Model")

        if GROQ_API_KEY:

            st.success(
                "Groq API key detected"
            )

        else:

            st.error(
                "Groq API key not found"
            )


with status_col2:

    with st.container(
        border=True,
        key="status_faiss",
    ):

        st.markdown("### 📚 Knowledge Base")

        index_exists = FAISS_INDEX_PATH.exists()
        metadata_exists = FAISS_METADATA_PATH.exists()
        config_exists = FAISS_CONFIG_PATH.exists()

        if index_exists and metadata_exists:

            st.success(
                "FAISS index ready"
            )

        else:

            st.error(
                "FAISS index not found"
            )

        st.caption(
            f"index.faiss: {'✓' if index_exists else '✗'}"
        )

        st.caption(
            f"metadata.json: {'✓' if metadata_exists else '✗'}"
        )

        st.caption(
            f"config.json: {'✓' if config_exists else '✗'}"
        )


with status_col3:

    with st.container(
        border=True,
        key="status_agents",
    ):

        st.markdown("### 🤖 Agent System")

        st.success(
            "8-agent architecture configured"
        )

        st.caption(
            f"Active planning days: {accessible_duration}"
        )


st.divider()


# ============================================================
# GENERATE BUTTON
# ============================================================

generate_trip = st.button(
    "🚀 Generate My TrekTales Plan",
    use_container_width=True,
)


if generate_trip:

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not destination.strip():

        st.error(
            "Please enter a destination."
        )

        st.stop()

    if not starting_location.strip():

        st.error(
            "Please enter your starting location."
        )

        st.stop()

    if not GROQ_API_KEY:

        st.error(
            "GROQ_API_KEY is missing from Streamlit Secrets."
        )

        st.stop()

    if not FAISS_INDEX_PATH.exists():

        st.error(
            "FAISS index not found at "
            "`faiss_db/index.faiss`."
        )

        st.stop()

    if not FAISS_METADATA_PATH.exists():

        st.error(
            "FAISS metadata not found at "
            "`faiss_db/metadata.json`."
        )

        st.stop()

    # --------------------------------------------------------
    # CLEAR PREVIOUS RESULT
    # --------------------------------------------------------

    st.session_state.trip_result = None
    st.session_state.trip_evidence = []
    st.session_state.last_error = None

# --------------------------------------------------------
# RETRIEVAL
# --------------------------------------------------------

with st.status(
    "🔎 Preparing your TrekTales trip...",
    expanded=True,
) as status:

    st.write(
        "Loading the tourism knowledge base..."
    )

    try:

        RetrieverClass = safe_import_retriever()

        retriever = RetrieverClass(
            index_path=FAISS_INDEX_PATH,
            metadata_path=FAISS_METADATA_PATH,
            config_path=FAISS_CONFIG_PATH,
        )

        query = (
            f"Destination: {destination}. "
            f"Starting location: {starting_location}. "
            f"Trip duration: {accessible_duration} days. "
            f"Budget: {budget}. "
            f"Travel style: {travel_style}. "
            f"Travelers: {travelers}. "
            f"Interests: {', '.join(interests)}."
        )

        evidence = retrieve_with_retriever(
            retriever,
            query,
        )

        if evidence is None:
            evidence = []

        st.session_state.trip_evidence = evidence

        st.write(
            f"Retrieved {len(evidence)} knowledge items."
        )

    except Exception as exc:

        status.update(
            label="❌ Knowledge retrieval failed",
            state="error",
            expanded=True,
        )

        st.error(
            "The FAISS retriever could not be loaded."
        )

        st.exception(exc)

        st.stop()
        
        # ----------------------------------------------------
        # PREMIUM DAY ENFORCEMENT
        # ----------------------------------------------------

        if (
            requested_duration > FREE_DAYS
            and not st.session_state.payment_verified
        ):

            st.info(
                f"Premium is locked. "
                f"The AI will generate Day 1 only."
            )

        # ----------------------------------------------------
        # CREW
        # ----------------------------------------------------

        st.write(
            "🤖 Activating TrekTales AI agents..."
        )

        try:

            CrewClass = safe_import_crew()

            crew = CrewClass()

            result = run_crew(
                crew=crew,
                destination=destination,
                duration=accessible_duration,
                budget=budget,
                travelers=travelers,
                travel_style=travel_style,
                language=language,
                interests=interests,
                starting_location=starting_location,
                evidence=evidence,
            )

            st.session_state.trip_result = result

            status.update(
                label="✅ TrekTales plan generated!",
                state="complete",
                expanded=False,
            )

        except Exception as exc:

            status.update(
                label="❌ Trip generation failed",
                state="error",
                expanded=True,
            )

            st.error(
                "The TrekTales AI crew could not generate "
                "the itinerary."
            )

            st.exception(exc)

            st.stop()


# ============================================================
# DISPLAY RESULT
# ============================================================

if st.session_state.trip_result:

    st.divider()

    st.markdown(
        "## 🗺️ Your TrekTales Plan"
    )

    if st.session_state.payment_verified:

        st.success(
            f"Premium itinerary: {accessible_duration} day(s)"
        )

    elif requested_duration > FREE_DAYS:

        st.info(
            "Free preview: Day 1"
        )

    answer = extract_text_from_result(
        st.session_state.trip_result
    )

    answer = clean_text(answer)

    with st.container(
        border=True,
        key="answer_card",
    ):

        st.markdown(
            "### 🌿 Personalized Itinerary"
        )

        # Important:
        # Do not use unsafe_allow_html=True here.
        # This prevents AI output from breaking the page.
        st.markdown(
            answer,
            unsafe_allow_html=False,
        )


# ============================================================
# SOURCES
# ============================================================

sources = extract_sources(
    st.session_state.trip_evidence
)

if sources:

    st.divider()

    st.markdown(
        "## 📚 Knowledge Sources"
    )

    for index, source in enumerate(sources):

        with st.container(
            border=True,
            key=f"source_{index}",
        ):

            st.markdown(
                f"**📄 {source['source']}**"
            )

            if (
                source["page"]
                and source["page"].lower() != "n/a"
            ):

                st.caption(
                    f"Page: {source['page']}"
                )


# ============================================================
# PREMIUM SECTION
# ============================================================

if requested_duration >= 2:

    st.divider()

    st.markdown(
        "## 🔐 Unlock Additional Days"
    )

    with st.container(
        border=True,
        key="locked_card",
    ):

        if st.session_state.payment_verified:

            st.markdown(
                "### 🔓 Premium Unlocked"
            )

            st.markdown(
                f"You can now generate all "
                f"{requested_duration} requested days."
            )

        else:

            st.markdown(
                "### 🔒 Days 2–3 Are Locked"
            )

            st.markdown(
                f"Day 1 is free. "
                f"Unlock the premium itinerary for "
                f"**Rs. {UNLOCK_PRICE}**."
            )

    # --------------------------------------------------------
    # PAYMENT
    # --------------------------------------------------------

    if not st.session_state.payment_verified:

        with st.container(
            border=True,
            key="payment_card",
        ):

            st.markdown(
                "### 💳 Payment Verification"
            )

            st.write(
                f"Payment amount: **Rs. {UNLOCK_PRICE}**"
            )

            st.write(
                f"Recipient: **{EXPECTED_PAYMENT_RECIPIENT}**"
            )

            if QR_PATH.exists():

                st.image(
                    str(QR_PATH),
                    caption="TrekTales Payment QR",
                    width=260,
                )

            else:

                st.warning(
                    "Payment QR not found at "
                    "`assets/jazzcash_qr.jpg`."
                )

            uploaded_screenshot = st.file_uploader(
                "📸 Upload payment screenshot",
                type=[
                    "png",
                    "jpg",
                    "jpeg",
                    "webp",
                ],
                key="payment_screenshot",
            )

            if uploaded_screenshot:

                verify_button = st.button(
                    "🔍 Verify Payment Screenshot",
                    use_container_width=True,
                )

                if verify_button:

                    with st.spinner(
                        "👁️ Vision Agent is analyzing the screenshot..."
                    ):

                        try:

                            analyze_payment_screenshot = (
                                safe_import_vision()
                            )

                            # Try the most common interface first.
                            try:

                                vision_result = (
                                    analyze_payment_screenshot(
                                        uploaded_screenshot
                                    )
                                )

                            except TypeError:

                                # Try raw bytes interface.
                                uploaded_screenshot.seek(0)

                                vision_result = (
                                    analyze_payment_screenshot(
                                        uploaded_screenshot.read()
                                    )
                                )

                            st.session_state.vision_result = (
                                vision_result
                            )

                        except Exception as exc:

                            st.error(
                                "Vision Agent could not analyze "
                                "the payment screenshot."
                            )

                            st.exception(exc)

                            st.stop()

                    # ------------------------------------------------
                    # VISION RESULT
                    # ------------------------------------------------

                    vision = (
                        st.session_state.vision_result
                    )

                    if isinstance(
                        vision,
                        dict,
                    ):

                        recipient = str(
                            vision.get(
                                "recipient",
                                "",
                            )
                        ).strip()

                        amount = vision.get(
                            "amount",
                            0,
                        )

                        payment_status = str(
                            vision.get(
                                "status",
                                "",
                            )
                        ).strip()

                        confidence = vision.get(
                            "confidence",
                            "",
                        )

                    else:

                        st.error(
                            "Vision Agent returned an "
                            "unexpected response format."
                        )

                        st.stop()

                    st.markdown(
                        "### 👁️ Screenshot Analysis"
                    )

                    metric1, metric2, metric3 = st.columns(3)

                    with metric1:

                        st.metric(
                            "Recipient",
                            recipient
                            if recipient
                            else "Not detected",
                        )

                    with metric2:

                        st.metric(
                            "Amount",
                            f"Rs. {amount}",
                        )

                    with metric3:

                        st.metric(
                            "Status",
                            payment_status
                            if payment_status
                            else "Not detected",
                        )

                    if confidence:

                        st.caption(
                            f"Vision confidence: {confidence}"
                        )

                    # ------------------------------------------------
                    # DETERMINISTIC PAYMENT CHECK
                    # ------------------------------------------------

                    payment_data = {
                        "recipient": recipient,
                        "amount": amount,
                        "status": payment_status,
                    }

                    try:

                        payment_result = (
                            verify_payment_safely(
                                payment_data
                            )
                        )

                    except Exception as exc:

                        st.error(
                            "The deterministic payment verifier "
                            "could not validate the result."
                        )

                        st.exception(exc)

                        st.stop()

                    st.session_state.payment_result = (
                        payment_result
                    )

                    verified = is_payment_verified(
                        payment_result
                    )

                    st.session_state.payment_verified = (
                        verified
                    )

                    if verified:

                        st.success(
                            "✅ Payment verified successfully."
                        )

                        st.info(
                            "Generate your itinerary again to "
                            "create all requested days."
                        )

                    else:

                        st.error(
                            "❌ Payment could not be verified."
                        )

                        st.warning(
                            "The recipient, amount and payment "
                            "status did not satisfy the application's "
                            "verification rules."
                        )

    else:

        st.success(
            "🔓 Premium access is active for this session."
        )

        if st.button(
            "🔒 Reset Premium Session",
            use_container_width=True,
        ):

            st.session_state.payment_verified = False
            st.session_state.payment_result = None
            st.session_state.vision_result = None

            st.rerun()


# ============================================================
# DISCLAIMER
# ============================================================

st.divider()

with st.container(
    border=True,
    key="disclaimer_card",
):

    st.markdown(
        "**Important:** TrekTales provides tourism planning "
        "information for general informational purposes. "
        "Travel conditions, prices, availability, weather, "
        "transport schedules and local rules can change. "
        "Verify important details with current or official "
        "sources before travelling."
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:

    st.markdown(
        "🌿 **TrekTales**"
    )

with footer_col2:

    st.markdown(
        "AI Multi-Agent Travel Planner"
    )

with footer_col3:

    st.markdown(
        "Built with Streamlit + Groq"
    )
