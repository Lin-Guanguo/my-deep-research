"""Tests for LangGraph builder."""

from __future__ import annotations

import unittest

from src.config.configuration import AppConfig
from src.graph.builder import build_graph, initial_state
from src.models.plan import Plan


class DummyPlanner:
    def __init__(self, plan: Plan) -> None:
        self.plan = plan
        self.calls: list[tuple[str, str | None, str | None]] = []

    def generate_plan(self, topic: str, *, locale: str, context: str | None = None, extra_meta=None) -> Plan:
        self.calls.append((topic, locale, context))
        return self.plan


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
        graph = build_graph(cfg, planner_agent=dummy_planner)

        state = initial_state("Test Topic", locale="en-US", metadata={"context": "ctx"})
        result = graph.invoke(state.model_dump())

        self.assertIn("plan", result)
        self.assertEqual(result["plan"]["topic"], "Test")
        self.assertTrue(result["metadata"]["awaiting_review"])
        self.assertEqual(dummy_planner.calls, [("Test Topic", "en-US", "ctx")])


if __name__ == "__main__":
    unittest.main()
