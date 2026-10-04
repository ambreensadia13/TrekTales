from pathlib import Path
 import re
 import json

import streamlit as st

**============================================================**

**PAGE CONFIG**

**============================================================**

st.set_page_config(
 page_title="TrekTales",
 page_icon="🌿",
 layout="wide",
 initial_sidebar_state="expanded",
 )

**============================================================**

**COLORS**

**============================================================**

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

**============================================================**

**PROJECT PATHS**

**============================================================**

ROOT_DIR = Path(**file**).resolve().parent

FAISS_DIR = ROOT_DIR / "faiss_db"

FAISS_INDEX_PATH = (
 FAISS_DIR / "index.faiss"
 )

FAISS_METADATA_PATH = (
 FAISS_DIR / "metadata.json"
 )

FAISS_CONFIG_PATH = (
 FAISS_DIR / "config.json"
 )

ASSETS_DIR = ROOT_DIR / "assets"

QR_PATH = (
 ASSETS_DIR / "jazzcash_qr.jpg"
 )

KNOWLEDGE_BASE_DIR = (
 ROOT_DIR / "tourism_knowledge_base"
 )

**============================================================**

**SAFE CONFIG VALUES**

**============================================================**

DEFAULT_FREE_DAYS = 1
 DEFAULT_PAID_DAYS = 3
 DEFAULT_UNLOCK_PRICE = 199

DEFAULT_MODEL = (
 "openai/gpt-oss-120b"
 )

DEFAULT_VISION_MODEL = (
 "meta-llama/llama-4-scout-17b-16e-instruct"
 )

**============================================================**

**SAFE SECRET READER**

**============================================================**

def get_secret(
 name,
 default="",
 ):
 try:

    value = st.secrets.get(

        name,

        default,

    )

    if value is None:

        return default

    return str(value)

except Exception:

    return default

**============================================================**

**CONFIGURATION**

**============================================================**

GROQ_API_KEY = get_secret(
 "GROQ_API_KEY",
 "",
 )

GROQ_MODEL = get_secret(
 "GROQ_MODEL",
 DEFAULT_MODEL,
 )

GROQ_BASE_URL = get_secret(
 "GROQ_BASE_URL",
 "[https://api.groq.com/openai/v1](https://api.groq.com/openai/v1)",
 )

GROQ_VISION_MODEL = get_secret(
 "GROQ_VISION_MODEL",
 DEFAULT_VISION_MODEL,
 )

EXPECTED_PAYMENT_RECIPIENT = get_secret(
 "EXPECTED_PAYMENT_RECIPIENT",
 "TrekTales",
 )

**============================================================**

**TRY TO LOAD PROJECT CONFIG**

**============================================================**

FREE_DAYS = DEFAULT_FREE_DAYS
 PAID_DAYS = DEFAULT_PAID_DAYS
 UNLOCK_PRICE = DEFAULT_UNLOCK_PRICE

try:

from src.config import ( 

    FREE_DAYS as CONFIG_FREE_DAYS, 

    PAID_DAYS as CONFIG_PAID_DAYS, 

    UNLOCK_PRICE as CONFIG_UNLOCK_PRICE, 

    EXPECTED_PAYMENT_RECIPIENT as CONFIG_PAYMENT_RECIPIENT, 

    GROQ_MODEL as CONFIG_GROQ_MODEL, 

) 

FREE_DAYS = int( 

    CONFIG_FREE_DAYS 

) 

PAID_DAYS = int( 

    CONFIG_PAID_DAYS 

) 

UNLOCK_PRICE = int( 

    CONFIG_UNLOCK_PRICE 

) 

if CONFIG_PAYMENT_RECIPIENT: 

    EXPECTED_PAYMENT_RECIPIENT = str( 

        CONFIG_PAYMENT_RECIPIENT 

    ) 

if CONFIG_GROQ_MODEL: 

    GROQ_MODEL = str( 

        CONFIG_GROQ_MODEL 

    ) 

except Exception:
 pass

**============================================================**

**SESSION STATE**

**============================================================**

if "payment_verified" not in st.session_state:

st.session_state.payment_verified = False 

if "trip_result" not in st.session_state:

st.session_state.trip_result = None 

if "trip_evidence" not in st.session_state:

st.session_state.trip_evidence = [] 

if "payment_result" not in st.session_state:

st.session_state.payment_result = None 

if "vision_result" not in st.session_state:

st.session_state.vision_result = None 

if "last_error" not in st.session_state:

st.session_state.last_error = None 

**============================================================**

**CSS**

**============================================================**

st.markdown(
 f"""

""",
 unsafe_allow_html=True,
 )

**============================================================**

**HELPERS**

**============================================================**

def clean_text(text):
 """
 Remove accidental HTML from model output.

Markdown is intentionally preserved so the enhanced 

itinerary can render headings, lists and emphasis. 

""" 

if text is None: 

    return "" 

text = str(text) 

text = re.sub( 

    r"\<script.\*?\</script>", 

    "", 

    text, 

    flags=re.IGNORECASE | re.DOTALL, 

) 

text = re.sub( 

    r"\<style.\*?\</style>", 

    "", 

    text, 

    flags=re.IGNORECASE | re.DOTALL, 

) 

text = re.sub( 

    r"<[^>]+>", 

    "", 

    text, 

) 

text = text.replace( 

    "\`\`\`html", 

    "", 

) 

text = text.replace( 

    "\`\`\`HTML", 

    "", 

) 

text = text.replace( 

    "\`\`\`markdown", 

    "", 

) 

text = text.replace( 

    "\`\`\`Markdown", 

    "", 

) 

text = text.replace( 

    "\`\`\`", 

    "", 

) 

return text.strip() 

def safe_import_retriever():
 from src.retriever import HybridRetriever

return HybridRetriever 

def safe_import_crew():
 from src.crew import TrekTalesCrew

return TrekTalesCrew 

def safe_import_payment():
 from src.payment import verify_payment

return verify_payment 

def safe_import_vision():
 from src.vision import analyze_payment_screenshot

return analyze_payment_screenshot 

def extract_text_from_result(result):
 """
 Safely extract output from different result formats.
 """

if result is None: 

    return "" 

if isinstance(result, str): 

    return result 

if isinstance(result, dict): 

    for key in ( 

        "answer", 

        "result", 

        "output", 

        "raw", 

        "plan", 

        "response", 

        "content", 

    ): 

        if key in result and result[key]: 

            return str(result[key]) 

    return json.dumps( 

        result, 

        ensure_ascii=False, 

        indent=2, 

    ) 

for attribute in ( 

    "raw", 

    "output", 

    "result", 

    "content", 

): 

    try: 

        value = getattr( 

            result, 

            attribute, 

            None, 

        ) 

        if value: 

            return str(value) 

    except Exception: 

        pass 

return str(result) 

def extract_sources(evidence):
 """
 Extract source filenames from retrieved evidence.

No sources are invented. 

""" 

sources = [] 

if not evidence: 

    return sources 

for item in evidence: 

    if not isinstance(item, dict): 

        continue 

    metadata = item.get( 

        "metadata", 

        {}, 

    ) 

    if not isinstance(metadata, dict): 

        metadata = {} 

    source = ( 

        metadata.get("source") 

        or item.get("source") 

        or metadata.get("document") 

        or item.get("document") 

        or metadata.get("filename") 

        or item.get("filename") 

        or "" 

    ) 

    page = ( 

        metadata.get("page") 

        or item.get("page") 

        or "" 

    ) 

    if not source: 

        continue 

    source = str(source).replace( 

        "\\\\", 

        "/", 

    ) 

    source = source.split("/")[-1] 

    source = source.replace( 

        ".html", 

        "", 

    ) 

    sources.append( 

        { 

            "source": source, 

            "page": str(page), 

        } 

    ) 

unique = [] 

seen = set() 

for source in sources: 

    key = ( 

        source["source"], 

        source["page"], 

    ) 

    if key not in seen: 

        seen.add(key) 

        unique.append(source) 

return unique 

def retrieve_with_retriever(
 retriever,
 query,
 ):
 """
 Support common retriever APIs.
 """

if hasattr( 

    retriever, 

    "search", 

): 

    try: 

        return retriever.search( 

            query, 

            top_k=6, 

        ) 

    except TypeError: 

        return retriever.search( 

            query 

        ) 

if hasattr( 

    retriever, 

    "retrieve", 

): 

    try: 

        return retriever.retrieve( 

            query, 

            top_k=6, 

        ) 

    except TypeError: 

        return retriever.retrieve( 

            query 

        ) 

raise AttributeError( 

    "HybridRetriever does not provide " 

    "search() or retrieve()." 

) 

def run_crew(
 crew,
 destination,
 duration,
 budget,
 travelers,
 travel_style,
 language,
 interests,
 starting_location,
 evidence,
 ):
 """
 Run TrekTalesCrew using its supported interface.
 """

request = { 

    "destination": destination, 

    "starting_location": starting_location, 

    "days": duration, 

    "duration": duration, 

    "budget": budget, 

    "travelers": travelers, 

    "travel_style": travel_style, 

    "language": language, 

    "interests": interests, 

    "evidence": evidence, 

} 

\# -------------------------------------------------------- 

\# Preferred TrekTalesCrew\.run() interface 

\# -------------------------------------------------------- 

if hasattr( 

    crew, 

    "run", 

): 

    try: 

        return crew\.run( 

            destination=destination, 

            starting_location=starting_location, 

            days=duration, 

            budget=budget, 

            travelers=travelers, 

            travel_style=travel_style, 

            language=language, 

            interests=interests, 

            evidence=evidence, 

        ) 

    except TypeError: 

        try: 

            return crew\.run( 

                request 

            ) 

        except TypeError: 

            pass 

\# -------------------------------------------------------- 

\# kickoff() 

\# -------------------------------------------------------- 

if hasattr( 

    crew, 

    "kickoff", 

): 

    try: 

        return crew\.kickoff( 

            request 

        ) 

    except TypeError: 

        pass 

\# -------------------------------------------------------- 

\# plan() 

\# -------------------------------------------------------- 

if hasattr( 

    crew, 

    "plan", 

): 

    try: 

        return crew\.plan( 

            destination=destination, 

            starting_location=starting_location, 

            duration=duration, 

            days=duration, 

            budget=budget, 

            travelers=travelers, 

            travel_style=travel_style, 

            language=language, 

            interests=interests, 

            evidence=evidence, 

        ) 

    except TypeError: 

        pass 

\# -------------------------------------------------------- 

\# generate() 

\# -------------------------------------------------------- 

if hasattr( 

    crew, 

    "generate", 

): 

    try: 

        return crew\.generate( 

            destination=destination, 

            starting_location=starting_location, 

            duration=duration, 

            days=duration, 

            budget=budget, 

            travelers=travelers, 

            travel_style=travel_style, 

            language=language, 

            interests=interests, 

            evidence=evidence, 

        ) 

    except TypeError: 

        pass 

raise RuntimeError( 

    "TrekTalesCrew was loaded, but it does not provide " 

    "a compatible run(), kickoff(), plan(), or generate() method." 

) 

def verify_payment_safely(
 payment_data,
 ):
 """
 Call the project's deterministic payment verifier.
 """

verify_payment = safe_import_payment() 

try: 

    return verify_payment( 

        payment_data, 

    ) 

except TypeError: 

    pass 

return verify_payment( 

    recipient=payment_data.get( 

        "recipient", 

        "", 

    ), 

    amount=payment_data.get( 

        "amount", 

        0, 

    ), 

    status=payment_data.get( 

        "status", 

        "", 

    ), 

) 

def is_payment_verified(
 result,
 ):
 """
 Normalize verifier output.
 """

if isinstance( 

    result, 

    bool, 

): 

    return result 

if isinstance( 

    result, 

    dict, 

): 

    return bool( 

        result.get( 

            "verified", 

            result.get( 

                "success", 

                False, 

            ), 

        ) 

    ) 

return False 

def validate_requested_days(
 days,
 ):
 try:

    days = int(days) 

except Exception: 

    days = 1 

return max( 

    1, 

    min( 

        days, 

        PAID_DAYS, 

    ), 

) 

**============================================================**

**BRAND**

**============================================================**

with st.container(
 key="top_brand",
 ):

st.markdown( 

    "# TrekTales" 

) 

st.markdown( 

    "AI Multi-Agent Travel Planner" 

) 

**============================================================**

**SIDEBAR**

**============================================================**

with st.sidebar:

st.markdown( 

    "## 🌿 TrekTales" 

) 

st.markdown( 

    "Plan smarter trips with AI-powered travel agents." 

) 

st.divider() 

with st.container( 

    border=True, 

    key="sidebar_access", 

): 

    st.markdown( 

        "### 🔐 Access Model" 

    ) 

    st.markdown( 

        f"\*\*Day {FREE_DAYS}:\*\* Free" 

    ) 

    st.markdown( 

        f"\*\*Days {FREE_DAYS + 1}–{PAID_DAYS}:\*\* " 

        f"Rs. {UNLOCK_PRICE}" 

    ) 

    if st.session_state.payment_verified: 

        st.success( 

            "Premium unlocked" 

        ) 

    else: 

        st.info( 

            "Premium locked" 

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

st.markdown( 

    "### 🤖 AI Agents" 

) 

agents = [ 

    ( 

        1, 

        "Master Orchestrator", 

        "Coordinates the travel workflow.", 

    ), 

    ( 

        2, 

        "Knowledge Agent", 

        "Retrieves information from FAISS.", 

    ), 

    ( 

        3, 

        "Planner Agent", 

        "Creates the itinerary.", 

    ), 

    ( 

        4, 

        "Budget Agent", 

        "Handles budget-aware planning.", 

    ), 

    ( 

        5, 

        "Safety Agent", 

        "Provides safety guidance.", 

    ), 

    ( 

        6, 

        "Summarizer Agent", 

        "Creates the final summary.", 

    ), 

    ( 

        7, 

        "Payment Agent", 

        "Handles payment verification.", 

    ), 

    ( 

        8, 

        "Vision Agent", 

        "Analyzes payment screenshots.", 

    ), 

] 

for ( 

    number, 

    name, 

    description, 

) in agents: 

    with st.container( 

        border=True, 

        key=f"agent\_{number}", 

    ): 

        st.markdown( 

            f"\*\*AGENT {number:02d}\*\*" 

        ) 

        st.markdown( 

            f"\*\*{name}\*\*" 

        ) 

        st.caption( 

            description 

        ) 

st.divider() 

st.caption( 

    f"Groq model: {GROQ_MODEL}" 

) 

**============================================================**

**HERO**

**============================================================**

with st.container(
 border=True,
 key="hero",
 ):

st.markdown( 

    "## 🌍 Plan Your Next Adventure" 

) 

st.markdown( 

    "Create personalized travel plans using a " 

    "multi-agent AI system grounded in your tourism " 

    "knowledge base." 

) 

st.markdown( 

    "📚 Knowledge Grounding  •  " 

    "🗺️ Smart Planning  •  " 

    "💰 Budget Awareness  •  " 

    "🛡️ Safety  •  " 

    "👁️ Vision Verification" 

) 

**============================================================**

**FEATURES**

**============================================================**

st.markdown(
 "## ✨ TrekTales Features"
 )

feature_columns = st.columns(3)

with feature_columns[0]:

with st.container( 

    border=True, 

    key="feature_knowledge", 

): 

    st.markdown( 

        "### 🧠 Knowledge Grounding" 

    ) 

    st.write( 

        "Uses your tourism knowledge base and " 

        "FAISS retrieval to ground recommendations." 

    ) 

with feature_columns[1]:

with st.container( 

    border=True, 

    key="feature_agents", 

): 

    st.markdown( 

        "### 🤖 8 AI Agents" 

    ) 

    st.write( 

        "Specialized agents support research, " 

        "planning, budgeting, safety and verification." 

    ) 

with feature_columns[2]:

with st.container( 

    border=True, 

    key="feature_payment", 

): 

    st.markdown( 

        "### 💳 Premium Unlock" 

    ) 

    st.write( 

        f"Day 1 is free. Additional days " 

        f"require the Rs. {UNLOCK_PRICE} unlock." 

    ) 

st.divider()

**============================================================**

**TRIP INPUT**

**============================================================**

st.markdown(
 "## 🧭 Create Your Rawalpindi Trip"
 )

st.caption(
 "Tell TrekTales about your trip and it will build a "
 "Rawalpindi itinerary using your tourism knowledge base."
 )

input_col1, input_col2 = st.columns(2)

**============================================================**

**LEFT COLUMN**

**============================================================**

with input_col1:

destination = "Rawalpindi" 

st.markdown( 

    """ 

    \<div class="destination-box"> 

        \<div class="destination-label">📍 Destination\</div> 

        \<div class="destination-value">RAWALPINDI\</div> 

    \</div> 

    """, 

    unsafe_allow_html=True, 

) 

starting_location = st.text_input( 

    "🚗 Where will you start your journey?", 

    placeholder="e.g. Islamabad", 

) 

requested_duration = st.selectbox( 

    "📅 How long do you want to explore Rawalpindi?", 

    options=[1, 2, 3], 

    format_func=lambda x: ( 

        "1 Day — Quick Trip" 

        if x == 1 

        else "2 Days — Explore More" 

        if x == 2 

        else "3 Days — Full Experience" 

    ), 

) 

travelers = st.number_input( 

    "👥 How many people are traveling?", 

    min_value=1, 

    max_value=20, 

    value=2, 

    step=1, 

) 

**============================================================**

**RIGHT COLUMN**

**============================================================**

with input_col2:

budget_options = { 

    "Budget — PKR 1,500–3,000/person/day": 

        "Budget — PKR 1,500–3,000 per person per day", 

    "Moderate — PKR 3,000–6,000/person/day": 

        "Moderate — PKR 3,000–6,000 per person per day", 

    "Comfortable — PKR 6,000–10,000/person/day": 

        "Comfortable — PKR 6,000–10,000 per person per day", 

    "Premium — PKR 10,000–20,000+/person/day": 

        "Premium — PKR 10,000–20,000+ per person per day", 

} 

budget_label = st.selectbox( 

    "💰 What is your approximate daily budget?", 

    list( 

        budget_options.keys() 

    ), 

) 

budget = budget_options[ 

    budget_label 

] 

travel_style = st.selectbox( 

    "🎒 What type of Rawalpindi trip do you prefer?", 

    [ 

        "Adventure", 

        "Relaxed", 

        "Family", 

        "Romantic", 

        "Cultural", 

        "Nature", 

        "Photography", 

        "Mixed", 

    ], 

) 

interests = st.multiselect( 

    "⭐ What would you like to explore?", 

    [ 

        "Mountains", 

        "Nature", 

        "Food", 

        "Culture", 

        "History", 

        "Photography", 

        "Adventure", 

        "Shopping", 

        "Family Activities", 

        "Nightlife", 

    ], 

    default=[ 

        "Nature", 

        "Photography", 

    ], 

) 

**============================================================**

**ACCESS CALCULATION**

**============================================================**

requested_duration = validate_requested_days(
 requested_duration
 )

if st.session_state.payment_verified:

accessible_duration = ( 

    requested_duration 

) 

else:

accessible_duration = min( 

    requested_duration, 

    FREE_DAYS, 

) 

**============================================================**

**PREMIUM NOTICE**

**============================================================**

if (
 requested_duration > FREE_DAYS
 and not st.session_state.payment_verified
 ):

st.warning( 

    f"You selected {requested_duration} days. " 

    f"Only Day 1 is currently available. " 

    f"Unlock premium for Rs. {UNLOCK_PRICE} " 

    f"to generate all requested days." 

) 

st.divider()

**============================================================**

**SYSTEM STATUS**

**============================================================**

st.markdown(
 "## ⚙️ System Status"
 )

status_col1, status_col2, status_col3 = st.columns(3)

with status_col1:

with st.container( 

    border=True, 

    key="status_groq", 

): 

    st.markdown( 

        "### 🧠 AI Model" 

    ) 

    if GROQ_API_KEY: 

        st.success( 

            "Groq API key detected" 

        ) 

    else: 

        st.error( 

            "Groq API key not found" 

        ) 

with status_col2:

with st.container( 

    border=True, 

    key="status_faiss", 

): 

    st.markdown( 

        "### 📚 Knowledge Base" 

    ) 

    index_exists = ( 

        FAISS_INDEX_PATH.exists() 

    ) 

    metadata_exists = ( 

        FAISS_METADATA_PATH.exists() 

    ) 

    config_exists = ( 

        FAISS_CONFIG_PATH.exists() 

    ) 

    if ( 

        index_exists 

        and metadata_exists 

    ): 

        st.success( 

            "FAISS index ready" 

        ) 

    else: 

        st.error( 

            "FAISS index not found" 

        ) 

    st.caption( 

        f"index.faiss: " 

        f"{'✓' if index_exists else '✗'}" 

    ) 

    st.caption( 

        f"metadata.json: " 

        f"{'✓' if metadata_exists else '✗'}" 

    ) 

    st.caption( 

        f"config.json: " 

        f"{'✓' if config_exists else '✗'}" 

    ) 

with status_col3:

with st.container( 

    border=True, 

    key="status_agents", 

): 

    st.markdown( 

        "### 🤖 Agent System" 

    ) 

    st.success( 

        "8-agent architecture configured" 

    ) 

    st.caption( 

        f"Active planning days: " 

        f"{accessible_duration}" 

    ) 

st.divider()

**============================================================**

**GENERATE BUTTON**

**============================================================**

generate_trip = st.button(
 "🚀 Generate My TrekTales Plan",
 use_container_width=True,
 )

**============================================================**

**GENERATION**

**IMPORTANT:**

**Everything below executes ONLY when the user clicks**

**Generate.**

**============================================================**

if generate_trip:

\# -------------------------------------------------------- 

\# VALIDATION 

\# -------------------------------------------------------- 

if not destination.strip(): 

    st.error( 

        "Please enter a destination." 

    ) 

    st.stop() 

if not starting_location.strip(): 

    st.error( 

        "Please enter your starting location." 

    ) 

    st.stop() 

if not GROQ_API_KEY: 

    st.error( 

        "GROQ_API_KEY is missing from Streamlit Secrets." 

    ) 

    st.stop() 

if not FAISS_INDEX_PATH.exists(): 

    st.error( 

        "FAISS index not found at " 

        "\`faiss_db/index.faiss\`." 

    ) 

    st.stop() 

if not FAISS_METADATA_PATH.exists(): 

    st.error( 

        "FAISS metadata not found at " 

        "\`faiss_db/metadata.json\`." 

    ) 

    st.stop() 

\# -------------------------------------------------------- 

\# CLEAR PREVIOUS RESULT 

\# -------------------------------------------------------- 

st.session_state.trip_result = None 

st.session_state.trip_evidence = [] 

st.session_state.last_error = None 

\# -------------------------------------------------------- 

\# RETRIEVAL + GENERATION 

\# -------------------------------------------------------- 

with st.status( 

    "🔎 Preparing your TrekTales trip...", 

    expanded=True, 

) as status: 

    st.write( 

        "Loading the tourism knowledge base..." 

    ) 

    # ---------------------------------------------------- 

    # RETRIEVER 

    # ---------------------------------------------------- 

    try: 

        RetrieverClass = ( 

            safe_import_retriever() 

        ) 

        retriever = RetrieverClass( 

            index_path=FAISS_INDEX_PATH, 

            metadata_path=FAISS_METADATA_PATH, 

            config_path=FAISS_CONFIG_PATH, 

        ) 

        query = ( 

            f"Destination: {destination}. " 

            f"Starting location: {starting_location}. " 

            f"Trip duration: {accessible_duration} days. " 

            f"Budget: {budget}. " 

            f"Travel style: {travel_style}. " 

            f"Travelers: {travelers}. " 

            f"Interests: " 

            f"{', '.join(interests)}." 

        ) 

        evidence = retrieve_with_retriever( 

            retriever, 

            query, 

        ) 

        if evidence is None: 

            evidence = [] 

        st.session_state.trip_evidence = ( 

            evidence 

        ) 

        st.write( 

            f"Retrieved {len(evidence)} " 

            f"knowledge items." 

        ) 

        if not evidence: 

            st.warning( 

                "No tourism knowledge-base evidence " 

                "was retrieved. The itinerary generator " 

                "will not invent missing tourism facts." 

            ) 

    except Exception as exc: 

        status.update( 

            label="❌ Knowledge retrieval failed", 

            state="error", 

            expanded=True, 

        ) 

        st.error( 

            "The FAISS retriever could not be loaded." 

        ) 

        st.exception(exc) 

        st.stop() 

    # ---------------------------------------------------- 

    # PREMIUM DAY ENFORCEMENT 

    # ---------------------------------------------------- 

    if ( 

        requested_duration > FREE_DAYS 

        and not st.session_state.payment_verified 

    ): 

        st.info( 

            "Premium is locked. " 

            "The AI will generate Day 1 only." 

        ) 

    # ---------------------------------------------------- 

    # CREW 

    # ---------------------------------------------------- 

    st.write( 

        "🤖 Activating TrekTales AI agents..." 

    ) 

    try: 

        CrewClass = safe_import_crew() 

        crew = CrewClass() 

        result = run_crew( 

            crew=crew, 

            destination=destination, 

            duration=accessible_duration, 

            budget=budget, 

            travelers=travelers, 

            travel_style=travel_style, 

            language=language, 

            interests=interests, 

            starting_location=starting_location, 

            evidence=evidence, 

        ) 

        st.session_state.trip_result = ( 

            result 

        ) 

        status.update( 

            label="✅ TrekTales plan generated!", 

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

            "The TrekTales AI crew could not " 

            "generate the itinerary." 

        ) 

        st.exception(exc) 

        st.stop() 

**============================================================**

**DISPLAY RESULT**

**============================================================**

if st.session_state.trip_result:

st.divider() 

st.markdown( 

    "## 🗺️ Your TrekTales Plan" 

) 

if st.session_state.payment_verified: 

    st.success( 

        f"Premium itinerary: " 

        f"{accessible_duration} day(s)" 

    ) 

elif requested_duration > FREE_DAYS: 

    st.info( 

        "Free preview: Day 1" 

    ) 

answer = extract_text_from_result( 

    st.session_state.trip_result 

) 

answer = clean_text( 

    answer 

) 

with st.container( 

    border=True, 

    key="answer_card", 

): 

    st.markdown( 

        "### 🌿 Personalized Itinerary" 

    ) 

    st.markdown( 

        answer, 

        unsafe_allow_html=False, 

    ) 

**============================================================**

**SOURCES**

**============================================================**

sources = extract_sources(
 st.session_state.trip_evidence
 )

if sources:

st.divider() 

st.markdown( 

    "## 📚 Knowledge Sources" 

) 

for index, source in enumerate( 

    sources 

): 

    with st.container( 

        border=True, 

        key=f"source\_{index}", 

    ): 

        st.markdown( 

            f"\*\*📄 {source['source']}\*\*" 

        ) 

        if ( 

            source["page"] 

            and source["page"].lower() 

            != "n/a" 

        ): 

            st.caption( 

                f"Page: {source['page']}" 

            ) 

**============================================================**

**PREMIUM SECTION**

**============================================================**

if requested_duration >= 2:

st.divider() 

st.markdown( 

    "## 🔐 Unlock Additional Days" 

) 

with st.container( 

    border=True, 

    key="locked_card", 

): 

    if st.session_state.payment_verified: 

        st.markdown( 

            "### 🔓 Premium Unlocked" 

        ) 

        st.markdown( 

            f"You can now generate all " 

            f"{requested_duration} requested days." 

        ) 

    else: 

        st.markdown( 

            "### 🔒 Days 2–3 Are Locked" 

        ) 

        st.markdown( 

            f"Day 1 is free. " 

            f"Unlock the premium itinerary for " 

            f"\*\*Rs. {UNLOCK_PRICE}\*\*." 

        ) 

\# -------------------------------------------------------- 

\# PAYMENT 

\# -------------------------------------------------------- 

if not st.session_state.payment_verified: 

    with st.container( 

        border=True, 

        key="payment_card", 

    ): 

        st.markdown( 

            "### 💳 Payment Verification" 

        ) 

        st.write( 

            f"Payment amount: " 

            f"\*\*Rs. {UNLOCK_PRICE}\*\*" 

        ) 

        st.write( 

            f"Recipient: " 

            f"\*\*{EXPECTED_PAYMENT_RECIPIENT}\*\*" 

        ) 

        if QR_PATH.exists(): 

            st.image( 

                str(QR_PATH), 

                caption="TrekTales Payment QR", 

                width=260, 

            ) 

        else: 

            st.warning( 

                "Payment QR not found at " 

                "\`assets/jazzcash_qr.jpg\`." 

            ) 

        uploaded_screenshot = ( 

            st.file_uploader( 

                "📸 Upload payment screenshot", 

                type=[ 

                    "png", 

                    "jpg", 

                    "jpeg", 

                    "webp", 

                ], 

                key="payment_screenshot", 

            ) 

        ) 

        if uploaded_screenshot: 

            verify_button = st.button( 

                "🔍 Verify Payment Screenshot", 

                use_container_width=True, 

            ) 

            if verify_button: 

                with st.spinner( 

                    "👁️ Vision Agent is analyzing " 

                    "the screenshot..." 

                ): 

                    try: 

                        analyze_payment_screenshot = ( 

                            safe_import_vision() 

                        ) 

                        try: 

                            vision_result = ( 

                                analyze_payment_screenshot( 

                                    uploaded_screenshot 

                                ) 

                            ) 

                        except TypeError: 

                            uploaded_screenshot.seek( 

                                0 

                            ) 

                            vision_result = ( 

                                analyze_payment_screenshot( 

                                    uploaded_screenshot.read() 

                                ) 

                            ) 

                        st.session_state.vision_result = ( 

                            vision_result 

                        ) 

                    except Exception as exc: 

                        st.error( 

                            "Vision Agent could not analyze " 

                            "the payment screenshot." 

                        ) 

                        st.exception(exc) 

                        st.stop() 

                # ------------------------------------------------ 

                # VISION RESULT 

                # ------------------------------------------------ 

                vision = ( 

                    st.session_state.vision_result 

                ) 

                if isinstance( 

                    vision, 

                    dict, 

                ): 

                    recipient = str( 

                        vision.get( 

                            "recipient", 

                            "", 

                        ) 

                    ).strip() 

                    amount = vision.get( 

                        "amount", 

                        0, 

                    ) 

                    payment_status = str( 

                        vision.get( 

                            "status", 

                            "", 

                        ) 

                    ).strip() 

                    confidence = vision.get( 

                        "confidence", 

                        "", 

                    ) 

                else: 

                    st.error( 

                        "Vision Agent returned an " 

                        "unexpected response format." 

                    ) 

                    st.stop() 

                st.markdown( 

                    "### 👁️ Screenshot Analysis" 

                ) 

                metric1, metric2, metric3 = ( 

                    st.columns(3) 

                ) 

                with metric1: 

                    st.metric( 

                        "Recipient", 

                        recipient 

                        if recipient 

                        else "Not detected", 

                    ) 

                with metric2: 

                    st.metric( 

                        "Amount", 

                        f"Rs. {amount}", 

                    ) 

                with metric3: 

                    st.metric( 

                        "Status", 

                        payment_status 

                        if payment_status 

                        else "Not detected", 

                    ) 

                if confidence: 

                    st.caption( 

                        f"Vision confidence: " 

                        f"{confidence}" 

                    ) 

                # ------------------------------------------------ 

                # DETERMINISTIC PAYMENT CHECK 

                # ------------------------------------------------ 

                payment_data = { 

                    "recipient": recipient, 

                    "amount": amount, 

                    "status": payment_status, 

                } 

                try: 

                    payment_result = ( 

                        verify_payment_safely( 

                            payment_data 

                        ) 

                    ) 

                except Exception as exc: 

                    st.error( 

                        "The deterministic payment verifier " 

                        "could not validate the result." 

                    ) 

                    st.exception(exc) 

                    st.stop() 

                st.session_state.payment_result = ( 

                    payment_result 

                ) 

                verified = ( 

                    is_payment_verified( 

                        payment_result 

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

                        "Generate your itinerary again " 

                        "to create all requested days." 

                    ) 

                else: 

                    st.error( 

                        "❌ Payment could not be verified." 

                    ) 

                    st.warning( 

                        "The recipient, amount and payment " 

                        "status did not satisfy the application's " 

                        "verification rules." 

                    ) 

else: 

    st.success( 

        "🔓 Premium access is active for this session." 

    ) 

    if st.button( 

        "🔒 Reset Premium Session", 

        use_container_width=True, 

    ): 

        st.session_state.payment_verified = False 

        st.session_state.payment_result = None 

        st.session_state.vision_result = None 

        st.rerun() 

**============================================================**

**DISCLAIMER**

**============================================================**

st.divider()

with st.container(
 border=True,
 key="disclaimer_card",
 ):

st.markdown( 

    "\*\*Important:\*\* TrekTales provides tourism planning " 

    "information for general informational purposes. " 

    "Travel conditions, prices, availability, weather, " 

    "transport schedules and local rules can change. " 

    "Verify important details with current or official " 

    "sources before travelling." 

) 

**============================================================**

**FOOTER**

**============================================================**

st.markdown("---")

footer_col1, footer_col2, footer_col3 = (
 st.columns(3)
 )

with footer_col1:

st.markdown( 

    "🌿 \*\*TrekTales\*\*" 

) 

with footer_col2:

st.markdown( 

    "AI Multi-Agent Travel Planner" 

) 

with footer_col3:

st.markdown( 

    "Built with Streamlit + Groq" 

).........crew\\.py    from \_\_future\_\_ import annotations

import time
 from typing import Any

import requests
 import streamlit as st

class TrekTalesCrew:
 """
 TrekTales itinerary generation client.

Uses Groq's OpenAI-compatible HTTP API.

The itinerary is generated strictly from the tourism

knowledge-base evidence supplied by the FAISS retriever.

"""

def \_\_init\_\_(self):

    self.base_url = self.\_get_secret(

        "GROQ_BASE_URL",

        "[https://api.groq.com/openai/v1](https://api.groq.com/openai/v1)",

    ).rstrip("/")

    self.model = self.\_get_secret(

        "GROQ_MODEL",

        "openai/gpt-oss-120b",

    )

    # Keep retries deliberately small so the app does not

    # repeatedly hammer Groq during a rate-limit event.

    self.max_retries = 2

\# ========================================================

\# SECRET

\# ========================================================

@staticmethod

def \_get_secret(name: str, default: str = "") -> str:

    try:

        value = st.secrets.get(name, default)

        if value is None:

            return default

        return str(value).strip()

    except Exception:

        return default

\# ========================================================

\# API KEY

\# ========================================================

def \_get_api_key(self) -> str:

    key = self.\_get_secret("GROQ_API_KEY", "")

    if not key:

        raise RuntimeError(

            "GROQ_API_KEY is missing from Streamlit Secrets. "

            "Open Streamlit Cloud → Settings → Secrets and add "

            "your valid Groq API key."

        )

    if not key.startswith("gsk\_"):

        raise RuntimeError(

            "GROQ_API_KEY does not appear to be a valid Groq API key. "

            "Check the value in Streamlit Secrets."

        )

    return key

\# ========================================================

\# EVIDENCE FORMATTER

\# ========================================================

@staticmethod

def \_format_evidence(evidence: list[Any]) -> str:

    """

    Convert retrieved FAISS evidence into a clean context

    block for the language model.

    No information is added that was not present in evidence.

    """

    if not evidence:

        return (

            "No tourism knowledge-base evidence was retrieved."

        )

    blocks = []

    for index, item in enumerate(evidence, start=1):

        if isinstance(item, dict):

            # Some retrievers store metadata at the top level,

            # while others store it inside item["metadata"].

            metadata = item.get("metadata", {})

            if not isinstance(metadata, dict):

                metadata = {}

            text = (

                item.get("text")

                or item.get("content")

                or item.get("chunk")

                or metadata.get("text")

                or metadata.get("content")

                or ""

            )

            source = (

                item.get("source")

                or item.get("document")

                or item.get("filename")

                or metadata.get("source")

                or metadata.get("document")

                or metadata.get("filename")

                or ""

            )

            page = (

                item.get("page")

                or metadata.get("page")

                or ""

            )

        else:

            text = str(item)

            source = ""

            page = ""

        text = str(text).strip()

        if not text:

            continue

        source_text = str(source).strip()

        if source_text:

            source_text = source_text.replace("\\\\", "/")

            source_text = source_text.split("/")[-1]

        # Remove accidental HTML artifacts from source names.

        source_text = source_text.replace(".html", "")

        if page not in ("", None, "N/A", "n/a"):

            location = f"{source_text} | Page {page}"

        else:

            location = source_text

        blocks.append(

            f"[Knowledge Item {index}]\n"

            f"Source: {location or 'Knowledge Base'}\n"

            f"{text}"

        )

    if not blocks:

        return (

            "No usable tourism knowledge-base evidence "

            "was retrieved."

        )

    return "\n\n".join(blocks)

\# ========================================================

\# PROMPT

\# ========================================================

def \_build_prompt(

    self,

    destination: str,

    starting_location: str,

    days: int,

    budget: str,

    travelers: int,

    travel_style: str,

    language: str,

    interests: list[str],

    evidence: list[Any],

) -> str:

    evidence_text = self.\_format_evidence(evidence)

    interests_text = (

        ", ".join(str(item) for item in interests)

        if interests

        else "No specific interests provided."

    )

    return f"""

You are the TrekTales itinerary-generation engine.

Your task is to create a polished, useful and personalized travel
 itinerary for the user.

CRITICAL RULE:

You MUST use ONLY the tourism knowledge-base evidence provided
 at the end of this prompt.

The knowledge base is the source of truth for tourism facts.

Do NOT use outside knowledge.

**============================================================** 
 **TRIP DETAILS**

Destination:
 {destination}

Starting location:
 {starting_location}

Number of days:
 {days}

Travelers:
 {travelers}

Budget:
 {budget}

Travel style:
 {travel_style}

Language:
 {language}

Interests:
 {interests_text}

**============================================================** 
 **ABSOLUTE ANTI-HALLUCINATION RULES**

1. Never invent tourism information.
2. Never invent:
   - attractions
   - restaurants
   - hotels
   - activities
   - prices
   - entry fees
   - ticket costs
   - travel times
   - distances
   - taxi fares
   - transport routes
   - opening hours
   - closing hours
   - addresses
   - phone numbers
   - contact information
   - availability
   - ratings
   - reviews
   - historical facts
   - weather conditions
   - safety conditions
   - local rules
   - events
   - schedules
3. Never use general knowledge to fill a missing tourism      fact.
4. Never estimate a missing price.
5. Never estimate a missing distance.
6. Never estimate a missing travel time.
7. Never calculate a taxi cost when the necessary      information
         is not explicitly present in the knowledge base.
8. Never create a restaurant, hotel or attraction simply      because
         it would make the itinerary look better.
9. Every tourism recommendation must be supported by the      supplied
         knowledge-base evidence.
10. If information is missing, explicitly write:

Not available in the TrekTales tourism knowledge base.

11. Do not create fake citations.
12. Do not create fake filenames.
13. Do not claim that a source contains information unless      that
          information is actually present in the supplied evidence.
14. Do not output HTML.
15. Do not output Markdown code fences.
16. Use clean Markdown.
17. Follow the requested language.
18. Generate exactly {days} day(s).
19. Do not add an extra day.
20. Do not silently reduce the requested number of days.
21. If the evidence is insufficient for a particular day,
          clearly state that the required information is unavailable
          instead of inventing activities.

**============================================================** 
 **OUTPUT STYLE**

Make the result visually organized and easy to read.

Use:

- Markdown headings
- Bold labels where useful
- Bullet points
- Short paragraphs
- Emojis where appropriate
- Clear day sections
- Practical information
- Knowledge-base source names

Do not use HTML.

Do not use code fences.

**============================================================** 
 **REQUIRED OUTPUT STRUCTURE**

Begin with:

**🌿 Personalized {destination} Adventure Itinerary**

Then provide:

**📍 Trip Overview**

Include:

- Destination
- Starting location
- Duration
- Travelers
- Budget
- Travel style
- Interests

Only use values supplied in the trip details.

**============================================================** 
 **DAY-BY-DAY ITINERARY**

Create exactly {days} day sections.

Use:

**☀️ Day 1 — [appropriate theme]**

Then, if required:

**☀️ Day 2 — [appropriate theme]**

Continue until exactly Day {days}.

For every day, create a useful structure such as:

**⏰ Suggested Schedule**

Use time blocks only when the knowledge base supports
 the timing.

For each supported activity/place, provide:

- Place/activity name
- What is supported by the knowledge base
- Relevant cost, if explicitly available
- Relevant practical information, if explicitly available
- Why it matches the user's stated interests, when this      can
        be supported without inventing facts

Do not manufacture times just to make the itinerary look full.

If a useful detail is missing, write:

Not available in the TrekTales tourism knowledge base.

**============================================================** 
 **TRAVEL / TRANSPORT**

When discussing movement between locations:

Only provide travel time, distance, route, fare or transport
 information if it is explicitly supported by the evidence.

Otherwise write:

Not available in the TrekTales tourism knowledge base.

Never estimate it.

**============================================================** 
 **BUDGET**

After the daily itinerary, provide:

**💰 Budget Considerations**

List only costs explicitly supported by the knowledge base.

If a cost is missing:

Not available in the TrekTales tourism knowledge base.

Do not invent a total.

Do not calculate a total using unsupported values.

**============================================================** 
 **PHOTOGRAPHY**

Provide:

**📸 Photography Highlights**

Only mention locations or activities supported by the knowledge
 base.

Do not invent viewpoints, photo spots, landscapes or photography
 features.

If insufficient information exists:

Not available in the TrekTales tourism knowledge base.

**============================================================** 
 **WHAT TO CARRY**

Provide:

**🎒 What to Carry**

Keep this practical.

Do not invent weather conditions.

Do not claim that a particular item is required because of
 weather or local conditions unless the supplied evidence supports
 that claim.

**============================================================** 
 **IMPORTANT INFORMATION**

Provide:

**⚠️ Important Information**

Include only important information supported by the knowledge base.

For unavailable tourism information:

Not available in the TrekTales tourism knowledge base.

**============================================================** 
 **KNOWLEDGE-BASE SOURCES**

Finish with:

**📚 Knowledge-Base Sources**

List only filenames that actually occur in the supplied evidence.

Use the filename only.

Do not invent filenames.

Do not create fake references.

**============================================================** 
 **LANGUAGE**

Write the complete itinerary in:

{language}

**============================================================** 
 **FINAL VALIDATION BEFORE ANSWERING**

Before producing the final response, internally verify:

- Exactly {days} day(s) are present.
- All tourism facts come from the supplied evidence.
- No attraction was invented.
- No restaurant was invented.
- No hotel was invented.
- No price was invented.
- No travel time was invented.
- No distance was invented.
- No taxi fare was invented.
- No opening hours were invented.
- No fake source was invented.
- Missing information is explicitly marked.
- No HTML exists in the answer.
- No Markdown code fence exists in the answer.
- The destination remains {destination}.
- The response follows the requested language.

**============================================================** 
 **TOURISM KNOWLEDGE-BASE EVIDENCE**

{evidence_text}

**============================================================** 
 **END OF KNOWLEDGE-BASE EVIDENCE**

Now generate the final TrekTales itinerary.
 """

\# ========================================================

\# RATE LIMIT INFORMATION

\# ========================================================

@staticmethod

def \_get_rate_limit_details(

    response: requests.Response,

) -> dict[str, str]:

    headers = response.headers

    return {

        "retry_after": headers.get(

            "retry-after",

            "",

        ),

        "remaining_tokens": headers.get(

            "x-ratelimit-remaining-tokens",

            "",

        ),

        "remaining_requests": headers.get(

            "x-ratelimit-remaining-requests",

            "",

        ),

        "reset_tokens": headers.get(

            "x-ratelimit-reset-tokens",

            "",

        ),

        "reset_requests": headers.get(

            "x-ratelimit-reset-requests",

            "",

        ),

    }

\# ========================================================

\# RATE LIMIT MESSAGE

\# ========================================================

def \_rate_limit_error(

    self,

    response: requests.Response,

    attempt: int,

) -> RuntimeError:

    details = self.\_get_rate_limit_details(response)

    retry_after = details["retry_after"]

    reset_tokens = details["reset_tokens"]

    reset_requests = details["reset_requests"]

    try:

        error_data = response.json()

        error_object = error_data.get(

            "error",

            {},

        )

        if isinstance(error_object, dict):

            message = str(

                error_object.get(

                    "message",

                    "",

                )

            ).strip()

        else:

            message = str(error_object).strip()

    except Exception:

        message = ""

    if retry_after:

        wait_text = (

            f"Groq asked the application to retry after "

            f"{retry_after} seconds."

        )

    elif reset_tokens:

        wait_text = (

            f"The token limit is expected to reset in "

            f"{reset_tokens}."

        )

    elif reset_requests:

        wait_text = (

            f"The request limit is expected to reset in "

            f"{reset_requests}."

        )

    else:

        wait_text = (

            "Groq has temporarily limited this request."

        )

    if attempt >= self.max_retries:

        extra = ""

        if message:

            extra = f" Groq says: {message}"

        return RuntimeError(

            "Groq rate limit is currently active. "

            f"{wait_text}"

            f"{extra} "

            "Please wait for the limit to reset and try "

            "generating the itinerary again."

        )

    return RuntimeError(

        f"Temporary Groq rate limit detected. "

        f"{wait_text}"

    )

\# ========================================================

\# GROQ REQUEST

\# ========================================================

def \_call_groq(

    self,

    prompt: str,

) -> str:

    api_key = self.\_get_api_key()

    url = f"{self.base_url}/chat/completions"

    headers = {

        "Authorization": f"Bearer {api_key}",

        "Content-Type": "application/json",

    }

    payload = {

        "model": self.model,

        "messages": [

            {

                "role": "system",

                "content": (

                    "You are TrekTales, a grounded tourism "

                    "itinerary generation assistant. "

                    "The supplied tourism knowledge base is "

                    "the only source of tourism facts. "

                    "Never invent missing tourism information. "

                    "When information is unavailable, explicitly "

                    "say: Not available in the TrekTales tourism "

                    "knowledge base."

                ),

            },

            {

                "role": "user",

                "content": prompt,

            },

        ],

        "temperature": 0.2,

        "max_tokens": 1800,

        "reasoning_effort": "medium",

    }

    last_response = None

    for attempt in range(

        self.max_retries + 1

    ):

        try:

            response = requests.post(

                url,

                headers=headers,

                json=payload,

                timeout=120,

            )

            last_response = response

        except requests.RequestException as exc:

            if attempt < self.max_retries:

                time.sleep(2)

                continue

            raise RuntimeError(

                "Could not connect to the Groq API. "

                "Please check your internet connection, "

                "GROQ_BASE_URL, and try again."

            ) from exc

        # ====================================================

        # SUCCESS

        # ====================================================

        if response.status_code == 200:

            break

        # ====================================================

        # AUTHENTICATION

        # ====================================================

        if response.status_code in (401, 403):

            try:

                error_data = response.json()

                error_object = error_data.get(

                    "error",

                    {},

                )

                if isinstance(

                    error_object,

                    dict,

                ):

                    message = str(

                        error_object.get(

                            "message",

                            "",

                        )

                    ).strip()

                else:

                    message = str(

                        error_object

                    ).strip()

            except Exception:

                message = ""

            if response.status_code == 403:

                raise RuntimeError(

                    "Groq rejected access to the configured "

                    "model or API resource. "

                    f"Model: {self.model}. "

                    f"{message}"

                )

            raise RuntimeError(

                "Groq authentication failed. "

                "Your GROQ_API_KEY is missing, invalid, "

                "expired, or does not have access to the "

                "configured Groq API. "

                f"{message}"

            )

        # ====================================================

        # MODEL ERROR

        # ====================================================

        if response.status_code == 404:

            try:

                error_data = response.json()

                error_object = error_data.get(

                    "error",

                    {},

                )

                if isinstance(

                    error_object,

                    dict,

                ):

                    message = str(

                        error_object.get(

                            "message",

                            "",

                        )

                    ).strip()

                else:

                    message = str(

                        error_object

                    ).strip()

            except Exception:

                message = ""

            raise RuntimeError(

                "The configured Groq model is unavailable. "

                f"Model: {self.model}. "

                f"{message}"

            )

        # ====================================================

        # RATE LIMIT

        # ====================================================

        if response.status_code == 429:

            if attempt < self.max_retries:

                details = (

                    self.\_get_rate_limit_details(

                        response

                    )

                )

                retry_after = (

                    details["retry_after"]

                )

                wait_seconds = 2.0

                try:

                    if retry_after:

                        wait_seconds = float(

                            retry_after

                        )

                except (

                    TypeError,

                    ValueError,

                ):

                    wait_seconds = 2.0

                wait_seconds = max(

                    1.0,

                    min(

                        wait_seconds,

                        15.0,

                    ),

                )

                time.sleep(

                    wait_seconds

                )

                continue

            raise self.\_rate_limit_error(

                response,

                attempt,

            )

        # ====================================================

        # OTHER API ERRORS

        # ====================================================

        if response.status_code >= 400:

            try:

                error_data = response.json()

                error_object = error_data.get(

                    "error",

                    {},

                )

                if isinstance(

                    error_object,

                    dict,

                ):

                    message = str(

                        error_object.get(

                            "message",

                            "",

                        )

                    ).strip()

                else:

                    message = str(

                        error_object

                    ).strip()

            except Exception:

                message = response.text[:500]

            raise RuntimeError(

                f"Groq API request failed "

                f"(HTTP {response.status_code}). "

                f"{message}"

            )

    # ========================================================

    # SAFETY CHECK

    # ========================================================

    if last_response is None:

        raise RuntimeError(

            "No response was received from Groq."

        )

    # ========================================================

    # RESPONSE JSON

    # ========================================================

    try:

        data = last_response.json()

    except Exception as exc:

        raise RuntimeError(

            "Groq returned an invalid response."

        ) from exc

    # ========================================================

    # CONTENT

    # ========================================================

    try:

        content = (

            data["choices"][0]

            ["message"]

            ["content"]

        )

    except (

        KeyError,

        IndexError,

        TypeError,

    ) as exc:

        raise RuntimeError(

            "Groq returned no itinerary content."

        ) from exc

    if not content or not str(content).strip():

        raise RuntimeError(

            "Groq returned an empty itinerary."

        )

    return str(content).strip()

\# ========================================================

\# MAIN RUN

\# ========================================================

def run(

    self,

    destination: str,

    starting_location: str,

    days: int,

    budget: str,

    travelers: int,

    travel_style: str,

    language: str,

    interests: list[str],

    evidence: list[Any],

) -> str:

    try:

        days = int(days)

    except Exception:

        days = 1

    days = max(

        1,

        min(days, 3),

    )

    try:

        travelers = int(travelers)

    except Exception:

        travelers = 1

    travelers = max(

        1,

        travelers,

    )

    prompt = self.\_build_prompt(

        destination=destination,

        starting_location=starting_location,

        days=days,

        budget=budget,

        travelers=travelers,

        travel_style=travel_style,

        language=language,

        interests=interests,

        evidence=evidence,

    )

    return self.\_call_groq(prompt)

\# ========================================================

\# COMPATIBILITY METHODS

\# ========================================================

def generate(self, \*\*kwargs):

    return self.run(\*\*kwargs)

def plan(self, \*\*kwargs):

    return self.run(\*\*kwargs)

**all** = ["TrekTalesCrew"]
