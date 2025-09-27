"""Tests for CLI planner workflow."""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.models.plan import Plan


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
        plan_payload = plan.model_dump()

        graph_stub = SimpleNamespace()
        graph_stub.invoke = lambda state: {"plan": plan_payload, "metadata": {}}
        mock_build_graph.return_value = graph_stub

        from scripts import run_cli

        run_cli.main(["--question", "What?", "--auto-accept", "--no-store"])

        mock_display.assert_called_once()
        mock_summary.assert_called_once()
        mock_store.assert_not_called()


if __name__ == "__main__":
    unittest.main()
