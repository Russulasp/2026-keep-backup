from __future__ import annotations

import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO
from pathlib import Path

from keep_backup.runner import _finalize_run


class RunnerFinalizeTests(unittest.TestCase):
    def test_finalize_run_writes_common_log_and_summary_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_file = Path(tmp) / "logs" / "run.log"
            start = datetime(2026, 1, 1, 12, 0, 0)

            stdout = StringIO()
            with redirect_stdout(stdout):
                _finalize_run(
                    log_file=log_file,
                    run_label="playwright smoke",
                    start=start,
                    success=True,
                    notes_count=3,
                    output="https://example.test",
                    error_message=None,
                )

            log_text = log_file.read_text(encoding="utf-8")
            self.assertIn("playwright smoke finished (success=True)", log_text)
            self.assertIn("duration_seconds=", log_text)
            self.assertIn("notes_count=3", log_text)
            self.assertIn("output=https://example.test", log_text)

            summary = stdout.getvalue()
            self.assertIn("summary success=true", summary)
            self.assertIn("notes_count=3", summary)
            self.assertIn("output=https://example.test", summary)


if __name__ == "__main__":
    unittest.main()
