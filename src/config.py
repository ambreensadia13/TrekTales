from pathlib import Path
import os

import streamlit as st


# ============================================================
# TREKTALES DIRECTORIES
# ============================================================

SRC_DIR = Path(__file__).resolve().parent
ROOT_DIR = SRC_DIR.parent

KNOWLEDGE_BASE_DIR = ROOT_DIR / "tourism_knowledge_base"

DATA_DIR = ROOT_DIR / "data"
FAISS_DIR = DATA_DIR / "faiss_index"

ASSETS_DIR = ROOT_DIR / "assets"

FAISS_INDEX_PATH = FAISS_DIR / "index.faiss"
METADATA_PATH = FAISS_DIR / "metadata.json"

QR_PATH = ASSETS_DIR / "jazzcash_qr.png"


# ============================================================
# APPLICATION INFORMATION
# ============================================================

APP_NAME = "TrekTales"

APP_TAGLINE = "Your AI Multi-Agent Travel Planner"

APP_VERSION = "1.0.0"


# ============================================================
# TREKTALES THEME COLORS
# ============================================================

PRIMARY_RED = "#DA2C38"

DEEP_GREEN = "#226F54"

LIGHT_GREEN = "#87C38F"

CREAM = "#F4F0BB"

DARK_BROWN = "#43291F"

WHITE = "#FFFFFF"

BLACK = "#111111"

DARK_GREEN = "#174936"


# ============================================================
# PAYMENT / ACCESS SETTINGS
# ============================================================

FREE_DAYS = 1

PAID_DAYS = 2

UNLOCK_PRICE = 199

EXPECTED_PAYMENT_RECIPIENT = "ambreen sadia"

EXPECTED_PAYMENT_STATUS = "sent"


# ============================================================
# GROQ API CONFIGURATION
# ============================================================

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


def get_secret(name: str, default: str = "") -> str:
    """
    Safely read a value from Streamlit Secrets.

    Falls back to an environment variable if the
    Streamlit secret is unavailable.
    """

    try:
        value = st.secrets.get(name, None)
    except Exception:
        value = None

    if value is not None:
        return str(value).strip()

    return os.getenv(name, default).strip()


# ============================================================
# GROQ API KEY
# ============================================================

GROQ_API_KEY = get_secret("GROQ_API_KEY")


# ============================================================
# GROQ MODEL
# ============================================================

GROQ_MODEL = get_secret(
    "GROQ_MODEL",
    "openai/gpt-oss-120b",
)


# ============================================================
# AI SETTINGS
# ============================================================

TEMPERATURE = 0.2

MAX_OUTPUT_TOKENS = 1500


# ============================================================
# RAG SETTINGS
# ============================================================

EMBEDDING_MODEL = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)

CHUNK_SIZE = 1000

CHUNK_OVERLAP = 150

TOP_K_FAISS = 8

TOP_K_BM25 = 8

TOP_K_FINAL = 6


# ============================================================
# OPTIONAL RERANKER
# ============================================================

RERANKER_MODEL = (
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)


# ============================================================
# PAYMENT IMAGE SETTINGS
# ============================================================

MAX_PAYMENT_IMAGE_MB = 20


# ============================================================
# SUPPORTED LANGUAGES
# ============================================================

SUPPORTED_LANGUAGES = [
    "English",
    "Urdu",
    "Roman Urdu",
]


# ============================================================
# TRAVELER TYPES
# ============================================================

TRAVELER_TYPES = [
    "Solo",
    "Couple",
    "Family",
    "Friends",
]


# ============================================================
# TRIP DURATIONS
# ============================================================

SUPPORTED_TRIP_DURATIONS = [
    1,
    2,
    3,
]


# ============================================================
# 8 TREKTALES AGENTS
# ============================================================

AGENT_NAMES = [
    "Master Orchestrator",
    "Knowledge Agent",
    "Planner Agent",
    "Budget Agent",
    "Safety Agent",
    "Summarizer Agent",
    "Payment Agent",
    "Vision Agent",
]


# ============================================================
# CONFIGURATION VALIDATION
# ============================================================

def validate_configuration() -> list[str]:
    """
    Check important TrekTales configuration and files.

    Returns an empty list when no problems are detected.
    """

    problems: list[str] = []

    # --------------------------------------------------------
    # GROQ API KEY
    # --------------------------------------------------------

    if not GROQ_API_KEY:

        problems.append(
            "GROQ_API_KEY is missing from Streamlit Secrets."
        )

    # --------------------------------------------------------
    # KNOWLEDGE BASE
    # --------------------------------------------------------

    if not KNOWLEDGE_BASE_DIR.exists():

        problems.append(
            "The tourism_knowledge_base directory was not found."
        )

    # --------------------------------------------------------
    # FAISS DIRECTORY
    # --------------------------------------------------------

    if not FAISS_DIR.exists():

        problems.append(
            "The data/faiss_index directory was not found."
        )

    # --------------------------------------------------------
    # FAISS INDEX
    # --------------------------------------------------------

    if not FAISS_INDEX_PATH.exists():

        problems.append(
            "FAISS index file is missing: "
            "data/faiss_index/index.faiss"
        )

    # --------------------------------------------------------
    # METADATA
    # --------------------------------------------------------

    if not METADATA_PATH.exists():

        problems.append(
            "FAISS metadata file is missing: "
            "data/faiss_index/metadata.json"
        )

    return problems


# ============================================================
# CREATE REQUIRED DIRECTORIES
# ============================================================

def ensure_directories() -> None:
    """
    Create required local directories.

    This does not generate the knowledge base or FAISS files.
    """

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    FAISS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    ASSETS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# CONFIGURATION SUMMARY
# ============================================================

CONFIG = {
    "app_name": APP_NAME,
    "app_version": APP_VERSION,
    "groq_base_url": GROQ_BASE_URL,
    "groq_model": GROQ_MODEL,
    "free_days": FREE_DAYS,
    "paid_days": PAID_DAYS,
    "unlock_price": UNLOCK_PRICE,
    "embedding_model": EMBEDDING_MODEL,
    "chunk_size": CHUNK_SIZE,
    "chunk_overlap": CHUNK_OVERLAP,
    "top_k_faiss": TOP_K_FAISS,
    "top_k_bm25": TOP_K_BM25,
    "top_k_final": TOP_K_FINAL,
}
