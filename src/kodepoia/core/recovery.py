from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar


@dataclass(slots=True)
class RecoveryCheckpoint:
    task_id: str
    phase: str
    state: dict[str, Any]
    updated_at: str
    integrity_sha256: str | None = None


T = TypeVar("T")


class RecoveryJournal:
    """Durable single-task checkpoint journal with integrity-bound v2 writes.

    New checkpoints are written atomically within the destination filesystem and
    carry a SHA-256 digest over their canonical payload. Legacy v1 checkpoints
    remain readable for compatibility, but callers can require integrity-bound
    state before using a checkpoint as recovery authority.
    """

    SCHEMA_VERSION = 2

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _canonical_payload(
        task_id: str,
        phase: str,
        state: dict[str, Any],
        updated_at: str,
    ) -> bytes:
        payload = {
            "task_id": task_id,
            "phase": phase,
            "state": state,
            "updated_at": updated_at,
        }
        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    @classmethod
    def _integrity_digest(
        cls,
        task_id: str,
        phase: str,
        state: dict[str, Any],
        updated_at: str,
    ) -> str:
        return hashlib.sha256(
            cls._canonical_payload(task_id, phase, state, updated_at)
        ).hexdigest()

    def save(self, task_id: str, phase: str, state: dict[str, Any]) -> RecoveryCheckpoint:
        updated_at = datetime.now(UTC).isoformat()
        normalized_state = dict(state)
        integrity = self._integrity_digest(task_id, phase, normalized_state, updated_at)
        checkpoint = RecoveryCheckpoint(
            task_id,
            phase,
            normalized_state,
            updated_at,
            integrity,
        )
        payload = json.dumps(
            {
                "schema_version": self.SCHEMA_VERSION,
                **asdict(checkpoint),
            },
            ensure_ascii=False,
            indent=2,
        )
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
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)
        return checkpoint

    def load(
        self,
        *,
        require_integrity: bool = False,
        expected_task_id: str | None = None,
    ) -> RecoveryCheckpoint | None:
        if not self.path.exists():
            return None
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Recovery checkpoint must be a JSON object")

        schema_version = data.get("schema_version")
        if schema_version is None:
            if require_integrity:
                raise ValueError("Recovery checkpoint lacks integrity metadata")
            checkpoint = RecoveryCheckpoint(
                task_id=str(data["task_id"]),
                phase=str(data["phase"]),
                state=dict(data["state"]),
                updated_at=str(data["updated_at"]),
            )
        else:
            if int(schema_version) != self.SCHEMA_VERSION:
                raise ValueError(f"Unsupported recovery checkpoint schema: {schema_version}")
            state = dict(data["state"])
            task_id = str(data["task_id"])
            phase = str(data["phase"])
            updated_at = str(data["updated_at"])
            integrity = str(data.get("integrity_sha256") or "")
            expected = self._integrity_digest(task_id, phase, state, updated_at)
            if not integrity or integrity != expected:
                raise ValueError("Recovery checkpoint integrity verification failed")
            checkpoint = RecoveryCheckpoint(
                task_id=task_id,
                phase=phase,
                state=state,
                updated_at=updated_at,
                integrity_sha256=integrity,
            )

        if expected_task_id is not None and checkpoint.task_id != expected_task_id:
            raise ValueError(
                "Recovery checkpoint task mismatch: "
                f"expected {expected_task_id!r}, got {checkpoint.task_id!r}"
            )
        return checkpoint

    def resume(
        self,
        handler: Callable[[RecoveryCheckpoint], T],
        *,
        clear_on_success: bool = True,
        require_integrity: bool = False,
        expected_task_id: str | None = None,
    ) -> T | None:
        checkpoint = self.load(
            require_integrity=require_integrity,
            expected_task_id=expected_task_id,
        )
        if checkpoint is None:
            return None
        result = handler(checkpoint)
        if clear_on_success:
            self.clear()
        return result

    def clear(self) -> None:
        self.path.unlink(missing_ok=True)
