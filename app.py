import os

import streamlit as st

from src.config import (
    XAI_API_KEY,
    TEXT_MODEL,
    VISION_MODEL
)

from src.rag import (
    search,
    build_context
)

from src.crew import (
    run_tourism_crew
)

from src.vision import (
    analyze_payment_image
)

from src.payment import (
    verify_payment
)

from src.citations import (
    format_sources
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="TrekTales | AI Tourism Planner",
    page_icon="🥾",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "payment_unlocked": False,
    "revenue": 0,
    "last_query": "",
    "final_answer": "",
    "retrieved_results": [],
    "premium_answer": ""
}

for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


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
            #F4F0BB 0%,
            #F4F0BB 55%,
            #87C38F 100%
        );
}

[data-testid="stAppViewContainer"] {
    background:
        linear-gradient(
            135deg,
            #F4F0BB 0%,
            #F4F0BB 55%,
            #87C38F 100%
        );
}

[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stSidebar"] {
    background: #43291F;
    border-right: 3px solid #226F54;
}

[data-testid="stSidebar"] * {
    color: #F4F0BB !important;
}

.hero {
    background:
        linear-gradient(
            135deg,
            #43291F,
            #226F54,
            #87C38F
        );

    padding: 42px;
    border-radius: 28px;
    margin-bottom: 28px;

    border: 2px solid #F4F0BB;

    box-shadow:
        0 18px 45px rgba(67,41,31,0.25);
}

.badge {
    display: inline-block;

    background: #DA2C38;
    color: white;

    padding: 7px 15px;

    border-radius: 30px;

    font-size: 12px;
    font-weight: 800;
}

.hero-title {
    color: #F4F0BB;

    font-size: 52px;
    font-weight: 900;

    margin-top: 14px;
}

.hero-subtitle {
    color: white;

    font-size: 20px;
    font-weight: 600;
}

.hero-text {
    color: #F4F0BB;

    max-width: 850px;

    line-height: 1.7;

    margin-top: 12px;
}

.section-title {
    color: #43291F;

    font-size: 28px;
    font-weight: 900;

    margin-top: 18px;
}

.section-text {
    color: #226F54;

    margin-bottom: 18px;
}

.feature-card {
    background: rgba(255,255,255,0.78);

    border: 2px solid #87C38F;

    border-radius: 18px;

    padding: 20px;

    height: 100%;

    box-shadow:
        0 8px 25px rgba(67,41,31,0.10);
}

.feature-title {
    color: #43291F;
    font-weight: 900;
}

.feature-text {
    color: #226F54;
    font-size: 13px;
    line-height: 1.6;
}

div[data-testid="stTextInput"] input {
    background: #FFFDF0 !important;
    color: #43291F !important;

    border: 2px solid #87C38F !important;

    border-radius: 14px !important;

    padding: 14px !important;
}

.stButton > button {
    background: #226F54;

    color: white;

    border: 2px solid #226F54;

    border-radius: 13px;

    font-weight: 800;

    min-height: 44px;
}

.stButton > button:hover {
    background: #DA2C38;
    border-color: #DA2C38;
}

.answer-box {
    background: #FFFDF0;

    border: 2px solid #87C38F;

    border-radius: 18px;

    padding: 25px;

    color: #43291F;

    line-height: 1.75;

    box-shadow:
        0 8px 25px rgba(67,41,31,0.10);
}

.answer-title {
    background: #43291F;

    color: #F4F0BB;

    padding: 15px 20px;

    border-radius: 16px 16px 0 0;

    font-weight: 900;

    font-size: 18px;
}

.agent-card {
    background: rgba(255,255,255,0.75);

    border: 2px solid #87C38F;

    border-radius: 16px;

    padding: 15px;

    min-height: 100px;
}

.agent-name {
    color: #43291F;
    font-weight: 900;
}

.agent-description {
    color: #226F54;
    font-size: 12px;
    margin-top: 5px;
}

.premium {
    background:
        linear-gradient(
            135deg,
            #43291F,
            #226F54
        );

    padding: 30px;

    border-radius: 24px;

    text-align: center;

    border: 2px solid #87C38F;
}

.premium-title {
    color: #F4F0BB;

    font-size: 28px;
    font-weight: 900;
}

.premium-text {
    color: white;
}

.premium-price {
    color: #F4F0BB;

    font-size: 40px;
    font-weight: 900;
}

.source {
    background: #FFFDF0;

    border-left: 5px solid #226F54;

    border-radius: 10px;

    padding: 12px;

    margin-bottom: 8px;

    color: #43291F;
}

.footer {
    text-align: center;

    color: #43291F;

    padding: 30px;

    font-size: 13px;
}

</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
<div class="hero">

    <span class="badge">
        ✨ 8-AGENT AI TOURISM SYSTEM
    </span>

    <div class="hero-title">
        🥾 TrekTales
    </div>

    <div class="hero-subtitle">
        Your AI-powered travel companion
    </div>

    <div class="hero-text">
        Build personalized Rawalpindi travel plans using
        FAISS RAG, specialized AI agents and Grok-powered
        reasoning.
    </div>

</div>
""",
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <h2>🥾 TrekTales</h2>
        <p>AI Tourism Intelligence</p>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    st.markdown("### 🤖 Agent System")

    agents = [
        "🧭 Master Orchestrator",
        "📚 Knowledge Agent",
        "🗓 Planner Agent",
        "💰 Budget Agent",
        "🛡 Safety Agent",
        "📝 Summarizer Agent",
        "💳 Payment Agent",
        "👁 Vision Agent"
    ]

    for agent in agents:
        st.write(agent)

    st.divider()

    st.metric(
        "Demo Revenue",
        f"Rs. {st.session_state.revenue}"
    )

    if st.session_state.payment_unlocked:

        st.success(
            "🔓 Premium unlocked"
        )

    else:

        st.warning(
            "🔒 Premium locked"
        )

    st.divider()

    st.caption(
        "TrekTales • AI Tourism Demo"
    )


# ============================================================
# API CHECK
# ============================================================

if not XAI_API_KEY:

    st.error(
        "XAI_API_KEY is missing."
    )

    st.info(
        "Add XAI_API_KEY in Streamlit Secrets."
    )

    st.stop()


# ============================================================
# PLANNER
# ============================================================

st.markdown(
    '<div class="section-title">🌍 Plan Your Journey</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-text">'
    'Ask TrekTales in English, Urdu or Roman Urdu.'
    '</div>',
    unsafe_allow_html=True
)

query = st.text_input(
    "Travel request",
    placeholder="Example: 3 din ka Rawalpindi tour batao",
    label_visibility="collapsed"
)

col1, col2 = st.columns(2)

with col1:

    plan_button = st.button(
        "✨ Plan My Trip",
        use_container_width=True
    )

with col2:

    clear_button = st.button(
        "🧹 Clear",
        use_container_width=True
    )

if clear_button:

    for key, value in defaults.items():
        st.session_state[key] = value

    st.rerun()


# ============================================================
# GENERATE PLAN
# ============================================================

if plan_button:

    if not query.strip():

        st.warning(
            "Please enter a travel request."
        )

        st.stop()

    st.session_state.last_query = query

    with st.spinner(
        "🔎 Searching TrekTales knowledge base..."
    ):

        try:

            results = search(
                query,
                top_k=8
            )

            context = build_context(
                results
            )

            st.session_state.retrieved_results = results

        except Exception as error:

            st.error(
                f"RAG error: {error}"
            )

            st.stop()

    st.markdown(
        '<div class="section-title">🤖 AI Travel Team</div>',
        unsafe_allow_html=True
    )

    agent_columns = st.columns(5)

    agent_cards = [
        (
            "📚 Knowledge",
            "Finding tourism facts"
        ),
        (
            "🗓 Planner",
            "Building itinerary"
        ),
        (
            "💰 Budget",
            "Calculating costs"
        ),
        (
            "🛡 Safety",
            "Checking safety"
        ),
        (
            "📝 Summary",
            "Creating final plan"
        )
    ]

    for column, card in zip(
        agent_columns,
        agent_cards
    ):

        with column:

            st.markdown(
                f"""
                <div class="agent-card">

                    <div class="agent-name">
                        {card[0]}
                    </div>

                    <div class="agent-description">
                        {card[1]}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

    with st.spinner(
        "🧠 Grok agents are creating your travel plan..."
    ):

        try:

            answer = run_tourism_crew(
                XAI_API_KEY,
                TEXT_MODEL,
                query,
                context
            )

            st.session_state.final_answer = answer

        except Exception as error:

            st.error(
                f"Grok error: {error}"
            )

            st.stop()


# ============================================================
# MAIN ANSWER
# ============================================================

if st.session_state.final_answer:

    st.markdown(
        '<div class="section-title">🗺️ Your TrekTales Plan</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="answer-title">'
        '✨ AI-Generated Travel Plan'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="answer-box">'
        + st.session_state.final_answer
        + '</div>',
        unsafe_allow_html=True
    )


# ============================================================
# PREMIUM
# ============================================================

st.divider()

st.markdown(
    '<div class="section-title">🔐 Premium 3-Day Experience</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-text">'
    'Unlock the extended itinerary after the demo payment verification.'
    '</div>',
    unsafe_allow_html=True
)


if not st.session_state.payment_unlocked:

    st.markdown(
        """
        <div class="premium">

            <div style="font-size:45px;">
                🔒
            </div>

            <div class="premium-title">
                Days 2 & 3 are locked
            </div>

            <div class="premium-text">
                Unlock the complete multi-day experience.
            </div>

            <div class="premium-price">
                Rs. 199
            </div>

            <div class="premium-text">
                Demo recipient:
                <strong>Ambreen Sadia</strong>
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    payment_col1, payment_col2 = st.columns(2)

    with payment_col1:

        st.markdown("### 💳 Demo Payment")

        st.write(
            "Complete the demo payment of Rs. 199."
        )

        qr_path = (
            "assets/jazzcash_qr.png"
        )

        if os.path.exists(qr_path):

            st.image(
                qr_path,
                caption="TrekTales Demo JazzCash QR",
                width=280
            )

        else:

            st.warning(
                "assets/jazzcash_qr.png was not found."
            )

    with payment_col2:

        st.markdown(
            "### 📤 Payment Screenshot"
        )

        uploaded_file = st.file_uploader(
            "Upload payment screenshot",
            type=[
                "png",
                "jpg",
                "jpeg"
            ]
        )

        verify_button = st.button(
            "🔎 Verify Payment",
            use_container_width=True
        )

        if verify_button:

            if uploaded_file is None:

                st.warning(
                    "Please upload a payment screenshot."
                )

            else:

                with st.spinner(
                    "👁 Vision Agent is reading the screenshot..."
                ):

                    try:

                        vision_result = (
                            analyze_payment_image(
                                uploaded_file,
                                XAI_API_KEY,
                                VISION_MODEL
                            )
                        )

                    except Exception as error:

                        st.error(
                            f"Vision error: {error}"
                        )

                        vision_result = None

                if vision_result:

                    recipient = vision_result.get(
                        "recipient"
                    )

                    amount = vision_result.get(
                        "amount"
                    )

                    status = vision_result.get(
                        "status"
                    )

                    c1, c2, c3 = st.columns(3)

                    with c1:
                        st.metric(
                            "Recipient",
                            str(recipient or "Not detected")
                        )

                    with c2:
                        st.metric(
                            "Amount",
                            str(amount or "Not detected")
                        )

                    with c3:
                        st.metric(
                            "Status",
                            str(status or "Not detected")
                        )

                    verification = verify_payment(
                        recipient,
                        amount,
                        status
                    )

                    if verification["verified"]:

                        st.session_state.payment_unlocked = True

                        st.session_state.revenue += 199

                        st.success(
                            "✅ Demo payment verification passed."
                        )

                        st.rerun()

                    else:

                        st.error(
                            "❌ Payment did not pass the demo verification rules."
                        )

                        st.write(
                            "Required recipient: Ambreen Sadia"
                        )

                        st.write(
                            "Required amount: Rs. 199"
                        )

                        st.write(
                            "Required status: Sent / Successful / Completed"
                        )


# ============================================================
# PREMIUM UNLOCKED
# ============================================================

else:

    st.markdown(
        """
        <div class="premium">

            <div style="font-size:45px;">
                🔓
            </div>

            <div class="premium-title">
                Premium Unlocked!
            </div>

            <div class="premium-text">
                Your extended itinerary is available.
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    if st.session_state.last_query:

        if not st.session_state.premium_answer:

            premium_query = (
                st.session_state.last_query
                + "\n"
                + "Create the complete Day 2 and Day 3 itinerary."
            )

            with st.spinner(
                "🧠 Creating premium itinerary..."
            ):

                try:

                    premium_results = search(
                        premium_query,
                        top_k=10
                    )

                    premium_context = build_context(
                        premium_results
                    )

                    st.session_state.premium_answer = (
                        run_tourism_crew(
                            XAI_API_KEY,
                            TEXT_MODEL,
                            premium_query,
                            premium_context
                        )
                    )

                except Exception as error:

                    st.error(
                        f"Premium error: {error}"
                    )

        if st.session_state.premium_answer:

            st.markdown(
                '<div class="answer-title">'
                '🌟 Complete Premium Itinerary'
                '</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                '<div class="answer-box">'
                + st.session_state.premium_answer
                + '</div>',
                unsafe_allow_html=True
            )

    else:

        st.info(
            "Create a trip plan first."
        )

    if st.button(
        "🔒 Lock Premium Again"
    ):

        st.session_state.payment_unlocked = False
        st.session_state.premium_answer = ""

        st.rerun()


# ============================================================
# SOURCES
# ============================================================

if st.session_state.retrieved_results:

    st.divider()

    st.markdown(
        '<div class="section-title">📚 Knowledge Sources</div>',
        unsafe_allow_html=True
    )

    sources = format_sources(
        st.session_state.retrieved_results
    )

    with st.expander(
        "📖 View Retrieved Sources"
    ):

        for index, source in enumerate(
            sources,
            start=1
        ):

            st.markdown(
                f"""
                <div class="source">
                    <strong>📄 Source {index}</strong><br>
                    {source}
                </div>
                """,
                unsafe_allow_html=True
            )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
<div class="footer">

    🥾 <strong>TrekTales</strong>
    &nbsp;•&nbsp;
    AI-Powered Tourism Intelligence

    <br><br>

    FAISS • RAG • Grok • 8-Agent Architecture

</div>
""",
    unsafe_allow_html=True
)
