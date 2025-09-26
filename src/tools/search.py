"""Tavily search abstraction for Deep Research."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Mapping, Sequence

import httpx

logger = logging.getLogger(__name__)

_TAVILY_ENDPOINT = "https://api.tavily.com/search"


class SearchError(RuntimeError):
    """Raised when Tavily returns an unrecoverable failure."""


def search_web(
    query: str,
    *,
    tavily_key: str,
    max_results: int = 5,
    timeout: float = 10.0,
    params: Mapping[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Dispatch a search query to Tavily and return normalized results."""

    if not tavily_key:
        raise ValueError("Tavily API key is required")

    payload: Dict[str, Any] = {
        "api_key": tavily_key,
        "query": query,
        "max_results": max_results,
    }
    if params:
        payload.update(params)

    logger.info(
        "Tavily search requested",
        extra={
            "query": query,
            "max_results": max_results,
            "timeout": timeout,
        },
    )

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(_TAVILY_ENDPOINT, json=payload)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise SearchError(f"Tavily request failed: {exc}") from exc

    data = response.json()
    raw_results = data.get("results")
    if raw_results is None:
        raise SearchError("Tavily response missing 'results' field")

    return normalize_results(raw_results)


def normalize_results(raw_results: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Map Tavily fields to the canonical result schema."""

    normalized: List[Dict[str, Any]] = []
    for item in raw_results:
        normalized.append(
            {
                "title": str(item.get("title", "")),
                "url": str(item.get("url", "")),
                "snippet": str(item.get("snippet", "")),
            }
        )
    return normalized
