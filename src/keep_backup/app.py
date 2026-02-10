from __future__ import annotations

import argparse
import json
import os
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


def run_playwright_smoke(
    log_file: Path,
    *,
    url: str,
    profile_dir: Path | None = None,
    notes_selector: str | None = None,
    min_notes: int | None = None,
) -> int:
    start = datetime.now()
    append_log(log_file, "playwright smoke started")

    success = False
    notes_count = 0
    error_message = None
    output = url

    try:
        try:
            from playwright.sync_api import sync_playwright
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "playwright is not installed. Install dependencies and run `playwright install chromium`."
            ) from exc

        with sync_playwright() as playwright:
            if profile_dir:
                append_log(log_file, f"playwright smoke profile_dir={profile_dir}")
                context = playwright.chromium.launch_persistent_context(
                    user_data_dir=str(profile_dir),
                    headless=True,
                )
                page = context.pages[0] if context.pages else context.new_page()
            else:
                append_log(log_file, "playwright smoke profile_dir=(none)")
                browser = playwright.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()

            response = page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(1000)
            title = page.title()
            status = response.status if response else "file"
            append_log(log_file, f"playwright smoke page_title={title}")
            append_log(log_file, f"playwright smoke http_status={status}")
            if notes_selector:
                notes_count = page.locator(notes_selector).count()
                append_log(log_file, f"playwright smoke notes_count={notes_count}")
                if min_notes is not None and notes_count < min_notes:
                    raise RuntimeError(f"fixture notes count too small: {notes_count}")
            context.close()
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


def run_playwright_keep_smoke(log_file: Path) -> int:
    profile_dir = load_keep_profile_dir()
    return run_playwright_smoke(log_file, url="https://keep.google.com/", profile_dir=profile_dir)


def load_keep_profile_dir() -> Path | None:
    raw_value = os.environ.get("KEEP_BROWSER_PROFILE_DIR", "").strip()
    if not raw_value:
        return None
    return Path(raw_value).expanduser()



def load_dotenv_if_present(dotenv_path: Path = Path(".env")) -> None:
    if not dotenv_path.exists():
        return
    with dotenv_path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


def run_playwright_fixture_smoke(log_file: Path, fixture_path: Path) -> int:
    if not fixture_path.exists():
        raise FileNotFoundError(f"fixture not found: {fixture_path}")
    fixture_url = fixture_path.resolve().as_uri()
    return run_playwright_smoke(
        log_file,
        url=fixture_url,
        notes_selector='[data-testid="keep-note"]',
        min_notes=1,
    )


def load_notes_from_file(notes_file: Path) -> list[dict[str, str]]:
    if not notes_file.exists():
        raise FileNotFoundError(f"notes file not found: {notes_file}")
    notes: list[dict[str, str]] = []
    with notes_file.open("r", encoding="utf-8") as handle:
        for line in handle:
            body = line.strip()
            if body:
                notes.append({"body": body})
    return notes


def build_notes(note_bodies: list[str], notes_file: Path | None) -> list[dict[str, str]]:
    notes: list[dict[str, str]] = []
    for body in note_bodies:
        body = body.strip()
        if body:
            notes.append({"body": body})
    if notes_file:
        notes.extend(load_notes_from_file(notes_file))
    if not notes:
        raise ValueError("no notes provided. Use --note or --notes-file.")
    return notes


def run_backup(note_bodies: list[str], notes_file: Path | None) -> int:
    start = datetime.now()
    paths = build_paths(start)
    append_log(paths.log_file, f"run started start_time={start.isoformat()}")

    success = False
    notes: list[dict[str, str]] = []
    error_message = None

    try:
        notes = build_notes(note_bodies, notes_file)
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
        append_log(paths.log_file, f"run finished (success={success}) end_time={end.isoformat()}")
        append_log(paths.log_file, f"duration_seconds={duration:.2f}")
        append_log(paths.log_file, f"notes_count={len(notes)}")
        append_log(paths.log_file, f"output_dir={paths.backup_dir}")
        if error_message:
            append_log(paths.log_file, f"error={error_message}")
        print(summary)
        if error_message:
            print(f"error={error_message}")

    return 0 if success else 1


def main() -> int:
    load_dotenv_if_present()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["backup", "smoke-playwright", "smoke-playwright-fixture"],
        default="backup",
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
    args = parser.parse_args()

    now = datetime.now()
    paths = build_paths(now)

    if args.mode == "smoke-playwright":
        return run_playwright_keep_smoke(paths.log_file)
    if args.mode == "smoke-playwright-fixture":
        return run_playwright_fixture_smoke(paths.log_file, args.fixture)
    return run_backup(args.note, args.notes_file)


if __name__ == "__main__":
    raise SystemExit(main())
