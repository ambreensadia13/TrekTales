from __future__ import annotations

import time
from typing import Any

import requests
import streamlit as st


class TrekTalesCrew:
    """
    TrekTales grounded itinerary-generation engine.

    Uses Groq's OpenAI-compatible Chat Completions API.

    IMPORTANT:
    Tourism facts must come only from the evidence retrieved
    by the FAISS tourism knowledge base.
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

        # Deliberately small retry count.
        # Repeated retries can make Groq rate limits worse.
        self.max_retries = 1

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
                "GROQ_API_KEY is missing from Streamlit "
                "Secrets. Add your valid Groq API key."
            )

        if not key.startswith("gsk_"):

            raise RuntimeError(
                "GROQ_API_KEY does not appear to be a valid "
                "Groq API key. Check Streamlit Secrets."
            )

        return key

    # ========================================================
    # EVIDENCE FORMATTER
    # ========================================================

    @staticmethod
    def _format_evidence(
        evidence: list[Any],
    ) -> str:

        """
        Convert FAISS evidence into a strict knowledge block.

        No tourism facts are added here.
        """

        if not evidence:

            return (
                "NO USABLE TOURISM KNOWLEDGE-BASE EVIDENCE "
                "WAS RETRIEVED."
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

                if not isinstance(
                    metadata,
                    dict,
                ):
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

                source_text = source_text.split(
                    "/"
                )[-1]

                source_text = source_text.replace(
                    ".html",
                    "",
                )

            if (
                page
                and str(page).lower() != "n/a"
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
                "NO USABLE TOURISM KNOWLEDGE-BASE EVIDENCE "
                "WAS RETRIEVED."
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
You are TrekTales, a grounded tourism itinerary
generation engine.

Your job is to create a polished, personalized,
easy-to-read travel itinerary.

============================================================
MOST IMPORTANT RULE
============================================================

The TOURISM KNOWLEDGE-BASE EVIDENCE at the bottom of this
prompt is the ONLY source of tourism facts.

You MUST NOT use your own world knowledge.

You MUST NOT browse the internet.

You MUST NOT guess.

You MUST NOT fill missing tourism information from memory.

If a tourism fact is not supported by the supplied evidence,
write exactly:

Not available in the TrekTales tourism knowledge base.

============================================================
TRIP DETAILS
============================================================

Destination:
{destination}

Starting location:
{starting_location}

Duration:
{days} day(s)

Travelers:
{travelers}

Budget:
{budget}

Travel style:
{travel_style}

Interests:
{interests_text}

Requested language:
{language}

============================================================
ANTI-HALLUCINATION RULES
============================================================

Never invent or assume:

- attractions
- landmarks
- restaurants
- cafes
- hotels
- activities
- ticket prices
- entry fees
- food prices
- transportation fares
- taxi fares
- distances
- travel times
- routes
- opening hours
- closing hours
- addresses
- telephone numbers
- contact information
- ratings
- reviews
- availability
- historical facts
- weather
- safety conditions
- local regulations
- events
- schedules
- parking information
- viewpoints
- photography locations

Never turn a generic statement into a specific tourism fact.

Never infer a price.

Never infer a distance.

Never infer a travel time.

Never infer that two places are near each other.

Never invent a restaurant simply to make the itinerary
more interesting.

Never invent a hotel.

Never invent a landmark.

Never invent a source filename.

Never create fake citations.

If information is absent, explicitly state:

Not available in the TrekTales tourism knowledge base.

============================================================
PERSONALIZATION RULE
============================================================

You SHOULD personalize the structure using the user inputs.

For example:

- If the user selected Photography, emphasize supported
  photography-related places or activities.
- If the user selected Nature, emphasize supported natural
  locations or activities.
- If the user selected Culture, emphasize supported cultural
  information.
- If the user selected Adventure, emphasize supported
  adventure activities.

However:

Personalization MUST NOT create new facts.

If the knowledge base does not support the selected interest,
say that relevant information is unavailable.

============================================================
EXACT DAY RULE
============================================================

Generate EXACTLY {days} day(s).

Do not generate fewer days.

Do not generate more days.

Do not add a hidden extra day.

Every day must contain only activities supported by the
knowledge base.

If there is not enough evidence for a complete day, do NOT
invent activities.

Instead, clearly state:

Not enough tourism information is available in the TrekTales
tourism knowledge base to provide additional supported
activities for this day.

============================================================
OUTPUT FORMAT
============================================================

Make the itinerary visually attractive.

Use clean Markdown.

Do NOT use HTML.

Do NOT use code fences.

Do NOT output JSON.

Do NOT output XML.

Use emojis where appropriate.

Use short paragraphs.

Use bullet points.

Use bold labels.

============================================================
HEADER
============================================================

Start exactly in this style:

🌿 Personalized {destination} Adventure Itinerary

Then immediately provide:

📍 {destination} · {days} Day(s) · {travelers} Traveler(s)

Then include:

**Travel style:** {travel_style}

**Focus:** [only user-selected interests]

**Budget:** {budget}

============================================================
TRIP OVERVIEW
============================================================

Create:

### 📍 Trip Overview

Include:

- Destination
- Starting location
- Duration
- Travelers
- Travel style
- Interests
- Budget

Use the supplied user values.

Do not add unsupported tourism facts.

============================================================
DAY-BY-DAY ITINERARY
============================================================

Create exactly {days} day sections.

Use this format:

### ☀️ Day 1 — [supported theme]

Then:

**⏰ Suggested Schedule**

Only use actual times if the evidence provides times.

If times are unavailable, do NOT invent times.

You may instead organize the day as:

- Morning
- Afternoon
- Evening

but only attach activities supported by evidence.

For every recommended place/activity include:

**Place/Activity:** name

**Why it fits:** only when this connection is supported
by the supplied evidence and user preferences.

**Cost:** only if explicitly available.

**Practical information:** only if explicitly available.

For unsupported details write:

Not available in the TrekTales tourism knowledge base.

============================================================
TRANSPORT
============================================================

Include:

### 🚗 Travel & Transport

Only mention transportation information found in evidence.

Never estimate:

- distance
- travel duration
- taxi price
- fuel cost
- route
- fare

If unavailable:

Not available in the TrekTales tourism knowledge base.

============================================================
BUDGET
============================================================

Include:

### 💰 Budget Considerations

List only explicitly supported costs.

Do NOT invent a total.

Do NOT calculate unsupported costs.

Do NOT turn the user's selected budget range into an actual
trip cost.

If prices are missing:

Not available in the TrekTales tourism knowledge base.

============================================================
PHOTOGRAPHY
============================================================

Include:

### 📸 Photography Highlights

Mention only photography-related places or activities that
are supported by evidence.

Do not invent viewpoints.

Do not invent scenic spots.

Do not invent photo opportunities.

If unavailable:

Not available in the TrekTales tourism knowledge base.

============================================================
WHAT TO CARRY
============================================================

Include:

### 🎒 What to Carry

Keep this practical.

Do not claim something is required because of weather,
terrain, safety or local conditions unless the knowledge
base explicitly supports that claim.

General personal travel items may be suggested only when
they do not imply an unsupported tourism fact.

============================================================
IMPORTANT INFORMATION
============================================================

Include:

### ⚠️ Important Information

Only include tourism-specific warnings or rules when they
are supported by evidence.

Otherwise write:

Not available in the TrekTales tourism knowledge base.

============================================================
KNOWLEDGE SOURCES
============================================================

Finish with:

### 📚 Knowledge-Base Sources

List ONLY source filenames that appear in the supplied
knowledge evidence.

Use filenames only.

Never create a filename.

Never invent a citation.

============================================================
LANGUAGE
============================================================

The complete response must be written in:

{language}

If the requested language is Urdu, use Urdu script.

If the requested language is Roman Urdu, use Roman Urdu.

If the requested language is English, use English.

Do not mix languages unnecessarily.

============================================================
FINAL INTERNAL CHECK
============================================================

Before answering, verify:

1. Exactly {days} day sections exist.
2. Destination is {destination}.
3. Starting location is {starting_location}.
4. Travelers is {travelers}.
5. Budget is {budget}.
6. Travel style is {travel_style}.
7. Only supplied evidence is used for tourism facts.
8. No attraction was invented.
9. No restaurant was invented.
10. No hotel was invented.
11. No price was invented.
12. No distance was invented.
13. No travel time was invented.
14. No taxi fare was invented.
15. No opening hours were invented.
16. No fake source was invented.
17. No unsupported historical fact was invented.
18. Missing information is clearly marked.
19. No HTML is present.
20. No code fences are present.
21. No JSON is present.
22. The requested language is respected.

============================================================
TOURISM KNOWLEDGE-BASE EVIDENCE
============================================================

{evidence_text}

============================================================
END OF TOURISM KNOWLEDGE-BASE EVIDENCE
============================================================

Now generate the final TrekTales itinerary.
"""

    # ========================================================
    # RATE LIMIT DETAILS
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
    # RATE LIMIT ERROR
    # ========================================================

    def _rate_limit_error(
        self,
        response: requests.Response,
    ) -> RuntimeError:

        details = self._get_rate_limit_details(
            response
        )

        retry_after = details["retry_after"]
        reset_tokens = details["reset_tokens"]
        reset_requests = details["reset_requests"]

        message = ""

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
            pass

        if retry_after:

            wait_text = (
                f"Groq requested a retry after "
                f"{retry_after} seconds."
            )

        elif reset_tokens:

            wait_text = (
                f"Groq token limits may reset in "
                f"{reset_tokens}."
            )

        elif reset_requests:

            wait_text = (
                f"Groq request limits may reset in "
                f"{reset_requests}."
            )

        else:

            wait_text = (
                "Groq has temporarily rate-limited "
                "this request."
            )

        extra = ""

        if message:
            extra = f" Groq says: {message}"

        return RuntimeError(
            "Groq rate limit is currently active. "
            f"{wait_text}{extra} "
            "Please wait and try again."
        )

    # ========================================================
    # GROQ REQUEST
    # ========================================================

    def _call_groq(
        self,
        prompt: str,
    ) -> str:

        api_key = self._get_api_key()

        url = (
            f"{self.base_url}/chat/completions"
        )

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
                        "You are TrekTales, a grounded "
                        "tourism itinerary assistant. "
                        "The supplied tourism knowledge "
                        "base is the ONLY source of tourism "
                        "facts. Never invent tourism facts. "
                        "Never use outside knowledge. "
                        "If information is missing, say: "
                        "Not available in the TrekTales "
                        "tourism knowledge base."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.1,
            "max_tokens": 1800,
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
                    "Check your internet connection, "
                    "GROQ_BASE_URL and GROQ_API_KEY."
                ) from exc

            # ------------------------------------------------
            # SUCCESS
            # ------------------------------------------------

            if response.status_code == 200:
                break

            # ------------------------------------------------
            # AUTHENTICATION
            # ------------------------------------------------

            if response.status_code in (
                401,
                403,
            ):

                message = ""

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
                    pass

                if response.status_code == 403:

                    raise RuntimeError(
                        "Groq rejected access to the "
                        f"configured model: {self.model}. "
                        f"{message}"
                    )

                raise RuntimeError(
                    "Groq authentication failed. "
                    "Check GROQ_API_KEY. "
                    f"{message}"
                )

            # ------------------------------------------------
            # MODEL ERROR
            # ------------------------------------------------

            if response.status_code == 404:

                message = ""

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
                    pass

                raise RuntimeError(
                    "The configured Groq model is unavailable. "
                    f"Model: {self.model}. "
                    f"{message}"
                )

            # ------------------------------------------------
            # RATE LIMIT
            # ------------------------------------------------

            if response.status_code == 429:

                if attempt < self.max_retries:

                    details = (
                        self._get_rate_limit_details(
                            response
                        )
                    )

                    retry_after = (
                        details["retry_after"]
                    )

                    wait_seconds = 3.0

                    try:

                        if retry_after:
                            wait_seconds = float(
                                retry_after
                            )

                    except (
                        TypeError,
                        ValueError,
                    ):

                        wait_seconds = 3.0

                    wait_seconds = max(
                        1.0,
                        min(
                            wait_seconds,
                            10.0,
                        ),
                    )

                    time.sleep(
                        wait_seconds
                    )

                    continue

                raise self._rate_limit_error(
                    response
                )

            # ------------------------------------------------
            # OTHER API ERRORS
            # ------------------------------------------------

            if response.status_code >= 400:

                message = ""

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

        # ====================================================
        # RESPONSE SAFETY
        # ====================================================

        if last_response is None:

            raise RuntimeError(
                "No response was received from Groq."
            )

        try:

            data = last_response.json()

        except Exception as exc:

            raise RuntimeError(
                "Groq returned an invalid JSON response."
            ) from exc

        # ====================================================
        # CONTENT
        # ====================================================

        try:

            content = (
                data["choices"][0]
                ["message"]
                ["content"]
            )

        except (
            KeyError,
            IndexError,
            TypeError,
        ) as exc:

            raise RuntimeError(
                "Groq returned no itinerary content."
            ) from exc

        if not content or not str(content).strip():

            raise RuntimeError(
                "Groq returned an empty itinerary."
            )

        return str(content).strip()

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
            min(days, 3),
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

    def generate(
        self,
        **kwargs,
    ):

        return self.run(**kwargs)

    def plan(
        self,
        **kwargs,
    ):

        return self.run(**kwargs)


__all__ = ["TrekTalesCrew"]
