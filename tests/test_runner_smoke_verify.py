from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from keep_backup.runner import _verify_playwright_page


class _FakeResponse:
    def __init__(self, status: int) -> None:
        self.status = status


class _FakeLocator:
    def __init__(self, count_value: int) -> None:
        self._count_value = count_value

    def count(self) -> int:
        return self._count_value


class _FakePage:
    def __init__(self, *, url: str, title: str = "Keep", notes_count: int = 0) -> None:
        self.url = url
        self._title = title
        self._notes_count = notes_count

    def goto(self, url: str, wait_until: str) -> _FakeResponse:  # noqa: ARG002
        return _FakeResponse(status=200)

    def wait_for_timeout(self, _: int) -> None:
        return None

    def title(self) -> str:
        return self._title

    def locator(self, _: str) -> _FakeLocator:
        return _FakeLocator(self._notes_count)


class RunnerSmokeVerifyTests(unittest.TestCase):
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
                    required_url_prefixes=["https://keep.google.com/"],
                    forbidden_url_prefixes=["https://accounts.google.com/"],
                )


if __name__ == "__main__":
    unittest.main()
