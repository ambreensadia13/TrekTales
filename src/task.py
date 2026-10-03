from crewai import Task


def create_tasks(
    knowledge_agent,
    planner_agent,
    budget_agent,
    safety_agent,
    summarizer_agent,
    user_query: str,
    evidence_text: str,
    trip_days: int,
) -> list[Task]:

    grounding = """
IMPORTANT:

Use ONLY the evidence supplied in this task.

If information is missing:
"Information not found in the tourism knowledge base."

Never invent facts, prices, names, addresses, schedules,
transport fares, safety statistics or contact information.
"""

    knowledge_task = Task(
        description=f"""
User request:
{user_query}

Tourism knowledge-base evidence:
{evidence_text}

Identify the factual tourism information directly relevant
to the user's request.

{grounding}

Return:
- relevant facts
- source
- page
- department
""",
        expected_output=(
            "A grounded evidence summary with source and page references."
        ),
        agent=knowledge_agent,
    )

    planner_task = Task(
        description=f"""
Create a {trip_days}-day travel itinerary for:

{user_query}

Use only the supplied tourism evidence.

{evidence_text}

{grounding}

The itinerary must clearly distinguish:
- confirmed evidence-based items
- user-provided preferences
- unavailable information

Do not invent missing attractions or schedules.
""",
        expected_output=(
            "A practical day-by-day itinerary grounded in the evidence."
        ),
        agent=planner_agent,
    )

    budget_task = Task(
        description=f"""
Prepare the travel budget for:

{user_query}

Use the supplied evidence:

{evidence_text}

{grounding}

If a price is not available in the evidence,
write "Price not available in knowledge base."

Do not create current market prices.
Do not guess hotel rates.
Do not guess transport fares.
""",
        expected_output=(
            "A transparent budget breakdown with unavailable prices explicitly marked."
        ),
        agent=budget_agent,
    )

    safety_task = Task(
        description=f"""
Prepare safety guidance for:

{user_query}

Use only this evidence:

{evidence_text}

{grounding}

Do not invent emergency numbers,
crime statistics, road conditions,
or safety policies.
""",
        expected_output=(
            "Evidence-grounded travel safety guidance with citations."
        ),
        agent=safety_agent,
    )

    summarizer_task = Task(
        description=f"""
Create the final TrekTales answer for:

{user_query}

Trip length:
{trip_days} days

The final answer must combine:
1. knowledge findings
2. itinerary
3. budget
4. safety

Rules:
- Never invent missing facts.
- Preserve source names and page numbers.
- Mention unavailable information honestly.
- Use clear headings.
- Keep the response practical.
- Do not claim real-time verification.
- Do not claim payment verification.
""",
        expected_output=(
            "A polished grounded tourism answer with itinerary, budget, "
            "safety notes and source citations."
        ),
        agent=summarizer_agent,
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
        summarizer_task,
    ]
