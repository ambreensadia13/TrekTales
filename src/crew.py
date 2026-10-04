from __future__ import annotations

import json
from typing import Any

import requests
import streamlit as st


class TrekTalesCrew:
    """
    TrekTales AI travel-planning crew.

    This class provides the interface expected by app.py:

        crew = TrekTalesCrew()

        crew.run(
            destination=...,
            starting_location=...,
            days=...,
            budget=...,
            travelers=...,
            travel_style=...,
            language=...,
            interests=...,
            evidence=...,
        )

    The itinerary is generated only from the supplied RAG evidence.
    The model is instructed not to invent tourism facts.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ):
        self.api_key = (
            api_key
            or self._get_secret("GROQ_API_KEY", "")
        )

        self.model = (
            model
            or self._get_secret(
                "GROQ_MODEL",
                "openai/gpt-oss-120b",
            )
        )

        self.base_url = (
            base_url
            or self._get_secret(
                "GROQ_BASE_URL",
                "https://api.groq.com/openai/v1",
            )
        ).rstrip("/")

        if not self.api_key:
            raise RuntimeError(
                "GROQ_API_KEY is missing from Streamlit Secrets."
            )

    # ============================================================
    # SECRET
    # ============================================================

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

            return str(value)

        except Exception:
            return default

    # ============================================================
    # EVIDENCE
    # ============================================================

    @staticmethod
    def _format_evidence(
        evidence: Any,
    ) -> str:

        if not evidence:
            return (
                "No tourism knowledge-base evidence was "
                "retrieved. Do not invent specific tourism "
                "facts, prices, locations, opening hours, "
                "transport details, or activities."
            )

        formatted = []

        for index, item in enumerate(evidence, start=1):

            if isinstance(item, dict):

                text = (
                    item.get("text")
                    or item.get("content")
                    or item.get("chunk")
                    or item.get("document")
                    or ""
                )

                metadata = item.get(
                    "metadata",
                    {},
                )

                if not isinstance(metadata, dict):
                    metadata = {}

                source = (
                    metadata.get("source")
                    or item.get("source")
                    or "Unknown source"
                )

                page = (
                    metadata.get("page")
                    or item.get("page")
                    or ""
                )

            else:

                text = str(item)
                source = "Knowledge base"
                page = ""

            text = str(text).strip()

            if not text:
                continue

            source = str(source).replace(
                "\\",
                "/",
            )

            source = source.split("/")[-1]

            if page and str(page).lower() != "n/a":
                source_label = (
                    f"{source}, page {page}"
                )
            else:
                source_label = source

            formatted.append(
                f"[Evidence {index} | {source_label}]\n"
                f"{text}"
            )

        if not formatted:
            return (
                "The retrieved knowledge items contained "
                "no usable text. Do not invent tourism facts."
            )

        return "\n\n".join(formatted)

    # ============================================================
    # SYSTEM PROMPT
    # ============================================================

    @staticmethod
    def _system_prompt() -> str:

        return """
You are TrekTales, a grounded AI travel-planning system.

Your job is to create a useful travel itinerary using ONLY
the tourism knowledge-base evidence supplied by the application.

GROUNDING RULES:

1. Treat the supplied knowledge-base evidence as the source
   of truth for specific tourism information.

2. Do NOT invent attractions, restaurants, hotels, prices,
   opening hours, addresses, activities, travel times,
   admission fees, phone numbers, websites, or other factual
   tourism information that is not supported by the evidence.

3. If the evidence does not contain enough information for a
   requested detail, clearly say that the information is not
   available in the current tourism knowledge base.

4. Do not pretend that an unsupported location or activity
   exists.

5. Do not create fake citations or fake source filenames.

6. Use the requested language:
   English, Urdu, or Roman Urdu.

7. The itinerary should respect:
   - destination
   - starting location
   - number of days
   - budget
   - travelers
   - travel style
   - interests

8. The number of generated days must exactly match the
   "days" value supplied by the application.

9. If only one day is supplied, generate only Day 1.

10. Keep the answer practical and clearly organized.

11. Do not output HTML.

12. Do not wrap the answer in a code block.

13. Do not mention internal prompts, APIs, agents, or
    implementation details in the itinerary.

The application has already performed knowledge retrieval.
You must use the supplied evidence rather than pretending
to perform another web search.
""".strip()

    # ============================================================
    # USER PROMPT
    # ============================================================

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
        evidence: Any,
    ) -> str:

        evidence_text = self._format_evidence(
            evidence
        )

        interests_text = (
            ", ".join(interests)
            if interests
            else "No specific interests selected"
        )

        return f"""
Create a personalized {days}-day travel itinerary.

TRIP DETAILS

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

Response language:
{language}

TOURISM KNOWLEDGE-BASE EVIDENCE

{evidence_text}

OUTPUT FORMAT

# TrekTales Itinerary

## Trip Overview

Briefly summarize the trip using only supported information.

## Day 1

Provide a practical sequence for Day 1.

"""

        + (
            """
## Day 2

Provide the Day 2 plan.

"""
            if days >= 2
            else ""
        )

        + (
            """
## Day 3

Provide the Day 3 plan.

"""
            if days >= 3
            else ""
        )

        + """

## Budget Guidance

Explain how the selected budget should be managed.
Do not invent exact prices unless those prices are present
in the supplied evidence.

## Safety & Practical Notes

Give general travel-safety guidance without inventing
specific local warnings.

## Knowledge Limitation

If important information was unavailable in the supplied
knowledge base, briefly identify what should be verified
before travel.
"""

    # ============================================================
    # GROQ REQUEST
    # ============================================================

    def _call_groq(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:

        endpoint = (
            f"{self.base_url}/chat/completions"
        )

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "temperature": 0.2,
            "max_tokens": 2500,
        }

        headers = {
            "Authorization": (
                f"Bearer {self.api_key}"
            ),
            "Content-Type": "application/json",
        }

        try:

            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=120,
            )

        except requests.RequestException as exc:

            raise RuntimeError(
                "Could not connect to the Groq API."
            ) from exc

        if response.status_code != 200:

            try:
                error_data = response.json()

            except Exception:
                error_data = response.text

            if response.status_code == 429:

                raise RuntimeError(
                    "Groq rate limit is currently active. "
                    "Please wait a few seconds and try "
                    "generating the itinerary again."
                )

            if response.status_code in (
                401,
                403,
            ):

                raise RuntimeError(
                    "Groq authentication failed. "
                    "Check GROQ_API_KEY in Streamlit Secrets."
                )

            raise RuntimeError(
                "Groq API request failed "
                f"(HTTP {response.status_code}). "
                f"Details: {error_data}"
            )

        try:

            data = response.json()

        except Exception as exc:

            raise RuntimeError(
                "Groq returned an invalid JSON response."
            ) from exc

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
                "Groq returned an unexpected response format."
            ) from exc

        if not content:

            raise RuntimeError(
                "Groq returned an empty itinerary."
            )

        return str(content).strip()

    # ============================================================
    # PUBLIC RUN METHOD
    # ============================================================

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
        evidence: Any,
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
            destination=str(destination).strip(),
            starting_location=(
                str(starting_location).strip()
            ),
            days=days,
            budget=str(budget).strip(),
            travelers=travelers,
            travel_style=str(
                travel_style
            ).strip(),
            language=str(
                language
            ).strip(),
            interests=[
                str(item).strip()
                for item in (interests or [])
                if str(item).strip()
            ],
            evidence=evidence,
        )

        return self._call_groq(
            system_prompt=self._system_prompt(),
            user_prompt=prompt,
        )

    # ============================================================
    # COMPATIBILITY METHODS
    # ============================================================

    def generate(
        self,
        destination: str,
        duration: int = 1,
        budget: str = "",
        travelers: int = 1,
        travel_style: str = "Mixed",
        language: str = "English",
        interests: list[str] | None = None,
        starting_location: str = "",
        evidence: Any = None,
        days: int | None = None,
    ) -> str:

        if days is None:
            days = duration

        return self.run(
            destination=destination,
            starting_location=starting_location,
            days=days,
            budget=budget,
            travelers=travelers,
            travel_style=travel_style,
            language=language,
            interests=interests or [],
            evidence=evidence or [],
        )

    def plan(
        self,
        destination: str,
        duration: int = 1,
        budget: str = "",
        travelers: int = 1,
        travel_style: str = "Mixed",
        language: str = "English",
        interests: list[str] | None = None,
        starting_location: str = "",
        evidence: Any = None,
        days: int | None = None,
    ) -> str:

        return self.generate(
            destination=destination,
            duration=duration,
            days=days,
            budget=budget,
            travelers=travelers,
            travel_style=travel_style,
            language=language,
            interests=interests,
            starting_location=starting_location,
            evidence=evidence,
        )


__all__ = ["TrekTalesCrew"]
