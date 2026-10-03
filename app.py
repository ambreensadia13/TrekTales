from pathlib import Path

import streamlit as st

from src.config import (
    APP_NAME,
    APP_TAGLINE,
    EXPECTED_PAYMENT_RECIPIENT,
    FAISS_INDEX_PATH,
    FREE_DAYS,
    MAX_PAYMENT_IMAGE_MB,
    PAID_DAYS,
    QR_PATH,
    UNLOCK_PRICE,
    validate_configuration,
)

from src.retriever import HybridRetriever
from src.citations import (
    evidence_to_prompt,
    format_citations,
)

from src.crew import TrekTalesCrew

from src.vision import analyze_payment_screenshot
from src.payment import validate_payment


# ---------------------------------------------------------
# PAGE
# ---------------------------------------------------------

st.set_page_config(
    page_title="TrekTales AI",
    page_icon="🥾",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------
# CSS
# ---------------------------------------------------------

st.markdown(
    """
<style>

.stApp {
    background:
        linear-gradient(
            135deg,
            #f4f0bb 0%,
            #ffffff 38%,
            #e9f5ef 100%
        );
}

.main-title {
    font-size: 3.1rem;
    font-weight: 900;
    color: #43291f;
    margin-bottom: 0.2rem;
}

.subtitle {
    font-size: 1.1rem;
    color: #226f54;
    margin-bottom: 1.5rem;
}

.agent-card {
    background: rgba(255,255,255,0.85);
    border: 1px solid rgba(67,41,31,0.12);
    border-radius: 16px;
    padding: 14px;
    margin-bottom: 10px;
}

.agent-title {
    color: #43291f;
    font-weight: 800;
}

.answer-card {
    background: white;
    border-radius: 20px;
    padding: 28px;
    border-left: 6px solid #da2c38;
    box-shadow: 0 8px 30px rgba(67,41,31,0.08);
}

.source-card {
    background: #f8faf8;
    border: 1px solid #87c38f;
    border-radius: 12px;
    padding: 12px;
    margin-bottom: 8px;
}

.lock-card {
    background: linear-gradient(
        135deg,
        #43291f,
        #226f54
    );
    color: white;
    border-radius: 18px;
    padding: 24px;
    margin-top: 20px;
}

.success-card {
    background: #e9f7ed;
    border: 1px solid #87c38f;
    border-radius: 15px;
    padding: 18px;
}

.warning-card {
    background: #fff8df;
    border: 1px solid #e5cf72;
    border-radius: 15px;
    padding: 18px;
}

div.stButton > button {
    border-radius: 12px;
    font-weight: 700;
}

</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

if "unlocked" not in st.session_state:
    st.session_state.unlocked = False

if "payment_result" not in st.session_state:
    st.session_state.payment_result = None

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "last_evidence" not in st.session_state:
    st.session_state.last_evidence = []

if "last_query" not in st.session_state:
    st.session_state.last_query = ""


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

@st.cache_resource(show_spinner=False)
def get_retriever():
    return HybridRetriever()


def run_trip_planner(
    query: str,
    evidence,
    trip_days: int,
):
    evidence_text = evidence_to_prompt(
        evidence
    )

    crew = TrekTalesCrew(
        user_query=query,
        evidence_text=evidence_text,
        trip_days=trip_days,
    )

    return crew.run()


def display_sources(evidence):
    if not evidence:
        return

    citations = format_citations(
        evidence
    )

    st.markdown("### 📚 Knowledge-Base Sources")

    for citation in citations:
        st.markdown(
            f"""
            <div class="source-card">
                📄 <strong>{citation["source"]}</strong>
                &nbsp; • &nbsp;
                Page {citation["page"]}
                &nbsp; • &nbsp;
                {citation["department"]}
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

with st.sidebar:

    st.markdown(
        "## 🥾 TrekTales"
    )

    st.caption(
        "8-Agent AI Tourism System"
    )

    st.divider()

    st.markdown("### 🤖 Agents")

    agents = [
        ("👑", "Master Orchestrator"),
        ("📚", "Knowledge Agent"),
        ("🗺️", "Planner Agent"),
        ("💰", "Budget Agent"),
        ("🛡️", "Safety Agent"),
        ("📝", "Summarizer Agent"),
        ("💳", "Payment Agent"),
        ("👁️", "Vision Agent"),
    ]

    for icon, name in agents:
        st.markdown(
            f"""
            <div class="agent-card">
                {icon} <span class="agent-title">{name}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    st.markdown("### 🔐 Trip Access")

    if st.session_state.unlocked:
        st.success(
            "Day 2 + Day 3 unlocked"
        )
    else:
        st.info(
            "Day 1 is free.\n\n"
            f"Day 2 + Day 3: Rs. {UNLOCK_PRICE}"
        )

    st.divider()

    st.caption(
        "AI provider: xAI / Grok"
    )


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.markdown(
    '<div class="main-title">🥾 TrekTales</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="subtitle">{APP_TAGLINE}</div>',
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# CONFIG CHECK
# ---------------------------------------------------------

problems = validate_configuration()

if problems:
    for problem in problems:
        st.error(problem)

    st.info(
        "Add XAI_API_KEY to Streamlit Secrets before using "
        "the AI features."
    )

    st.stop()


# ---------------------------------------------------------
# CHECK INDEX
# ---------------------------------------------------------

if not FAISS_INDEX_PATH.exists():

    st.warning(
        "The tourism knowledge-base index has not been created yet."
    )

    st.code(
        "python ingest.py",
        language="bash",
    )

    st.info(
        "Place your six tourism PDFs inside "
        "`tourism_knowledge_base/`, run ingest.py, "
        "then upload the generated data/faiss_index folder "
        "to your GitHub repository."
    )

    st.stop()


# ---------------------------------------------------------
# MAIN INPUT
# ---------------------------------------------------------

st.markdown("## 🗺️ Plan Your Trip")

query = st.text_area(
    "Tell TrekTales what kind of trip you want",
    placeholder=(
        "Example: Plan a 3-day family trip to Rawalpindi "
        "with places to visit, transport, food, safety "
        "and an estimated budget."
    ),
    height=130,
)

col1, col2, col3 = st.columns(3)

with col1:
    trip_days = st.selectbox(
        "Trip duration",
        [1, 2, 3],
        index=2,
    )

with col2:
    language = st.selectbox(
        "Response language",
        [
            "English",
            "Urdu",
            "Roman Urdu",
        ],
    )

with col3:
    traveler_type = st.selectbox(
        "Traveler type",
        [
            "Solo",
            "Couple",
            "Family",
            "Friends",
        ],
    )


st.markdown("")


# ---------------------------------------------------------
# PLAN BUTTON
# ---------------------------------------------------------

if st.button(
    "✨ Create My TrekTales Plan",
    type="primary",
    use_container_width=True,
):

    if not query.strip():
        st.warning(
            "Please enter your travel request first."
        )
        st.stop()

    full_query = f"""
Original user request:
{query}

Traveler type:
{traveler_type}

Requested language:
{language}

Trip duration:
{trip_days} day(s)
"""

    try:

        with st.spinner(
            "TrekTales agents are working..."
        ):

            retriever = get_retriever()

            evidence = retriever.search(
                full_query
            )

            if not evidence:
                st.error(
                    "No relevant information was found "
                    "in the tourism knowledge base."
                )
                st.stop()

            result = run_trip_planner(
                full_query,
                evidence,
                trip_days,
            )

            st.session_state.last_result = str(
                result
            )

            st.session_state.last_evidence = evidence

            st.session_state.last_query = full_query

    except Exception as exc:

        st.error(
            "The trip planner encountered an error."
        )

        st.exception(exc)

        st.stop()


# ---------------------------------------------------------
# RESULT
# ---------------------------------------------------------

if st.session_state.last_result:

    st.markdown(
        '<div class="answer-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        st.session_state.last_result
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    display_sources(
        st.session_state.last_evidence
    )


# ---------------------------------------------------------
# PAYMENT SECTION
# ---------------------------------------------------------

st.divider()

st.markdown("## 🔐 Unlock Extended Trip")

if st.session_state.unlocked:

    st.markdown(
        """
        <div class="success-card">
        ✅ <strong>Extended itinerary unlocked.</strong><br>
        Day 2 and Day 3 are now available in the TrekTales session.
        </div>
        """,
        unsafe_allow_html=True,
    )

else:

    st.markdown(
        f"""
        <div class="lock-card">
        <h3>🔒 Day 2 + Day 3 are locked</h3>

        Day 1 is available in the free demo.

        <br><br>

        Unlock the extended itinerary for
        <strong>Rs. {UNLOCK_PRICE}</strong>.

        <br><br>

        <small>
        AI Screenshot Verification — Demo
        </small>
        </div>
        """,
        unsafe_allow_html=True,
    )

    payment_col1, payment_col2 = st.columns(
        [1, 1]
    )

    with payment_col1:

        st.markdown(
            "### 📱 JazzCash Payment"
        )

        if QR_PATH.exists():
            st.image(
                str(QR_PATH),
                caption=(
                    f"Demo payment amount: "
                    f"Rs. {UNLOCK_PRICE}"
                ),
                width=280,
            )
        else:
            st.warning(
                "jazzcash_qr.png was not found in assets/."
            )

        st.caption(
            f"Expected demo recipient: "
            f"{EXPECTED_PAYMENT_RECIPIENT.title()}"
        )

    with payment_col2:

        st.markdown(
            "### 📸 Upload Payment Screenshot"
        )

        uploaded_file = st.file_uploader(
            "Upload PNG or JPG",
            type=["png", "jpg", "jpeg"],
        )

        st.caption(
            "The Vision Agent extracts visible payment "
            "information. This demo does not verify a real "
            "JazzCash transaction with the provider."
        )

        if uploaded_file:

            file_size_mb = (
                uploaded_file.size
                / (1024 * 1024)
            )

            if file_size_mb > MAX_PAYMENT_IMAGE_MB:

                st.error(
                    f"Image is larger than "
                    f"{MAX_PAYMENT_IMAGE_MB} MB."
                )

            else:

                st.image(
                    uploaded_file,
                    caption="Uploaded payment screenshot",
                    width=320,
                )

                if st.button(
                    "🔍 Verify Screenshot",
                    use_container_width=True,
                ):

                    try:

                        with st.spinner(
                            "Vision Agent is reading the screenshot..."
                        ):

                            image_bytes = (
                                uploaded_file.getvalue()
                            )

                            mime_type = (
                                uploaded_file.type
                                or "image/png"
                            )

                            vision_result = (
                                analyze_payment_screenshot(
                                    image_bytes,
                                    mime_type,
                                )
                            )

                            payment_result = (
                                validate_payment(
                                    vision_result
                                )
                            )

                            st.session_state.payment_result = (
                                payment_result
                            )

                    except Exception as exc:

                        st.error(
                            "Screenshot analysis failed."
                        )

                        st.exception(exc)


# ---------------------------------------------------------
# PAYMENT RESULT
# ---------------------------------------------------------

if st.session_state.payment_result:

    result = st.session_state.payment_result

    st.divider()

    st.markdown(
        "### 👁️ Vision Agent Result"
    )

    r1, r2, r3, r4 = st.columns(4)

    with r1:
        st.metric(
            "Recipient",
            result.get(
                "recipient",
                "Unknown",
            ),
        )

    with r2:
        amount = result.get(
            "amount"
        )

        st.metric(
            "Amount",
            f"Rs. {amount}"
            if amount is not None
            else "Unknown",
        )

    with r3:
        st.metric(
            "Status",
            result.get(
                "status",
                "Unknown",
            ).title(),
        )

    with r4:
        # This is a deterministic validation result,
        # not a financial-provider verification.
        st.metric(
            "Demo Result",
            "PASS"
            if result.get("approved")
            else "FAIL",
        )

    if result.get("approved"):

        st.markdown(
            """
            <div class="success-card">
            <strong>✅ Demo verification passed.</strong><br><br>
            The screenshot fields satisfy the TrekTales
            demo validation rules.
            <br><br>
            <strong>Important:</strong> this is not confirmation
            from JazzCash that a real payment was received.
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "🔓 Unlock Day 2 + Day 3",
            type="primary",
            use_container_width=True,
        ):

            st.session_state.unlocked = True

            st.success(
                "Day 2 and Day 3 are now unlocked for this session."
            )

            st.rerun()

    else:

        st.markdown(
            """
            <div class="warning-card">
            ❌ <strong>Demo verification failed.</strong><br><br>
            The screenshot did not satisfy all required
            demo conditions.
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.divider()

st.caption(
    "TrekTales • 8-Agent Tourism System • "
    "Powered by xAI/Grok • Hybrid RAG"
)

st.caption(
    "Tourism information is limited to the supplied "
    "knowledge base. Prices and availability are not "
    "assumed to be current unless explicitly provided "
    "in the knowledge base."
)
