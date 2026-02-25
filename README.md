# keep-backup

Minimal starter for backing up Google Keep notes.

## Make commands (recommended entry)
Run the common entry points via `make` (container-first):

```bash
make docker-up
make smoke
make smoke-fixture
make backup
make docker-down
```

## 帰宅後にそのまま打てる実行順（迷わない版）
まずはリポジトリ直下で以下を順番に実行してください。

```bash
cd /path/to/2026-keep-backup
cp --update=none .env.example .env
make docker-up
```

次に `.env` を開いて、ログイン済みプロファイルの実パスを設定します。

```env
KEEP_BROWSER_PROFILE_DIR_HOST=/home/yourname/.config/google-chrome/Profile 1
KEEP_BROWSER_PROFILE_DIR_CONTAINER=/keep-profile
```

ここまでできたら、以下の順番で確認すると迷いにくいです。

```bash
make smoke
make smoke-fixture
make backup
```

Docker イメージ内の依存は `uv sync --locked` で `uv.lock` から解決されます。
ローカルで `pyproject.toml` / `uv.lock` を更新した場合は、`make docker-up`（`--build` 付き）を再実行して
イメージ内依存を同期してください。

ログイン済みプロファイルを Docker で使う場合は、`.env` の
`KEEP_BROWSER_PROFILE_DIR_HOST` に **WSL 側の絶対パス** を設定してください。
`docker-compose.yml` では `KEEP_BROWSER_PROFILE_DIR_HOST` を bind mount のソースに使い、
`KEEP_BROWSER_PROFILE_DIR_CONTAINER`（既定値 `/keep-profile`）をコンテナ側パスとして使います。
さらにアプリには `KEEP_BROWSER_PROFILE_DIR` としてコンテナ側パスを渡すため、
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

`make docker-up` now builds the local `Dockerfile`, which pins a Playwright-ready base image,
installs `uv`, and runs `uv sync --locked` during image build. `make docker-smoke` runs the app
through `uv run --no-sync`, so Docker execution also follows `pyproject.toml + uv.lock` as the
single dependency source of truth.

## Smoke run (no profile)
Run a Playwright startup smoke check without any login profile:

```bash
make smoke
```

This mode verifies Chromium can launch and reach Google Keep, then prints the same CI-friendly summary lines.

## Thin vertical slice (manual notes)
Provide a small set of note bodies manually and write a minimal `keep.json`:

```bash
docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode backup --note "買い物メモ" --note "次の会議アジェンダ"
```

You can also load one note per line from a text file:

```bash
docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode backup --notes-file notes.txt
```


## Logged-in browser profile configuration
This project treats the logged-in Chromium profile as an **external asset**.
Do not copy the profile folder into this repository.

1. Copy the sample file and set your local value:

```bash
cp .env.example .env
```

2. Set `KEEP_BROWSER_PROFILE_DIR_HOST` in `.env` to an absolute path on your machine (outside the repo). Optionally keep `KEEP_BROWSER_PROFILE_DIR_CONTAINER=/keep-profile`.

Example:

```env
KEEP_BROWSER_PROFILE_DIR_HOST=/home/yourname/.config/google-chrome/Profile 1
KEEP_BROWSER_PROFILE_DIR_CONTAINER=/keep-profile
```

3. Run smoke/backup as usual via Docker entry.
   - Docker (`docker compose ...`) 実行時は、`KEEP_BROWSER_PROFILE_DIR_HOST` を `KEEP_BROWSER_PROFILE_DIR_CONTAINER` に mount し、アプリへは `KEEP_BROWSER_PROFILE_DIR` としてコンテナ側パスを渡します。

Notes:
- `.env` is gitignored and must not be committed.
- CI runs are expected to leave `KEEP_BROWSER_PROFILE_DIR` / `KEEP_BROWSER_PROFILE_DIR_HOST` unset, so no-profile smoke remains available.



For temporary local experiments only, you may still use `uv run ...`, but it is not a standard operational entry.

## Runtime dependency policy
Runtime dependencies are declared in `pyproject.toml` and locked in `uv.lock`.

- Playwright (Python package) is included as a regular runtime dependency.
- `uv run --with ...` is reserved for temporary local experiments and is not a standard local/CI execution path.
- Browser binaries remain environment setup artifacts and are installed separately (`uv run playwright install chromium`).
- Docker image builds also install dependencies from lock via `uv sync --locked`, and runtime commands use `uv run`.

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

1. Builds the repository `Dockerfile` via `docker compose build app` so CI uses the same Playwright-ready container base.
2. Runs `docker compose run --rm app uv lock --check` inside the container for lock consistency.
3. Executes `docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode smoke-playwright-fixture` (no logged-in profile).
4. Validates stdout contains a `summary ...` line with `success=true` and no `error=` line.
5. Uploads `logs/run_*.log` as an artifact when the job fails.

## Local verification (same container smoke mode)
You can reproduce CI smoke behavior locally with Docker:

```bash
make docker-up
docker compose run --rm app uv lock --check
docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode smoke-playwright-fixture
make docker-down
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
