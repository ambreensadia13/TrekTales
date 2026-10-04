import re
import time
from typing import Any, Dict, List

from openai import OpenAI, RateLimitError

from src.config import (
    GROQ_API_KEY,
    GROQ_BASE_URL,
    GROQ_MODEL,
)

from src.agents import get_agent_descriptions

from src.rag import (
    build_context,
    has_grounded_evidence,
)

from src.tasks import build_planning_instructions


class TrekTalesCrew:
    """
    TrekTales AI itinerary orchestrator.

    Responsibilities:
    - Ground itinerary generation in the tourism knowledge base.
    - Produce detailed tourist-friendly itineraries.
    - Support 1, 2, or 3 days.
    - Keep Rawalpindi as the supported destination.
    - Preserve source information.
    - Avoid fabricated tourism facts.
    - Use Groq for final itinerary generation.
    - Handle temporary Groq rate limits.
    """

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(self):

        if not GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is missing. "
                "Add GROQ_API_KEY to Streamlit Secrets."
            )

        self.client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url=GROQ_BASE_URL,
        )

    # ============================================================
    # RATE LIMIT HANDLING
    # ============================================================

    @staticmethod
    def _get_retry_delay(
        error: Exception,
        default_delay: int = 8,
    ) -> float:
        """
        Extract retry delay from a Groq 429 response when possible.
        """

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
                            str(retry_after).strip()
                        )

                        if value > 0:
                            return min(
                                max(value, 1.0),
                                30.0,
                            )

                    except (
                        ValueError,
                        TypeError,
                    ):
                        pass

        except Exception:
            pass

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
                            max(value, 1.0),
                            30.0,
                        )

                except (
                    ValueError,
                    TypeError,
                ):
                    pass

        return float(default_delay)

    # ============================================================
    # GROQ REQUEST
    # ============================================================

    def _call_groq(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 3000,
    ) -> str:
        """
        Send the final itinerary request to Groq.

        Uses a controlled number of retries for temporary
        rate-limit responses.
        """

        try:

            max_tokens = int(
                max_tokens
            )

        except (
            TypeError,
            ValueError,
        ):

            max_tokens = 3000

        max_tokens = max(
            1200,
            min(
                max_tokens,
                4000,
            ),
        )

        last_error = None

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
                        temperature=0.25,
                        max_tokens=max_tokens,
                    )
                )

                if not response.choices:
                    raise RuntimeError(
                        "Groq returned no response choices."
                    )

                content = (
                    response
                    .choices[0]
                    .message
                    .content
                )

                if not content:
                    raise RuntimeError(
                        "Groq returned an empty itinerary."
                    )

                return str(
                    content
                ).strip()

            except RateLimitError as error:

                last_error = error

                if attempt >= 2:

                    raise RuntimeError(
                        "Groq rate limit is currently active. "
                        "Please wait a few seconds and generate "
                        "the itinerary again."
                    ) from error

                delay = self._get_retry_delay(
                    error,
                    default_delay=8,
                )

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

        if last_error:

            raise RuntimeError(
                "Unable to complete the Groq request."
            ) from last_error

        raise RuntimeError(
            "Unable to complete the Groq request."
        )

    # ============================================================
    # TEXT HELPERS
    # ============================================================

    @staticmethod
    def _safe_string(
        value: Any,
        default: str = "",
    ) -> str:

        if value is None:
            return default

        try:
            return str(
                value
            ).strip()

        except Exception:
            return default

    # ============================================================
    # COMPACT RAG CONTEXT
    # ============================================================

    @staticmethod
    def _compact_context(
        context: Any,
        max_chars: int = 18000,
    ) -> str:
        """
        Keep enough knowledge-base information for detailed
        itineraries without creating an unnecessarily huge prompt.
        """

        context = TrekTalesCrew._safe_string(
            context
        )

        if not context:
            return ""

        if len(context) <= max_chars:
            return context

        return (
            context[:max_chars]
            + "\n\n"
            "[Additional retrieved knowledge was omitted "
            "to control prompt size.]"
        )

    # ============================================================
    # AGENT DESCRIPTION
    # ============================================================

    @staticmethod
    def _get_agents_text() -> str:

        try:

            descriptions = get_agent_descriptions()

        except Exception:

            descriptions = ""

        descriptions = TrekTalesCrew._safe_string(
            descriptions
        )

        if not descriptions:
            return (
                "The TrekTales agents collaboratively "
                "analyze the retrieved tourism information "
                "and prepare the final itinerary."
            )

        if len(descriptions) > 6000:

            descriptions = descriptions[:6000]

        return descriptions

    # ============================================================
    # SOURCE EXTRACTION
    # ============================================================

    @staticmethod
    def _extract_sources(
        evidence: Any,
    ) -> List[Dict[str, str]]:
        """
        Extract unique source/page combinations.

        The same PDF appearing on multiple pages remains visible
        as separate references when the pages differ.
        Exact duplicate source/page pairs are removed.
        """

        sources = []

        if not evidence:
            return sources

        seen = set()

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
                    "source"
                )
                or metadata.get(
                    "filename"
                )
                or "Unknown source"
            )

            page = (
                item.get("page")
                or metadata.get(
                    "page"
                )
                or metadata.get(
                    "page_number"
                )
                or "N/A"
            )

            record_id = (
                item.get("record_id")
                or metadata.get(
                    "record_id"
                )
                or ""
            )

            source = TrekTalesCrew._safe_string(
                source,
                "Unknown source",
            )

            page = TrekTalesCrew._safe_string(
                page,
                "N/A",
            )

            record_id = TrekTalesCrew._safe_string(
                record_id
            )

            key = (
                source.lower(),
                page.lower(),
            )

            if key in seen:
                continue

            seen.add(key)

            sources.append(
                {
                    "source": source,
                    "page": page,
                    "record_id": record_id,
                }
            )

        return sources

    # ============================================================
    # RESPONSE CLEANING
    # ============================================================

    @staticmethod
    def _clean_response(
        text: str,
    ) -> str:

        text = TrekTalesCrew._safe_string(
            text
        )

        if not text:
            return ""

        # Remove code fences.
        text = re.sub(
            r"^\s*```(?:markdown|md|text)?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\s*```\s*$",
            "",
            text,
        )

        # Remove HTML.
        text = re.sub(
            r"<[^>]+>",
            "",
            text,
        )

        # Remove duplicate application-level titles.
        title_patterns = [
            r"^\s*#+\s*🌿\s*RAWALPINDI\s+ITINERARY\s*$",
            r"^\s*🌿\s*RAWALPINDI\s+ITINERARY\s*$",
            r"^\s*#+\s*PERSONALIZED\s+ITINERARY\s*$",
            r"^\s*PERSONALIZED\s+ITINERARY\s*$",
            r"^\s*#+\s*YOUR\s+RAWALPINDI\s+ITINERARY\s*$",
            r"^\s*YOUR\s+RAWALPINDI\s+ITINERARY\s*$",
        ]

        for pattern in title_patterns:

            text = re.sub(
                pattern,
                "",
                text,
                flags=re.IGNORECASE | re.MULTILINE,
            )

        # Normalize excessive whitespace.
        text = re.sub(
            r"\n{4,}",
            "\n\n",
            text,
        )

        return text.strip()

    # ============================================================
    # DAY VALIDATION
    # ============================================================

    @staticmethod
    def _find_day_numbers(
        answer: str,
    ) -> List[int]:

        if not answer:
            return []

        matches = re.findall(
            r"(?im)"
            r"^\s*"
            r"(?:#+\s*)?"
            r"(?:🌿\s*)?"
            r"Day\s+(\d+)\b",
            answer,
        )

        numbers = []

        for value in matches:

            try:

                number = int(
                    value
                )

            except ValueError:

                continue

            if number not in numbers:
                numbers.append(
                    number
                )

        return numbers

    # ============================================================
    # REMOVE UNREQUESTED DAYS
    # ============================================================

    @staticmethod
    def _remove_extra_days(
        answer: str,
        requested_days: int,
    ) -> str:
        """
        Safety cleanup if the model accidentally creates
        Day 4+.
        """

        if not answer:
            return ""

        matches = list(
            re.finditer(
                r"(?im)"
                r"^\s*"
                r"(?:#+\s*)?"
                r"(?:🌿\s*)?"
                r"Day\s+(\d+)\b.*$",
                answer,
            )
        )

        if not matches:
            return answer.strip()

        parts = []

        for index, match in enumerate(
            matches
        ):

            try:

                day_number = int(
                    match.group(1)
                )

            except ValueError:

                continue

            start = match.start()

            if index + 1 < len(matches):

                end = matches[
                    index + 1
                ].start()

            else:

                end = len(answer)

            if day_number <= requested_days:

                section = answer[
                    start:end
                ].strip()

                if section:
                    parts.append(
                        section
                    )

        if parts:

            return "\n\n".join(
                parts
            ).strip()

        return answer.strip()

    # ============================================================
    # MAIN RUN METHOD
    # ============================================================

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
    ) -> Dict[str, Any]:
        """
        Generate the final tourist-facing itinerary.
        """

        # ========================================================
        # DESTINATION
        # ========================================================

        destination = self._safe_string(
            destination,
            "Rawalpindi",
        )

        # The current TrekTales RAG knowledge base is
        # Rawalpindi-focused.

        if destination.lower() != "rawalpindi":

            destination = "Rawalpindi"

        # ========================================================
        # DAYS
        # ========================================================

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

        # ========================================================
        # TRAVELERS
        # ========================================================

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

        # ========================================================
        # OTHER INPUTS
        # ========================================================

        starting_location = self._safe_string(
            starting_location,
            "Not specified",
        )

        budget = self._safe_string(
            budget,
            "Not specified",
        )

        travel_style = self._safe_string(
            travel_style,
            "Mixed",
        )

        language = self._safe_string(
            language,
            "English",
        )

        if interests is None:

            interests_list = []

        elif isinstance(
            interests,
            (list, tuple, set),
        ):

            interests_list = [
                self._safe_string(item)
                for item in interests
                if self._safe_string(item)
            ]

        else:

            interests_list = [
                self._safe_string(
                    interests
                )
            ]

        interests_text = (
            ", ".join(
                interests_list
            )
            if interests_list
            else "Not specified"
        )

        # ========================================================
        # KNOWLEDGE CHECK
        # ========================================================

        if not evidence:

            return {
                "answer": (
                    "I could not find enough information "
                    "in the TrekTales Rawalpindi knowledge "
                    "base to create a grounded itinerary."
                ),
                "days": days,
                "sources": [],
            }

        try:

            grounded = has_grounded_evidence(
                evidence
            )

        except Exception:

            grounded = bool(
                evidence
            )

        if not grounded:

            return {
                "answer": (
                    "I could not find enough grounded "
                    "information in the TrekTales "
                    "Rawalpindi knowledge base."
                ),
                "days": days,
                "sources": [],
            }

        # ========================================================
        # BUILD RAG CONTEXT
        # ========================================================

        try:

            context = build_context(
                evidence,
                max_items=6,
            )

        except TypeError:

            context = build_context(
                evidence
            )

        context = self._compact_context(
            context,
            max_chars=18000,
        )

        # ========================================================
        # AGENT INFORMATION
        # ========================================================

        agent_descriptions = (
            self._get_agents_text()
        )

        # ========================================================
        # EXISTING PLANNING INSTRUCTIONS
        # ========================================================

        try:

            planning_instructions = (
                build_planning_instructions(
                    destination=destination,
                    starting_location=starting_location,
                    days=days,
                    budget=budget,
                    travelers=travelers,
                    travel_style=travel_style,
                    language=language,
                    interests=interests_list,
                )
            )

        except Exception:

            planning_instructions = ""

        planning_instructions = (
            self._safe_string(
                planning_instructions
            )
        )

        # ========================================================
        # SYSTEM PROMPT
        # ========================================================

        system_prompt = f"""
You are the senior travel-planning orchestrator for
TrekTales.

Your job is to transform verified tourism knowledge
into a polished, detailed, attractive itinerary that
a real tourist can easily follow.

The internal TrekTales system contains multiple
specialized agents.

Their work happens internally.

Do NOT expose internal reasoning, agent deliberations,
chain-of-thought, or technical implementation details.

============================================================
SUPPORTED DESTINATION
============================================================

Rawalpindi.

The current TrekTales tourism knowledge base is
specifically intended for Rawalpindi.

Do not change the destination.

============================================================
KNOWLEDGE-GROUNDED TRAVEL PLANNING
============================================================

The supplied knowledge-base evidence is the source of
truth for tourism facts.

You may organize, combine, summarize, and sequence
information from the evidence.

You may make reasonable itinerary-ordering decisions
using the supplied activities.

However, NEVER invent tourism facts.

Never fabricate:

- attraction names
- restaurants
- hotels
- entrance fees
- food prices
- transport fares
- opening hours
- closing hours
- distances
- exact travel durations
- availability
- reservations
- booking status
- contact details
- addresses
- events
- discounts
- weather
- safety guarantees

If a useful piece of information is missing, say:

"Not listed in the knowledge base."

============================================================
IMPORTANT: DETAILED DOES NOT MEAN FABRICATED
============================================================

The itinerary should feel rich and complete because of:

- useful descriptions
- chronological organization
- morning planning
- afternoon planning
- evening planning
- breaks
- activity duration when supported
- known costs
- practical sequencing
- source references
- daily summaries
- trip-level summary

Do NOT make it detailed by inventing facts.

============================================================
EXACT NUMBER OF DAYS
============================================================

The requested trip length is:

{days} day(s)

Generate exactly:

{days} day(s)

If the trip is 1 day:
Only Day 1.

If the trip is 2 days:
Day 1 and Day 2.

If the trip is 3 days:
Day 1, Day 2 and Day 3.

Never create Day 4 or any additional day.

============================================================
TOURIST-FRIENDLY OUTPUT
============================================================

The output should look like a professional travel
planner rather than a technical AI response.

Do NOT begin with:

"🌿 RAWALPINDI ITINERARY"

Do NOT begin with:

"Personalized Itinerary"

Do NOT begin with:

"Your Rawalpindi Itinerary"

The Streamlit application already provides the main
page heading.

Begin directly with a compact trip overview.

============================================================
TRIP OVERVIEW
============================================================

Start with:

📋 Trip Overview

Include:

• Destination
• Duration
• Travelers
• Travel style
• Budget
• Starting location
• Main interests

Keep this overview concise.

============================================================
DAY STRUCTURE
============================================================

Each day must feel like a complete day.

Use:

🌿 Day 1 — [attractive descriptive subtitle]

Then divide the day naturally into:

🌅 Morning

☀️ Afternoon

🌇 Evening

Use these sections when the retrieved activities
support them.

Do not invent activities merely to fill a section.

============================================================
ACTIVITY DETAIL
============================================================

For each recommended activity provide:

🕐 Time

📍 Activity / Location

A useful 2–4 sentence description explaining why
the activity fits the selected travel style and
interests.

🎟️ Known cost

📚 Source

Example structure:

🕐 09:00 – 11:00

📍 Activity Name

A concise tourist-friendly description based only
on the knowledge base.

🎟️ Cost: Rs. XXX

📚 Source: filename.pdf — Page X

If the source does not contain a price:

🎟️ Cost: Not listed in the knowledge base.

============================================================
TIME HANDLING
============================================================

Create practical itinerary time slots.

If the knowledge base explicitly provides a duration,
respect it.

If it does not provide an exact duration, use a
reasonable planning block without claiming that the
location officially requires that amount of time.

Do not present planning times as official opening hours.

For example:

"09:00 – 10:30"

is an itinerary planning suggestion.

It must NOT be described as official opening hours
unless the evidence explicitly says so.

============================================================
SEQUENCING
============================================================

Arrange the supplied activities in a sensible order.

Try to avoid unnecessary repetition.

Do not add an attraction simply because a normal
tourist itinerary might include it.

Only use activities supported by the supplied evidence.

============================================================
MEALS AND BREAKS
============================================================

Include reasonable meal or rest breaks when they help
the itinerary flow.

However:

Do NOT invent restaurant names.

Do NOT invent food prices.

If restaurant or food information is unavailable:

🍽️ Meal Break

Food details are not listed in the knowledge base.

============================================================
COSTS
============================================================

Use only costs explicitly supported by the evidence.

Never estimate.

Never convert an unknown cost into zero.

At the end of each day include:

💰 Known Cost Summary

List the known costs that can actually be calculated.

Then state:

"Additional costs are not listed in the knowledge base."

when applicable.

============================================================
BUDGET
============================================================

The user's budget is a planning preference.

Do not claim that the knowledge base guarantees
that the entire trip will fit within the budget.

Use the budget to prioritize appropriate activities
when the evidence supports doing so.

============================================================
TRAVEL STYLE
============================================================

Adapt the presentation to:

{travel_style}

For example:

Romantic:
- relaxed pacing
- scenic moments
- couple-friendly sequencing

Family:
- balanced pacing
- family-oriented activities

Adventure:
- active experiences
- energetic sequencing

Cultural:
- history and heritage emphasis

Photography:
- visually interesting locations

Relaxed:
- fewer rushed transitions

But do not invent characteristics of an attraction
that are not supported by the knowledge base.

============================================================
INTERESTS
============================================================

User interests:

{interests_text}

Prioritize retrieved activities that match these
interests when possible.

============================================================
SOURCE POLICY
============================================================

Every tourism recommendation must be supported by
the supplied evidence.

Preserve source identifiers.

If a source contains:

source = something.pdf
page = 4

show:

📚 Source: something.pdf — Page 4

Do not invent filenames or page numbers.

============================================================
DEMO DATA
============================================================

Some records may explicitly identify themselves as
demo, sample, or fictional information.

If the evidence says that a record is demo data,
do not present it as independently verified real-world
tourism information.

============================================================
FINAL DAY SUMMARY
============================================================

After each day include:

✨ Day Highlights

A short list of the main experiences.

💰 Known Cost Summary

Only supported costs.

============================================================
FINAL TRIP SUMMARY
============================================================

After the final day include:

🌿 Trip Wrap-Up

Include:

• Destination
• Number of days
• Travelers
• Travel style
• Budget
• Main interests
• Main experiences included
• Total known costs, only when they can actually
  be calculated from the evidence

Then clearly state that unlisted expenses are not
included in the known-cost calculation.

============================================================
FORMATTING
============================================================

Use clean Markdown.

Use:

- headings
- bullet points
- short paragraphs
- emojis where helpful
- bold labels

Do NOT use HTML.

Do NOT use JSON.

Do NOT use code blocks.

Do NOT output internal agent information.

Do NOT output chain-of-thought.

Do NOT repeat the main itinerary title.

The result must be visually comfortable to read on
a Streamlit travel-planning application.

============================================================
AGENT ARCHITECTURE
============================================================

The following describes the internal TrekTales agents:

{agent_descriptions}

Use their responsibilities internally.

Do not describe their internal reasoning to the tourist.
""".strip()

        # ========================================================
        # USER PROMPT
        # ========================================================

        user_prompt = f"""
Create the final TrekTales tourist itinerary.

============================================================
TRIP REQUEST
============================================================

Destination:
Rawalpindi

Starting location:
{starting_location}

Number of travelers:
{travelers}

Duration:
EXACTLY {days} DAY(S)

Budget:
{budget}

Travel style:
{travel_style}

Interests:
{interests_text}

Preferred response language:
{language}


============================================================
EXISTING PLANNING INSTRUCTIONS
============================================================

{planning_instructions}


============================================================
RAWALPINDI TOURISM KNOWLEDGE
============================================================

{context}


============================================================
FINAL REQUIREMENTS
============================================================

Create a COMPLETE, DETAILED and ATTRACTIVE tourist
itinerary.

The user should be able to understand what they can
do during each part of each day.

For every day:

1. Give the day an attractive subtitle.
2. Divide the day into morning, afternoon and evening
   where the evidence supports it.
3. Include multiple activities when supported by the
   knowledge base.
4. Give useful descriptions.
5. Include planning times.
6. Include known costs.
7. Include source references.
8. Include meal/rest breaks when useful.
9. Include a known-cost summary.
10. Include day highlights.

After the final day provide a trip wrap-up.

VERY IMPORTANT:

Generate EXACTLY {days} day(s).

Do not generate extra days.

Use ONLY the supplied tourism knowledge.

Do not invent attractions.

Do not invent restaurants.

Do not invent prices.

Do not invent opening hours.

Do not invent distances.

Do not invent transport schedules.

Do not invent booking availability.

If something is not provided, write:

"Not listed in the knowledge base."

Do not create a duplicate main itinerary title.

Return ONLY the final traveler-facing itinerary.
""".strip()

        # ========================================================
        # OUTPUT TOKEN BUDGET
        # ========================================================

        # More generous than the previous version so the model
        # can actually complete morning + afternoon + evening
        # sections without being cut off.

        if days == 1:

            output_limit = 2600

        elif days == 2:

            output_limit = 3200

        else:

            output_limit = 3800

        # ========================================================
        # GENERATE
        # ========================================================

        answer = self._call_groq(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=output_limit,
        )

        # ========================================================
        # CLEAN
        # ========================================================

        answer = self._clean_response(
            answer
        )

        # ========================================================
        # SAFETY CHECK FOR EXTRA DAYS
        # ========================================================

        detected_days = self._find_day_numbers(
            answer
        )

        if any(
            day > days
            for day in detected_days
        ):

            answer = self._remove_extra_days(
                answer,
                days,
            )

        # ========================================================
        # FALLBACK
        # ========================================================

        if not answer:

            answer = (
                "TrekTales could not produce a complete "
                "itinerary from the available Rawalpindi "
                "knowledge base. Please try generating "
                "the trip again."
            )

        # ========================================================
        # SOURCES
        # ========================================================

        sources = self._extract_sources(
            evidence
        )

        # ========================================================
        # RETURN
        # ========================================================

        return {
            "answer": answer,
            "days": days,
            "sources": sources,
        }


# ================================================================
# OPTIONAL FACTORY FUNCTION
# ================================================================

def create_crew() -> TrekTalesCrew:
    """
    Convenience factory used by application code if needed.
    """

    return TrekTalesCrew()
