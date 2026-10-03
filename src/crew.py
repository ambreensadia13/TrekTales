from crewai import Agent, Crew, Process

from .agents import (
    create_grok_llm,
    create_knowledge_agent,
    create_planner_agent,
    create_budget_agent,
    create_safety_agent,
    create_summarizer_agent,
    create_payment_agent,
    create_vision_agent,
)

from .tasks import create_tasks


class TrekTalesCrew:
    """
    TrekTales 8-agent CrewAI system.

    Agents:
    1. Master Orchestrator
    2. Knowledge Agent
    3. Planner Agent
    4. Budget Agent
    5. Safety Agent
    6. Summarizer Agent
    7. Payment Agent
    8. Vision Agent
    """

    def __init__(
        self,
        user_query: str,
        evidence_text: str,
        trip_days: int = 3,
    ):
        self.user_query = user_query
        self.evidence_text = evidence_text
        self.trip_days = trip_days

        self.llm = create_grok_llm()

        # -------------------------------------------------
        # SPECIALIST AGENTS
        # -------------------------------------------------

        self.knowledge_agent = create_knowledge_agent(
            self.llm
        )

        self.planner_agent = create_planner_agent(
            self.llm
        )

        self.budget_agent = create_budget_agent(
            self.llm
        )

        self.safety_agent = create_safety_agent(
            self.llm
        )

        self.summarizer_agent = create_summarizer_agent(
            self.llm
        )

        self.payment_agent = create_payment_agent(
            self.llm
        )

        self.vision_agent = create_vision_agent(
            self.llm
        )

        # -------------------------------------------------
        # MASTER ORCHESTRATOR
        # -------------------------------------------------

        self.master_agent = Agent(
            role="Master Orchestrator",
            goal=(
                "Coordinate the TrekTales specialist agents and ensure "
                "that the final tourism response is grounded in supplied "
                "knowledge-base evidence."
            ),
            backstory=(
                "You are the TrekTales project manager. "
                "You coordinate the Knowledge, Planner, Budget, Safety "
                "and Summarizer specialists. You enforce the rule that "
                "unsupported tourism facts must never be invented."
            ),
            llm=self.llm,
            allow_delegation=False,
            verbose=False,
        )

    def run(self):
        """
        Execute the tourism workflow.
        """

        tasks = create_tasks(
            knowledge_agent=self.knowledge_agent,
            planner_agent=self.planner_agent,
            budget_agent=self.budget_agent,
            safety_agent=self.safety_agent,
            summarizer_agent=self.summarizer_agent,
            user_query=self.user_query,
            evidence_text=self.evidence_text,
            trip_days=self.trip_days,
        )

        crew = Crew(
            agents=[
                self.master_agent,
                self.knowledge_agent,
                self.planner_agent,
                self.budget_agent,
                self.safety_agent,
                self.summarizer_agent,
            ],
            tasks=tasks,
            process=Process.sequential,
            verbose=False,
        )

        result = crew.kickoff()

        return result
