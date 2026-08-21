from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_type: str
    actor: str
    outcome: str
    request_id: str | None = None
    details: Mapping[str, Any] | None = None
    timestamp: str = ""

    def normalized(self) -> dict[str, Any]:
        data = asdict(self)
        if not data["timestamp"]:
            data["timestamp"] = datetime.now(UTC).isoformat()
        return data


class AuditLog:
    """Append-only JSONL audit log with per-process serialization and fsync."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def append(self, event: AuditEvent) -> None:
        payload = json.dumps(event.normalized(), ensure_ascii=False, sort_keys=True)
        with self._lock:
            with self.path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(payload + "\n")
                stream.flush()
                os.fsync(stream.fileno())

    def tail(self, limit: int = 100) -> list[dict[str, Any]]:
        if limit <= 0 or not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()[-limit:]
        return [json.loads(line) for line in lines if line.strip()]
