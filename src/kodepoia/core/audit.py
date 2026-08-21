from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any


@dataclass(frozen=True, slots=True)
class AuditEvent:
    timestamp: str
    category: str
    action: str
    actor: str
    outcome: str
    details: dict[str, Any]
    previous_hash: str
    event_hash: str


class AuditLog:
    """Append-only JSONL audit trail with a simple tamper-evident hash chain."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def _last_hash(self) -> str:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return "0" * 64
        last = self.path.read_text(encoding="utf-8").splitlines()[-1]
        return str(json.loads(last)["event_hash"])

    def append(self, category: str, action: str, actor: str, outcome: str, details: dict[str, Any] | None = None) -> AuditEvent:
        with self._lock:
            previous_hash = self._last_hash()
            payload = {"timestamp": datetime.now(UTC).isoformat(), "category": category, "action": action, "actor": actor, "outcome": outcome, "details": details or {}, "previous_hash": previous_hash}
            digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
            event = AuditEvent(**payload, event_hash=digest)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(asdict(event), ensure_ascii=False, sort_keys=True) + "\n")
            return event

    def verify(self) -> bool:
        previous = "0" * 64
        if not self.path.exists():
            return True
        for line in self.path.read_text(encoding="utf-8").splitlines():
            event = json.loads(line)
            expected_hash = event.pop("event_hash")
            if event.get("previous_hash") != previous:
                return False
            actual = hashlib.sha256(json.dumps(event, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
            if actual != expected_hash:
                return False
            previous = expected_hash
        return True
