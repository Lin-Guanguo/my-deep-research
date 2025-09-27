"""Entry point for the Deep Research CLI demo."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> None:
    """Placeholder CLI launcher.

    Stage 0 focuses on defining the human review contract; the actual LangGraph
    execution will be implemented in Stage 1. For now we surface the CLI usage
    expectations documented in `docs/human-review-cli.md`.
    """

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--show-review-help",
        action="store_true",
        help="Print human review workflow instructions and exit.",
    )
    args = parser.parse_args(argv)

    if args.show_review_help:
        help_path = PROJECT_ROOT / "docs" / "human-review-cli.md"
        sys.stdout.write(help_path.read_text(encoding="utf-8"))
        sys.stdout.write("\n")
        return

    raise NotImplementedError("CLI runner not implemented yet; see docs/human-review-cli.md")


if __name__ == "__main__":
    main()
