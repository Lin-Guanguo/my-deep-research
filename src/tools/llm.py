"""LLM client helpers with shared logging and retry settings."""

from __future__ import annotations

import logging
from typing import Any, Mapping

logger = logging.getLogger(__name__)


def call_llm(
    prompt: str,
    *,
    model: str,
    temperature: float = 0.0,
    timeout: float = 30.0,
    extra: Mapping[str, Any] | None = None,
) -> str:
    """Call the configured LLM and return the raw text response.

    This placeholder only logs the request metadata; concrete integrations should
    add retry/timeout handling (e.g., using `tenacity`) and cost tracking.
    """

    logger.info(
        "LLM call requested", extra={
            "model": model,
            "temperature": temperature,
            "timeout": timeout,
            "meta": dict(extra or {}),
        }
    )
    raise NotImplementedError("LLM client not wired up yet")
