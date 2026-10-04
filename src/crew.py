from __future__ import annotations

import json
import time
from typing import Any

import requests
import streamlit as st


class TrekTalesCrew:
    """
    TrekTales itinerary generation client.

    Uses Groq's OpenAI-compatible HTTP API.

    The class keeps the public TrekTalesCrew interface expected by
    app.py while providing controlled retry handling for temporary
    Groq rate limits.
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

        # Keep retries deliberately small.
        # We do not want the Streamlit app repeatedly hammering Groq.
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
                source_text = source_text.replace("\\", "/")
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

        interests_text = (
            ", ".join(str(item) for item in interests)
            if interests
            else "No specific interests provided."
        )

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
11. Do not use general world knowledge to fill missing tourism facts.
12. Only make claims that are supported by the supplied evidence.

The itinerary should include:

- Trip overview
- Day-by-day plan
- Suggested activities supported by the knowledge base
- Budget considerations when supported by the evidence
- Practical notes
- Knowledge-base sources used

If information is missing from the knowledge base, say:

"Not available in the TrekTales tourism knowledge base."

Do not invent an answer.

TOURISM KNOWLEDGE BASE

{evidence_text}
"""

    # ========================================================
    # RATE LIMIT INFORMATION
    # ========================================================

    @staticmethod
    def _get_rate_limit_details(response: requests.Response) -> dict[str, str]:
        """
        Extract Groq rate-limit information from response headers.

        Groq exposes retry-after and x-ratelimit-* headers.
        """

        headers = response.headers

        return {
            "retry_after": headers.get("retry-after", ""),
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

        details = self._get_rate_limit_details(response)

        retry_after = details["retry_after"]
        reset_tokens = details["reset_tokens"]
        reset_requests = details["reset_requests"]

        try:
            error_data = response.json()

            error_object = error_data.get("error", {})

            if isinstance(error_object, dict):
                message = str(
                    error_object.get("message", "")
                ).strip()
            else:
                message = str(error_object).strip()

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
            f"Temporary Groq rate limit detected. "
            f"{wait_text}"
        )

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
                        "itinerary generation assistant. "
                        "You must follow the supplied tourism "
                        "knowledge base and must never invent "
                        "tourism facts."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.2,
            "max_tokens": 1800,
            "reasoning_effort": "medium",
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
                    "GROQ_BASE_URL, and try again."
                ) from exc

            # ====================================================
            # SUCCESS
            # ====================================================

            if response.status_code == 200:
                break

            # ====================================================
            # AUTHENTICATION
            # ====================================================

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

            # ====================================================
            # MODEL ERROR
            # ====================================================

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

            # ====================================================
            # RATE LIMIT
            # ====================================================

            if response.status_code == 429:

                if attempt < self.max_retries:

                    details = self._get_rate_limit_details(
                        response
                    )

                    retry_after = details["retry_after"]

                    wait_seconds = 2.0

                    try:
                        if retry_after:
                            wait_seconds = float(
                                retry_after
                            )
                    except (TypeError, ValueError):
                        wait_seconds = 2.0

                    # Never let a malformed header create
                    # an excessive wait inside Streamlit.
                    wait_seconds = max(
                        1.0,
                        min(wait_seconds, 15.0),
                    )

                    time.sleep(wait_seconds)

                    continue

                raise self._rate_limit_error(
                    response,
                    attempt,
                )

            # ====================================================
            # OTHER API ERRORS
            # ====================================================

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
        # RESPONSE JSON
        # ========================================================

        try:
            data = last_response.json()

        except Exception as exc:

            raise RuntimeError(
                "Groq returned an invalid response."
            ) from exc

        # ========================================================
        # CONTENT
        # ========================================================

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

        # ----------------------------------------------------
        # DAYS
        # ----------------------------------------------------

        try:
            days = int(days)
        except Exception:
            days = 1

        days = max(1, min(days, 3))

        # ----------------------------------------------------
        # TRAVELERS
        # ----------------------------------------------------

        try:
            travelers = int(travelers)
        except Exception:
            travelers = 1

        travelers = max(1, travelers)

        # ----------------------------------------------------
        # PROMPT
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # GROQ
        # ----------------------------------------------------

        return self._call_groq(prompt)

    # ========================================================
    # COMPATIBILITY METHODS
    # ========================================================

    def generate(self, **kwargs):
        return self.run(**kwargs)

    def plan(self, **kwargs):
        return self.run(**kwargs)


__all__ = ["TrekTalesCrew"]
