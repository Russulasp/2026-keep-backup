from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO
from pathlib import Path

from keep_backup.io import RunPaths
from keep_backup.runner import build_notes, run_backup_with_paths


class RunnerBackupTests(unittest.TestCase):
    def test_build_notes_raises_when_no_inputs(self) -> None:
        with self.assertRaises(ValueError):
            build_notes([], None)

    def test_run_backup_with_paths_writes_backup_and_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            notes_file = tmp_path / "notes.txt"
            notes_file.write_text("line from file\n\n", encoding="utf-8")

            start = datetime(2026, 1, 1, 12, 0, 0)
            paths = RunPaths(
                backup_dir=tmp_path / "backups" / "2026-01-01",
                backup_file=tmp_path / "backups" / "2026-01-01" / "keep.json",
                log_file=tmp_path / "logs" / "run_2026-01-01_120000.log",
            )

            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = run_backup_with_paths(["manual note"], notes_file, paths, start)

            self.assertEqual(exit_code, 0)
            self.assertTrue(paths.backup_file.exists())
            self.assertTrue(paths.log_file.exists())

            payload = json.loads(paths.backup_file.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["notes"]), 2)
            self.assertEqual(payload["notes"][0]["body"], "manual note")
            self.assertEqual(payload["notes"][1]["body"], "line from file")

            output = stdout.getvalue()
            self.assertIn("summary success=true", output)
            self.assertIn("notes_count=2", output)

    def test_run_backup_with_paths_returns_error_on_missing_notes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            start = datetime(2026, 1, 1, 12, 0, 0)
            paths = RunPaths(
                backup_dir=tmp_path / "backups" / "2026-01-01",
                backup_file=tmp_path / "backups" / "2026-01-01" / "keep.json",
                log_file=tmp_path / "logs" / "run_2026-01-01_120000.log",
            )

            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = run_backup_with_paths([], None, paths, start)

            self.assertEqual(exit_code, 1)
            output = stdout.getvalue()
            self.assertIn("summary success=false", output)
            self.assertIn("error=no notes provided", output)
            self.assertTrue(paths.log_file.exists())


if __name__ == "__main__":
    unittest.main()
