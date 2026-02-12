# 01-sequence — 代表ユースケースのシーケンス図（backupモード）

- 入口: `make backup` → `uv run python -m keep_backup.app --mode backup`（または `python -m keep_backup.app` の既定モード）。
- 出口: `backups/YYYY-MM-DD/keep.json` と `logs/run_YYYY-MM-DD_HHMMSS.log` を生成し、stdout に `summary ...` を出力。
- 主要関数: `keep_backup.app.main` → `keep_backup.runner.run_backup` → `keep_backup.runner.run_backup_with_paths` → `keep_backup.io.write_backup` / `keep_backup.runner._finalize_run`。
- テストコマンド: `uv run python -m unittest`。
- CIコマンド（関連）:
  - PRスモーク: `uv run python -m keep_backup.app --mode smoke-playwright-fixture`
  - バックアップCI: `python -m keep_backup.app --note "ci-smoke-note"`

```mermaid
sequenceDiagram
    autonumber
    participant U as User/CI
    participant MK as Make/CLI
    participant APP as app.main
    participant IO as io.build_paths
    participant RUN as runner.run_backup_with_paths
    participant FS as FileSystem

    U->>MK: make backup
    Note over MK,APP: テストカバー: test_cli.py で mode 解釈を確認
    MK->>APP: python -m keep_backup.app --mode backup
    APP->>APP: load_dotenv_if_present()
    APP->>IO: build_paths(now)
    IO-->>APP: backup_file / log_file
    APP->>RUN: run_backup(note, notes_file)
    RUN->>RUN: build_notes(...)
    Note over RUN: テストカバー: test_runner_backup.py<br/>- 入力なしエラー<br/>- note + notes_file マージ
    RUN->>FS: append_log("run started ...")
    RUN->>FS: write_backup(keep.json)
    RUN->>FS: append_log("finished/duration/notes_count/output")
    RUN-->>U: stdout: summary success=... notes_count=... output=...
    Note over RUN,U: テストカバー: test_runner_finalize.py で<br/>共通ログ項目と summary 出力を確認

    alt 入力ノートが0件
      RUN->>FS: append_log("error=...")
      RUN-->>U: summary success=false + error=...
    end
```

## 要確認メモ
- README には将来の「ログイン済みプロファイルでの実Keep取得」方針があるが、現状の backup モードは手入力/ファイル入力ノートを JSON 化する薄い縦切り実装。実Keep全件取得のフローは未実装（要確認）。
