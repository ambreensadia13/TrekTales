from pathlib import Path
import json
import re
import importlib

import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="TrekTales",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# COLORS
# ============================================================

RED = "#DA2C38"
GREEN = "#226F54"
LIGHT_GREEN = "#87C38F"
CREAM = "#F4F1DE"
DARK = "#17201B"
BROWN = "#6B4F3A"
WHITE = "#FFFFFF"


# ============================================================
# ROOT PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent

FAISS_DIR = ROOT_DIR / "faiss_db"

FAISS_INDEX_PATH = FAISS_DIR / "index.faiss"
METADATA_PATH = FAISS_DIR / "metadata.json"
CONFIG_PATH = FAISS_DIR / "config.json"

ASSETS_DIR = ROOT_DIR / "assets"
QR_PATH = ASSETS_DIR / "jazzcash_qr.jpg"

KNOWLEDGE_BASE_DIR = ROOT_DIR / "tourism_knowledge_base"


# ============================================================
# DEFAULT SETTINGS
# ============================================================

FREE_DAYS = 1
PAID_DAYS = 3
UNLOCK_PRICE = 199

DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"
DEFAULT_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


# ============================================================
# STREAMLIT SECRETS
# ============================================================

def get_secret(name, default=""):
    try:
        value = st.secrets.get(name, default)

        if value is None:
            return default

        return str(value).strip()

    except Exception:
        return default


GROQ_API_KEY = get_secret("GROQ_API_KEY")
GROQ_MODEL = get_secret("GROQ_MODEL", DEFAULT_GROQ_MODEL)
GROQ_BASE_URL = get_secret(
    "GROQ_BASE_URL",
    "https://api.groq.com/openai/v1",
)

VISION_MODEL = get_secret(
    "VISION_MODEL",
    DEFAULT_VISION_MODEL,
)


# ============================================================
# OPTIONAL CONFIG IMPORT
# ============================================================

def load_optional_config():
    try:
        module = importlib.import_module("src.config")
        return module
    except Exception:
        return None


CONFIG_MODULE = load_optional_config()


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_SESSION_STATE = {
    "payment_verified": False,
    "trip_result": None,
    "trip_evidence": [],
    "payment_result": None,
    "vision_result": None,
    "last_error": None,
}

for key, value in DEFAULT_SESSION_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# CSS
# ============================================================

st.markdown(
    f"""
<style>

html, body, [class*="css"] {{
    font-family: Arial, sans-serif;
}}

.stApp {{
    background:
        linear-gradient(
            135deg,
            #f4f1de 0%,
            #ffffff 48%,
            #edf7ef 100%
        );
}}

[data-testid="stSidebar"] {{
    background: linear-gradient(
        180deg,
        {DARK},
        #20382b
    );
}}

[data-testid="stSidebar"] * {{
    color: white !important;
}}

.hero {{
    padding: 30px;
    border-radius: 24px;
    background:
        linear-gradient(
            135deg,
            #17201b,
            #226f54
        );
    color: white;
    margin-bottom: 25px;
    box-shadow: 0 12px 35px rgba(0,0,0,0.12);
}}

.hero h1 {{
    margin-bottom: 8px;
    font-size: 42px;
}}

.hero p {{
    font-size: 17px;
    margin-bottom: 0;
    opacity: 0.95;
}}

.section-card {{
    background: rgba(255,255,255,0.92);
    padding: 22px;
    border-radius: 18px;
    border: 1px solid rgba(34,111,84,0.14);
    box-shadow: 0 8px 25px rgba(0,0,0,0.06);
    margin-bottom: 18px;
}}

.answer-card {{
    background: #ffffff;
    padding: 28px;
    border-radius: 20px;
    border: 1px solid #dfe9e2;
    box-shadow: 0 10px 30px rgba(0,0,0,0.07);
}}

.answer-card h1 {{
    color: #17201b;
}}

.answer-card h2 {{
    color: #226f54;
    margin-top: 30px;
}}

.answer-card h3 {{
    color: #6b4f3a;
}}

.answer-card p,
.answer-card li,
.answer-card td,
.answer-card th {{
    color: #17201b;
}}

.answer-card table {{
    width: 100%;
}}

.locked-card {{
    background: #fff7e6;
    border: 1px solid #e6c878;
    padding: 20px;
    border-radius: 18px;
    margin-top: 15px;
}}

.status-good {{
    color: #226f54;
    font-weight: 700;
}}

.status-bad {{
    color: #da2c38;
    font-weight: 700;
}}

.source-card {{
    background: #f6faf7;
    border-left: 4px solid #226f54;
    padding: 12px 15px;
    border-radius: 8px;
    margin-bottom: 8px;
}}

.small-muted {{
    color: #65736b;
    font-size: 13px;
}}

.stButton > button {{
    border-radius: 12px;
    font-weight: 700;
}}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SAFE TEXT CLEANER
# ============================================================

def clean_text(text):
    """
    Removes accidental HTML/code-fence artifacts while
    preserving Markdown headings, bullets, tables and emphasis.
    """

    if text is None:
        return ""

    text = str(text).strip()

    # Remove script blocks.
    text = re.sub(
        r"<script\b[^>]*>.*?</script>",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Remove style blocks.
    text = re.sub(
        r"<style\b[^>]*>.*?</style>",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Remove only common accidental presentation HTML.
    text = re.sub(
        r"</?(?:div|span|p|br|strong|em|b|i|ul|ol|li|"
        r"h1|h2|h3|h4|h5|h6)[^>]*>",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # Remove Markdown code fences only.
    text = re.sub(
        r"```(?:markdown|md|text)?",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = text.replace("```", "")

    return text.strip()


# ============================================================
# SAFE IMPORT HELPERS
# ============================================================

def safe_import_retriever():
    """
    Tries common retriever module/class names used by TrekTales.
    """

    candidates = [
        ("src.retriever", "TourismRetriever"),
        ("src.retriever", "Retriever"),
        ("src.retriever", "TrekTalesRetriever"),
        ("src.rag", "TourismRetriever"),
        ("src.rag", "Retriever"),
    ]

    errors = []

    for module_name, class_name in candidates:
        try:
            module = importlib.import_module(module_name)
            cls = getattr(module, class_name)

            try:
                return cls(
                    index_path=str(FAISS_INDEX_PATH),
                    metadata_path=str(METADATA_PATH),
                )
            except TypeError:
                try:
                    return cls(
                        str(FAISS_INDEX_PATH),
                        str(METADATA_PATH),
                    )
                except TypeError:
                    return cls()

        except Exception as exc:
            errors.append(
                f"{module_name}.{class_name}: {exc}"
            )

    raise RuntimeError(
        "Could not initialize the tourism retriever.\n\n"
        + "\n".join(errors)
    )


def safe_import_crew():
    try:
        module = importlib.import_module("src.crew")

        cls = getattr(module, "TrekTalesCrew", None)

        if cls is None:
            raise RuntimeError(
                "TrekTalesCrew was not found in src/crew.py."
            )

        return cls()

    except Exception as exc:
        raise RuntimeError(
            f"Could not load TrekTales AI crew: {exc}"
        ) from exc


def safe_import_vision():
    candidates = [
        ("src.vision", "analyze_payment_screenshot"),
        ("src.vision", "analyze_payment"),
    ]

    errors = []

    for module_name, function_name in candidates:
        try:
            module = importlib.import_module(module_name)
            function = getattr(module, function_name)
            return function
        except Exception as exc:
            errors.append(
                f"{module_name}.{function_name}: {exc}"
            )

    raise RuntimeError(
        "Payment vision analyzer could not be loaded.\n\n"
        + "\n".join(errors)
    )


# ============================================================
# RESULT EXTRACTION
# ============================================================

def extract_text_from_result(result):
    if result is None:
        return ""

    if isinstance(result, str):
        return result

    if isinstance(result, dict):
        for key in [
            "output",
            "result",
            "response",
            "answer",
            "content",
            "text",
        ]:
            value = result.get(key)

            if value:
                return str(value)

    for attribute in [
        "output",
        "result",
        "response",
        "answer",
        "content",
        "text",
        "raw",
    ]:
        try:
            value = getattr(result, attribute, None)

            if value:
                return str(value)

        except Exception:
            pass

    return str(result)


# ============================================================
# EVIDENCE EXTRACTION
# ============================================================

def extract_sources(evidence):
    sources = []

    if not evidence:
        return sources

    for item in evidence:

        source = ""

        if isinstance(item, dict):

            metadata = item.get("metadata", {})

            if not isinstance(metadata, dict):
                metadata = {}

            source = (
                item.get("source")
                or item.get("document")
                or item.get("filename")
                or metadata.get("source")
                or metadata.get("document")
                or metadata.get("filename")
                or ""
            )

        else:

            try:
                metadata = getattr(item, "metadata", {}) or {}

                source = (
                    getattr(item, "source", "")
                    or metadata.get("source", "")
                    or metadata.get("filename", "")
                )

            except Exception:
                source = ""

        if source:

            source = str(source).replace("\\", "/")
            source = source.split("/")[-1]

            source = re.sub(
                r"\.html?$",
                "",
                source,
                flags=re.IGNORECASE,
            )

            if source and source not in sources:
                sources.append(source)

    return sources


# ============================================================
# RETRIEVER RESULT NORMALIZATION
# ============================================================

def normalize_retriever_result(result):

    if result is None:
        return []

    if isinstance(result, dict):

        for key in [
            "results",
            "documents",
            "chunks",
            "evidence",
            "matches",
        ]:
            value = result.get(key)

            if isinstance(value, list):
                return value

        return [result]

    if isinstance(result, (list, tuple)):
        return list(result)

    try:
        return list(result)
    except Exception:
        return [result]


# ============================================================
# RETRIEVAL
# ============================================================

def retrieve_with_retriever(
    retriever,
    query,
    top_k=6,
):

    methods = [
        "search",
        "retrieve",
        "query",
    ]

    last_error = None

    for method_name in methods:

        method = getattr(
            retriever,
            method_name,
            None,
        )

        if not callable(method):
            continue

        try:

            try:
                result = method(
                    query,
                    top_k=top_k,
                )

            except TypeError:

                try:
                    result = method(
                        query,
                        k=top_k,
                    )

                except TypeError:
                    result = method(query)

            return normalize_retriever_result(result)

        except Exception as exc:
            last_error = exc

    if last_error:
        raise RuntimeError(
            f"Tourism retrieval failed: {last_error}"
        )

    raise RuntimeError(
        "The tourism retriever does not provide "
        "a supported search/retrieve/query method."
    )


# ============================================================
# CREW EXECUTION
# ============================================================

def run_crew(
    crew,
    destination,
    starting_location,
    duration,
    travelers,
    budget,
    travel_style,
    interests,
    language,
    evidence,
):

    kwargs = {
        "destination": destination,
        "starting_location": starting_location,
        "duration": duration,
        "days": duration,
        "travelers": travelers,
        "budget": budget,
        "travel_style": travel_style,
        "interests": interests,
        "language": language,
        "evidence": evidence,
        "knowledge": evidence,
    }

    methods = [
        "run",
        "generate",
        "plan",
        "kickoff",
    ]

    last_error = None

    for method_name in methods:

        method = getattr(
            crew,
            method_name,
            None,
        )

        if not callable(method):
            continue

        try:
            result = method(**kwargs)

            if result is not None:
                return result

        except TypeError as exc:

            last_error = exc

            # Try a simpler argument set for older versions.
            try:

                result = method(
                    destination=destination,
                    starting_location=starting_location,
                    duration=duration,
                    travelers=travelers,
                    budget=budget,
                    travel_style=travel_style,
                    interests=interests,
                    language=language,
                    evidence=evidence,
                )

                if result is not None:
                    return result

            except Exception as inner_exc:
                last_error = inner_exc

        except Exception as exc:
            last_error = exc

    if last_error:
        raise RuntimeError(
            f"TrekTales AI generation failed: {last_error}"
        )

    raise RuntimeError(
        "No supported generation method was found in src/crew.py."
    )


# ============================================================
# PAYMENT HELPERS
# ============================================================

def run_payment_vision(uploaded_file):

    analyzer = safe_import_vision()

    try:
        return analyzer(
            uploaded_file,
            api_key=GROQ_API_KEY,
            model=VISION_MODEL,
        )

    except TypeError:

        try:
            return analyzer(
                uploaded_file,
                GROQ_API_KEY,
                VISION_MODEL,
            )

        except TypeError:

            return analyzer(uploaded_file)


def verify_payment_result(result):

    if result is None:
        return False

    if isinstance(result, bool):
        return result

    if isinstance(result, dict):

        for key in [
            "verified",
            "is_verified",
            "valid",
            "success",
            "payment_verified",
        ]:
            value = result.get(key)

            if isinstance(value, bool):
                return value

    text = extract_text_from_result(result).lower()

    positive_terms = [
        "payment verified",
        "verified payment",
        "payment successful",
        "successful payment",
        "transaction verified",
    ]

    return any(
        term in text
        for term in positive_terms
    )


# ============================================================
# DAY VALIDATION
# ============================================================

def validate_requested_days(value):

    try:
        value = int(value)
    except Exception:
        return 1

    return max(
        1,
        min(PAID_DAYS, value),
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div style="
            text-align:center;
            padding:10px 0 20px 0;
        ">
            <div style="
                font-size:42px;
            ">🌿</div>

            <h2 style="
                margin:0;
            ">TrekTales</h2>

            <p style="
                opacity:0.8;
                font-size:13px;
            ">
                Knowledge-Grounded AI Travel Planner
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🔐 Access")

    if st.session_state.payment_verified:
        st.success("Premium access unlocked")
    else:
        st.info(
            f"Free preview: {FREE_DAYS} day"
        )

    st.markdown("---")

    st.markdown("### 🌐 Language")

    language = st.selectbox(
        "Response language",
        [
            "English",
            "Urdu",
            "Roman Urdu",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")

    st.markdown("### 🤖 TrekTales AI System")

    agents = [
        "Master Orchestrator",
        "Knowledge Agent",
        "Planner Agent",
        "Budget Agent",
        "Safety Agent",
        "Summarizer Agent",
        "Payment Agent",
        "Vision Agent",
    ]

    for number, agent in enumerate(agents, 1):

        st.markdown(
            f"""
            <div style="
                padding:5px 0;
                font-size:13px;
            ">
                <b>{number}.</b> {agent}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    st.markdown("### ⚙️ System Status")

    if GROQ_API_KEY:
        st.markdown(
            '<span class="status-good">● Groq API key configured</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="status-bad">● Groq API key missing</span>',
            unsafe_allow_html=True,
        )

    if FAISS_INDEX_PATH.exists():
        st.markdown(
            '<span class="status-good">● FAISS index found</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="status-bad">● FAISS index not found</span>',
            unsafe_allow_html=True,
        )

    if METADATA_PATH.exists():
        st.markdown(
            '<span class="status-good">● Metadata found</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="status-bad">● Metadata not found</span>',
            unsafe_allow_html=True,
        )


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="hero">

        <h1>🌿 TrekTales</h1>

        <p>
            Personalized travel itineraries generated from
            your tourism knowledge base.
        </p>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# TRIP INPUTS
# ============================================================

st.markdown("## 🧭 Plan Your Journey")

col1, col2 = st.columns(2)

with col1:

    destination = st.text_input(
        "📍 Destination",
        value="Rawalpindi",
    )

    starting_location = st.text_input(
        "🚗 Starting Location",
        placeholder="e.g. Sibbi",
    )

    duration = st.selectbox(
        "📅 Trip Duration",
        [1, 2, 3],
        index=0,
        format_func=lambda x: (
            f"{x} Day" if x == 1 else f"{x} Days"
        ),
    )

    travelers = st.number_input(
        "👥 Travelers",
        min_value=1,
        max_value=20,
        value=2,
        step=1,
    )


with col2:

    budget = st.selectbox(
        "💰 Budget",
        [
            "Budget",
            "Moderate",
            "Premium",
        ],
    )

    travel_style = st.selectbox(
        "🌿 Travel Style",
        [
            "Balanced",
            "Adventure",
            "Relaxed",
            "Family",
            "Cultural",
            "Nature",
            "Photography",
        ],
    )

    interests = st.multiselect(
        "🎯 Interests",
        [
            "Historical Places",
            "Parks",
            "Nature",
            "Food",
            "Photography",
            "Culture",
            "Family Activities",
            "Adventure",
            "Shopping",
        ],
        default=[],
    )


# ============================================================
# FREE / PREMIUM ACCESS
# ============================================================

requested_duration = validate_requested_days(duration)

if st.session_state.payment_verified:

    accessible_duration = requested_duration

else:

    accessible_duration = min(
        requested_duration,
        FREE_DAYS,
    )


if (
    not st.session_state.payment_verified
    and requested_duration > FREE_DAYS
):

    st.markdown(
        f"""
        <div class="locked-card">

        <h3>🔒 Premium itinerary</h3>

        <p>
        Your current free access generates
        <b>Day 1 only</b>.
        </p>

        <p>
        Unlock premium access for
        <b>Rs. {UNLOCK_PRICE}</b>
        to generate up to
        <b>{PAID_DAYS} days</b>.
        </p>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# GENERATE BUTTON
# ============================================================

st.markdown("")

generate = st.button(
    "🌿 Generate My TrekTales Itinerary",
    type="primary",
    use_container_width=True,
)


# ============================================================
# GENERATION
# ============================================================

if generate:

    st.session_state.last_error = None
    st.session_state.trip_result = None
    st.session_state.trip_evidence = []

    if not GROQ_API_KEY:

        st.session_state.last_error = (
            "GROQ_API_KEY is missing from Streamlit Secrets."
        )

    elif not destination.strip():

        st.session_state.last_error = (
            "Please enter a destination."
        )

    elif not starting_location.strip():

        st.session_state.last_error = (
            "Please enter your starting location."
        )

    elif not FAISS_INDEX_PATH.exists():

        st.session_state.last_error = (
            "FAISS index not found. "
            "Please create the tourism knowledge base "
            "and FAISS index before generating a trip."
        )

    elif not METADATA_PATH.exists():

        st.session_state.last_error = (
            "FAISS metadata.json was not found."
        )

    else:

        try:

            progress = st.progress(0)

            status = st.empty()

            status.info(
                "Loading the tourism knowledge base..."
            )

            progress.progress(20)

            # ------------------------------------------------
            # RETRIEVER
            # ------------------------------------------------

            retriever = safe_import_retriever()

            query_parts = [
                f"Destination: {destination}",
                f"Starting location: {starting_location}",
                f"Duration: {accessible_duration} days",
                f"Travelers: {travelers}",
                f"Budget: {budget}",
                f"Travel style: {travel_style}",
            ]

            if interests:
                query_parts.append(
                    "Interests: "
                    + ", ".join(interests)
                )

            retrieval_query = "\n".join(
                query_parts
            )

            evidence = retrieve_with_retriever(
                retriever,
                retrieval_query,
                top_k=6,
            )

            st.session_state.trip_evidence = evidence

            progress.progress(45)

            status.info(
                f"Retrieved {len(evidence)} "
                "knowledge items."
            )

            if not evidence:

                raise RuntimeError(
                    "No tourism knowledge-base evidence "
                    "was retrieved for this request. "
                    "The itinerary was not generated "
                    "because TrekTales does not invent "
                    "missing tourism facts."
                )

            # ------------------------------------------------
            # CREW
            # ------------------------------------------------

            status.info(
                "🤖 Activating TrekTales AI agents..."
            )

            crew = safe_import_crew()

            progress.progress(65)

            result = run_crew(
                crew=crew,
                destination=destination,
                starting_location=starting_location,
                duration=accessible_duration,
                travelers=travelers,
                budget=budget,
                travel_style=travel_style,
                interests=interests,
                language=language,
                evidence=evidence,
            )

            answer = clean_text(
                extract_text_from_result(result)
            )

            progress.progress(100)

            if not answer:

                raise RuntimeError(
                    "The AI returned an empty itinerary."
                )

            st.session_state.trip_result = answer

            status.success(
                "TrekTales itinerary generated."
            )

        except Exception as exc:

            st.session_state.last_error = str(exc)

            progress.empty()
            status.empty()


# ============================================================
# ERROR DISPLAY
# ============================================================

if st.session_state.last_error:

    st.error(
        "❌ Trip generation failed"
    )

    st.code(
        st.session_state.last_error,
        language="text",
    )


# ============================================================
# ITINERARY OUTPUT
# ============================================================

if st.session_state.trip_result:

    st.divider()

    answer = clean_text(
        st.session_state.trip_result
    )

    # IMPORTANT:
    # Do NOT add another title or heading here.
    # crew.py is responsible for the complete Markdown
    # itinerary structure.

    with st.container(
        border=True,
    ):

        st.markdown(
            answer,
            unsafe_allow_html=False,
        )


# ============================================================
# KNOWLEDGE SOURCES
# ============================================================

if st.session_state.trip_result:

    sources = extract_sources(
        st.session_state.trip_evidence
    )

    # Only show this supplementary section if the generated
    # answer itself does not already contain a KB source section.

    answer_lower = (
        st.session_state.trip_result.lower()
    )

    has_embedded_sources = (
        "knowledge-base sources" in answer_lower
        or "knowledge base sources" in answer_lower
    )

    if sources and not has_embedded_sources:

        st.markdown("---")

        st.markdown(
            "### 📚 Knowledge Sources"
        )

        for source in sources:

            st.markdown(
                f"""
                <div class="source-card">
                    📄 {source}
                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# PREMIUM PAYMENT
# ============================================================

if not st.session_state.payment_verified:

    st.divider()

    st.markdown(
        "## 🔓 Unlock Premium"
    )

    st.markdown(
        f"""
        <div class="section-card">

        <h3>Premium Access — Rs. {UNLOCK_PRICE}</h3>

        <p>
        Premium access allows TrekTales to generate
        up to {PAID_DAYS} days instead of the
        {FREE_DAYS}-day free preview.
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
                caption="JazzCash Payment QR",
                use_container_width=True,
            )

        else:

            st.warning(
                "Payment QR image was not found."
            )

    with payment_col2:

        st.markdown(
            "### 📤 Upload Payment Screenshot"
        )

        payment_file = st.file_uploader(
            "Upload your payment screenshot",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp",
            ],
            key="payment_upload",
        )

        verify_button = st.button(
            "🔎 Verify Payment",
            use_container_width=True,
        )

        if verify_button:

            if payment_file is None:

                st.warning(
                    "Please upload a payment screenshot first."
                )

            elif not GROQ_API_KEY:

                st.error(
                    "GROQ_API_KEY is missing."
                )

            else:

                try:

                    with st.spinner(
                        "Analyzing payment screenshot..."
                    ):

                        vision_result = run_payment_vision(
                            payment_file
                        )

                    st.session_state.vision_result = (
                        vision_result
                    )

                    verified = verify_payment_result(
                        vision_result
                    )

                    if verified:

                        st.session_state.payment_verified = True

                        st.session_state.payment_result = (
                            vision_result
                        )

                        st.success(
                            "✅ Payment verified. "
                            "Premium access is unlocked."
                        )

                        st.rerun()

                    else:

                        st.error(
                            "❌ Payment could not be verified."
                        )

                        st.info(
                            "Only a verified payment result "
                            "can unlock premium access."
                        )

                except Exception as exc:

                    st.error(
                        "Payment verification failed."
                    )

                    st.code(
                        str(exc),
                        language="text",
                    )


# ============================================================
# DISCLAIMER
# ============================================================

st.divider()

st.markdown(
    """
    <div class="section-card">

    <h4>⚠️ TrekTales Information Notice</h4>

    <p>
    TrekTales generates travel plans from its tourism
    knowledge base. If a destination fact, price,
    distance, route, restaurant, opening time, or other
    detail is not available in the knowledge base,
    the system should explicitly state that the
    information is unavailable instead of guessing.
    </p>

    <p>
    Always independently verify current prices,
    opening hours, transport availability, weather,
    safety conditions, and other time-sensitive
    information before travelling.
    </p>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div style="
        text-align:center;
        padding:25px 0;
        color:#65736b;
        font-size:13px;
    ">
        🌿 TrekTales · Knowledge-Grounded AI Travel Planner
    </div>
    """,
    unsafe_allow_html=True,
)
