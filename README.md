# keep-backup

Minimal starter for backing up Google Keep notes.

## Smoke run (no profile)
Run a Playwright startup smoke check without any login profile:

```bash
uv run python -m keep_backup.app --mode smoke-playwright
```

This mode verifies Chromium can launch and reach Google Keep, then prints the same CI-friendly summary lines.

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
