from pathlib import Path
import json
import streamlit as st


# ============================================================
# ROOT
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[1]

SRC_DIR = ROOT_DIR / "src"

ASSETS_DIR = ROOT_DIR / "assets"

KNOWLEDGE_BASE_DIR = (
    ROOT_DIR / "tourism_knowledge_base"
)

FAISS_DIR = (
    ROOT_DIR / "faiss_db"
)


# ============================================================
# FAISS
# ============================================================

FAISS_INDEX_PATH = (
    FAISS_DIR / "index.faiss"
)

METADATA_PATH = (
    FAISS_DIR / "metadata.json"
)

FAISS_CONFIG_PATH = (
    FAISS_DIR / "config.json"
)


# ============================================================
# PAYMENT
# ============================================================

PAYMENT_QR_PATH = (
    ASSETS_DIR / "jazzcash_qr.jpg"
)

FREE_DAYS = 1

PAID_DAYS = 2

MAX_TRIP_DAYS = 3

UNLOCK_PRICE = 199


# ============================================================
# SECRETS
# ============================================================

def get_secret(
    name,
    default=None
):

    try:

        value = st.secrets.get(
            name,
            default
        )

        if value is None:
            return default

        return value

    except Exception:

        return default


# ============================================================
# GROQ
# ============================================================

GROQ_API_KEY = get_secret(
    "GROQ_API_KEY",
    ""
)

GROQ_BASE_URL = get_secret(
    "GROQ_BASE_URL",
    "https://api.groq.com/openai/v1"
)

GROQ_MODEL = get_secret(
    "GROQ_MODEL",
    "openai/gpt-oss-120b"
)

GROQ_VISION_MODEL = get_secret(
    "GROQ_VISION_MODEL",
    "qwen/qwen3.8-27b"
)


# ============================================================
# PAYMENT
# ============================================================

EXPECTED_PAYMENT_RECIPIENT = get_secret(
    "EXPECTED_PAYMENT_RECIPIENT",
    "TrekTales"
)


# ============================================================
# RAG
# ============================================================

DEFAULT_EMBEDDING_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)

DEFAULT_CHUNK_SIZE = 900

DEFAULT_CHUNK_OVERLAP = 150

DEFAULT_TOP_K = 6

SEMANTIC_WEIGHT = 0.75

KEYWORD_WEIGHT = 0.25


# ============================================================
# LOAD FAISS CONFIG
# ============================================================

def load_faiss_config():

    defaults = {
        "embedding_model":
            DEFAULT_EMBEDDING_MODEL,

        "chunk_size":
            DEFAULT_CHUNK_SIZE,

        "chunk_overlap":
            DEFAULT_CHUNK_OVERLAP,

        "metric":
            "cosine",

        "index":
            "IndexFlatIP"
    }

    if not FAISS_CONFIG_PATH.exists():

        return defaults

    try:

        with open(
            FAISS_CONFIG_PATH,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        return {
            "embedding_model":
                data.get(
                    "embedding_model",
                    DEFAULT_EMBEDDING_MODEL
                ),

            "chunk_size":
                data.get(
                    "chunk_size",
                    DEFAULT_CHUNK_SIZE
                ),

            "chunk_overlap":
                data.get(
                    "chunk_overlap",
                    DEFAULT_CHUNK_OVERLAP
                ),

            "metric":
                data.get(
                    "metric",
                    data.get(
                        "similarity",
                        "cosine"
                    )
                ),

            "index":
                data.get(
                    "index",
                    "IndexFlatIP"
                )
        }

    except Exception:

        return defaults


FAISS_CONFIG = load_faiss_config()


EMBEDDING_MODEL = (
    FAISS_CONFIG["embedding_model"]
)

CHUNK_SIZE = (
    FAISS_CONFIG["chunk_size"]
)

CHUNK_OVERLAP = (
    FAISS_CONFIG["chunk_overlap"]
)

FAISS_METRIC = (
    FAISS_CONFIG["metric"]
)

TOP_K = DEFAULT_TOP_K

MIN_TRIP_DAYS = 1


# ============================================================
# FILE STATUS
# ============================================================

def faiss_files_exist():

    return (
        FAISS_INDEX_PATH.exists()
        and METADATA_PATH.exists()
        and FAISS_CONFIG_PATH.exists()
    )


def get_faiss_status():

    return {
        "index":
            FAISS_INDEX_PATH.exists(),

        "metadata":
            METADATA_PATH.exists(),

        "config":
            FAISS_CONFIG_PATH.exists(),

        "ready":
            faiss_files_exist()
    }


# ============================================================
# DAYS
# ============================================================

def validate_trip_days(days):

    try:
        days = int(days)

    except Exception:
        days = 1

    return max(
        MIN_TRIP_DAYS,
        min(
            days,
            MAX_TRIP_DAYS
        )
    )


def get_accessible_days(
    requested_days,
    payment_verified=False
):

    requested_days = validate_trip_days(
        requested_days
    )

    if requested_days <= FREE_DAYS:
        return requested_days

    if payment_verified:
        return requested_days

    return FREE_DAYS


def payment_required(
    requested_days,
    payment_verified=False
):

    requested_days = validate_trip_days(
        requested_days
    )

    return (
        requested_days > FREE_DAYS
        and not payment_verified
    )
