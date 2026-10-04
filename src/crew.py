from crewai import Crew, Process

from .agents import create_agents
from .tasks import create_tasks


class TrekTalesCrew:
    """Main CrewAI workflow for TrekTales."""

    def __init__(self):
        self.agents = create_agents()
        self.tasks = create_tasks(self.agents)

        # Only use the travel-planning tasks.
        # Payment and vision are handled separately by the application.
        travel_task_names = {
            "knowledge",
            "planner",
            "budget",
            "safety",
            "summarizer",
        }

        travel_tasks = [
            task
            for task in self.tasks
            if getattr(task, "name", None) in travel_task_names
        ]

        self.crew = Crew(
            agents=[
                self.agents["knowledge"],
                self.agents["planner"],
                self.agents["budget"],
                self.agents["safety"],
                self.agents["summarizer"],
            ],
            tasks=travel_tasks,
            process=Process.sequential,
            verbose=False,
        )

    def run(self, request):
        """Run the TrekTales travel-planning workflow."""

        if not isinstance(request, dict):
            raise TypeError("request must be a dictionary")

        interests = request.get("interests", [])

        if isinstance(interests, list):
            interests = ", ".join(
                str(item).strip()
                for item in interests
                if str(item).strip()
            )
        else:
            interests = str(interests)

        evidence = request.get("evidence", "")

        if isinstance(evidence, list):
            evidence = "\n".join(
                str(item).strip()
                for item in evidence
                if str(item).strip()
            )
        else:
            evidence = str(evidence)

        # Keep the request compact.
        inputs = {
            "destination": str(
                request.get("destination", "")
            ).strip(),

            "duration": str(
                request.get("duration", "")
            ).strip(),

            "traveler_type": str(
                request.get("traveler_type", "")
            ).strip(),

            "interests": interests,

            "budget": str(
                request.get("budget", "")
            ).strip(),

            "language": str(
                request.get("language", "English")
            ).strip(),

            "evidence": evidence,

            # These are kept for task compatibility.
            "knowledge_output": "",
            "planner_output": "",
            "budget_output": "",
            "safety_output": "",
        }

        return self.crew.kickoff(inputs=inputs)

    def kickoff(self, request):
        """Compatibility alias for kickoff()."""
        return self.run(request)
