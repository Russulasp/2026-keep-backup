# keep-backup

Minimal starter for backing up Google Keep notes.

## Make commands (recommended entry)
Run the common entry points via `make`:

```bash
make smoke
```

```bash
make smoke-fixture
```

```bash
make backup
```

## 帰宅後にそのまま打てる実行順（迷わない版）
まずはリポジトリ直下で以下を順番に実行してください。

```bash
cd /path/to/2026-keep-backup
uv lock --check
uv sync --locked
uv run playwright install chromium
cp --update=none .env.example .env
```

次に `.env` を開いて、ログイン済みプロファイルの実パスを設定します。

```env
KEEP_BROWSER_PROFILE_DIR=/home/yourname/.config/google-chrome/Profile 1
```

ここまでできたら、以下の順番で確認すると迷いにくいです。

```bash
make smoke
make smoke-fixture
uv run python -m keep_backup.app --mode backup --note "買い物メモ"
```

Docker 経由で確認したい場合は、次の順で実行します。

```bash
make docker-up
make docker-smoke
make docker-down
```

ログイン済みプロファイルを Docker で使う場合は、`.env` の
`KEEP_BROWSER_PROFILE_DIR` に **WSL 側の絶対パス** を設定してください。
`docker-compose.yml` でそのパスを `/keep-profile` に bind mount し、
コンテナ内では `KEEP_BROWSER_PROFILE_DIR=/keep-profile` を使うため、
WSL と Docker のパス差分を意識せずに実行できます。

## Docker Compose (optional)
If you want to keep a Playwright-ready container around, start it with:

```bash
make docker-up
```

Stop it with:

```bash
make docker-down
```

You can also run the smoke check through Docker:

```bash
make docker-smoke
```

## Smoke run (no profile)
Run a Playwright startup smoke check without any login profile:

```bash
uv run python -m keep_backup.app --mode smoke-playwright
```

This mode verifies Chromium can launch and reach Google Keep, then prints the same CI-friendly summary lines.

## Thin vertical slice (manual notes)
Provide a small set of note bodies manually and write a minimal `keep.json`:

```bash
uv run python -m keep_backup.app --mode backup --note "買い物メモ" --note "次の会議アジェンダ"
```

You can also load one note per line from a text file:

```bash
uv run python -m keep_backup.app --mode backup --notes-file notes.txt
```


## Logged-in browser profile configuration
This project treats the logged-in Chromium profile as an **external asset**.
Do not copy the profile folder into this repository.

1. Copy the sample file and set your local value:

```bash
cp .env.example .env
```

2. Set `KEEP_BROWSER_PROFILE_DIR` in `.env` to an absolute path on your machine (outside the repo).

Example:

```env
KEEP_BROWSER_PROFILE_DIR=/home/yourname/.config/google-chrome/Profile 1
```

3. Run smoke/backup as usual. The app reads only `KEEP_BROWSER_PROFILE_DIR` and does not depend on a hard-coded profile location.
   - ローカル (`uv run ...`) 実行時は `.env` の実パスをそのまま使います。
   - Docker (`docker compose ...`) 実行時は、指定したパスを `/keep-profile` に mount して参照します。

Notes:
- `.env` is gitignored and must not be committed.
- CI runs are expected to leave `KEEP_BROWSER_PROFILE_DIR` unset, so no-profile smoke remains available.


## Runtime dependency policy
Runtime dependencies are declared in `pyproject.toml` and locked in `uv.lock`.

- Playwright (Python package) is included as a regular runtime dependency.
- `uv run --with ...` is reserved for temporary local experiments and is not a standard local/CI execution path.
- Browser binaries remain environment setup artifacts and are installed separately (`uv run playwright install chromium`).

## CI summary and notifications
The app prints a minimal stdout summary for CI consumption:

```
summary success=true notes_count=123 duration_seconds=4.20 output=backups/2025-01-01/keep.json
```

If an error occurs, an additional line is printed with the message:

```
error=...
```

CI can use these stdout lines directly for pass/fail checks and optional email notifications.
Configure the following secrets in CI:

* `SMTP_USERNAME`: sender (Gmail address)
* `SMTP_PASSWORD`: 16-character app password (label `github-actions`)
* `NOTIFY_EMAIL`: notification recipient


## CI (PR) no-profile smoke
Pull requests to `main` run `.github/workflows/no-profile-smoke-pr.yml`.

What this workflow does:

1. Runs `uv lock --check` and `uv sync --locked` for lock consistency.
2. Installs Playwright Chromium in CI (`playwright install --with-deps chromium`) without using a logged-in profile.
3. Executes `uv run python -m keep_backup.app --mode smoke-playwright`.
4. Validates stdout contains a `summary ...` line with `success=true` and no `error=` line.
5. Uploads `logs/run_*.log` as an artifact when the job fails.

## Local verification (same smoke mode)
You can reproduce CI smoke behavior locally:

```bash
uv lock --check
uv sync --locked
uv run playwright install chromium
uv run python -m keep_backup.app --mode smoke-playwright
```

Expected stdout:

- `summary success=true ...`
- No `error=...` line

## Future additions
Planned additions (to be refined as the project matures):

- Windows entry batch (`backup_keep.bat`) that only dispatches to WSL/Docker.
- WSL entry that calls the shared Docker Compose command.
- Logged-in browser profile handling for the real Keep scrape.
- Standard vertical slice implementation (normal/archive/trash full backup).
- Artifact capture for failures (`logs/artifacts/`).
