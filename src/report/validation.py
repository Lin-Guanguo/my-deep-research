"""Reporter-side helpers for validating research notes before rendering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from src.models.plan import ResearchNote
from pydantic import ValidationError


@dataclass
class ValidationIssue:
    """Represents a validation problem discovered in a research note."""

    index: int
    kind: str
    message: str


@dataclass
class LowConfidenceFlag:
    """Captures notes that fall below the reporter's confidence threshold."""

    index: int
    confidence: float
    claim: str


def normalize_notes(notes: Iterable[ResearchNote | dict]) -> List[ResearchNote]:
    """Convert incoming notes into `ResearchNote` instances."""

    normalized: List[ResearchNote] = []
    for item in notes:
        if isinstance(item, ResearchNote):
            normalized.append(item)
            continue

        payload = dict(item)
        try:
            normalized.append(ResearchNote(**payload))
        except ValidationError:
            normalized.append(ResearchNote.model_construct(**payload))
    return normalized


def validate_notes(
    notes: Sequence[ResearchNote | dict],
    *,
    low_confidence_threshold: float = 0.6,
) -> tuple[List[ResearchNote], List[ValidationIssue], List[LowConfidenceFlag]]:
    """Validate structured notes and surface citation/confidence issues.

    Returns a tuple of (normalized notes, blocking issues, low-confidence flags).
    Reporter implementations can refuse to render when blocking issues exist
    and surface low-confidence flags in the risk section or footnotes.
    """

    normalized = normalize_notes(notes)
    issues: List[ValidationIssue] = []
    low_confidence: List[LowConfidenceFlag] = []

    for idx, note in enumerate(normalized):
        source = note.source.strip() if note.source else ""
        if not source:
            issues.append(
                ValidationIssue(index=idx, kind="missing_source", message="note.source is empty")
            )

        claim = note.claim.strip() if note.claim else ""
        if not claim:
            issues.append(
                ValidationIssue(index=idx, kind="missing_claim", message="note.claim is empty")
            )

        if note.confidence is not None and note.confidence < low_confidence_threshold:
            low_confidence.append(
                LowConfidenceFlag(
                    index=idx,
                    confidence=note.confidence,
                    claim=note.claim,
                )
            )

    return normalized, issues, low_confidence


__all__ = [
    "ValidationIssue",
    "LowConfidenceFlag",
    "normalize_notes",
    "validate_notes",
]
