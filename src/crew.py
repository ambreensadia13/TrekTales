```python
from crewai import Crew, Process

from .agents import create_agents
from .tasks import create_tasks


class TrekTalesCrew:
    """Main CrewAI workflow for TrekTales travel planning."""

    def __init__(self):
        # Create the agents.
        self.agents = create_agents()

        # Create the five travel-planning tasks.
        self.tasks = create_tasks(self.agents)

        # Make sure the workflow has tasks before creating the Crew.
        if not self.tasks:
            raise RuntimeError(
                "TrekTales could not create any travel-planning tasks."
            )

        # Create the CrewAI workflow.
        self.crew = Crew(
            agents=list(self.agents.values()),
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False,
        )

    def run(self, request):
        """Run the TrekTales travel-planning workflow."""

        if not isinstance(request, dict):
            raise TypeError("request must be a dictionary")

        # -----------------------------------------------------
        # Normalize interests
        # -----------------------------------------------------
        interests = request.get("interests", "")

        if isinstance(interests, list):
            interests = ", ".join(
                str(item).strip()
                for item in interests
                if str(item).strip()
            )
        else:
            interests = str(interests).strip()

        # -----------------------------------------------------
        # Normalize retrieved knowledge
        # -----------------------------------------------------
        evidence = request.get("evidence", "")

        if isinstance(evidence, list):
            evidence = "\n\n".join(
                str(item).strip()
                for item in evidence
                if str(item).strip()
            )
        else:
            evidence = str(evidence).strip()

        # -----------------------------------------------------
        # Keep the LLM input compact
        # -----------------------------------------------------
        destination = str(
            request.get("destination", "")
        ).strip()

        duration = str(
            request.get("duration", "")
        ).strip()

        traveler_type = str(
            request.get("traveler_type", "")
        ).strip()

        budget = str(
            request.get("budget", "")
        ).strip()

        language = str(
            request.get("language", "English")
        ).strip()

        inputs = {
            "destination": destination,
            "duration": duration,
            "traveler_type": traveler_type,
            "interests": interests,
            "budget": budget,
            "language": language,
            "evidence": evidence,

            # These are populated by CrewAI task context.
            "knowledge_output": "",
            "planner_output": "",
            "budget_output": "",
            "safety_output": "",
        }

        # -----------------------------------------------------
        # Run CrewAI
        # -----------------------------------------------------
        return self.crew.kickoff(inputs=inputs)

    def kickoff(self, request):
        """Compatibility alias for code that calls kickoff()."""
        return self.run(request)
```
