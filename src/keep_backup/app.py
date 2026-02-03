from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class RunPaths:
    backup_dir: Path
    backup_file: Path
    log_file: Path


def build_paths(now: datetime) -> RunPaths:
    date_stamp = now.strftime("%Y-%m-%d")
    log_stamp = now.strftime("%Y-%m-%d_%H%M%S")
    backup_dir = Path("backups") / date_stamp
    backup_file = backup_dir / "keep.json"
    log_file = Path("logs") / f"run_{log_stamp}.log"
    return RunPaths(backup_dir=backup_dir, backup_file=backup_file, log_file=log_file)


def append_log(log_file: Path, message: str) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(f"[{timestamp}] {message}\n")


def write_backup(backup_file: Path, now: datetime, notes: list[dict[str, str]]) -> None:
    backup_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "scraped_at": now.isoformat(),
        "notes": notes,
    }
    with backup_file.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main() -> int:
    start = datetime.now()
    paths = build_paths(start)
    append_log(paths.log_file, "run started")

    success = False
    notes: list[dict[str, str]] = []
    error_message = None

    try:
        notes = [{"body": "Hello World"}]
        write_backup(paths.backup_file, start, notes)
        success = True
    except Exception as exc:  # noqa: BLE001
        error_message = str(exc)
    finally:
        end = datetime.now()
        duration = (end - start).total_seconds()
        append_log(paths.log_file, f"run finished (success={success})")
        append_log(paths.log_file, f"duration_seconds={duration:.2f}")
        append_log(paths.log_file, f"notes_count={len(notes)}")
        append_log(paths.log_file, f"output={paths.backup_file}")
        if error_message:
            append_log(paths.log_file, f"error={error_message}")

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
