"""Planner agent implementation using OpenRouter and validated Plan schema."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from src.config.configuration import AppConfig
from src.models.plan import Plan
from src.tools.llm import LLMError, call_llm

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"
_SYSTEM_PROMPT_PATH = PROMPTS_DIR / "planner_system.txt"
_USER_TEMPLATE_PATH = PROMPTS_DIR / "planner_user.jinja"


@dataclass
class PlannerAgent:
    """Encapsulates the planner prompt generation and Plan parsing."""

    config: AppConfig

    def __post_init__(self) -> None:
        if not _SYSTEM_PROMPT_PATH.exists():
            raise FileNotFoundError(f"Missing system prompt at {_SYSTEM_PROMPT_PATH}")
        if not _USER_TEMPLATE_PATH.exists():
            raise FileNotFoundError(f"Missing user template at {_USER_TEMPLATE_PATH}")
        self._system_prompt = _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
        self._user_template = _USER_TEMPLATE_PATH.read_text(encoding="utf-8")

    def generate_plan(
        self,
        topic: str,
        *,
        locale: str,
        context: str | None = None,
        extra_meta: Dict[str, Any] | None = None,
    ) -> Plan:
        """Call OpenRouter with planner prompts and return a validated Plan."""

        cfg = self.config
        api_cfg = cfg.api
        if not api_cfg.openrouter_key:
            raise ValueError("OpenRouter key is required for planner agent")

        user_prompt = self._render_user_prompt(topic=topic, locale=locale, context=context)

        try:
            raw_response = call_llm(
                user_prompt,
                model=cfg.models.planner,
                openrouter_key=api_cfg.openrouter_key,
                temperature=cfg.models.temperature,
                timeout=60.0,
                extra={"topic": topic, "locale": locale} | (extra_meta or {}),
                system_prompt=self._system_prompt,
            )
        except LLMError:
            logger.exception("Planner LLM call failed", extra={"topic": topic, "locale": locale})
            raise

        try:
            plan = Plan.model_validate_json(raw_response)
        except json.JSONDecodeError:
            logger.error("Planner returned invalid JSON", extra={"response": raw_response})
            raise
        except Exception:
            logger.exception("Planner response failed schema validation")
            raise

        if not plan.metadata.locale:
            plan.metadata.locale = locale

        logger.info(
            "Planner generated plan",
            extra={
                "topic": topic,
                "steps": len(plan.steps),
                "locale": plan.metadata.locale,
            },
        )
        return plan

    def _render_user_prompt(self, *, topic: str, locale: str, context: str | None) -> str:
        return self._user_template.format(topic=topic, locale=locale, context=context or "")
