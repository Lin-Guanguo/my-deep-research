"""Tests for CLI planner workflow."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from src.models.plan import Plan
from src.graph.state import GraphState


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

        def fake_build_graph(cfg, *, planner_agent=None, review_handler=None):
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


if __name__ == "__main__":
    unittest.main()
