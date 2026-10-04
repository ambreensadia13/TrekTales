from __future__ import annotations

import time
from typing import Any

import requests
import streamlit as st


class TrekTalesCrew:
    """
    TrekTales grounded itinerary generator.

    The model may only use tourism facts contained in the
    retrieved FAISS evidence.
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
    def _get_secret(name: str, default: str = "") -> str:
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
        key = self._get_secret("GROQ_API_KEY", "")

        if not key:
            raise RuntimeError(
                "GROQ_API_KEY is missing from Streamlit Secrets."
            )

        if not key.startswith("gsk_"):
            raise RuntimeError(
                "GROQ_API_KEY does not appear to be a valid Groq API key."
            )

        return key

    # ========================================================
    # CLEAN SOURCE NAME
    # ========================================================

    @staticmethod
    def _clean_source(source: Any) -> str:
        if not source:
            return ""

        source = str(source).replace("\\", "/")
        source = source.split("/")[-1]

        return source.strip()

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

        blocks = []

        for index, item in enumerate(evidence, start=1):

            if isinstance(item, dict):

                metadata = item.get("metadata", {})

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

            if page not in ("", None, "N/A", "n/a"):
                source_label = f"{source} | Page {page}"
            else:
                source_label = source

            blocks.append(
                f"""
============================================================
KNOWLEDGE ITEM {index}
============================================================

SOURCE:
{source_label or "Unknown source"}

CONTENT:
{text}
""".strip()
            )

        if not blocks:
            return (
                "NO USABLE TOURISM KNOWLEDGE-BASE EVIDENCE WAS RETRIEVED."
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

        evidence_text = self._format_evidence(evidence)

        interests_text = (
            ", ".join(str(x) for x in interests)
            if interests
            else "No specific interests provided."
        )

        return f"""
You are TrekTales, a professional AI travel itinerary generator.

Your job is to create a polished, detailed and personalized
travel itinerary.

The itinerary must look like a professional travel-planning
document, not like a short chatbot answer.

============================================================
USER TRIP
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

Response language:
{language}

============================================================
MOST IMPORTANT RULE
============================================================

The TOURISM KNOWLEDGE-BASE EVIDENCE at the bottom of this prompt
is the ONLY source of tourism facts.

You MUST NOT use outside tourism knowledge.

You MUST NOT fill missing information with guesses.

This includes:

- attractions
- restaurants
- hotels
- transport
- taxi fares
- distances
- travel times
- entry fees
- food prices
- opening hours
- closing hours
- addresses
- phone numbers
- events
- schedules
- facilities
- availability
- ratings
- reviews
- historical claims
- weather claims
- safety claims
- local rules

If the evidence does not contain a required fact, write:

**Not available in the TrekTales tourism knowledge base.**

Do not make up an alternative value.

============================================================
PERSONALIZATION
============================================================

The itinerary must actually reflect:

Destination:
{destination}

Travel style:
{travel_style}

Interests:
{interests_text}

Budget:
{budget}

Travelers:
{travelers}

For example, if the evidence supports nature locations and the
user selected nature, prioritize those locations.

If photography is selected, organize supported photography-
relevant places into the photography section.

Do not invent photography features merely because photography
was selected.

============================================================
DAY COUNT
============================================================

Generate exactly {days} day(s).

If days = 1:
Generate only Day 1.

If days = 2:
Generate Day 1 and Day 2.

If days = 3:
Generate Day 1, Day 2 and Day 3.

Never silently reduce the number of requested days.

However, if the evidence is insufficient for a particular day,
do not invent activities.

Instead explain that the available knowledge base does not
contain enough verified information for that day.

============================================================
OUTPUT FORMAT
============================================================

The output must be clean Markdown.

Do NOT output HTML.

Do NOT output code fences.

Do NOT output JSON.

Do NOT output XML.

Do NOT add commentary before the itinerary.

Start immediately with:

# 🌿 Personalized {destination} Adventure Itinerary

Then create this structure.

============================================================
HEADER
============================================================

# 🌿 Personalized {destination} Adventure Itinerary

### 📍 {destination} · {days} Day(s) · {travelers} Travelers

**Travel style:** {travel_style}

**Focus:** [only interests supplied by the user]

**Budget:** {budget}

============================================================
TRIP OVERVIEW
============================================================

## 🗺️ Trip Overview

Write a short personalized paragraph explaining the trip.

Then use bullet points for the major supported experiences.

Every listed experience must be supported by the knowledge base.

If an important part of the requested trip cannot be supported,
say so clearly.

============================================================
DAY ITINERARY
============================================================

For every day use:

# ☀️ Day 1 — [descriptive theme]

For subsequent days:

# ☀️ Day 2 — [descriptive theme]

# ☀️ Day 3 — [descriptive theme]

Use descriptive themes only when supported by the evidence.

For each supported activity, use this format:

### HH:MM – HH:MM | [emoji] [Place / Activity]

**Focus:** [supported focus]

Describe what the traveler can do using ONLY evidence.

Then include useful supported information.

Example:

**Entry:** **Rs. 100 per person**

📚 **Source:** `filename.pdf`

If price is not present:

**Entry:** Not available in the TrekTales tourism knowledge base.

Do NOT manufacture times.

If the knowledge base does not contain actual times, do not invent
07:30, 08:30, 11:00 etc.

Instead use:

### [Time not available] | 🌳 [Place]

or simply:

### 🌳 [Place]

This is extremely important.

============================================================
TRANSPORT
============================================================

When transport information exists in the evidence, include it.

Example:

**Transport:** Taxi

**Known cost:** Rs. 300 base fare

📚 **Source:** `TR-003 – Taxi`

If distance or total fare is unavailable, explicitly say:

> ⚠️ The exact distance or total fare is not available in the
> TrekTales tourism knowledge base.

Never calculate unsupported taxi costs.

============================================================
MEALS
============================================================

If the knowledge base contains a verified restaurant or food
location, include it.

If it contains food prices, include them.

If no restaurant is supported, do NOT invent one.

Instead say:

The TrekTales knowledge base does not contain a verified
restaurant recommendation for this stop.

If the food price is missing:

**Food cost:** Not available in the TrekTales tourism
knowledge base.

============================================================
BUDGET
============================================================

After all days:

# 💰 Estimated Budget

Create a Markdown table.

Use only verified costs.

Example:

| Expense | Cost |
|---|---:|
| Ayub National Park | Rs. 100/person |
| Food | Rs. 300–500/person |
| Taxi | Distance-dependent |
| **Known subtotal** | **Rs. 400–600/person** |

IMPORTANT:

Only calculate a subtotal if every value used in the subtotal
is explicitly available and mathematically valid.

Do not calculate unsupported taxi costs.

If the complete trip cannot be calculated:

**Total trip cost:** Cannot be fully calculated from the
TrekTales knowledge base.

Then discuss the user's selected budget:

### 🎯 Your Budget

**{budget}**

Explain which parts are verified and which costs remain unknown.

============================================================
PHOTOGRAPHY
============================================================

# 📸 Photography Highlights

Include only locations or activities supported by the evidence.

Use this format:

### 🌳 [Place]

**Best for:** [only supported information]

If the evidence does not explicitly describe photography
features, do not invent them.

You may connect a user-selected photography interest to a place
only when the activity/place itself is supported, without making
unsupported factual claims.

============================================================
WHAT TO CARRY
============================================================

# 🎒 What to Carry

Keep this section practical but do not claim that something is
required because of weather, facilities or local conditions
unless the knowledge base supports that claim.

General travel-preparation suggestions may be phrased as
recommendations rather than facts about the destination.

Examples:

- 📱 Fully charged phone/camera
- 🔋 Power bank
- 👟 Comfortable walking shoes
- 💧 Drinking water
- 💵 Small cash denominations

Do not claim these are destination-specific requirements.

============================================================
IMPORTANT INFORMATION
============================================================

# ⚠️ Important Information

Explicitly list important missing information.

For example:

- Exact distance: Not available in the TrekTales tourism
  knowledge base.
- Exact taxi fare: Not available in the TrekTales tourism
  knowledge base.
- Verified restaurant: Not available in the TrekTales tourism
  knowledge base.

Only include missing facts that are relevant to this itinerary.

============================================================
KNOWLEDGE-BASE SOURCES
============================================================

# 📚 Knowledge-Base Sources

List ONLY source filenames that actually occur in the supplied
evidence.

Example:

- `Pindi_Places.pdf`
- `TR-003 – Taxi`
- `PL-002 – Ayub National Park`

Never invent a filename.

Never cite a source that does not appear in the evidence.

Use filename only.

============================================================
FINAL RECOMMENDATION
============================================================

# 🌿 TrekTales Recommendation

Give a concise sequence such as:

**Best sequence:**

🚕 Starting point → 🌳 supported place → 🏛️ supported place
→ 🍽️ supported food stop → 🚕 return

Only include places actually supported by the evidence.

Do not invent missing transport routes.

============================================================
ANTI-HALLUCINATION CHECK
============================================================

Before producing the answer, verify internally:

1. Exactly {days} day(s).
2. Destination is {destination}.
3. Starting location is {starting_location}.
4. Traveler count is {travelers}.
5. Budget is {budget}.
6. Travel style is {travel_style}.
7. Interests are {interests_text}.
8. Every tourism fact comes from the evidence.
9. No attraction was invented.
10. No restaurant was invented.
11. No hotel was invented.
12. No price was invented.
13. No distance was invented.
14. No travel time was invented.
15. No taxi fare was invented.
16. No opening hours were invented.
17. No fake source was invented.
18. Missing information is clearly marked.
19. No HTML.
20. No code fences.
21. The response is clean Markdown.
22. The response is detailed enough to be genuinely useful.

============================================================
TOURISM KNOWLEDGE-BASE EVIDENCE
============================================================

{evidence_text}

============================================================
END EVIDENCE
============================================================

Now generate the final TrekTales itinerary.
"""

    # ========================================================
    # RATE LIMIT HELPERS
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
                        "You are TrekTales. "
                        "Generate polished Markdown itineraries. "
                        "Use only the supplied tourism evidence. "
                        "Never hallucinate tourism facts. "
                        "Missing facts must be explicitly marked "
                        "as unavailable in the TrekTales tourism "
                        "knowledge base."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.2,
            "max_tokens": 5000,
        }

        last_response = None

        for attempt in range(self.max_retries + 1):

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
                    "GROQ_BASE_URL and GROQ_API_KEY."
                ) from exc

            if response.status_code == 200:
                break

            if response.status_code in (401, 403):

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
                        message = str(error_object).strip()

                except Exception:
                    message = ""

                if response.status_code == 403:
                    raise RuntimeError(
                        "Groq rejected access to the configured "
                        f"model '{self.model}'. {message}"
                    )

                raise RuntimeError(
                    "Groq authentication failed. "
                    "Check GROQ_API_KEY. "
                    f"{message}"
                )

            if response.status_code == 404:

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
                        message = str(error_object).strip()

                except Exception:
                    message = ""

                raise RuntimeError(
                    "The configured Groq model is unavailable. "
                    f"Model: {self.model}. "
                    f"{message}"
                )

            if response.status_code == 429:

                if attempt < self.max_retries:

                    details = self._get_rate_limit_details(
                        response
                    )

                    retry_after = details["retry_after"]

                    try:
                        wait_seconds = float(
                            retry_after
                        ) if retry_after else 3.0

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

                    time.sleep(wait_seconds)

                    continue

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
                        message = str(error_object).strip()

                except Exception:
                    message = ""

                raise RuntimeError(
                    "Groq rate limit is currently active. "
                    "Please wait for the limit to reset and "
                    "generate the itinerary again."
                    + (
                        f" Groq says: {message}"
                        if message
                        else ""
                    )
                )

            if response.status_code >= 400:

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
                        message = str(error_object).strip()

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

        try:
            data = last_response.json()

        except Exception as exc:
            raise RuntimeError(
                "Groq returned an invalid response."
            ) from exc

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

        days = max(1, min(days, 3))

        try:
            travelers = int(travelers)
        except Exception:
            travelers = 1

        travelers = max(1, travelers)

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
    # COMPATIBILITY
    # ========================================================

    def generate(self, **kwargs):
        return self.run(**kwargs)

    def plan(self, **kwargs):
        return self.run(**kwargs)


__all__ = ["TrekTalesCrew"]
