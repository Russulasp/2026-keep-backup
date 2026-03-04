from __future__ import annotations

import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO
from pathlib import Path

import keep_backup.runner as runner_module
from keep_backup.io import RunPaths
from keep_backup.runner import (
    _extract_note_payloads,
    build_notes,
    load_keep_profile_dir,
    run_backup_with_paths,
    run_playwright_keep_login_smoke,
)


class _FakeExtractPage:
    def __init__(self, notes: list[dict[str, str]]) -> None:
        self._notes = notes

    def evaluate(self, _: str) -> list[dict[str, str]]:
        return self._notes


class RunnerBackupTests(unittest.TestCase):

    def test_load_keep_profile_dir_reads_host_variable_as_fallback(self) -> None:
        original_main = os.environ.pop("KEEP_BROWSER_PROFILE_DIR", None)
        original_host = os.environ.pop("KEEP_BROWSER_PROFILE_DIR_HOST", None)
        try:
            os.environ["KEEP_BROWSER_PROFILE_DIR_HOST"] = "~/profile-host"
            profile_dir = load_keep_profile_dir()
            self.assertIsNotNone(profile_dir)
            self.assertTrue(str(profile_dir).endswith("profile-host"))
        finally:
            if original_main is not None:
                os.environ["KEEP_BROWSER_PROFILE_DIR"] = original_main
            else:
                os.environ.pop("KEEP_BROWSER_PROFILE_DIR", None)
            if original_host is not None:
                os.environ["KEEP_BROWSER_PROFILE_DIR_HOST"] = original_host
            else:
                os.environ.pop("KEEP_BROWSER_PROFILE_DIR_HOST", None)

    def test_build_notes_raises_when_no_inputs(self) -> None:
        with self.assertRaises(ValueError):
            build_notes([], None)

    def test_run_playwright_keep_login_smoke_requires_profile_dir(self) -> None:
        original_main = os.environ.pop("KEEP_BROWSER_PROFILE_DIR", None)
        original_host = os.environ.pop("KEEP_BROWSER_PROFILE_DIR_HOST", None)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                log_file = Path(tmp) / "logs" / "run.log"
                with self.assertRaises(RuntimeError):
                    run_playwright_keep_login_smoke(log_file)
        finally:
            if original_main is not None:
                os.environ["KEEP_BROWSER_PROFILE_DIR"] = original_main
            else:
                os.environ.pop("KEEP_BROWSER_PROFILE_DIR", None)
            if original_host is not None:
                os.environ["KEEP_BROWSER_PROFILE_DIR_HOST"] = original_host
            else:
                os.environ.pop("KEEP_BROWSER_PROFILE_DIR_HOST", None)

    def test_extract_note_payloads_keeps_title_and_body(self) -> None:
        page = _FakeExtractPage(
            [
                {"title": "title-1", "body": "body-1"},
                {"title": "", "body": "body-only"},
                {"title": "ignored", "body": "   "},
                {"title": "", "body": ""},
            ]
        )
        notes = _extract_note_payloads(page)
        self.assertEqual(notes[0], {"title": "title-1", "body": "body-1"})
        self.assertEqual(notes[1], {"body": "body-only"})
        self.assertEqual(notes[2], {"title": "ignored", "body": ""})
        self.assertEqual(len(notes), 3)

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

    def test_run_backup_with_paths_without_input_uses_keep_collection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            start = datetime(2026, 1, 1, 12, 0, 0)
            paths = RunPaths(
                backup_dir=tmp_path / "backups" / "2026-01-01",
                backup_file=tmp_path / "backups" / "2026-01-01" / "keep.json",
                log_file=tmp_path / "logs" / "run_2026-01-01_120000.log",
            )

            original_collector = runner_module._collect_keep_notes_for_backup
            runner_module._collect_keep_notes_for_backup = lambda _log: [
                {"title": "auto", "body": "from keep"}
            ]
            try:
                exit_code = run_backup_with_paths([], None, paths, start)
            finally:
                runner_module._collect_keep_notes_for_backup = original_collector

            self.assertEqual(exit_code, 0)
            payload = json.loads(paths.backup_file.read_text(encoding="utf-8"))
            self.assertEqual(payload["notes"], [{"title": "auto", "body": "from keep"}])

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
                exit_code = run_backup_with_paths([], Path("missing-file.txt"), paths, start)

            self.assertEqual(exit_code, 1)
            output = stdout.getvalue()
            self.assertIn("summary success=false", output)
            self.assertIn("error=notes file not found", output)
            self.assertTrue(paths.log_file.exists())


if __name__ == "__main__":
    unittest.main()
