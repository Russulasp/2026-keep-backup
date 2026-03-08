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
    run_parse_dom_with_paths,
    run_playwright_keep_login_smoke,
    _resolve_dom_snapshot_input,
)


class _FakeExtractPage:
    def __init__(self, notes: list[dict[str, str]]) -> None:
        self._notes = notes
        self.last_script = ""

    def evaluate(self, script: str) -> list[dict[str, str]]:
        self.last_script = script
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

    def test_extract_note_payloads_uses_escaped_newline_in_eval_script(self) -> None:
        page = _FakeExtractPage([])
        _extract_note_payloads(page)
        self.assertIn("ariaLabel.includes('\\n')", page.last_script)
        self.assertIn(".split('\\n')", page.last_script)
        self.assertIn("rest.join('\\n')", page.last_script)

    def test_extract_note_payloads_supports_select_note_card_selector(self) -> None:
        page = _FakeExtractPage([])
        _extract_note_payloads(page)
        self.assertIn('[aria-label="Select note"]', page.last_script)
        self.assertIn('[aria-label="メモを選択"]', page.last_script)

    def test_extract_note_payloads_discards_generic_select_note_body(self) -> None:
        page = _FakeExtractPage([])
        _extract_note_payloads(page)
        self.assertIn("'メモを選択'", page.last_script)
        self.assertIn("genericLabels", page.last_script)

    def test_extract_note_payloads_body_excludes_same_text_as_title(self) -> None:
        page = _FakeExtractPage([])
        _extract_note_payloads(page)
        self.assertIn("extractDistinctText", page.last_script)
        self.assertIn("], title);", page.last_script)

    def test_extract_note_payloads_avoids_aria_label_fallback_when_equal_to_title(self) -> None:
        page = _FakeExtractPage([])
        _extract_note_payloads(page)
        self.assertIn(
            "ariaLabel && (!normalizedTitle || ariaLabel !== normalizedTitle)",
            page.last_script,
        )


    def test_extract_note_payloads_supports_fixture_title_and_body_selectors(self) -> None:
        page = _FakeExtractPage([])
        _extract_note_payloads(page)
        self.assertIn("'.note .title'", page.last_script)
        self.assertIn("'.note .body'", page.last_script)

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

    def test_run_backup_with_paths_manual_input_logs_dom_snapshot_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            start = datetime(2026, 1, 1, 12, 0, 0)
            paths = RunPaths(
                backup_dir=tmp_path / "backups" / "2026-01-01",
                backup_file=tmp_path / "backups" / "2026-01-01" / "keep.json",
                log_file=tmp_path / "logs" / "run_2026-01-01_120000.log",
            )

            exit_code = run_backup_with_paths(["manual"], None, paths, start)
            self.assertEqual(exit_code, 0)
            log_text = paths.log_file.read_text(encoding="utf-8")
            self.assertIn("backup dom_snapshot_skipped=true reason=manual_input", log_text)

    def test_resolve_dom_snapshot_input_uses_latest_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            cwd = Path.cwd()
            try:
                os.chdir(tmp_path)
                artifacts_dir = Path("logs") / "artifacts"
                artifacts_dir.mkdir(parents=True, exist_ok=True)
                first = artifacts_dir / "dom_snapshot_2026-01-01_010101.html"
                second = artifacts_dir / "dom_snapshot_2026-01-02_020202.html"
                first.write_text("<html></html>", encoding="utf-8")
                second.write_text("<html></html>", encoding="utf-8")
                resolved = _resolve_dom_snapshot_input(None)
            finally:
                os.chdir(cwd)
            self.assertEqual(resolved.name, second.name)

    def test_run_parse_dom_with_paths_writes_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            start = datetime(2026, 1, 1, 12, 0, 0)
            paths = RunPaths(
                backup_dir=tmp_path / "backups" / "2026-01-01",
                backup_file=tmp_path / "backups" / "2026-01-01" / "keep.json",
                log_file=tmp_path / "logs" / "run_2026-01-01_120000.log",
            )
            dom_input = tmp_path / "logs" / "artifacts" / "dom_snapshot_x.html"
            dom_input.parent.mkdir(parents=True, exist_ok=True)
            dom_input.write_text("<html></html>", encoding="utf-8")
            dom_output = tmp_path / "backups" / "parsed.json"

            original_extractor = runner_module._extract_notes_from_dom_snapshot
            runner_module._extract_notes_from_dom_snapshot = lambda _dom, *, log_file: [
                {"title": "from-dom", "body": "parsed"}
            ]
            try:
                exit_code = run_parse_dom_with_paths(
                    paths=paths,
                    start=start,
                    dom_input=dom_input,
                    dom_output=dom_output,
                )
            finally:
                runner_module._extract_notes_from_dom_snapshot = original_extractor

            self.assertEqual(exit_code, 0)
            payload = json.loads(dom_output.read_text(encoding="utf-8"))
            self.assertEqual(payload["notes"], [{"title": "from-dom", "body": "parsed"}])


if __name__ == "__main__":
    unittest.main()
