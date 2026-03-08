from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from keep_backup.io import (
    RunPaths,
    append_log,
    build_paths,
    format_bool,
    load_notes_from_file,
    write_backup,
)


PLAYWRIGHT_PAGE_SETTLE_MS = 10_000
DOM_SNAPSHOT_MAX_CHARS = 200_000
INFINITE_SCROLL_MAX_ITERATIONS = 12
INFINITE_SCROLL_WAIT_MS = 1_000
INFINITE_SCROLL_STABLE_PASSES = 2
DOM_PARSED_OUTPUT_FILE_NAME = "keep_from_dom.json"
KEEP_PROBE_NOTES_SELECTOR = ", ".join(
    [
        '[aria-label="Notes"] [role="listitem"]',
        '[aria-label="Notes"] [role="list"]',
        '[aria-label="メモ"] [role="listitem"]',
        '[aria-label="メモ"] [role="list"]',
        '[aria-label="Select note"]',
        '[aria-label="メモを選択"]',
    ]
)


def load_keep_profile_dir() -> Path | None:
    raw_value = os.environ.get("KEEP_BROWSER_PROFILE_DIR", "").strip()
    if not raw_value:
        raw_value = os.environ.get("KEEP_BROWSER_PROFILE_DIR_HOST", "").strip()
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
    log_file: Path,
    error_message: str | None,
) -> None:
    summary = (
        "summary "
        f"success={format_bool(success)} "
        f"notes_count={notes_count} "
        f"duration_seconds={duration:.2f} "
        f"output={output} "
        f"log_file={log_file}"
    )
    print(summary)
    if error_message:
        print(f"error={error_message}")


def _finalize_run(
    *,
    log_file: Path,
    run_label: str,
    start: datetime,
    success: bool,
    notes_count: int,
    output: Path | str,
    error_message: str | None,
) -> None:
    end = datetime.now()
    duration = (end - start).total_seconds()
    append_log(log_file, f"{run_label} finished (success={success}) end_time={end.isoformat()}")
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
        log_file=log_file,
        error_message=error_message,
    )


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
        if note_bodies or notes_file:
            append_log(paths.log_file, "backup source=manual")
            append_log(paths.log_file, "backup dom_snapshot_skipped=true reason=manual_input")
            notes = build_notes(note_bodies, notes_file)
        else:
            notes = _collect_keep_notes_for_backup(paths.log_file)
        write_backup(paths.backup_file, start, notes)
        success = True
    except Exception as exc:  # noqa: BLE001
        error_message = str(exc)
    finally:
        _finalize_run(
            log_file=paths.log_file,
            run_label="run",
            start=start,
            success=success,
            notes_count=len(notes),
            output=paths.backup_file,
            error_message=error_message,
        )

    return 0 if success else 1


def run_parse_dom_with_paths(
    *,
    paths: RunPaths,
    start: datetime,
    dom_input: Path | None,
    dom_output: Path | None,
) -> int:
    append_log(paths.log_file, f"parse-dom started start_time={start.isoformat()}")

    success = False
    notes: list[dict[str, str]] = []
    error_message = None
    output_path = dom_output or (paths.backup_dir / DOM_PARSED_OUTPUT_FILE_NAME)

    try:
        snapshot_path = _resolve_dom_snapshot_input(dom_input)
        append_log(paths.log_file, f"parse-dom input={snapshot_path}")
        notes = _extract_notes_from_dom_snapshot(snapshot_path, log_file=paths.log_file)
        if not notes:
            raise RuntimeError("failed to extract notes from DOM snapshot")
        write_backup(output_path, start, notes)
        success = True
    except Exception as exc:  # noqa: BLE001
        error_message = str(exc)
    finally:
        _finalize_run(
            log_file=paths.log_file,
            run_label="parse-dom",
            start=start,
            success=success,
            notes_count=len(notes),
            output=output_path,
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
    min_notes_error_label: str = "notes",
    required_url_prefixes: list[str] | None = None,
    forbidden_url_prefixes: list[str] | None = None,
) -> int:
    start = datetime.now()
    append_log(log_file, f"playwright smoke started start_time={start.isoformat()}")

    success = False
    notes_count = 0
    error_message = None
    output = url

    try:
        with _open_playwright_page(log_file, profile_dir) as page:
            notes_count = _verify_playwright_page(
                page,
                log_file=log_file,
                url=url,
                notes_selector=notes_selector,
                min_notes=min_notes,
                min_notes_error_label=min_notes_error_label,
                required_url_prefixes=required_url_prefixes,
                forbidden_url_prefixes=forbidden_url_prefixes,
            )
        success = True
    except Exception as exc:  # noqa: BLE001
        error_message = str(exc)
    finally:
        _finalize_run(
            log_file=log_file,
            run_label="playwright smoke",
            start=start,
            success=success,
            notes_count=notes_count,
            output=output,
            error_message=error_message,
        )

    return 0 if success else 1


def run_playwright_keep_smoke(log_file: Path) -> int:
    profile_dir = load_keep_profile_dir()
    return run_playwright_smoke(log_file, url="https://keep.google.com/", profile_dir=profile_dir)


def run_playwright_keep_login_smoke(log_file: Path) -> int:
    profile_dir = load_keep_profile_dir()
    if not profile_dir:
        raise RuntimeError(
            "KEEP_BROWSER_PROFILE_DIR is not configured. Set KEEP_BROWSER_PROFILE_DIR_HOST in .env."
        )
    return run_playwright_smoke(
        log_file,
        url="https://keep.google.com/",
        profile_dir=profile_dir,
        required_url_prefixes=["https://keep.google.com/"],
        forbidden_url_prefixes=["https://accounts.google.com/"],
    )


def run_playwright_keep_probe(log_file: Path) -> int:
    profile_dir = load_keep_profile_dir()
    if not profile_dir:
        raise RuntimeError(
            "KEEP_BROWSER_PROFILE_DIR is not configured. Set KEEP_BROWSER_PROFILE_DIR_HOST in .env."
        )
    return run_playwright_smoke(
        log_file,
        url="https://keep.google.com/",
        profile_dir=profile_dir,
        notes_selector=KEEP_PROBE_NOTES_SELECTOR,
        min_notes=1,
        min_notes_error_label="probe elements",
        required_url_prefixes=["https://keep.google.com/"],
        forbidden_url_prefixes=["https://accounts.google.com/"],
    )



def _build_dom_snapshot_path(log_file: Path) -> Path:
    artifacts_dir = log_file.parent / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    stem = log_file.stem.replace("run_", "")
    return artifacts_dir / f"dom_snapshot_{stem}.html"


def _write_dom_snapshot(page: object, *, snapshot_path: Path, log_file: Path) -> None:
    html = page.content()
    original_len = len(html)
    truncated = False
    if original_len > DOM_SNAPSHOT_MAX_CHARS:
        html = html[:DOM_SNAPSHOT_MAX_CHARS]
        truncated = True
    snapshot_path.write_text(html, encoding="utf-8")
    append_log(
        log_file,
        f"playwright smoke dom_snapshot={snapshot_path} chars={len(html)} truncated={truncated} original_chars={original_len}",
    )


def run_playwright_keep_dom_smoke(log_file: Path) -> int:
    profile_dir = load_keep_profile_dir()
    if not profile_dir:
        raise RuntimeError(
            "KEEP_BROWSER_PROFILE_DIR is not configured. Set KEEP_BROWSER_PROFILE_DIR_HOST in .env."
        )

    start = datetime.now()
    append_log(log_file, f"playwright smoke started start_time={start.isoformat()}")

    success = False
    notes_count = 0
    error_message = None
    snapshot_path = _build_dom_snapshot_path(log_file)
    output = snapshot_path

    try:
        with _open_playwright_page(log_file, profile_dir) as page:
            try:
                notes_count = _verify_playwright_page(
                    page,
                    log_file=log_file,
                    url="https://keep.google.com/",
                    notes_selector=KEEP_PROBE_NOTES_SELECTOR,
                    min_notes=1,
                    min_notes_error_label="probe elements",
                    required_url_prefixes=["https://keep.google.com/"],
                    forbidden_url_prefixes=["https://accounts.google.com/"],
                )
                success = True
            except Exception as exc:  # noqa: BLE001
                error_message = str(exc)
            finally:
                try:
                    _write_dom_snapshot(page, snapshot_path=snapshot_path, log_file=log_file)
                except Exception as snapshot_exc:  # noqa: BLE001
                    append_log(log_file, f"playwright smoke dom_snapshot_error={snapshot_exc}")
                    if error_message is None:
                        error_message = f"failed to write dom snapshot: {snapshot_exc}"
    except Exception as exc:  # noqa: BLE001
        error_message = str(exc)
    finally:
        _finalize_run(
            log_file=log_file,
            run_label="playwright smoke dom",
            start=start,
            success=success,
            notes_count=notes_count,
            output=output,
            error_message=error_message,
        )

    return 0 if success else 1

def run_playwright_fixture_smoke(log_file: Path, fixture_path: Path) -> int:
    if not fixture_path.exists():
        raise FileNotFoundError(f"fixture not found: {fixture_path}")
    fixture_url = fixture_path.resolve().as_uri()
    return run_playwright_smoke(
        log_file,
        url=fixture_url,
        notes_selector='[data-testid="keep-note"]',
        min_notes=1,
        min_notes_error_label="fixture notes",
    )


def _collect_keep_notes_for_backup(log_file: Path) -> list[dict[str, str]]:
    profile_dir = load_keep_profile_dir()
    if not profile_dir:
        raise RuntimeError(
            "KEEP_BROWSER_PROFILE_DIR is not configured. Set KEEP_BROWSER_PROFILE_DIR_HOST in .env."
        )

    append_log(log_file, "backup source=keep")
    with _open_playwright_page(log_file, profile_dir) as page:
        _verify_playwright_page(
            page,
            log_file=log_file,
            url="https://keep.google.com/",
            notes_selector=KEEP_PROBE_NOTES_SELECTOR,
            min_notes=1,
            min_notes_error_label="backup notes",
            required_url_prefixes=["https://keep.google.com/"],
            forbidden_url_prefixes=["https://accounts.google.com/"],
        )
        snapshot_path = _build_dom_snapshot_path(log_file)
        _write_dom_snapshot(page, snapshot_path=snapshot_path, log_file=log_file)
        notes = _extract_note_payloads(page)
    append_log(log_file, f"backup extracted_notes={len(notes)}")
    if not notes:
        raise RuntimeError("failed to extract notes from Keep page")
    return notes


def _extract_note_payloads(page: object) -> list[dict[str, str]]:
    raw_notes = page.evaluate(
        """
        () => {
          const genericLabels = new Set([
            'Select note',
            'メモを選択',
            'Note',
            'メモ',
            'Take a note…',
            'Take a note...',
            'メモを入力…',
          ]);

          const cardSelectors = [
            '.notes-container .IZ65Hb-n0tgWb',
            '[aria-label="Notes"] [role="listitem"]',
            '[aria-label="メモ"] [role="listitem"]',
            '[aria-label="Select note"]',
            '[aria-label="メモを選択"]',
            '[role="listitem"]',
          ];

          const cards = [];
          for (const selector of cardSelectors) {
            for (const element of document.querySelectorAll(selector)) {
              const card = element.closest('.IZ65Hb-n0tgWb, [role="listitem"], article, li') || element;
              if (!cards.includes(card)) {
                cards.push(card);
              }
            }
          }

          const readText = (element) => (element?.innerText || element?.textContent || '').trim();

          const extractText = (root, selectors) => {
            for (const selector of selectors) {
              const found = root.querySelector(selector);
              if (!found) continue;
              const text = readText(found);
              if (text) return text;
            }
            return '';
          };

          const extractDistinctText = (root, selectors, excludeText) => {
            for (const selector of selectors) {
              for (const found of root.querySelectorAll(selector)) {
                const text = readText(found);
                if (!text) continue;
                if (excludeText && text === excludeText) continue;
                return text;
              }
            }
            return '';
          };

          const notes = [];
          for (const card of cards) {
            const ariaLabel = (card.getAttribute('aria-label') || '').trim();
            const title = extractText(card, [
              '[aria-label="Title"]',
              '[aria-label="タイトル"]',
              '[placeholder="Title"]',
              '[placeholder="タイトル"]',
              '.IZ65Hb-YPqjbf[role="textbox"]',
              '[data-testid="note-title"]',
              '.note .title',
            ]);
            let body = extractDistinctText(card, [
              '[aria-label="Note"]',
              '[aria-label="メモ"]',
              '.IZ65Hb-vIzZGf-L9AdLc-haAclf',
              '[contenteditable="true"][role="textbox"]',
              '[data-testid="note-content"]',
              '.note .body',
            ], title);

            let normalizedTitle = title;
            let normalizedBody = body;

            if (!normalizedTitle && ariaLabel.includes('\\n')) {
              const [firstLine, ...rest] = ariaLabel
                .split('\\n')
                .map((line) => line.trim())
                .filter(Boolean);
              normalizedTitle = firstLine || '';
              if (!normalizedBody && rest.length > 0) {
                normalizedBody = rest.join('\\n');
              }
            }

            if (!normalizedBody && ariaLabel && (!normalizedTitle || ariaLabel !== normalizedTitle)) {
              normalizedBody = ariaLabel;
            }

            if (genericLabels.has(normalizedTitle)) {
              normalizedTitle = '';
            }
            if (genericLabels.has(normalizedBody)) {
              normalizedBody = '';
            }

            if (!normalizedTitle && !normalizedBody) {
              continue;
            }

            notes.push({
              title: normalizedTitle,
              body: normalizedBody,
            });
          }
          return notes;
        }
        """
    )

    notes: list[dict[str, str]] = []
    for item in raw_notes:
        title = str(item.get("title", "")).strip()
        body = str(item.get("body", "")).strip()
        if not title and not body:
            continue
        note: dict[str, str] = {"body": body}
        if title:
            note["title"] = title
        notes.append(note)
    return notes


def _resolve_dom_snapshot_input(dom_input: Path | None) -> Path:
    if dom_input is not None:
        if not dom_input.exists():
            raise FileNotFoundError(f"dom snapshot not found: {dom_input}")
        return dom_input

    artifacts_dir = Path("logs") / "artifacts"
    candidates = sorted(artifacts_dir.glob("dom_snapshot_*.html"), key=lambda path: path.stat().st_mtime)
    if not candidates:
        raise FileNotFoundError(
            "dom snapshot not found: logs/artifacts/dom_snapshot_*.html"
        )
    return candidates[-1]


def _extract_notes_from_dom_snapshot(dom_snapshot_path: Path, *, log_file: Path) -> list[dict[str, str]]:
    snapshot_url = dom_snapshot_path.resolve().as_uri()
    with _open_playwright_page(log_file, profile_dir=None) as page:
        _verify_playwright_page(
            page,
            log_file=log_file,
            url=snapshot_url,
            notes_selector=None,
            min_notes=None,
            min_notes_error_label="dom notes",
            required_url_prefixes=["file://"],
            forbidden_url_prefixes=None,
        )
        notes = _extract_note_payloads(page)
    append_log(log_file, f"parse-dom extracted_notes={len(notes)}")
    return notes


def _load_sync_playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "playwright is not installed. Install dependencies and run `playwright install chromium`."
        ) from exc
    return sync_playwright


@contextmanager
def _open_playwright_page(log_file: Path, profile_dir: Path | None) -> Iterator[object]:
    sync_playwright = _load_sync_playwright()
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

        try:
            yield page
        finally:
            context.close()


def _verify_playwright_page(
    page: object,
    *,
    log_file: Path,
    url: str,
    notes_selector: str | None,
    min_notes: int | None,
    min_notes_error_label: str,
    required_url_prefixes: list[str] | None,
    forbidden_url_prefixes: list[str] | None,
) -> int:
    response = page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(PLAYWRIGHT_PAGE_SETTLE_MS)
    title = page.title()
    current_url = page.url
    status = response.status if response else "file"
    append_log(log_file, f"playwright smoke page_title={title}")
    append_log(log_file, f"playwright smoke http_status={status}")
    append_log(log_file, f"playwright smoke page_url={current_url}")
    ready_state = page.evaluate("document.readyState")
    append_log(log_file, f"playwright smoke ready_state={ready_state}")

    if forbidden_url_prefixes:
        for forbidden_prefix in forbidden_url_prefixes:
            if current_url.startswith(forbidden_prefix):
                raise RuntimeError(f"unexpected page_url for logged-in smoke: {current_url}")

    if required_url_prefixes:
        if not any(current_url.startswith(prefix) for prefix in required_url_prefixes):
            raise RuntimeError(f"unexpected page_url: {current_url}")

    notes_count = 0
    if notes_selector:
        append_log(log_file, f"playwright smoke notes_selector={notes_selector}")
        notes_count = _collect_notes_with_infinite_scroll(
            page,
            log_file=log_file,
            notes_selector=notes_selector,
        )
        append_log(log_file, f"playwright smoke notes_count={notes_count}")
        if min_notes is not None and notes_count < min_notes:
            raise RuntimeError(f"{min_notes_error_label} count too small: {notes_count}")
    return notes_count


def _collect_notes_with_infinite_scroll(
    page: object,
    *,
    log_file: Path,
    notes_selector: str,
) -> int:
    highest_count = page.locator(notes_selector).count()
    stable_passes = 0

    for iteration in range(1, INFINITE_SCROLL_MAX_ITERATIONS + 1):
        page.mouse.wheel(0, 2_000)
        page.wait_for_timeout(INFINITE_SCROLL_WAIT_MS)
        latest_count = page.locator(notes_selector).count()

        if latest_count > highest_count:
            highest_count = latest_count
            stable_passes = 0
        else:
            stable_passes += 1

        append_log(
            log_file,
            "playwright smoke scroll "
            f"iteration={iteration} notes_count={latest_count} stable_passes={stable_passes}",
        )

        if stable_passes >= INFINITE_SCROLL_STABLE_PASSES:
            break

    return highest_count
