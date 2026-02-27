from __future__ import annotations

from datetime import datetime
from typing import Callable

from keep_backup.cli import (
    MODE_BACKUP,
    MODE_SMOKE_FIXTURE,
    MODE_SMOKE_KEEP,
    MODE_SMOKE_LOGIN,
    parse_args,
)
from keep_backup.io import build_paths, load_dotenv_if_present
from keep_backup.runner import (
    run_backup,
    run_playwright_fixture_smoke,
    run_playwright_keep_login_smoke,
    run_playwright_keep_smoke,
)


def main(argv: list[str] | None = None) -> int:
    load_dotenv_if_present()
    args = parse_args(argv)

    now = datetime.now()
    paths = build_paths(now)

    mode_handlers: dict[str, Callable[[], int]] = {
        MODE_BACKUP: lambda: run_backup(args.note, args.notes_file),
        MODE_SMOKE_KEEP: lambda: run_playwright_keep_smoke(paths.log_file),
        MODE_SMOKE_FIXTURE: lambda: run_playwright_fixture_smoke(paths.log_file, args.fixture),
        MODE_SMOKE_LOGIN: lambda: run_playwright_keep_login_smoke(paths.log_file),
    }
    return mode_handlers[args.mode]()


if __name__ == "__main__":
    raise SystemExit(main())
