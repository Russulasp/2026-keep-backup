from __future__ import annotations

import argparse
from pathlib import Path


# NOTE:
# - Constant names express behavior clearly.
# - String values are kept stable to avoid changing external entry points.
MODE_BACKUP = "backup"
MODE_SMOKE_KEEP = "smoke-playwright"
MODE_SMOKE_FIXTURE = "smoke-playwright-fixture"
MODE_SMOKE_LOGIN = "smoke-playwright-login"

# Backward-compatible aliases for existing imports.
MODE_SMOKE_PLAYWRIGHT = MODE_SMOKE_KEEP
MODE_SMOKE_PLAYWRIGHT_FIXTURE = MODE_SMOKE_FIXTURE
MODE_SMOKE_PLAYWRIGHT_LOGIN = MODE_SMOKE_LOGIN


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=[
            MODE_BACKUP,
            MODE_SMOKE_KEEP,
            MODE_SMOKE_FIXTURE,
            MODE_SMOKE_LOGIN,
        ],
        default=MODE_BACKUP,
        help=(
            "Execution mode: backup | smoke-playwright (Keep reachability) | "
            "smoke-playwright-fixture (fixture-based smoke) | "
            "smoke-playwright-login (logged-in profile validation)."
        ),
    )
    parser.add_argument(
        "--note",
        action="append",
        default=[],
        help="Manual note body text. Can be provided multiple times.",
    )
    parser.add_argument(
        "--notes-file",
        type=Path,
        help="Path to a text file with one note body per line.",
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        default=Path("fixtures/keep_mock.html"),
        help="Path to a mock Keep HTML fixture for Playwright smoke.",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = build_parser()
    return parser.parse_args(argv)
