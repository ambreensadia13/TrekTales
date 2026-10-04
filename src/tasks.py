from __future__ import annotations

from crewai import Task


def create_tasks(agents):
    """Create a sequential RAG-grounded travel workflow.

    Downstream tasks receive upstream outputs through CrewAI's `context`.
    They do not depend on manually fabricated `{knowledge_output}` placeholders.
    """

    knowledge_task = Task(
        description="""
Analyze the supplied TrekTales RAG evidence for this request.

Destination: {destination}
Starting location: {starting_location}
Requested trip days: {requested_days}
Accessible days right now: {accessible_days}
Travelers: {travelers}
Travel style: {travel_style}
Interests: {interests}
Budget level: {budget}
Language: {language}

Retrieved evidence:
{evidence}

Source manifest:
{source_manifest}

Strict rules:
- Treat the retrieved evidence as the only verified tourism knowledge.
- The metadata fields SOURCE, PAGE, DEPARTMENT and RECORD ID are authoritative.
- Never invent a source, price, address, opening time, route, warning or policy.
- The supplied dataset is demo/fictional tourism data; do not describe it as live data.
- If the requested destination is not supported by the evidence, say so clearly.
- Keep the evidence summary concise.
""",
        expected_output=(
            "A concise evidence summary that preserves source filenames, pages, "
            "departments and supported facts, with unsupported destination facts excluded."
        ),
        agent=agents["knowledge"],
    )

    planner_task = Task(
        description="""
Create the itinerary using the Knowledge Agent's context.

Destination: {destination}
Starting location: {starting_location}
Requested trip days: {requested_days}
Accessible days right now: {accessible_days}
Travelers: {travelers}
Travel style: {travel_style}
Interests: {interests}
Budget level: {budget}
Language: {language}

The previous task's output is the authoritative knowledge context.

Strict day-access rule:
- Generate itinerary content for ONLY the accessible days.
- If accessible_days is 1, output Day 1 only. Do NOT output Day 2 or Day 3 content.
- If accessible_days is 2, output Day 1 and Day 2 only.
- If accessible_days is 3, output Day 1, Day 2 and Day 3.
- If requested_days is greater than accessible_days, add one short line stating that the remaining days are locked.

Other rules:
- Use supported places and activities from the knowledge context.
- Do not invent exact prices or schedules.
- Clearly mark general suggestions when evidence does not support a destination-specific fact.
- Keep each day practical rather than filling it with excessive activities.
""",
        expected_output="A concise itinerary containing only the permitted days.",
        agent=agents["planner"],
        context=[knowledge_task],
    )

    budget_task = Task(
        description="""
Prepare the budget section using the previous Knowledge and Planner outputs.

Requested days: {requested_days}
Accessible days: {accessible_days}
Travelers: {travelers}
Budget level: {budget}

Rules:
- Use exact demo prices only when they appear in the supplied evidence.
- Do not invent hotel, food, transport or activity prices.
- If a total is calculated, show it as a demo/estimated total and state the assumptions.
- Do not calculate costs for locked days.
- Keep the budget concise.
""",
        expected_output="A transparent budget with supported demo prices and clearly labelled estimates.",
        agent=agents["budget"],
        context=[knowledge_task, planner_task],
    )

    safety_task = Task(
        description="""
Prepare safety guidance using the previous Knowledge and Planner outputs.

Destination: {destination}
Accessible days: {accessible_days}
Travelers: {travelers}
Travel style: {travel_style}

Rules:
- Use location-specific safety claims only when supported by the evidence.
- General precautions must be labelled as general precautions.
- Never invent emergency numbers, weather, incidents, road conditions or official advisories.
- Keep this section practical and short.
""",
        expected_output="A concise safety section grounded in the available evidence.",
        agent=agents["safety"],
        context=[knowledge_task, planner_task],
    )

    summary_task = Task(
        description="""
Create the final TrekTales answer from the previous specialist outputs.

Destination: {destination}
Starting location: {starting_location}
Requested days: {requested_days}
Accessible days: {accessible_days}
Travelers: {travelers}
Travel style: {travel_style}
Interests: {interests}
Budget: {budget}
Language: {language}

Authoritative source manifest:
{source_manifest}

Required structure:
1. Trip Overview
2. Day-by-Day Itinerary
3. Budget
4. Safety Tips
5. Sources and Limitations

Strict rules:
- Include ONLY the accessible itinerary days.
- Never generate locked Day 2/Day 3 content when those days are not accessible.
- Do not invent facts, prices, schedules or sources.
- The source manifest is authoritative for source names. Do not create new filenames.
- State that the knowledge base contains fictional/demo data when relevant.
- If the destination is unsupported by the knowledge base, say that destination-specific facts could not be verified.
- Respect the requested language.
- Keep the final response practical and concise.
""",
        expected_output="A polished final travel plan with only permitted days and a sources/limitations section.",
        agent=agents["summarizer"],
        context=[knowledge_task, planner_task, budget_task, safety_task],
    )

    return [knowledge_task, planner_task, budget_task, safety_task, summary_task]
