"""Researcher agent that enriches plan steps via Tavily search."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Callable, Iterable, List, Sequence

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
    duration_seconds: float | None = None
    total_results: int = 0
    applied_max_results: int | None = None
    applied_max_notes: int | None = None
    degradation_mode: str | None = None


@dataclass
class ResearchContext:
    """Context bundle passed to the Researcher for each execution."""

    topic: str
    locale: str
    step: PlanStep
    max_results: int
    timeout_seconds: float
    max_notes: int | None = None
    scratchpad: Sequence[ResearchNote] = ()
    prior_notes: Sequence[ResearchNote] = ()
    budget_tokens_remaining: int | None = None
    budget_cost_limit: float | None = None
    degradation_hint: str | None = None


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

    def run_step(self, context: ResearchContext) -> ResearcherResult:
        """Execute a single plan step and return captured notes and references."""

        api_key = self._config.api.tavily_key
        if not api_key:
            raise ResearcherError("Missing Tavily API key; cannot execute research step")

        max_results = max(1, context.max_results)
        timeout = max(1.0, float(context.timeout_seconds))

        effective_max_results = max_results
        effective_max_notes = context.max_notes or min(3, max_results)
        degradation_mode = _resolve_degradation_mode(context)

        if degradation_mode:
            if "budget" in degradation_mode:
                effective_max_results = min(effective_max_results, 2)
                effective_max_notes = min(effective_max_notes, 1)
            if "conservative" in degradation_mode:
                effective_max_results = min(effective_max_results, 2)
                effective_max_notes = min(effective_max_notes, 1)
            if "aggressive" in degradation_mode:
                effective_max_results = max(1, effective_max_results // 2)
                effective_max_notes = max(1, effective_max_notes // 2)

        query = self._build_query(
            topic=context.topic,
            step=context.step,
            locale=context.locale,
        )
        search_fn = self._search_callable or _default_search_callable

        started_at = perf_counter()
        try:
            results = search_fn(query, api_key, max_results, timeout)
        except SearchError as exc:
            raise ResearcherError(str(exc)) from exc
        duration = perf_counter() - started_at

        notes, references = self._extract_notes(
            context.step,
            results,
            max_notes=effective_max_notes,
        )
        if not notes:
            raise ResearcherError("Tavily returned no usable results for this step")

        return ResearcherResult(
            query=query,
            notes=notes,
            references=references,
            duration_seconds=duration,
            total_results=len(results),
            applied_max_results=effective_max_results,
            applied_max_notes=effective_max_notes,
            degradation_mode=degradation_mode,
        )

    def _build_query(self, *, topic: str, step: PlanStep, locale: str) -> str:
        components = [topic.strip(), step.title.strip()]
        if locale:
            components.append(locale.strip())
        return " | ".join(filter(None, components))

    def _iter_candidates(self, results: Iterable[dict]) -> Iterable[dict]:
        return results

    def _extract_notes(
        self,
        step: PlanStep,
        results: Sequence[dict],
        *,
        max_notes: int,
    ) -> tuple[List[ResearchNote], List[str]]:
        notes: List[ResearchNote] = []
        references: List[str] = []
        seen_urls: set[str] = set()

        for item in self._iter_candidates(results):
            if len(notes) >= max_notes:
                break

            url = str(item.get("url", "")).strip()
            title = str(item.get("title", "")).strip()
            snippet = str(item.get("snippet", "")).strip()

            if not url or url in seen_urls:
                continue

            seen_urls.add(url)
            confidence = self._estimate_confidence(step, title=title, snippet=snippet)
            note = ResearchNote(
                source=url,
                claim=title or step.expected_outcome,
                evidence=snippet or None,
                confidence=confidence,
            )
            notes.append(note)
            references.append(url)

        return notes, references

    def _estimate_confidence(self, step: PlanStep, *, title: str, snippet: str) -> float:
        base = 0.6
        if snippet:
            base += 0.15
            if len(snippet) > 120:
                base += 0.05
        if title:
            title_lower = title.lower()
            keywords = self._keywords_for_step(step)
            if any(token in title_lower for token in keywords):
                base += 0.05
        return max(0.5, min(base, 0.95))

    def _keywords_for_step(self, step: PlanStep) -> List[str]:
        tokens = []
        for text in (step.title, step.expected_outcome):
            if not text:
                continue
            tokens.extend(word.lower() for word in text.split() if len(word) > 3)
        return tokens


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


def _resolve_degradation_mode(context: ResearchContext) -> str | None:
    modes: list[str] = []
    if context.degradation_hint:
        modes.append(context.degradation_hint)
    if context.budget_tokens_remaining is not None and context.budget_tokens_remaining < 500:
        modes.append("budget")
    if context.budget_cost_limit is not None and context.budget_cost_limit < 1.0:
        if "budget" not in modes:
            modes.append("budget")
    if not modes:
        return None
    # Deduplicate while preserving order
    seen: set[str] = set()
    ordered: list[str] = []
    for mode in modes:
        if mode not in seen:
            seen.add(mode)
            ordered.append(mode)
    return ",".join(ordered)
