```python
from crewai import Task


def create_tasks(agents):
    """
    Create the TrekTales travel-planning tasks.

    Required agents:
        knowledge
        planner
        budget
        safety
        summarizer

    Payment and vision processing should be handled separately by the
    application and are intentionally not included in the normal
    travel-planning workflow.
    """

    # ---------------------------------------------------------
    # 1. KNOWLEDGE TASK
    # ---------------------------------------------------------
    knowledge_task = Task(
        description="""
Use the tourism knowledge-base evidence to find information relevant
to the user's trip.

Trip:
Destination: {destination}
Duration: {duration}
Traveler type: {traveler_type}
Interests: {interests}
Budget: {budget}

Knowledge-base evidence:
{evidence}

Rules:
- Use only information contained in the evidence.
- Do not invent attractions, hotels, prices, opening hours, addresses,
  transport schedules, weather, or safety warnings.
- If the evidence is empty or does not contain relevant information,
  clearly say that the information is unavailable.
- Keep the response concise.
- Preserve useful source filenames when they are available.

Return only the most relevant evidence for planning the trip.
""",
        expected_output="""
A concise evidence summary containing only relevant supported information,
including places, activities, accommodation, transport, food, safety
information, and source filenames when available.
""",
        agent=agents["knowledge"],
    )

    # ---------------------------------------------------------
    # 2. PLANNER TASK
    # ---------------------------------------------------------
    planner_task = Task(
        description="""
Create a practical travel itinerary using the trip information and
the Knowledge Agent's findings.

Trip:
Destination: {destination}
Duration: {duration}
Traveler type: {traveler_type}
Interests: {interests}
Budget: {budget}
Language: {language}

Knowledge findings:
{knowledge_output}

Rules:
- Do not invent facts presented as verified information.
- Prefer places and activities supported by the knowledge findings.
- If knowledge is unavailable, clearly label suggestions as general
  suggestions rather than verified facts.
- Keep the itinerary concise.
- Avoid unnecessary explanations.

For each day include:
- Main places or activities
- Approximate sequence
- Meal suggestion
- Transport/practical note when useful

Create a realistic itinerary that fits the stated duration.
""",
        expected_output="""
A concise day-by-day itinerary with activities, places, meal suggestions,
and practical travel notes.
""",
        agent=agents["planner"],
        context=[knowledge_task],
    )

    # ---------------------------------------------------------
    # 3. BUDGET TASK
    # ---------------------------------------------------------
    budget_task = Task(
        description="""
Create a simple trip-budget estimate based on the user's budget,
the itinerary, and available knowledge.

Trip:
Destination: {destination}
Duration: {duration}
Budget: {budget}

Knowledge findings:
{knowledge_output}

Itinerary:
{planner_output}

Rules:
- Never claim an exact current price unless it appears in the evidence.
- Clearly distinguish known amounts from estimates.
- If prices are unavailable, say so.
- Do not create fake prices.
- Keep the calculation simple and concise.

Cover:
- Accommodation
- Transport
- Food
- Activities
- Miscellaneous
- Estimated total
""",
        expected_output="""
A concise and transparent budget breakdown with assumptions and an
estimated total where possible.
""",
        agent=agents["budget"],
        context=[knowledge_task, planner_task],
    )

    # ---------------------------------------------------------
    # 4. SAFETY TASK
    # ---------------------------------------------------------
    safety_task = Task(
        description="""
Review the proposed trip for practical safety considerations.

Trip:
Destination: {destination}
Duration: {duration}
Traveler type: {traveler_type}

Knowledge findings:
{knowledge_output}

Itinerary:
{planner_output}

Rules:
- Do not invent incidents, warnings, emergency numbers, road conditions,
  weather conditions, or government advisories.
- Location-specific safety information must be supported by the evidence.
- General precautions must be clearly presented as general precautions.
- Keep this section short and practical.

Return only the most useful safety recommendations.
""",
        expected_output="""
A concise safety section containing relevant precautions and clearly
labelled general travel advice.
""",
        agent=agents["safety"],
        context=[knowledge_task, planner_task],
    )

    # ---------------------------------------------------------
    # 5. FINAL SUMMARIZER TASK
    # ---------------------------------------------------------
    summary_task = Task(
        description="""
Create the final TrekTales travel plan.

Trip:
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

Create a useful, concise final answer.

Use this structure:

1. Trip Overview
2. Day-by-Day Itinerary
3. Budget
4. Safety Tips
5. Sources / Limitations

Rules:
- Do not invent verified facts.
- Do not present estimated prices as exact prices.
- Mention source filenames when available.
- If the knowledge base returned no useful information, clearly state
  that some recommendations are general suggestions.
- Respect the requested language.
- Do not repeat the same information.
- Avoid lengthy explanations.
- Keep the final answer practical.
""",
        expected_output="""
A concise polished travel plan containing:
- Trip overview
- Day-by-day itinerary
- Budget
- Safety tips
- Sources or limitations
""",
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
```

This version returns **exactly 5 travel tasks**, so your `crew.py` should receive a non-empty task list and won't produce the previous `No task outputs available` error.

One important point: your `agents.py` must contain these five keys:

```python
agents["knowledge"]
agents["planner"]
agents["budget"]
agents["safety"]
agents["summarizer"]
```

If your current `agents.py` uses different names or still requires `master_orchestrator`, `payment`, or `vision`, it needs to be made consistent with this `tasks.py`.
