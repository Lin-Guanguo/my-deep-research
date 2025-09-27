"""Validation tests for sample planner outputs."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from src.models.plan import Plan, StepType


class PlannerSampleTests(unittest.TestCase):
    """Ensure bundled sample plans conform to the Plan schema."""

    SAMPLE_PATH = Path("samples/planner_plans.jsonl")

    def test_sample_file_exists(self) -> None:
        self.assertTrue(self.SAMPLE_PATH.exists(), "Planner sample file is missing")

    def test_each_sample_parses(self) -> None:
        with self.SAMPLE_PATH.open("r", encoding="utf-8") as handle:
            records = [line.strip() for line in handle if line.strip()]

        self.assertGreaterEqual(len(records), 2, "Expect at least two planner samples")

        for raw in records:
            payload = json.loads(raw)
            plan = Plan.model_validate(payload)

            self.assertGreaterEqual(len(plan.steps), 3, "Plan should contain multiple steps")
            for step in plan.steps:
                self.assertIsInstance(step.step_type, StepType)
                self.assertTrue(step.id.startswith("step-"))
                self.assertTrue(step.expected_outcome)

            self.assertIsNotNone(plan.metadata.locale)


if __name__ == "__main__":
    unittest.main()
