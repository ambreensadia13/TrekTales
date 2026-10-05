from __future__ import annotations

import time
from typing import Any

import requests
import streamlit as st


class TrekTalesCrew:
    """
    TrekTales itinerary generation client.

    Uses Groq's OpenAI-compatible HTTP API.

    The itinerary is generated strictly from the tourism
    knowledge-base evidence supplied by the FAISS retriever.
    """

    def __init__(self):

        self.base_url = self._get_secret(
            "GROQ_BASE_URL",
            "https://api.groq.com/openai/v1",
        ).rstrip("/")

        self.model = self._get_secret(
            "GROQ_MODEL",
            "openai/gpt-oss-120b",
        )

        self.max_retries = 2

    # ========================================================
    # SECRET
    # ========================================================

    @staticmethod
    def _get_secret(
        name: str,
        default: str = "",
    ) -> str:

        try:

            value = st.secrets.get(
                name,
                default,
            )

            if value is None:
                return default

            return str(value).strip()

        except Exception:

            return default

    # ========================================================
    # API KEY
    # ========================================================

    def _get_api_key(self) -> str:

        key = self._get_secret(
            "GROQ_API_KEY",
            "",
        )

        if not key:

            raise RuntimeError(
                "GROQ_API_KEY is missing from Streamlit Secrets. "
                "Open Streamlit Cloud → Settings → Secrets and add "
                "your valid Groq API key."
            )

        if not key.startswith("gsk_"):

            raise RuntimeError(
                "GROQ_API_KEY does not appear to be a valid Groq API key. "
                "Check the value in Streamlit Secrets."
            )

        return key

    # ========================================================
    # EVIDENCE FORMATTER
    # ========================================================

    @staticmethod
    def _format_evidence(
        evidence: list[Any],
    ) -> str:

        if not evidence:

            return (
                "No tourism knowledge-base evidence was retrieved."
            )

        blocks = []

        for index, item in enumerate(
            evidence,
            start=1,
        ):

            if isinstance(item, dict):

                metadata = item.get(
                    "metadata",
                    {},
                )

                if not isinstance(metadata, dict):
                    metadata = {}

                text = (
                    item.get("text")
                    or item.get("content")
                    or item.get("chunk")
                    or metadata.get("text")
                    or metadata.get("content")
                    or ""
                )

                source = (
                    item.get("source")
                    or item.get("document")
                    or item.get("filename")
                    or metadata.get("source")
                    or metadata.get("document")
                    or metadata.get("filename")
                    or ""
                )

                page = (
                    item.get("page")
                    or metadata.get("page")
                    or ""
                )

            else:

                text = str(item)
                source = ""
                page = ""

            text = str(text).strip()

            if not text:
                continue

            source_text = str(source).strip()

            if source_text:

                source_text = source_text.replace(
                    "\\",
                    "/",
                )

                source_text = source_text.split("/")[-1]

            source_text = source_text.replace(
                ".html",
                "",
            )

            if page not in (
                "",
                None,
                "N/A",
                "n/a",
            ):

                location = (
                    f"{source_text} | Page {page}"
                )

            else:

                location = source_text

            blocks.append(
                f"[Knowledge Item {index}]\n"
                f"Source: {location or 'Knowledge Base'}\n"
                f"{text}"
            )

        if not blocks:

            return (
                "No usable tourism knowledge-base evidence "
                "was retrieved."
            )

        return "\n\n".join(blocks)

    # ========================================================
    # PROMPT
    # ========================================================

    def _build_prompt(
        self,
        destination: str,
        starting_location: str,
        days: int,
        budget: str,
        travelers: int,
        travel_style: str,
        language: str,
        interests: list[str],
        evidence: list[Any],
    ) -> str:

        evidence_text = self._format_evidence(
            evidence
        )

        interests_text = (
            ", ".join(
                str(item)
                for item in interests
            )
            if interests
            else "No specific interests provided."
        )

        return f"""
You are the TrekTales itinerary-generation engine.

Create a polished, useful and personalized travel itinerary.

CRITICAL GROUNDING RULE:

You MUST use ONLY the tourism knowledge-base evidence
provided at the end of this prompt.

The supplied knowledge base is the source of truth for
tourism facts.

Do NOT use outside tourism knowledge.

============================================================
TRIP DETAILS
============================================================

Destination:
{destination}

Starting location:
{starting_location}

Number of days:
{days}

Travelers:
{travelers}

Budget:
{budget}

Travel style:
{travel_style}

Language:
{language}

Interests:
{interests_text}

============================================================
ABSOLUTE ANTI-HALLUCINATION RULES
============================================================

1. Never invent tourism information.

2. Never invent:
   - attractions
   - restaurants
   - hotels
   - activities
   - prices
   - entry fees
   - ticket costs
   - travel times
   - distances
   - taxi fares
   - transport routes
   - opening hours
   - closing hours
   - addresses
   - phone numbers
   - contact information
   - availability
   - ratings
   - reviews
   - historical facts
   - weather conditions
   - safety conditions
   - local rules
   - events
   - schedules

3. Never use general knowledge to fill a missing
   tourism fact.

4. Never estimate a missing price.

5. Never estimate a missing distance.

6. Never estimate a missing travel time.

7. Never calculate a taxi cost when the required
   information is not explicitly present in the knowledge base.

8. Never create a restaurant, hotel or attraction simply
   because it would make the itinerary look better.

9. Every tourism recommendation must be supported by
   the supplied knowledge-base evidence.

10. If information is missing, explicitly write:

Not available in the TrekTales tourism knowledge base.

11. Do not create fake citations.

12. Do not create fake filenames.

13. Do not claim that a source contains information unless
    that information is actually present in the supplied evidence.

14. Do not output HTML.

15. Do not output Markdown code fences.

16. Use clean Markdown.

17. Follow the requested language.

18. Generate exactly {days} day(s).

19. Do not add an extra day.

20. Do not silently reduce the requested number of days.

21. If the evidence is insufficient for a particular day,
    clearly state that the required information is unavailable
    instead of inventing activities.

============================================================
OUTPUT STYLE
============================================================

Make the result visually organized and easy to read.

Use:

- Markdown headings
- Bold labels
- Bullet points
- Short paragraphs
- Emojis where appropriate
- Clear day sections
- Practical information
- Knowledge-base source names

Do not use HTML.

Do not use code fences.

============================================================
PERSONALIZED ACTIVITY SELECTION
============================================================

Do NOT include every location or activity found in the evidence.
Select only the strongest supported experiences for THIS traveler.

Selection priority:
1. Destination relevance
2. Travel style
3. Selected interests
4. Trip duration
5. Budget compatibility
6. Logical flow supported by the evidence
7. Practical realism

QUALITY OVER QUANTITY. For a 1-day trip, prefer a small number of
meaningful experiences instead of a crowded checklist. Do not force
every selected interest into the itinerary. If an interest has no
suitable evidence, do not invent an activity for it.

============================================================
REQUIRED OUTPUT STRUCTURE
============================================================

Begin with:

**🌿 Personalized {destination} Adventure Itinerary**

Then provide:

**📍 Trip Overview**

Include:

- Destination
- Starting location
- Duration
- Travelers
- Budget
- Travel style
- Interests

Only use values supplied in the trip details.

**✨ Why This Trip Fits You**

Write 2–3 concise sentences explaining how the selected plan matches
the traveler’s travel style, interests, duration and budget. Use only
the supplied trip details and supported evidence.

**🧭 Trip Flow**

Give a short one-line flow using only selected activities, for example:
Morning → History & Culture → Afternoon → Nature & Photography → Evening → Food
Do not introduce activities that are not used later in the itinerary.

============================================================
DAY-BY-DAY ITINERARY
============================================================

Create exactly {days} day sections.

Use:

**☀️ Day 1 — [appropriate theme]**

If required:

**☀️ Day 2 — [appropriate theme]**

Continue until exactly Day {days}.

For every day provide a useful structure such as:

**⏰ Suggested Schedule**

Use time blocks only when the knowledge base supports
the timing.

For each supported activity/place provide:

- Place/activity name
- What is supported by the knowledge base
- Relevant cost, if explicitly available
- Relevant practical information, if explicitly available
- Why it matches the user's stated interests, when this
  can be supported without inventing facts

Do not overcrowd a day.

Use exact clock times ONLY when the knowledge base explicitly provides them.
Otherwise use Morning, Late Morning, Afternoon or Evening. Never invent
arrival times, departure times, visit durations, travel durations or meal durations.

Do not manufacture times.

If a useful detail is missing, write:

Not available in the TrekTales tourism knowledge base.

============================================================
TRAVEL / TRANSPORT
============================================================

Only provide travel time, distance, route, fare or transport
information if explicitly supported by the evidence.

Otherwise write:

Not available in the TrekTales tourism knowledge base.

Never estimate it.

============================================================
BUDGET
============================================================

Provide:

**💰 Budget Considerations**

List only costs explicitly supported by the knowledge base.

If a cost is missing:

Not available in the TrekTales tourism knowledge base.

Do not invent a total.

Do not calculate a total using unsupported values.

If the evidence explicitly labels a price, fare or fee as demo, sample or test data,
preserve that label and write: “Sample value from the TrekTales knowledge base.”
Never present demo/sample/test data as a current, official or verified price.

============================================================
PHOTOGRAPHY
============================================================

Provide:

**📸 Photography Highlights**

Only mention locations or activities supported by the
knowledge base.

Do not invent viewpoints, photo spots, landscapes or
photography features.

If insufficient information exists:

Not available in the TrekTales tourism knowledge base.

============================================================
WHAT TO CARRY
============================================================

Provide:

**🎒 What to Carry**

Only recommend items directly supported by the evidence or clearly necessary
for a selected activity. Do not invent weather, terrain or safety conditions.
Do not present generic packing advice as knowledge-base facts.

If the evidence does not provide enough support, write:

Not available in the TrekTales tourism knowledge base.

============================================================
IMPORTANT INFORMATION
============================================================

Provide:

**⚠️ Important Information**

Include only important information supported by the
knowledge base.

For unavailable tourism information:

Not available in the TrekTales tourism knowledge base.

============================================================
OPTIONAL ALTERNATIVE
============================================================

If one strong evidence-supported activity matches the traveler’s interests
but does not fit naturally into the primary schedule, optionally provide:

**🔄 Optional Alternative**

Include at most one. If none exists, omit this section. Do not add an alternative
just to make the itinerary longer.

============================================================
KNOWLEDGE-BASE SOURCES
============================================================

Finish with:

**📚 Knowledge-Base Sources**

List only unique filenames that actually occur in the supplied evidence.
Use the filename only. Do not show retrieval numbers, embedding IDs, scores
or invented page numbers. Do not invent filenames.

============================================================
LANGUAGE
============================================================

Write the complete itinerary in:

{language}

============================================================
FINAL VALIDATION
============================================================

Before answering, internally verify:

- Exactly {days} day(s) are present.
- All tourism facts come from supplied evidence.
- No attraction was invented.
- No restaurant was invented.
- No hotel was invented.
- No price was invented.
- No travel time was invented.
- No distance was invented.
- No taxi fare was invented.
- No opening hours were invented.
- No fake source was invented.
- Missing information is explicitly marked.
- No HTML exists in the answer.
- No Markdown code fence exists in the answer.
- The destination remains {destination}.
- The response follows the requested language.
- Activities were selected for this traveler instead of listing every retrieved place.
- The itinerary is not unnecessarily overcrowded.
- Exact times are used only when explicitly supported.
- Demo/sample/test prices are clearly labeled and never presented as current.
- Packing advice is not invented or falsely attributed to the knowledge base.
- Sources are unique filenames only.

============================================================
TOURISM KNOWLEDGE-BASE EVIDENCE
============================================================

{evidence_text}

============================================================
END OF KNOWLEDGE-BASE EVIDENCE
============================================================

Now generate the final TrekTales itinerary.
"""

    # ========================================================
    # RATE LIMIT INFORMATION
    # ========================================================

    @staticmethod
    def _get_rate_limit_details(
        response: requests.Response,
    ) -> dict[str, str]:

        headers = response.headers

        return {
            "retry_after": headers.get(
                "retry-after",
                "",
            ),
            "remaining_tokens": headers.get(
                "x-ratelimit-remaining-tokens",
                "",
            ),
            "remaining_requests": headers.get(
                "x-ratelimit-remaining-requests",
                "",
            ),
            "reset_tokens": headers.get(
                "x-ratelimit-reset-tokens",
                "",
            ),
            "reset_requests": headers.get(
                "x-ratelimit-reset-requests",
                "",
            ),
        }

    # ========================================================
    # RATE LIMIT MESSAGE
    # ========================================================

    def _rate_limit_error(
        self,
        response: requests.Response,
        attempt: int,
    ) -> RuntimeError:

        details = self._get_rate_limit_details(
            response
        )

        retry_after = details["retry_after"]
        reset_tokens = details["reset_tokens"]
        reset_requests = details["reset_requests"]

        try:

            error_data = response.json()

            error_object = error_data.get(
                "error",
                {},
            )

            if isinstance(error_object, dict):

                message = str(
                    error_object.get(
                        "message",
                        "",
                    )
                ).strip()

            else:

                message = str(
                    error_object
                ).strip()

        except Exception:

            message = ""

        if retry_after:

            wait_text = (
                f"Groq asked the application to retry after "
                f"{retry_after} seconds."
            )

        elif reset_tokens:

            wait_text = (
                f"The token limit is expected to reset in "
                f"{reset_tokens}."
            )

        elif reset_requests:

            wait_text = (
                f"The request limit is expected to reset in "
                f"{reset_requests}."
            )

        else:

            wait_text = (
                "Groq has temporarily limited this request."
            )

        if attempt >= self.max_retries:

            extra = ""

            if message:
                extra = f" Groq says: {message}"

            return RuntimeError(
                "Groq rate limit is currently active. "
                f"{wait_text}"
                f"{extra} "
                "Please wait for the limit to reset and try "
                "generating the itinerary again."
            )

        return RuntimeError(
            "Temporary Groq rate limit detected. "
            f"{wait_text}"
        )

    # ========================================================
    # GROQ REQUEST
    # ========================================================

    def _call_groq(
        self,
        prompt: str,
    ) -> str:

        api_key = self._get_api_key()

        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are TrekTales, a grounded tourism "
                        "itinerary generation assistant. "
                        "The supplied tourism knowledge base is "
                        "the only source of tourism facts. "
                        "Never invent missing tourism information. "
                        "When information is unavailable, explicitly "
                        "say: Not available in the TrekTales tourism "
                        "knowledge base."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.2,
            "max_completion_tokens": 6000,
            "reasoning_effort": "medium",
            "include_reasoning": False,
        }

        last_response = None

        for attempt in range(
            self.max_retries + 1
        ):

            try:

                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=120,
                )

                last_response = response

            except requests.RequestException as exc:

                if attempt < self.max_retries:

                    time.sleep(2)
                    continue

                raise RuntimeError(
                    "Could not connect to the Groq API. "
                    "Please check your internet connection, "
                    "GROQ_BASE_URL, and try again."
                ) from exc

            # =================================================
            # SUCCESS
            # =================================================

            if response.status_code == 200:
                try:
                    data = response.json()
                except Exception as exc:
                    if attempt < self.max_retries:
                        time.sleep(1.5)
                        continue

                    raise RuntimeError(
                        "Groq returned an invalid JSON response."
                    ) from exc

                choices = data.get("choices", [])

                if not choices:
                    if attempt < self.max_retries:
                        time.sleep(1.5)
                        continue

                    raise RuntimeError(
                        "Groq returned no completion choices."
                    )

                first_choice = choices[0]

                if not isinstance(first_choice, dict):
                    if attempt < self.max_retries:
                        time.sleep(1.5)
                        continue

                    raise RuntimeError(
                        "Groq returned an invalid completion choice."
                    )

                message = first_choice.get("message", {})

                if not isinstance(message, dict):
                    if attempt < self.max_retries:
                        time.sleep(1.5)
                        continue

                    raise RuntimeError(
                        "Groq returned an invalid message object."
                    )

                content = message.get("content")

                if content is not None and str(content).strip():
                    return str(content).strip()

                if attempt < self.max_retries:
                    time.sleep(1.5)
                    continue

                finish_reason = str(
                    first_choice.get(
                        "finish_reason",
                        "unknown",
                    )
                )

                reasoning = message.get("reasoning")

                reasoning_note = ""

                if reasoning:
                    reasoning_note = (
                        " Groq returned reasoning content but no final "
                        "itinerary content."
                    )

                raise RuntimeError(
                    "Groq returned an empty itinerary. "
                    f"Finish reason: {finish_reason}."
                    f"{reasoning_note}"
                )

            # =================================================
            # AUTHENTICATION
            # =================================================

            if response.status_code in (401, 403):

                try:

                    error_data = response.json()

                    error_object = error_data.get(
                        "error",
                        {},
                    )

                    if isinstance(
                        error_object,
                        dict,
                    ):

                        message = str(
                            error_object.get(
                                "message",
                                "",
                            )
                        ).strip()

                    else:

                        message = str(
                            error_object
                        ).strip()

                except Exception:

                    message = ""

                if response.status_code == 403:

                    raise RuntimeError(
                        "Groq rejected access to the configured "
                        "model or API resource. "
                        f"Model: {self.model}. "
                        f"{message}"
                    )

                raise RuntimeError(
                    "Groq authentication failed. "
                    "Your GROQ_API_KEY is missing, invalid, "
                    "expired, or does not have access to the "
                    "configured Groq API. "
                    f"{message}"
                )

            # =================================================
            # MODEL ERROR
            # =================================================

            if response.status_code == 404:

                try:

                    error_data = response.json()

                    error_object = error_data.get(
                        "error",
                        {},
                    )

                    if isinstance(
                        error_object,
                        dict,
                    ):

                        message = str(
                            error_object.get(
                                "message",
                                "",
                            )
                        ).strip()

                    else:

                        message = str(
                            error_object
                        ).strip()

                except Exception:

                    message = ""

                raise RuntimeError(
                    "The configured Groq model is unavailable. "
                    f"Model: {self.model}. "
                    f"{message}"
                )

            # =================================================
            # RATE LIMIT
            # =================================================

            if response.status_code == 429:

                if attempt < self.max_retries:

                    details = (
                        self._get_rate_limit_details(
                            response
                        )
                    )

                    retry_after = details["retry_after"]

                    wait_seconds = 2.0

                    try:

                        if retry_after:

                            wait_seconds = float(
                                retry_after
                            )

                    except (
                        TypeError,
                        ValueError,
                    ):

                        wait_seconds = 2.0

                    wait_seconds = max(
                        1.0,
                        min(
                            wait_seconds,
                            15.0,
                        ),
                    )

                    time.sleep(wait_seconds)

                    continue

                raise self._rate_limit_error(
                    response,
                    attempt,
                )

            # =================================================
            # OTHER API ERRORS
            # =================================================

            if response.status_code >= 400:

                try:

                    error_data = response.json()

                    error_object = error_data.get(
                        "error",
                        {},
                    )

                    if isinstance(
                        error_object,
                        dict,
                    ):

                        message = str(
                            error_object.get(
                                "message",
                                "",
                            )
                        ).strip()

                    else:

                        message = str(
                            error_object
                        ).strip()

                except Exception:

                    message = response.text[:500]

                raise RuntimeError(
                    f"Groq API request failed "
                    f"(HTTP {response.status_code}). "
                    f"{message}"
                )

        # ========================================================
        # SAFETY CHECK
        # ========================================================

        if last_response is None:

            raise RuntimeError(
                "No response was received from Groq."
            )

        # ========================================================
        # RESPONSE JSON FALLBACK
        # ========================================================

        try:

            data = last_response.json()

        except Exception as exc:

            raise RuntimeError(
                "Groq returned an invalid response."
            ) from exc

        choices = data.get("choices", [])

        if not choices:

            raise RuntimeError(
                "Groq returned no completion choices."
            )

        first_choice = choices[0]

        if not isinstance(first_choice, dict):

            raise RuntimeError(
                "Groq returned an invalid completion choice."
            )

        message = first_choice.get(
            "message",
            {},
        )

        if not isinstance(message, dict):

            raise RuntimeError(
                "Groq returned an invalid message object."
            )

        content = message.get("content")

        if content is None:

            finish_reason = str(
                first_choice.get(
                    "finish_reason",
                    "unknown",
                )
            )

            raise RuntimeError(
                "Groq returned no itinerary content. "
                f"Finish reason: {finish_reason}."
            )

        content = str(content).strip()

        if not content:

            finish_reason = str(
                first_choice.get(
                    "finish_reason",
                    "unknown",
                )
            )

            raise RuntimeError(
                "Groq returned an empty itinerary. "
                f"Finish reason: {finish_reason}."
            )

        return content

    # ========================================================
    # MAIN RUN
    # ========================================================

    def run(
        self,
        destination: str,
        starting_location: str,
        days: int,
        budget: str,
        travelers: int,
        travel_style: str,
        language: str,
        interests: list[str],
        evidence: list[Any],
    ) -> str:

        try:
            days = int(days)

        except Exception:
            days = 1

        days = max(
            1,
            min(
                days,
                3,
            ),
        )

        try:
            travelers = int(travelers)

        except Exception:
            travelers = 1

        travelers = max(
            1,
            travelers,
        )

        prompt = self._build_prompt(
            destination=destination,
            starting_location=starting_location,
            days=days,
            budget=budget,
            travelers=travelers,
            travel_style=travel_style,
            language=language,
            interests=interests,
            evidence=evidence,
        )

        return self._call_groq(prompt)

    # ========================================================
    # COMPATIBILITY METHODS
    # ========================================================

    def generate(self, **kwargs):
        return self.run(**kwargs)

    def plan(self, **kwargs):
        return self.run(**kwargs)


__all__ = ["TrekTalesCrew"]
