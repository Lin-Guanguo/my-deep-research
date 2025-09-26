"""Tavily search abstraction for Deep Research."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Mapping, Sequence

logger = logging.getLogger(__name__)


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
    """Dispatch a search query to Tavily and return normalized results.

    Implementations should apply rate limiting and retries, then normalize the
    payload into a list of {"title", "url", "snippet"} dicts.
    """

    logger.info(
        "Tavily search requested",
        extra={
            "query": query,
            "max_results": max_results,
            "timeout": timeout,
            "params": dict(params or {}),
        },
    )
    raise NotImplementedError("Tavily integration not implemented")


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
