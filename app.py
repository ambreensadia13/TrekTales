from __future__ import annotations

import time
from typing import Any

import requests
import streamlit as st


class TrekTalesCrew:
    """
    TrekTales grounded itinerary generation engine.

    This class uses Groq's OpenAI-compatible API.

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

        self.max_retries = 2

        try:

            self.max_tokens = int(
                self._get_secret(
                    "GROQ_MAX_TOKENS",
                    "4000",
                )
            )

        except Exception:

            self.max_tokens = 4000


        # Prevent unreasonable values.
        self.max_tokens = max(
            2500,
            min(
                self.max_tokens,
                5000,
            ),
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
                "Add a valid Groq API key in Streamlit Cloud → "
                "Settings → Secrets."
            )

        if not key.startswith("gsk_"):

            raise RuntimeError(
                "GROQ_API_KEY does not appear to be a valid "
                "Groq API key."
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
        Convert FAISS retrieval results into a clear evidence
        block for the language model.
        """

        if not evidence:

            return (
                "NO TOURISM KNOWLEDGE-BASE EVIDENCE WAS RETRIEVED."
            )

        blocks = []

        for index, item in enumerate(
            evidence,
            start=1,
        ):

            if isinstance(
                item,
                dict,
            ):

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


            text = str(
                text
            ).strip()

            if not text:
                continue


            source_text = str(
                source
            ).strip()

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


            if page and str(page).lower() != "n/a":

                location = (
                    f"{source_text} | Page {page}"
                )

            else:

                location = (
                    source_text
                    or "Knowledge Base"
                )


            blocks.append(
                f"""
[KNOWLEDGE ITEM {index}]

SOURCE:
{location}

CONTENT:
{text}
""".strip()
            )


        if not blocks:

            return (
                "NO USABLE TOURISM KNOWLEDGE-BASE "
                "EVIDENCE WAS RETRIEVED."
            )


        return "\n\n".join(
            blocks
        )


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
You are the TrekTales AI itinerary generation engine.

Create a polished, detailed, personalized travel itinerary.

The final answer must look like a professional travel-planning
document, not like a short chatbot answer.

============================================================
TRIP INFORMATION
============================================================

Destination:
{destination}

Starting location:
{starting_location}

Number of days:
{days}

Number of travelers:
{travelers}

Budget:
{budget}

Travel style:
{travel_style}

Interests:
{interests_text}

Language:
{language}

============================================================
MOST IMPORTANT RULE — KNOWLEDGE GROUNDING
============================================================

The tourism knowledge-base evidence at the END of this prompt
is the ONLY source of tourism facts.

You MUST NOT use outside tourism knowledge.

You MUST NOT invent missing information.

If the knowledge base does not contain a fact, write:

"Not available in the TrekTales tourism knowledge base."

============================================================
NEVER INVENT THESE
============================================================

Never invent:

- attractions
- parks
- restaurants
- hotels
- food places
- activities
- entry fees
- ticket prices
- food prices
- taxi fares
- transport fares
- distances
- travel times
- routes
- addresses
- opening hours
- closing hours
- phone numbers
- contact information
- availability
- ratings
- reviews
- historical facts
- weather
- road conditions
- safety conditions
- local rules
- events
- schedules

Do not estimate missing tourism information.

Do not turn a general assumption into a tourism fact.

Do not invent a source.

Do not invent a filename.

Do not invent a page number.

============================================================
IMPORTANT RULE ABOUT TIMES
============================================================

The example style uses times such as:

07:30 – 08:30
08:30 – 11:00

You may ONLY use exact time blocks when the supplied knowledge
base actually supports those timings.

If the knowledge base does NOT contain exact times:

DO NOT invent them.

Instead use a heading such as:

### 🌅 Morning — Suggested Order

or:

### 🕐 Suggested Timing

Then clearly state that exact timing is not available.

============================================================
IMPORTANT RULE ABOUT TRANSPORT
============================================================

For transport:

Only mention a transport type, route, distance, duration,
or fare if it is explicitly supported by the evidence.

If the evidence says a taxi has a base fare but does not
provide the distance-based fare, preserve that distinction.

For example:

- Taxi base fare: Rs. 300
- Distance-based fare: Not available in the TrekTales
  tourism knowledge base

Do NOT calculate the final taxi cost yourself.

============================================================
IMPORTANT RULE ABOUT BUDGET
============================================================

You may create a budget table.

However:

ONLY include costs supported by the evidence.

You may calculate a subtotal ONLY when every value needed
for that subtotal is explicitly supported.

If an important cost is missing:

"Cannot be fully calculated from the knowledge base."

Never create an estimated total using an unsupported price.

============================================================
IMPORTANT RULE ABOUT PERSONALIZATION
============================================================

You MAY personalize the organization using the user's:

- destination
- starting location
- number of travelers
- budget
- travel style
- interests

For example, if the user selects:

Nature
Photography
Local Culture

you may organize supported attractions around those interests.

However, you MUST NOT invent tourism facts to satisfy an interest.

============================================================
OUTPUT FORMAT
============================================================

Create the final answer in clean Markdown.

DO NOT output HTML.

DO NOT output code fences.

DO NOT explain your internal reasoning.

DO NOT mention that you are an AI model.

Start exactly with:

# 🌿 Personalized {destination} Adventure Itinerary

Then immediately provide a compact trip summary:

### 📍 {destination} · {days} Day(s) · {travelers} Travelers

**Travel style:** [selected travel style]

**Focus:** [selected interests]

**Budget:** **{budget}**

Then:

---

## 🗺️ Trip Overview

Write a useful personalized overview.

Mention the types of supported places/activities that the
retrieved evidence actually contains.

Do not invent any location.

Explain that missing prices, travel times or services are
explicitly marked unavailable rather than guessed.

============================================================
DAY-BY-DAY ITINERARY
============================================================

Create EXACTLY {days} day section(s).

For one day:

# ☀️ Your Day in {destination}

For multiple days:

# ☀️ Day 1 — [supported theme]

# ☀️ Day 2 — [supported theme]

etc.

Never create more days than requested.

Never silently remove a requested day.

============================================================
ACTIVITY FORMAT
============================================================

For each supported stop use a rich structure such as:

### [Timing or Morning/Afternoon/Evening] | [emoji] [Place]

**Focus:** [supported focus]

Write a useful description based only on evidence.

Then:

**Suggested experience:**

- supported activity
- supported activity
- supported activity

Then, when available:

**Entry:** **[verified amount]**

📚 **Source:** `[actual source]`

If information is missing:

**Entry:** Not available in the TrekTales tourism knowledge base.

Do not create a fake price.

============================================================
TRANSPORT SECTIONS
============================================================

When transport is supported by the evidence, provide:

### 🚕 Journey / Transport

**Transport:** [supported transport]

**Starting point:** {starting_location}

**Destination:** {destination}

Then list only supported cost/distance/time information.

If unavailable:

> ⚠️ The knowledge base does not provide the required
> transport information, so the final cost or duration
> cannot be reliably calculated.

============================================================
LUNCH / FOOD
============================================================

If the evidence contains a specific food location:

describe it using only supported information.

If no restaurant is present:

### 🍽️ Lunch Break

Explain that the knowledge base does not contain a verified
restaurant recommendation.

Do NOT invent a restaurant.

Do NOT invent a meal price.

============================================================
BUDGET
============================================================

After all days:

# 💰 Estimated Budget

Create:

### Per Person

| Expense | Estimated Cost |
| --- | --- |
| supported expense | supported cost |
| supported expense | supported cost |
| **Known subtotal** | **supported subtotal** |

Only calculate totals that are mathematically supported.

Then:

### 🎯 Your Budget

Show the user's selected budget.

Explain whether the complete trip can or cannot be calculated
from the available evidence.

If a major cost is missing, clearly identify it.

============================================================
PHOTOGRAPHY
============================================================

Then:

# 📸 Photography Highlights

Only include locations supported by the evidence.

For each supported place:

### 🌳 [Place]

**Best for:** [only if supported or a clearly general
organization based on the user's photography interest]

Do not invent special viewpoints or photo spots.

============================================================
WHAT TO CARRY
============================================================

Then:

# 🎒 What to Carry

You may provide general travel-preparation suggestions such as:

- fully charged phone/camera
- power bank
- comfortable walking shoes
- drinking water
- small cash denominations
- camera accessories

These are general preparation suggestions.

Do NOT claim that weather, terrain, facilities or local conditions
require an item unless the evidence supports that claim.

============================================================
IMPORTANT INFORMATION
============================================================

Then:

# ⚠️ Important Information

Explicitly identify important missing information.

For example:

- exact transport distance
- exact taxi total
- verified restaurant
- meal price
- operating hours
- exact travel duration

ONLY list missing information that is actually missing.

Do not claim something is missing if it appears in the evidence.

============================================================
KNOWLEDGE SOURCES
============================================================

Then:

# 📚 Knowledge-Base Sources

List ONLY sources that actually appear in the evidence.

Use:

- `filename`

If page information is available in the evidence, it may be
included, but never invent a page.

============================================================
FINAL RECOMMENDATION
============================================================

Finish with:

## 🌿 TrekTales Recommendation

Provide a concise best sequence.

Only include places and activities supported by the evidence.

For example, the structure may be:

**Best sequence:**

🚕 Starting point → 🌳 supported place →
🏛️ supported place → 🍽️ lunch →
🌿 supported place → 🚕 return

Do NOT invent a route if the evidence does not support it.

============================================================
SOURCE INTEGRITY
============================================================

Every tourism claim must be traceable to the supplied evidence.

Do not create fake citations.

Do not create fake sources.

Do not cite information from outside the knowledge base.

============================================================
FINAL CHECK
============================================================

Before answering, internally verify:

1. Exactly {days} day(s) are present.
2. Destination is {destination}.
3. Starting location is {starting_location}.
4. Traveler count is {travelers}.
5. Budget is {budget}.
6. Travel style is {travel_style}.
7. Interests are {interests_text}.
8. No tourism fact was invented.
9. No restaurant was invented.
10. No attraction was invented.
11. No price was invented.
12. No taxi fare was invented.
13. No distance was invented.
14. No travel time was invented.
15. No opening hours were invented.
16. No fake source was invented.
17. Missing information is explicitly marked.
18. Markdown is clean.
19. No HTML exists.
20. No code fences exist.

============================================================
TOURISM KNOWLEDGE-BASE EVIDENCE
============================================================

{evidence_text}

============================================================
END OF EVIDENCE
============================================================

Now produce ONLY the final polished TrekTales itinerary.
"""


    # ========================================================
    # RATE LIMIT DETAILS
    # ========================================================

    @staticmethod
    def _rate_limit_details(
        response: requests.Response,
    ) -> dict:

        headers = response.headers

        return {
            "retry_after": headers.get(
                "retry-after",
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
                        "You are the TrekTales grounded "
                        "travel itinerary engine. "
                        "Use ONLY the tourism knowledge "
                        "base supplied in the user prompt. "
                        "Never invent tourism facts. "
                        "Missing facts must be explicitly "
                        "marked unavailable."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],

            "temperature": 0.2,

            "max_tokens": self.max_tokens,

            "reasoning_effort": "medium",
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
                    "Please check your GROQ_BASE_URL and "
                    "internet connection."
                ) from exc


            # ------------------------------------------------
            # SUCCESS
            # ------------------------------------------------

            if response.status_code == 200:
                break


            # ------------------------------------------------
            # AUTH
            # ------------------------------------------------

            if response.status_code in (
                401,
                403,
            ):

                try:

                    data = response.json()

                    error = data.get(
                        "error",
                        {},
                    )

                    if isinstance(
                        error,
                        dict,
                    ):

                        message = str(
                            error.get(
                                "message",
                                "",
                            )
                        )

                    else:

                        message = str(error)

                except Exception:

                    message = ""


                raise RuntimeError(
                    "Groq authentication/access failed. "
                    f"Model: {self.model}. "
                    f"{message}"
                )


            # ------------------------------------------------
            # MODEL NOT FOUND
            # ------------------------------------------------

            if response.status_code == 404:

                try:

                    data = response.json()

                    error = data.get(
                        "error",
                        {},
                    )

                    if isinstance(
                        error,
                        dict,
                    ):

                        message = str(
                            error.get(
                                "message",
                                "",
                            )
                        )

                    else:

                        message = str(error)

                except Exception:

                    message = ""


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
                        self._rate_limit_details(
                            response
                        )
                    )

                    retry_after = (
                        details["retry_after"]
                    )

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

                    time.sleep(
                        wait_seconds
                    )

                    continue


                raise RuntimeError(
                    "Groq rate limit is currently active. "
                    "Please wait for the rate limit to reset "
                    "and try generating the itinerary again."
                )


            # ------------------------------------------------
            # OTHER ERRORS
            # ------------------------------------------------

            if response.status_code >= 400:

                try:

                    data = response.json()

                    error = data.get(
                        "error",
                        {},
                    )

                    if isinstance(
                        error,
                        dict,
                    ):

                        message = str(
                            error.get(
                                "message",
                                "",
                            )
                        )

                    else:

                        message = str(error)

                except Exception:

                    message = response.text[:500]


                raise RuntimeError(
                    f"Groq API request failed "
                    f"(HTTP {response.status_code}). "
                    f"{message}"
                )


        if last_response is None:

            raise RuntimeError(
                "No response was received from Groq."
            )


        # ====================================================
        # JSON
        # ====================================================

        try:

            data = last_response.json()

        except Exception as exc:

            raise RuntimeError(
                "Groq returned an invalid response."
            ) from exc


        # ====================================================
        # CONTENT
        # ====================================================

        try:

            content = (
                data[
                    "choices"
                ][
                    0
                ][
                    "message"
                ][
                    "content"
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


        return str(
            content
        ).strip()


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
        **kwargs,
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

            travelers = int(
                travelers
            )

        except Exception:

            travelers = 1


        travelers = max(
            1,
            travelers,
        )


        if interests is None:
            interests = []


        if evidence is None:
            evidence = []


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


        return self._call_groq(
            prompt
        )


    # ========================================================
    # COMPATIBILITY METHODS
    # ========================================================

    def generate(
        self,
        **kwargs,
    ):

        return self.run(
            **kwargs
        )


    def plan(
        self,
        **kwargs,
    ):

        return self.run(
            **kwargs
        )


__all__ = [
    "TrekTalesCrew"
]
