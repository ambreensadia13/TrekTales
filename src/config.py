from pathlib import Path
import os
import streamlit as st

SRC_DIR = Path(__file__).resolve().parent
ROOT_DIR = SRC_DIR.parent

KNOWLEDGE_BASE_DIR = ROOT_DIR / "tourism_knowledge_base"
FAISS_DIR = ROOT_DIR / "faiss_db"
FAISS_INDEX_PATH = FAISS_DIR / "index.faiss"
METADATA_PATH = FAISS_DIR / "metadata.json"
FAISS_CONFIG_PATH = FAISS_DIR / "config.json"
ASSETS_DIR = ROOT_DIR / "assets"

# The repository currently contains jazzcash_qr.jpg. Keep PNG as a fallback.
QR_PATH = ASSETS_DIR / "jazzcash_qr.jpg"
if not QR_PATH.exists():
    QR_PATH = ASSETS_DIR / "jazzcash_qr.png"

APP_NAME = "TrekTales"
APP_TAGLINE = "Your AI Multi-Agent Travel Planner"
APP_VERSION = "1.1.0"

PRIMARY_RED = "#DA2C38"
DEEP_GREEN = "#226F54"
LIGHT_GREEN = "#87C38F"
CREAM = "#F4F0BB"
DARK_BROWN = "#43291F"
WHITE = "#FFFFFF"
BLACK = "#111111"
DARK_GREEN = "#174936"

FREE_DAYS = 1
PAID_DAYS = 2
MAX_TRIP_DAYS = 3
MAX_PAYMENT_IMAGE_MB = 20
UNLOCK_PRICE = 199
EXPECTED_PAYMENT_RECIPIENT = "ambreen sadia"
EXPECTED_PAYMENT_STATUS = "sent"

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


def get_secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, None)
    except Exception:
        value = None
    if value is not None:
        return str(value).strip()
    return os.getenv(name, default).strip()


GROQ_API_KEY = get_secret("GROQ_API_KEY")
GROQ_MODEL = get_secret("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_VISION_MODEL = get_secret(
    "GROQ_VISION_MODEL",
    "meta-llama/llama-4-scout-17b-16e-instruct",
)

TEMPERATURE = 0.2
MAX_OUTPUT_TOKENS = 1800

# IMPORTANT: this matches the model recorded in faiss_db/config.json.
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
TOP_K_FAISS = 8
TOP_K_BM25 = 8
TOP_K_FINAL = 6

SUPPORTED_LANGUAGES = ["English", "Urdu", "Roman Urdu"]
TRAVELER_TYPES = ["Solo", "Couple", "Family", "Friends"]
SUPPORTED_TRIP_DURATIONS = [1, 2, 3]

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


def validate_configuration() -> list[str]:
    problems: list[str] = []
    if not GROQ_API_KEY:
        problems.append("GROQ_API_KEY is missing from Streamlit Secrets.")
    if not FAISS_DIR.exists():
        problems.append(f"FAISS directory was not found: {FAISS_DIR}")
    if not FAISS_INDEX_PATH.exists():
        problems.append(f"FAISS index was not found: {FAISS_INDEX_PATH}")
    if not METADATA_PATH.exists():
        problems.append(f"FAISS metadata was not found: {METADATA_PATH}")
    if not FAISS_CONFIG_PATH.exists():
        problems.append(f"FAISS config was not found: {FAISS_CONFIG_PATH}")
    return problems


def ensure_directories() -> None:
    FAISS_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)


CONFIG = {
    "app_name": APP_NAME,
    "app_version": APP_VERSION,
    "groq_base_url": GROQ_BASE_URL,
    "groq_model": GROQ_MODEL,
    "groq_vision_model": GROQ_VISION_MODEL,
    "free_days": FREE_DAYS,
    "paid_days": PAID_DAYS,
    "max_trip_days": MAX_TRIP_DAYS,
    "unlock_price": UNLOCK_PRICE,
    "faiss_dir": str(FAISS_DIR),
    "embedding_model": EMBEDDING_MODEL,
    "top_k_faiss": TOP_K_FAISS,
    "top_k_bm25": TOP_K_BM25,
    "top_k_final": TOP_K_FINAL,
}
