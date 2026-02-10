from __future__ import annotations

import json
import os
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


def load_notes_from_file(notes_file: Path) -> list[dict[str, str]]:
    if not notes_file.exists():
        raise FileNotFoundError(f"notes file not found: {notes_file}")
    notes: list[dict[str, str]] = []
    with notes_file.open("r", encoding="utf-8") as handle:
        for line in handle:
            body = line.strip()
            if body:
                notes.append({"body": body})
    return notes


def load_dotenv_if_present(dotenv_path: Path = Path(".env")) -> None:
    if not dotenv_path.exists():
        return
    with dotenv_path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


def format_bool(value: bool) -> str:
    return str(value).lower()
