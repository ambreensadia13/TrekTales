import re
from pathlib import Path

import streamlit as st

from src.config import (
    FREE_DAYS,
    PAID_DAYS,
    UNLOCK_PRICE,
    EXPECTED_PAYMENT_RECIPIENT,
    GROQ_MODEL,
)

from src.crew import TrekTalesCrew
from src.retriever import HybridRetriever
from src.payment import verify_payment
from src.vision import analyze_payment_screenshot


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
# CUSTOM CSS
# ============================================================

st.markdown(
    f"""
    <style>

    /* --------------------------------------------------------
       GLOBAL
    -------------------------------------------------------- */

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

    /* --------------------------------------------------------
       TOP TREKTALES BRAND
    -------------------------------------------------------- */

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

    /* --------------------------------------------------------
       SIDEBAR
    -------------------------------------------------------- */

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

    section[data-testid="stSidebar"] .stMarkdown p {{
        color: {WHITE} !important;
    }}

    /* Sidebar access card */

    div[class*="st-key-sidebar_access"] {{
        background: rgba(255, 255, 255, 0.10) !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        border-radius: 16px !important;
        padding: 1rem !important;
    }}

    div[class*="st-key-sidebar_access"] * {{
        color: {WHITE} !important;
    }}

    /* Sidebar agent cards */

    div[class*="st-key-agent_"] {{
        background: rgba(255, 255, 255, 0.09) !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
        border-left: 4px solid {LIGHT_GREEN} !important;
        border-radius: 12px !important;
        padding: 0.7rem !important;
        margin-bottom: 0.55rem !important;
    }}

    div[class*="st-key-agent_"] * {{
        color: {WHITE} !important;
    }}

    /* --------------------------------------------------------
       HERO
    -------------------------------------------------------- */

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
        box-shadow: 0 15px 35px rgba(34, 111, 84, 0.20);
    }}

    div[class*="st-key-hero"] * {{
        color: {WHITE} !important;
    }}

    /* --------------------------------------------------------
       LIGHT FEATURE CARDS
    -------------------------------------------------------- */

    div[class*="st-key-feature_"] {{
        background: {WHITE} !important;
        border: 1px solid rgba(34, 111, 84, 0.18) !important;
        border-radius: 18px !important;
        padding: 1.1rem !important;
        min-height: 175px;
        box-shadow: 0 7px 20px rgba(67, 41, 31, 0.08);
    }}

    div[class*="st-key-feature_"] * {{
        color: {BLACK} !important;
    }}

    /* --------------------------------------------------------
       LIGHT CONTENT CARDS
    -------------------------------------------------------- */

    div[class*="st-key-light_card"] {{
        background: {WHITE} !important;
        border: 1px solid rgba(34, 111, 84, 0.18) !important;
        border-radius: 18px !important;
        padding: 1.2rem !important;
        box-shadow: 0 7px 20px rgba(67, 41, 31, 0.07);
    }}

    div[class*="st-key-light_card"] * {{
        color: {BLACK} !important;
    }}

    /* --------------------------------------------------------
       ANSWER CARD
    -------------------------------------------------------- */

    div[class*="st-key-answer_card"] {{
        background: {WHITE} !important;
        border: 2px solid {LIGHT_GREEN} !important;
        border-radius: 20px !important;
        padding: 1.4rem !important;
        box-shadow: 0 8px 25px rgba(34, 111, 84, 0.10);
    }}

    div[class*="st-key-answer_card"] * {{
        color: {BLACK} !important;
    }}

    /* --------------------------------------------------------
       DARK LOCKED CARD
    -------------------------------------------------------- */

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

    /* --------------------------------------------------------
       PAYMENT CARD
    -------------------------------------------------------- */

    div[class*="st-key-payment_card"] {{
        background: {WHITE} !important;
        border: 2px solid {RED} !important;
        border-radius: 20px !important;
        padding: 1.4rem !important;
        box-shadow: 0 8px 25px rgba(218, 44, 56, 0.12);
    }}

    div[class*="st-key-payment_card"] * {{
        color: {BLACK} !important;
    }}

    /* --------------------------------------------------------
       DISCLAIMER
    -------------------------------------------------------- */

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

    /* --------------------------------------------------------
       STATUS CARDS
    -------------------------------------------------------- */

    div[class*="st-key-status_"] {{
        background: {WHITE} !important;
        border: 1px solid rgba(34, 111, 84, 0.20) !important;
        border-radius: 14px !important;
        padding: 0.8rem !important;
    }}

    div[class*="st-key-status_"] * {{
        color: {BLACK} !important;
    }}

    /* --------------------------------------------------------
       SOURCE CARDS
    -------------------------------------------------------- */

    div[class*="st-key-source_"] {{
        background: {LIGHT_GREY} !important;
        border: 1px solid #DDDDDD !important;
        border-radius: 12px !important;
        padding: 0.8rem !important;
    }}

    div[class*="st-key-source_"] * {{
        color: {BLACK} !important;
    }}

    /* --------------------------------------------------------
       BUTTONS
    -------------------------------------------------------- */

    .stButton > button {{
        background: {RED} !important;
        color: {WHITE} !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        min-height: 2.7rem;
        transition: 0.2s ease;
    }}

    .stButton > button:hover {{
        background: {GREEN} !important;
        color: {WHITE} !important;
        border: none !important;
    }}

    .stButton > button p {{
        color: {WHITE} !important;
    }}

    /* --------------------------------------------------------
       INPUTS
    -------------------------------------------------------- */

    div[data-baseweb="select"] > div {{
        background: {WHITE} !important;
        color: {BLACK} !important;
    }}

    div[data-baseweb="select"] * {{
        color: {BLACK} !important;
    }}

    input, textarea {{
        color: {BLACK} !important;
        background: {WHITE} !important;
    }}

    textarea {{
        border-radius: 12px !important;
    }}

    /* --------------------------------------------------------
       FILE UPLOADER
    -------------------------------------------------------- */

    section[data-testid="stFileUploaderDropzone"] {{
        background: {WHITE} !important;
        border: 1px dashed {GREEN} !important;
        border-radius: 14px !important;
    }}

    section[data-testid="stFileUploaderDropzone"] * {{
        color: {BLACK} !important;
    }}

    /* --------------------------------------------------------
       METRICS
    -------------------------------------------------------- */

    div[data-testid="stMetric"] {{
        background: {WHITE};
        border: 1px solid rgba(34, 111, 84, 0.18);
        border-radius: 14px;
        padding: 0.8rem;
    }}

    div[data-testid="stMetric"] * {{
        color: {BLACK} !important;
    }}

    /* --------------------------------------------------------
       MOBILE
       Colors remain exactly the same.
    -------------------------------------------------------- */

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

        div[class*="st-key-answer_card"] {{
            padding: 1rem !important;
        }}

        div[class*="st-key-payment_card"] {{
            padding: 1rem !important;
        }}
    }}

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "trip_result" not in st.session_state:
    st.session_state.trip_result = None

if "trip_evidence" not in st.session_state:
    st.session_state.trip_evidence = []

if "payment_verified" not in st.session_state:
    st.session_state.payment_verified = False

if "payment_result" not in st.session_state:
    st.session_state.payment_result = None

if "vision_result" not in st.session_state:
    st.session_state.vision_result = None


# ============================================================
# HELPERS
# ============================================================

def clean_display_text(value):
    """
    Removes accidental HTML tags from AI-generated text.
    Markdown remains supported.
    """
    if value is None:
        return ""

    text = str(value)

    # Remove HTML tags.
    text = re.sub(r"<[^>]+>", "", text)

    # Remove accidental HTML code fences.
    text = text.replace("```html", "")
    text = text.replace("```HTML", "")
    text = text.replace("```", "")

    return text.strip()


def get_retriever():
    """
    Creates the hybrid retriever.
    """
    return HybridRetriever()


def retrieve_evidence(retriever, query):
    """
    Supports either .search() or .retrieve() depending
    on the retriever implementation.
    """

    try:
        if hasattr(retriever, "search"):
            return retriever.search(
                query,
                top_k=6,
            )

        if hasattr(retriever, "retrieve"):
            return retriever.retrieve(
                query,
                top_k=6,
            )

    except TypeError:
        if hasattr(retriever, "search"):
            return retriever.search(query)

        if hasattr(retriever, "retrieve"):
            return retriever.retrieve(query)

    return []


def format_sources(evidence):
    """
    Extracts source information safely.
    """

    sources = []

    if not evidence:
        return sources

    for item in evidence:

        if not isinstance(item, dict):
            continue

        metadata = item.get("metadata", {})

        if not isinstance(metadata, dict):
            metadata = {}

        source = (
            metadata.get("source")
            or item.get("source")
            or "Unknown source"
        )

        page = (
            metadata.get("page")
            or item.get("page")
            or "N/A"
        )

        department = (
            metadata.get("department")
            or item.get("department")
            or ""
        )

        sources.append(
            {
                "source": str(source),
                "page": str(page),
                "department": str(department),
            }
        )

    return sources


def run_trip_planner(
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
    Runs the TrekTales multi-agent crew.
    """

    crew = TrekTalesCrew()

    request = {
        "destination": destination,
        "duration": duration,
        "budget": budget,
        "travelers": travelers,
        "travel_style": travel_style,
        "language": language,
        "interests": interests,
        "starting_location": starting_location,
        "evidence": evidence,
    }

    # Support common crew interfaces.
    if hasattr(crew, "run"):
        return crew.run(request)

    if hasattr(crew, "kickoff"):
        return crew.kickoff(request)

    raise AttributeError(
        "TrekTalesCrew must provide either run() or kickoff()."
    )


# ============================================================
# TOP BRAND
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

    # --------------------------------------------------------
    # ACCESS MODEL
    # --------------------------------------------------------

    with st.container(
        border=True,
        key="sidebar_access",
    ):

        st.markdown("### 🔐 Access Model")

        st.markdown(
            f"**Day 1:** Free"
        )

        st.markdown(
            f"**Days {FREE_DAYS + 1}–{PAID_DAYS}:** "
            f"Rs. {UNLOCK_PRICE} demo unlock"
        )

    st.divider()

    # --------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------

    language = st.selectbox(
        "🌐 Response Language",
        [
            "English",
            "Urdu",
            "Roman Urdu",
        ],
    )

    # --------------------------------------------------------
    # AGENTS
    # --------------------------------------------------------

    st.markdown("### 🤖 AI Agents")

    agents = [
        (
            1,
            "Master Orchestrator",
            "Coordinates the complete travel workflow.",
        ),
        (
            2,
            "Knowledge Agent",
            "Retrieves tourism knowledge from the FAISS database.",
        ),
        (
            3,
            "Planner Agent",
            "Builds the itinerary and daily travel plan.",
        ),
        (
            4,
            "Budget Agent",
            "Estimates expenses and keeps the trip budget-aware.",
        ),
        (
            5,
            "Safety Agent",
            "Provides destination and travel safety guidance.",
        ),
        (
            6,
            "Summarizer Agent",
            "Turns the final plan into a clear travel summary.",
        ),
        (
            7,
            "Payment Agent",
            "Handles the demo payment verification workflow.",
        ),
        (
            8,
            "Vision Agent",
            "Analyzes uploaded payment screenshots.",
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
        f"Model: {GROQ_MODEL}"
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
        "Create practical, personalized travel plans using "
        "a multi-agent AI system grounded in your tourism knowledge base."
    )

    st.markdown(
        "📚 Knowledge Grounding  •  🗺️ Smart Planning  •  "
        "💰 Budget Awareness  •  🛡️ Safety  •  👁️ Vision Verification"
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

        st.markdown("### 🧠 Knowledge Grounding")

        st.write(
            "Uses your tourism knowledge base and FAISS retrieval "
            "to ground travel recommendations."
        )

with feature_columns[1]:

    with st.container(
        border=True,
        key="feature_agents",
    ):

        st.markdown("### 🤖 8 AI Agents")

        st.write(
            "Specialized agents work together for research, "
            "planning, budgeting, safety, summaries and verification."
        )

with feature_columns[2]:

    with st.container(
        border=True,
        key="feature_payment",
    ):

        st.markdown("### 💳 Demo Unlock")

        st.write(
            f"Day 1 is free. Additional days use the "
            f"Rs. {UNLOCK_PRICE} demo payment workflow."
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
        placeholder="e.g. Murree, Hunza, Skardu",
    )

    starting_location = st.text_input(
        "🚗 Starting Location",
        placeholder="e.g. Islamabad",
    )

    duration = st.slider(
        "📅 Trip Duration",
        min_value=1,
        max_value=3,
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


st.divider()


# ============================================================
# SYSTEM STATUS
# ============================================================

st.markdown("## ⚙️ System Status")

status_col1, status_col2, status_col3 = st.columns(3)

# ------------------------------------------------------------
# GROQ
# ------------------------------------------------------------

with status_col1:

    with st.container(
        border=True,
        key="status_groq",
    ):

        st.markdown("### 🧠 AI Model")

        try:
            groq_key_exists = bool(
                st.secrets.get("GROQ_API_KEY", "")
            )
        except Exception:
            groq_key_exists = False

        if groq_key_exists:
            st.markdown("● Groq API key detected")
        else:
            st.markdown("● Groq API key not found")


# ------------------------------------------------------------
# FAISS
# ------------------------------------------------------------

with status_col2:

    with st.container(
        border=True,
        key="status_faiss",
    ):

        st.markdown("### 📚 Knowledge Base")

        index_path = Path(
            "data/faiss_index/index.faiss"
        )

        metadata_path = Path(
            "data/faiss_index/metadata.json"
        )

        if index_path.exists() and metadata_path.exists():
            st.markdown("● FAISS index ready")
        else:
            st.markdown("● FAISS index not found")


# ------------------------------------------------------------
# AGENTS
# ------------------------------------------------------------

with status_col3:

    with st.container(
        border=True,
        key="status_agents",
    ):

        st.markdown("### 🤖 Agent System")

        st.markdown(
            "● 8-agent architecture configured"
        )


st.divider()


# ============================================================
# GENERATE TRIP
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
            "Please enter a destination first."
        )
        st.stop()

    if not starting_location.strip():

        st.error(
            "Please enter your starting location."
        )
        st.stop()

    # --------------------------------------------------------
    # RESET
    # --------------------------------------------------------

    st.session_state.trip_result = None
    st.session_state.trip_evidence = []

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

            retriever = get_retriever()

            query = (
                f"Destination: {destination}. "
                f"Starting location: {starting_location}. "
                f"Duration: {duration} days. "
                f"Budget: {budget}. "
                f"Travelers: {travelers}. "
                f"Travel style: {travel_style}. "
                f"Interests: {', '.join(interests)}."
            )

            evidence = retrieve_evidence(
                retriever,
                query,
            )

            st.session_state.trip_evidence = evidence

            st.write(
                f"Retrieved {len(evidence)} knowledge items."
            )

        except Exception as exc:

            st.error(
                "Could not load the tourism knowledge base."
            )

            st.exception(exc)
            st.stop()

        # ----------------------------------------------------
        # MULTI-AGENT CREW
        # ----------------------------------------------------

        st.write(
            "🤖 Activating the TrekTales AI agents..."
        )

        try:

            result = run_trip_planner(
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
                "The AI travel planner encountered an error."
            )

            st.exception(exc)
            st.stop()


# ============================================================
# DISPLAY TRIP RESULT
# ============================================================

if st.session_state.trip_result:

    st.divider()

    st.markdown("## 🗺️ Your TrekTales Plan")

    raw_result = st.session_state.trip_result

    if isinstance(raw_result, dict):

        answer = (
            raw_result.get("answer")
            or raw_result.get("result")
            or raw_result.get("output")
            or raw_result.get("plan")
            or str(raw_result)
        )

    else:

        answer = str(raw_result)

    answer = clean_display_text(answer)

    with st.container(
        border=True,
        key="answer_card",
    ):

        st.markdown("### 🌿 Your Personalized Itinerary")

        st.markdown(
            answer,
            unsafe_allow_html=False,
        )


    # ========================================================
    # SOURCES
    # ========================================================

    sources = format_sources(
        st.session_state.trip_evidence
    )

    if sources:

        st.markdown("## 📚 Knowledge Sources")

        for index, source in enumerate(sources):

            source_name = source["source"]
            page = source["page"]
            department = source["department"]

            with st.container(
                border=True,
                key=f"source_{index}",
            ):

                st.markdown(
                    f"**📄 {source_name}**"
                )

                st.write(
                    f"Page: {page}"
                )

                if department:
                    st.write(
                        f"Department: {department}"
                    )


# ============================================================
# PAYMENT SECTION
# ============================================================

if duration >= 2:

    st.divider()

    st.markdown("## 🔐 Unlock Additional Days")

    with st.container(
        border=True,
        key="locked_card",
    ):

        st.markdown(
            "### 🔒 Days 2–3 Require Demo Unlock"
        )

        st.markdown(
            f"Day 1 is free. "
            f"To demonstrate the payment and vision workflow, "
            f"Days 2–3 use a **Rs. {UNLOCK_PRICE}** demo payment."
        )

        st.markdown(
            "The payment verification shown here is a demo and "
            "does not connect to a real JazzCash transaction API."
        )


    # ========================================================
    # PAYMENT CARD
    # ========================================================

    with st.container(
        border=True,
        key="payment_card",
    ):

        st.markdown(
            "### 💳 Demo Payment Verification"
        )

        st.write(
            f"Send **Rs. {UNLOCK_PRICE}** to the configured "
            "demo JazzCash recipient."
        )

        st.write(
            f"Expected recipient: **{EXPECTED_PAYMENT_RECIPIENT}**"
        )

        # ----------------------------------------------------
        # QR CODE
        # ----------------------------------------------------

        qr_path = Path(
            "assets/jazzcash_qr.png"
        )

        if qr_path.exists():

            st.image(
                str(qr_path),
                caption="JazzCash Demo QR",
                width=260,
            )

        else:

            st.warning(
                "JazzCash QR image was not found at "
                "`assets/jazzcash_qr.png`."
            )

        # ----------------------------------------------------
        # SCREENSHOT
        # ----------------------------------------------------

        uploaded_screenshot = st.file_uploader(
            "📸 Upload your payment screenshot",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp",
            ],
            key="payment_screenshot",
        )

        # ----------------------------------------------------
        # VERIFY
        # ----------------------------------------------------

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

                        vision_result = analyze_payment_screenshot(
                            uploaded_screenshot
                        )

                        st.session_state.vision_result = (
                            vision_result
                        )

                    except Exception as exc:

                        st.error(
                            "The Vision Agent could not analyze "
                            "the screenshot."
                        )

                        st.exception(exc)
                        st.stop()

                # ------------------------------------------------
                # VISION RESULT
                # ------------------------------------------------

                if isinstance(
                    st.session_state.vision_result,
                    dict,
                ):

                    vision = (
                        st.session_state.vision_result
                    )

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
                        0,
                    )

                    st.markdown(
                        "### 👁️ AI Screenshot Verification"
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
                        st.write(
                            f"AI confidence: {confidence}"
                        )

                    # ------------------------------------------------
                    # DETERMINISTIC VALIDATION
                    # ------------------------------------------------

                    payment_data = {
                        "recipient": recipient,
                        "amount": amount,
                        "status": payment_status,
                    }

                    try:

                        payment_result = verify_payment(
                            payment_data
                        )

                    except TypeError:

                        try:

                            payment_result = verify_payment(
                                recipient=recipient,
                                amount=amount,
                                status=payment_status,
                            )

                        except Exception:

                            payment_result = {
                                "verified": (
                                    recipient.lower()
                                    == EXPECTED_PAYMENT_RECIPIENT.lower()
                                    and float(amount)
                                    == float(UNLOCK_PRICE)
                                    and payment_status.lower()
                                    in {
                                        "sent",
                                        "successful",
                                        "completed",
                                    }
                                )
                            }

                    except Exception:

                        payment_result = {
                            "verified": (
                                recipient.lower()
                                == EXPECTED_PAYMENT_RECIPIENT.lower()
                                and float(amount)
                                == float(UNLOCK_PRICE)
                                and payment_status.lower()
                                in {
                                    "sent",
                                    "successful",
                                    "completed",
                                }
                            )
                        }

                    st.session_state.payment_result = (
                        payment_result
                    )

                    # ------------------------------------------------
                    # FINAL RESULT
                    # ------------------------------------------------

                    if isinstance(
                        payment_result,
                        dict,
                    ):

                        verified = bool(
                            payment_result.get(
                                "verified",
                                False,
                            )
                        )

                    else:

                        verified = bool(
                            payment_result
                        )

                    st.session_state.payment_verified = (
                        verified
                    )

                    if verified:

                        st.success(
                            "✅ Demo payment verification successful."
                        )

                        st.markdown(
                            "**AI Screenshot Verification — Demo**"
                        )

                        st.info(
                            "The screenshot was analyzed by the "
                            "Vision Agent, while the final recipient, "
                            "amount and status checks were validated "
                            "deterministically by the application."
                        )

                    else:

                        st.error(
                            "❌ Payment could not be verified."
                        )

                        st.markdown(
                            "Please check the recipient, amount and "
                            "payment status shown in the screenshot."
                        )


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
        "Verify important details with official or current "
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
