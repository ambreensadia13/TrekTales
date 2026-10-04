from pathlib import Path
import html
import re

import streamlit as st

from src.config import (
    FREE_DAYS,
    MAX_TRIP_DAYS,
    UNLOCK_PRICE,
    EXPECTED_PAYMENT_RECIPIENT,
    GROQ_API_KEY,
    FAISS_INDEX_PATH,
    METADATA_PATH,
    CONFIG_PATH,
)
from src.retriever import HybridRetriever
from src.crew import TrekTalesCrew
from src.payment import verify_payment
from src.vision import analyze_payment_screenshot


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="TrekTales — AI Travel Planner",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background:
            linear-gradient(
                135deg,
                rgba(218,44,56,0.08),
                rgba(34,111,84,0.08)
            );
    }

    .hero {
        padding: 2.2rem;
        border-radius: 24px;
        margin-bottom: 1.5rem;
        background: linear-gradient(
            135deg,
            #DA2C38,
            #226F54
        );
        color: white;
        box-shadow: 0 15px 35px rgba(0,0,0,0.18);
    }

    .hero h1 {
        font-size: 3rem;
        margin: 0;
        font-weight: 800;
    }

    .hero p {
        font-size: 1.05rem;
        margin-top: 0.5rem;
        opacity: 0.95;
    }

    .card {
        padding: 1.25rem;
        border-radius: 18px;
        border: 1px solid rgba(128,128,128,0.25);
        background: rgba(255,255,255,0.04);
        margin-bottom: 1rem;
    }

    .status-card {
        padding: 1rem;
        border-radius: 16px;
        border: 1px solid rgba(128,128,128,0.25);
        min-height: 120px;
    }

    .source-card {
        padding: 0.9rem 1rem;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,0.25);
        margin-bottom: 0.6rem;
    }

    .day-card {
        padding: 1.2rem;
        border-radius: 18px;
        border: 1px solid rgba(128,128,128,0.25);
        margin-bottom: 1rem;
    }

    .locked-card {
        padding: 1.3rem;
        border-radius: 18px;
        border: 1px dashed #DA2C38;
        margin-bottom: 1rem;
    }

    .small-muted {
        opacity: 0.72;
        font-size: 0.88rem;
    }

    div.stButton > button {
        border-radius: 12px;
        font-weight: 700;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "trip_result": None,
    "trip_evidence": [],
    "requested_days": 1,
    "accessible_days": 1,
    "payment_verified": False,
    "payment_result": None,
    "vision_result": None,
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# HELPERS
# ============================================================

def clean_display_text(value):
    """Safely clean accidental HTML/code fences from model output."""

    if value is None:
        return ""

    text = str(value)

    text = re.sub(
        r"<[^>]+>",
        "",
        text,
    )

    text = text.replace("```markdown", "")
    text = text.replace("```md", "")
    text = text.replace("```text", "")
    text = text.replace("```", "")

    return text.strip()


def get_retriever():
    """Create the hybrid tourism retriever."""

    return HybridRetriever(
        index_path=FAISS_INDEX_PATH,
        metadata_path=METADATA_PATH,
        config_path=CONFIG_PATH,
    )


def build_retrieval_query(
    destination,
    starting_location,
    requested_days,
    budget,
    travelers,
    travel_style,
    interests,
):
    """Create a deterministic retrieval query."""

    interest_text = ", ".join(interests) if interests else "general tourism"

    return (
        f"Destination: {destination}. "
        f"Starting location: {starting_location}. "
        f"Trip duration: exactly {requested_days} days. "
        f"Budget: {budget}. "
        f"Travelers: {travelers}. "
        f"Travel style: {travel_style}. "
        f"Interests: {interest_text}. "
        "Find relevant places, activities, food, hotels, transport "
        "and safety information from the TrekTales knowledge base."
    )


def format_sources(evidence):
    """Return unique source records from retrieval evidence."""

    sources = []
    seen = set()

    for item in evidence or []:

        if not isinstance(item, dict):
            continue

        metadata = item.get("metadata", {})

        if not isinstance(metadata, dict):
            metadata = {}

        source = (
            metadata.get("source")
            or item.get("source")
            or "Unknown source"
        )

        page = (
            metadata.get("page")
            or item.get("page")
            or "N/A"
        )

        department = (
            metadata.get("department")
            or item.get("department")
            or ""
        )

        record_id = (
            metadata.get("record_id")
            or item.get("record_id")
            or ""
        )

        key = (
            str(source),
            str(page),
            str(record_id),
        )

        if key in seen:
            continue

        seen.add(key)

        sources.append(
            {
                "source": str(source),
                "page": str(page),
                "department": str(department),
                "record_id": str(record_id),
            }
        )

    return sources


def normalize_result(result):
    """Convert the crew response into a displayable string."""

    if result is None:
        return ""

    if isinstance(result, dict):

        for key in (
            "answer",
            "result",
            "output",
            "plan",
            "content",
        ):
            value = result.get(key)

            if value:
                return clean_display_text(value)

    return clean_display_text(result)


def extract_day_sections(text):
    """
    Split a generated itinerary into day sections.

    This is only for presentation.
    The actual day-count enforcement happens before generation.
    """

    if not text:
        return []

    pattern = re.compile(
        r"(?im)(?=^\s*(?:#{1,4}\s*)?(?:day|day\s+)[1-3]\b)"
    )

    sections = pattern.split(text)

    cleaned = []

    for section in sections:

        section = section.strip()

        if not section:
            continue

        match = re.match(
            r"(?is)^(?:#{1,4}\s*)?Day\s+([1-3])\b",
            section,
        )

        if match:
            day_number = int(match.group(1))
            cleaned.append(
                {
                    "day": day_number,
                    "text": section,
                }
            )

    return cleaned


def enforce_display_day_limit(text, requested_days):
    """
    Prevent accidental display of days beyond the requested duration.

    This is a UI safety layer.
    The planner itself also receives the exact day count.
    """

    sections = extract_day_sections(text)

    if not sections:
        return text

    allowed = []

    for section in sections:

        if section["day"] <= requested_days:
            allowed.append(section["text"])

    if not allowed:
        return text

    return "\n\n".join(allowed)


def payment_is_verified():
    return bool(st.session_state.payment_verified)


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="hero">
        <h1>🌿 TrekTales</h1>
        <p>
            AI-powered multi-agent travel planning using a grounded
            tourism knowledge base.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🌿 TrekTales")

    st.caption(
        "Plan trips using the TrekTales tourism knowledge base."
    )

    st.divider()

    st.markdown("### 🔐 Access")

    st.info(
        f"Day 1 is free.\n\n"
        f"Days 2–{MAX_TRIP_DAYS} require a "
        f"Rs. {UNLOCK_PRICE} demo unlock."
    )

    st.divider()

    language = st.selectbox(
        "🌐 Response Language",
        [
            "English",
            "Urdu",
            "Roman Urdu",
        ],
    )

    travel_style = st.selectbox(
        "🎒 Travel Style",
        [
            "Balanced",
            "Budget",
            "Family",
            "Adventure",
            "Relaxed",
            "Cultural",
        ],
    )

    interests = st.multiselect(
        "❤️ Interests",
        [
            "Historical places",
            "Food",
            "Nature",
            "Sports",
            "Shopping",
            "Family activities",
            "Adventure",
            "Photography",
        ],
        default=[
            "Historical places",
            "Food",
        ],
    )

    st.divider()

    st.markdown("### 🤖 AI Architecture")

    st.caption("1. Master Orchestrator")
    st.caption("2. Knowledge Agent")
    st.caption("3. Planner Agent")
    st.caption("4. Budget Agent")
    st.caption("5. Safety Agent")
    st.caption("6. Summarizer Agent")
    st.caption("7. Payment Agent")
    st.caption("8. Vision Agent")


# ============================================================
# INPUT
# ============================================================

st.markdown("## 🧭 Create Your Trip")

col1, col2 = st.columns(2)

with col1:

    starting_location = st.text_input(
        "📍 Starting Location",
        placeholder="e.g. Islamabad",
    )

with col2:

    destination = st.text_input(
        "📌 Destination",
        value="Rawalpindi",
        placeholder="e.g. Rawalpindi",
    )


col3, col4, col5 = st.columns(3)

with col3:

    requested_days = st.number_input(
        "📅 Number of Days",
        min_value=1,
        max_value=MAX_TRIP_DAYS,
        value=1,
        step=1,
    )

with col4:

    travelers = st.number_input(
        "👥 Travelers",
        min_value=1,
        max_value=20,
        value=2,
        step=1,
    )

with col5:

    budget = st.number_input(
        "💰 Budget (Rs.)",
        min_value=0,
        value=15000,
        step=1000,
    )


st.caption(
    f"Day 1 is free. "
    f"Days {FREE_DAYS + 1}–{MAX_TRIP_DAYS} require "
    f"the Rs. {UNLOCK_PRICE} demo unlock."
)


# ============================================================
# STATUS
# ============================================================

st.markdown("## 🔎 System Status")

status_col1, status_col2, status_col3 = st.columns(3)

with status_col1:

    with st.container(
        border=True,
    ):

        st.markdown("### 🧠 Groq")

        if GROQ_API_KEY:
            st.success("API key detected")
        else:
            st.error("GROQ_API_KEY missing")


with status_col2:

    with st.container(
        border=True,
    ):

        st.markdown("### 📚 FAISS")

        if (
            FAISS_INDEX_PATH.exists()
            and METADATA_PATH.exists()
        ):
            st.success("Knowledge base ready")
        else:
            st.error("FAISS files not found")


with status_col3:

    with st.container(
        border=True,
    ):

        st.markdown("### 🤖 Agents")

        st.success("8-agent architecture ready")


# ============================================================
# GENERATE BUTTON
# ============================================================

generate_trip = st.button(
    "🚀 Generate TrekTales Plan",
    type="primary",
    use_container_width=True,
)


if generate_trip:

    # --------------------------------------------------------
    # INPUT VALIDATION
    # --------------------------------------------------------

    if not GROQ_API_KEY:
        st.error(
            "GROQ_API_KEY is missing. "
            "Add it to Streamlit Secrets."
        )
        st.stop()

    if not destination.strip():
        st.error(
            "Please enter a destination."
        )
        st.stop()

    if not starting_location.strip():
        st.error(
            "Please enter a starting location."
        )
        st.stop()

    requested_days = int(requested_days)

    if requested_days < 1:
        requested_days = 1

    if requested_days > MAX_TRIP_DAYS:
        requested_days = MAX_TRIP_DAYS

    # --------------------------------------------------------
    # ACCESS CONTROL
    # --------------------------------------------------------

    accessible_days = FREE_DAYS

    if requested_days > FREE_DAYS:

        if not payment_is_verified():

            st.session_state.requested_days = requested_days
            st.session_state.accessible_days = FREE_DAYS

            st.warning(
                f"🔐 Your requested trip is {requested_days} days. "
                f"Day 1 is free, but Days "
                f"{FREE_DAYS + 1}–{requested_days} are locked."
            )

            st.info(
                f"Complete the Rs. {UNLOCK_PRICE} demo payment "
                f"verification below to unlock the additional days."
            )

            st.stop()

        accessible_days = requested_days

    else:
        accessible_days = requested_days

    # --------------------------------------------------------
    # RESET
    # --------------------------------------------------------

    st.session_state.trip_result = None
    st.session_state.trip_evidence = []
    st.session_state.requested_days = requested_days
    st.session_state.accessible_days = accessible_days

    # --------------------------------------------------------
    # RETRIEVAL
    # --------------------------------------------------------

    with st.status(
        "🔎 Preparing your TrekTales trip...",
        expanded=True,
    ) as status:

        st.write(
            "📚 Loading the tourism knowledge base..."
        )

        try:

            retriever = get_retriever()

            query = build_retrieval_query(
                destination=destination.strip(),
                starting_location=starting_location.strip(),
                requested_days=accessible_days,
                budget=budget,
                travelers=travelers,
                travel_style=travel_style,
                interests=interests,
            )

            evidence = retriever.search(
                query,
                top_k=8,
            )

            st.session_state.trip_evidence = evidence

            st.write(
                f"Retrieved {len(evidence)} relevant knowledge records."
            )

        except Exception as exc:

            status.update(
                label="❌ Knowledge base error",
                state="error",
            )

            st.error(
                "The TrekTales knowledge base could not be loaded."
            )

            st.exception(exc)
            st.stop()

        # ----------------------------------------------------
        # NO-EVIDENCE SAFETY
        # ----------------------------------------------------

        if not evidence:

            status.update(
                label="⚠️ No supporting tourism information found",
                state="error",
            )

            st.warning(
                "TrekTales could not find supporting information "
                "for this request in its knowledge base."
            )

            st.info(
                "No itinerary was generated because the app is "
                "configured not to invent tourism information."
            )

            st.stop()

        # ----------------------------------------------------
        # MULTI-AGENT PLANNER
        # ----------------------------------------------------

        st.write(
            "🤖 Activating the TrekTales multi-agent planner..."
        )

        try:

            crew = TrekTalesCrew()

            result = crew.run(
                destination=destination.strip(),
                starting_location=starting_location.strip(),
                days=accessible_days,
                budget=float(budget),
                travelers=int(travelers),
                travel_style=travel_style,
                language=language,
                interests=interests,
                evidence=evidence,
            )

            if not result:
                raise RuntimeError(
                    "The AI planner returned an empty result."
                )

            st.session_state.trip_result = result

            status.update(
                label="✅ TrekTales plan generated",
                state="complete",
                expanded=False,
            )

        except Exception as exc:

            status.update(
                label="❌ Trip generation failed",
                state="error",
                expanded=True,
            )

            st.error(
                "The TrekTales planner could not complete the request."
            )

            st.exception(exc)

            st.stop()


# ============================================================
# DISPLAY RESULT
# ============================================================

if st.session_state.trip_result:

    st.divider()

    st.markdown("## 🗺️ Your TrekTales Plan")

    answer = normalize_result(
        st.session_state.trip_result
    )

    answer = enforce_display_day_limit(
        answer,
        st.session_state.accessible_days,
    )

    if not answer:

        st.warning(
            "No itinerary content was returned."
        )

    else:

        with st.container(
            border=True,
        ):

            st.markdown(
                "### 🌿 Personalized Itinerary"
            )

            st.markdown(
                answer,
                unsafe_allow_html=False,
            )


    # ========================================================
    # SOURCES
    # ========================================================

    sources = format_sources(
        st.session_state.trip_evidence
    )

    if sources:

        st.markdown("## 📚 Knowledge Sources")

        for index, source in enumerate(
            sources,
            start=1,
        ):

            with st.container(
                border=True,
            ):

                source_name = html.escape(
                    source["source"]
                )

                page = html.escape(
                    source["page"]
                )

                department = html.escape(
                    source["department"]
                )

                record_id = html.escape(
                    source["record_id"]
                )

                st.markdown(
                    f"**📄 {source_name}**"
                )

                if page:
                    st.caption(
                        f"Page: {page}"
                    )

                if department:
                    st.caption(
                        f"Category: {department}"
                    )

                if record_id:
                    st.caption(
                        f"Record: {record_id}"
                    )


# ============================================================
# PAYMENT SECTION
# ============================================================

if not payment_is_verified():

    st.divider()

    with st.container(
        border=True,
    ):

        st.markdown("## 🔐 Unlock Days 2–3")

        st.markdown(
            f"""
            Day 1 is free.

            To unlock additional itinerary days, complete the
            **Rs. {UNLOCK_PRICE} demo payment** to:

            **{EXPECTED_PAYMENT_RECIPIENT}**
            """
        )

        qr_path = (
            Path(__file__).resolve().parent
            / "assets"
            / "jazzcash_qr.jpg"
        )

        if qr_path.exists():

            st.image(
                str(qr_path),
                width=250,
                caption="Demo payment QR",
            )

        st.caption(
            "Upload a payment screenshot after completing "
            "the demo payment."
        )

        payment_file = st.file_uploader(
            "📸 Upload Payment Screenshot",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp",
            ],
            key="payment_upload",
        )

        verify_button = st.button(
            "🔍 Analyze & Verify Payment",
            use_container_width=True,
        )

        if verify_button:

            if payment_file is None:

                st.warning(
                    "Please upload a payment screenshot first."
                )

            else:

                with st.spinner(
                    "Analyzing payment screenshot..."
                ):

                    try:

                        image_bytes = payment_file.getvalue()

                        vision_result = analyze_payment_screenshot(
                            image_bytes
                        )

                        st.session_state.vision_result = (
                            vision_result
                        )

                        recipient = str(
                            vision_result.get(
                                "recipient",
                                "",
                            )
                        ).strip()

                        amount = vision_result.get(
                            "amount",
                            0,
                        )

                        payment_status = str(
                            vision_result.get(
                                "status",
                                "",
                            )
                        ).strip()

                        payment_data = {
                            "recipient": recipient,
                            "amount": amount,
                            "status": payment_status,
                        }

                        payment_result = verify_payment(
                            payment_data
                        )

                        st.session_state.payment_result = (
                            payment_result
                        )

                        verified = bool(
                            payment_result.get(
                                "verified",
                                False,
                            )
                        )

                        st.session_state.payment_verified = (
                            verified
                        )

                        if verified:

                            st.success(
                                "✅ Payment verified successfully."
                            )

                            st.info(
                                "Days 2–3 are now unlocked for this "
                                "current app session."
                            )

                        else:

                            st.error(
                                "❌ Payment could not be verified."
                            )

                            st.warning(
                                "The recipient, amount and payment "
                                "status did not satisfy the required "
                                "demo verification rules."
                            )

                    except Exception as exc:

                        st.error(
                            "Payment screenshot verification failed."
                        )

                        st.exception(exc)


# ============================================================
# PAYMENT RESULT DETAILS
# ============================================================

if st.session_state.vision_result:

    st.divider()

    with st.container(
        border=True,
    ):

        st.markdown(
            "### 🔎 Payment Analysis"
        )

        vision = st.session_state.vision_result

        st.write(
            f"Recipient: "
            f"{vision.get('recipient', 'Not detected')}"
        )

        st.write(
            f"Amount: "
            f"{vision.get('amount', 'Not detected')}"
        )

        st.write(
            f"Status: "
            f"{vision.get('status', 'Not detected')}"
        )

        if vision.get("confidence"):
            st.write(
                f"AI confidence: "
                f"{vision.get('confidence')}"
            )


# ============================================================
# DISCLAIMER
# ============================================================

st.divider()

with st.container(
    border=True,
):

    st.markdown(
        """
        **Important:** TrekTales is a tourism planning
        demonstration application. Its tourism knowledge base
        contains demonstration data and should not be treated as
        live booking, pricing, weather, transport or safety data.

        Always verify important travel information with current
        official or local sources before travelling.
        """
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

footer1, footer2, footer3 = st.columns(3)

with footer1:
    st.caption("🌿 TrekTales")

with footer2:
    st.caption("AI Multi-Agent Travel Planner")

with footer3:
    st.caption("Powered by Groq + FAISS")
