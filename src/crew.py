from __future__ import annotations

import json
from typing import Any

import requests
import streamlit as st


class TrekTalesCrew:
    """
    TrekTales itinerary generation client.

    This class keeps the public TrekTalesCrew interface used by app.py
    while calling Groq through its OpenAI-compatible HTTP API.
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
    def _format_evidence(evidence: list[Any]) -> str:
        if not evidence:
            return (
                "No tourism knowledge-base evidence was retrieved."
            )

        blocks = []

        for index, item in enumerate(evidence, start=1):

            if isinstance(item, dict):

                text = (
                    item.get("text")
                    or item.get("content")
                    or item.get("chunk")
                    or ""
                )

                source = (
                    item.get("source")
                    or item.get("document")
                    or item.get("filename")
                    or ""
                )

                page = item.get("page", "")

            else:

                text = str(item)
                source = ""
                page = ""

            text = str(text).strip()

            if not text:
                continue

            source_text = str(source).strip()

            if source_text:
                source_text = source_text.split("/")[-1]

            location = source_text

            if page not in ("", None, "N/A"):
                location = f"{source_text} | Page {page}"

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

        evidence_text = self._format_evidence(evidence)

        interests_text = ", ".join(
            str(item) for item in interests
        ) if interests else "No specific interests provided."

        return f"""
You are the itinerary-generation engine for TrekTales.

Create a practical travel itinerary using ONLY the supplied
tourism knowledge-base evidence.

TRIP DETAILS
Destination: {destination}
Starting location: {starting_location}
Number of days: {days}
Travelers: {travelers}
Budget: {budget}
Travel style: {travel_style}
Language: {language}
Interests: {interests_text}

IMPORTANT GROUNDING RULES

1. Use the tourism knowledge-base evidence as the primary source.
2. Do not invent attractions, restaurants, hotels, prices,
   opening hours, travel times, addresses, phone numbers,
   activities, or other tourism facts.
3. If the knowledge base does not contain enough information,
   clearly say that the information is not available.
4. Do not fabricate sources.
5. Do not create fake citations.
6. Do not output HTML.
7. Do not output Markdown code fences.
8. Respect the requested number of days exactly.
9. Keep recommendations relevant to the supplied destination.
10. Use the requested language.

The itinerary should include:

- Trip overview
- Day-by-day plan
- Suggested activities supported by the knowledge base
- Budget considerations when supported by the evidence
- Practical notes
- Knowledge-base sources used

TOURISM KNOWLEDGE BASE

{evidence_text}
"""

    # ========================================================
    # GROQ REQUEST
    # ========================================================

    def _call_groq(self, prompt: str) -> str:

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
                        "itinerary generation assistant."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.2,
            "max_tokens": 2500,
        }

        try:

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=120,
            )

        except requests.RequestException as exc:

            raise RuntimeError(
                "Could not connect to the Groq API. "
                "Please check your internet connection, "
                "GROQ_BASE_URL, and try again."
            ) from exc

        # ====================================================
        # AUTHENTICATION
        # ====================================================

        if response.status_code in (401, 403):

            raise RuntimeError(
                "Groq authentication failed. "
                "Your GROQ_API_KEY is missing, invalid, "
                "expired, or does not have access to the "
                "configured Groq API. Check Streamlit Secrets."
            )

        # ====================================================
        # MODEL ERROR
        # ====================================================

        if response.status_code == 404:

            try:
                error_data = response.json()
                message = (
                    error_data
                    .get("error", {})
                    .get("message", "")
                )
            except Exception:
                message = ""

            raise RuntimeError(
                "The configured Groq model is unavailable. "
                f"Model: {self.model}. "
                f"{message}"
            )

        # ====================================================
        # RATE LIMIT
        # ====================================================

        if response.status_code == 429:

            raise RuntimeError(
                "Groq rate limit is currently active. "
                "Please wait a few seconds and generate "
                "the itinerary again."
            )

        # ====================================================
        # OTHER API ERRORS
        # ====================================================

        if response.status_code >= 400:

            try:
                error_data = response.json()

                message = (
                    error_data
                    .get("error", {})
                    .get("message", "")
                )

            except Exception:
                message = response.text[:500]

            raise RuntimeError(
                f"Groq API request failed "
                f"(HTTP {response.status_code}). "
                f"{message}"
            )

        # ====================================================
        # RESPONSE JSON
        # ====================================================

        try:
            data = response.json()

        except Exception as exc:

            raise RuntimeError(
                "Groq returned an invalid response."
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

        except (KeyError, IndexError, TypeError) as exc:

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

        if days < 1:
            days = 1

        if days > 3:
            days = 3

        try:
            travelers = int(travelers)
        except Exception:
            travelers = 1

        if travelers < 1:
            travelers = 1

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
