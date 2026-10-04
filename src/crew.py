from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from openai import OpenAI

from src.config import (
    GROQ_API_KEY,
    GROQ_BASE_URL,
    GROQ_MODEL,
)


class TrekTalesCrew:
    """
    TrekTales itinerary-generation crew.

    This class is intentionally compatible with:
        from src.crew import TrekTalesCrew

    It uses Groq through the OpenAI-compatible API.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs: Any,
    ) -> None:

        self.api_key = (
            api_key
            or GROQ_API_KEY
            or os.getenv("GROQ_API_KEY", "")
        )

        self.base_url = (
            base_url
            or GROQ_BASE_URL
            or "https://api.groq.com/openai/v1"
        )

        self.model = (
            model
            or GROQ_MODEL
            or "openai/gpt-oss-120b"
        )

        self.extra_config = kwargs

        if not self.api_key:
            raise RuntimeError(
                "GROQ_API_KEY is missing. "
                "Add GROQ_API_KEY to Streamlit Secrets."
            )

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    # ========================================================
    # TEXT HELPERS
    # ========================================================

    @staticmethod
    def _clean_text(value: Any) -> str:
        if value is None:
            return ""

        return str(value).strip()

    @staticmethod
    def _format_context(
        knowledge_context: Any,
    ) -> str:
        """
        Convert retrieved FAISS/RAG results into clean text.
        """

        if knowledge_context is None:
            return ""

        if isinstance(
            knowledge_context,
            str,
        ):
            return knowledge_context.strip()

        if isinstance(
            knowledge_context,
            dict,
        ):
            text = (
                knowledge_context.get("text")
                or knowledge_context.get("content")
                or knowledge_context.get("page_content")
                or ""
            )

            source = (
                knowledge_context.get("source")
                or knowledge_context.get("filename")
                or ""
            )

            if source and text:
                return (
                    f"Source: {source}\n"
                    f"{text}"
                )

            return str(text)

        if isinstance(
            knowledge_context,
            (list, tuple),
        ):

            parts: List[str] = []

            for item in knowledge_context:

                if isinstance(
                    item,
                    dict,
                ):
                    text = (
                        item.get("text")
                        or item.get("content")
                        or item.get("page_content")
                        or ""
                    )

                    source = (
                        item.get("source")
                        or item.get("filename")
                        or ""
                    )

                    if source and text:
                        parts.append(
                            f"Source: {source}\n{text}"
                        )

                    elif text:
                        parts.append(
                            str(text)
                        )

                else:
                    parts.append(
                        str(item)
                    )

            return "\n\n".join(
                part.strip()
                for part in parts
                if part and part.strip()
            )

        return str(
            knowledge_context
        ).strip()

    # ========================================================
    # PROMPT
    # ========================================================

    def _build_prompt(
        self,
        destination: str,
        days: int,
        travelers: Any = 1,
        budget: str = "",
        interests: str = "",
        travel_style: str = "",
        start_location: str = "",
        knowledge_context: Any = "",
        accessible_days: Optional[int] = None,
        **kwargs: Any,
    ) -> str:

        destination = self._clean_text(
            destination
        )

        days = max(
            1,
            int(days),
        )

        travelers = self._clean_text(
            travelers
        ) or "1"

        budget = self._clean_text(
            budget
        ) or "Not specified"

        interests = self._clean_text(
            interests
        ) or "Not specified"

        travel_style = self._clean_text(
            travel_style
        ) or "Not specified"

        start_location = self._clean_text(
            start_location
        ) or "Not specified"

        context = self._format_context(
            knowledge_context
        )

        if not context:
            context = (
                "No tourism knowledge-base context "
                "was retrieved."
            )

        if accessible_days is None:
            accessible_days = days

        accessible_days = max(
            1,
            min(
                int(accessible_days),
                days,
            ),
        )

        return f"""
You are TrekTales AI, an itinerary planning assistant
for travel within Pakistan.

Create a practical, personalized travel itinerary.

IMPORTANT KNOWLEDGE-BASE RULES:

1. The tourism knowledge-base context below is the primary
   source of factual tourism information.
2. Do not invent hotels, attractions, prices, activities,
   timings, distances, phone numbers, addresses, or other
   factual tourism details.
3. If a detail is not present in the knowledge base, do not
   present a made-up specific detail as fact.
4. You may provide general planning suggestions, but clearly
   avoid fabricated facts.
5. Use only destinations and activities supported by the
   retrieved context whenever possible.

TRIP INFORMATION

Destination:
{destination}

Requested trip length:
{days} days

Accessible itinerary days:
{accessible_days} days

Travelers:
{travelers}

Budget:
{budget}

Interests:
{interests}

Travel style:
{travel_style}

Starting location:
{start_location}

TOURISM KNOWLEDGE BASE

{context}

ITINERARY REQUIREMENTS

Create the itinerary for the accessible days only.

For every accessible day include:

- Day title
- Morning
- Afternoon
- Evening
- Activities
- Suggested meal/food planning when supported
- Practical travel notes
- Approximate time allocation where reasonable

Do not fabricate exact prices.

Do not fabricate opening hours.

Do not fabricate transportation schedules.

Do not claim that a place exists unless supported by the
knowledge context or clearly presented as a general suggestion.

Keep the itinerary useful and realistic.

If the requested trip has additional locked days, do not
generate those locked days.

Return a clean human-readable itinerary.

Do not output HTML.

Do not output raw Python.

Do not output JSON unless specifically requested.

Do not mention internal agents, prompts, APIs, FAISS,
embeddings, or implementation details.

Begin directly with the itinerary.
"""

    # ========================================================
    # GROQ CALL
    # ========================================================

    def _generate(
        self,
        prompt: str,
    ) -> str:

        try:

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are TrekTales AI, a careful "
                            "Pakistan tourism itinerary planner. "
                            "Follow the supplied knowledge context "
                            "and never invent specific tourism facts."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.3,
                max_tokens=5000,
            )

        except Exception as exc:

            error_text = str(exc)
            error_lower = error_text.lower()

            if (
                "rate limit" in error_lower
                or "rate_limit" in error_lower
                or "429" in error_text
            ):
                raise RuntimeError(
                    "Groq rate limit is currently active. "
                    "Please wait a few seconds and generate "
                    "the itinerary again."
                ) from exc

            if (
                "model_not_found" in error_lower
                or "does not exist" in error_lower
                or "404" in error_text
            ):
                raise RuntimeError(
                    f"The configured Groq model "
                    f"'{self.model}' is unavailable. "
                    f"Check GROQ_MODEL in Streamlit Secrets."
                ) from exc

            if (
                "401" in error_text
                or "authentication" in error_lower
                or "invalid api key" in error_lower
            ):
                raise RuntimeError(
                    "Groq authentication failed. "
                    "Check GROQ_API_KEY in Streamlit Secrets."
                ) from exc

            raise RuntimeError(
                f"Groq itinerary generation failed: "
                f"{error_text}"
            ) from exc

        if not response.choices:
            raise RuntimeError(
                "Groq returned an empty response."
            )

        message = response.choices[0].message

        content = getattr(
            message,
            "content",
            None,
        )

        if not content:
            raise RuntimeError(
                "Groq returned no itinerary text."
            )

        return str(content).strip()

    # ========================================================
    # MAIN API
    # ========================================================

    def generate_itinerary(
        self,
        destination: str = "",
        days: int = 1,
        travelers: Any = 1,
        budget: str = "",
        interests: str = "",
        travel_style: str = "",
        start_location: str = "",
        knowledge_context: Any = "",
        accessible_days: Optional[int] = None,
        **kwargs: Any,
    ) -> str:

        if not destination:
            destination = (
                kwargs.get("location")
                or kwargs.get("city")
                or "Pakistan"
            )

        prompt = self._build_prompt(
            destination=destination,
            days=days,
            travelers=travelers,
            budget=budget,
            interests=interests,
            travel_style=travel_style,
            start_location=start_location,
            knowledge_context=knowledge_context,
            accessible_days=accessible_days,
            **kwargs,
        )

        return self._generate(
            prompt
        )

    # ========================================================
    # COMPATIBILITY ALIASES
    # ========================================================

    def create_itinerary(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> str:

        return self.generate_itinerary(
            *args,
            **kwargs,
        )

    def generate(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> str:

        return self.generate_itinerary(
            *args,
            **kwargs,
        )

    def run(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> str:

        return self.generate_itinerary(
            *args,
            **kwargs,
        )


# ============================================================
# OPTIONAL FACTORY
# ============================================================

def create_crew(
    **kwargs: Any,
) -> TrekTalesCrew:

    return TrekTalesCrew(
        **kwargs
    )


# ============================================================
# MODULE EXPORTS
# ============================================================

__all__ = [
    "TrekTalesCrew",
    "create_crew",
]
