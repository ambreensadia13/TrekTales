from crewai import Agent

from .config import XAI_API_KEY, TEXT_MODEL, XAI_BASE_URL


def create_grok_llm():
    """
    Create one xAI/Grok LLM configuration for CrewAI.

    xAI exposes an OpenAI-compatible API endpoint.
    """
    if not XAI_API_KEY:
        raise RuntimeError(
            "XAI_API_KEY is missing from Streamlit Secrets."
        )

    from crewai import LLM

    return LLM(
        model=TEXT_MODEL,
        api_key=XAI_API_KEY,
        base_url=XAI_BASE_URL,
        custom_openai=True,
        temperature=0.1,
    )


def grounding_rules() -> str:
    return """
STRICT GROUNDING RULES:

1. Use only the supplied tourism knowledge-base evidence.
2. Never invent tourism facts.
3. Never invent hotel names.
4. Never invent addresses.
5. Never invent opening hours.
6. Never invent ticket prices.
7. Never invent transport fares.
8. Never invent safety statistics.
9. Never invent phone numbers.
10. Never invent emergency contacts.
11. Never use general model memory as tourism evidence.
12. If the evidence does not contain an answer, explicitly say:
   "Information not found in the tourism knowledge base."
13. Preserve source names and page numbers.
14. Do not turn estimates into confirmed prices.
15. Distinguish between knowledge-base facts and user-provided information.
"""


def create_knowledge_agent(llm) -> Agent:
    return Agent(
        role="Tourism Knowledge Specialist",
        goal=(
            "Retrieve and explain only tourism facts that are "
            "supported by the supplied knowledge-base evidence."
        ),
        backstory=(
            "You are the evidence specialist of TrekTales. "
            "You never fill missing information with guesses. "
            "Every factual statement must be traceable to supplied evidence."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=False,
    )


def create_planner_agent(llm) -> Agent:
    return Agent(
        role="Travel Itinerary Planner",
        goal=(
            "Create practical day-by-day itineraries using only "
            "places, activities, transport information and constraints "
            "contained in the supplied evidence."
        ),
        backstory=(
            "You design organized travel plans. You never invent "
            "attractions or schedules that are absent from the evidence."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=False,
    )


def create_budget_agent(llm) -> Agent:
    return Agent(
        role="Travel Budget Specialist",
        goal=(
            "Calculate transparent travel budgets from user-provided "
            "values and prices explicitly present in the evidence."
        ),
        backstory=(
            "You are conservative with money. If a current price is "
            "not present in the knowledge base or supplied by the user, "
            "you mark it as unavailable instead of guessing."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=False,
    )


def create_safety_agent(llm) -> Agent:
    return Agent(
        role="Travel Safety Specialist",
        goal=(
            "Provide safety considerations supported by the tourism "
            "safety knowledge base."
        ),
        backstory=(
            "You focus on practical travel safety and clearly separate "
            "documented guidance from unknown information."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=False,
    )


def create_summarizer_agent(llm) -> Agent:
    return Agent(
        role="Senior Travel Guide Summarizer",
        goal=(
            "Combine the specialist outputs into a concise, useful, "
            "grounded TrekTales response with citations."
        ),
        backstory=(
            "You are the final editor. You remove unsupported claims "
            "and preserve the source references supplied by the specialists."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=False,
    )


def create_payment_agent(llm) -> Agent:
    return Agent(
        role="Payment Access Manager",
        goal=(
            "Manage the TrekTales demo access state using deterministic "
            "validation results supplied by Python."
        ),
        backstory=(
            "You never claim that an image proves a real payment. "
            "You only interpret the deterministic validation result."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=False,
    )


def create_vision_agent(llm) -> Agent:
    return Agent(
        role="Payment Screenshot Vision Specialist",
        goal=(
            "Extract visible payment fields from a payment screenshot "
            "without inventing unreadable information."
        ),
        backstory=(
            "You inspect payment screenshots and report only visible "
            "recipient, amount and status information."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=False,
    )
