import html
import json
from pathlib import Path

import streamlit as st


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="TrekTales AI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# TREKTALES COLOR PALETTE
# ============================================================

RED = "#DA2C38"
GREEN = "#226F54"
LIGHT_GREEN = "#87C38F"
CREAM = "#F4F0BB"
BROWN = "#43291F"

WHITE = "#FFFFFF"
BLACK = "#111111"
SOFT_WHITE = "#FFFDF4"
DARK_GREEN = "#174936"

LIGHT_BG = "#FFFDF4"
GREEN_BG = "#EEF8ED"


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent

QR_PATH = (
    ROOT_DIR
    / "assets"
    / "jazzcash_qr.png"
)

FAISS_INDEX_PATH = (
    ROOT_DIR
    / "data"
    / "faiss_index"
    / "index.faiss"
)

METADATA_PATH = (
    ROOT_DIR
    / "data"
    / "faiss_index"
    / "metadata.json"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    f"""
    <style>

    /* ========================================================
       GLOBAL
    ======================================================== */

    html,
    body,
    [data-testid="stAppViewContainer"] {{
        margin: 0;
        padding: 0;
    }}

    .stApp {{
        background:
            radial-gradient(
                circle at 10% 10%,
                rgba(135, 195, 143, 0.38),
                transparent 28%
            ),
            radial-gradient(
                circle at 90% 15%,
                rgba(218, 44, 56, 0.13),
                transparent 25%
            ),
            linear-gradient(
                135deg,
                {CREAM} 0%,
                #FFFDF4 48%,
                #EEF8ED 100%
            );

        color: {BROWN};
    }}

    .main .block-container {{
        max-width: 1400px;

        padding-top: 2rem;
        padding-bottom: 3rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }}


    /* ========================================================
       REMOVE DEFAULT STREAMLIT ELEMENTS
    ======================================================== */

    #MainMenu {{
        visibility: hidden;
    }}

    footer {{
        visibility: hidden;
    }}

    header {{
        background: transparent !important;
    }}


    /* ========================================================
       DEFAULT LIGHT AREA TEXT
    ======================================================== */

    .main .block-container h1,
    .main .block-container h2,
    .main .block-container h3,
    .main .block-container h4 {{
        color: {BROWN} !important;
    }}

    .main .block-container p {{
        color: {BROWN};
    }}

    .main .block-container label {{
        color: {BROWN} !important;
    }}


    /* ========================================================
       HERO
       DARK BACKGROUND = WHITE TEXT
    ======================================================== */

    .hero {{
        position: relative;

        overflow: hidden;

        background:
            linear-gradient(
                135deg,
                {GREEN} 0%,
                {DARK_GREEN} 62%,
                {BROWN} 100%
            );

        border-radius: 28px;

        padding: 42px;

        margin-bottom: 25px;

        box-shadow:
            0 20px 45px
            rgba(67, 41, 31, 0.20);
    }}

    .hero::after {{
        content: "";

        position: absolute;

        width: 240px;
        height: 240px;

        right: -70px;
        top: -90px;

        background:
            rgba(135, 195, 143, 0.30);

        border-radius: 50%;
    }}

    .hero-badge {{
        position: relative;
        z-index: 2;

        display: inline-block;

        background: {LIGHT_GREEN};

        color: {BLACK} !important;

        padding: 7px 14px;

        border-radius: 999px;

        font-size: 13px;

        font-weight: 800;

        margin-bottom: 15px;
    }}

    .hero-title {{
        position: relative;
        z-index: 2;

        color: {WHITE} !important;

        font-size: 52px;

        line-height: 1.05;

        font-weight: 900;

        margin: 0;

        letter-spacing: -1.5px;
    }}

    .hero-title span {{
        color: {CREAM} !important;
    }}

    .hero-subtitle {{
        position: relative;
        z-index: 2;

        color: {WHITE} !important;

        font-size: 18px;

        line-height: 1.65;

        max-width: 760px;

        margin-top: 15px;

        margin-bottom: 0;
    }}


    /* ========================================================
       SECTION HEADINGS
    ======================================================== */

    .section-title {{
        color: {BROWN} !important;

        font-size: 25px;

        font-weight: 850;

        margin-top: 25px;

        margin-bottom: 6px;
    }}

    .section-description {{
        color: {GREEN} !important;

        font-size: 14px;

        margin-bottom: 16px;
    }}


    /* ========================================================
       FEATURE CARDS
       LIGHT BACKGROUND = DARK TEXT
    ======================================================== */

    .feature-card {{
        background: rgba(255, 255, 255, 0.94);

        border:
            1px solid
            rgba(34, 111, 84, 0.18);

        border-radius: 18px;

        padding: 21px;

        min-height: 150px;

        box-shadow:
            0 8px 25px
            rgba(67, 41, 31, 0.08);

        box-sizing: border-box;
    }}

    .feature-icon {{
        font-size: 28px;

        margin-bottom: 8px;
    }}

    .feature-title {{
        color: {GREEN} !important;

        font-size: 17px;

        font-weight: 800;

        margin-bottom: 7px;
    }}

    .feature-text {{
        color: {BLACK} !important;

        font-size: 13px;

        line-height: 1.55;
    }}


    /* ========================================================
       AGENT CARDS
       LIGHT BACKGROUND = DARK TEXT
    ======================================================== */

    .agent-card {{
        background: {SOFT_WHITE};

        border:
            1px solid
            rgba(34, 111, 84, 0.18);

        border-left:
            5px solid {GREEN};

        border-radius: 14px;

        padding: 13px 15px;

        margin-bottom: 9px;

        box-sizing: border-box;
    }}

    .agent-number {{
        color: {RED} !important;

        font-weight: 900;

        font-size: 12px;
    }}

    .agent-name {{
        color: {BLACK} !important;

        font-weight: 800;

        font-size: 14px;
    }}

    .agent-description {{
        color: {GREEN} !important;

        font-size: 12px;

        margin-top: 3px;
    }}


    /* ========================================================
       ANSWER CARD
       WHITE BACKGROUND = DARK TEXT
    ======================================================== */

    .answer-card {{
        background: {WHITE};

        border-radius: 22px;

        border:
            2px solid
            rgba(34, 111, 84, 0.20);

        border-top:
            6px solid {RED};

        padding: 28px;

        margin-top: 18px;

        box-shadow:
            0 12px 32px
            rgba(67, 41, 31, 0.10);

        box-sizing: border-box;
    }}

    .answer-heading {{
        color: {GREEN} !important;

        font-size: 21px;

        font-weight: 850;

        margin-bottom: 15px;
    }}

    .answer-card p,
    .answer-card li {{
        color: {BLACK} !important;
    }}


    /* ========================================================
       LOCKED CARD
       DARK BACKGROUND = WHITE TEXT
    ======================================================== */

    .locked-card {{
        background:
            linear-gradient(
                135deg,
                {DARK_GREEN},
                {BROWN}
            );

        color: {WHITE} !important;

        border-radius: 22px;

        padding: 28px;

        margin-top: 20px;

        box-shadow:
            0 15px 35px
            rgba(67, 41, 31, 0.20);

        box-sizing: border-box;
    }}

    .locked-card *,
    .locked-card p {{
        color: {WHITE} !important;
    }}

    .locked-title {{
        color: {WHITE} !important;

        font-size: 23px;

        font-weight: 850;
    }}

    .locked-text {{
        color: {WHITE} !important;

        line-height: 1.6;

        font-size: 14px;
    }}

    .price {{
        color: {LIGHT_GREEN} !important;

        font-size: 32px;

        font-weight: 900;
    }}


    /* ========================================================
       PAYMENT CARD
       LIGHT BACKGROUND = DARK TEXT
    ======================================================== */

    .payment-card {{
        background: {SOFT_WHITE};

        border:
            2px solid {LIGHT_GREEN};

        border-radius: 22px;

        padding: 25px;

        margin-top: 20px;

        box-sizing: border-box;
    }}

    .payment-title {{
        color: {GREEN} !important;

        font-size: 23px;

        font-weight: 850;
    }}

    .payment-note {{
        color: {BLACK} !important;

        font-size: 13px;

        line-height: 1.6;
    }}


    /* ========================================================
       SOURCE CARDS
       LIGHT BACKGROUND = DARK TEXT
    ======================================================== */

    .source-card {{
        background: {GREEN_BG};

        border-left:
            5px solid {GREEN};

        border-radius: 12px;

        padding: 12px 15px;

        margin-top: 8px;

        box-sizing: border-box;
    }}

    .source-name {{
        color: {GREEN} !important;

        font-weight: 850;

        font-size: 13px;
    }}

    .source-page {{
        color: {BLACK} !important;

        font-size: 12px;
    }}


    /* ========================================================
       STATUS
    ======================================================== */

    .status-good {{
        background:
            rgba(135, 195, 143, 0.30);

        border:
            1px solid {LIGHT_GREEN};

        border-radius: 12px;

        padding: 12px 15px;

        color: {DARK_GREEN} !important;

        font-weight: 750;

        box-sizing: border-box;
    }}

    .status-warning {{
        background:
            rgba(218, 44, 56, 0.10);

        border:
            1px solid
            rgba(218, 44, 56, 0.35);

        border-radius: 12px;

        padding: 12px 15px;

        color: {BROWN} !important;

        font-weight: 700;

        box-sizing: border-box;
    }}


    /* ========================================================
       STREAMLIT INPUTS
       LIGHT BACKGROUND = BLACK TEXT
    ======================================================== */

    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"] > div,
    div[data-baseweb="select"] > div {{
        background:
            rgba(255, 255, 255, 0.96) !important;

        border:
            1px solid
            rgba(34, 111, 84, 0.30) !important;

        border-radius:
            12px !important;
    }}

    input,
    textarea {{
        color: {BLACK} !important;

        -webkit-text-fill-color:
            {BLACK} !important;
    }}

    input::placeholder,
    textarea::placeholder {{
        color: #555555 !important;

        opacity: 1 !important;
    }}

    div[data-baseweb="select"] * {{
        color: {BLACK} !important;
    }}


    /* ========================================================
       BUTTONS
       RED/GREEN BACKGROUND = WHITE TEXT
    ======================================================== */

    .stButton > button {{
        width: 100%;

        border: none !important;

        border-radius:
            13px !important;

        background:
            linear-gradient(
                135deg,
                {RED},
                #B8202B
            ) !important;

        color: {WHITE} !important;

        font-weight: 850 !important;

        min-height: 48px;

        box-shadow:
            0 8px 18px
            rgba(218, 44, 56, 0.20);

        transition:
            0.2s ease;
    }}

    .stButton > button,
    .stButton > button *,
    .stButton > button p,
    .stButton > button span {{
        color: {WHITE} !important;

        -webkit-text-fill-color:
            {WHITE} !important;
    }}

    .stButton > button:hover {{
        background:
            linear-gradient(
                135deg,
                {GREEN},
                {DARK_GREEN}
            ) !important;

        transform:
            translateY(-1px);
    }}


    /* ========================================================
       SIDEBAR
       DARK BACKGROUND = WHITE TEXT
    ======================================================== */

    section[data-testid="stSidebar"] {{
        background:
            linear-gradient(
                180deg,
                {BROWN} 0%,
                #2D5C4A 55%,
                {GREEN} 100%
            );

        color: {WHITE} !important;
    }}

    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4 {{
        color: {WHITE} !important;
    }}

    .sidebar-brand-title {{
        color: {WHITE} !important;

        font-size: 25px;

        font-weight: 900;

        margin-top: 12px;
    }}

    .sidebar-brand-subtitle {{
        color:
            rgba(255, 255, 255, 0.88) !important;

        font-size: 12px;

        margin-top: 2px;
    }}

    .sidebar-access {{
        background:
            rgba(255, 255, 255, 0.12);

        border-radius: 14px;

        padding: 15px;
    }}

    .sidebar-access-title {{
        color: {WHITE} !important;

        font-weight: 800;
    }}

    .sidebar-access-text {{
        color:
            rgba(255, 255, 255, 0.92) !important;

        font-size: 13px;

        margin-top: 8px;

        line-height: 1.5;
    }}

    section[data-testid="stSidebar"]
    .stButton > button {{
        background:
            {RED} !important;

        color:
            {WHITE} !important;
    }}


    /* ========================================================
       FILE UPLOADER
    ======================================================== */

    section[data-testid="stFileUploader"] {{
        color: {BLACK} !important;
    }}

    section[data-testid="stFileUploader"] label,
    section[data-testid="stFileUploader"] span {{
        color: {BLACK} !important;
    }}


    /* ========================================================
       METRICS
    ======================================================== */

    div[data-testid="stMetric"] {{
        background:
            rgba(255, 255, 255, 0.88);

        border-radius: 14px;

        padding: 12px;

        border:
            1px solid
            rgba(34, 111, 84, 0.15);

        box-sizing: border-box;
    }}

    div[data-testid="stMetric"] label {{
        color: {GREEN} !important;
    }}

    div[data-testid="stMetric"] div {{
        color: {BLACK} !important;
    }}


    /* ========================================================
       DIVIDER
    ======================================================== */

    hr {{
        border-color:
            rgba(67, 41, 31, 0.12);
    }}


    /* ========================================================
       DISCLAIMER
       LIGHT BACKGROUND = BLACK TEXT
    ======================================================== */

    .disclaimer {{
        background:
            rgba(244, 240, 187, 0.75);

        border:
            1px solid
            rgba(67, 41, 31, 0.14);

        border-radius: 15px;

        padding: 15px 18px;

        color: {BLACK} !important;

        font-size: 12px;

        line-height: 1.6;

        box-sizing: border-box;
    }}

    .disclaimer *,
    .disclaimer b {{
        color: {BLACK} !important;
    }}


    /* ========================================================
       FOOTER
    ======================================================== */

    .footer {{
        text-align: center;

        color: {GREEN} !important;

        font-size: 12px;

        margin-top: 45px;

        padding-top: 20px;

        border-top:
            1px solid
            rgba(34, 111, 84, 0.18);
    }}


    /* ========================================================
       MOBILE RESPONSIVE DESIGN
       IMPORTANT:
       COLORS ARE NOT CHANGED HERE.
       ONLY SIZE / SPACING / LAYOUT CHANGES.
    ======================================================== */

    @media (max-width: 768px) {{

        .main .block-container {{
            padding-top: 1rem;
            padding-bottom: 2rem;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }}


        /* HERO */

        .hero {{
            border-radius: 20px;

            padding:
                28px 22px 26px 22px;

            margin-bottom: 18px;
        }}

        .hero-title {{
            font-size: 38px;

            letter-spacing: -0.8px;
        }}

        .hero-subtitle {{
            font-size: 15px;

            line-height: 1.55;
        }}

        .hero-badge {{
            font-size: 10px;

            padding:
                6px 10px;
        }}

        .hero::after {{
            width: 150px;
            height: 150px;

            right: -60px;
            top: -55px;
        }}


        /* SECTION HEADINGS */

        .section-title {{
            font-size: 21px;

            margin-top: 20px;
        }}

        .section-description {{
            font-size: 13px;
        }}


        /* FEATURE CARDS */

        .feature-card {{
            min-height: auto;

            padding: 17px;

            margin-bottom: 12px;

            border-radius: 16px;
        }}

        .feature-title {{
            font-size: 16px;
        }}

        .feature-text {{
            font-size: 13px;
        }}


        /* AGENT CARDS */

        .agent-card {{
            padding:
                12px 13px;

            margin-bottom: 8px;

            border-radius: 12px;
        }}

        .agent-name {{
            font-size: 13px;
        }}

        .agent-description {{
            font-size: 11px;
        }}


        /* ANSWER */

        .answer-card {{
            padding: 20px;

            border-radius: 18px;
        }}

        .answer-heading {{
            font-size: 19px;
        }}


        /* LOCKED */

        .locked-card {{
            padding: 22px;

            border-radius: 18px;
        }}

        .locked-title {{
            font-size: 20px;
        }}

        .locked-text {{
            font-size: 13px;
        }}

        .price {{
            font-size: 28px;
        }}


        /* PAYMENT */

        .payment-card {{
            padding: 20px;

            border-radius: 18px;
        }}

        .payment-title {{
            font-size: 20px;
        }}


        /* BUTTON */

        .stButton > button {{
            min-height: 46px;

            font-size: 14px;
        }}


        /* INPUTS */

        textarea {{
            min-height: 130px !important;
        }}


        /* STATUS */

        .status-good,
        .status-warning {{
            font-size: 12px;

            padding:
                10px 12px;

            margin-bottom: 8px;
        }}


        /* SOURCE */

        .source-card {{
            padding:
                11px 12px;
        }}

        .source-name {{
            font-size: 12px;
        }}

        .source-page {{
            font-size: 11px;
        }}


        /* PAYMENT IMAGE */

        img {{
            max-width: 100% !important;
            height: auto !important;
        }}


        /* METRICS */

        div[data-testid="stMetric"] {{
            margin-bottom: 8px;
        }}


        /* FOOTER */

        .footer {{
            font-size: 11px;

            line-height: 1.6;

            margin-top: 30px;
        }}


        /* DISCLAIMER */

        .disclaimer {{
            font-size: 11px;

            padding:
                13px 14px;
        }}
    }}


    /* ========================================================
       VERY SMALL PHONES
    ======================================================== */

    @media (max-width: 430px) {{

        .main .block-container {{
            padding-left: 0.6rem;
            padding-right: 0.6rem;
        }}

        .hero {{
            padding:
                24px 18px;
        }}

        .hero-title {{
            font-size: 34px;
        }}

        .hero-subtitle {{
            font-size: 14px;
        }}

        .hero-badge {{
            font-size: 9px;
        }}

        .section-title {{
            font-size: 19px;
        }}

        .feature-card {{
            padding: 15px;
        }}

        .answer-card {{
            padding: 17px;
        }}

        .locked-card {{
            padding: 18px;
        }}

        .payment-card {{
            padding: 17px;
        }}

        .price {{
            font-size: 26px;
        }}
    }}

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# IMPORT TREKTALES CONFIG
# ============================================================

try:

    from src.config import (
        FREE_DAYS,
        PAID_DAYS,
        UNLOCK_PRICE,
        EXPECTED_PAYMENT_RECIPIENT,
    )

except Exception:

    FREE_DAYS = 1
    PAID_DAYS = 2
    UNLOCK_PRICE = 199
    EXPECTED_PAYMENT_RECIPIENT = "ambreen sadia"


# ============================================================
# GROQ API KEY
# ============================================================

def get_groq_api_key():

    try:
        key = st.secrets.get(
            "GROQ_API_KEY",
            "",
        )

    except Exception:
        key = ""

    return str(key).strip()


GROQ_API_KEY = get_groq_api_key()


# ============================================================
# GROQ CLIENT
# ============================================================

def create_groq_client():

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
# HELPERS
# ============================================================

def safe_text(value):

    if value is None:
        return ""

    return str(value).strip()


def display_agent(
    name,
    description,
    number,
):

    st.markdown(
        f"""
        <div class="agent-card">

            <div class="agent-number">
                AGENT {number:02d}
            </div>

            <div class="agent-name">
                {html.escape(name)}
            </div>

            <div class="agent-description">
                {html.escape(description)}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


def normalize_result(result):

    if result is None:
        return ""

    if isinstance(result, str):
        return result.strip()

    for attribute in (
        "raw",
        "output",
        "result",
    ):

        value = getattr(
            result,
            attribute,
            None,
        )

        if value:
            return str(value).strip()

    return str(result).strip()


def load_sources_from_metadata():

    if not METADATA_PATH.exists():
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

        return []

    except Exception:

        return []


# ============================================================
# SESSION STATE
# ============================================================

if "trip_result" not in st.session_state:
    st.session_state.trip_result = None

if "trip_evidence" not in st.session_state:
    st.session_state.trip_evidence = []

if "payment_unlocked" not in st.session_state:
    st.session_state.payment_unlocked = False

if "vision_result" not in st.session_state:
    st.session_state.vision_result = None

if "payment_validation" not in st.session_state:
    st.session_state.payment_validation = None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        f"""
        <div style="
            text-align:center;
            padding:10px 0 22px 0;
        ">

            <div style="
                font-size:45px;
                background:{LIGHT_GREEN};
                width:75px;
                height:75px;
                border-radius:22px;
                margin:auto;
                display:flex;
                align-items:center;
                justify-content:center;
            ">
                🌿
            </div>

            <div class="sidebar-brand-title">
                TrekTales
            </div>

            <div class="sidebar-brand-subtitle">
                AI Multi-Agent Travel Planner
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    st.markdown(
        "### 🤖 Your 8 AI Agents"
    )

    display_agent(
        "Master Orchestrator",
        "Coordinates the complete tourism workflow.",
        1,
    )

    display_agent(
        "Knowledge Agent",
        "Retrieves grounded tourism knowledge.",
        2,
    )

    display_agent(
        "Planner Agent",
        "Builds the day-by-day itinerary.",
        3,
    )

    display_agent(
        "Budget Agent",
        "Organizes estimated travel costs.",
        4,
    )

    display_agent(
        "Safety Agent",
        "Provides evidence-based safety guidance.",
        5,
    )

    display_agent(
        "Summarizer Agent",
        "Creates the final polished response.",
        6,
    )

    display_agent(
        "Payment Agent",
        "Handles the demo unlock state.",
        7,
    )

    display_agent(
        "Vision Agent",
        "Extracts payment information from images.",
        8,
    )

    st.markdown("---")

    st.markdown(
        f"""
        <div class="sidebar-access">

            <div class="sidebar-access-title">
                🔐 Access Model
            </div>

            <div class="sidebar-access-text">
                Day 1 is free.<br>
                Days 2–3 unlock after the
                <b>Rs. {UNLOCK_PRICE}</b>
                demo payment flow.
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
    <div class="hero">

        <div class="hero-badge">
            🌿 GROQ-POWERED • MULTI-AGENT TOURISM AI
        </div>

        <h1 class="hero-title">
            Trek<span>Tales</span>
        </h1>

        <p class="hero-subtitle">
            Plan smarter journeys with a coordinated AI travel team
            for places, itineraries, budgets, food, transport and safety.
        </p>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# FEATURE CARDS
# ============================================================

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.markdown(
        """
        <div class="feature-card">

            <div class="feature-icon">
                🧠
            </div>

            <div class="feature-title">
                Knowledge Grounding
            </div>

            <div class="feature-text">
                Tourism answers are grounded in your supplied
                knowledge base.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


with col2:

    st.markdown(
        """
        <div class="feature-card">

            <div class="feature-icon">
                🗺️
            </div>

            <div class="feature-title">
                Smart Planning
            </div>

            <div class="feature-text">
                Build structured day-by-day travel plans based
                on your preferences.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


with col3:

    st.markdown(
        """
        <div class="feature-card">

            <div class="feature-icon">
                💰
            </div>

            <div class="feature-title">
                Budget + Safety
            </div>

            <div class="feature-text">
                Keep budget planning and safety considerations
                together in one itinerary.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


with col4:

    st.markdown(
        """
        <div class="feature-card">

            <div class="feature-icon">
                📷
            </div>

            <div class="feature-title">
                AI Screenshot Demo
            </div>

            <div class="feature-text">
                Extract payment details from an uploaded
                screenshot for the demo unlock flow.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SYSTEM STATUS
# ============================================================

st.markdown(
    '<div class="section-title">⚙️ System Status</div>',
    unsafe_allow_html=True,
)


status_col1, status_col2, status_col3 = st.columns(3)


with status_col1:

    if GROQ_API_KEY:

        st.markdown(
            '<div class="status-good">● Groq API key loaded</div>',
            unsafe_allow_html=True,
        )

    else:

        st.markdown(
            '<div class="status-warning">● GROQ_API_KEY missing</div>',
            unsafe_allow_html=True,
        )


with status_col2:

    if (
        FAISS_INDEX_PATH.exists()
        and METADATA_PATH.exists()
    ):

        st.markdown(
            '<div class="status-good">● Tourism knowledge base ready</div>',
            unsafe_allow_html=True,
        )

    else:

        st.markdown(
            '<div class="status-warning">● FAISS index not found</div>',
            unsafe_allow_html=True,
        )


with status_col3:

    st.markdown(
        '<div class="status-good">● 8-agent architecture loaded</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# TRIP PLANNER
# ============================================================

st.markdown(
    '<div class="section-title">🧳 Plan Your Journey</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="section-description">
        Tell TrekTales where you want to go and what kind of
        experience you want.
    </div>
    """,
    unsafe_allow_html=True,
)


left, right = st.columns([1.7, 1])


with left:

    user_query = st.text_area(
        "Travel request",
        placeholder=(
            "Example: Plan a family trip to Rawalpindi. "
            "Include places, food, transport, safety and budget."
        ),
        height=160,
        label_visibility="collapsed",
    )


with right:

    duration = st.selectbox(
        "Trip duration",
        options=[1, 2, 3],
        format_func=lambda value:
            f"{value} Day"
            if value == 1
            else f"{value} Days",
    )

    language = st.selectbox(
        "Response language",
        options=[
            "English",
            "Urdu",
            "Roman Urdu",
        ],
    )

    traveler_type = st.selectbox(
        "Traveler type",
        options=[
            "Solo",
            "Couple",
            "Family",
            "Friends",
        ],
    )


# ============================================================
# CREATE PLAN BUTTON
# ============================================================

create_plan = st.button(
    "🌿 Create My TrekTales Plan",
    use_container_width=True,
)


if create_plan:

    if not user_query.strip():

        st.warning(
            "Please enter your travel request first."
        )

        st.stop()


    if not GROQ_API_KEY:

        st.error(
            "GROQ_API_KEY is missing. Add your Groq key in "
            "Streamlit Cloud → Settings → Secrets."
        )

        st.stop()


    if (
        not FAISS_INDEX_PATH.exists()
        or not METADATA_PATH.exists()
    ):

        st.error(
            "The tourism FAISS index was not found. "
            "Run ingest.py first and upload the generated "
            "data/faiss_index files to your repository."
        )

        st.stop()


    try:

        with st.status(
            "🌿 TrekTales agents are working...",
            expanded=True,
        ) as status:

            # =================================================
            # RETRIEVER
            # =================================================

            st.write(
                "🔎 Knowledge Agent: searching tourism evidence..."
            )

            from src.retriever import HybridRetriever

            retriever = HybridRetriever()

            evidence = retriever.search(
                user_query,
                top_k=6,
            )

            st.session_state.trip_evidence = evidence


            if not evidence:

                status.update(
                    label="No tourism evidence found",
                    state="error",
                )

                st.error(
                    "No relevant information was found in the "
                    "tourism knowledge base. TrekTales will not "
                    "invent tourism facts."
                )

                st.stop()


            # =================================================
            # CREW
            # =================================================

            st.write(
                "🤖 Master Orchestrator: coordinating agents..."
            )

            from src.crew import TrekTalesCrew

            crew = TrekTalesCrew()

            st.write(
                "🧠 Knowledge Agent: grounding the request..."
            )

            st.write(
                "🗺️ Planner Agent: building itinerary..."
            )

            st.write(
                "💰 Budget Agent: preparing cost guidance..."
            )

            st.write(
                "🛡️ Safety Agent: checking safety evidence..."
            )

            st.write(
                "✍️ Summarizer Agent: preparing final answer..."
            )


            result = crew.run(
                user_query=user_query,
                evidence=evidence,
                duration=duration,
                language=language,
                traveler_type=traveler_type,
            )


            answer = normalize_result(result)


            if not answer:

                raise RuntimeError(
                    "The tourism crew returned an empty response."
                )


            st.session_state.trip_result = answer


            status.update(
                label="🌿 TrekTales plan created",
                state="complete",
            )


    except ImportError as error:

        st.error(
            "A TrekTales module could not be imported."
        )

        st.code(str(error))


    except Exception as error:

        st.error(
            "TrekTales could not complete the trip-planning request."
        )

        st.code(str(error))


# ============================================================
# DISPLAY PLAN
# ============================================================

if st.session_state.trip_result:

    st.markdown(
        """
        <div class="answer-card">

            <div class="answer-heading">
                🌿 Your TrekTales Travel Plan
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        st.session_state.trip_result
    )


# ============================================================
# SOURCES
# ============================================================

if st.session_state.trip_evidence:

    st.markdown(
        '<div class="section-title">📚 Knowledge Sources</div>',
        unsafe_allow_html=True,
    )

    seen = set()


    for item in st.session_state.trip_evidence:

        if not isinstance(item, dict):
            continue


        metadata = item.get(
            "metadata",
            item,
        )


        source = safe_text(
            metadata.get(
                "source",
                "Unknown source",
            )
        )


        page = safe_text(
            metadata.get(
                "page",
                "N/A",
            )
        )


        department = safe_text(
            metadata.get(
                "department",
                "Tourism",
            )
        )


        key = (
            source.lower(),
            page.lower(),
            department.lower(),
        )


        if key in seen:
            continue


        seen.add(key)


        st.markdown(
            f"""
            <div class="source-card">

                <div class="source-name">
                    📄 {html.escape(source)}
                </div>

                <div class="source-page">
                    Page: {html.escape(page)}
                    &nbsp; • &nbsp;
                    Department: {html.escape(department)}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# PREMIUM ACCESS
# ============================================================

if duration >= 2:

    st.markdown(
        """
        <div class="locked-card">

            <div class="locked-title">
                🔐 Unlock Your Extended Journey
            </div>

            <p class="locked-text">
                Day 1 is available for free. Days 2 and 3 are
                protected by the TrekTales demo payment flow.
            </p>

            <div class="price">
                Rs. 199
            </div>

            <p class="locked-text">
                Upload your payment screenshot below after
                completing the demo payment.
            </p>

        </div>
        """,
        unsafe_allow_html=True,
    )


    st.markdown(
        """
        <div class="payment-card">

            <div class="payment-title">
                💳 TrekTales Premium Access
            </div>

            <p class="payment-note">
                Scan the JazzCash QR and upload the resulting
                payment screenshot for the AI extraction demo.
            </p>

        </div>
        """,
        unsafe_allow_html=True,
    )


    payment_col1, payment_col2 = st.columns(2)


    with payment_col1:

        if QR_PATH.exists():

            st.image(
                str(QR_PATH),
                caption="TrekTales Demo Payment — Rs. 199",
                width=300,
            )

        else:

            st.warning(
                "JazzCash QR image was not found at "
                "assets/jazzcash_qr.png."
            )


    with payment_col2:

        uploaded_payment = st.file_uploader(
            "Upload payment screenshot",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp",
            ],
            help=(
                "Upload a clear screenshot containing the "
                "recipient, amount and payment status."
            ),
        )


        verify_payment = st.button(
            "🔍 Analyze Payment Screenshot",
            use_container_width=True,
        )


        if verify_payment:

            if uploaded_payment is None:

                st.warning(
                    "Please upload a payment screenshot first."
                )

            else:

                try:

                    file_size_mb = (
                        uploaded_payment.size
                        / (1024 * 1024)
                    )


                    if file_size_mb > 20:

                        st.error(
                            "The image is larger than 20 MB."
                        )

                    else:

                        with st.spinner(
                            "Vision Agent is extracting payment details..."
                        ):

                            from src.vision import (
                                analyze_payment_image
                            )

                            image_bytes = (
                                uploaded_payment.getvalue()
                            )


                            vision_result = (
                                analyze_payment_image(
                                    image_bytes
                                )
                            )


                            st.session_state.vision_result = (
                                vision_result
                            )


                        st.success(
                            "Vision Agent completed screenshot extraction."
                        )


                except Exception as error:

                    st.error(
                        "The payment screenshot could not be analyzed."
                    )

                    st.code(str(error))


# ============================================================
# DISPLAY VISION RESULT
# ============================================================

if st.session_state.vision_result:

    result = st.session_state.vision_result


    recipient = safe_text(
        result.get(
            "recipient",
            "",
        )
    )


    amount = result.get(
        "amount"
    )


    payment_status = safe_text(
        result.get(
            "status",
            "",
        )
    )


    confidence = result.get(
        "confidence",
        0,
    )


    st.markdown(
        '<div class="section-title">📷 AI Screenshot Extraction</div>',
        unsafe_allow_html=True,
    )


    v1, v2, v3, v4 = st.columns(4)


    with v1:

        st.metric(
            "Recipient",
            recipient or "Not detected",
        )


    with v2:

        st.metric(
            "Amount",
            f"Rs. {amount}"
            if amount is not None
            else "Not detected",
        )


    with v3:

        st.metric(
            "Status",
            payment_status or "Not detected",
        )


    with v4:

        st.metric(
            "Confidence",
            f"{confidence}%",
        )


# ============================================================
# PAYMENT VALIDATION
# ============================================================

if st.session_state.vision_result:

    validate_payment_button = st.button(
        "🔐 Validate Demo Payment",
        use_container_width=True,
    )


    if validate_payment_button:

        try:

            from src.payment import validate_payment


            validation = validate_payment(
                st.session_state.vision_result
            )


            st.session_state.payment_validation = (
                validation
            )


            approved = bool(
                validation.get(
                    "approved",
                    False,
                )
            )


            if approved:

                st.session_state.payment_unlocked = True


                st.success(
                    "Demo payment conditions passed. "
                    "Days 2–3 are unlocked."
                )


            else:

                st.session_state.payment_unlocked = False


                st.warning(
                    "The extracted screenshot information "
                    "did not satisfy the demo payment rules."
                )


        except Exception as error:

            st.error(
                "Payment validation failed."
            )

            st.code(str(error))


# ============================================================
# UNLOCKED PREMIUM CONTENT
# ============================================================

if st.session_state.payment_unlocked:

    st.markdown(
        """
        <div class="answer-card">

            <div class="answer-heading">
                🔓 Days 2–3 Unlocked
            </div>

            <p>
                Your TrekTales demo access has been unlocked.
                The extended itinerary can now be displayed.
            </p>

        </div>
        """,
        unsafe_allow_html=True,
    )


    st.info(
        "Payment verification note: this is a demo screenshot "
        "verification flow. AI extracts the screenshot fields, "
        "while deterministic Python rules decide whether the "
        "demo unlock conditions are satisfied. A real production "
        "payment system should verify transactions through the "
        "payment provider's backend/API."
    )


# ============================================================
# DISCLAIMER
# ============================================================

st.markdown("---")


st.markdown(
    """
    <div class="disclaimer">

        <b>Important:</b>
        TrekTales provides tourism planning information based
        on the application's supplied knowledge base.
        Prices, availability and travel conditions may change.
        The payment screenshot feature is a demonstration and
        does not independently prove that a real payment occurred.

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

        🌿 TrekTales AI
        &nbsp;•&nbsp;
        Multi-Agent Tourism Assistant
        &nbsp;•&nbsp;
        Powered by Groq

    </div>
    """,
    unsafe_allow_html=True,
)
