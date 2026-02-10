from __future__ import annotations

import argparse
from pathlib import Path


MODE_BACKUP = "backup"
MODE_SMOKE_PLAYWRIGHT = "smoke-playwright"
MODE_SMOKE_PLAYWRIGHT_FIXTURE = "smoke-playwright-fixture"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=[MODE_BACKUP, MODE_SMOKE_PLAYWRIGHT, MODE_SMOKE_PLAYWRIGHT_FIXTURE],
        default=MODE_BACKUP,
        help="Execution mode. Use smoke-playwright for no-profile browser startup check.",
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
