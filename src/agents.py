from __future__ import annotations

from crewai import Agent, LLM

from .config import GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL, TEMPERATURE


def get_groq_llm() -> LLM:
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is missing. Add GROQ_API_KEY to Streamlit Secrets."
        )

    return LLM(
        model=f"groq/{GROQ_MODEL}",
        api_key=GROQ_API_KEY,
        base_url=GROQ_BASE_URL,
        temperature=TEMPERATURE,
    )


def create_agents() -> dict[str, Agent]:
    llm = get_groq_llm()

    return {
        "master": Agent(
            role="Master Orchestrator",
            goal="Coordinate a grounded, practical travel-planning workflow.",
            backstory=(
                "You coordinate specialist travel agents. You never replace "
                "retrieved evidence with invented facts."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False,
        ),
        "knowledge": Agent(
            role="Knowledge Agent",
            goal="Extract only useful facts that are supported by retrieved evidence.",
            backstory=(
                "You are a strict tourism knowledge analyst. Every location-specific "
                "claim must be supported by the supplied RAG evidence."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False,
        ),
        "planner": Agent(
            role="Planner Agent",
            goal="Build a concise day-by-day itinerary using only the allowed days.",
            backstory=(
                "You design realistic itineraries while respecting access limits, "
                "traveler count, interests, budget and retrieved evidence."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False,
        ),
        "budget": Agent(
            role="Budget Agent",
            goal="Prepare a transparent budget from supported demo prices and estimates.",
            backstory=(
                "You distinguish clearly between prices explicitly present in the "
                "knowledge base and estimates that cannot be verified."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False,
        ),
        "safety": Agent(
            role="Safety Agent",
            goal="Provide supported safety guidance and clearly label general precautions.",
            backstory=(
                "You never invent emergency numbers, warnings, weather or government "
                "advisories."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False,
        ),
        "summarizer": Agent(
            role="Summarizer Agent",
            goal="Produce the final concise travel plan without adding unsupported facts.",
            backstory=(
                "You combine specialist outputs and preserve source limitations and "
                "access restrictions."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False,
        ),
        "payment": Agent(
            role="Payment Agent",
            goal="Explain the demo payment verification workflow without claiming real transaction access.",
            backstory="You describe deterministic application checks honestly.",
            llm=llm,
            verbose=False,
            allow_delegation=False,
        ),
        "vision": Agent(
            role="Vision Agent",
            goal="Interpret payment screenshot fields when a compatible vision model is used.",
            backstory="You extract visible fields but never declare a payment genuine by vision alone.",
            llm=llm,
            verbose=False,
            allow_delegation=False,
        ),
    }


def get_all_agents() -> list[Agent]:
    return list(create_agents().values())
