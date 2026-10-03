from crewai import Task


def create_tasks(agents):
    """
    Create the 8 TrekTales CrewAI tasks.

    Expected agent keys:
        master_orchestrator
        knowledge
        planner
        budget
        safety
        summarizer
        payment
        vision
    """

    master_task = Task(
        description="""
You are the Master Orchestrator for TrekTales.

Coordinate the travel-planning workflow using the provided user request
and the outputs of the specialist agents.

User request:
{request}

Create a clear travel-planning objective for the specialist agents.

Do not invent places, prices, timings, policies, or safety information.
Use the retrieved knowledge supplied to the workflow whenever possible.
""",
        expected_output="""
A concise travel-planning objective containing:
- destination
- duration
- traveler type
- interests
- budget
- language
- important constraints
""",
        agent=agents["master_orchestrator"],
    )

    knowledge_task = Task(
        description="""
You are the Knowledge Agent.

Use the supplied tourism knowledge-base evidence to identify information
relevant to the user's trip.

User request:
{request}

Retrieved evidence:
{evidence}

Return only information supported by the retrieved evidence.

Clearly distinguish between:
- information found in the knowledge base
- information that is not available

Never invent facts, prices, opening hours, addresses, transport schedules,
or safety information.
""",
        expected_output="""
A structured evidence summary containing relevant:
- places
- hotels/accommodation information
- transport information
- food information
- activities
- safety information
- source filenames
""",
        agent=agents["knowledge"],
    )

    planner_task = Task(
        description="""
You are the Planner Agent.

Create a practical day-by-day itinerary using the user's request and the
Knowledge Agent's findings.

User request:
{request}

Knowledge findings:
{knowledge_output}

Do not invent unsupported facts.

For every recommended location, prefer information supported by the
knowledge-base evidence.

Create a realistic itinerary with:
- Day number
- approximate schedule
- places to visit
- activities
- meal suggestions
- transport suggestions
- practical notes
""",
        expected_output="""
A day-by-day travel itinerary with realistic sequencing and practical notes.
""",
        agent=agents["planner"],
        context=[knowledge_task],
    )

    budget_task = Task(
        description="""
You are the Budget Agent.

Estimate the trip budget from the available knowledge and the user's
specified budget.

User request:
{request}

Knowledge findings:
{knowledge_output}

Planned itinerary:
{planner_output}

Do not pretend that an exact current price is known unless it is explicitly
present in the provided evidence.

Separate:
- known amounts
- estimated amounts
- unavailable amounts

Provide a simple budget breakdown.
""",
        expected_output="""
A transparent budget breakdown covering:
- accommodation
- transport
- food
- activities
- miscellaneous expenses
- estimated total
- important assumptions
""",
        agent=agents["budget"],
        context=[knowledge_task, planner_task],
    )

    safety_task = Task(
        description="""
You are the Safety Agent.

Review the proposed itinerary for practical travel-safety considerations.

User request:
{request}

Knowledge findings:
{knowledge_output}

Planned itinerary:
{planner_output}

Only make safety claims supported by the available evidence or clearly label
general precautions as general precautions.

Do not invent incidents, warnings, emergency numbers, road conditions,
weather conditions, or government advisories.
""",
        expected_output="""
A concise safety section containing:
- relevant precautions
- transport considerations
- location-specific considerations when supported
- general travel precautions
""",
        agent=agents["safety"],
        context=[knowledge_task, planner_task],
    )

    summary_task = Task(
        description="""
You are the Summarizer Agent.

Create the final TrekTales travel response using the specialist outputs.

User request:
{request}

Knowledge:
{knowledge_output}

Itinerary:
{planner_output}

Budget:
{budget_output}

Safety:
{safety_output}

Produce a clean, useful travel plan.

Requirements:
- Do not invent facts.
- Do not claim unsupported prices are exact.
- Keep the itinerary easy to follow.
- Include budget information.
- Include safety information.
- Mention source filenames when available.
- Respect the requested language.
""",
        expected_output="""
A polished final travel plan containing:
1. Trip overview
2. Day-by-day itinerary
3. Budget
4. Safety tips
5. Sources
6. Important assumptions or limitations
""",
        agent=agents["summarizer"],
        context=[
            knowledge_task,
            planner_task,
            budget_task,
            safety_task,
        ],
    )

    payment_task = Task(
        description="""
You are the Payment Agent for TrekTales.

This is a DEMONSTRATION payment workflow.

Expected unlock price:
Rs. 199

Expected recipient:
ambreen sadia

Do not claim that a real payment has been verified.

If payment information is supplied, summarize it for the application.
Actual payment verification must be performed by deterministic Python
validation outside the language model.
""",
        expected_output="""
A concise payment-demo assessment without claiming real payment verification.
""",
        agent=agents["payment"],
    )

    vision_task = Task(
        description="""
You are the Vision Agent for TrekTales.

This agent is intended for analysis of an uploaded JazzCash payment
screenshot.

Extract only information that is visibly present in the supplied image.

Potential fields:
- recipient
- amount
- payment status
- transaction/reference information
- confidence

Never claim that a screenshot proves a real payment independently.
The application performs deterministic validation after extraction.
""",
        expected_output="""
Structured screenshot information containing recipient, amount, status,
and confidence when visible.
""",
        agent=agents["vision"],
    )

    return [
        master_task,
        knowledge_task,
        planner_task,
        budget_task,
        safety_task,
        summary_task,
        payment_task,
        vision_task,
    ]
