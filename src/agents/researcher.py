"""Researcher agent that enriches plan steps via Tavily search."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List

from src.config.configuration import AppConfig
from src.models.plan import PlanStep, ResearchNote
from src.tools.search import SearchError, search_web


class ResearcherError(RuntimeError):
    """Raised when the Researcher agent cannot complete a step."""


@dataclass
class ResearcherResult:
    """Outcome data returned by the Researcher after executing a step."""

    query: str
    notes: List[ResearchNote]
    references: List[str]


class ResearcherAgent:
    """Minimal Researcher that uses Tavily to gather supporting evidence."""

    def __init__(
        self,
        config: AppConfig,
        *,
        search_callable: Callable[[str, str, int, float], List[dict]] | None = None,
    ) -> None:
        self._config = config
        self._search_callable = search_callable

    def run_step(self, *, topic: str, step: PlanStep, locale: str) -> ResearcherResult:
        """Execute a single plan step and return captured notes and references."""

        api_key = self._config.api.tavily_key
        if not api_key:
            raise ResearcherError("Missing Tavily API key; cannot execute research step")

        max_results = max(1, self._config.search.max_queries)
        timeout = max(1.0, float(self._config.search.timeout_seconds))

        query = self._build_query(topic=topic, step=step, locale=locale)
        search_fn = self._search_callable or _default_search_callable

        try:
            results = search_fn(query, api_key, max_results, timeout)
        except SearchError as exc:
            raise ResearcherError(str(exc)) from exc

        notes: List[ResearchNote] = []
        references: List[str] = []

        for item in self._iter_candidates(results):
            url = item.get("url", "").strip()
            title = item.get("title", "").strip()
            snippet = item.get("snippet", "").strip()
            if not url:
                continue
            note = ResearchNote(
                source=url,
                claim=title or step.expected_outcome,
                evidence=snippet or None,
            )
            notes.append(note)
            references.append(url)
            break  # minimal implementation captures the first useful hit

        if not notes:
            raise ResearcherError("Tavily returned no usable results for this step")

        return ResearcherResult(query=query, notes=notes, references=references)

    def _build_query(self, *, topic: str, step: PlanStep, locale: str) -> str:
        components = [topic.strip(), step.title.strip()]
        if locale:
            components.append(locale.strip())
        return " | ".join(filter(None, components))

    def _iter_candidates(self, results: Iterable[dict]) -> Iterable[dict]:
        return results


def _default_search_callable(
    query: str,
    api_key: str,
    max_results: int,
    timeout: float,
) -> List[dict]:
    return search_web(
        query,
        tavily_key=api_key,
        max_results=max_results,
        timeout=timeout,
    )
