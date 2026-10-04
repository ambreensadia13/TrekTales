from pathlib import Path
import json
import re

import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="TrekTales AI",
    page_icon="🥾",
    layout="wide",
)


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent

FAISS_DIR = ROOT_DIR / "faiss_db"
FAISS_INDEX_PATH = FAISS_DIR / "index.faiss"
METADATA_PATH = FAISS_DIR / "metadata.json"
FAISS_CONFIG_PATH = FAISS_DIR / "config.json"

ASSETS_DIR = ROOT_DIR / "assets"
PAYMENT_QR_PATH = ASSETS_DIR / "jazzcash_qr.jpg"


# ============================================================
# SAFE SECRETS
# ============================================================

def get_secret(name, default=""):
    try:
        value = st.secrets.get(name, default)
        if value is None:
            return default
        return value
    except Exception:
        return default


GROQ_API_KEY = get_secret("GROQ_API_KEY", "")

GROQ_MODEL = get_secret(
    "GROQ_MODEL",
    "openai/gpt-oss-120b"
)

UNLOCK_PRICE = 199
MAX_DAYS = 3
FREE_DAYS = 1


# ============================================================
# SESSION STATE
# ============================================================

if "payment_verified" not in st.session_state:
    st.session_state.payment_verified = False

if "result" not in st.session_state:
    st.session_state.result = None

if "sources" not in st.session_state:
    st.session_state.sources = []

if "diagnostic" not in st.session_state:
    st.session_state.diagnostic = []


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background:
            linear-gradient(
                135deg,
                #43291F 0%,
                #226F54 50%,
                #17231D 100%
            );
    }

    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .hero {
        background: linear-gradient(
            135deg,
            #DA2C38,
            #226F54
        );

        padding: 2.5rem;
        border-radius: 25px;
        margin-bottom: 1.5rem;

        box-shadow:
            0 15px 50px rgba(0,0,0,0.30);
    }

    .hero h1 {
        color: white !important;
        font-size: 3.2rem;
        font-weight: 800;
        margin-bottom: 0.3rem;
    }

    .hero p {
        color: white !important;
        font-size: 1.1rem;
    }

    .glass {
        background: rgba(255,255,255,0.09);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 20px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    .result {
        background: #F4F0BB;
        color: #43291F;
        border-radius: 22px;
        padding: 2rem;
        margin-top: 1.5rem;
        box-shadow:
            0 15px 45px rgba(0,0,0,0.25);
    }

    .result h1,
    .result h2,
    .result h3,
    .result h4 {
        color: #226F54 !important;
    }

    .result p,
    .result li {
        color: #43291F !important;
    }

    .source {
        background: rgba(135,195,143,0.15);
        border: 1px solid #87C38F;
        border-radius: 12px;
        padding: 0.8rem;
        margin-top: 0.5rem;
    }

    .source p {
        color: #F4F0BB !important;
        margin: 0;
    }

    .success-box {
        background: rgba(135,195,143,0.18);
        border: 1px solid #87C38F;
        border-radius: 15px;
        padding: 1rem;
    }

    .warning-box {
        background: rgba(218,44,56,0.18);
        border: 1px solid #DA2C38;
        border-radius: 15px;
        padding: 1rem;
    }

    .stButton > button {
        width: 100%;
        border-radius: 12px;
        border: none;
        background: #DA2C38;
        color: white;
        font-weight: 700;
        min-height: 45px;
    }

    .stButton > button:hover {
        background: #226F54;
        color: white;
    }

    div[data-testid="stSidebar"] {
        background: #17231D;
    }

    div[data-testid="stSidebar"] * {
        color: #F4F0BB;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="hero">
        <h1>🥾 TrekTales AI</h1>
        <p>
            AI-powered tourism itinerary planning,
            grounded in your TrekTales knowledge base.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATABASE STATUS
# ============================================================

index_exists = FAISS_INDEX_PATH.exists()
metadata_exists = METADATA_PATH.exists()
config_exists = FAISS_CONFIG_PATH.exists()

with st.sidebar:

    st.markdown("## 🥾 TrekTales")

    st.markdown("---")

    st.markdown("### Knowledge Base")

    if index_exists:
        st.success("✓ FAISS index found")
    else:
        st.error("✗ index.faiss missing")

    if metadata_exists:
        st.success("✓ Metadata found")
    else:
        st.error("✗ metadata.json missing")

    if config_exists:
        st.success("✓ Config found")
    else:
        st.warning("⚠ config.json missing")

    st.markdown("---")

    st.markdown("### Premium")

    if st.session_state.payment_verified:
        st.success("✓ Premium unlocked")
    else:
        st.info(
            "Day 1 is free.\n\n"
            "Days 2–3 require premium access."
        )

    st.markdown("---")

    if GROQ_API_KEY:
        st.success("✓ Groq API key detected")
    else:
        st.error("✗ Groq API key missing")


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def clean_model_text(text):
    if not text:
        return ""

    text = str(text)

    text = text.replace("```markdown", "")
    text = text.replace("```", "")
    text = text.replace("**", "")

    return text.strip()


def load_json(path):
    try:
        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)
    except Exception as e:
        return None


def normalize_record(record):
    """
    Convert different possible metadata structures
    into one consistent format.
    """

    if isinstance(record, str):
        return {
            "text": record,
            "source": "Unknown source",
            "page": "N/A"
        }

    if not isinstance(record, dict):
        return None

    metadata = record.get(
        "metadata",
        {}
    )

    if not isinstance(metadata, dict):
        metadata = {}

    text = (
        record.get("text")
        or record.get("content")
        or record.get("page_content")
        or metadata.get("text")
        or ""
    )

    source = (
        record.get("source")
        or metadata.get("source")
        or "Unknown source"
    )

    page = (
        record.get("page")
        or metadata.get("page")
        or "N/A"
    )

    return {
        "text": str(text),
        "source": str(source),
        "page": str(page)
    }


def load_metadata():

    data = load_json(
        METADATA_PATH
    )

    if data is None:
        return []

    # Normal list
    if isinstance(data, list):

        output = []

        for item in data:

            record = normalize_record(
                item
            )

            if record and record["text"]:
                output.append(record)

        return output

    # Dictionary
    if isinstance(data, dict):

        possible_keys = [
            "metadata",
            "records",
            "documents",
            "items",
            "data"
        ]

        for key in possible_keys:

            value = data.get(key)

            if isinstance(value, list):

                output = []

                for item in value:

                    record = normalize_record(
                        item
                    )

                    if record and record["text"]:
                        output.append(record)

                if output:
                    return output

    return []


# ============================================================
# KEYWORD FALLBACK
# ============================================================

def keyword_search(
    query,
    records,
    top_k=6
):

    if not records:
        return []

    query_words = set(
        re.findall(
            r"[a-zA-Z0-9]+",
            query.lower()
        )
    )

    query_words = {
        word
        for word in query_words
        if len(word) >= 3
    }

    scored = []

    for record in records:

        text = record["text"].lower()

        score = 0

        for word in query_words:

            if word in text:
                score += 1

        if score > 0:

            scored.append(
                (
                    score,
                    record
                )
            )

    scored.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return [
        record
        for _, record in scored[:top_k]
    ]


# ============================================================
# FAISS SEARCH
# ============================================================

@st.cache_resource(
    show_spinner=False
)
def load_embedding_model():

    from sentence_transformers import (
        SentenceTransformer
    )

    # Must match the model used when
    # your FAISS index was created.
    return SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2"
    )


@st.cache_resource(
    show_spinner=False
)
def load_faiss_index():

    import faiss

    return faiss.read_index(
        str(FAISS_INDEX_PATH)
    )


def semantic_search(
    query,
    records,
    top_k=6
):

    import numpy as np

    index = load_faiss_index()

    model = load_embedding_model()

    embedding = model.encode(
        [query],
        normalize_embeddings=True,
        convert_to_numpy=True
    )

    embedding = np.asarray(
        embedding,
        dtype="float32"
    )

    scores, indices = index.search(
        embedding,
        top_k
    )

    results = []

    for score, idx in zip(
        scores[0],
        indices[0]
    ):

        idx = int(idx)

        if idx < 0:
            continue

        if idx >= len(records):
            continue

        record = dict(
            records[idx]
        )

        record["score"] = float(
            score
        )

        results.append(
            record
        )

    return results


def retrieve(query):

    records = load_metadata()

    if not records:
        raise RuntimeError(
            "metadata.json was found but no usable "
            "records could be read."
        )

    # Try FAISS first
    if index_exists:

        try:

            results = semantic_search(
                query,
                records,
                top_k=6
            )

            if results:
                return results

        except Exception as e:

            st.session_state.diagnostic.append(
                "FAISS search fallback: "
                + str(e)
            )

    # Keyword fallback
    results = keyword_search(
        query,
        records,
        top_k=6
    )

    return results


# ============================================================
# GROQ
# ============================================================

def generate_with_groq(
    destination,
    days,
    travelers,
    interests,
    budget,
    context
):

    if not GROQ_API_KEY:

        raise RuntimeError(
            "GROQ_API_KEY is missing from Streamlit Secrets."
        )

    try:

        from groq import Groq

    except Exception as e:

        raise RuntimeError(
            "Groq package is not installed. "
            "Check requirements.txt."
        ) from e

    client = Groq(
        api_key=GROQ_API_KEY
    )

    prompt = f"""
You are TrekTales AI, a tourism itinerary planner.

You MUST follow these rules:

1. Use ONLY the knowledge-base information supplied below.
2. Do not invent attractions, restaurants, hotels,
   prices, addresses, distances, timings, phone numbers,
   transport information or other factual details.
3. If the knowledge base does not contain enough
   information, say so.
4. Generate EXACTLY {days} day(s).
5. Never create Day {days + 1}.
6. Keep the itinerary practical.
7. Use the user's interests when relevant.
8. The knowledge base may contain DEMO DATA.
9. Do not claim demo information is independently verified.
10. Do not invent facts merely to make the itinerary longer.

TRIP:

Destination:
{destination}

Days:
{days}

Travelers:
{travelers}

Interests:
{interests}

Budget:
{budget}

KNOWLEDGE BASE:

{context}

OUTPUT:

# TrekTales Itinerary

For each requested day:

## Day X

Morning:
...

Afternoon:
...

Evening:
...

At the end:

## Important Notes

Keep the answer concise.
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a grounded tourism "
                    "assistant. Never fabricate facts."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_tokens=3000
    )

    if not response.choices:
        raise RuntimeError(
            "Groq returned no response."
        )

    answer = response.choices[0].message.content

    return clean_model_text(
        answer
    )


# ============================================================
# INPUT SECTION
# ============================================================

st.markdown(
    "## ✈️ Plan Your Adventure"
)

col1, col2 = st.columns(2)

with col1:

    destination = st.text_input(
        "📍 Destination",
        placeholder="Example: Rawalpindi"
    )

    travelers = st.number_input(
        "👥 Travelers",
        min_value=1,
        max_value=20,
        value=2
    )

    budget = st.selectbox(
        "💰 Budget",
        [
            "Budget",
            "Moderate",
            "Premium"
        ]
    )


with col2:

    days = st.slider(
        "📅 Trip Duration",
        min_value=1,
        max_value=MAX_DAYS,
        value=1
    )

    interests = st.multiselect(
        "❤️ Interests",
        [
            "Adventure",
            "Culture",
            "Food",
            "Nature",
            "Sports",
            "Shopping",
            "Family",
            "Relaxation"
        ],
        default=["Culture"]
    )


# ============================================================
# PREMIUM
# ============================================================

if days > FREE_DAYS:

    st.markdown(
        f"""
        <div class="warning-box">
        <strong>🔐 Premium itinerary</strong><br><br>
        Day 1 is free.
        Days 2–{MAX_DAYS} require premium access.
        Unlock price: <strong>Rs. {UNLOCK_PRICE}</strong>
        </div>
        """,
        unsafe_allow_html=True
    )

    if not st.session_state.payment_verified:

        st.markdown(
            "### 💳 Unlock Premium"
        )

        pay1, pay2 = st.columns(2)

        with pay1:

            if PAYMENT_QR_PATH.exists():

                st.image(
                    str(PAYMENT_QR_PATH),
                    caption="Scan to pay",
                    width=280
                )

            else:

                st.info(
                    "Payment QR is not available."
                )

        with pay2:

            st.write(
                f"Amount: Rs. {UNLOCK_PRICE}"
            )

            st.write(
                "For the hackathon demo, "
                "you can verify your payment "
                "through your existing payment workflow."
            )

            uploaded = st.file_uploader(
                "Upload payment screenshot",
                type=[
                    "png",
                    "jpg",
                    "jpeg",
                    "webp"
                ]
            )

            if uploaded is not None:

                st.warning(
                    "Payment screenshot uploaded. "
                    "Use your existing payment verification "
                    "module if required."
                )

            if st.button(
                "🔓 Demo Unlock Premium"
            ):

                # IMPORTANT:
                # This is only a demo unlock for a
                # hackathon presentation.
                #
                # It does NOT claim that a payment
                # was actually verified.

                st.session_state.payment_verified = True

                st.success(
                    "Premium demo access unlocked."
                )

                st.rerun()


# ============================================================
# GENERATE BUTTON
# ============================================================

st.markdown("")

generate = st.button(
    "🥾 Generate My TrekTales Itinerary"
)


# ============================================================
# GENERATION
# ============================================================

if generate:

    st.session_state.diagnostic = []

    if not destination.strip():

        st.warning(
            "Please enter a destination."
        )

    else:

        # --------------------------------------------
        # Access control
        # --------------------------------------------

        if (
            days > FREE_DAYS
            and not st.session_state.payment_verified
        ):

            actual_days = FREE_DAYS

            st.info(
                "Only Day 1 is available because "
                "premium access has not been unlocked."
            )

        else:

            actual_days = days


        # --------------------------------------------
        # Search
        # --------------------------------------------

        search_query = (
            f"{destination} "
            f"{' '.join(interests)} "
            f"{budget}"
        )

        try:

            with st.spinner(
                "🔎 Searching TrekTales knowledge base..."
            ):

                records = retrieve(
                    search_query
                )

            if not records:

                st.error(
                    "No relevant information was found "
                    "in the knowledge base."
                )

            else:

                # ------------------------------------
                # Context
                # ------------------------------------

                context_blocks = []

                sources = []

                for number, record in enumerate(
                    records,
                    start=1
                ):

                    source = record.get(
                        "source",
                        "Unknown source"
                    )

                    page = record.get(
                        "page",
                        "N/A"
                    )

                    text = record.get(
                        "text",
                        ""
                    )

                    context_blocks.append(
                        f"""
SOURCE {number}

File:
{source}

Page:
{page}

Content:
{text}
"""
                    )

                    source_tuple = (
                        source,
                        page
                    )

                    if source_tuple not in sources:

                        sources.append(
                            source_tuple
                        )

                context = "\n".join(
                    context_blocks
                )

                # ------------------------------------
                # Groq
                # ------------------------------------

                with st.spinner(
                    "🤖 Creating your itinerary with Groq..."
                ):

                    answer = generate_with_groq(
                        destination=destination,
                        days=actual_days,
                        travelers=travelers,
                        interests=(
                            ", ".join(interests)
                            if interests
                            else "General sightseeing"
                        ),
                        budget=budget,
                        context=context
                    )

                st.session_state.result = answer
                st.session_state.sources = sources


        except Exception as e:

            st.error(
                "The itinerary could not be generated."
            )

            st.markdown(
                "### 🔧 Error"
            )

            st.code(
                str(e)
            )

            st.info(
                "The main TrekTales interface is working. "
                "The error above occurred during retrieval "
                "or Groq generation."
            )


# ============================================================
# RESULT
# ============================================================

if st.session_state.result:

    st.markdown(
        "---"
    )

    st.markdown(
        "## 🗺️ Your TrekTales Itinerary"
    )

    st.markdown(
        '<div class="result">',
        unsafe_allow_html=True
    )

    st.markdown(
        st.session_state.result
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )

    # --------------------------------------------
    # SOURCES
    # --------------------------------------------

    st.markdown(
        "### 📚 Sources Used"
    )

    for source, page in st.session_state.sources:

        st.markdown(
            f"""
            <div class="source">
                <p>
                📄 <strong>{source}</strong>
                &nbsp; | &nbsp;
                Page: {page}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# DIAGNOSTICS
# ============================================================

if st.session_state.diagnostic:

    with st.expander(
        "Technical diagnostics"
    ):

        for item in st.session_state.diagnostic:

            st.write(
                item
            )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "TrekTales AI • Hackathon Demo • "
    "Knowledge-grounded itinerary generation"
)
