"""Tests for the Researcher agent Tavily integration."""

from __future__ import annotations

import unittest

from src.agents.researcher import ResearchContext, ResearcherAgent, ResearcherError
from src.config.configuration import AppConfig, ApiConfig
from src.models.plan import PlanStep


class ResearcherAgentTests(unittest.TestCase):
    def _make_config(self, *, tavily_key: str | None) -> AppConfig:
        cfg = AppConfig()
        cfg.api = ApiConfig(openrouter_key="dummy", tavily_key=tavily_key)
        return cfg

    def test_run_step_uses_search_callable(self) -> None:
        captured = {}

        def fake_search(query: str, api_key: str, max_results: int, timeout: float):
            captured.update(
                {
                    "query": query,
                    "api_key": api_key,
                    "max_results": max_results,
                    "timeout": timeout,
                }
            )
            return [
                {
                    "title": "LangGraph overview",
                    "url": "https://example.com/langgraph",
                    "snippet": "LangGraph enables orchestrating agents.",
                },
                {
                    "title": "LangGraph overview",  # duplicate URL should be skipped
                    "url": "https://example.com/langgraph",
                    "snippet": "duplicate",
                },
            ]

        config = self._make_config(tavily_key="tvly-key")
        agent = ResearcherAgent(config, search_callable=fake_search)

        step = PlanStep(
            id="step-1",
            title="Discover LangGraph",
            step_type="RESEARCH",
            expected_outcome="Summarize LangGraph capabilities",
        )

        context = ResearchContext(
            topic="LangGraph best practices",
            locale="en-US",
            step=step,
            max_results=agent._config.search.max_queries,
            timeout_seconds=agent._config.search.timeout_seconds,
        )

        result = agent.run_step(context)

        self.assertEqual(result.query, "LangGraph best practices | Discover LangGraph | en-US")
        self.assertEqual(len(result.notes), 1)
        self.assertEqual(result.notes[0].source, "https://example.com/langgraph")
        self.assertEqual(captured["api_key"], "tvly-key")
        self.assertGreaterEqual(captured["max_results"], 1)
        self.assertGreaterEqual(captured["timeout"], 1.0)
        self.assertIsNotNone(result.duration_seconds)
        self.assertGreaterEqual(result.total_results, 1)
        self.assertGreaterEqual(result.notes[0].confidence or 0.0, 0.6)
        self.assertEqual(result.applied_max_results, agent._config.search.max_queries)
        self.assertEqual(result.applied_max_notes, min(3, agent._config.search.max_queries))
        self.assertIsNone(result.degradation_mode)

    def test_missing_api_key_raises(self) -> None:
        config = self._make_config(tavily_key=None)
        agent = ResearcherAgent(config, search_callable=lambda *args, **kwargs: [])

        step = PlanStep(
            id="step-1",
            title="Check",
            step_type="RESEARCH",
            expected_outcome="Outcome",
        )

        with self.assertRaises(ResearcherError):
            agent.run_step(
                ResearchContext(
                    topic="Topic",
                    locale="en-US",
                    step=step,
                    max_results=1,
                    timeout_seconds=5.0,
                )
            )

    def test_no_results_raises(self) -> None:
        config = self._make_config(tavily_key="tvly")
        agent = ResearcherAgent(config, search_callable=lambda *args, **kwargs: [])

        step = PlanStep(
            id="step-1",
            title="Check",
            step_type="RESEARCH",
            expected_outcome="Outcome",
        )

        with self.assertRaises(ResearcherError):
            agent.run_step(
                ResearchContext(
                    topic="Topic",
                    locale="en-US",
                    step=step,
                    max_results=2,
                    timeout_seconds=5.0,
                )
            )

    def test_multiple_results_returns_limited_notes(self) -> None:
        config = self._make_config(tavily_key="tvly")

        def fake_search(*args, **kwargs):
            return [
                {
                    "title": "LangGraph tutorial",
                    "url": f"https://example.com/item-{idx}",
                    "snippet": "Detailed walkthrough of LangGraph pipelines.",
                }
                for idx in range(10)
            ]

        agent = ResearcherAgent(config, search_callable=fake_search)

        step = PlanStep(
            id="step-2",
            title="Enumerate Best Practices",
            step_type="RESEARCH",
            expected_outcome="List actionable guidance",
        )

        result = agent.run_step(
            ResearchContext(
                topic="LangGraph",
                locale="en-US",
                step=step,
                max_results=agent._config.search.max_queries,
                timeout_seconds=agent._config.search.timeout_seconds,
            )
        )

        self.assertLessEqual(len(result.notes), 3)
        self.assertEqual(len(result.notes), len(result.references))
        self.assertTrue(all(note.confidence and note.confidence >= 0.6 for note in result.notes))
        self.assertIsNone(result.degradation_mode)

    def test_max_notes_override_limits_output(self) -> None:
        config = self._make_config(tavily_key="tvly")

        def fake_search(*args, **kwargs):
            return [
                {
                    "title": f"Result {idx}",
                    "url": f"https://example.com/result-{idx}",
                    "snippet": "Details",
                }
                for idx in range(5)
            ]

        agent = ResearcherAgent(config, search_callable=fake_search)

        step = PlanStep(
            id="step-3",
            title="Collect references",
            step_type="RESEARCH",
            expected_outcome="Obtain citations",
        )

        context = ResearchContext(
            topic="LangGraph",
            locale="en-US",
            step=step,
            max_results=5,
            timeout_seconds=agent._config.search.timeout_seconds,
            max_notes=2,
        )

        result = agent.run_step(context)
        self.assertEqual(len(result.notes), 2)
        self.assertEqual(result.applied_max_notes, 2)

    def test_budget_degradation_applies_limits(self) -> None:
        config = self._make_config(tavily_key="tvly")

        def fake_search(*args, **kwargs):
            return [
                {
                    "title": f"Data point {idx}",
                    "url": f"https://example.com/data-{idx}",
                    "snippet": "Excerpt",
                }
                for idx in range(4)
            ]

        agent = ResearcherAgent(config, search_callable=fake_search)

        step = PlanStep(
            id="step-4",
            title="Budgeted lookup",
            step_type="RESEARCH",
            expected_outcome="Collect minimal evidence",
        )

        context = ResearchContext(
            topic="LangGraph",
            locale="en-US",
            step=step,
            max_results=4,
            timeout_seconds=agent._config.search.timeout_seconds,
            budget_tokens_remaining=200,
            budget_cost_limit=0.5,
            degradation_hint="conservative",
        )

        result = agent.run_step(context)

        self.assertLessEqual(result.applied_max_results, 2)
        self.assertLessEqual(result.applied_max_notes, 1)
        self.assertIn("budget", result.degradation_mode or "")
        self.assertIn("conservative", result.degradation_mode or "")
        self.assertGreaterEqual(len(result.notes), 1)


if __name__ == "__main__":
    unittest.main()
