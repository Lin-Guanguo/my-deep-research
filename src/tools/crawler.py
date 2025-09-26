"""HTML fetching and readability helpers."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Article:
    """Normalized article payload after readability extraction."""

    url: str
    title: Optional[str]
    content: Optional[str]
    language: Optional[str]


def fetch_article(url: str, *, timeout: float = 12.0, use_readability: bool = True) -> Article:
    """Download and parse article content.

    Implementations should perform HTTP requests with timeout/retry controls,
    then apply readability/trafilatura extraction and populate the Article
    structure.
    """

    logger.info(
        "Fetching article", extra={"url": url, "timeout": timeout, "readability": use_readability}
    )
    raise NotImplementedError("Crawler not implemented yet")
