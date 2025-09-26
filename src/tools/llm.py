"""LLM client helpers for the OpenRouter integration."""

from __future__ import annotations

import logging
from typing import Any, Mapping

logger = logging.getLogger(__name__)


def call_llm(
    prompt: str,
    *,
    model: str,
    openrouter_key: str,
    temperature: float = 0.0,
    timeout: float = 30.0,
    extra: Mapping[str, Any] | None = None,
) -> str:
    """Call OpenRouter with the provided prompt and return the raw text response.

    This placeholder logs request metadata; real implementations should add
    retry/timeout handling (e.g., via `tenacity`) and cost tracking before
    performing the HTTP call against the OpenRouter API.
    """

    logger.info(
        "OpenRouter call requested",
        extra={
            "model": model,
            "temperature": temperature,
            "timeout": timeout,
            "meta": dict(extra or {}),
        },
    )
    raise NotImplementedError("OpenRouter client not wired up yet")
