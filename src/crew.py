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

    The application uses a structured multi-agent architecture.
    Groq performs the final language reasoning.

    Important design rules:
    - Tourism information must come from the supplied RAG evidence.
    - Missing information must never be invented.
    - The requested number of days is enforced.
    - Source information is preserved.
    - Groq requests are kept reasonably small to reduce TPM usage.
    - Groq 429 errors are retried automatically.
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

        The previous version used max_tokens=3000.
        This version uses a smaller dynamic limit and
        retries temporary 429 errors.
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
        # Maximum of three attempts
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
                # No more attempts
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

        # Remove accidental HTML tags.
        text = re.sub(
            r"<[^>]+>",
            "",
            text,
        )

        # Remove excessive blank lines.
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
        Keep the retrieved RAG context within a reasonable
        size so the Groq request does not become unnecessarily
        large.
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
            "control prompt size. Use only the supplied "
            "knowledge above.]"
        )

    # ========================================================
    # COMPACT AGENT DESCRIPTIONS
    # ========================================================

    @staticmethod
    def _compact_agent_descriptions(
        descriptions,
        max_chars=6000,
    ):
        """
        Keep the agent architecture visible without allowing
        lengthy descriptions to consume excessive tokens.
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
    # REMOVE EXTRA DAYS LOCALLY
    # ========================================================

    @staticmethod
    def _remove_extra_days(
        answer,
        requested_days,
    ):
        """
        Remove accidentally generated days beyond the
        requested number.

        This is done locally instead of sending a second
        request to Groq.
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

        if requested_days < 1:
            requested_days = 1

        pattern = re.compile(
            r"(?im)"
            r"^\s*"
            r"(?:#+\s*)?"
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
    # SOURCE EXTRACTION
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

        # ----------------------------------------------------
        # DESTINATION SAFETY
        # ----------------------------------------------------

        # TrekTales currently uses Rawalpindi tourism
        # knowledge as its grounded destination.
        #
        # The UI also fixes the destination to Rawalpindi.
        #
        # This check prevents an unsupported destination
        # from accidentally reaching the model.

        destination = str(
            destination
        ).strip()

        if destination.lower() != "rawalpindi":

            destination = "Rawalpindi"

        # ----------------------------------------------------
        # DAY SAFETY
        # ----------------------------------------------------

        try:

            days = int(days)

        except (
            TypeError,
            ValueError,
        ):

            days = 1

        days = max(
            1,
            min(days, 3),
        )

        # ----------------------------------------------------
        # HARD RAG SAFETY CHECK
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # RAG CONTEXT
        # ----------------------------------------------------

        context = build_context(
            evidence,
            max_items=6,
        )

        context = self._compact_context(
            context,
            max_chars=14000,
        )

        # ----------------------------------------------------
        # AGENT DESCRIPTIONS
        # ----------------------------------------------------

        agent_descriptions = (
            get_agent_descriptions()
        )

        agent_descriptions = (
            self._compact_agent_descriptions(
                agent_descriptions,
                max_chars=6000,
            )
        )

        # ----------------------------------------------------
        # TRIP INSTRUCTIONS
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

        trip_instructions = str(
            trip_instructions
        ).strip()

        # ====================================================
        # SYSTEM PROMPT
        # ====================================================

        system_prompt = f"""
You are the TrekTales Master Orchestrator.

TrekTales uses a structured six-agent travel-planning
architecture.

The agents work together to create one final itinerary.
Do not expose internal agent reasoning.

The supplied tourism knowledge is the ONLY source of
tourism facts.

SIX-AGENT ARCHITECTURE
======================

{agent_descriptions}


DESTINATION
===========

The supported destination for this TrekTales version
is Rawalpindi.

Use Rawalpindi only.


GROUNDING POLICY
================

Use ONLY the supplied tourism knowledge records.

The supplied knowledge records are the source of truth.

Do NOT use outside tourism knowledge.

Do NOT invent missing information.

Do NOT invent prices.

Do NOT invent restaurants.

Do NOT invent hotels.

Do NOT invent attractions.

Do NOT invent transportation schedules.

Do NOT invent opening hours.

Do NOT invent distances.

Do NOT invent travel times.

Do NOT claim live availability.

Do NOT claim that a booking was made.

If something is not present in the knowledge base,
say:

"Not listed in the knowledge base."


DAY COUNT POLICY
================

Generate EXACTLY {days} day(s).

If the request is for one day, generate only Day 1.

If the request is for two days, generate only Day 1
and Day 2.

If the request is for three days, generate only Day 1,
Day 2, and Day 3.

Never generate an additional day.


ITINERARY STRUCTURE
===================

Start with:

🌿 RAWALPINDI ITINERARY

Then provide a short trip summary containing:

- Travel style
- Number of travelers
- Budget
- Starting location

Then create the requested days in chronological order.

For every day use a heading similar to:

🌿 DAY 1 — descriptive day title

For every activity include:

TIME

ACTIVITY

LOCATION

SHORT DESCRIPTION

KNOWN COST, if supported

SOURCE

Keep the itinerary practical and easy to follow.


TIME POLICY
===========

Times are for itinerary organization.

Do NOT present an approximate itinerary time as an
official opening hour.

Only state official opening hours when the knowledge
base explicitly provides them.


COST POLICY
===========

If the knowledge base provides a price, show the
supported price.

If a price is missing, write:

"Cost: Not listed in the knowledge base."

Never estimate a missing price.

Never convert an unknown cost into a zero cost.

At the end of each day, provide:

💰 Known costs for the day

Only calculate costs that can actually be calculated
from the supplied knowledge.

Do not include unknown food, transport, hotel, or
activity costs in the total.


MEAL POLICY
===========

If the knowledge base does not contain a specific
restaurant or food information, provide a simple
meal break.

State:

"Food cost: Not listed in the knowledge base."

Do not invent a restaurant.


SOURCE POLICY
=============

Every tourism recommendation must be traceable to
the supplied knowledge records.

Do not fabricate source names.

Preserve the source identifiers supplied with the
evidence.


DEMO DATA POLICY
================

The knowledge base may contain fictional demonstration
tourism records.

Do not present demo records as verified real-world facts.

If a record is clearly marked as demo or fictional,
preserve that indication in the itinerary.


FINAL SUMMARY
=============

After the final requested day, provide:

🌿 TRIP SUMMARY

Include:

- Destination
- Number of days
- Number of travelers
- Travel style
- Budget
- Total known costs, if calculable
- Costs that are not available in the knowledge base

Never present unknown costs as zero.


FORMAT POLICY
=============

Use clean Markdown.

Use headings.

Use bullet points where useful.

Use simple readable sections.

Do not output JSON.

Do not output HTML.

Do not output tables unless a table genuinely improves
readability.

Do not output internal agent reasoning.

Do not mention system prompts.

Do not mention internal orchestration.

Return only the final traveler-facing itinerary.
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

Number of travelers:
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


SUPPLIED RAWALPINDI TOURISM KNOWLEDGE
=====================================

{context}


FINAL TASK
==========

Create the final TrekTales itinerary.

Generate EXACTLY {days} DAY(S).

Do not generate Day {days + 1}.

Use only the supplied tourism knowledge.

For every supported activity:

- Give a clear time.
- Give the activity name.
- Give the location when available.
- Give a concise useful description.
- Give the supported cost when available.
- Give the supplied source identifier.

For missing information, clearly say that it is not
listed in the knowledge base.

Do not invent tourism information.

Make the final answer polished, useful, chronological,
and easy for a traveler to follow.

Return only the final itinerary.
""".strip()

        # ====================================================
        # OUTPUT TOKEN CONTROL
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

        # ----------------------------------------------------
        # Remove extra days locally
        # ----------------------------------------------------

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
