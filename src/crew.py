import re
import time

from openai import OpenAI, RateLimitError

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
    TrekTales AI orchestration layer.

    The application uses a structured six-agent architecture.
    Groq performs the final language reasoning.

    Important rules:

    1. Rawalpindi is the supported destination.
    2. Tourism facts must come from the supplied RAG evidence.
    3. Missing information must never be invented.
    4. The requested number of days is enforced.
    5. Sources are preserved.
    6. Groq requests are kept reasonably small.
    7. Groq 429 errors are retried automatically.
    8. The AI does not generate duplicate UI headings.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

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
    # GROQ RETRY DELAY
    # ========================================================

    @staticmethod
    def _get_retry_delay(
        error,
        default_delay=8,
    ):
        """
        Determine how long to wait after a Groq 429 error.
        """

        # ----------------------------------------------------
        # Try Retry-After response header
        # ----------------------------------------------------

        try:

            response = getattr(
                error,
                "response",
                None,
            )

            if response is not None:

                headers = getattr(
                    response,
                    "headers",
                    {},
                )

                retry_after = (
                    headers.get("retry-after")
                    or headers.get("Retry-After")
                )

                if retry_after:

                    try:

                        value = float(
                            str(
                                retry_after
                            ).strip()
                        )

                        if value > 0:
                            return min(
                                max(value, 1),
                                30,
                            )

                    except (
                        ValueError,
                        TypeError,
                    ):
                        pass

        except Exception:
            pass

        # ----------------------------------------------------
        # Parse Groq error message
        # ----------------------------------------------------

        message = str(error)

        patterns = [
            r"try again in\s+([0-9]+(?:\.[0-9]+)?)s",
            r"retry[- ]after[:\s]+([0-9]+(?:\.[0-9]+)?)",
            r"reset[^0-9]*([0-9]+(?:\.[0-9]+)?)s",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                message,
                flags=re.IGNORECASE,
            )

            if match:

                try:

                    value = float(
                        match.group(1)
                    )

                    if value > 0:
                        return min(
                            max(value, 1),
                            30,
                        )

                except (
                    ValueError,
                    TypeError,
                ):
                    pass

        return default_delay

    # ========================================================
    # GROQ CALL
    # ========================================================

    def _call_groq(
        self,
        system_prompt,
        user_prompt,
        max_tokens=1600,
    ):
        """
        Controlled Groq request.

        The request is intentionally limited to reduce
        token-per-minute pressure.

        Temporary 429 errors are retried automatically.
        """

        try:

            max_tokens = int(
                max_tokens
            )

        except (
            TypeError,
            ValueError,
        ):

            max_tokens = 1600

        max_tokens = max(
            700,
            min(
                max_tokens,
                2200,
            ),
        )

        last_error = None

        # ----------------------------------------------------
        # Retry up to three times
        # ----------------------------------------------------

        for attempt in range(3):

            try:

                response = (
                    self.client
                    .chat
                    .completions
                    .create(
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
                        max_tokens=max_tokens,
                    )
                )

                if not response.choices:

                    raise RuntimeError(
                        "Groq returned no choices."
                    )

                content = (
                    response
                    .choices[0]
                    .message
                    .content
                )

                if not content:

                    raise RuntimeError(
                        "Groq returned an empty response."
                    )

                return str(
                    content
                ).strip()

            except RateLimitError as error:

                last_error = error

                # ------------------------------------------------
                # Final attempt failed
                # ------------------------------------------------

                if attempt >= 2:

                    raise RuntimeError(
                        "Groq rate limit is still active. "
                        "Please wait a few seconds and try "
                        "generating the trip again."
                    ) from error

                delay = self._get_retry_delay(
                    error,
                    default_delay=8,
                )

                # Add a small safety margin.
                delay = min(
                    max(
                        delay + 1,
                        3,
                    ),
                    20,
                )

                time.sleep(delay)

            except Exception:
                raise

        if last_error is not None:

            raise RuntimeError(
                "Groq request could not be completed."
            ) from last_error

        raise RuntimeError(
            "Groq request could not be completed."
        )

    # ========================================================
    # CLEAN RESPONSE
    # ========================================================

    @staticmethod
    def _clean_response(text):

        if not text:
            return ""

        text = str(
            text
        ).strip()

        # ----------------------------------------------------
        # Remove Markdown code fences
        # ----------------------------------------------------

        text = re.sub(
            r"^```(?:markdown|md|text)?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\s*```$",
            "",
            text,
        )

        # ----------------------------------------------------
        # Remove HTML tags
        # ----------------------------------------------------

        text = re.sub(
            r"<[^>]+>",
            "",
            text,
        )

        # ----------------------------------------------------
        # Remove duplicate top-level itinerary headings
        # ----------------------------------------------------

        text = re.sub(
            r"(?im)"
            r"^\s*"
            r"(?:#+\s*)?"
            r"🌿\s*RAWALPINDI\s+ITINERARY\s*$",
            "",
            text,
        )

        text = re.sub(
            r"(?im)"
            r"^\s*"
            r"(?:#+\s*)?"
            r"PERSONALIZED\s+ITINERARY\s*$",
            "",
            text,
        )

        # ----------------------------------------------------
        # Remove accidental generic title
        # ----------------------------------------------------

        text = re.sub(
            r"(?im)"
            r"^\s*"
            r"(?:#+\s*)?"
            r"YOUR\s+RAWALPINDI\s+ITINERARY\s*$",
            "",
            text,
        )

        # ----------------------------------------------------
        # Remove excessive blank lines
        # ----------------------------------------------------

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        return text.strip()

    # ========================================================
    # COMPACT CONTEXT
    # ========================================================

    @staticmethod
    def _compact_context(
        context,
        max_chars=14000,
    ):
        """
        Keep the retrieved RAG context reasonably small.
        """

        if not context:
            return ""

        context = str(
            context
        ).strip()

        if len(context) <= max_chars:
            return context

        return (
            context[:max_chars]
            + "\n\n"
            "[Additional retrieved content omitted to "
            "control prompt size.]"
        )

    # ========================================================
    # COMPACT AGENT DESCRIPTIONS
    # ========================================================

    @staticmethod
    def _compact_agent_descriptions(
        descriptions,
        max_chars=5000,
    ):
        """
        Keep the six-agent architecture visible without
        wasting unnecessary prompt tokens.
        """

        if descriptions is None:
            return ""

        try:

            text = str(
                descriptions
            ).strip()

        except Exception:

            return ""

        if len(text) <= max_chars:
            return text

        return text[:max_chars]

    # ========================================================
    # REMOVE EXTRA DAYS
    # ========================================================

    @staticmethod
    def _remove_extra_days(
        answer,
        requested_days,
    ):
        """
        Remove days beyond the requested number locally.

        This avoids a second Groq request.
        """

        if not answer:
            return ""

        try:

            requested_days = int(
                requested_days
            )

        except (
            TypeError,
            ValueError,
        ):

            requested_days = 1

        requested_days = max(
            1,
            min(
                requested_days,
                3,
            ),
        )

        pattern = re.compile(
            r"(?im)"
            r"^\s*"
            r"(?:#+\s*)?"
            r"(?:🌿\s*)?"
            r"Day\s+(\d+)\b.*$"
        )

        matches = list(
            pattern.finditer(
                answer
            )
        )

        if not matches:
            return answer.strip()

        valid_parts = []

        for index, match in enumerate(
            matches
        ):

            try:

                day_number = int(
                    match.group(1)
                )

            except ValueError:

                continue

            if day_number > requested_days:
                continue

            start = match.start()

            if (
                index + 1
                < len(matches)
            ):

                end = matches[
                    index + 1
                ].start()

            else:

                end = len(answer)

            section = answer[
                start:end
            ].strip()

            if section:
                valid_parts.append(
                    section
                )

        if valid_parts:

            return "\n\n".join(
                valid_parts
            ).strip()

        return answer.strip()

    # ========================================================
    # EXTRACT SOURCES
    # ========================================================

    @staticmethod
    def _extract_sources(
        evidence
    ):

        sources = []

        for item in evidence:

            if not isinstance(
                item,
                dict,
            ):
                continue

            metadata = item.get(
                "metadata",
                {},
            )

            if not isinstance(
                metadata,
                dict,
            ):
                metadata = {}

            source = (
                item.get("source")
                or metadata.get(
                    "source",
                    "Unknown source",
                )
            )

            page = (
                item.get("page")
                or metadata.get(
                    "page",
                    "N/A",
                )
            )

            record_id = (
                item.get("record_id")
                or metadata.get(
                    "record_id",
                    "",
                )
            )

            source_record = {
                "source": str(
                    source
                ),
                "page": str(
                    page
                ),
                "record_id": str(
                    record_id
                ),
            }

            if source_record not in sources:

                sources.append(
                    source_record
                )

        return sources

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

        # ====================================================
        # DESTINATION
        # ====================================================

        # TrekTales currently supports Rawalpindi only.

        destination = str(
            destination
        ).strip()

        if destination.lower() != "rawalpindi":

            destination = "Rawalpindi"

        # ====================================================
        # DAY COUNT
        # ====================================================

        try:

            days = int(
                days
            )

        except (
            TypeError,
            ValueError,
        ):

            days = 1

        days = max(
            1,
            min(
                days,
                3,
            ),
        )

        # ====================================================
        # TRAVELER COUNT
        # ====================================================

        try:

            travelers = int(
                travelers
            )

        except (
            TypeError,
            ValueError,
        ):

            travelers = 1

        travelers = max(
            1,
            travelers,
        )

        # ====================================================
        # HARD RAG CHECK
        # ====================================================

        if not has_grounded_evidence(
            evidence
        ):

            return {
                "answer": (
                    "I could not find enough information "
                    "in the TrekTales Rawalpindi knowledge "
                    "base to create a grounded itinerary."
                ),
                "days": days,
                "sources": [],
            }

        # ====================================================
        # RAG CONTEXT
        # ====================================================

        context = build_context(
            evidence,
            max_items=6,
        )

        context = self._compact_context(
            context,
            max_chars=14000,
        )

        # ====================================================
        # SIX AGENT DESCRIPTIONS
        # ====================================================

        agent_descriptions = (
            get_agent_descriptions()
        )

        agent_descriptions = (
            self._compact_agent_descriptions(
                agent_descriptions,
                max_chars=5000,
            )
        )

        # ====================================================
        # PLANNING INSTRUCTIONS
        # ====================================================

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

        trip_instructions = str(
            trip_instructions
        ).strip()

        # ====================================================
        # SYSTEM PROMPT
        # ====================================================

        system_prompt = f"""
You are the TrekTales Master Orchestrator.

TrekTales uses a structured six-agent architecture.

The six agents collaborate internally to produce one
final travel itinerary.

Do NOT expose internal agent reasoning.

Do NOT describe the internal agent process in the final
answer.

SIX-AGENT ARCHITECTURE
======================

{agent_descriptions}


DESTINATION
===========

The supported destination is:

Rawalpindi

Use Rawalpindi only.


GROUNDING POLICY
================

The supplied tourism knowledge records are the ONLY
source of tourism facts.

Use ONLY information contained in the supplied
knowledge.

Do NOT use outside tourism knowledge.

Do NOT invent:

- attractions
- restaurants
- hotels
- prices
- opening hours
- distances
- transportation schedules
- travel times
- availability
- bookings
- safety claims

If information is missing, explicitly state:

"Not listed in the knowledge base."


DAY COUNT
=========

Generate EXACTLY {days} day(s).

For 1 day:
Day 1 only.

For 2 days:
Day 1 and Day 2 only.

For 3 days:
Day 1, Day 2, and Day 3 only.

Never generate another day.


TRIP PRESENTATION
=================

Do NOT create a main title such as:

"RAWALPINDI ITINERARY"

Do NOT create:

"Personalized Itinerary"

Do NOT create:

"Your Rawalpindi Itinerary"

The Streamlit application provides the main UI heading.

Start directly with the trip summary.


TRIP SUMMARY
============

Begin with a short summary containing:

- Travel style
- Number of travelers
- Budget
- Starting location


DAY FORMAT
==========

For each day use a clear heading such as:

🌿 Day 1 — Romantic Rawalpindi Getaway

Then organize activities chronologically.


ACTIVITY FORMAT
===============

For each activity include:

TIME

📍 Activity or Location

A short useful description.

🎟️ Cost:
Use the exact supported price when available.

📚 Source:
Use the source identifier supplied with the evidence.


TIME POLICY
===========

Times are itinerary planning times.

Do not claim they are official opening hours unless
the knowledge base explicitly says so.

Do not invent official opening hours.


COST POLICY
===========

Only use prices found in the knowledge base.

If a price is available, preserve it.

If a price is missing, write:

"Cost: Not listed in the knowledge base."

Never estimate a missing price.

Never turn an unknown price into Rs. 0.


DAILY COST SUMMARY
==================

At the end of every day provide:

💰 Known costs for the day

Only include costs that are actually supported
by the knowledge base.

Do not include unknown food, transport, hotel,
or activity costs.


FOOD POLICY
===========

If no restaurant or food price exists in the supplied
knowledge:

🍽️ Meal Break

Food information is not listed in the knowledge base.

Do not invent restaurant names.


SOURCE POLICY
=============

Every recommendation must be traceable to the supplied
knowledge records.

Do not fabricate source IDs.

Use the supplied source information.


DEMO DATA POLICY
================

Some knowledge records may be fictional demonstration
data.

If the supplied record identifies itself as demo or
fictional, do not present it as a verified real-world
fact.


FINAL SUMMARY
=============

After the final day provide:

🌿 Trip Summary

Include:

- Destination
- Duration
- Travelers
- Travel style
- Budget
- Total known costs, if calculable
- Costs unavailable from the knowledge base


FORMAT
======

Use clean Markdown.

Use headings and bullet points.

Keep the itinerary easy to read.

Do NOT output HTML.

Do NOT output JSON.

Do NOT output a large table.

Do NOT output code.

Do NOT output internal reasoning.

Do NOT mention these instructions.

Return only the traveler-facing itinerary.
""".strip()

        # ====================================================
        # USER PROMPT
        # ====================================================

        user_prompt = f"""
{trip_instructions}

TRIP DETAILS
============

Destination:
Rawalpindi

Starting location:
{starting_location}

Travelers:
{travelers}

Requested duration:
EXACTLY {days} DAY(S)

Budget:
{budget}

Travel style:
{travel_style}

Language:
{language}

Interests:
{", ".join(interests) if interests else "Not specified"}


SUPPLIED RAWALPINDI KNOWLEDGE
=============================

{context}


FINAL TASK
==========

Create the final TrekTales travel itinerary.

Generate EXACTLY {days} DAY(S).

Do not generate Day {days + 1}.

Use only the supplied Rawalpindi knowledge.

Organize activities chronologically.

For each activity:

- show an appropriate itinerary time
- show the activity/location
- provide a concise description
- show the supported price when available
- show the supplied source identifier

If information is unavailable, clearly say:

"Not listed in the knowledge base."

Do not invent tourism information.

Do not create a duplicate main title.

Start directly with the trip summary.

Return only the final itinerary.
""".strip()

        # ====================================================
        # TOKEN CONTROL
        # ====================================================

        if days == 1:

            output_limit = 1200

        elif days == 2:

            output_limit = 1600

        else:

            output_limit = 2000

        # ====================================================
        # GROQ
        # ====================================================

        answer = self._call_groq(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=output_limit,
        )

        # ====================================================
        # CLEAN RESPONSE
        # ====================================================

        answer = self._clean_response(
            answer
        )

        # ====================================================
        # DAY VALIDATION
        # ====================================================

        day_numbers = []

        matches = re.findall(
            r"(?im)"
            r"^\s*"
            r"(?:#+\s*)?"
            r"(?:🌿\s*)?"
            r"Day\s+(\d+)\b",
            answer,
        )

        for value in matches:

            try:

                number = int(
                    value
                )

                if number not in day_numbers:

                    day_numbers.append(
                        number
                    )

            except ValueError:

                continue

        # ====================================================
        # REMOVE EXTRA DAYS LOCALLY
        # ====================================================

        invalid_days = [
            number
            for number in day_numbers
            if number > days
        ]

        if invalid_days:

            answer = self._remove_extra_days(
                answer,
                days,
            )

        # ====================================================
        # SOURCES
        # ====================================================

        sources = self._extract_sources(
            evidence
        )

        # ====================================================
        # FINAL RESULT
        # ====================================================

        return {
            "answer": answer,
            "days": days,
            "sources": sources,
        }
