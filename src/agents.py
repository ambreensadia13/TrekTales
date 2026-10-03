from crewai import Agent, LLM

from .config import GROQ_API_KEY, GROQ_MODEL


# ============================================================
# GROQ LLM
# ============================================================

def get_groq_llm():
    """
    Creates the Groq LLM used by all TrekTales agents.
    """

    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is missing. "
            "Add GROQ_API_KEY to Streamlit Secrets."
        )

    return LLM(
        model=f"groq/{GROQ_MODEL}",
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
        temperature=0.2,
    )


# ============================================================
# AGENT 1 — MASTER ORCHESTRATOR
# ============================================================

def create_master_orchestrator(llm):
    return Agent(
        role="Master Orchestrator",
        goal=(
            "Coordinate the TrekTales travel planning workflow "
            "and ensure that all specialized agents contribute "
            "to a useful and coherent travel plan."
        ),
        backstory=(
            "You are the lead AI travel coordinator for TrekTales. "
            "You organize information from the knowledge, planning, "
            "budget, safety and summarization agents."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=True,
    )


# ============================================================
# AGENT 2 — KNOWLEDGE AGENT
# ============================================================

def create_knowledge_agent(llm):
    return Agent(
        role="Knowledge Agent",
        goal=(
            "Use the supplied tourism knowledge and retrieved "
            "evidence to provide accurate destination information."
        ),
        backstory=(
            "You specialize in tourism knowledge retrieval. "
            "You must prioritize supplied knowledge-base evidence "
            "and avoid inventing unsupported facts."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )


# ============================================================
# AGENT 3 — PLANNER AGENT
# ============================================================

def create_planner_agent(llm):
    return Agent(
        role="Planner Agent",
        goal=(
            "Create a practical day-by-day travel itinerary "
            "based on the destination, duration, travelers, "
            "travel style and interests."
        ),
        backstory=(
            "You are an experienced itinerary planner. "
            "You organize activities logically while considering "
            "travel time, realistic pacing and user preferences."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )


# ============================================================
# AGENT 4 — BUDGET AGENT
# ============================================================

def create_budget_agent(llm):
    return Agent(
        role="Budget Agent",
        goal=(
            "Estimate travel expenses according to the selected "
            "budget level and number of travelers."
        ),
        backstory=(
            "You specialize in practical travel budgeting. "
            "You categorize likely expenses such as transport, "
            "accommodation, food and activities."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )


# ============================================================
# AGENT 5 — SAFETY AGENT
# ============================================================

def create_safety_agent(llm):
    return Agent(
        role="Safety Agent",
        goal=(
            "Identify relevant travel safety considerations "
            "for the selected destination and itinerary."
        ),
        backstory=(
            "You focus on responsible travel planning. "
            "You highlight practical safety considerations "
            "without exaggerating risks."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )


# ============================================================
# AGENT 6 — SUMMARIZER AGENT
# ============================================================

def create_summarizer_agent(llm):
    return Agent(
        role="Summarizer Agent",
        goal=(
            "Turn the work of the other travel agents into "
            "a clear, structured and easy-to-read final plan."
        ),
        backstory=(
            "You are an expert travel-content editor. "
            "You create concise and useful final travel plans "
            "while preserving important details."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )


# ============================================================
# AGENT 7 — PAYMENT AGENT
# ============================================================

def create_payment_agent(llm):
    return Agent(
        role="Payment Agent",
        goal=(
            "Support the TrekTales demo payment workflow and "
            "clearly communicate payment verification results."
        ),
        backstory=(
            "You manage the application's demonstration payment "
            "workflow. You do not claim that a screenshot proves "
            "a real financial transaction."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )


# ============================================================
# AGENT 8 — VISION AGENT
# ============================================================

def create_vision_agent(llm):
    return Agent(
        role="Vision Agent",
        goal=(
            "Analyze payment screenshots and extract visible "
            "recipient, amount, status and confidence information."
        ),
        backstory=(
            "You are a vision-analysis agent used only for the "
            "TrekTales payment demonstration. Your extracted "
            "information is subsequently validated by deterministic "
            "Python logic."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )


# ============================================================
# CREATE ALL AGENTS
# ============================================================

def create_agents():
    """
    Creates all eight TrekTales agents.
    """

    llm = get_groq_llm()

    return {
        "master_orchestrator": create_master_orchestrator(llm),
        "knowledge": create_knowledge_agent(llm),
        "planner": create_planner_agent(llm),
        "budget": create_budget_agent(llm),
        "safety": create_safety_agent(llm),
        "summarizer": create_summarizer_agent(llm),
        "payment": create_payment_agent(llm),
        "vision": create_vision_agent(llm),
    }


# ============================================================
# OPTIONAL LIST INTERFACE
# ============================================================

def get_all_agents():
    """
    Returns the agents as a list.
    Useful if crew.py expects a list.
    """

    agents = create_agents()

    return [
        agents["master_orchestrator"],
        agents["knowledge"],
        agents["planner"],
        agents["budget"],
        agents["safety"],
        agents["summarizer"],
        agents["payment"],
        agents["vision"],
    ]
