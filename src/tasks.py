def build_planning_instructions(
    destination,
    starting_location,
    days,
    budget,
    travelers,
    travel_style,
    language,
    interests,
):
    """
    Build deterministic planning constraints.

    The exact day count is intentionally generated in Python
    and passed to Groq explicitly.
    """

    interest_text = (
        ", ".join(interests)
        if interests
        else "general tourism"
    )

    return f"""
TRIP REQUIREMENTS

Destination:
{destination}

Starting location:
{starting_location}

EXACT NUMBER OF DAYS:
{days}

Number of travelers:
{travelers}

Budget:
Rs. {budget}

Travel style:
{travel_style}

Interests:
{interest_text}

Response language:
{language}


STRICT REQUIREMENTS

1. Generate exactly {days} day(s).

2. Do not create Day {days + 1}.

3. Every day must be explicitly labelled:
   Day 1, Day 2, etc.

4. Use ONLY the supplied tourism knowledge records.

5. Never invent a hotel, restaurant, attraction,
   transport option, opening hour, price, safety fact,
   address or activity.

6. If a requested detail is unavailable in the knowledge
   base, say that it is unavailable.

7. Do not transform demo data into real-world claims.

8. Keep the plan consistent with the supplied budget
   as much as the knowledge base allows.

9. Do not claim live availability.

10. Do not claim that a booking was made.

11. Keep source information traceable.

12. Use the requested response language.
"""
