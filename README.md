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

Notes:
- `.env` is gitignored and must not be committed.
- CI runs are expected to leave `KEEP_BROWSER_PROFILE_DIR` unset, so no-profile smoke remains available.

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
3. Executes `uv run --with playwright python -m keep_backup.app --mode smoke-playwright`.
4. Validates stdout contains a `summary ...` line with `success=true` and no `error=` line.
5. Uploads `logs/run_*.log` as an artifact when the job fails.

## Local verification (same smoke mode)
You can reproduce CI smoke behavior locally:

```bash
uv lock --check
uv sync --locked
uv run --with playwright playwright install chromium
uv run --with playwright python -m keep_backup.app --mode smoke-playwright
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
