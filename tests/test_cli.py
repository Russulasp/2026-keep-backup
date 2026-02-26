from __future__ import annotations

import unittest

from keep_backup.cli import (
    MODE_BACKUP,
    MODE_SMOKE_PLAYWRIGHT_FIXTURE,
    MODE_SMOKE_PLAYWRIGHT_LOGIN,
    parse_args,
)


class CliTests(unittest.TestCase):
    def test_parse_args_defaults(self) -> None:
        args = parse_args([])
        self.assertEqual(args.mode, MODE_BACKUP)
        self.assertEqual(args.note, [])

    def test_parse_args_fixture_mode(self) -> None:
        args = parse_args(["--mode", MODE_SMOKE_PLAYWRIGHT_FIXTURE, "--note", "a"])
        self.assertEqual(args.mode, MODE_SMOKE_PLAYWRIGHT_FIXTURE)
        self.assertEqual(args.note, ["a"])

    def test_parse_args_login_mode(self) -> None:
        args = parse_args(["--mode", MODE_SMOKE_PLAYWRIGHT_LOGIN])
        self.assertEqual(args.mode, MODE_SMOKE_PLAYWRIGHT_LOGIN)


if __name__ == "__main__":
    unittest.main()
