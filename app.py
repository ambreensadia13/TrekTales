from __future__ import annotations

import re
from pathlib import Path

import streamlit as st

from src.config import (
    APP_NAME,
    EXPECTED_PAYMENT_RECIPIENT,
    FREE_DAYS,
    GROQ_API_KEY,
    GROQ_MODEL,
    MAX_TRIP_DAYS,
    METADATA_PATH,
    PAID_DAYS,
    QR_PATH,
    SUPPORTED_LANGUAGES,
    UNLOCK_PRICE,
    FAISS_INDEX_PATH,
)
from src.crew import TrekTalesCrew
from src.payment import verify_payment
from src.retriever import HybridRetriever
from src.vision import analyze_payment_screenshot


st.set_page_config(
    page_title=APP_NAME,
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

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


st.markdown(
    f"""
    <style>
    .stApp {{ background: linear-gradient(135deg,{SOFT_WHITE} 0%,{CREAM} 100%); color:{BLACK}; }}
    .main .block-container {{ max-width:1250px; padding-top:1.2rem; padding-bottom:2rem; }}
    h1,h2,h3,h4,h5,h6 {{ color:{BLACK} !important; }}
    p,li,label {{ color:{BLACK}; }}
    div[class*="st-key-top_brand"] {{ background:transparent !important; border:none !important; text-align:center; padding:.2rem 0 .5rem; }}
    div[class*="st-key-top_brand"] h1 {{ color:{BROWN} !important; font-size:3.2rem !important; font-weight:900 !important; margin:0 !important; }}
    div[class*="st-key-top_brand"] p {{ color:{GREEN} !important; font-weight:600; }}
    section[data-testid="stSidebar"] {{ background:linear-gradient(180deg,{DARK_GREEN} 0%,{GREEN} 100%); }}
    section[data-testid="stSidebar"] * {{ color:{WHITE} !important; }}
    div[class*="st-key-sidebar_access"],div[class*="st-key-agent_"] {{ background:rgba(255,255,255,.09) !important; border:1px solid rgba(255,255,255,.2) !important; border-radius:14px !important; padding:.8rem !important; margin-bottom:.5rem; }}
    div[class*="st-key-hero"] {{ background:linear-gradient(135deg,{DARK_GREEN},{GREEN}) !important; border:none !important; border-radius:24px !important; padding:2rem !important; box-shadow:0 15px 35px rgba(34,111,84,.2); }}
    div[class*="st-key-hero"] * {{ color:{WHITE} !important; }}
    div[class*="st-key-feature_"] {{ background:{WHITE} !important; border:1px solid rgba(34,111,84,.18) !important; border-radius:18px !important; padding:1rem !important; min-height:160px; }}
    div[class*="st-key-feature_"] * {{ color:{BLACK} !important; }}
    div[class*="st-key-answer_card"] {{ background:{WHITE} !important; border:2px solid {LIGHT_GREEN} !important; border-radius:20px !important; padding:1.3rem !important; }}
    div[class*="st-key-answer_card"] * {{ color:{BLACK} !important; }}
    div[class*="st-key-locked_card"] {{ background:linear-gradient(135deg,{DARK_GREEN},{GREEN}) !important; border:none !important; border-radius:20px !important; padding:1.3rem !important; }}
    div[class*="st-key-locked_card"] * {{ color:{WHITE} !important; }}
    div[class*="st-key-payment_card"] {{ background:{WHITE} !important; border:2px solid {RED} !important; border-radius:20px !important; padding:1.3rem !important; }}
    div[class*="st-key-payment_card"] * {{ color:{BLACK} !important; }}
    div[class*="st-key-source_"] {{ background:{LIGHT_GREY} !important; border:1px solid #ddd !important; border-radius:12px !important; padding:.8rem !important; }}
    div[class*="st-key-source_"] * {{ color:{BLACK} !important; }}
    div[class*="st-key-disclaimer_card"] {{ background:{WHITE} !important; border-left:5px solid {GREEN} !important; border-radius:14px !important; padding:1rem !important; }}
    div[class*="st-key-disclaimer_card"] * {{ color:{BLACK} !important; }}
    .stButton > button {{ background:{RED} !important; color:{WHITE} !important; border:none !important; border-radius:12px !important; font-weight:700 !important; min-height:2.7rem; }}
    .stButton > button:hover {{ background:{GREEN} !important; color:{WHITE} !important; }}
    div[data-baseweb="select"] > div,input,textarea {{ background:{WHITE} !important; color:{BLACK} !important; }}
    div[data-baseweb="select"] * {{ color:{BLACK} !important; }}
    section[data-testid="stFileUploaderDropzone"] {{ background:{WHITE} !important; border:1px dashed {GREEN} !important; border-radius:14px !important; }}
    section[data-testid="stFileUploaderDropzone"] * {{ color:{BLACK} !important; }}
    div[data-testid="stMetric"] {{ background:{WHITE}; border:1px solid rgba(34,111,84,.18); border-radius:14px; padding:.8rem; }}
    div[data-testid="stMetric"] * {{ color:{BLACK} !important; }}
    @media(max-width:768px) {{ .main .block-container{{padding:.8rem}} div[class*="st-key-top_brand"] h1{{font-size:2.4rem !important}} div[class*="st-key-hero"]{{padding:1.2rem !important}} }}
    </style>
    """,
    unsafe_allow_html=True,
)


for key, default in {
    "trip_result": None,
    "trip_evidence": [],
    "payment_verified": False,
    "payment_result": None,
    "vision_result": None,
    "payment_unlock_scope": 0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def clean_display_text(value) -> str:
    text = str(value or "")
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("```html", "").replace("```HTML", "").replace("```", "")
    return text.strip()


def get_retriever() -> HybridRetriever:
    return HybridRetriever()


def extract_result_text(result) -> str:
    if result is None:
        return ""
    if isinstance(result, dict):
        for key in ("answer", "result", "output", "plan"):
            if result.get(key):
                return clean_display_text(result[key])
    for attr in ("raw", "output"):
        value = getattr(result, attr, None)
        if value:
            return clean_display_text(value)
    return clean_display_text(result)


def format_sources(evidence: list[dict]) -> list[dict]:
    seen = set()
    output = []
    for item in evidence or []:
        if not isinstance(item, dict):
            continue
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        source = str(metadata.get("source") or item.get("source") or "Unknown source")
        page = str(metadata.get("page") or item.get("page") or "N/A")
        department = str(metadata.get("department") or item.get("department") or "General")
        key = (source, page, department)
        if key in seen:
            continue
        seen.add(key)
        output.append({"source": source, "page": page, "department": department})
    return output


def run_trip_planner(*, destination, requested_days, accessible_days, budget,
                     travelers, travel_style, language, interests,
                     starting_location, evidence):
    crew = TrekTalesCrew()
    request = {
        "destination": destination,
        "requested_days": requested_days,
        "accessible_days": accessible_days,
        "duration": requested_days,
        "budget": budget,
        "travelers": travelers,
        "travel_style": travel_style,
        "language": language,
        "interests": interests,
        "starting_location": starting_location,
        "evidence": evidence,
    }
    return crew.run(request)


def access_days(requested_days: int) -> int:
    if requested_days <= FREE_DAYS:
        return requested_days
    if st.session_state.payment_verified and st.session_state.payment_unlock_scope >= requested_days:
        return requested_days
    return FREE_DAYS


with st.container(key="top_brand"):
    st.markdown("# TrekTales")
    st.markdown("AI Multi-Agent Travel Planner")

with st.sidebar:
    st.markdown("## 🌿 TrekTales")
    st.write("Plan smarter trips with AI-powered travel agents.")
    st.divider()
    with st.container(border=True, key="sidebar_access"):
        st.markdown("### 🔐 Access Model")
        st.markdown("**Day 1:** Free")
        st.markdown(f"**Days 2–3:** Rs. {UNLOCK_PRICE} demo unlock")

    language = st.selectbox("🌐 Response Language", SUPPORTED_LANGUAGES)

    st.markdown("### 🤖 AI Agents")
    agent_info = [
        (1, "Master Orchestrator", "Coordinates the workflow."),
        (2, "Knowledge Agent", "Analyzes retrieved tourism evidence."),
        (3, "Planner Agent", "Builds the itinerary."),
        (4, "Budget Agent", "Handles supported prices and estimates."),
        (5, "Safety Agent", "Reviews travel safety."),
        (6, "Summarizer Agent", "Creates the final answer."),
        (7, "Payment Agent", "Supports demo payment verification."),
        (8, "Vision Agent", "Reads payment screenshots."),
    ]
    for number, name, description in agent_info:
        with st.container(border=True, key=f"agent_{number}"):
            st.markdown(f"**AGENT {number:02d}**")
            st.markdown(f"**{name}**")
            st.caption(description)
    st.divider()
    st.caption(f"Groq model: {GROQ_MODEL}")

with st.container(border=True, key="hero"):
    st.markdown("## 🌍 Plan Your Next Adventure")
    st.markdown(
        "Create a practical travel plan grounded in your FAISS tourism knowledge base, "
        "with specialist AI agents for planning, budget and safety."
    )
    st.markdown("📚 RAG Grounding  •  🗺️ Planning  •  💰 Budget  •  🛡️ Safety  •  💳 Demo Unlock")

st.markdown("## ✨ TrekTales Features")
c1, c2, c3 = st.columns(3)
with c1:
    with st.container(border=True, key="feature_knowledge"):
        st.markdown("### 🧠 Knowledge Grounding")
        st.write("Uses the existing FAISS index and BM25 ranking together.")
with c2:
    with st.container(border=True, key="feature_agents"):
        st.markdown("### 🤖 Multi-Agent Planning")
        st.write("Knowledge, planner, budget, safety and summarizer agents work sequentially.")
with c3:
    with st.container(border=True, key="feature_payment"):
        st.markdown("### 💳 Demo Unlock")
        st.write(f"Day 1 is free. Days 2–3 unlock after deterministic demo verification for Rs. {UNLOCK_PRICE}.")

st.divider()
st.markdown("## 🧭 Create Your Trip")
left, right = st.columns(2)
with left:
    destination = st.text_input("📍 Destination", placeholder="e.g. Rawalpindi")
    starting_location = st.text_input("🚗 Starting Location", placeholder="e.g. Islamabad")
    duration = st.slider("📅 Trip Duration", 1, MAX_TRIP_DAYS, 1, 1)
    travelers = st.number_input("👥 Number of Travelers", 1, 20, 2, 1)
with right:
    budget = st.selectbox("💰 Budget Level", ["Budget", "Moderate", "Comfortable", "Premium"])
    travel_style = st.selectbox("🎒 Travel Style", ["Adventure", "Relaxed", "Family", "Romantic", "Cultural", "Nature", "Photography", "Mixed"])
    interests = st.multiselect(
        "⭐ Interests",
        ["Mountains", "Nature", "Food", "Culture", "History", "Photography", "Adventure", "Shopping", "Family Activities", "Nightlife"],
        default=["Nature", "Photography"],
    )

st.divider()
st.markdown("## ⚙️ System Status")
s1, s2, s3 = st.columns(3)
with s1:
    with st.container(border=True):
        st.markdown("### 🧠 Groq")
        st.write("● API key detected" if GROQ_API_KEY else "● API key missing")
with s2:
    with st.container(border=True):
        st.markdown("### 📚 FAISS")
        st.write("● Index ready" if FAISS_INDEX_PATH.exists() and METADATA_PATH.exists() else "● Index/metadata missing")
with s3:
    with st.container(border=True):
        st.markdown("### 🔐 Access")
        if duration == 1:
            st.write("● Day 1 available")
        elif st.session_state.payment_verified and st.session_state.payment_unlock_scope >= duration:
            st.write("● Premium days unlocked")
        else:
            st.write("● Day 2+ locked")

st.divider()
generate_trip = st.button("🚀 Generate My TrekTales Plan", use_container_width=True)

if generate_trip:
    if not destination.strip():
        st.error("Please enter a destination first.")
        st.stop()
    if not starting_location.strip():
        st.error("Please enter your starting location.")
        st.stop()
    if not GROQ_API_KEY:
        st.error("GROQ_API_KEY is missing from Streamlit Secrets.")
        st.stop()

    accessible = access_days(duration)
    if duration > accessible:
        st.info(
            f"Your {duration}-day request is currently limited to Day 1. "
            f"Days 2–{duration} remain locked until the demo payment is verified."
        )

    st.session_state.trip_result = None
    st.session_state.trip_evidence = []

    with st.status("🔎 Preparing your TrekTales trip...", expanded=True) as status:
        try:
            retriever = get_retriever()
            query = (
                f"Destination: {destination}. Starting location: {starting_location}. "
                f"Requested duration: {duration} days. Accessible days: {accessible}. "
                f"Travelers: {travelers}. Travel style: {travel_style}. "
                f"Interests: {', '.join(interests) if interests else 'none'}. "
                f"Budget: {budget}."
            )
            evidence = retriever.search(query, top_k=6)
            st.session_state.trip_evidence = evidence
            st.write(f"Retrieved {len(evidence)} RAG evidence records.")
        except Exception as exc:
            st.error("Could not load the FAISS tourism knowledge base.")
            st.exception(exc)
            st.stop()

        try:
            result = run_trip_planner(
                destination=destination,
                requested_days=duration,
                accessible_days=accessible,
                budget=budget,
                travelers=travelers,
                travel_style=travel_style,
                language=language,
                interests=interests,
                starting_location=starting_location,
                evidence=evidence,
            )
            st.session_state.trip_result = result
            status.update(label="✅ TrekTales plan generated", state="complete", expanded=False)
        except Exception as exc:
            status.update(label="❌ Trip generation failed", state="error", expanded=True)
            st.error("The AI travel planner encountered an error.")
            st.exception(exc)
            st.stop()


if st.session_state.trip_result:
    st.divider()
    st.markdown("## 🗺️ Your TrekTales Plan")
    answer = extract_result_text(st.session_state.trip_result)
    with st.container(border=True, key="answer_card"):
        st.markdown("### 🌿 Your Personalized Itinerary")
        st.markdown(answer, unsafe_allow_html=False)

    sources = format_sources(st.session_state.trip_evidence)
    if sources:
        st.markdown("## 📚 Knowledge Sources")
        for index, source in enumerate(sources):
            with st.container(border=True, key=f"source_{index}"):
                st.markdown(f"**📄 {source['source']}**")
                st.write(f"Page: {source['page']}")
                st.write(f"Department: {source['department']}")


# Premium access is displayed separately and never used to expose locked itinerary content.
if duration >= 2 and not (st.session_state.payment_verified and st.session_state.payment_unlock_scope >= duration):
    st.divider()
    with st.container(border=True, key="locked_card"):
        st.markdown("## 🔒 Days 2–3 are Locked")
        st.write(
            f"Day 1 is free. Verify the Rs. {UNLOCK_PRICE} demo payment to unlock the additional requested days."
        )
        st.caption("This is a demo workflow. It does not connect to a real JazzCash transaction API.")

    with st.container(border=True, key="payment_card"):
        st.markdown("### 💳 Demo Payment Verification")
        st.write(f"Send **Rs. {UNLOCK_PRICE}** to the configured demo recipient.")
        st.write(f"Expected recipient: **{EXPECTED_PAYMENT_RECIPIENT}**")

        if QR_PATH.exists():
            st.image(str(QR_PATH), caption="JazzCash Demo QR", width=260)
        else:
            st.warning("JazzCash QR image was not found in the assets folder.")

        uploaded = st.file_uploader(
            "📸 Upload your payment screenshot",
            type=["png", "jpg", "jpeg", "webp"],
            key="payment_screenshot",
        )

        if uploaded and st.button("🔍 Verify Payment Screenshot", use_container_width=True):
            with st.spinner("👁️ Vision Agent is analyzing the screenshot..."):
                try:
                    vision = analyze_payment_screenshot(uploaded)
                    st.session_state.vision_result = vision
                except Exception as exc:
                    st.error("The Vision Agent could not analyze the screenshot.")
                    st.exception(exc)
                    st.stop()

            vision = st.session_state.vision_result or {}
            recipient = str(vision.get("recipient") or "").strip()
            amount = vision.get("amount", 0)
            payment_status = str(vision.get("status") or "").strip()
            confidence = vision.get("confidence", 0)

            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Recipient", recipient or "Not detected")
            with m2:
                st.metric("Amount", f"Rs. {amount}")
            with m3:
                st.metric("Status", payment_status or "Not detected")
            if confidence:
                st.write(f"AI confidence: {confidence}")

            try:
                payment_result = verify_payment({
                    "recipient": recipient,
                    "amount": amount,
                    "status": payment_status,
                })
            except TypeError:
                payment_result = verify_payment(recipient, amount, payment_status)
            except Exception as exc:
                payment_result = {"verified": False, "error": str(exc)}

            verified = bool(payment_result.get("verified", False)) if isinstance(payment_result, dict) else bool(payment_result)
            st.session_state.payment_result = payment_result
            st.session_state.payment_verified = verified
            st.session_state.payment_unlock_scope = duration if verified else 0

            if verified:
                st.success("✅ Demo payment verification successful.")
                st.info(
                    f"Days 2–{duration} are now unlocked. Click **Generate My TrekTales Plan** again "
                    "to generate the full requested itinerary."
                )
            else:
                st.error("❌ Payment could not be verified. Check the recipient, amount and status.")

elif duration >= 2 and st.session_state.payment_verified and st.session_state.payment_unlock_scope >= duration:
    st.success(f"🔓 Premium access active for all {duration} requested days.")


st.divider()
with st.container(border=True, key="disclaimer_card"):
    st.markdown(
        "**Important:** TrekTales is a demo travel-planning application. Its tourism knowledge base contains fictional/demo records. "
        "Prices, schedules, availability, weather, transport and local rules may change. Verify important details with current official sources before travelling."
    )

st.markdown("---")
a, b, c = st.columns(3)
with a:
    st.markdown("🌿 **TrekTales**")
with b:
    st.markdown("AI Multi-Agent Travel Planner")
with c:
    st.markdown("Built with Streamlit + Groq")
