from __future__ import annotations

import time
from typing import Any

import requests
import streamlit as st


class TrekTalesCrew:
    """
    TrekTales grounded itinerary generation engine.

    Uses Groq's OpenAI-compatible HTTP API.

    The model is strictly grounded in the tourism evidence
    retrieved by the FAISS knowledge base.
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

        # Small retry count.
        # This prevents repeated API hammering during 429 errors.
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
                "GROQ_API_KEY is missing from Streamlit Secrets. "
                "Open Streamlit Cloud → Settings → Secrets and "
                "add your valid Groq API key."
            )

        if not key.startswith("gsk_"):

            raise RuntimeError(
                "GROQ_API_KEY does not appear to be a valid "
                "Groq API key. Check the value in Streamlit Secrets."
            )

        return key


    # ========================================================
    # SOURCE CLEANING
    # ========================================================

    @staticmethod
    def _clean_source(source: Any) -> str:

        if not source:
            return ""

        source = str(source).strip()

        source = source.replace(
            "\\",
            "/",
        )

        source = source.split("/")[-1]

        source = source.replace(
            ".html",
            "",
        )

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
                "NO TOURISM KNOWLEDGE-BASE EVIDENCE "
                "WAS RETRIEVED."
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

            source = cls._clean_source(
                source
            )

            page_text = str(
                page
            ).strip()

            if (
                page_text
                and page_text.lower()
                not in (
                    "n/a",
                    "none",
                )
            ):

                location = (
                    f"{source} | Page {page_text}"
                )

            else:

                location = source

            blocks.append(
                "\n".join(
                    [
                        f"===== KNOWLEDGE ITEM {index} =====",
                        f"SOURCE: {location or 'Knowledge Base'}",
                        "CONTENT:",
                        text,
                        f"===== END ITEM {index} =====",
                    ]
                )
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

        if interests:

            interests_text = ", ".join(
                str(item)
                for item in interests
            )

        else:

            interests_text = (
                "No specific interests provided."
            )

        return f"""
You are the senior itinerary writer for TrekTales.

Your job is to transform the supplied tourism knowledge-base
evidence into a polished, detailed and personalized travel
itinerary.

The user wants an ENHANCED itinerary, not a short summary.

============================================================
TRIP INFORMATION
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

Interests:
{interests_text}

Response language:
{language}

============================================================
MOST IMPORTANT RULE — KNOWLEDGE GROUNDING
============================================================

The tourism knowledge-base evidence supplied at the bottom of
this prompt is the ONLY source of tourism facts.

You MUST NOT use outside tourism knowledge.

You MUST NOT fill gaps from your own knowledge.

You MUST NOT guess.

You MUST NOT hallucinate.

Every tourism-specific factual claim must be supported by the
provided evidence.

============================================================
NEVER INVENT THESE
============================================================

Never invent:

- attractions
- restaurants
- hotels
- activities
- prices
- entry fees
- ticket prices
- taxi fares
- transport fares
- travel times
- distances
- routes
- opening hours
- closing hours
- addresses
- phone numbers
- contact details
- availability
- ratings
- reviews
- historical facts
- weather
- events
- schedules
- local rules
- safety conditions

If something is not supported by the evidence, write:

**Not available in the TrekTales tourism knowledge base.**

For example:

**Travel time:** Not available in the TrekTales tourism
knowledge base.

Do NOT replace a missing fact with an estimate.

============================================================
IMPORTANT DISTANCE / TAXI RULE
============================================================

If the knowledge base provides a taxi base fare but does not
provide the distance-based fare, do NOT calculate the final
taxi price.

You may say:

- Taxi base fare: Rs. 300
- Distance-based fare: Not available in the TrekTales
  tourism knowledge base.

If the distance itself is missing, explicitly say so.

Do not calculate a round-trip taxi total unless the evidence
contains enough verified information to calculate it.

============================================================
ENHANCED OUTPUT REQUIREMENT
============================================================

Do NOT produce a short generic answer.

Produce a rich, structured itinerary similar to a professional
travel planner.

Use:

- Markdown headings
- bold labels
- bullet points
- tables where useful
- emojis
- practical explanations
- source references
- clear time blocks when supported
- personalized explanations
- budget analysis
- photography highlights
- packing suggestions
- important-information section
- final recommendation

The answer should feel complete and polished.

============================================================
TIME BLOCK RULE
============================================================

Only use exact times when:

1. the evidence provides those times, OR
2. the user has supplied those times.

Do NOT invent opening hours.

Do NOT invent activity durations.

However, when the evidence gives enough information to create
a logical sequence, you may organize supported activities into
a schedule.

If an exact time is not supported, do not pretend that it is
verified.

============================================================
PERSONALIZATION RULE
============================================================

Use the user's:

- destination
- starting location
- number of travelers
- budget
- travel style
- interests

to organize the supplied evidence.

Do not create new tourism facts simply to personalize the trip.

For example, if the user's interests include photography,
explain why a knowledge-base-supported location fits photography
only when that connection can reasonably be made from the
supplied information.

============================================================
OUTPUT
============================================================

Start EXACTLY with:

# 🌿 Personalized {destination} Adventure Itinerary

Then include:

## 📍 {destination} · {days} Day(s) · {travelers} Travelers

Show:

**Travel style:** {travel_style}

**Focus:** [derive from the user's supplied interests]

**Budget:** {budget}

============================================================
TRIP OVERVIEW
============================================================

Create:

## 🗺️ Trip Overview

Write a concise but useful personalized overview.

Explain the overall character of the trip using ONLY
knowledge-base-supported places and activities.

Then provide a bullet list of the major supported stops.

============================================================
DAY-BY-DAY ITINERARY
============================================================

Create EXACTLY {days} day(s).

For one day:

# ☀️ Your Day in {destination}

For multiple days:

# ☀️ Day 1 — [supported theme]

# ☀️ Day 2 — [supported theme]

Continue until exactly Day {days}.

Do not create extra days.

============================================================
EACH STOP
============================================================

For every supported stop, use a structure similar to:

### 07:30 – 08:30 | 🚕 Travel from {starting_location}
to {destination}

Only use the time if supported.

Then:

**Transport:** [only if supported]

**Starting point:** [only if supported]

**Destination:** [only if supported]

Explain the supported information.

Then:

**Known cost:**

- [verified cost]
- [missing component explicitly marked unavailable]

📚 **Source:** `filename`

If important information is missing, add:

> ⚠️ The knowledge base does not provide the required
> information, so TrekTales has not estimated it.

============================================================
ACTIVITY DETAIL
============================================================

For a place/activity, use:

### 🌳 [Place Name]

**Focus:** [supported focus]

Write a useful personalized explanation.

Then:

**Suggested experience:**

- supported activity
- supported activity
- supported activity

Only use activities supported by the evidence.

If entry price is supported:

**Entry:** **Rs. X per person**

If not:

**Entry:** Not available in the TrekTales tourism
knowledge base.

Then:

📚 **Source:** `filename`

============================================================
LUNCH / FOOD
============================================================

If the evidence contains a verified restaurant:

Provide it.

If the evidence does NOT contain a verified restaurant,
DO NOT invent one.

Instead say:

### 🍽️ Lunch Break

The TrekTales knowledge base does not contain a verified
restaurant recommendation for this stop.

**Food cost:** Not available in the TrekTales tourism
knowledge base.

============================================================
TRANSPORT
============================================================

Transport must be evidence-grounded.

If the evidence contains:

- taxi
- bus
- train
- walking
- route
- fare
- base fare

use those facts.

If something is missing, explicitly say:

**Not available in the TrekTales tourism knowledge base.**

============================================================
BUDGET
============================================================

After the itinerary provide:

# 💰 Estimated Budget

Use a table when useful.

Example:

| Expense | Estimated Cost |
|---|---:|
| Entry | Rs. X |
| Food | Rs. X |
| Taxi | Distance-dependent |
| Known subtotal | Rs. X |

Only calculate totals from verified numbers.

If a total cannot be calculated reliably:

**Total trip cost:** Cannot be fully calculated from the
available knowledge base.

Then discuss the user's selected budget:

### 🎯 Your Budget

{budget}

Explain whether the available knowledge base is sufficient
to confirm the complete budget.

Do NOT claim that the budget is sufficient unless the evidence
actually supports that conclusion.

============================================================
PHOTOGRAPHY
============================================================

Create:

# 📸 Photography Highlights

List only supported locations.

For each:

### 🌳 [Supported location]

**Best for:** [only supported or reasonable from the supplied
evidence]

Do not invent viewpoints or photo spots.

============================================================
WHAT TO CARRY
============================================================

Create:

# 🎒 What to Carry

Provide general practical travel-preparation suggestions.

Do NOT claim that a particular item is required because of
weather or local conditions unless supported by evidence.

These can be presented as general preparation suggestions,
not tourism facts.

============================================================
IMPORTANT INFORMATION
============================================================

Create:

# ⚠️ Important Information

Clearly list important missing information.

Examples:

- Exact distance: Not available in the TrekTales tourism
  knowledge base.
- Exact taxi total: Not available in the TrekTales tourism
  knowledge base.
- Verified lunch restaurant: Not available in the TrekTales
  tourism knowledge base.

Do not invent missing information.

============================================================
KNOWLEDGE-BASE SOURCES
============================================================

Finish with:

# 📚 Knowledge-Base Sources

List only the filenames that actually occur in the evidence.

Use:

- `filename.pdf`
- `another_file.txt`

Do NOT invent filenames.

Do NOT add a source merely because it would be useful.

============================================================
TREKTALES RECOMMENDATION
============================================================

Finish with:

## 🌿 TrekTales Recommendation

Give the best sequence based ONLY on the supported places
in the evidence.

Use a compact format such as:

🚕 Start → 🌳 Stop → 🏛️ Stop → 🍽️ Lunch →
🌿 Stop → 🍢 Stop → 🚕 Return

Only include stops actually supported by the evidence.

============================================================
FINAL QUALITY CHECK
============================================================

Before returning the answer, verify internally:

1. Exactly {days} day(s) are present.
2. Destination is {destination}.
3. Starting location is {starting_location}.
4. Traveler count is {travelers}.
5. Budget is {budget}.
6. Travel style is {travel_style}.
7. User interests are reflected.
8. Every tourism fact comes from evidence.
9. No attraction was invented.
10. No restaurant was invented.
11. No hotel was invented.
12. No price was invented.
13. No distance was invented.
14. No travel time was invented.
15. No taxi total was invented.
16. No opening hours were invented.
17. No fake source was invented.
18. Missing information is explicitly marked.
19. The answer is detailed and enhanced.
20. The answer contains no HTML.
21. The answer contains no code fences.
22. The answer follows the requested language.

============================================================
TOURISM KNOWLEDGE-BASE EVIDENCE
============================================================

{evidence_text}

============================================================
END OF TOURISM KNOWLEDGE-BASE EVIDENCE
============================================================

Now produce ONLY the final enhanced TrekTales itinerary.
"""


    # ========================================================
    # RATE-LIMIT DETAILS
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
    # RATE-LIMIT ERROR
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

        except Exception:
            pass

        if retry_after:

            wait_text = (
                f"Groq requested a retry after "
                f"{retry_after} seconds."
            )

        elif reset_tokens:

            wait_text = (
                f"Token limit reset information: "
                f"{reset_tokens}."
            )

        elif reset_requests:

            wait_text = (
                f"Request limit reset information: "
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
            f"{wait_text}"
            f"{extra} "
            "Please wait for the limit to reset and "
            "try again."
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
            f"{self.base_url}"
            "/chat/completions"
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
                        "You are the TrekTales senior "
                        "itinerary writer. "
                        "Use ONLY the tourism evidence "
                        "provided by the user prompt. "
                        "Never invent tourism facts. "
                        "When information is missing, "
                        "say exactly that it is not "
                        "available in the TrekTales "
                        "tourism knowledge base. "
                        "Return polished Markdown only."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.2,
            "max_tokens": 4000,
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
                    "Please check GROQ_BASE_URL and your "
                    "internet connection."
                ) from exc

            # =================================================
            # SUCCESS
            # =================================================

            if response.status_code == 200:
                break

            # =================================================
            # AUTH
            # =================================================

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

                except Exception:
                    pass

                if response.status_code == 403:

                    raise RuntimeError(
                        "Groq rejected access to the "
                        "configured model or API resource. "
                        f"Model: {self.model}. "
                        f"{message}"
                    )

                raise RuntimeError(
                    "Groq authentication failed. "
                    "Check GROQ_API_KEY in Streamlit Secrets. "
                    f"{message}"
                )

            # =================================================
            # MODEL NOT FOUND
            # =================================================

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

                except Exception:
                    pass

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

                    retry_after = details[
                        "retry_after"
                    ]

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

            # =================================================
            # OTHER ERRORS
            # =================================================

            if response.status_code >= 400:

                message = response.text[:700]

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
                                message,
                            )
                        ).strip()

                except Exception:
                    pass

                raise RuntimeError(
                    f"Groq API request failed "
                    f"(HTTP {response.status_code}). "
                    f"{message}"
                )

        # =====================================================
        # RESPONSE SAFETY
        # =====================================================

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

        # =====================================================
        # CHOICE
        # =====================================================

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
    "TrekTalesCrew",
]
