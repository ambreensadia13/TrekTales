from crewai import Crew, Process

from .agents import create_agents
from .tasks import create_tasks


class TrekTalesCrew:
    """
    Main TrekTales multi-agent system.
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
        """

        if not isinstance(request, dict):
            raise TypeError(
                "request must be a dictionary."
            )

        interests = request.get(
            "interests",
            [],
        )

        if isinstance(interests, list):

            interests = ", ".join(
                str(item)
                for item in interests
            )

        evidence = request.get(
            "evidence",
            [],
        )

        if isinstance(evidence, list):

            evidence_text = "\n".join(
                str(item)
                for item in evidence
            )

        else:

            evidence_text = str(
                evidence
            )

        inputs = {
            "destination": str(
                request.get(
                    "destination",
                    "",
                )
            ),

            "starting_location": str(
                request.get(
                    "starting_location",
                    "",
                )
            ),

            "duration": request.get(
                "duration",
                1,
            ),

            "travelers": request.get(
                "travelers",
                1,
            ),

            "budget": str(
                request.get(
                    "budget",
                    "Moderate",
                )
            ),

            "travel_style": str(
                request.get(
                    "travel_style",
                    "Mixed",
                )
            ),

            "language": str(
                request.get(
                    "language",
                    "English",
                )
            ),

            "interests": interests,

            "evidence": evidence_text,
        }

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
