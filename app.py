from pathlib import Path
import re
import json

import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="TrekTales | Rawalpindi Adventure Planner",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# TREKTALES THEME
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

SRC_DIR = ROOT_DIR / "src"

FAISS_DIR = ROOT_DIR / "faiss_db"

FAISS_INDEX_PATH = FAISS_DIR / "index.faiss"
FAISS_METADATA_PATH = FAISS_DIR / "metadata.json"
FAISS_CONFIG_PATH = FAISS_DIR / "config.json"

ASSETS_DIR = ROOT_DIR / "assets"
QR_PATH = ASSETS_DIR / "jazzcash_qr.jpg"

KNOWLEDGE_BASE_DIR = ROOT_DIR / "tourism_knowledge_base"


# ============================================================
# DEFAULT CONFIG
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

        return str(value).strip()

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
# OPTIONAL PROJECT CONFIG
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
    pass


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_SESSION_STATE = {
    "payment_verified": False,
    "trip_result": None,
    "trip_evidence": [],
    "payment_result": None,
    "vision_result": None,
    "last_error": None,
}

for key, value in DEFAULT_SESSION_STATE.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    f"""
    <style>

    /* ========================================================
       GLOBAL
       ======================================================== */

    .stApp {{
        background:
            linear-gradient(
                135deg,
                #F4F0BB 0%,
                #FFFDF4 45%,
                #E8F5E9 100%
            );
        color: {BLACK};
    }}

    .block-container {{
        max-width: 1250px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }}

    /* ========================================================
       HEADINGS
       ======================================================== */

    h1, h2, h3, h4 {{
        color: {DARK_GREEN} !important;
    }}

    p, li, label {{
        color: {BLACK};
    }}

    /* ========================================================
       BRAND
       ======================================================== */

    .brand {{
        text-align: center;
        padding: 1rem 0 1.5rem 0;
    }}

    .brand-title {{
        font-size: 3.4rem;
        font-weight: 900;
        color: {DARK_GREEN};
        letter-spacing: -1px;
        margin-bottom: 0;
    }}

    .brand-subtitle {{
        font-size: 1.1rem;
        font-weight: 700;
        color: {GREEN};
        margin-top: 0.2rem;
    }}

    .brand-tagline {{
        color: {BROWN};
        font-size: 0.95rem;
        margin-top: 0.5rem;
    }}

    /* ========================================================
       HERO
       ======================================================== */

    .hero {{
        background:
            linear-gradient(
                135deg,
                rgba(34,111,84,0.97),
                rgba(23,73,54,0.97)
            );
        border-radius: 24px;
        padding: 2.4rem;
        color: white;
        box-shadow: 0 12px 35px rgba(23,73,54,0.18);
        margin-bottom: 1.8rem;
    }}

    .hero h1,
    .hero h2,
    .hero h3,
    .hero p {{
        color: white !important;
    }}

    .hero-title {{
        font-size: 2.3rem;
        font-weight: 900;
        margin-bottom: 0.6rem;
    }}

    .hero-text {{
        font-size: 1.05rem;
        line-height: 1.7;
        max-width: 850px;
    }}

    .hero-pills {{
        margin-top: 1.2rem;
        font-size: 0.95rem;
        font-weight: 700;
    }}

    /* ========================================================
       DESTINATION
       ======================================================== */

    .destination-card {{
        background: {SOFT_WHITE};
        border: 2px solid {GREEN};
        border-radius: 18px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1rem;
    }}

    .destination-label {{
        color: {GREEN};
        font-size: 0.8rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}

    .destination-name {{
        color: {DARK_GREEN};
        font-size: 2rem;
        font-weight: 900;
        margin-top: 0.2rem;
    }}

    /* ========================================================
       FEATURE CARDS
       ======================================================== */

    .feature-card {{
        background: rgba(255,255,255,0.75);
        border: 1px solid rgba(34,111,84,0.25);
        border-radius: 18px;
        padding: 1.3rem;
        min-height: 170px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.04);
    }}

    .feature-title {{
        color: {DARK_GREEN};
        font-weight: 900;
        font-size: 1.15rem;
    }}

    .feature-text {{
        color: {BROWN};
        line-height: 1.6;
    }}

    /* ========================================================
       ITINERARY CARD
       ======================================================== */

    .itinerary-header {{
        background:
            linear-gradient(
                135deg,
                {GREEN},
                {DARK_GREEN}
            );
        color: white;
        border-radius: 18px 18px 0 0;
        padding: 1rem 1.4rem;
        font-size: 1.25rem;
        font-weight: 900;
    }}

    .itinerary-body {{
        background: white;
        border-radius: 0 0 18px 18px;
        padding: 1.6rem;
        border: 1px solid #E4E4E4;
    }}

    .itinerary-body h1,
    .itinerary-body h2,
    .itinerary-body h3 {{
        color: {DARK_GREEN} !important;
    }}

    .itinerary-body strong {{
        color: {DARK_GREEN};
    }}

    /* ========================================================
       STATUS
       ======================================================== */

    .status-card {{
        background: rgba(255,255,255,0.8);
        border-radius: 16px;
        border: 1px solid rgba(34,111,84,0.18);
        padding: 1rem;
    }}

    /* ========================================================
       PREMIUM
       ======================================================== */

    .premium-card {{
        background:
            linear-gradient(
                135deg,
                #FFF8DC,
                #FFFDF4
            );
        border: 2px solid {RED};
        border-radius: 20px;
        padding: 1.5rem;
    }}

    .premium-title {{
        color: {RED};
        font-size: 1.5rem;
        font-weight: 900;
    }}

    /* ========================================================
       SOURCES
       ======================================================== */

    .source-card {{
        background: white;
        border-left: 5px solid {GREEN};
        border-radius: 10px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
    }}

    /* ========================================================
       BUTTONS
       ======================================================== */

    .stButton > button {{
        border-radius: 12px;
        font-weight: 800;
        min-height: 45px;
    }}

    /* ========================================================
       SIDEBAR
       ======================================================== */

    section[data-testid="stSidebar"] {{
        background:
            linear-gradient(
                180deg,
                #F4F0BB 0%,
                #E8F5E9 100%
            );
    }}

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {{
        color: {DARK_GREEN} !important;
    }}

    /* ========================================================
       METRICS
       ======================================================== */

    div[data-testid="stMetric"] {{
        background: white;
        border-radius: 14px;
        padding: 0.8rem;
        border: 1px solid #E5E5E5;
    }}

    /* ========================================================
       FOOTER
       ======================================================== */

    .footer {{
        text-align: center;
        color: {BROWN};
        padding: 1rem;
        font-size: 0.9rem;
    }}

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

def clean_text(text):
    """
    Remove accidental HTML/code wrappers while preserving
    Markdown so Streamlit can render the itinerary properly.
    """

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

    text = re.sub(
        r"```(?:html|HTML|markdown|Markdown)?",
        "",
        text,
    )

    text = text.replace(
        "```",
        "",
    )

    return text.strip()


def extract_text_from_result(result):
    """
    Safely extract generated itinerary text.
    """

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

            value = result.get(key)

            if value:
                return str(value)

        return json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )

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
            or metadata.get("document")
            or item.get("document")
            or metadata.get("filename")
            or item.get("filename")
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

        source = source.split("/")[-1]

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


# ============================================================
# IMPORT HELPERS
# ============================================================

def safe_import_retriever():

    from src.retriever import HybridRetriever

    return HybridRetriever


def safe_import_crew():

    from src.crew import TrekTalesCrew

    return TrekTalesCrew


def safe_import_payment():

    from src.payment import verify_payment

    return verify_payment


def safe_import_vision():

    from src.vision import analyze_payment_screenshot

    return analyze_payment_screenshot


# ============================================================
# RETRIEVER
# ============================================================

def retrieve_with_retriever(
    retriever,
    query,
):

    if hasattr(retriever, "search"):

        try:

            return retriever.search(
                query,
                top_k=6,
            )

        except TypeError:

            return retriever.search(query)

    if hasattr(retriever, "retrieve"):

        try:

            return retriever.retrieve(
                query,
                top_k=6,
            )

        except TypeError:

            return retriever.retrieve(query)

    raise AttributeError(
        "HybridRetriever must provide search() "
        "or retrieve()."
    )


# ============================================================
# CREW RUNNER
# ============================================================

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

    request = {
        "destination": destination,
        "starting_location": starting_location,
        "days": duration,
        "duration": duration,
        "budget": budget,
        "travelers": travelers,
        "travel_style": travel_style,
        "language": language,
        "interests": interests,
        "evidence": evidence,
    }

    # --------------------------------------------------------
    # run()
    # --------------------------------------------------------

    if hasattr(crew, "run"):

        try:

            return crew.run(
                destination=destination,
                starting_location=starting_location,
                days=duration,
                budget=budget,
                travelers=travelers,
                travel_style=travel_style,
                language=language,
                interests=interests,
                evidence=evidence,
            )

        except TypeError:

            try:

                return crew.run(request)

            except TypeError:
                pass

    # --------------------------------------------------------
    # kickoff()
    # --------------------------------------------------------

    if hasattr(crew, "kickoff"):

        try:

            return crew.kickoff(request)

        except TypeError:
            pass

    # --------------------------------------------------------
    # plan()
    # --------------------------------------------------------

    if hasattr(crew, "plan"):

        try:

            return crew.plan(
                destination=destination,
                starting_location=starting_location,
                duration=duration,
                days=duration,
                budget=budget,
                travelers=travelers,
                travel_style=travel_style,
                language=language,
                interests=interests,
                evidence=evidence,
            )

        except TypeError:
            pass

    # --------------------------------------------------------
    # generate()
    # --------------------------------------------------------

    if hasattr(crew, "generate"):

        try:

            return crew.generate(
                destination=destination,
                starting_location=starting_location,
                duration=duration,
                days=duration,
                budget=budget,
                travelers=travelers,
                travel_style=travel_style,
                language=language,
                interests=interests,
                evidence=evidence,
            )

        except TypeError:
            pass

    raise RuntimeError(
        "TrekTalesCrew does not provide a compatible "
        "run(), kickoff(), plan(), or generate() method."
    )


# ============================================================
# PAYMENT HELPERS
# ============================================================

def verify_payment_safely(payment_data):

    verify_payment = safe_import_payment()

    try:

        return verify_payment(payment_data)

    except TypeError:

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

        days = FREE_DAYS

    return max(
        1,
        min(
            days,
            PAID_DAYS,
        ),
    )


# ============================================================
# BRAND HEADER
# ============================================================

st.markdown(
    """
    <div class="brand">

        <div class="brand-title">
            🌿 TrekTales
        </div>

        <div class="brand-subtitle">
            AI-Powered Personalized Travel Planner
        </div>

        <div class="brand-tagline">
            Discover Rawalpindi through a smarter,
            personalized adventure plan.
        </div>

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

    st.write(
        "Your AI travel companion for personalized "
        "Rawalpindi adventures."
    )

    st.divider()

    # --------------------------------------------------------
    # ACCESS
    # --------------------------------------------------------

    st.markdown(
        "### 🔐 Trip Access"
    )

    st.write(
        f"🆓 **Day {FREE_DAYS}** — Free"
    )

    st.write(
        f"🔒 **Days {FREE_DAYS + 1}–{PAID_DAYS}** "
        f"— Rs. {UNLOCK_PRICE}"
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

    # --------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------

    language = st.selectbox(
        "🌐 Itinerary Language",
        [
            "English",
            "Urdu",
            "Roman Urdu",
        ],
    )

    st.divider()

    # --------------------------------------------------------
    # AGENTS
    # --------------------------------------------------------

    st.markdown(
        "### 🤖 TrekTales AI Crew"
    )

    agents = [
        (
            "01",
            "Master Orchestrator",
            "Coordinates the complete travel workflow.",
        ),
        (
            "02",
            "Knowledge Agent",
            "Retrieves grounded tourism information.",
        ),
        (
            "03",
            "Planner Agent",
            "Builds the personalized itinerary.",
        ),
        (
            "04",
            "Budget Agent",
            "Keeps activities aligned with the budget.",
        ),
        (
            "05",
            "Safety Agent",
            "Adds practical travel safety guidance.",
        ),
        (
            "06",
            "Summarizer Agent",
            "Structures the final travel plan.",
        ),
        (
            "07",
            "Payment Agent",
            "Handles premium verification.",
        ),
        (
            "08",
            "Vision Agent",
            "Analyzes uploaded payment screenshots.",
        ),
    ]

    for number, name, description in agents:

        with st.container(
            border=True,
        ):

            st.caption(
                f"AGENT {number}"
            )

            st.markdown(
                f"**{name}**"
            )

            st.caption(
                description
            )

    st.divider()

    st.caption(
        f"Powered by Groq • {GROQ_MODEL}"
    )


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="hero">

        <div class="hero-title">
            🌍 Your Adventure Starts Here
        </div>

        <div class="hero-text">
            Tell TrekTales how you want to explore
            Rawalpindi. Our AI-powered travel workflow
            combines your preferences, budget, interests
            and tourism knowledge base to create a
            personalized itinerary.
        </div>

        <div class="hero-pills">
            📚 Knowledge Grounding
            &nbsp; • &nbsp;
            🤖 Multi-Agent Planning
            &nbsp; • &nbsp;
            💰 Budget Awareness
            &nbsp; • &nbsp;
            🥾 Personalized Experiences
            &nbsp; • &nbsp;
            🛡️ Safety Guidance
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# FEATURES
# ============================================================

st.markdown(
    "## ✨ Why TrekTales?"
)

feature_columns = st.columns(3)

features = [
    (
        "🧠",
        "Knowledge-Grounded",
        "Tourism recommendations are grounded using "
        "your FAISS tourism knowledge base."
    ),
    (
        "🤖",
        "Multi-Agent AI",
        "Specialized agents work together to create "
        "a structured travel experience."
    ),
    (
        "💚",
        "Personalized",
        "Your duration, travelers, budget, style and "
        "interests shape the itinerary."
    ),
]

for column, feature in zip(
    feature_columns,
    features,
):

    icon, title, description = feature

    with column:

        st.markdown(
            f"""
            <div class="feature-card">

                <div style="font-size:2rem;">
                    {icon}
                </div>

                <div class="feature-title">
                    {title}
                </div>

                <div class="feature-text">
                    {description}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


st.divider()


# ============================================================
# TRIP INPUT
# ============================================================

st.markdown(
    "## 🧭 Build Your Rawalpindi Adventure"
)

st.caption(
    "Customize your experience and let TrekTales "
    "create your personalized plan."
)

input_col1, input_col2 = st.columns(2)


# ============================================================
# LEFT INPUTS
# ============================================================

with input_col1:

    destination = "Rawalpindi"

    st.markdown(
        """
        <div class="destination-card">

            <div class="destination-label">
                📍 Destination
            </div>

            <div class="destination-name">
                RAWALPINDI
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    starting_location = st.text_input(
        "🚗 Starting Point",
        placeholder="e.g. Islamabad, Saddar, Bahria Town",
    )

    requested_duration = st.selectbox(
        "📅 Trip Duration",
        options=[
            1,
            2,
            3,
        ],
        format_func=lambda x: (
            "1 Day — Quick Adventure"
            if x == 1
            else "2 Days — Explore More"
            if x == 2
            else "3 Days — Full Experience"
        ),
    )

    travelers = st.number_input(
        "👥 Travelers",
        min_value=1,
        max_value=20,
        value=2,
        step=1,
    )


# ============================================================
# RIGHT INPUTS
# ============================================================

with input_col2:

    budget_options = {

        "Budget — PKR 1,500–3,000/person/day":
            "PKR 1,500–3,000 per person per day",

        "Moderate — PKR 3,000–6,000/person/day":
            "PKR 3,000–6,000 per person per day",

        "Comfortable — PKR 6,000–10,000/person/day":
            "PKR 6,000–10,000 per person per day",

        "Premium — PKR 10,000–20,000+/person/day":
            "PKR 10,000–20,000+ per person per day",
    }

    budget_label = st.selectbox(
        "💰 Daily Budget",
        list(
            budget_options.keys()
        ),
    )

    budget = budget_options[
        budget_label
    ]

    travel_style = st.selectbox(
        "🎒 Travel Style",
        [
            "Active & Outdoor",
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
        "⭐ What interests you?",
        [
            "Nature",
            "Photography",
            "Local Culture",
            "History",
            "Food",
            "Adventure",
            "Shopping",
            "Family Activities",
            "Architecture",
            "Outdoor Activities",
        ],
        default=[
            "Nature",
            "Photography",
            "Local Culture",
        ],
    )


# ============================================================
# ACCESS CONTROL
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
        f"🔒 You selected {requested_duration} days. "
        f"Day 1 is free. Unlock the complete "
        f"{requested_duration}-day itinerary for "
        f"Rs. {UNLOCK_PRICE}."
    )


st.divider()


# ============================================================
# TRIP SUMMARY
# ============================================================

st.markdown(
    "## 📝 Your Trip Preferences"
)

summary1, summary2, summary3, summary4 = st.columns(4)

with summary1:
    st.metric(
        "📍 Destination",
        "Rawalpindi",
    )

with summary2:
    st.metric(
        "📅 Days",
        accessible_duration,
    )

with summary3:
    st.metric(
        "👥 Travelers",
        travelers,
    )

with summary4:
    st.metric(
        "🎒 Style",
        travel_style,
    )


st.divider()


# ============================================================
# SYSTEM STATUS
# ============================================================

with st.expander(
    "⚙️ TrekTales System Status",
    expanded=False,
):

    status_col1, status_col2, status_col3 = st.columns(3)

    # --------------------------------------------------------
    # GROQ
    # --------------------------------------------------------

    with status_col1:

        st.markdown(
            "### 🧠 AI Model"
        )

        if GROQ_API_KEY:

            st.success(
                "Groq API key detected"
            )

        else:

            st.error(
                "Groq API key missing"
            )

    # --------------------------------------------------------
    # FAISS
    # --------------------------------------------------------

    with status_col2:

        st.markdown(
            "### 📚 Knowledge Base"
        )

        index_exists = (
            FAISS_INDEX_PATH.exists()
        )

        metadata_exists = (
            FAISS_METADATA_PATH.exists()
        )

        config_exists = (
            FAISS_CONFIG_PATH.exists()
        )

        if (
            index_exists
            and metadata_exists
        ):

            st.success(
                "FAISS index ready"
            )

        else:

            st.error(
                "FAISS index incomplete"
            )

        st.caption(
            f"index.faiss: "
            f"{'✓' if index_exists else '✗'}"
        )

        st.caption(
            f"metadata.json: "
            f"{'✓' if metadata_exists else '✗'}"
        )

        st.caption(
            f"config.json: "
            f"{'✓' if config_exists else '✗'}"
        )

    # --------------------------------------------------------
    # AGENTS
    # --------------------------------------------------------

    with status_col3:

        st.markdown(
            "### 🤖 AI Crew"
        )

        st.success(
            "8-agent architecture"
        )

        st.caption(
            f"Planning days: "
            f"{accessible_duration}"
        )


# ============================================================
# GENERATE BUTTON
# ============================================================

st.markdown("")

generate_trip = st.button(
    "🌿 Create My Personalized TrekTales Adventure",
    use_container_width=True,
    type="primary",
)


# ============================================================
# GENERATION
# ============================================================

if generate_trip:

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

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
    # RESET OLD RESULT
    # --------------------------------------------------------

    st.session_state.trip_result = None
    st.session_state.trip_evidence = []
    st.session_state.last_error = None

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    with st.status(
        "🌿 Creating your TrekTales adventure...",
        expanded=True,
    ) as status:

        # ====================================================
        # RETRIEVAL
        # ====================================================

        st.write(
            "📚 Searching the tourism knowledge base..."
        )

        try:

            RetrieverClass = (
                safe_import_retriever()
            )

            retriever = RetrieverClass(
                index_path=FAISS_INDEX_PATH,
                metadata_path=FAISS_METADATA_PATH,
                config_path=FAISS_CONFIG_PATH,
            )

            query = (
                f"Rawalpindi travel itinerary. "
                f"Destination: {destination}. "
                f"Starting location: {starting_location}. "
                f"Duration: {accessible_duration} days. "
                f"Travelers: {travelers}. "
                f"Budget: {budget}. "
                f"Travel style: {travel_style}. "
                f"Interests: "
                f"{', '.join(interests)}. "
                f"Find relevant attractions, "
                f"activities, local culture, nature, "
                f"photography opportunities, food, "
                f"travel considerations and safety "
                f"information from the knowledge base."
            )

            evidence = retrieve_with_retriever(
                retriever,
                query,
            )

            if evidence is None:
                evidence = []

            st.session_state.trip_evidence = evidence

            st.write(
                f"✓ Retrieved {len(evidence)} "
                f"relevant knowledge items."
            )

            if not evidence:

                st.warning(
                    "No relevant tourism evidence was retrieved. "
                    "The AI should not invent unsupported "
                    "tourism facts."
                )

        except Exception as exc:

            status.update(
                label="❌ Knowledge retrieval failed",
                state="error",
                expanded=True,
            )

            st.error(
                "The tourism knowledge base could not "
                "be loaded."
            )

            st.exception(exc)

            st.stop()

        # ====================================================
        # PREMIUM
        # ====================================================

        if (
            requested_duration > FREE_DAYS
            and not st.session_state.payment_verified
        ):

            st.info(
                f"🔒 Premium locked. "
                f"TrekTales will generate Day 1 as the "
                f"free preview."
            )

        # ====================================================
        # AI CREW
        # ====================================================

        st.write(
            "🤖 Activating the TrekTales AI crew..."
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

            if not result:

                raise RuntimeError(
                    "The AI crew returned an empty itinerary."
                )

            st.session_state.trip_result = result

            status.update(
                label="🌿 Your TrekTales adventure is ready!",
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
                "The TrekTales AI crew could not "
                "generate the itinerary."
            )

            st.exception(exc)

            st.stop()


# ============================================================
# DISPLAY ITINERARY
# ============================================================

if st.session_state.trip_result:

    st.divider()

    st.markdown(
        "## 🗺️ Your Personalized Rawalpindi Adventure"
    )

    if st.session_state.payment_verified:

        st.success(
            f"🔓 Premium itinerary • "
            f"{accessible_duration} day(s)"
        )

    elif requested_duration > FREE_DAYS:

        st.info(
            "🆓 Free preview • Day 1"
        )

    # --------------------------------------------------------
    # EXTRACT OUTPUT
    # --------------------------------------------------------

    answer = extract_text_from_result(
        st.session_state.trip_result
    )

    answer = clean_text(
        answer
    )

    # --------------------------------------------------------
    # OUTPUT CARD
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="itinerary-header">
            🌿 TrekTales • Personalized Adventure Plan
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(
        border=True,
    ):

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

    with st.expander(
        "📚 Tourism Knowledge Sources",
        expanded=False,
    ):

        st.caption(
            "These are the source documents retrieved "
            "from the TrekTales tourism knowledge base."
        )

        for source in sources:

            page_text = ""

            if (
                source["page"]
                and source["page"].lower() != "n/a"
            ):

                page_text = (
                    f" • Page {source['page']}"
                )

            st.markdown(
                f"""
                <div class="source-card">
                    📄 <strong>{source['source']}</strong>
                    {page_text}
                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# PREMIUM UNLOCK
# ============================================================

if requested_duration >= 2:

    st.divider()

    st.markdown(
        "## 🔐 Unlock Your Complete Adventure"
    )

    st.markdown(
        f"""
        <div class="premium-card">

            <div class="premium-title">
                {'🔓 Premium Unlocked'
                 if st.session_state.payment_verified
                 else '🌟 Continue Exploring'}
            </div>

            <p>
                {
                    f'Premium access is active. You can now '
                    f'generate your complete {requested_duration}-day '
                    f'Rawalpindi adventure.'
                    if st.session_state.payment_verified
                    else
                    f'Day 1 is free. Unlock the remaining '
                    f'itinerary for only Rs. {UNLOCK_PRICE}.'
                }
            </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    # ========================================================
    # PAYMENT
    # ========================================================

    if not st.session_state.payment_verified:

        st.markdown(
            "### 💳 Premium Payment Verification"
        )

        payment_col1, payment_col2 = st.columns(2)

        with payment_col1:

            st.write(
                f"**Unlock Price:** Rs. {UNLOCK_PRICE}"
            )

            st.write(
                f"**Recipient:** "
                f"{EXPECTED_PAYMENT_RECIPIENT}"
            )

            if QR_PATH.exists():

                st.image(
                    str(QR_PATH),
                    caption="TrekTales Payment QR",
                    width=280,
                )

            else:

                st.warning(
                    "Payment QR not found at "
                    "`assets/jazzcash_qr.jpg`."
                )

        with payment_col2:

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
                    "👁️ Analyze Payment Screenshot",
                    use_container_width=True,
                )

                if verify_button:

                    with st.spinner(
                        "👁️ Vision Agent is analyzing "
                        "your payment screenshot..."
                    ):

                        try:

                            analyze_payment_screenshot = (
                                safe_import_vision()
                            )

                            try:

                                vision_result = (
                                    analyze_payment_screenshot(
                                        uploaded_screenshot
                                    )
                                )

                            except TypeError:

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

                    # ========================================
                    # VISION RESULT
                    # ========================================

                    vision = (
                        st.session_state.vision_result
                    )

                    if not isinstance(
                        vision,
                        dict,
                    ):

                        st.error(
                            "Vision Agent returned an "
                            "unexpected response format."
                        )

                        st.stop()

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
                            f"Vision confidence: "
                            f"{confidence}"
                        )

                    # ========================================
                    # DETERMINISTIC VERIFICATION
                    # ========================================

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
                            "The deterministic payment "
                            "verifier could not validate "
                            "the result."
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
                            "✅ Payment verified successfully!"
                        )

                        st.info(
                            "Generate your itinerary again "
                            "to unlock all requested days."
                        )

                    else:

                        st.error(
                            "❌ Payment could not be verified."
                        )

                        st.warning(
                            "The recipient, amount or payment "
                            "status did not satisfy the application's "
                            "verification rules."
                        )

    # ========================================================
    # PREMIUM ACTIVE
    # ========================================================

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
# TRAVEL DISCLAIMER
# ============================================================

st.divider()

with st.container(
    border=True,
):

    st.markdown(
        """
        **🌿 Travel Note:** TrekTales provides travel-planning
        information for general informational purposes.
        Prices, opening hours, weather, transport schedules,
        road conditions, availability and local circumstances
        can change. Verify important details with current
        official or local sources before travelling.
        """
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    "---"
)

st.markdown(
    """
    <div class="footer">

        🌿 <strong>TrekTales</strong>
        &nbsp; • &nbsp;
        AI-Powered Rawalpindi Travel Planner
        &nbsp; • &nbsp;
        Built with Streamlit + Groq

    </div>
    """,
    unsafe_allow_html=True,
)
