AGENTS = {
    "master_orchestrator": {
        "name": "Master Orchestrator",
        "role": (
            "Coordinate the complete TrekTales travel-planning "
            "workflow and ensure every output remains grounded."
        ),
    },

    "knowledge": {
        "name": "Knowledge Agent",
        "role": (
            "Interpret only the tourism information supplied "
            "by the retrieval system."
        ),
    },

    "planner": {
        "name": "Planner Agent",
        "role": (
            "Construct an itinerary for exactly the requested "
            "number of days."
        ),
    },

    "budget": {
        "name": "Budget Agent",
        "role": (
            "Keep the proposed itinerary consistent with the "
            "user's supplied budget."
        ),
    },

    "safety": {
        "name": "Safety Agent",
        "role": (
            "Identify safety-related information only when it "
            "is supported by the tourism knowledge base."
        ),
    },

    "summarizer": {
        "name": "Summarizer Agent",
        "role": (
            "Produce a clear and readable final itinerary."
        ),
    },

    "payment": {
        "name": "Payment Agent",
        "role": (
            "Describe access/payment state without independently "
            "granting paid access."
        ),
    },

    "vision": {
        "name": "Vision Agent",
        "role": (
            "Extract visible payment information from an uploaded "
            "payment screenshot."
        ),
    },
}


def get_agent_descriptions():
    lines = []

    for key, agent in AGENTS.items():

        lines.append(
            f"{agent['name']}: {agent['role']}"
        )

    return "\n".join(lines)
