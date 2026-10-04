from crewai import Crew, Process

from .agents import create_agents
from .tasks import create_tasks


class TrekTalesCrew:
    """Main CrewAI workflow for TrekTales."""

    def __init__(self):
        self.agents = create_agents()
        self.tasks = create_tasks(self.agents)

        # create_tasks() already returns the tasks in the correct order.
        # Keep all returned tasks so CrewAI always has valid tasks.
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
            interests = ", ".join(
                str(item).strip()
                for item in interests
                if str(item).strip()
            )
        else:
            interests = str(interests).strip()

        evidence = request.get("evidence", "")

        if isinstance(evidence, list):
            evidence = "\n\n".join(
                str(item).strip()
                for item in evidence
                if str(item).strip()
            )
        else:
            evidence = str(evidence).strip()

        # Keep the input compact.
        inputs = {
            "request": (
                f"Destination: {str(request.get('destination', '')).strip()}\n"
                f"Duration: {str(request.get('duration', '')).strip()}\n"
                f"Traveler type: {str(request.get('traveler_type', '')).strip()}\n"
                f"Interests: {interests}\n"
                f"Budget: {str(request.get('budget', '')).strip()}\n"
                f"Language: {str(request.get('language', 'English')).strip()}"
            ),

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

            # Used by the sequential task context.
            "knowledge_output": "",
            "planner_output": "",
            "budget_output": "",
            "safety_output": "",
        }

        return self.crew.kickoff(inputs=inputs)

    def kickoff(self, request):
        """Compatibility alias for code that calls kickoff()."""
        return self.run(request)
