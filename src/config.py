from pathlib import Path
import json

import streamlit as st


# ============================================================
# PROJECT PATHS
# ============================================================
# This file is:
#
# TrekTales/
# └── src/
#     └── config.py
#
# Therefore:
# parents[0] = src
# parents[1] = TrekTales project root
#
# This is CORRECT for src/config.py.
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[1]

SRC_DIR = ROOT_DIR / "src"
ASSETS_DIR = ROOT_DIR / "assets"

KNOWLEDGE_BASE_DIR = (
    ROOT_DIR / "tourism_knowledge_base"
)

FAISS_DIR = ROOT_DIR / "faiss_db"

FAISS_INDEX_PATH = (
    FAISS_DIR / "index.faiss"
)

METADATA_PATH = (
    FAISS_DIR / "metadata.json"
)

FAISS_CONFIG_PATH = (
    FAISS_DIR / "config.json"
)

PAYMENT_QR_PATH = (
    ASSETS_DIR / "jazzcash_qr.jpg"
)


# ============================================================
# TREKTALES ACCESS SETTINGS
# ============================================================

# Day 1 is free.
FREE_DAYS = 1

# Days 2 and 3 require payment.
PAID_DAYS = 2

# Maximum supported itinerary length.
MAX_TRIP_DAYS = 3

# Minimum supported itinerary length.
MIN_TRIP_DAYS = 1

# Premium unlock price.
UNLOCK_PRICE = 199


# ============================================================
# PAYMENT SETTINGS
# ============================================================
# IMPORTANT:
#
# This is a DEMO payment verification workflow.
# It does NOT connect to JazzCash's payment API.
#
# The uploaded screenshot is analyzed to extract information.
# The extracted information is then checked deterministically
# by src/payment.py.
#
# Change this value to the exact recipient/account identifier
# shown in the payment screenshot you want TrekTales to accept.
#
# It can also be supplied through Streamlit Secrets:
#
# EXPECTED_PAYMENT_RECIPIENT = "your-recipient"
#
# If no secret is supplied, the default below is used.
# ============================================================

EXPECTED_PAYMENT_RECIPIENT = st.secrets.get(
    "EXPECTED_PAYMENT_RECIPIENT",
    "TrekTales",
)


# ============================================================
# GROQ SETTINGS
# ============================================================
# TrekTales uses GROQ only.
#
# No OpenAI API key is required.
# No xAI API key is required.
#
# GROQ_API_KEY must be added to:
#
# Streamlit Cloud
# → App settings
# → Secrets
#
# Example:
#
# GROQ_API_KEY = "gsk_..."
#
# Optional:
#
# GROQ_MODEL = "openai/gpt-oss-120b"
# GROQ_VISION_MODEL = "qwen/qwen3.6-27b"
# ============================================================

def get_secret(name: str, default=None):
    """
    Safely retrieve a value from Streamlit Secrets.

    Returning a default instead of crashing during import makes
    the application easier to diagnose when a secret is missing.
    """

    try:
        value = st.secrets.get(
            name,
            default,
        )
    except Exception:
        value = default

    if value is None:
        return default

    return value


GROQ_API_KEY = get_secret(
    "GROQ_API_KEY",
    "",
)


# Groq's OpenAI-compatible endpoint.
#
# This is used by the current src/crew.py and src/vision.py.
GROQ_BASE_URL = get_secret(
    "GROQ_BASE_URL",
    "https://api.groq.com/openai/v1",
)


# Main TrekTales text-generation model.
GROQ_MODEL = get_secret(
    "GROQ_MODEL",
    "openai/gpt-oss-120b",
)


# Vision model used for extracting visible information from
# uploaded payment screenshots.
#
# This can be overridden through Streamlit Secrets.
GROQ_VISION_MODEL = get_secret(
    "GROQ_VISION_MODEL",
    "qwen/qwen3.6-27b",
)


# ============================================================
# RAG / EMBEDDING SETTINGS
# ============================================================

# Safe fallback only.
#
# The actual model used by the existing FAISS database is loaded
# from faiss_db/config.json whenever possible.
DEFAULT_EMBEDDING_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)


# These values are used by ingest.py as defaults if required.
DEFAULT_CHUNK_SIZE = 900

DEFAULT_CHUNK_OVERLAP = 150


# Default number of retrieved records.
DEFAULT_TOP_K = 6


# Public aliases used by the rest of the application.
TOP_K = DEFAULT_TOP_K


# ============================================================
# HYBRID RETRIEVAL WEIGHTS
# ============================================================
# The current src/retriever.py imports these two constants.
#
# Semantic retrieval is the primary signal.
# Keyword matching provides additional support for exact terms.
#
# The two values sum to 1.0.
# ============================================================

SEMANTIC_WEIGHT = 0.75

KEYWORD_WEIGHT = 0.25


# ============================================================
# FAISS CONFIGURATION
# ============================================================

def _safe_number(
    value,
    default,
    minimum=None,
):
    """
    Safely convert a configuration value to a number.
    """

    try:
        number = int(value)

        if minimum is not None:
            number = max(
                minimum,
                number,
            )

        return number

    except (
        TypeError,
        ValueError,
    ):
        return default


def load_faiss_config() -> dict:
    """
    Load the configuration used to create the existing FAISS
    database.

    The embedding model stored in config.json is especially
    important because the query embedding model must match the
    model used to create the FAISS index.
    """

    defaults = {
        "embedding_model": DEFAULT_EMBEDDING_MODEL,
        "chunk_size": DEFAULT_CHUNK_SIZE,
        "chunk_overlap": DEFAULT_CHUNK_OVERLAP,
        "metric": "cosine",
    }

    if not FAISS_CONFIG_PATH.exists():
        return defaults

    try:
        with open(
            FAISS_CONFIG_PATH,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return defaults

        embedding_model = (
            data.get("embedding_model")
            or data.get("embedding_model_name")
            or DEFAULT_EMBEDDING_MODEL
        )

        chunk_size = _safe_number(
            data.get(
                "chunk_size",
                DEFAULT_CHUNK_SIZE,
            ),
            DEFAULT_CHUNK_SIZE,
            minimum=1,
        )

        chunk_overlap = _safe_number(
            data.get(
                "chunk_overlap",
                DEFAULT_CHUNK_OVERLAP,
            ),
            DEFAULT_CHUNK_OVERLAP,
            minimum=0,
        )

        metric = str(
            data.get(
                "metric",
                "cosine",
            )
        ).strip().lower()

        if not metric:
            metric = "cosine"

        return {
            "embedding_model": str(
                embedding_model
            ).strip(),
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "metric": metric,
        }

    except (
        OSError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ):
        return defaults


FAISS_CONFIG = load_faiss_config()


# ============================================================
# ACTIVE RAG CONFIGURATION
# ============================================================

# IMPORTANT:
# Use the model stored in the existing FAISS config whenever
# possible. Do NOT blindly replace it with another model.
EMBEDDING_MODEL = FAISS_CONFIG[
    "embedding_model"
]

CHUNK_SIZE = FAISS_CONFIG[
    "chunk_size"
]

CHUNK_OVERLAP = FAISS_CONFIG[
    "chunk_overlap"
]

FAISS_METRIC = FAISS_CONFIG[
    "metric"
]


# ============================================================
# FAISS STATUS HELPERS
# ============================================================

def faiss_files_exist() -> bool:
    """
    Return True only when all required FAISS files exist.
    """

    return (
        FAISS_INDEX_PATH.is_file()
        and METADATA_PATH.is_file()
        and FAISS_CONFIG_PATH.is_file()
    )


def get_faiss_status() -> dict:
    """
    Return detailed FAISS database status.

    Useful for displaying diagnostics inside Streamlit.
    """

    return {
        "directory": str(FAISS_DIR),
        "index": FAISS_INDEX_PATH.is_file(),
        "metadata": METADATA_PATH.is_file(),
        "config": FAISS_CONFIG_PATH.is_file(),
        "ready": faiss_files_exist(),
    }


# ============================================================
# PROJECT RESOURCE STATUS
# ============================================================

def get_project_status() -> dict:
    """
    Return the status of important TrekTales resources.
    """

    return {
        "root": ROOT_DIR.exists(),
        "assets": ASSETS_DIR.exists(),
        "knowledge_base": KNOWLEDGE_BASE_DIR.exists(),
        "faiss_directory": FAISS_DIR.exists(),
        "faiss_ready": faiss_files_exist(),
        "payment_qr": PAYMENT_QR_PATH.is_file(),
        "groq_key_configured": bool(
            GROQ_API_KEY
        ),
    }


# ============================================================
# TRIP-DAY VALIDATION
# ============================================================

def validate_trip_days(days: int) -> int:
    """
    Normalize and constrain the requested number of trip days.

    TrekTales supports exactly:
        1 day
        2 days
        3 days

    The returned value is always within those limits.
    """

    try:
        requested_days = int(days)

    except (
        TypeError,
        ValueError,
    ):
        requested_days = MIN_TRIP_DAYS

    return max(
        MIN_TRIP_DAYS,
        min(
            requested_days,
            MAX_TRIP_DAYS,
        ),
    )


# ============================================================
# ACCESS CONTROL
# ============================================================

def get_accessible_days(
    requested_days: int,
    payment_verified: bool = False,
) -> int:
    """
    Determine how many days can actually be generated.

    Rules:

    1 day:
        Free.

    2 or 3 days:
        Payment required.

    Verified payment:
        Full requested itinerary becomes accessible.
    """

    requested_days = validate_trip_days(
        requested_days
    )

    if requested_days <= FREE_DAYS:
        return requested_days

    if payment_verified:
        return requested_days

    return FREE_DAYS


def payment_required(
    requested_days: int,
    payment_verified: bool = False,
) -> bool:
    """
    Return True when the requested itinerary requires payment.
    """

    requested_days = validate_trip_days(
        requested_days
    )

    return (
        requested_days > FREE_DAYS
        and not payment_verified
    )


# ============================================================
# ACCESS DESCRIPTION
# ============================================================

def get_access_message(
    requested_days: int,
    payment_verified: bool = False,
) -> str:
    """
    Return a user-friendly description of the current
    itinerary access state.
    """

    requested_days = validate_trip_days(
        requested_days
    )

    if requested_days <= FREE_DAYS:
        return (
            "Day 1 is available for free."
        )

    if payment_verified:
        return (
            f"All {requested_days} requested "
            f"days are unlocked."
        )

    return (
        "Day 1 is free. "
        f"Days 2–{requested_days} require "
        f"payment of Rs. {UNLOCK_PRICE}."
    )


# ============================================================
# CONFIGURATION SUMMARY
# ============================================================

def get_config_summary() -> dict:
    """
    Return a safe configuration summary.

    The actual API key is intentionally NOT returned.
    """

    return {
        "root_dir": str(ROOT_DIR),
        "faiss_dir": str(FAISS_DIR),
        "faiss_index": str(
            FAISS_INDEX_PATH
        ),
        "metadata": str(
            METADATA_PATH
        ),
        "faiss_config": str(
            FAISS_CONFIG_PATH
        ),
        "knowledge_base": str(
            KNOWLEDGE_BASE_DIR
        ),
        "payment_qr": str(
            PAYMENT_QR_PATH
        ),
        "embedding_model": EMBEDDING_MODEL,
        "faiss_metric": FAISS_METRIC,
        "top_k": TOP_K,
        "semantic_weight": SEMANTIC_WEIGHT,
        "keyword_weight": KEYWORD_WEIGHT,
        "groq_model": GROQ_MODEL,
        "groq_vision_model": GROQ_VISION_MODEL,
        "free_days": FREE_DAYS,
        "max_trip_days": MAX_TRIP_DAYS,
        "unlock_price": UNLOCK_PRICE,
        "groq_key_configured": bool(
            GROQ_API_KEY
        ),
    }
