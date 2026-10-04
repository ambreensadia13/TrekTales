from pathlib import Path
import base64
import json
import re

import streamlit as st



\# ============================================================
\# PAGE CONFIG
\# ============================================================

st.set_page_config(
    page_title="TrekTales",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)



\# ============================================================
\# PROJECT PATHS
\# ============================================================

ROOT_DIR = Path(\_\_file\_\_).resolve().parent

FAISS_DIR = ROOT_DIR / "faiss_db"
FAISS_INDEX_PATH = FAISS_DIR / "index.faiss"
METADATA_PATH = FAISS_DIR / "metadata.json"
FAISS_CONFIG_PATH = FAISS_DIR / "config.json"

ASSETS_DIR = ROOT_DIR / "assets"
QR_PATH = ASSETS_DIR / "jazzcash_qr.jpg"



\# ============================================================
\# TREKTALES SETTINGS
\# ============================================================

FREE_DAYS = 1
MAX_TRIP_DAYS = 10
UNLOCK_PRICE = 199

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"

DEFAULT_GROQ_VISION_MODEL = (
    "meta-llama/llama-4-scout-17b-16e-instruct"
)

DEFAULT_GROQ_BASE_URL = (
    "[https://api.groq.com/openai/v1](https://api.groq.com/openai/v1)"
)

TOP_K = 6



\# ============================================================
\# COLORS
\# ============================================================

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



\# ============================================================
\# CSS
\# ============================================================

st.markdown(
    f"""
\<style>

\* {{
    box-sizing: border-box;
}}

html,
body,
[data-testid="stAppViewContainer"] {{
    font-family: Arial, Helvetica, sans-serif;
}}

.stApp {{
    background:
        linear-gradient(
            135deg,
            {SOFT_WHITE} 0%,
            {CREAM} 48%,
            \#ffffff 100%
        );
    color: {BLACK};
}}

.main .block-container {{
    max-width: 1250px;
    padding-top: 1rem;
    padding-bottom: 3rem;
}}



/\* ============================================================
   SIDEBAR
   \============================================================ \*/

[data-testid="stSidebar"] {{
    background: {GREEN} !important;
}}

[data-testid="stSidebar"] > div {{
    background: {GREEN} !important;
}}

[data-testid="stSidebar"] \* {{
    color: {WHITE} !important;
}}

.sidebar-brand {{
    text-align: center;
    padding: 10px 5px 22px;
}}

.sidebar-brand-title {{
    color: {CREAM} !important;
    font-size: 28px;
    font-weight: 900;
}}

.sidebar-brand-subtitle {{
    color: {WHITE} !important;
    font-size: 13px;
    opacity: 0.9;
}}

.sidebar-card {{
    background: rgba(255, 255, 255, 0.10);
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 14px;
    padding: 14px;
    margin: 10px 0;
}}

.sidebar-card-title {{
    color: {CREAM} !important;
    font-size: 13px;
    font-weight: 800;
    margin-bottom: 7px;
}}

.sidebar-card-text {{
    color: {WHITE} !important;
    font-size: 12px;
    line-height: 1.55;
}}



/\* ============================================================
   BRAND
   \============================================================ \*/

.brand-wrapper {{
    text-align: center;
    padding: 5px 0 20px;
}}

.brand-title {{
    color: {GREEN};
    font-size: clamp(2rem, 5vw, 3.5rem);
    font-weight: 900;
    letter-spacing: -2px;
    margin: 0;
}}

.brand-title span {{
    color: {RED};
}}

.brand-subtitle {{
    color: {BROWN};
    font-size: clamp(0.85rem, 2vw, 1.05rem);
    margin-top: 6px;
}}



/\* ============================================================
   HERO
   \============================================================ \*/

.hero-card {{
    background:
        linear-gradient(
            135deg,
            {GREEN},
            {DARK_GREEN}
        );
    border-radius: 24px;
    padding: clamp(25px, 5vw, 50px);
    color: {WHITE};
    box-shadow: 0 15px 45px rgba(34, 111, 84, 0.22);
    margin-bottom: 25px;
}}

.hero-card h1 {{
    color: {WHITE} !important;
    font-size: clamp(2rem, 5vw, 3.4rem);
    line-height: 1.1;
    font-weight: 900;
    margin-bottom: 15px;
}}

.hero-card p {{
    color: {WHITE} !important;
    font-size: clamp(0.9rem, 2vw, 1.1rem);
    line-height: 1.7;
    max-width: 850px;
}}



/\* ============================================================
   SECTION HEADINGS
   \============================================================ \*/

.section-title {{
    color: {BROWN};
    font-size: 1.65rem;
    font-weight: 900;
    margin-top: 30px;
    margin-bottom: 8px;
}}

.section-subtitle {{
    color: {GREEN};
    font-size: 0.95rem;
    margin-bottom: 18px;
}}



/\* ============================================================
   FEATURE CARDS
   \============================================================ \*/

.feature-card {{
    background: {WHITE};
    border: 1px solid rgba(67, 41, 31, 0.12);
    border-radius: 18px;
    padding: 22px;
    min-height: 170px;
    box-shadow: 0 7px 22px rgba(67, 41, 31, 0.08);
}}

.feature-icon {{
    font-size: 29px;
    margin-bottom: 7px;
}}

.feature-card h3 {{
    color: {BROWN} !important;
    font-size: 1.05rem;
    margin-bottom: 8px;
}}

.feature-card p {{
    color: {BLACK} !important;
    font-size: 0.9rem;
    line-height: 1.6;
}}



/\* ============================================================
   FORM INPUTS
   \============================================================ \*/

label {{
    color: {BROWN} !important;
    font-weight: 700 !important;
}}

.stTextInput input,
.stTextArea textarea,
.stNumberInput input {{
    background: {WHITE} !important;
    color: {BLACK} !important;
    border: 2px solid rgba(34, 111, 84, 0.25) !important;
    border-radius: 11px !important;
}}

.stTextInput input\:focus,
.stTextArea textarea\:focus,
.stNumberInput input\:focus {{
    border-color: {GREEN} !important;
    box-shadow: 0 0 0 2px rgba(135, 195, 143, 0.25) !important;
}}



/\* ============================================================
   SELECT BOXES
   \============================================================ \*/

div[data-baseweb="select"] > div {{
    background: {WHITE} !important;
    color: {BLACK} !important;
    border: 2px solid rgba(34, 111, 84, 0.25) !important;
    border-radius: 11px !important;
}}

div[data-baseweb="select"] span {{
    color: {BLACK} !important;
}}

ul[role="listbox"] {{
    background: {WHITE} !important;
}}

li[role="option"] {{
    color: {BLACK} !important;
}}

li[role="option"]\:hover {{
    background: {LIGHT_GREEN} !important;
    color: {BLACK} !important;
}}



/\* ============================================================
   MULTISELECT
   \============================================================ \*/

div[data-baseweb="tag"] {{
    background: {LIGHT_GREEN} !important;
}}

div[data-baseweb="tag"] span {{
    color: {BLACK} !important;
}}



/\* ============================================================
   BUTTONS
   \============================================================ \*/

.stButton > button {{
    background: {RED} !important;
    color: {WHITE} !important;
    border: none !important;
    border-radius: 12px !important;
    min-height: 48px !important;
    font-weight: 800 !important;
    font-size: 15px !important;
}}

.stButton > button\:hover {{
    background: {BROWN} !important;
    color: {WHITE} !important;
}}



/\* ============================================================
   AI RESPONSE
   \============================================================ \*/

.response-card {{
    background: {WHITE};
    border-left: 6px solid {GREEN};
    border-radius: 18px;
    padding: 25px;
    margin: 15px 0;
    box-shadow: 0 8px 25px rgba(67, 41, 31, 0.10);
    overflow-wrap: anywhere;
}}

.response-card,
.response-card p,
.response-card li,
.response-card span,
.response-card strong {{
    color: {BLACK} !important;
}}

.response-card h1,
.response-card h2,
.response-card h3,
.response-card h4 {{
    color: {BROWN} !important;
}}



/\* ============================================================
   SOURCE CARDS
   \============================================================ \*/

.source-card {{
    background: {CREAM};
    border-left: 4px solid {GREEN};
    padding: 12px 15px;
    border-radius: 10px;
    margin: 7px 0;
}}

.source-card-title {{
    color: {BROWN} !important;
    font-weight: 800;
    font-size: 13px;
}}

.source-card-text {{
    color: {BLACK} !important;
    font-size: 12px;
}}



/\* ============================================================
   AGENT CARDS
   \============================================================ \*/

.agent-card {{
    background: {WHITE};
    border: 1px solid rgba(67, 41, 31, 0.10);
    border-radius: 15px;
    padding: 15px;
    min-height: 135px;
    box-shadow: 0 5px 18px rgba(67, 41, 31, 0.06);
}}

.agent-number {{
    color: {RED};
    font-weight: 900;
    font-size: 12px;
}}

.agent-name {{
    color: {BROWN} !important;
    font-weight: 900;
    font-size: 15px;
    margin-top: 4px;
}}

.agent-role {{
    color: {BLACK} !important;
    font-size: 12px;
    line-height: 1.5;
    margin-top: 7px;
}}



/\* ============================================================
   STATUS
   \============================================================ \*/

.status-card {{
    background: {WHITE};
    border-radius: 15px;
    padding: 15px;
    border: 1px solid rgba(67, 41, 31, 0.10);
    box-shadow: 0 5px 18px rgba(67, 41, 31, 0.06);
}}

.status-ready {{
    color: {GREEN} !important;
    font-weight: 800;
}}

.status-warning {{
    color: {RED} !important;
    font-weight: 800;
}}



/\* ============================================================
   PAYMENT CARD
   \============================================================ \*/

.payment-card {{
    background: {WHITE};
    border: 2px solid {LIGHT_GREEN};
    border-radius: 20px;
    padding: 25px;
    box-shadow: 0 8px 25px rgba(34, 111, 84, 0.10);
}}

.payment-title {{
    color: {BROWN} !important;
    font-size: 1.4rem;
    font-weight: 900;
}}

.payment-price {{
    color: {RED} !important;
    font-size: 2rem;
    font-weight: 900;
}}



/\* ============================================================
   FILE UPLOADER
   \============================================================ \*/

.stFileUploader {{
    background: {LIGHT_GREEN} !important;
    border: 2px solid {GREEN} !important;
    border-radius: 15px !important;
    padding: 8px !important;
}}

.stFileUploader section {{
    background: {LIGHT_GREEN} !important;
    border-radius: 12px !important;
}}

.stFileUploader section > div {{
    color: {BLACK} !important;
}}

.stFileUploader label,
.stFileUploader label \* {{
    color: {BLACK} !important;
}}

.stFileUploader button {{
    background: {LIGHT_GREEN} !important;
    color: {BLACK} !important;
    border: 2px solid {GREEN} !important;
    border-radius: 10px !important;
    font-weight: 800 !important;
}}

.stFileUploader button\:hover {{
    background: {GREEN} !important;
    color: {WHITE} !important;
}}



/\* ============================================================
   FOOTER
   \============================================================ \*/

.footer {{
    text-align: center;
    color: {BROWN};
    opacity: 0.75;
    font-size: 12px;
    padding: 30px 10px 10px;
}}



/\* ============================================================
   MOBILE
   \============================================================ \*/

@media screen and (max-width: 768px) {{

    .main .block-container {{
        padding: 0.8rem 0.7rem 2rem !important;
        max-width: 100% !important;
    }}

    .brand-title {{
        font-size: 2.25rem !important;
        letter-spacing: -1px;
    }}

    .hero-card {{
        padding: 25px 18px !important;
        border-radius: 18px !important;
    }}

    .hero-card h1 {{
        font-size: 2rem !important;
    }}

    .hero-card p {{
        font-size: 0.9rem !important;
    }}

    .feature-card {{
        min-height: auto !important;
        margin-bottom: 12px;
        padding: 18px !important;
    }}

    .agent-card {{
        min-height: auto !important;
        margin-bottom: 12px;
    }}

    .response-card {{
        padding: 17px !important;
        border-radius: 15px !important;
    }}

    .response-card p,
    .response-card li {{
        font-size: 0.92rem !important;
        line-height: 1.65 !important;
    }}

    .payment-card {{
        padding: 18px !important;
        border-radius: 16px !important;
    }}

    .payment-price {{
        font-size: 1.7rem !important;
    }}

    .stButton > button {{
        width: 100% !important;
        min-height: 48px !important;
    }}

    .stFileUploader,
    .stFileUploader section {{
        background: {LIGHT_GREEN} !important;
        border-color: {GREEN} !important;
    }}

    .stFileUploader button {{
        background: {LIGHT_GREEN} !important;
        color: {BLACK} !important;
        border-color: {GREEN} !important;
    }}

    img {{
        max-width: 100% !important;
        height: auto !important;
    }}

    .main,
    .main > div,
    section.main,
    .block-container {{
        max-width: 100% !important;
        overflow-x: hidden !important;
    }}
}}

\</style>
""",
    unsafe_allow_html=True,
)



\# ============================================================
\# SAFE HELPERS
\# ============================================================

def get_secret(name, default=""):
    try:
        value = st.secrets.get(name, default)
    except Exception:
        value = default

    if value is None:
        return default

    return str(value)



def clean_text(value):
    if value is None:
        return ""

    text = str(value)

    text = text.replace("\x00", "")

    \# Remove accidental HTML tags from model output.
    text = re.sub(
        r"<[^>]+>",
        "",
        text,
    )

    return text.strip()



def normalize_metadata(raw):
    if isinstance(raw, list):
        return raw

    if isinstance(raw, dict):

        for key in [
            "records",
            "metadata",
            "chunks",
            "documents",
            "data",
        ]:

            value = raw\.get(key)

            if isinstance(value, list):
                return value

    return []



def get_record_text(record):
    if not isinstance(record, dict):
        return ""

    for key in [
        "text",
        "content",
        "chunk",
        "document",
        "page_content",
    ]:

        value = record.get(key)

        if value:
            return str(value).strip()

    return ""



def get_record_source(record):
    if not isinstance(record, dict):
        return "Unknown source"

    for key in [
        "source",
        "filename",
        "file_name",
        "file",
        "document_name",
    ]:

        value = record.get(key)

        if value:
            return Path(str(value)).name

    return "Unknown source"



def get_record_page(record):
    if not isinstance(record, dict):
        return ""

    for key in [
        "page",
        "page_number",
        "page_num",
    ]:

        value = record.get(key)

        if value not in [None, ""]:
            return str(value)

    return ""



\# ============================================================
\# LOAD METADATA
\# ============================================================

@st.cache_data(show_spinner=False)
def load_metadata():

    if not METADATA_PATH.exists():
        return []

    try:

        with open(
            METADATA_PATH,
            "r",
            encoding="utf-8",
        ) as file:

            raw = json.load(file)

        return normalize_metadata(raw)

    except Exception:

        return []



\# ============================================================
\# LOAD FAISS
\# ============================================================

@st.cache_resource(show_spinner=False)
def load_faiss_resources():

    import faiss

    from sentence_transformers import SentenceTransformer

    if not FAISS_INDEX_PATH.exists():
        raise FileNotFoundError(
            "FAISS index not found."
        )

    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            "FAISS metadata not found."
        )

    index = faiss.read_index(
        str(FAISS_INDEX_PATH)
    )

    metadata = load_metadata()

    if index.ntotal == 0:
        raise RuntimeError(
            "The FAISS index is empty."
        )

    if len(metadata) == 0:
        raise RuntimeError(
            "The metadata file contains no records."
        )

    if index.ntotal != len(metadata):

        raise RuntimeError(
            "FAISS and metadata record counts do not match."
        )

    model = SentenceTransformer(
        DEFAULT_EMBEDDING_MODEL
    )

    return index, metadata, model



\# ============================================================
\# KEYWORD SCORE
\# ============================================================

def keyword_score(query, text):

    query_words = set(
        re.findall(
            r"\b[a-zA-Z0-9]{3,}\b",
            query.lower(),
        )
    )

    text_words = set(
        re.findall(
            r"\b[a-zA-Z0-9]{3,}\b",
            text.lower(),
        )
    )

    if not query_words:
        return 0.0

    overlap = query_words.intersection(
        text_words
    )

    return len(overlap) / len(query_words)



\# ============================================================
\# RETRIEVAL
\# ============================================================

def retrieve_context(
    query,
    top_k=TOP_K,
):

    index, metadata, model = (
        load_faiss_resources()
    )

    import numpy as np

    query_embedding = model.encode(
        [query],
        normalize_embeddings=True,
    )

    query_embedding = np.asarray(
        query_embedding,
        dtype="float32",
    )

    k = min(
        top_k,
        index.ntotal,
    )

    scores, indices = index.search(
        query_embedding,
        k,
    )

    results = []

    for score, index_id in zip(
        scores[0],
        indices[0],
    ):

        if index_id < 0:
            continue

        if index_id >= len(metadata):
            continue

        record = metadata[index_id]

        text = get_record_text(record)

        if not text:
            continue

        source = get_record_source(
            record
        )

        page = get_record_page(
            record
        )

        semantic = float(score)

        keyword = keyword_score(
            query,
            text,
        )

        combined = (
            0.75 \* semantic
            \+ 0.25 \* keyword
        )

        results.append(
            {
                "text": text,
                "source": source,
                "page": page,
                "score": combined,
            }
        )

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return results[:top_k]



def build_context(results):

    pieces = []

    for number, item in enumerate(
        results,
        start=1,
    ):

        location = item["source"]

        if item["page"]:
            location += (
                f" | Page {item['page']}"
            )

        pieces.append(
            f"""
SOURCE {number}
{location}

{item['text']}
""".strip()
        )

    return (
        "\n\n"
        "--------------------------------"
        "\n\n"
    ).join(pieces)



\# ============================================================
\# GROQ CLIENT
\# ============================================================

def get_groq_client():

    api_key = get_secret(
        "GROQ_API_KEY",
        "",
    )

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing."
        )

    base_url = get_secret(
        "GROQ_BASE_URL",
        DEFAULT_GROQ_BASE_URL,
    )

    try:

        from groq import Groq

        return Groq(
            api_key=api_key,
            base_url=base_url,
        )

    except ImportError:

        from openai import OpenAI

        return OpenAI(
            api_key=api_key,
            base_url=base_url,
        )



\# ============================================================
\# 8-AGENT ARCHITECTURE
\# ============================================================

AGENTS = [
    (
        "01",
        "🎯 Master Orchestrator",
        "Coordinates the complete TrekTales workflow and controls the agent sequence.",
    ),
    (
        "02",
        "🔎 Knowledge Agent",
        "Retrieves tourism evidence from the FAISS knowledge base.",
    ),
    (
        "03",
        "🗺️ Planner Agent",
        "Builds the day-by-day itinerary from retrieved evidence.",
    ),
    (
        "04",
        "💰 Budget Agent",
        "Handles budget-level planning and supported cost information.",
    ),
    (
        "05",
        "🛡️ Safety Agent",
        "Adds travel and safety information supported by the knowledge base.",
    ),
    (
        "06",
        "📝 Summarizer Agent",
        "Organizes the final response and source information.",
    ),
    (
        "07",
        "💳 Payment Agent",
        "Controls premium access and payment verification state.",
    ),
    (
        "08",
        "👁️ Vision Agent",
        "Extracts visible payment information from uploaded screenshots.",
    ),
]



\# ============================================================
\# TRIP GENERATION
\# ============================================================

def generate_trip(
    destination,
    starting_location,
    duration,
    travelers,
    budget,
    travel_style,
    interests,
    response_language,
    context,
):

    model = get_secret(
        "GROQ_MODEL",
        DEFAULT_GROQ_MODEL,
    )

    client = get_groq_client()

    system_prompt = f"""
You are TrekTales, an AI tourism planning system.

The TrekTales architecture contains exactly eight agents:

1\. Master Orchestrator
2\. Knowledge Agent
3\. Planner Agent
4\. Budget Agent
5\. Safety Agent
6\. Summarizer Agent
7\. Payment Agent
8\. Vision Agent

For this itinerary request, the Master Orchestrator coordinates
the Knowledge, Planner, Budget, Safety and Summarizer workflow.

IMPORTANT FACTUAL RULES:

\- Use ONLY the supplied knowledge-base evidence.
\- Do not invent tourism facts.
\- Do not invent hotels.
\- Do not invent restaurants.
\- Do not invent attractions.
\- Do not invent prices.
\- Do not invent opening hours.
\- Do not invent transport schedules.
\- Do not invent addresses.
\- Do not invent safety rules.
\- Do not invent contact information.

If the knowledge base does not contain required information,
write:

"Information not available in the TrekTales knowledge base."

Generate exactly {duration} day(s).

Do not generate additional days.

Response language:
{response_language}

Keep the response useful, readable and practical.

The response must not contain HTML tags.
Do not output \<div>, \<p>, \<span>, style attributes,
or any other HTML.

Use Markdown headings and bullet points only.
"""

    user_prompt = f"""
Create a {duration}-day TrekTales travel itinerary.

Destination:
{destination}

Starting location:
{starting_location}

Travelers:
{travelers}

Budget:
{budget}

Travel style:
{travel_style}

Interests:
{interests}

Knowledge-base evidence:

{context}

Structure the answer as:

\# TrekTales {duration}-Day Plan

\## Trip Overview

\## Day 1
Morning
Afternoon
Evening
Day Notes

"""

    for day in range(
        2,
        duration + 1,
    ):

        user_prompt += f"""
\## Day {day}

Morning
Afternoon
Evening
Day Notes

"""

    user_prompt += """
\## Budget Notes

Only mention prices supported by the evidence.

\## Safety Notes

Only mention safety information supported by the evidence.

\## Sources Used

List only the source filenames present in the supplied evidence.
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        max_tokens=6000,
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError(
            "Groq returned an empty response."
        )

    return clean_text(content)



\# ============================================================
\# PAYMENT VISION
\# ============================================================

def image_to_data_url(
    uploaded_file,
):

    data = uploaded_file.getvalue()

    mime = uploaded_file.type or "image/jpeg"

    encoded = base64.b64encode(
        data
    ).decode("utf-8")

    return (
        f"data:{mime};base64,{encoded}"
    )



def analyze_payment_image(
    uploaded_file,
):

    api_key = get_secret(
        "GROQ_API_KEY",
        "",
    )

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing."
        )

    model = get_secret(
        "GROQ_VISION_MODEL",
        DEFAULT_GROQ_VISION_MODEL,
    )

    base_url = get_secret(
        "GROQ_BASE_URL",
        DEFAULT_GROQ_BASE_URL,
    )

    try:

        from groq import Groq

        client = Groq(
            api_key=api_key,
            base_url=base_url,
        )

    except ImportError:

        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    image_url = image_to_data_url(
        uploaded_file
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Extract visible payment information "
                    "from the screenshot. "
                    "Never invent missing information. "
                    "Return JSON only."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """
Extract:

{
  "recipient": "",
  "amount": "",
  "status": "",
  "transaction_id": "",
  "confidence": ""
}

Only report information visibly present.
Do not approve the payment.
""",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                        },
                    },
                ],
            },
        ],
        max_tokens=800,
    )

    content = (
        response.choices[0]
        .message
        .content
    )

    if not content:
        return {}

    try:

        cleaned = content.strip()

        cleaned = re.sub(
            r"^\`\`\`json",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r"^\`\`\`",
            "",
            cleaned,
        )

        cleaned = re.sub(
            r"\`\`\`$",
            "",
            cleaned,
        )

        return json.loads(
            cleaned.strip()
        )

    except Exception:

        return {
            "raw_analysis": content
        }



\# ============================================================
\# DETERMINISTIC PAYMENT VERIFICATION
\# ============================================================

def verify_payment_data(
    payment_data,
):

    if not isinstance(
        payment_data,
        dict,
    ):

        return (
            False,
            "Payment information could not be read.",
        )

    expected_recipient = get_secret(
        "EXPECTED_PAYMENT_RECIPIENT",
        "",
    ).strip()

    recipient = str(
        payment_data.get(
            "recipient",
            "",
        )
    ).strip()

    amount_raw = str(
        payment_data.get(
            "amount",
            "",
        )
    )

    status = str(
        payment_data.get(
            "status",
            "",
        )
    ).strip().lower()

    numbers = re.findall(
        r"\d+(?:\\.\d+)?",
        amount_raw,
    )

    amount = None

    if numbers:

        try:
            amount = float(
                numbers[0]
            )
        except Exception:
            amount = None

    valid_statuses = {
        "successful",
        "success",
        "completed",
        "complete",
        "paid",
        "sent",
    }

    if amount is None:

        return (
            False,
            "Payment amount could not be read.",
        )

    if amount < UNLOCK_PRICE:

        return (
            False,
            f"Payment amount must be at least Rs. {UNLOCK_PRICE}.",
        )

    if status not in valid_statuses:

        return (
            False,
            "Payment status is not shown as successful.",
        )

    if expected_recipient:

        if (
            recipient.lower()
            != expected_recipient.lower()
        ):

            return (
                False,
                "Payment recipient does not match the configured recipient.",
            )

    return (
        True,
        "Payment passed the verification checks.",
    )



\# ============================================================
\# ACCESS CONTROL
\# ============================================================

def accessible_days(
    requested_days,
    payment_verified,
):

    requested_days = max(
        1,
        min(
            int(requested_days),
            MAX_TRIP_DAYS,
        ),
    )

    if requested_days == 1:
        return 1

    if payment_verified:
        return requested_days

    return 1



\# ============================================================
\# SOURCE DISPLAY
\# ============================================================

def show_sources(
    results,
):

    if not results:
        return

    st.markdown(
        '\<div class="section-title">📚 Knowledge Sources\</div>',
        unsafe_allow_html=True,
    )

    seen = set()

    for item in results:

        source = item["source"]
        page = item["page"]

        key = (
            source,
            page,
        )

        if key in seen:
            continue

        seen.add(key)

        location = source

        if page:
            location += (
                f" — Page {page}"
            )

        st.markdown(
            f"""
            \<div class="source-card">
                \<div class="source-card-title">
                    📄 {source}
                \</div>
                \<div class="source-card-text">
                    {location}
                \</div>
            \</div>
            """,
            unsafe_allow_html=True,
        )



\# ============================================================
\# SESSION STATE
\# ============================================================

if "payment_verified" not in st.session_state:
    st.session_state.payment_verified = False

if "payment_analysis" not in st.session_state:
    st.session_state.payment_analysis = None

if "trip_result" not in st.session_state:
    st.session_state.trip_result = None

if "trip_sources" not in st.session_state:
    st.session_state.trip_sources = []

if "generated_days" not in st.session_state:
    st.session_state.generated_days = 0



\# ============================================================
\# SIDEBAR
\# ============================================================

with st.sidebar:

    st.markdown(
        """
        \<div class="sidebar-brand">
            \<div class="sidebar-brand-title">
                🌿 TrekTales
            \</div>
            \<div class="sidebar-brand-subtitle">
                AI Travel Planner
            \</div>
        \</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        \<div class="sidebar-card">
            \<div class="sidebar-card-title">
                🔓 ACCESS MODEL
            \</div>
            \<div class="sidebar-card-text">
                Day 1 is free.\<br>
                Days 2–10 require premium unlock.
            \</div>
        \</div>
        """,
        unsafe_allow_html=True,
    )

    response_language = st.selectbox(
        "Response Language",
        [
            "English",
            "Urdu",
            "Roman Urdu",
        ],
    )

    st.markdown(
        """
        \<div class="sidebar-card">
            \<div class="sidebar-card-title">
                🤖 8 AI AGENTS
            \</div>
            \<div class="sidebar-card-text">
                🎯 Master Orchestrator\<br>
                🔎 Knowledge Agent\<br>
                🗺️ Planner Agent\<br>
                💰 Budget Agent\<br>
                🛡️ Safety Agent\<br>
                📝 Summarizer Agent\<br>
                💳 Payment Agent\<br>
                👁️ Vision Agent
            \</div>
        \</div>
        """,
        unsafe_allow_html=True,
    )

    model_name = get_secret(
        "GROQ_MODEL",
        DEFAULT_GROQ_MODEL,
    )

    st.markdown(
        f"""
        \<div class="sidebar-card">
            \<div class="sidebar-card-title">
                ⚡ GROQ MODEL
            \</div>
            \<div class="sidebar-card-text">
                {model_name}
            \</div>
        \</div>
        """,
        unsafe_allow_html=True,
    )



\# ============================================================
\# BRAND
\# ============================================================

st.markdown(
    """
    \<div class="brand-wrapper">
        \<div class="brand-title">
            Trek\<span>Tales\</span> 🌿
        \</div>
        \<div class="brand-subtitle">
            AI-powered tourism planning grounded in your knowledge base
        \</div>
    \</div>
    """,
    unsafe_allow_html=True,
)



\# ============================================================
\# HERO
\# ============================================================

st.markdown(
    """
    \<div class="hero-card">
        \<h1>
            Plan your journey.\<br>
            Explore with confidence.
        \</h1>

        \<p>
            TrekTales creates personalized travel itineraries
            using your tourism knowledge base and Groq-powered
            AI agents.
        \</p>
    \</div>
    """,
    unsafe_allow_html=True,
)



\# ============================================================
\# FEATURES
\# ============================================================

feature1, feature2, feature3 = st.columns(3)

with feature1:

    st.markdown(
        """
        \<div class="feature-card">
            \<div class="feature-icon">🧠\</div>
            \<h3>Knowledge-Grounded AI\</h3>
            \<p>
                Tourism recommendations are generated from
                retrieved knowledge-base evidence.
            \</p>
        \</div>
        """,
        unsafe_allow_html=True,
    )

with feature2:

    st.markdown(
        """
        \<div class="feature-card">
            \<div class="feature-icon">🗺️\</div>
            \<h3>Personalized Planning\</h3>
            \<p>
                Build trips based on duration, travelers,
                budget, travel style and interests.
            \</p>
        \</div>
        """,
        unsafe_allow_html=True,
    )

with feature3:

    st.markdown(
        """
        \<div class="feature-card">
            \<div class="feature-icon">🛡️\</div>
            \<h3>Evidence First\</h3>
            \<p>
                TrekTales avoids inventing facts when the
                knowledge base does not contain the answer.
            \</p>
        \</div>
        """,
        unsafe_allow_html=True,
    )



\# ============================================================
\# 8 AGENTS
\# ============================================================

st.markdown(
    '\<div class="section-title">🤖 TrekTales 8-Agent System\</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '\<div class="section-subtitle">Eight specialized agents work together in the TrekTales architecture.\</div>',
    unsafe_allow_html=True,
)

for row_start in range(
    0,
    len(AGENTS),
    4,
):

    columns = st.columns(4)

    for column, agent in zip(
        columns,
        AGENTS[row_start\:row_start + 4],
    ):

        number, name, role = agent

        with column:

            st.markdown(
                f"""
                \<div class="agent-card">
                    \<div class="agent-number">
                        AGENT {number}
                    \</div>

                    \<div class="agent-name">
                        {name}
                    \</div>

                    \<div class="agent-role">
                        {role}
                    \</div>
                \</div>
                """,
                unsafe_allow_html=True,
            )



\# ============================================================
\# TRIP PLANNER
\# ============================================================

st.markdown(
    '\<div class="section-title">🧭 Build Your Trip\</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '\<div class="section-subtitle">Tell TrekTales what kind of journey you want.\</div>',
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)

with col1:

    destination = st.text_input(
        "Destination",
        placeholder="e.g. Rawalpindi",
    )

with col2:

    starting_location = st.text_input(
        "Starting Location",
        placeholder="e.g. Islamabad",
    )



col3, col4, col5 = st.columns(3)

with col3:

    duration = st.number_input(
        "Trip Duration",
        min_value=1,
        max_value=10,
        value=1,
        step=1,
        help="Choose between 1 and 10 days.",
    )

    st.caption(
        f"{int(duration)} day"
        f"{'s' if int(duration) != 1 else ''}"
        " selected"
    )

with col4:

    travelers = st.number_input(
        "Travelers",
        min_value=1,
        max_value=20,
        value=2,
        step=1,
    )

with col5:

    budget = st.selectbox(
        "Budget Level",
        [
            "Budget — Rs. 3,000–7,000/day",
            "Standard — Rs. 7,000–15,000/day",
            "Comfort — Rs. 15,000–30,000/day",
            "Premium — Rs. 30,000+/day",
        ],
        index=1,
    )



travel_style = st.selectbox(
    "Travel Style",
    [
        "Balanced",
        "Adventure",
        "Relaxed",
        "Family",
        "Cultural",
        "Nature",
        "Food & Exploration",
        "Budget Friendly",
        "Luxury",
    ],
)



\# ============================================================
\# INTEREST OPTIONS
\# ============================================================

st.markdown(
    '\<div class="section-subtitle">❤️ Choose your interests\</div>',
    unsafe_allow_html=True,
)

interest_options = [
    "🏛️ History & Heritage",
    "🌲 Nature",
    "🥾 Hiking & Trekking",
    "🍴 Food & Local Cuisine",
    "📸 Photography",
    "🕌 Culture & Architecture",
    "👨‍👩‍👧 Family Activities",
    "🎨 Arts & Creativity",
    "🛍️ Shopping",
    "🏏 Sports",
    "🌅 Scenic Views",
    "🧘 Relaxation",
    "🐦 Wildlife",
    "🏕️ Camping",
    "🎉 Local Events",
    "🚗 Road Trips",
]

selected_interests = st.multiselect(
    "Select one or more interests",
    options=interest_options,
    default=[],
    help="Choose the activities and experiences you want included.",
)



other_interests = st.text_input(
    "Other interests",
    placeholder="e.g. local markets, architecture, hidden places",
)



\# Build final interest text.

interest_parts = list(
    selected_interests
)

if other_interests.strip():

    interest_parts.append(
        other_interests.strip()
    )

if interest_parts:

    interests = ", ".join(
        interest_parts
    )

else:

    interests = "General sightseeing and exploration"



\# ============================================================
\# SYSTEM STATUS
\# ============================================================

st.markdown(
    '\<div class="section-title">⚙️ System Status\</div>',
    unsafe_allow_html=True,
)

status1, status2, status3 = st.columns(3)

groq_ready = bool(
    get_secret(
        "GROQ_API_KEY",
        "",
    ).strip()
)

with status1:

    if groq_ready:

        st.markdown(
            """
            \<div class="status-card">
                \<div class="status-ready">
                    🟢 Groq API Ready
                \</div>
                \<small>
                    GroqCloud key configured.
                \</small>
            \</div>
            """,
            unsafe_allow_html=True,
        )

    else:

        st.markdown(
            """
            \<div class="status-card">
                \<div class="status-warning">
                    🔴 Groq API Missing
                \</div>
                \<small>
                    Add GROQ_API_KEY to Secrets.
                \</small>
            \</div>
            """,
            unsafe_allow_html=True,
        )



with status2:

    faiss_ready = (
        FAISS_INDEX_PATH.exists()
        and METADATA_PATH.exists()
    )

    if faiss_ready:

        st.markdown(
            """
            \<div class="status-card">
                \<div class="status-ready">
                    🟢 FAISS Ready
                \</div>
                \<small>
                    Knowledge base detected.
                \</small>
            \</div>
            """,
            unsafe_allow_html=True,
        )

    else:

        st.markdown(
            """
            \<div class="status-card">
                \<div class="status-warning">
                    🔴 FAISS Missing
                \</div>
                \<small>
                    Check faiss_db.
                \</small>
            \</div>
            """,
            unsafe_allow_html=True,
        )



with status3:

    st.markdown(
        """
        \<div class="status-card">
            \<div class="status-ready">
                🟢 8-Agent System
            \</div>
            \<small>
                All eight TrekTales roles configured.
            \</small>
        \</div>
        """,
        unsafe_allow_html=True,
    )



\# ============================================================
\# ACCESS MESSAGE
\# ============================================================

requested_days = int(duration)

if requested_days > 1:

    if st.session_state.payment_verified:

        st.success(
            f"🔓 Premium access active. "
            f"Your {requested_days}-day trip is unlocked."
        )

    else:

        st.info(
            f"🔒 Day 1 is free. "
            f"Days 2–{requested_days} require the "
            f"Rs. {UNLOCK_PRICE} premium unlock."
        )



\# ============================================================
\# GENERATE BUTTON
\# ============================================================

st.markdown(
    '\<div class="section-title">✨ Generate Your Journey\</div>',
    unsafe_allow_html=True,
)

generate_button = st.button(
    "🌿 Generate My Trip",
    use_container_width=True,
)



if generate_button:

    if not destination.strip():

        st.error(
            "Please enter a destination."
        )

    elif not starting_location.strip():

        st.error(
            "Please enter your starting location."
        )

    elif not groq_ready:

        st.error(
            "GROQ_API_KEY is missing from Streamlit Secrets."
        )

    elif not faiss_ready:

        st.error(
            "FAISS files are missing. "
            "Expected faiss_db/index.faiss and "
            "faiss_db/metadata.json."
        )

    else:

        payment_verified = (
            st.session_state.payment_verified
        )

        days_to_generate = accessible_days(
            requested_days,
            payment_verified,
        )

        with st.spinner(
            "🔎 Knowledge Agent is retrieving evidence..."
        ):

            try:

                retrieval_query = f"""
Destination: {destination}
Starting location: {starting_location}
Duration: {days_to_generate} days
Travelers: {travelers}
Budget: {budget}
Travel style: {travel_style}
Interests: {interests}
"""

                results = retrieve_context(
                    retrieval_query
                )

                if not results:

                    st.error(
                        "No relevant evidence was found "
                        "in the TrekTales knowledge base."
                    )

                else:

                    context = build_context(
                        results
                    )

                    with st.spinner(
                        "🎯 Master Orchestrator is coordinating "
                        "the TrekTales agents..."
                    ):

                        trip_result = generate_trip(
                            destination=destination,
                            starting_location=starting_location,
                            duration=days_to_generate,
                            travelers=travelers,
                            budget=budget,
                            travel_style=travel_style,
                            interests=interests,
                            response_language=response_language,
                            context=context,
                        )

                    st.session_state.trip_result = (
                        trip_result
                    )

                    st.session_state.trip_sources = (
                        results
                    )

                    st.session_state.generated_days = (
                        days_to_generate
                    )

                    if (
                        requested_days > 1
                        and not payment_verified
                    ):

                        st.success(
                            "Day 1 has been generated. "
                            "Unlock premium access to generate "
                            f"Days 2–{requested_days}."
                        )

                    else:

                        st.success(
                            f"Your {days_to_generate}-day "
                            "TrekTales itinerary is ready."
                        )

            except Exception as exc:

                st.error(
                    "The trip could not be generated."
                )

                st.code(
                    str(exc),
                    language="text",
                )



\# ============================================================
\# TRIP RESULT
\# ============================================================

if st.session_state.trip_result:

    st.markdown(
        '\<div class="section-title">🗺️ Your TrekTales Journey\</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '\<div class="response-card">',
        unsafe_allow_html=True,
    )

    \# IMPORTANT:
    \# The AI output is cleaned before display.
    \# No HTML tags such as \<p> or \<div> are shown
    \# inside the actual response.

    st.markdown(
        st.session_state.trip_result
    )

    st.markdown(
        "\</div>",
        unsafe_allow_html=True,
    )

    show_sources(
        st.session_state.trip_sources
    )



\# ============================================================
\# PAYMENT / PREMIUM SECTION
\# ============================================================

if requested_days >= 2:

    st.markdown(
        '\<div class="section-title">🔓 Premium Access\</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.payment_verified:

        st.success(
            "✅ Premium access is active."
        )

        st.write(
            f"Your selected {requested_days}-day trip "
            "is unlocked."
        )

    else:

        payment_left, payment_right = st.columns(
            [1, 1.3]
        )

        with payment_left:

            st.markdown(
                '\<div class="payment-card">',
                unsafe_allow_html=True,
            )

            st.markdown(
                "### 🌿 TrekTales Premium"
            )

            st.write(
                f"Unlock Days 2–{requested_days}."
            )

            st.markdown(
                f"## Rs. {UNLOCK_PRICE}"
            )

            st.write(
                "One-time premium unlock."
            )

            st.markdown(
                "\</div>",
                unsafe_allow_html=True,
            )

            if QR_PATH.exists():

                st.image(
                    str(QR_PATH),
                    caption="Scan to make your payment",
                    use_container_width=True,
                )

            else:

                st.warning(
                    "Payment QR image not found."
                )

        with payment_right:

            st.markdown(
                '\<div class="payment-card">',
                unsafe_allow_html=True,
            )

            st.markdown(
                "### 📤 Upload Payment Screenshot"
            )

            st.write(
                f"Upload proof of your Rs. {UNLOCK_PRICE} payment."
            )

            st.markdown(
                "\</div>",
                unsafe_allow_html=True,
            )

            payment_file = st.file_uploader(
                "Choose payment screenshot",
                type=[
                    "jpg",
                    "jpeg",
                    "png",
                    "webp",
                ],
                key="payment_upload",
            )

            if payment_file is not None:

                analyze_button = st.button(
                    "🔍 Analyze Payment",
                    use_container_width=True,
                )

                if analyze_button:

                    with st.spinner(
                        "👁️ Vision Agent is reading the screenshot..."
                    ):

                        try:

                            analysis = (
                                analyze_payment_image(
                                    payment_file
                                )
                            )

                            st.session_state.payment_analysis = (
                                analysis
                            )

                            if analysis:

                                st.write(
                                    "Payment information detected:"
                                )

                                st.json(
                                    analysis
                                )

                                verified, message = (
                                    verify_payment_data(
                                        analysis
                                    )
                                )

                                if verified:

                                    st.session_state.payment_verified = (
                                        True
                                    )

                                    st.success(
                                        "✅ Payment verified."
                                    )

                                    st.rerun()

                                else:

                                    st.error(
                                        f"❌ Payment not verified: "
                                        f"{message}"
                                    )

                            else:

                                st.error(
                                    "No payment information "
                                    "could be extracted."
                                )

                        except Exception as exc:

                            st.error(
                                "Payment analysis failed."
                            )

                            st.code(
                                str(exc),
                                language="text",
                            )



\# ============================================================
\# PREMIUM LOCK NOTICE
\# ============================================================

if (
    requested_days > 1
    and not st.session_state.payment_verified
):

    st.warning(
        f"🔒 Days 2–{requested_days} are locked. "
        f"Complete the Rs. {UNLOCK_PRICE} premium verification "
        "to unlock them."
    )



\# ============================================================
\# DISCLAIMER
\# ============================================================

st.markdown(
    '\<div class="section-title">⚠️ Information Notice\</div>',
    unsafe_allow_html=True,
)

st.info(
    "TrekTales generates travel suggestions from its available "
    "knowledge base. Information can change over time. "
    "Confirm important prices, availability, transport schedules, "
    "weather and local safety conditions before travelling."
)



\# ============================================================
\# FOOTER
\# ============================================================

st.markdown(
    """
    \<div class="footer">
        🌿 TrekTales — AI-Powered Tourism Planner
        \<br>
        FAISS • Sentence Transformers • Groq • 8-Agent Architecture
    \</div>
    """,
    unsafe_allow_html=True,
)           only remove the html like tags that are shown on the ui
