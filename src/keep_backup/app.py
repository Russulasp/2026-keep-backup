from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path



@dataclass
class RunPaths:
    backup_dir: Path
    backup_file: Path
    log_file: Path


def build_paths(now: datetime) -> RunPaths:
    date_stamp = now.strftime("%Y-%m-%d")
    log_stamp = now.strftime("%Y-%m-%d_%H%M%S")
    backup_dir = Path("backups") / date_stamp
    backup_file = backup_dir / "keep.json"
    log_file = Path("logs") / f"run_{log_stamp}.log"
    return RunPaths(backup_dir=backup_dir, backup_file=backup_file, log_file=log_file)


def append_log(log_file: Path, message: str) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(f"[{timestamp}] {message}\n")


def write_backup(backup_file: Path, now: datetime, notes: list[dict[str, str]]) -> None:
    backup_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "scraped_at": now.isoformat(),
        "notes": notes,
    }
    with backup_file.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def format_bool(value: bool) -> str:
    return str(value).lower()


def run_playwright_smoke(log_file: Path) -> int:
    start = datetime.now()
    append_log(log_file, "playwright smoke started")

    success = False
    notes_count = 0
    error_message = None
    output = "-"

    try:
        try:
            from playwright.sync_api import sync_playwright
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "playwright is not installed. Install dependencies and run `playwright install chromium`."
            ) from exc

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            response = page.goto("https://keep.google.com/", wait_until="domcontentloaded")
            page.wait_for_timeout(1000)
            title = page.title()
            status = response.status if response else "unknown"
            append_log(log_file, f"playwright smoke page_title={title}")
            append_log(log_file, f"playwright smoke http_status={status}")
            browser.close()
        success = True
    except Exception as exc:  # noqa: BLE001
        error_message = str(exc)
    finally:
        end = datetime.now()
        duration = (end - start).total_seconds()
        summary = (
            "summary "
            f"success={format_bool(success)} "
            f"notes_count={notes_count} "
            f"duration_seconds={duration:.2f} "
            f"output={output}"
        )
        append_log(log_file, f"playwright smoke finished (success={success})")
        append_log(log_file, f"duration_seconds={duration:.2f}")
        append_log(log_file, f"notes_count={notes_count}")
        append_log(log_file, f"output={output}")
        if error_message:
            append_log(log_file, f"error={error_message}")
        print(summary)
        if error_message:
            print(f"error={error_message}")

    return 0 if success else 1


def run_backup() -> int:
    start = datetime.now()
    paths = build_paths(start)
    append_log(paths.log_file, "run started")

    success = False
    notes: list[dict[str, str]] = []
    error_message = None

    try:
        notes = [{"body": "Hello World"}]
        write_backup(paths.backup_file, start, notes)
        success = True
    except Exception as exc:  # noqa: BLE001
        error_message = str(exc)
    finally:
        end = datetime.now()
        duration = (end - start).total_seconds()
        summary = (
            "summary "
            f"success={format_bool(success)} "
            f"notes_count={len(notes)} "
            f"duration_seconds={duration:.2f} "
            f"output={paths.backup_file}"
        )
        append_log(paths.log_file, f"run finished (success={success})")
        append_log(paths.log_file, f"duration_seconds={duration:.2f}")
        append_log(paths.log_file, f"notes_count={len(notes)}")
        append_log(paths.log_file, f"output={paths.backup_file}")
        if error_message:
            append_log(paths.log_file, f"error={error_message}")
        print(summary)
        if error_message:
            print(f"error={error_message}")

    return 0 if success else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["backup", "smoke-playwright"],
        default="backup",
        help="Execution mode. Use smoke-playwright for no-profile browser startup check.",
    )
    args = parser.parse_args()

    now = datetime.now()
    paths = build_paths(now)

    if args.mode == "smoke-playwright":
        return run_playwright_smoke(paths.log_file)
    return run_backup()


if __name__ == "__main__":
    raise SystemExit(main())
