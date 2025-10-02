"""Tests for LangGraph builder."""

from __future__ import annotations

import unittest

from src.agents.researcher import ResearchContext, ResearcherResult
from src.config.configuration import AppConfig
from src.graph.builder import build_graph, initial_state
from src.models.plan import Plan, ResearchNote, StepStatus


class DummyPlanner:
    def __init__(self, plan: Plan) -> None:
        self.plan = plan
        self.calls: list[tuple[str, str | None, str | None]] = []

    def generate_plan(self, topic: str, *, locale: str, context: str | None = None, extra_meta=None) -> Plan:
        self.calls.append((topic, locale, context))
        return self.plan


class DummyResearcher:
    def __init__(self) -> None:
        self.calls: list[ResearchContext] = []

    def run_step(self, context: ResearchContext) -> ResearcherResult:  # noqa: ANN001
        self.calls.append(context)
        step = context.step
        topic = context.topic
        locale = context.locale
        note = ResearchNote(
            source="https://example.com",
            claim=f"Insight for {step.title}",
            evidence=None,
        )
        return ResearcherResult(
            query=f"{topic} | {step.title}",
            notes=[note],
            references=[note.source],
            duration_seconds=0.25,
            total_results=1,
        )


class GraphBuilderTests(unittest.TestCase):
    def test_graph_runs_through_reporter(self) -> None:
        cfg = AppConfig()
        plan = Plan(
            topic="Test",
            goal="Check",
            steps=[
                {
                    "id": "step-1",
                    "title": "Run",
                    "step_type": "RESEARCH",
                    "expected_outcome": "Complete",
                }
            ],
            assumptions=[],
            risks=[],
        )
        dummy_planner = DummyPlanner(plan)

        def handler(state):
            return "ACCEPT_PLAN", ""

        dummy_researcher = DummyResearcher()

        graph = build_graph(
            cfg,
            planner_agent=dummy_planner,
            review_handler=handler,
            researcher_agent=dummy_researcher,
        )

        state = initial_state("Test Topic", locale="en-US", metadata={"context": "ctx"})
        result = graph.invoke(state.model_dump())

        self.assertIn("plan", result)
        self.assertEqual(result["plan"]["topic"], "Test")
        self.assertEqual(result["metadata"]["last_review_action"], "ACCEPT_PLAN")
        self.assertEqual(dummy_planner.calls, [("Test Topic", "en-US", "ctx")])
        self.assertEqual(len(dummy_researcher.calls), 1)
        context = dummy_researcher.calls[0]
        self.assertEqual(context.topic, "Test Topic")
        self.assertEqual(context.step.id, "step-1")
        self.assertEqual(context.locale, "en-US")
        self.assertEqual(
            result["plan"]["steps"][0]["status"],
            StepStatus.COMPLETED.value,
        )
        metrics = result["metadata"].get("researcher_metrics")
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics["total_calls"], 1)
        self.assertEqual(metrics["total_notes"], 1)
        summary = result["metadata"].get("reporter_summary")
        self.assertIsNotNone(summary)
        self.assertEqual(summary["total_notes"], 1)
        markdown = result["metadata"].get("report_markdown")
        assert markdown is not None
        assert "# Research Report" in markdown

    def test_request_changes_loops_back_to_planner(self) -> None:
        cfg = AppConfig()
        plan1 = Plan(
            topic="First",
            goal="First",
            steps=[
                {
                    "id": "step-1",
                    "title": "Initial",
                    "step_type": "RESEARCH",
                    "expected_outcome": "Collect",
                }
            ],
            assumptions=[],
            risks=[],
        )
        plan2 = Plan(
            topic="Second",
            goal="Second",
            steps=[
                {
                    "id": "step-1",
                    "title": "Replan",
                    "step_type": "RESEARCH",
                    "expected_outcome": "Update",
                }
            ],
            assumptions=[],
            risks=[],
        )

        dummy_planner = DummyPlanner(plan1)
        dummy_planner.plans = [plan1, plan2]
        dummy_planner.index = 0

        def generate_plan(topic: str, *, locale: str, context: str | None = None, extra_meta=None):
            plan_obj = dummy_planner.plans[dummy_planner.index]
            dummy_planner.index = min(dummy_planner.index + 1, len(dummy_planner.plans) - 1)
            dummy_planner.calls.append((topic, locale, context))
            return plan_obj

        dummy_planner.generate_plan = generate_plan  # type: ignore[assignment]

        def handler(state):
            if state.plan and state.plan.topic == "First":
                return "REQUEST_CHANGES", "Add more detail"
            return "ACCEPT_PLAN", ""

        dummy_researcher = DummyResearcher()

        graph = build_graph(
            cfg,
            planner_agent=dummy_planner,
            review_handler=handler,
            researcher_agent=dummy_researcher,
        )

        state = initial_state("Topic", locale="en-US", metadata={"context": "ctx"})
        result = graph.invoke(state.model_dump())

        self.assertEqual(dummy_planner.calls, [("Topic", "en-US", "ctx"), ("Topic", "en-US", "ctx\nReviewer feedback: Add more detail")])
        self.assertEqual(result["plan"]["topic"], "Second")
        self.assertEqual(result["metadata"].get("last_review_action"), "ACCEPT_PLAN")
        self.assertEqual(dummy_researcher.calls[0].topic, "Topic")
        metrics = result["metadata"].get("researcher_metrics")
        self.assertEqual(metrics["total_calls"], 1)
        summary = result["metadata"].get("reporter_summary")
        self.assertEqual(summary["total_notes"], 1)
        markdown = result["metadata"].get("report_markdown")
        assert markdown is not None


if __name__ == "__main__":
    unittest.main()
