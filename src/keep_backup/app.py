from __future__ import annotations

from datetime import datetime

from keep_backup.cli import MODE_SMOKE_PLAYWRIGHT, MODE_SMOKE_PLAYWRIGHT_FIXTURE, parse_args
from keep_backup.io import build_paths, load_dotenv_if_present
from keep_backup.runner import run_backup, run_playwright_fixture_smoke, run_playwright_keep_smoke


def main(argv: list[str] | None = None) -> int:
    load_dotenv_if_present()
    args = parse_args(argv)

    now = datetime.now()
    paths = build_paths(now)

    if args.mode == MODE_SMOKE_PLAYWRIGHT:
        return run_playwright_keep_smoke(paths.log_file)
    if args.mode == MODE_SMOKE_PLAYWRIGHT_FIXTURE:
        return run_playwright_fixture_smoke(paths.log_file, args.fixture)
    return run_backup(args.note, args.notes_file)


if __name__ == "__main__":
    raise SystemExit(main())
