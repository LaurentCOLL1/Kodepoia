from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, TypeVar


@dataclass(slots=True)
class RecoveryCheckpoint:
    task_id: str
    phase: str
    state: dict[str, Any]
    updated_at: str


T = TypeVar("T")


class RecoveryJournal:
    """Durable single-task checkpoint journal.

    Writes are atomic within the destination filesystem: a fully flushed
    temporary file is replaced over the previous checkpoint only after the JSON
    payload has been written successfully.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, task_id: str, phase: str, state: dict[str, Any]) -> RecoveryCheckpoint:
        checkpoint = RecoveryCheckpoint(task_id, phase, state, datetime.now(UTC).isoformat())
        payload = json.dumps(asdict(checkpoint), ensure_ascii=False, indent=2)
        fd, temporary_name = tempfile.mkstemp(
            prefix=f".{self.path.name}.",
            suffix=".tmp",
            dir=self.path.parent,
            text=True,
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            temporary.replace(self.path)
        finally:
            temporary.unlink(missing_ok=True)
        return checkpoint

    def load(self) -> RecoveryCheckpoint | None:
        if not self.path.exists():
            return None
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Recovery checkpoint must be a JSON object")
        return RecoveryCheckpoint(
            task_id=str(data["task_id"]),
            phase=str(data["phase"]),
            state=dict(data["state"]),
            updated_at=str(data["updated_at"]),
        )

    def resume(self, handler: Callable[[RecoveryCheckpoint], T], *, clear_on_success: bool = True) -> T | None:
        checkpoint = self.load()
        if checkpoint is None:
            return None
        result = handler(checkpoint)
        if clear_on_success:
            self.clear()
        return result

    def clear(self) -> None:
        self.path.unlink(missing_ok=True)
