import json
import re

from openai import OpenAI

from src.agents import get_agent_descriptions
from src.config import (
    GROQ_API_KEY,
    GROQ_BASE_URL,
    GROQ_MODEL,
)
from src.rag import (
    build_context,
    has_grounded_evidence,
)
from src.tasks import build_planning_instructions


class TrekTalesCrew:
    """
    TrekTales multi-agent orchestration layer.

    The project exposes an eight-agent architecture, while
    Groq performs the actual language reasoning.

    This deliberately avoids CrewAI/LiteLLM configuration so
    the application remains stable on Streamlit Cloud.
    """

    def __init__(self):

        if not GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is missing. "
                "Add it to Streamlit Secrets."
            )

        self.client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url=GROQ_BASE_URL,
        )


    # ========================================================
    # GROQ CALL
    # ========================================================

    def _call_groq(
        self,
        system_prompt,
        user_prompt,
    ):

        response = (
            self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                temperature=0.1,
                max_tokens=3000,
            )
        )

        if not response.choices:
            raise RuntimeError(
                "Groq returned no choices."
            )

        content = (
            response.choices[0]
            .message
            .content
        )

        if not content:
            raise RuntimeError(
                "Groq returned an empty response."
            )

        return str(content).strip()


    # ========================================================
    # CLEAN RESPONSE
    # ========================================================

    @staticmethod
    def _clean_response(text):

        if not text:
            return ""

        text = re.sub(
            r"^```(?:markdown|md|text)?\s*",
            "",
            text.strip(),
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\s*```$",
            "",
            text,
        )

        return text.strip()


    # ========================================================
    # RUN
    # ========================================================

    def run(
        self,
        destination,
        starting_location,
        days,
        budget,
        travelers,
        travel_style,
        language,
        interests,
        evidence,
    ):

        # ----------------------------------------------------
        # HARD SAFETY CHECK
        # ----------------------------------------------------

        if not has_grounded_evidence(
            evidence
        ):

            return {
                "answer": (
                    "I could not find enough information in "
                    "the TrekTales knowledge base to create "
                    "a grounded itinerary."
                ),
                "days": days,
                "sources": [],
            }


        # ----------------------------------------------------
        # CONTEXT
        # ----------------------------------------------------

        context = build_context(
            evidence,
            max_items=8,
        )


        # ----------------------------------------------------
        # AGENT DESCRIPTION
        # ----------------------------------------------------

        agent_descriptions = (
            get_agent_descriptions()
        )


        # ----------------------------------------------------
        # TASK INSTRUCTIONS
        # ----------------------------------------------------

        trip_instructions = (
            build_planning_instructions(
                destination=destination,
                starting_location=starting_location,
                days=days,
                budget=budget,
                travelers=travelers,
                travel_style=travel_style,
                language=language,
                interests=interests,
            )
        )


        # ----------------------------------------------------
        # SYSTEM PROMPT
        # ----------------------------------------------------

        system_prompt = f"""
You are the TrekTales Master Orchestrator.

TrekTales uses these structured agents:

{agent_descriptions}


GROUNDING POLICY

You must use ONLY the supplied tourism knowledge
records.

The knowledge records are the source of truth.

Do NOT use your own outside tourism knowledge.

Do NOT invent missing information.

Do NOT silently replace missing information with
plausible information.

Do NOT invent prices.

Do NOT invent opening hours.

Do NOT invent hotels.

Do NOT invent restaurants.

Do NOT invent attractions.

Do NOT invent transport schedules.

Do NOT invent safety claims.

Do NOT claim live availability.

Do NOT claim a booking was made.

If the knowledge base does not contain something,
state that it is not available in the supplied
knowledge base.


DAY COUNT POLICY

The requested number of days is a hard application
constraint.

Generate exactly the requested number of days.

Never generate an additional day.


SOURCE POLICY

Each itinerary recommendation must be traceable to
the supplied knowledge records.

Do not fabricate source names.


DEMO DATA POLICY

The TrekTales knowledge base may contain fictional
demonstration tourism data.

Do not present demo records as verified real-world
facts.


OUTPUT POLICY

Create a practical itinerary.

Use clear headings.

Use:

Day 1
Day 2
Day 3

only when those days are requested.

Include useful details only when supported by the
knowledge base.

Keep the answer readable for a normal traveler.

Do not output JSON.

Do not output HTML.
"""


        # ----------------------------------------------------
        # USER PROMPT
        # ----------------------------------------------------

        user_prompt = f"""
{trip_instructions}


SUPPLIED TOURISM KNOWLEDGE
==========================

{context}


FINAL TASK
==========

Create the TrekTales itinerary now.

Remember:

EXACTLY {days} DAY(S).

Do not create Day {days + 1}.
"""


        # ----------------------------------------------------
        # GROQ
        # ----------------------------------------------------

        answer = self._call_groq(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )


        answer = self._clean_response(
            answer
        )


        # ----------------------------------------------------
        # FINAL DAY VALIDATION
        # ----------------------------------------------------

        day_numbers = []

        matches = re.findall(
            r"(?im)^\s*(?:#+\s*)?Day\s+(\d+)\b",
            answer,
        )

        for value in matches:

            try:
                number = int(value)

                if number not in day_numbers:
                    day_numbers.append(number)

            except ValueError:
                continue


        invalid_days = [
            number
            for number in day_numbers
            if number > days
        ]


        if invalid_days:

            # Ask Groq once to correct the day count.
            correction_prompt = f"""
Rewrite the following itinerary.

The ONLY allowed day headings are:

Day 1 through Day {days}.

Remove every later day.

Do not add any new tourism information.

Preserve the existing grounded information.

Return only the corrected itinerary.

CURRENT ITINERARY:

{answer}
"""

            answer = self._call_groq(
                system_prompt=(
                    "You are a strict itinerary formatter. "
                    "Do not invent information."
                ),
                user_prompt=correction_prompt,
            )

            answer = self._clean_response(
                answer
            )


        # ----------------------------------------------------
        # SOURCES
        # ----------------------------------------------------

        sources = []

        for item in evidence:

            if not isinstance(item, dict):
                continue

            source = (
                item.get("source")
                or item.get(
                    "metadata",
                    {},
                ).get(
                    "source",
                    "Unknown source",
                )
            )

            page = (
                item.get("page")
                or item.get(
                    "metadata",
                    {},
                ).get(
                    "page",
                    "N/A",
                )
            )

            record_id = (
                item.get("record_id")
                or item.get(
                    "metadata",
                    {},
                ).get(
                    "record_id",
                    "",
                )
            )

            source_record = {
                "source": str(source),
                "page": str(page),
                "record_id": str(record_id),
            }

            if source_record not in sources:
                sources.append(
                    source_record
                )


        return {
            "answer": answer,
            "days": days,
            "sources": sources,
        }
