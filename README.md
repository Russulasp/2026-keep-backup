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
