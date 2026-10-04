from crewai import Task


def create_tasks(agents):
    """
    Create the TrekTales travel-planning workflow.

    Required agents:
        knowledge
        planner
        budget
        safety
        summarizer
    """

    # ---------------------------------------------------------
    # 1. KNOWLEDGE TASK
    # ---------------------------------------------------------
    knowledge_task = Task(
        description="""
Find the most relevant information from the tourism knowledge base.

Destination: {destination}
Duration: {duration}
Traveler type: {traveler_type}
Interests: {interests}
Budget: {budget}

Retrieved knowledge:
{evidence}

Rules:
- Use only information supported by the retrieved knowledge.
- Never invent facts, prices, addresses, schedules, opening hours,
  warnings, or policies.
- If no useful knowledge was retrieved, explicitly state that.
- Keep the response short and focused.
- Include source filenames when available.
""",
        expected_output=(
            "A concise evidence summary containing only relevant "
            "supported travel information and source filenames."
        ),
        agent=agents["knowledge"],
    )

    # ---------------------------------------------------------
    # 2. PLANNER TASK
    # ---------------------------------------------------------
    planner_task = Task(
        description="""
Create a practical itinerary for the user's trip.

Destination: {destination}
Duration: {duration}
Traveler type: {traveler_type}
Interests: {interests}
Budget: {budget}
Language: {language}

Knowledge findings:
{knowledge_output}

Rules:
- Prefer recommendations supported by the knowledge findings.
- Do not present unsupported information as verified facts.
- If the knowledge base contains no useful information, clearly label
  recommendations as general suggestions.
- Do not invent exact prices or schedules.
- Keep the itinerary concise.
- Avoid repeating information.

For each day include:
- Main places or activities
- Approximate sequence
- Meal suggestion
- Practical or transport note when useful
""",
        expected_output=(
            "A concise day-by-day itinerary containing activities, "
            "places, meal suggestions, and practical notes."
        ),
        agent=agents["planner"],
        context=[knowledge_task],
    )

    # ---------------------------------------------------------
    # 3. BUDGET TASK
    # ---------------------------------------------------------
    budget_task = Task(
        description="""
Prepare a simple and transparent trip budget.

Destination: {destination}
Duration: {duration}
Budget: {budget}

Knowledge findings:
{knowledge_output}

Planned itinerary:
{planner_output}

Rules:
- Never invent exact prices.
- Use exact amounts only when supported by the knowledge.
- Clearly label estimated amounts.
- If reliable prices are unavailable, say so.
- Keep the response concise.

Cover:
- Accommodation
- Transport
- Food
- Activities
- Miscellaneous
- Estimated total
""",
        expected_output=(
            "A concise budget breakdown with known amounts, "
            "estimates, and important assumptions."
        ),
        agent=agents["budget"],
        context=[knowledge_task, planner_task],
    )

    # ---------------------------------------------------------
    # 4. SAFETY TASK
    # ---------------------------------------------------------
    safety_task = Task(
        description="""
Review the proposed itinerary for practical travel safety.

Destination: {destination}
Duration: {duration}
Traveler type: {traveler_type}

Knowledge findings:
{knowledge_output}

Planned itinerary:
{planner_output}

Rules:
- Do not invent incidents, warnings, emergency numbers, weather,
  road conditions, or government advisories.
- Location-specific safety claims must be supported by the knowledge.
- Clearly label general precautions as general precautions.
- Keep the response short and practical.
""",
        expected_output=(
            "A concise safety section containing supported safety "
            "information and clearly labelled general precautions."
        ),
        agent=agents["safety"],
        context=[knowledge_task, planner_task],
    )

    # ---------------------------------------------------------
    # 5. FINAL SUMMARY TASK
    # ---------------------------------------------------------
    summary_task = Task(
        description="""
Create the final TrekTales travel plan.

Destination: {destination}
Duration: {duration}
Traveler type: {traveler_type}
Interests: {interests}
Budget: {budget}
Language: {language}

Knowledge:
{knowledge_output}

Itinerary:
{planner_output}

Budget:
{budget_output}

Safety:
{safety_output}

Create the final answer using:

1. Trip Overview
2. Day-by-Day Itinerary
3. Budget
4. Safety Tips
5. Sources and Limitations

Rules:
- Do not invent verified facts.
- Do not present estimated prices as exact prices.
- Mention source filenames when available.
- If no useful knowledge was retrieved, clearly state that some
  recommendations are general suggestions.
- Respect the requested language.
- Do not repeat information unnecessarily.
- Keep the final answer concise and practical.
""",
        expected_output=(
            "A polished and concise travel plan containing a trip "
            "overview, day-by-day itinerary, budget, safety tips, "
            "and sources or limitations."
        ),
        agent=agents["summarizer"],
        context=[
            knowledge_task,
            planner_task,
            budget_task,
            safety_task,
        ],
    )

    return [
        knowledge_task,
        planner_task,
        budget_task,
        safety_task,
        summary_task,
    ]

