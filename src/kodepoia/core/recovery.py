from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class RecoveryCheckpoint:
    task_id: str
    phase: str
    state: dict[str, Any]
    updated_at: str


class RecoveryJournal:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, task_id: str, phase: str, state: dict[str, Any]) -> RecoveryCheckpoint:
        checkpoint = RecoveryCheckpoint(task_id, phase, state, datetime.now(UTC).isoformat())
        self.path.write_text(json.dumps(asdict(checkpoint), ensure_ascii=False, indent=2), encoding="utf-8")
        return checkpoint

    def load(self) -> RecoveryCheckpoint | None:
        if not self.path.exists():
            return None
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return RecoveryCheckpoint(**data)

    def clear(self) -> None:
        self.path.unlink(missing_ok=True)
