from __future__ import annotations

from crewai import Crew, Process

from .agents import create_agents
from .citations import evidence_to_prompt, format_citations
from .config import MAX_TRIP_DAYS
from .tasks import create_tasks


class TrekTalesCrew:
    def __init__(self):
        self.agents = create_agents()
        self.tasks = create_tasks(self.agents)
        if not self.tasks:
            raise RuntimeError("No TrekTales tasks were created.")

        self.crew = Crew(
            agents=list(self.agents.values()),
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False,
        )

    @staticmethod
    def _text_list(value) -> str:
        if isinstance(value, (list, tuple, set)):
            return ", ".join(str(x).strip() for x in value if str(x).strip())
        return str(value or "").strip()

    @staticmethod
    def _safe_days(value, default: int = 1) -> int:
        try:
            days = int(value)
        except (TypeError, ValueError):
            days = default
        return max(1, min(days, MAX_TRIP_DAYS))

    def run(self, request: dict):
        if not isinstance(request, dict):
            raise TypeError("request must be a dictionary")

        requested_days = self._safe_days(request.get("requested_days", request.get("duration", 1)))
        accessible_days = self._safe_days(request.get("accessible_days", 1))
        accessible_days = min(accessible_days, requested_days)

        evidence = request.get("evidence") or []
        if not isinstance(evidence, list):
            evidence = []

        source_manifest = format_citations(evidence)
        source_manifest_text = "\n".join(
            f"- {item['source']} | page {item['page']} | {item['department']}"
            for item in source_manifest
        ) or "- No sources retrieved"

        inputs = {
            "destination": str(request.get("destination", "")).strip(),
            "starting_location": str(request.get("starting_location", "")).strip(),
            "requested_days": requested_days,
            "accessible_days": accessible_days,
            "duration": requested_days,
            "travelers": request.get("travelers", 1),
            "traveler_type": str(request.get("traveler_type", "")).strip(),
            "travel_style": str(request.get("travel_style", "")).strip(),
            "interests": self._text_list(request.get("interests", "")),
            "budget": str(request.get("budget", "")).strip(),
            "language": str(request.get("language", "English")).strip(),
            "evidence": evidence_to_prompt(evidence),
            "source_manifest": source_manifest_text,
            "knowledge_output": "",
            "planner_output": "",
            "budget_output": "",
            "safety_output": "",
        }

        return self.crew.kickoff(inputs=inputs)

    def kickoff(self, request: dict):
        return self.run(request)
