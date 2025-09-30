"""Tests for CLI planner workflow."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.graph.state import GraphState
from src.models.plan import Plan
from src.models.persistence import PlanRunRecord, ReviewAction, ReviewLogEntry


class CliTests(unittest.TestCase):
    @patch("scripts.run_cli._store_plan")
    @patch("scripts.run_cli._emit_summary")
    @patch("scripts.run_cli._display_plan")
    @patch("scripts.run_cli.build_graph")
    @patch("scripts.run_cli.load_config")
    def test_auto_accept_flow(self, mock_load_config, mock_build_graph, mock_display, mock_summary, mock_store) -> None:
        from src.config.configuration import AppConfig, ApiConfig, ModelConfig

        model_cfg = ModelConfig(planner="gpt-test", researcher="gpt-test", reporter="gpt-test")
        api_cfg = ApiConfig(openrouter_key="dummy", tavily_key="tvly")
        config = AppConfig(models=model_cfg, api=api_cfg)
        mock_load_config.return_value = config

        plan = Plan(
            topic="Test",
            goal="Goal",
            steps=[
                {
                    "id": "step-1",
                    "title": "Step",
                    "step_type": "RESEARCH",
                    "expected_outcome": "Outcome",
                }
            ],
            assumptions=[],
            risks=[],
        )
        plan_payload = plan

        captured_handler = {}

        def fake_build_graph(
            cfg,
            *,
            planner_agent=None,
            review_handler=None,
            researcher_agent=None,
        ):
            captured_handler["handler"] = review_handler

            class Stub:
                def invoke(self, state):
                    graph_state = GraphState(**state)
                    graph_state.plan = plan_payload
                    if review_handler:
                        review_handler(graph_state)
                    return {
                        "plan": plan_payload.model_dump(),
                        "metadata": {"last_review_action": "ACCEPT_PLAN"},
                    }

            return Stub()

        mock_build_graph.side_effect = fake_build_graph

        from scripts import run_cli

        run_cli.main(["--question", "What?", "--auto-accept", "--no-store"])

        mock_display.assert_called_once()
        mock_summary.assert_called_once()
        mock_store.assert_not_called()
        assert captured_handler["handler"] is not None

    def test_store_plan_persists_record(self) -> None:
        from scripts import run_cli

        plan = Plan(
            topic="Persist Test",
            goal="Ensure persistence",
            steps=[
                {
                    "id": "step-1",
                    "title": "Verify",
                    "step_type": "RESEARCH",
                    "expected_outcome": "validation",
                }
            ],
            assumptions=[],
            risks=[],
        )

        review_entries = [
            ReviewLogEntry(attempt=1, action=ReviewAction.ACCEPT_PLAN, feedback="")
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            original_dir = run_cli.PLANS_DIR
            run_cli.PLANS_DIR = tmp_path
            try:
                run_cli._store_plan(
                    question="What is LangGraph?",
                    locale="en-US",
                    context="",
                    plan=plan,
                    review_log=review_entries,
                )
            finally:
                run_cli.PLANS_DIR = original_dir

            output_path = tmp_path / "plans.jsonl"
            self.assertTrue(output_path.exists())

            content = output_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(content), 1)
            record = PlanRunRecord.model_validate_json(content[0])
            self.assertEqual(record.question, "What is LangGraph?")
            self.assertEqual(record.locale, "en-US")
            self.assertEqual(record.review_log[0].action, ReviewAction.ACCEPT_PLAN)
            self.assertIsNone(record.telemetry)


if __name__ == "__main__":
    unittest.main()
