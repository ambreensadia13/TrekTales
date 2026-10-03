from crewai import Task


def create_tasks(agents):
    """
    Create all TrekTales tasks.

    Args:
        agents: Dictionary returned by create_agents().

    Returns:
        List of CrewAI Task objects.
    """

    # ========================================================
    # TASK 1 — MASTER ORCHESTRATION
    # ========================================================

    master_task = Task(
        description=(
            "Coordinate the complete TrekTales travel-planning "
            "workflow for the following request:\n\n"
            "Destination: {destination}\n"
            "Starting location: {starting_location}\n"
            "Duration: {duration} days\n"
            "Travelers: {travelers}\n"
            "Budget: {budget}\n"
            "Travel style: {travel_style}\n"
            "Interests: {interests}\n"
            "Language: {language}\n\n"
            "Retrieved tourism evidence:\n"
            "{evidence}\n\n"
            "Ensure the final travel plan is practical, coherent, "
            "and based on the supplied evidence where possible."
        ),
        expected_output=(
            "A coordinated travel-planning result containing "
            "destination information, itinerary planning, "
            "budget considerations, safety information and "
            "a final summary."
        ),
        agent=agents["master_orchestrator"],
    )

    # ========================================================
    # TASK 2 — KNOWLEDGE
    # ========================================================

    knowledge_task = Task(
        description=(
            "Analyze the supplied tourism knowledge for the "
            "requested trip.\n\n"
            "Destination: {destination}\n"
            "Starting location: {starting_location}\n"
            "Interests: {interests}\n\n"
            "Use the retrieved evidence below:\n"
            "{evidence}\n\n"
            "Identify useful destination information, places, "
            "activities, food, transport and other relevant "
            "tourism information. Do not invent unsupported "
            "facts."
        ),
        expected_output=(
            "A concise set of evidence-grounded tourism findings "
            "relevant to the requested trip."
        ),
        agent=agents["knowledge"],
    )

    # ========================================================
    # TASK 3 — PLANNER
    # ========================================================

    planner_task = Task(
        description=(
            "Create a practical day-by-day itinerary.\n\n"
            "Destination: {destination}\n"
            "Starting location: {starting_location}\n"
            "Duration: {duration} days\n"
            "Travelers: {travelers}\n"
            "Travel style: {travel_style}\n"
            "Interests: {interests}\n"
            "Language: {language}\n\n"
            "Use the tourism information and previous agent "
            "findings available in the task context."
        ),
        expected_output=(
            "A structured day-by-day itinerary with activities, "
            "logical sequencing and practical travel suggestions."
        ),
        agent=agents["planner"],
        context=[
            knowledge_task,
        ],
    )

    # ========================================================
    # TASK 4 — BUDGET
    # ========================================================

    budget_task = Task(
        description=(
            "Prepare a practical budget estimate for the trip.\n\n"
            "Destination: {destination}\n"
            "Duration: {duration} days\n"
            "Travelers: {travelers}\n"
            "Budget level: {budget}\n"
            "Starting location: {starting_location}\n\n"
            "Consider likely categories such as transport, "
            "accommodation, food and activities. Clearly label "
            "estimates as estimates rather than guaranteed prices."
        ),
        expected_output=(
            "A categorized travel budget with estimated costs "
            "and a reasonable total range."
        ),
        agent=agents["budget"],
        context=[
            knowledge_task,
            planner_task,
        ],
    )

    # ========================================================
    # TASK 5 — SAFETY
    # ========================================================

    safety_task = Task(
        description=(
            "Prepare practical safety guidance for the trip.\n\n"
            "Destination: {destination}\n"
            "Duration: {duration} days\n"
            "Travelers: {travelers}\n"
            "Travel style: {travel_style}\n\n"
            "Focus on practical considerations such as weather, "
            "transport, local conditions, emergency preparation "
            "and responsible travel."
        ),
        expected_output=(
            "A concise list of relevant travel safety "
            "considerations and precautions."
        ),
        agent=agents["safety"],
        context=[
            knowledge_task,
            planner_task,
        ],
    )

    # ========================================================
    # TASK 6 — SUMMARY
    # ========================================================

    summary_task = Task(
        description=(
            "Create the final TrekTales travel plan.\n\n"
            "Destination: {destination}\n"
            "Starting location: {starting_location}\n"
            "Duration: {duration} days\n"
            "Travelers: {travelers}\n"
            "Budget: {budget}\n"
            "Travel style: {travel_style}\n"
            "Interests: {interests}\n"
            "Language: {language}\n\n"
            "Combine the available findings from the knowledge, "
            "planning, budget and safety agents.\n\n"
            "Write the final response in the requested language. "
            "Keep it structured and easy to follow."
        ),
        expected_output=(
            "A complete personalized TrekTales travel plan "
            "including itinerary, budget guidance, safety "
            "information and useful travel notes."
        ),
        agent=agents["summarizer"],
        context=[
            knowledge_task,
            planner_task,
            budget_task,
            safety_task,
        ],
    )

    # ========================================================
    # TASK 7 — PAYMENT
    # ========================================================

    payment_task = Task(
        description=(
            "Explain the TrekTales demo payment workflow when "
            "payment information is provided. Do not claim that "
            "an AI screenshot analysis is proof of a real "
            "financial transaction."
        ),
        expected_output=(
            "A clear explanation of the demo payment verification "
            "result."
        ),
        agent=agents["payment"],
    )

    # ========================================================
    # TASK 8 — VISION
    # ========================================================

    vision_task = Task(
        description=(
            "Support payment screenshot analysis by identifying "
            "visible payment information such as recipient, "
            "amount and transaction status when such information "
            "is supplied."
        ),
        expected_output=(
            "Structured payment screenshot observations."
        ),
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
