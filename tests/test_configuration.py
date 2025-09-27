"""Unit tests for configuration loading helpers."""

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from src.config.configuration import AppConfig, load_config


class LoadConfigTests(unittest.TestCase):
    """Verify that load_config merges settings.yaml and secret overrides."""

    def test_uses_defaults_when_files_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = load_config(
                settings_path=Path(tmpdir) / "missing-settings.yaml",
                secret_path=Path(tmpdir) / "missing-secret",
            )
            self.assertIsInstance(cfg, AppConfig)
            self.assertEqual(cfg.runtime.locale, "zh-CN")
            self.assertEqual(cfg.models.planner, "gpt-4o-mini")
            self.assertIsNone(cfg.api.openrouter_key)
            self.assertIsNone(cfg.observability.langsmith_project)

    def test_secret_overrides_api_and_observability(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "settings.yaml"
            secret_path = Path(tmpdir) / "secret"

            settings_path.write_text(
                textwrap.dedent(
                    """
                    runtime:
                      locale: en-US
                    models:
                      planner: qwen-2
                      temperature: 0.2
                    api:
                      openrouter_key: placeholder
                    observability:
                      langsmith_project: default-project
                    """
                ).strip(),
                encoding="utf-8",
            )

            secret_path.write_text(
                textwrap.dedent(
                    """
                    OPENROUTER_KEY=sk-secret
                    TAVILY_API_KEY=tvly-secret
                    LANGSMITH_PROJECT=overridden-project
                    LANGSMITH_API_KEY=lsm-secret
                    """
                ).strip(),
                encoding="utf-8",
            )

            cfg = load_config(settings_path=settings_path, secret_path=secret_path)

            self.assertEqual(cfg.runtime.locale, "en-US")
            self.assertEqual(cfg.models.planner, "qwen-2")
            self.assertEqual(cfg.models.temperature, 0.2)
            self.assertEqual(cfg.api.openrouter_key, "sk-secret")
            self.assertEqual(cfg.api.tavily_key, "tvly-secret")
            self.assertEqual(cfg.observability.langsmith_project, "overridden-project")
            self.assertEqual(cfg.observability.langsmith_api_key, "lsm-secret")


if __name__ == "__main__":
    unittest.main()
