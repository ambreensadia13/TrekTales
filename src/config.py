from pathlib import Path
import os

import streamlit as st


# ============================================================
# PROJECT PATHS
# ============================================================

SRC_DIR = Path(__file__).resolve().parent
ROOT_DIR = SRC_DIR.parent


# ============================================================
# GROQ CONFIGURATION
# ============================================================

def get_secret(name, default=""):
    """
    Safely read a value from Streamlit Secrets first,
    then environment variables.
    """

    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""

    if value:
        return str(value).strip()

    value = os.getenv(name, default)

    if value:
        return str(value).strip()

    return default


GROQ_API_KEY = get_secret(
    "GROQ_API_KEY"
)


GROQ_MODEL = get_secret(
    "GROQ_MODEL",
    "openai/gpt-oss-120b",
)


GROQ_VISION_MODEL = get_secret(
    "GROQ_VISION_MODEL",
    "meta-llama/llama-4-scout-17b-16e-instruct",
)


GROQ_BASE_URL = get_secret(
    "GROQ_BASE_URL",
    "https://api.groq.com/openai/v1",
)


# ============================================================
# TRIP ACCESS
# ============================================================

FREE_DAYS = 1

PAID_DAYS = 2

MAX_TRIP_DAYS = FREE_DAYS + PAID_DAYS

UNLOCK_PRICE = 199


# ============================================================
# DEMO PAYMENT
# ============================================================

EXPECTED_PAYMENT_RECIPIENT = get_secret(
    "EXPECTED_PAYMENT_RECIPIENT",
    "TrekTales",
)


# ============================================================
# FAISS PATHS
# ============================================================

# Primary/current structure:
#
# faiss_db/
#   index.faiss
#   metadata.json
#   config.json

PRIMARY_FAISS_DIR = ROOT_DIR / "faiss_db"


# Compatibility with the previous structure:
#
# data/faiss_index/
#   index.faiss
#   metadata.json
#   config.json

LEGACY_FAISS_DIR = (
    ROOT_DIR
    / "data"
    / "faiss_index"
)


def choose_faiss_directory():
    """
    Prefer the root-level faiss_db folder.

    If it is not available, support the older
    data/faiss_index structure.
    """

    primary_index = (
        PRIMARY_FAISS_DIR
        / "index.faiss"
    )

    primary_metadata = (
        PRIMARY_FAISS_DIR
        / "metadata.json"
    )

    if (
        primary_index.exists()
        and primary_metadata.exists()
    ):
        return PRIMARY_FAISS_DIR

    legacy_index = (
        LEGACY_FAISS_DIR
        / "index.faiss"
    )

    legacy_metadata = (
        LEGACY_FAISS_DIR
        / "metadata.json"
    )

    if (
        legacy_index.exists()
        and legacy_metadata.exists()
    ):
        return LEGACY_FAISS_DIR

    return PRIMARY_FAISS_DIR


FAISS_DIR = choose_faiss_directory()

FAISS_INDEX_PATH = (
    FAISS_DIR
    / "index.faiss"
)

METADATA_PATH = (
    FAISS_DIR
    / "metadata.json"
)

CONFIG_PATH = (
    FAISS_DIR
    / "config.json"
)


# ============================================================
# EMBEDDING CONFIG
# ============================================================

DEFAULT_EMBEDDING_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)


# ============================================================
# RAG CONFIG
# ============================================================

DEFAULT_TOP_K = 8

KEYWORD_WEIGHT = 0.25

SEMANTIC_WEIGHT = 0.75


# ============================================================
# VALIDATION
# ============================================================

def validate_configuration():
    """
    Return human-readable configuration problems.
    """

    errors = []

    if not GROQ_API_KEY:
        errors.append(
            "GROQ_API_KEY is missing."
        )

    if not FAISS_INDEX_PATH.exists():
        errors.append(
            f"FAISS index not found: {FAISS_INDEX_PATH}"
        )

    if not METADATA_PATH.exists():
        errors.append(
            f"Metadata file not found: {METADATA_PATH}"
        )

    return errors
