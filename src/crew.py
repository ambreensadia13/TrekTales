from crewai import Crew, Process

from .agents import create_agents
from .tasks import create_tasks


class TrekTalesCrew:
    """
    Main TrekTales multi-agent crew.

    The crew contains eight specialized agents:
        1. Master Orchestrator
        2. Knowledge Agent
        3. Planner Agent
        4. Budget Agent
        5. Safety Agent
        6. Summarizer Agent
        7. Payment Agent
        8. Vision Agent
    """

    def __init__(self):
        # ----------------------------------------------------
        # CREATE AGENTS
        # ----------------------------------------------------

        self.agents = create_agents()

        # ----------------------------------------------------
        # CREATE TASKS
        # ----------------------------------------------------

        self.tasks = create_tasks(
            self.agents
        )

        # ----------------------------------------------------
        # CREATE CREW
        # ----------------------------------------------------

        self.crew = Crew(
            agents=list(self.agents.values()),
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False,
        )

    # ========================================================
    # RUN
    # ========================================================

    def run(self, request):
        """
        Run the TrekTales crew.

        Args:
            request: Dictionary containing trip information.

        Returns:
            CrewAI result.
        """

        if not isinstance(request, dict):
            raise TypeError(
                "TrekTalesCrew.run() expects a dictionary."
            )

        inputs = {
            "destination": request.get(
                "destination",
                "",
            ),
            "duration": request.get(
                "duration",
                1,
            ),
            "budget": request.get(
                "budget",
                "Moderate",
            ),
            "travelers": request.get(
                "travelers",
                1,
            ),
            "travel_style": request.get(
                "travel_style",
                "Mixed",
            ),
            "language": request.get(
                "language",
                "English",
            ),
            "interests": request.get(
                "interests",
                [],
            ),
            "starting_location": request.get(
                "starting_location",
                "",
            ),
            "evidence": request.get(
                "evidence",
                [],
            ),
        }

        # Convert interests to a clean string.
        if isinstance(
            inputs["interests"],
            list,
        ):
            inputs["interests"] = ", ".join(
                str(item)
                for item in inputs["interests"]
            )

        # Convert evidence into a readable string.
        if isinstance(
            inputs["evidence"],
            list,
        ):

            evidence_parts = []

            for item in inputs["evidence"]:

                if isinstance(item, dict):

                    evidence_parts.append(
                        str(item)
                    )

                else:

                    evidence_parts.append(
                        str(item)
                    )

            inputs["evidence"] = "\n".join(
                evidence_parts
            )

        else:

            inputs["evidence"] = str(
                inputs["evidence"]
            )

        # ----------------------------------------------------
        # EXECUTE CREW
        # ----------------------------------------------------

        return self.crew.kickoff(
            inputs=inputs
        )

    # ========================================================
    # KICKOFF ALIAS
    # ========================================================

    def kickoff(self, request):
        """
        Alias for run().
        """

        return self.run(request)
