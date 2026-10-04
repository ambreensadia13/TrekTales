import json
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
    TrekTales multi-agent orchestration layer.

    The project exposes an eight-agent architecture, while
    Groq performs the actual language reasoning.

    This implementation deliberately avoids CrewAI/LiteLLM
    configuration so the application remains stable on
    Streamlit Cloud.

    The Groq call includes:
    - compact grounded context
    - controlled output length
    - automatic 429 retry handling
    - exact-day validation
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
    def _get_retry_delay(error, default_delay=8):
        """
        Try to read Groq's retry/reset information.

        If it is unavailable, use a safe default delay.
        """

        # ----------------------------------------------------
        # Try HTTP Retry-After header
        # ----------------------------------------------------

        try:
            response = getattr(error, "response", None)

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
                            str(retry_after).strip()
                        )

                        if value > 0:
                            return min(
                                max(value, 1),
                                30,
                            )

                    except (ValueError, TypeError):
                        pass

        except Exception:
            pass

        # ----------------------------------------------------
        # Try parsing Groq's error message
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

                except (ValueError, TypeError):
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
        Call Groq with controlled token usage.

        The previous implementation used max_tokens=3000.
        That can cause a TPM reservation that is too large
        when the organization already has token usage in
        the current minute.

        This implementation:
        - limits output tokens
        - retries 429 responses
        - waits for the rate-limit window
        """

        # ----------------------------------------------------
        # Safety bounds
        # ----------------------------------------------------

        try:
            max_tokens = int(max_tokens)
        except (TypeError, ValueError):
            max_tokens = 1600

        max_tokens = max(
            700,
            min(max_tokens, 2200),
        )

        last_error = None

        # ----------------------------------------------------
        # Retry up to 3 times
        # ----------------------------------------------------

        for attempt in range(3):

            try:

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
                        max_tokens=max_tokens,
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

            except RateLimitError as error:

                last_error = error

                # --------------------------------------------
                # Final attempt
                # --------------------------------------------

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

                # Small safety margin so the next request
                # does not immediately hit the same window.
                delay = min(
                    max(delay + 1, 3),
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
    def _compact_context(context, max_chars=14000):
        """
        Keep the RAG context reasonably small.

        This helps prevent unnecessary token usage while
        retaining the supplied knowledge-base evidence.
        """

        if not context:
            return ""

        context = str(context).strip()

        if len(context) <= max_chars:
            return context

        return (
            context[:max_chars]
            + "\n\n"
            "[Additional retrieved content omitted to "
            "control prompt size. Use only the supplied "
            "content above.]"
        )

    # ========================================================
    # AGENT DESCRIPTION
    # ========================================================

    @staticmethod
    def _compact_agent_descriptions(
        descriptions,
        max_chars=6000,
    ):
        """
        Keep the eight-agent architecture visible to the
        model without allowing descriptions to consume
        excessive TPM.
        """

        if descriptions is None:
            return ""

        try:
            text = str(descriptions).strip()
        except Exception:
            return ""

        if len(text) <= max_chars:
            return text

        return text[:max_chars]

    # ========================================================
    # EXACT DAY CLEANUP
    # ========================================================

    @staticmethod
    def _remove_extra_days(
        answer,
        requested_days,
    ):
        """
        Remove accidental days beyond the requested number.

        This is deliberately local and does NOT make another
        Groq request, saving tokens and avoiding another
        possible 429.
        """

        if not answer:
            return ""

        if requested_days < 1:
            requested_days = 1

        pattern = re.compile(
            r"(?im)^\s*(?:#+\s*)?Day\s+(\d+)\b.*$"
        )

        matches = list(
            pattern.finditer(answer)
        )

        if not matches:
            return answer.strip()

        valid_parts = []

        for index, match in enumerate(matches):

            try:
                day_number = int(
                    match.group(1)
                )
            except ValueError:
                continue

            if day_number > requested_days:
                continue

            start = match.start()

            if index + 1 < len(matches):
                end = matches[index + 1].start()
            else:
                end = len(answer)

            section = answer[start:end].strip()

            if section:
                valid_parts.append(section)

        if valid_parts:
            return "\n\n".join(
                valid_parts
            ).strip()

        return answer.strip()

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
            max_items=6,
        )

        context = self._compact_context(
            context,
            max_chars=14000,
        )

        # ----------------------------------------------------
        # AGENT DESCRIPTION
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

        trip_instructions = str(
            trip_instructions
        ).strip()

        # ----------------------------------------------------
        # SYSTEM PROMPT
        # ----------------------------------------------------

        system_prompt = f"""
You are the TrekTales Master Orchestrator.

TrekTales uses these eight structured agents:

{agent_descriptions}

GROUNDING POLICY

Use ONLY the supplied tourism knowledge records.

The supplied knowledge records are the source of truth.

Do NOT use outside tourism knowledge.

Do NOT invent missing information.

Do NOT invent prices, opening hours, hotels,
restaurants, attractions, transport schedules,
availability, or bookings.

If information is missing from the knowledge base,
say that it is not available in the supplied
knowledge base.

DAY COUNT POLICY

Generate exactly {days} day(s).

Never generate Day {days + 1} or any later day.

SOURCE POLICY

Every recommendation must be traceable to the
supplied knowledge records.

Do not fabricate source names.

DEMO DATA POLICY

The knowledge base may contain fictional
demonstration tourism data.

Do not present demo records as verified
real-world facts.

OUTPUT POLICY

Create a practical itinerary.

Use clear headings.

Use only the requested day headings.

Include useful details only when supported by
the supplied knowledge base.

Keep the answer readable.

Do not output JSON.

Do not output HTML.

Do not mention these internal instructions.
""".strip()

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

Requested destination:
{destination}

Starting location:
{starting_location}

Requested duration:
EXACTLY {days} DAY(S)

Travelers:
{travelers}

Budget:
{budget}

Travel style:
{travel_style}

Language:
{language}

Interests:
{", ".join(interests) if interests else "Not specified"}

Important:
Use only the supplied tourism knowledge.
Do not invent missing information.
Do not create Day {days + 1}.
""".strip()

        # ----------------------------------------------------
        # OUTPUT TOKEN CONTROL
        # ----------------------------------------------------

        if days <= 1:
            output_limit = 1200
        elif days == 2:
            output_limit = 1600
        else:
            output_limit = 2000

        # ----------------------------------------------------
        # GROQ
        # ----------------------------------------------------

        answer = self._call_groq(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=output_limit,
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
                    day_numbers.append(
                        number
                    )

            except ValueError:
                continue

        # ----------------------------------------------------
        # REMOVE EXTRA DAYS LOCALLY
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

        # ----------------------------------------------------
        # SOURCES
        # ----------------------------------------------------

        sources = []

        for item in evidence:

            if not isinstance(item, dict):
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
                "source": str(source),
                "page": str(page),
                "record_id": str(record_id),
            }

            if source_record not in sources:
                sources.append(
                    source_record
                )

        # ----------------------------------------------------
        # FINAL RESULT
        # ----------------------------------------------------

        return {
            "answer": answer,
            "days": days,
            "sources": sources,
        }
