from pathlib import Path
import os

import streamlit as st


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

SRC_DIR = Path(__file__).resolve().parent
ROOT_DIR = SRC_DIR.parent

KNOWLEDGE_BASE_DIR = ROOT_DIR / "tourism_knowledge_base"
DATA_DIR = ROOT_DIR / "data"
FAISS_DIR = DATA_DIR / "faiss_index"
ASSETS_DIR = ROOT_DIR / "assets"

FAISS_INDEX_PATH = FAISS_DIR / "index.faiss"
METADATA_PATH = FAISS_DIR / "metadata.json"

QR_PATH = ASSETS_DIR / "jazzcash_qr.png"


# ---------------------------------------------------------
# APP
# ---------------------------------------------------------

APP_NAME = "TrekTales"
APP_TAGLINE = "Your AI Multi-Agent Travel Planner"

FREE_DAYS = 1
PAID_DAYS = 2
UNLOCK_PRICE = 199

EXPECTED_PAYMENT_RECIPIENT = "ambreen sadia"
EXPECTED_PAYMENT_STATUS = "sent"


# ---------------------------------------------------------
# XAI / GROK
# ---------------------------------------------------------

def get_secret(name: str, default: str = "") -> str:
    """
    Safely read a Streamlit secret.
    Falls back to environment variables for local development.
    """
    try:
        value = st.secrets.get(name, None)
    except Exception:
        value = None

    if value is not None:
        return str(value).strip()

    return os.getenv(name, default).strip()


XAI_API_KEY = get_secret("XAI_API_KEY")

# Current Grok model defaults.
# They can be overridden entirely from Streamlit Secrets.
TEXT_MODEL = get_secret("TEXT_MODEL", "grok-4.6")
VISION_MODEL = get_secret("VISION_MODEL", "grok-4.6")

XAI_BASE_URL = "https://api.x.ai/v1"


# ---------------------------------------------------------
# RAG
# ---------------------------------------------------------

EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

TOP_K_FAISS = 8
TOP_K_BM25 = 8
TOP_K_FINAL = 6

# Cross encoder is deliberately optional.
# The application falls back safely if it cannot load.
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


# ---------------------------------------------------------
# SAFETY
# ---------------------------------------------------------

MAX_PAYMENT_IMAGE_MB = 20


def validate_configuration() -> list[str]:
    """
    Return configuration problems without crashing the application.
    """
    problems = []

    if not XAI_API_KEY:
        problems.append(
            "XAI_API_KEY is missing from Streamlit Secrets."
        )

    if not KNOWLEDGE_BASE_DIR.exists():
        problems.append(
            f"Knowledge-base directory does not exist: {KNOWLEDGE_BASE_DIR}"
        )

    return problems
