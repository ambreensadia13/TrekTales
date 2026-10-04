from future import annotations

import time
from typing import Any

import requests
import streamlit as st

class TrekTalesCrew:
"""
Grounded TrekTales itinerary generation engine.

Tourism facts must come only from the evidence retrieved
from the TrekTales tourism knowledge base.
"""

def __init__(self) -> None:
    self.base_url = self._get_secret(
        "GROQ_BASE_URL",
        "https://api.groq.com/openai/v1",
    ).rstrip("/")

    self.model = self._get_secret(
        "GROQ_MODEL",
        "openai/gpt-oss-120b",
    )

    self.max_retries = 2

    try:
        self.max_tokens = int(
            self._get_secret(
                "GROQ_MAX_TOKENS",
                "4000",
            )
        )
    except (TypeError, ValueError):
        self.max_tokens = 4000

    self.max_tokens = max(
        2500,
        min(self.max_tokens, 5000),
    )

# ========================================================
# SECRET
# ========================================================

@staticmethod
def _get_secret(
    name: str,
    default: str = "",
) -> str:
    try:
        value = st.secrets.get(name, default)

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
            "Add your Groq API key in Streamlit Cloud → "
            "Settings → Secrets."
        )

    if not key.startswith("gsk_"):
        raise RuntimeError(
            "GROQ_API_KEY does not appear to be a valid "
            "Groq API key."
        )

    return key

# ========================================================
# SOURCE CLEANING
# ========================================================

@staticmethod
def _clean_source(source: Any) -> str:
    if not source:
        return ""

    cleaned = str(source).replace("\\", "/").strip()

    cleaned = cleaned.split("/")[-1]

    return cleaned

# ========================================================
# EVIDENCE FORMATTER
# ========================================================

@classmethod
def _format_evidence(
    cls,
    evidence: list[Any],
) -> str:

    if not evidence:
        return (
            "NO TOURISM KNOWLEDGE-BASE EVIDENCE WAS RETRIEVED."
        )

    blocks: list[str] = []

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

        source = cls._clean_source(source)

        if page and str(page).lower() != "n/a":
            source_label = (
                f"{source} | Page {page}"
            )
        else:
            source_label = source

        blocks.append(
            (
                f"============================================================\n"
                f"KNOWLEDGE ITEM {index}\n"
                f"============================================================\n\n"
                f"SOURCE:\n"
                f"{source_label or 'Knowledge Base'}\n\n"
                f"CONTENT:\n"
                f"{text}"
            )
        )

    if not blocks:
        return (
            "NO USABLE TOURISM KNOWLEDGE-BASE "
            "EVIDENCE WAS RETRIEVED."
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

You are TrekTales, a professional grounded travel itinerary generator.

Create a polished, detailed and personalized travel itinerary.

The final answer must look like a professional travel-planning
document rather than a short chatbot response.

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

Response language:
{language}

The TOURISM KNOWLEDGE-BASE EVIDENCE at the bottom of this prompt
is the ONLY source of tourism facts.

Do NOT use outside tourism knowledge.

Do NOT rely on your general knowledge.

Do NOT invent missing information.

If a tourism fact is not present in the supplied evidence,
explicitly say:

"Not available in the TrekTales tourism knowledge base."

Never guess.

Never estimate an unsupported tourism value.

Never invent:

attractions
parks
restaurants
hotels
food places
activities
entry fees
ticket prices
food prices
taxi fares
transport fares
distances
travel times
routes
addresses
opening hours
closing hours
phone numbers
contact information
availability
ratings
reviews
historical facts
weather
road conditions
safety conditions
local rules
events
schedules
facilities

Do not create fake sources.

Do not create fake filenames.

Do not create fake page numbers.

Use exact time ranges ONLY when the evidence explicitly supports
those times.

Do NOT invent times such as:

07:30 – 08:30
08:30 – 11:00
11:15 – 13:15

when the evidence does not contain them.

If exact timing is unavailable, use:

🌅 Morning — Suggested Order

or:

🕐 Suggested Timing

and clearly state that exact timing is not available.

Only mention transport information explicitly supported by evidence.

If the evidence contains a taxi base fare but not a distance-based
fare, preserve that distinction.

For example:

Taxi base fare: Rs. 300
Distance-based fare: Not available in the TrekTales tourism
knowledge base

Never calculate an unsupported final taxi fare.

Only include costs supported by the knowledge base.

A subtotal may be calculated only when every value required for
that subtotal is explicitly available.

If a major cost is missing, state:

"Cannot be fully calculated from the TrekTales knowledge base."

Never create a total from guessed prices.

Use the user's:

destination
starting location
traveler count
budget
travel style
interests

to organize the itinerary.

For example, if the user selected:

Nature
Photography
Local Culture

prioritize supported evidence that relates to those interests.

However, never invent a place or activity merely to satisfy
an interest.

Return ONLY the final polished itinerary.

Use clean Markdown.

Do NOT output:

HTML
code fences
JSON
XML
internal reasoning
explanations about your instructions
comments about being an AI

Start exactly with:

🌿 Personalized {destination} Adventure Itinerary
📍 {destination} · {days} Day(s) · {travelers} Travelers

Travel style: {travel_style}

Focus: {interests_text}

Budget: {budget}

🗺️ Trip Overview

Write a useful personalized overview based on the supplied
knowledge-base evidence.

Mention only supported places, activities and experiences.

Explain that missing information is explicitly marked rather
than guessed.

Create EXACTLY {days} day section(s).

For one day:

☀️ Your Day in {destination}

For multiple days:

☀️ Day 1 — [supported theme]
☀️ Day 2 — [supported theme]
☀️ Day 3 — [supported theme]

Never create more days than requested.

Never silently remove a requested day.

If evidence is insufficient for a requested day, say so rather
than inventing activities.

For each supported stop, use a rich structure.

If timing is supported:

HH – HH | 🌳 [Place]

If timing is NOT supported:

🌳 [Place]

Then:

Focus: [supported focus]

Write a useful description using ONLY the supplied evidence.

Then:

Suggested experience:

supported activity
supported activity
supported activity

Only include activities supported by the evidence.

When an entry price exists:

Entry: [verified amount]

📚 Source: [actual source]

When an entry price does not exist:

Entry: Not available in the TrekTales tourism knowledge base.

When transport is supported:

🚕 Journey / Transport

Transport: [supported transport]

Starting point: {starting_location}

Destination: {destination}

Include only supported:

fare
distance
duration
route

If important information is unavailable, state:

⚠️ The knowledge base does not provide the required transport
information, so the final cost or duration cannot be reliably
calculated.

If the evidence contains a verified food location, include it.

If food prices are present, include them.

If no restaurant is supported, do NOT invent one.

Instead write:

The TrekTales knowledge base does not contain a verified
restaurant recommendation for this stop.

If the food price is missing:

Food cost: Not available in the TrekTales tourism
knowledge base.

After all itinerary days:

💰 Estimated Budget

Create:

Per Person
Expense	Estimated Cost
supported expense	supported cost
supported expense	supported cost
Known subtotal	supported subtotal

Only calculate mathematically supported totals.

Then:

🎯 Your Budget

{budget}

Explain which costs are verified and which remain unavailable.

If the complete trip cannot be calculated:

Total trip cost: Cannot be fully calculated from the
TrekTales knowledge base.

📸 Photography Highlights

Only include supported places.

For each suitable supported location:

🌳 [Place]

Best for: [only supported information]

Do not invent viewpoints, scenery, photo spots or facilities.

🎒 What to Carry

General preparation recommendations are allowed.

For example:

📱 Fully charged phone/camera
🔋 Power bank
👟 Comfortable walking shoes
💧 Drinking water
💵 Small cash denominations
📸 Camera accessories if useful

These are general recommendations, not destination-specific facts.

Do not claim that weather or local conditions require something
unless the evidence supports that claim.

⚠️ Important Information

List only relevant information that is genuinely missing.

Examples:

Exact transport distance
Exact taxi total
Verified restaurant
Meal price
Operating hours
Exact travel duration

Do not claim information is missing if it exists in the evidence.

📚 Knowledge-Base Sources

List ONLY sources appearing in the supplied evidence.

Use filename only.

Example:

Pindi_Places.pdf
TR-003 – Taxi
PL-002 – Ayub National Park

Never invent a filename.

🌿 TrekTales Recommendation

Provide a concise best sequence using ONLY supported locations
and activities.

For example:

Best sequence:

🚕 Starting point → 🌳 supported place → 🏛️ supported place
→ 🍽️ supported food stop → 🚕 return

Do not invent unsupported routes.

Before producing the final response, verify internally:

Exactly {days} day(s) are present.
Destination is {destination}.
Starting location is {starting_location}.
Traveler count is {travelers}.
Budget is {budget}.
Travel style is {travel_style}.
Interests are {interests_text}.
Every tourism fact comes from the evidence.
No attraction was invented.
No restaurant was invented.
No hotel was invented.
No price was invented.
No distance was invented.
No travel time was invented.
No taxi fare was invented.
No opening hours were invented.
No fake source was invented.
Missing information is clearly marked.
No HTML exists.
No code fences exist.
The response is clean Markdown.
The itinerary is detailed enough to be useful.

{evidence_text}

Now produce ONLY the final polished TrekTales itinerary.
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
# ERROR MESSAGE
# ========================================================

@staticmethod
def _extract_error_message(
    response: requests.Response,
) -> str:

    try:
        data = response.json()

        error = data.get(
            "error",
            {},
        )

        if isinstance(error, dict):
            return str(
                error.get(
                    "message",
                    "",
                )
            ).strip()

        return str(error).strip()

    except Exception:
        return response.text[:500].strip()

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
                    "You are TrekTales, a grounded travel "
                    "itinerary generator. Use ONLY the tourism "
                    "knowledge-base evidence supplied in the "
                    "user message. Never invent tourism facts. "
                    "Missing facts must be explicitly marked "
                    "as unavailable in the TrekTales tourism "
                    "knowledge base. Return clean Markdown only."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.2,
        "max_tokens": self.max_tokens,
    }

    last_response: requests.Response | None = None

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
                "Please check GROQ_BASE_URL, GROQ_API_KEY "
                "and the internet connection."
            ) from exc

        # ------------------------------------------------
        # SUCCESS
        # ------------------------------------------------

        if response.status_code == 200:
            break

        # ------------------------------------------------
        # AUTHENTICATION
        # ------------------------------------------------

        if response.status_code == 401:
            message = self._extract_error_message(
                response
            )

            raise RuntimeError(
                "Groq authentication failed. "
                "Check GROQ_API_KEY."
                + (
                    f" Groq says: {message}"
                    if message
                    else ""
                )
            )

        # ------------------------------------------------
        # FORBIDDEN
        # ------------------------------------------------

        if response.status_code == 403:
            message = self._extract_error_message(
                response
            )

            raise RuntimeError(
                "Groq rejected access to the configured "
                f"model '{self.model}'."
                + (
                    f" Groq says: {message}"
                    if message
                    else ""
                )
            )

        # ------------------------------------------------
        # MODEL NOT FOUND
        # ------------------------------------------------

        if response.status_code == 404:
            message = self._extract_error_message(
                response
            )

            raise RuntimeError(
                "The configured Groq model is unavailable. "
                f"Model: {self.model}."
                + (
                    f" Groq says: {message}"
                    if message
                    else ""
                )
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
                    details.get(
                        "retry_after",
                        "",
                    )
                )

                try:
                    wait_seconds = (
                        float(retry_after)
                        if retry_after
                        else 3.0
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
                        15.0,
                    ),
                )

                time.sleep(
                    wait_seconds
                )

                continue

            message = self._extract_error_message(
                response
            )

            raise RuntimeError(
                "Groq rate limit is currently active. "
                "Please wait for the limit to reset and "
                "try generating the itinerary again."
                + (
                    f" Groq says: {message}"
                    if message
                    else ""
                )
            )

        # ------------------------------------------------
        # OTHER API ERRORS
        # ------------------------------------------------

        if response.status_code >= 400:

            message = self._extract_error_message(
                response
            )

            raise RuntimeError(
                f"Groq API request failed "
                f"(HTTP {response.status_code}). "
                f"{message}"
            )

    if last_response is None:
        raise RuntimeError(
            "No response was received from Groq."
        )

    if last_response.status_code != 200:
        raise RuntimeError(
            "Groq did not return a successful response."
        )

    # ====================================================
    # JSON
    # ====================================================

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
            data["choices"][0]["message"]["content"]
        )

    except (
        KeyError,
        IndexError,
        TypeError,
    ) as exc:

        raise RuntimeError(
            "Groq returned no itinerary content."
        ) from exc

    if not content:
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
    days: int = 1,
    budget: str = "",
    travelers: int = 1,
    travel_style: str = "Mixed",
    language: str = "English",
    interests: list[str] | None = None,
    evidence: list[Any] | None = None,
    **kwargs: Any,
) -> str:

    try:
        days = int(days)
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

    try:
        travelers = int(travelers)
    except (
        TypeError,
        ValueError,
    ):
        travelers = 1

    travelers = max(
        1,
        travelers,
    )

    interests = (
        interests
        if interests is not None
        else []
    )

    evidence = (
        evidence
        if evidence is not None
        else []
    )

    prompt = self._build_prompt(
        destination=str(destination).strip(),
        starting_location=str(
            starting_location
        ).strip(),
        days=days,
        budget=str(budget).strip(),
        travelers=travelers,
        travel_style=str(
            travel_style
        ).strip(),
        language=str(
            language
        ).strip(),
        interests=interests,
        evidence=evidence,
    )

    return self._call_groq(
        prompt
    )

# ========================================================
# COMPATIBILITY METHODS
# ========================================================

def generate(
    self,
    **kwargs: Any,
) -> str:
    return self.run(
        **kwargs
    )

def plan(
    self,
    **kwargs: Any,
) -> str:
    return self.run(
        **kwargs
    )

all = [
"TrekTalesCrew",
]
