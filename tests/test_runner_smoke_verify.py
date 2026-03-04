from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from keep_backup.runner import (
    KEEP_PROBE_NOTES_SELECTOR,
    _collect_notes_with_infinite_scroll,
    _verify_playwright_page,
)


class _FakeResponse:
    def __init__(self, status: int) -> None:
        self.status = status


class _FakeLocator:
    def __init__(self, count_value: int) -> None:
        self._count_value = count_value

    def count(self) -> int:
        return self._count_value


class _FakePage:
    class _FakeMouse:
        def __init__(self, page: "_FakePage") -> None:
            self._page = page

        def wheel(self, _: int, __: int) -> None:
            self._page._scroll_steps += 1

    def __init__(
        self,
        *,
        url: str,
        title: str = "Keep",
        notes_count: int = 0,
        notes_growth: list[int] | None = None,
    ) -> None:
        self.url = url
        self._title = title
        self._notes_count = notes_count
        self._notes_growth = notes_growth or []
        self._scroll_steps = 0
        self.mouse = self._FakeMouse(self)

    def goto(self, url: str, wait_until: str) -> _FakeResponse:  # noqa: ARG002
        return _FakeResponse(status=200)

    def wait_for_timeout(self, _: int) -> None:
        return None

    def title(self) -> str:
        return self._title

    def evaluate(self, script: str) -> str:
        if script == "document.readyState":
            return "complete"
        raise ValueError(f"unsupported script: {script}")

    def locator(self, _: str) -> _FakeLocator:
        if self._notes_growth:
            index = min(self._scroll_steps, len(self._notes_growth) - 1)
            return _FakeLocator(self._notes_growth[index])
        return _FakeLocator(self._notes_count)


class RunnerSmokeVerifyTests(unittest.TestCase):
    def test_probe_selector_contains_localized_fallbacks(self) -> None:
        self.assertIn('[aria-label="Notes"] [role="listitem"]', KEEP_PROBE_NOTES_SELECTOR)
        self.assertIn('[aria-label="メモ"] [role="listitem"]', KEEP_PROBE_NOTES_SELECTOR)
        self.assertIn('[aria-label="Select note"]', KEEP_PROBE_NOTES_SELECTOR)
        self.assertIn('[aria-label="メモを選択"]', KEEP_PROBE_NOTES_SELECTOR)

    def test_verify_accepts_keep_url_when_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_file = Path(tmp) / "logs" / "run.log"
            page = _FakePage(url="https://keep.google.com/u/0/")
            notes_count = _verify_playwright_page(
                page,
                log_file=log_file,
                url="https://keep.google.com/",
                notes_selector=None,
                min_notes=None,
                min_notes_error_label="notes",
                required_url_prefixes=["https://keep.google.com/"],
                forbidden_url_prefixes=["https://accounts.google.com/"],
            )
            self.assertEqual(notes_count, 0)

    def test_verify_rejects_google_accounts_redirect(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_file = Path(tmp) / "logs" / "run.log"
            page = _FakePage(url="https://accounts.google.com/v3/signin/")
            with self.assertRaises(RuntimeError):
                _verify_playwright_page(
                    page,
                    log_file=log_file,
                    url="https://keep.google.com/",
                    notes_selector=None,
                    min_notes=None,
                    min_notes_error_label="notes",
                    required_url_prefixes=["https://keep.google.com/"],
                    forbidden_url_prefixes=["https://accounts.google.com/"],
                )

    def test_collect_notes_scrolls_until_count_stabilizes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_file = Path(tmp) / "logs" / "run.log"
            page = _FakePage(
                url="https://keep.google.com/u/0/",
                notes_growth=[2, 5, 8, 8, 8],
            )

            notes_count = _collect_notes_with_infinite_scroll(
                page,
                log_file=log_file,
                notes_selector='[data-testid="keep-note"]',
            )

            self.assertEqual(notes_count, 8)


if __name__ == "__main__":
    unittest.main()
