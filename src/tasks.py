from crewai import Task


def create_tasks(agents):
    """Create the TrekTales travel-planning tasks."""

    knowledge_task = Task(
        description="""
Use the tourism knowledge-base evidence to find information relevant
to the user's trip.

Destination: {destination}
Duration: {duration}
Traveler type: {traveler_type}
Interests: {interests}
Budget: {budget}

Knowledge-base evidence:
{evidence}

Rules:
- Use only information contained in the evidence.
- Do not invent facts.
- Do not invent prices, opening hours, addresses, schedules, or warnings.
- If evidence is empty, say that relevant knowledge is unavailable.
- Keep the response concise.
- Include source filenames when available.
""",
        expected_output="""
A concise evidence summary containing relevant places, activities,
accommodation, transport, food, safety information, and source filenames.
""",
        agent=agents["knowledge"],
    )

    planner_task = Task(
        description="""
Create a practical itinerary using the trip information and
the Knowledge Agent's findings.

Destination: {destination}
Duration: {duration}
Traveler type: {traveler_type}
Interests: {interests}
Budget: {budget}
Language: {language}

Knowledge findings:
{knowledge_output}

Rules:
- Do not invent verified facts.
- Prefer information supported by the knowledge findings.
- If knowledge is unavailable, clearly label suggestions as general.
- Keep the itinerary concise.
- Avoid unnecessary explanations.

For each day include:
- Main activities
- Places to visit
- Meal suggestion
- Transport or practical note when useful
""",
        expected_output="""
A concise day-by-day travel itinerary with activities,
places, meal suggestions, and practical notes.
""",
        agent=agents["planner"],
        context=[knowledge_task],
    )

    budget_task = Task(
        description="""
Create a simple trip-budget estimate.

Destination: {destination}
Duration: {duration}
Budget: {budget}

Knowledge findings:
{knowledge_output}

Itinerary:
{planner_output}

Rules:
- Do not claim exact current prices unless they are in the evidence.
- Clearly label estimates.
- Never create fake prices.
- If prices are unavailable, say so.
- Keep the budget concise.

Cover:
- Accommodation
- Transport
- Food
- Activities
- Miscellaneous
- Estimated total
""",
        expected_output="""
A concise and transparent budget breakdown with assumptions.
""",
        agent=agents["budget"],
        context=[knowledge_task, planner_task],
    )

    safety_task = Task(
        description="""
Review the proposed trip for practical safety considerations.

Destination: {destination}
Duration: {duration}
Traveler type: {traveler_type}

Knowledge findings:
{knowledge_output}

Itinerary:
{planner_output}

Rules:
- Do not invent incidents or warnings.
- Do not invent emergency numbers.
- Do not invent weather or road conditions.
- Location-specific claims must be supported by the evidence.
- General precautions must be labelled as general precautions.
- Keep this section short.
""",
        expected_output="""
A concise safety section containing relevant precautions and
clearly labelled general travel advice.
""",
        agent=agents["safety"],
        context=[knowledge_task, planner_task],
    )

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

Create a concise final travel plan with these sections:

1. Trip Overview
2. Day-by-Day Itinerary
3. Budget
4. Safety Tips
5. Sources and Limitations

Rules:
- Do not invent verified facts.
- Do not present estimated prices as exact.
- Mention source filenames when available.
- If the knowledge base has no useful information, clearly say that
  some recommendations are general suggestions.
- Respect the requested language.
- Do not repeat information.
- Keep the response practical and concise.
""",
        expected_output="""
A polished concise travel plan containing the trip overview,
day-by-day itinerary, budget, safety tips, and sources or limitations.
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
