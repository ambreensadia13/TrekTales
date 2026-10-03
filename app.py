import os
import re
from pathlib import Path

import streamlit as st

from src.config import (
    APP_NAME,
    APP_TAGLINE,
    GROQ_MODEL,
    MAX_RAG_RESULTS,
    SUPPORTED_IMAGE_TYPES,
)
from src.rag import (
    database_exists,
    load_rag_database,
    search_knowledge_base,
)
from src.crew import generate_trip_plan
from src.citations import format_sources
from src.payment import render_payment_section
from src.vision import analyze_travel_image


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="TrekTales AI",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent
FAISS_DIR = ROOT_DIR / "faiss_db"
KB_DIR = ROOT_DIR / "tourism_knowledge_base"


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

    html, body, [class*="css"] {
        font-family: "DM Sans", sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(218,44,56,0.13), transparent 30%),
            radial-gradient(circle at top right, rgba(135,195,143,0.12), transparent 28%),
            #f4f0bb;
    }

    .main {
        padding-top: 1rem;
    }

    .hero {
        padding: 2.5rem 2rem;
        border-radius: 28px;
        background:
            linear-gradient(
                135deg,
                rgba(67,41,31,0.98),
                rgba(34,111,84,0.96)
            );
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 20px 50px rgba(67,41,31,0.22);
    }

    .hero h1 {
        font-family: "Playfair Display", serif;
        font-size: 3.3rem;
        margin-bottom: 0.4rem;
    }

    .hero p {
        font-size: 1.1rem;
        opacity: 0.92;
        max-width: 780px;
    }

    .badge {
        display: inline-block;
        padding: 0.35rem 0.8rem;
        border-radius: 999px;
        background: rgba(255,255,255,0.14);
        border: 1px solid rgba(255,255,255,0.25);
        font-size: 0.82rem;
        margin-bottom: 1rem;
    }

    .section-title {
        font-family: "Playfair Display", serif;
        color: #43291f;
        font-size: 1.8rem;
        margin-top: 1rem;
        margin-bottom: 0.7rem;
    }

    .info-card {
        background: rgba(255,255,255,0.68);
        border: 1px solid rgba(67,41,31,0.12);
        border-radius: 20px;
        padding: 1.1rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 25px rgba(67,41,31,0.07);
    }

    .source-card {
        background: rgba(135,195,143,0.18);
        border-left: 4px solid #226f54;
        border-radius: 12px;
        padding: 0.8rem 1rem;
        margin: 0.45rem 0;
    }

    .source-name {
        font-weight: 700;
        color: #226f54;
    }

    .disclaimer {
        background: rgba(218,44,56,0.09);
        border-left: 4px solid #da2c38;
        border-radius: 12px;
        padding: 0.9rem 1rem;
        color: #43291f;
        font-size: 0.88rem;
        margin-top: 1rem;
    }

    .stButton > button {
        border-radius: 12px;
        border: none;
        font-weight: 700;
        padding: 0.65rem 1rem;
        background: #da2c38;
        color: white;
    }

    .stButton > button:hover {
        background: #43291f;
        color: white;
    }

    div[data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                #43291f 0%,
                #226f54 100%
            );
    }

    div[data-testid="stSidebar"] * {
        color: white !important;
    }

    div[data-testid="stFileUploader"] {
        border-radius: 15px;
    }

    .footer {
        text-align: center;
        margin-top: 3rem;
        padding: 1.5rem;
        color: #43291f;
        font-size: 0.85rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

def clean_markdown(text: str) -> str:
    """Remove accidental HTML and excessive markdown formatting."""
    if not text:
        return ""

    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("```markdown", "")
    text = text.replace("```", "")
    text = text.replace("**", "")
    return text.strip()


@st.cache_resource(show_spinner=False)
def get_rag():
    """Load FAISS database once."""
    if not database_exists():
        return None

    try:
        return load_rag_database()
    except Exception:
        return None


def render_sources(results):
    if not results:
        return

    st.markdown("### 📚 Knowledge Sources")

    sources = format_sources(results)

    if not sources:
        st.info("No matching knowledge-base sources were found.")
        return

    for source in sources:
        st.markdown(
            f"""
            <div class="source-card">
                <div class="source-name">📄 {source}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🧭 TrekTales AI")
    st.caption("AI-powered travel planning for Pakistan")

    st.divider()

    st.markdown("### ⚙️ Trip Settings")

    destination = st.selectbox(
        "Destination",
        [
            "Rawalpindi",
            "Islamabad",
            "Murree",
            "Nathia Gali",
            "Hunza",
            "Skardu",
            "Other",
        ],
    )

    if destination == "Other":
        destination = st.text_input(
            "Enter destination",
            placeholder="e.g. Lahore",
        )

    trip_days = st.slider(
        "Trip duration",
        min_value=1,
        max_value=14,
        value=2,
    )

    budget = st.selectbox(
        "Budget",
        [
            "Budget",
            "Moderate",
            "Comfortable",
            "Luxury",
        ],
    )

    travelers = st.number_input(
        "Number of travelers",
        min_value=1,
        max_value=20,
        value=2,
    )

    interests = st.multiselect(
        "Interests",
        [
            "Food",
            "Historical Places",
            "Nature",
            "Shopping",
            "Adventure",
            "Family Activities",
            "Photography",
            "Culture",
            "Nightlife",
        ],
        default=["Food", "Historical Places"],
    )

    st.divider()

    language = st.selectbox(
        "Response language",
        [
            "English",
            "Urdu",
            "Roman Urdu",
        ],
    )

    st.divider()

    st.markdown("### 🧠 AI Engine")

    st.caption(f"CrewAI + Groq")
    st.caption(f"Model: `{GROQ_MODEL}`")

    if database_exists():
        st.success("FAISS knowledge base detected.")
    else:
        st.warning(
            "FAISS database not found. Run `python ingest.py` before deployment."
        )


# ============================================================
# HERO
# ============================================================

st.markdown(
    f"""
    <div class="hero">

        <div class="badge">
            🧠 CrewAI + ⚡ Groq + 📚 FAISS RAG
        </div>

        <h1>{APP_NAME}</h1>

        <p>{APP_TAGLINE}</p>

        <p>
            Build personalized Pakistan travel plans using a
            multi-agent AI system grounded in your tourism
            knowledge base.
        </p>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# TABS
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "🗺️ Trip Planner",
        "📚 Knowledge Base",
        "📸 Travel Vision",
        "💳 Support TrekTales",
    ]
)


# ============================================================
# TRIP PLANNER
# ============================================================

with tab1:

    st.markdown(
        '<div class="section-title">Plan Your Trip</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1.5, 1])

    with col1:

        trip_request = st.text_area(
            "Tell TrekTales what you want",
            placeholder=(
                "Example: Plan a 2-day Rawalpindi trip for two people. "
                "We love traditional food, historical places and photography."
            ),
            height=150,
        )

    with col2:

        st.markdown(
            """
            <div class="info-card">

            <strong>🤖 How TrekTales works</strong>

            <p>
            1. Searches your tourism knowledge base.
            </p>

            <p>
            2. Retrieves relevant local information.
            </p>

            <p>
            3. CrewAI agents analyze the trip.
            </p>

            <p>
            4. Groq generates the final itinerary.
            </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.button(
        "✨ Generate My Trip",
        type="primary",
        use_container_width=True,
    ):

        if not trip_request.strip():
            st.warning("Please describe your trip first.")
            st.stop()

        if not destination.strip():
            st.warning("Please enter a destination.")
            st.stop()

        if not os.getenv("GROQ_API_KEY"):

            try:
                if "GROQ_API_KEY" in st.secrets:
                    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
            except Exception:
                pass

        if not os.getenv("GROQ_API_KEY"):
            st.error(
                "GROQ_API_KEY is missing. Add it to Streamlit Secrets."
            )
            st.code(
                'GROQ_API_KEY = "your_groq_api_key"',
                language="toml",
            )
            st.stop()

        rag = get_rag()

        if rag is None:
            st.error(
                "FAISS knowledge base is unavailable. "
                "Run `python ingest.py` and upload the generated "
                "`faiss_db` folder to GitHub."
            )
            st.stop()

        with st.spinner("🔎 Searching the tourism knowledge base..."):

            try:

                search_text = (
                    f"Destination: {destination}\n"
                    f"Trip request: {trip_request}\n"
                    f"Interests: {', '.join(interests)}\n"
                    f"Budget: {budget}\n"
                )

                results = search_knowledge_base(
                    search_text,
                    rag,
                    top_k=MAX_RAG_RESULTS,
                )

            except Exception as exc:

                st.error(f"Knowledge-base search failed: {exc}")
                st.stop()

        if not results:
            st.warning(
                "No relevant tourism information was found. "
                "Try a more specific request."
            )
            st.stop()

        context_parts = []

        for item in results:

            source = item.get("source", "Unknown source")
            text = item.get("text", "")

            context_parts.append(
                f"SOURCE: {source}\n{text}"
            )

        rag_context = "\n\n---\n\n".join(context_parts)

        with st.spinner("🤖 CrewAI agents are planning your trip..."):

            try:

                answer = generate_trip_plan(
                    destination=destination,
                    trip_request=trip_request,
                    trip_days=trip_days,
                    budget=budget,
                    travelers=travelers,
                    interests=interests,
                    language=language,
                    rag_context=rag_context,
                )

            except Exception as exc:

                st.error(
                    "The AI planner encountered an error."
                )

                with st.expander("Technical details"):
                    st.code(str(exc))

                st.stop()

        st.markdown("### 🧭 Your TrekTales Plan")

        st.markdown(
            f"""
            <div class="info-card">
            {clean_markdown(answer)}
            </div>
            """,
            unsafe_allow_html=True,
        )

        render_sources(results)

        st.markdown(
            """
            <div class="disclaimer">
            ⚠️ Travel information can change. Always verify
            opening hours, prices, transport schedules,
            weather conditions and local restrictions before
            travelling.
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# KNOWLEDGE BASE
# ============================================================

with tab2:

    st.markdown(
        '<div class="section-title">📚 Tourism Knowledge Base</div>',
        unsafe_allow_html=True,
    )

    pdfs = sorted(KB_DIR.glob("*.pdf"))

    if pdfs:

        st.success(
            f"{len(pdfs)} tourism documents found."
        )

        for pdf in pdfs:

            st.markdown(
                f"""
                <div class="source-card">
                    📄 {pdf.name}
                </div>
                """,
                unsafe_allow_html=True,
            )

    else:

        st.warning(
            "No tourism PDF documents were found."
        )

    st.divider()

    if database_exists():

        st.success(
            "FAISS vector database is available."
        )

        st.caption(
            "The app uses semantic similarity search against "
            "your tourism documents before calling CrewAI."
        )

    else:

        st.error(
            "FAISS database is missing."
        )

        st.code(
            "python ingest.py",
            language="bash",
        )


# ============================================================
# VISION
# ============================================================

with tab3:

    st.markdown(
        '<div class="section-title">📸 Travel Vision</div>',
        unsafe_allow_html=True,
    )

    st.write(
        "Upload a travel image and ask TrekTales to analyze it."
    )

    uploaded_image = st.file_uploader(
        "Upload an image",
        type=SUPPORTED_IMAGE_TYPES,
    )

    vision_question = st.text_input(
        "What would you like to know?",
        value=(
            "Describe this travel scene and suggest what kind "
            "of place or activity it might represent."
        ),
    )

    if uploaded_image:

        st.image(
            uploaded_image,
            caption="Uploaded travel image",
            use_container_width=True,
        )

        if st.button(
            "🔍 Analyze Image",
            use_container_width=True,
        ):

            if not os.getenv("GROQ_API_KEY"):

                try:
                    if "GROQ_API_KEY" in st.secrets:
                        os.environ["GROQ_API_KEY"] = (
                            st.secrets["GROQ_API_KEY"]
                        )
                except Exception:
                    pass

            if not os.getenv("GROQ_API_KEY"):
                st.error("GROQ_API_KEY is missing.")
                st.stop()

            with st.spinner("Analyzing image..."):

                try:

                    result = analyze_travel_image(
                        uploaded_image.getvalue(),
                        uploaded_image.type,
                        vision_question,
                    )

                    st.markdown("### 🔎 Vision Analysis")
                    st.write(result)

                except Exception as exc:

                    st.error(
                        f"Vision analysis failed: {exc}"
                    )


# ============================================================
# PAYMENT
# ============================================================

with tab4:

    render_payment_section()


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        🧭 TrekTales AI · Built with Streamlit, CrewAI,
        Groq and FAISS
        <br>
        © 2026 TrekTales AI
    </div>
    """,
    unsafe_allow_html=True,
)
