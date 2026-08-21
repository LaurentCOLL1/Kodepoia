from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class RecoveryState:
    task_id: str
    phase: str
    status: str
    payload: dict[str, Any]
    updated_at: str


class KodeRecovery:
    """Atomic task checkpoint store used to resume interrupted work."""

    def __init__(self, state_dir: Path) -> None:
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def checkpoint(self, task_id: str, phase: str, status: str, payload: dict[str, Any] | None = None) -> RecoveryState:
        state = RecoveryState(task_id, phase, status, payload or {}, datetime.now(UTC).isoformat())
        self._atomic_json(self.state_dir / f"{task_id}.json", asdict(state))
        return state

    def load(self, task_id: str) -> RecoveryState | None:
        path = self.state_dir / f"{task_id}.json"
        if not path.exists():
            return None
        return RecoveryState(**json.loads(path.read_text(encoding="utf-8")))

    def pending(self) -> list[RecoveryState]:
        result: list[RecoveryState] = []
        for path in sorted(self.state_dir.glob("*.json")):
            state = RecoveryState(**json.loads(path.read_text(encoding="utf-8")))
            if state.status not in {"complete", "cancelled"}:
                result.append(state)
        return result

    def complete(self, task_id: str, payload: dict[str, Any] | None = None) -> RecoveryState:
        current = self.load(task_id)
        phase = current.phase if current else "unknown"
        return self.checkpoint(task_id, phase, "complete", payload or (current.payload if current else {}))

    @staticmethod
    def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
        fd, temp_name = tempfile.mkstemp(prefix=".recovery-", suffix=".json", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(payload, stream, indent=2, sort_keys=True)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, path)
        except BaseException:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
            raise
