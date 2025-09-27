"""Tests for reporter note validation helpers."""

from __future__ import annotations

import unittest

from src.report.validation import (
    LowConfidenceFlag,
    ValidationIssue,
    normalize_notes,
    validate_notes,
)


class ReportValidationTests(unittest.TestCase):
    def test_normalize_accepts_dicts_and_models(self) -> None:
        notes, issues, flags = validate_notes(
            [
                {
                    "source": "https://example.com",
                    "claim": "Example claim",
                    "evidence": None,
                    "confidence": 0.9,
                    "todo": None,
                }
            ]
        )
        self.assertEqual(len(notes), 1)
        self.assertFalse(issues)
        self.assertFalse(flags)

    def test_missing_source_detected(self) -> None:
        _, issues, _ = validate_notes(
            [
                {
                    "source": " ",
                    "claim": "Claim without citation",
                    "evidence": None,
                    "confidence": 0.7,
                    "todo": None,
                }
            ]
        )
        self.assertEqual(len(issues), 1)
        self.assertIsInstance(issues[0], ValidationIssue)
        self.assertEqual(issues[0].kind, "missing_source")

    def test_low_confidence_flagged(self) -> None:
        _, _, flags = validate_notes(
            [
                {
                    "source": "https://example.com/1",
                    "claim": "Claim",
                    "confidence": 0.4,
                }
            ],
            low_confidence_threshold=0.6,
        )
        self.assertEqual(len(flags), 1)
        self.assertIsInstance(flags[0], LowConfidenceFlag)
        self.assertEqual(flags[0].confidence, 0.4)


if __name__ == "__main__":
    unittest.main()
