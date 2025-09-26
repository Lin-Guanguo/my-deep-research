"""Web search abstraction for Deep Research."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Mapping, Sequence

logger = logging.getLogger(__name__)


class SearchError(RuntimeError):
    """Raised when the search provider returns an unrecoverable failure."""


def search_web(
    query: str,
    *,
    provider: str,
    max_results: int = 5,
    timeout: float = 10.0,
    params: Mapping[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Dispatch a search query to the configured provider and return results.

    Implementations should apply rate limiting and retries, then normalize the
    provider-specific payload into a list of {"title", "url", "snippet"} dicts.
    """

    logger.info(
        "Search requested", extra={
            "query": query,
            "provider": provider,
            "max_results": max_results,
            "timeout": timeout,
            "params": dict(params or {}),
        }
    )
    raise NotImplementedError("Search integration not implemented")


def normalize_results(raw_results: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Map provider-specific fields to the canonical result schema."""

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
