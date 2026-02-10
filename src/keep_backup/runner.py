from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from keep_backup.io import (
    RunPaths,
    append_log,
    build_paths,
    format_bool,
    load_notes_from_file,
    write_backup,
)


def load_keep_profile_dir() -> Path | None:
    raw_value = os.environ.get("KEEP_BROWSER_PROFILE_DIR", "").strip()
    if not raw_value:
        return None
    return Path(raw_value).expanduser()


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


def _print_summary(
    *,
    success: bool,
    notes_count: int,
    duration: float,
    output: Path | str,
    error_message: str | None,
) -> None:
    summary = (
        "summary "
        f"success={format_bool(success)} "
        f"notes_count={notes_count} "
        f"duration_seconds={duration:.2f} "
        f"output={output}"
    )
    print(summary)
    if error_message:
        print(f"error={error_message}")


def run_backup(note_bodies: list[str], notes_file: Path | None) -> int:
    start = datetime.now()
    paths = build_paths(start)
    return run_backup_with_paths(note_bodies, notes_file, paths, start)


def run_backup_with_paths(
    note_bodies: list[str],
    notes_file: Path | None,
    paths: RunPaths,
    start: datetime,
) -> int:
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
        append_log(paths.log_file, f"run finished (success={success}) end_time={end.isoformat()}")
        append_log(paths.log_file, f"duration_seconds={duration:.2f}")
        append_log(paths.log_file, f"notes_count={len(notes)}")
        append_log(paths.log_file, f"output_dir={paths.backup_dir}")
        if error_message:
            append_log(paths.log_file, f"error={error_message}")
        _print_summary(
            success=success,
            notes_count=len(notes),
            duration=duration,
            output=paths.backup_file,
            error_message=error_message,
        )

    return 0 if success else 1


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
        append_log(log_file, f"playwright smoke finished (success={success})")
        append_log(log_file, f"duration_seconds={duration:.2f}")
        append_log(log_file, f"notes_count={notes_count}")
        append_log(log_file, f"output={output}")
        if error_message:
            append_log(log_file, f"error={error_message}")
        _print_summary(
            success=success,
            notes_count=notes_count,
            duration=duration,
            output=output,
            error_message=error_message,
        )

    return 0 if success else 1


def run_playwright_keep_smoke(log_file: Path) -> int:
    profile_dir = load_keep_profile_dir()
    return run_playwright_smoke(log_file, url="https://keep.google.com/", profile_dir=profile_dir)


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
