"""LLM client helpers for the OpenRouter integration."""

from __future__ import annotations

import logging
from typing import Any, Mapping

import httpx

logger = logging.getLogger(__name__)

_OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"


class LLMError(RuntimeError):
    """Raised when the OpenRouter API responds with an error payload."""


def call_llm(
    prompt: str,
    *,
    model: str,
    openrouter_key: str,
    temperature: float = 0.0,
    timeout: float = 30.0,
    extra: Mapping[str, Any] | None = None,
) -> str:
    """Call OpenRouter with the provided prompt and return the text response."""

    if not openrouter_key:
        raise ValueError("OpenRouter API key is required")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful research assistant."},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
    }

    headers = {
        "Authorization": f"Bearer {openrouter_key}",
        "Content-Type": "application/json",
        "X-Title": "DeepResearchCLI",
    }

    logger.info(
        "OpenRouter call requested",
        extra={
            "model": model,
            "temperature": temperature,
            "timeout": timeout,
            "meta": dict(extra or {}),
        },
    )

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(_OPENROUTER_ENDPOINT, json=payload, headers=headers)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise LLMError(f"OpenRouter request failed: {exc}") from exc

    data = response.json()
    choices = data.get("choices", [])
    if not choices:
        raise LLMError("OpenRouter response contains no choices")

    message = choices[0].get("message", {})
    content = message.get("content")
    if not content:
        raise LLMError("OpenRouter response missing message content")

    return content.strip()
