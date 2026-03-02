from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from keep_backup.runner import DOM_SNAPSHOT_MAX_CHARS, _build_dom_snapshot_path, _write_dom_snapshot


class _FakePage:
    def __init__(self, html: str) -> None:
        self._html = html

    def content(self) -> str:
        return self._html


class RunnerDomSnapshotTests(unittest.TestCase):
    def test_write_dom_snapshot_truncates_large_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_file = Path(tmp) / "logs" / "run_2026-01-01_010101.log"
            snapshot_path = _build_dom_snapshot_path(log_file)
            page = _FakePage("x" * (DOM_SNAPSHOT_MAX_CHARS + 123))

            _write_dom_snapshot(page, snapshot_path=snapshot_path, log_file=log_file)

            self.assertTrue(snapshot_path.exists())
            content = snapshot_path.read_text(encoding="utf-8")
            self.assertEqual(len(content), DOM_SNAPSHOT_MAX_CHARS)


if __name__ == "__main__":
    unittest.main()
