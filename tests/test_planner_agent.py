"""Tests for PlannerAgent."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from src.agents.planner import PlannerAgent
from src.config.configuration import AppConfig, ApiConfig, ModelConfig
from src.models.plan import Plan
from pydantic import ValidationError


class PlannerAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        model_cfg = ModelConfig(planner="gpt-test", researcher="gpt-test", reporter="gpt-test")
        api_cfg = ApiConfig(openrouter_key="dummy", tavily_key="tvly")
        self.app_cfg = AppConfig(models=model_cfg, api=api_cfg)
        self.agent = PlannerAgent(self.app_cfg)

    @patch("src.agents.planner.call_llm")
    def test_generate_plan_success(self, mock_call_llm) -> None:
        sample_plan = Plan(
            topic="Sample",
            goal="Goal",
            steps=[
                {
                    "id": "step-1",
                    "title": "Test",
                    "step_type": "RESEARCH",
                    "expected_outcome": "Result",
                }
            ],
            assumptions=[],
            risks=[],
        )
        payload = sample_plan.model_dump_json()
        mock_call_llm.return_value = payload

        plan = self.agent.generate_plan("Sample", locale="en-US")
        self.assertEqual(plan.topic, "Sample")
        mock_call_llm.assert_called_once()

    @patch("src.agents.planner.call_llm")
    def test_generate_plan_invalid_json(self, mock_call_llm) -> None:
        mock_call_llm.return_value = "not-json"

        with self.assertRaises(ValidationError):
            self.agent.generate_plan("Sample", locale="en-US")

    def test_missing_api_key_raises(self) -> None:
        cfg = AppConfig()
        agent = PlannerAgent(cfg)
        with self.assertRaises(ValueError):
            agent.generate_plan("Sample", locale="en-US")


if __name__ == "__main__":
    unittest.main()
