from crewai import Crew, Process

from .agents import create_agents
from .tasks import create_tasks


class TrekTalesCrew:
    """Main CrewAI workflow for TrekTales."""

    def __init__(self):
        self.agents = create_agents()
        self.tasks = create_tasks(self.agents)

        self.crew = Crew(
            agents=list(self.agents.values()),
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False,
        )

    def run(self, request):
        """Run the TrekTales CrewAI workflow."""

        if not isinstance(request, dict):
            raise TypeError("request must be a dictionary")

        interests = request.get("interests", [])
        if isinstance(interests, list):
            interests = ", ".join(str(item) for item in interests)

        evidence = request.get("evidence", "")
        if isinstance(evidence, list):
            evidence = "\n\n".join(str(item) for item in evidence)

        inputs = {
            "request": str(request),
            "destination": str(request.get("destination", "")),
            "duration": str(request.get("duration", "")),
            "traveler_type": str(request.get("traveler_type", "")),
            "interests": str(interests),
            "budget": str(request.get("budget", "")),
            "language": str(request.get("language", "English")),
            "evidence": str(evidence),
            "knowledge_output": "",
            "planner_output": "",
            "budget_output": "",
            "safety_output": "",
        }

        return self.crew.kickoff(inputs=inputs)

    def kickoff(self, request):
        """Compatibility alias for code that calls kickoff()."""
        return self.run(request)
