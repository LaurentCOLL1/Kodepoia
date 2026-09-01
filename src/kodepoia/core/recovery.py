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

from kodepoia.core.fault_injection import DeterministicFaultInjector


@dataclass(slots=True)
class RecoveryCheckpoint:
    task_id: str
    phase: str
    state: dict[str, Any]
    updated_at: str


T = TypeVar("T")


class RecoveryJournal:
    """Integrity-protected durable single-task checkpoint journal."""

    SCHEMA_VERSION = 2

    def __init__(
        self,
        path: Path,
        fault_injector: DeterministicFaultInjector | None = None,
    ) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fault_injector = fault_injector

    def _fault(self, stage: str) -> None:
        if self.fault_injector is not None:
            self.fault_injector.hit("recovery.save", stage)

    @staticmethod
    def _canonical_checkpoint(data: dict[str, Any]) -> bytes:
        return json.dumps(
            data,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    @classmethod
    def _digest(cls, data: dict[str, Any]) -> str:
        return hashlib.sha256(cls._canonical_checkpoint(data)).hexdigest()

    @classmethod
    def _decode(cls, raw: Any) -> RecoveryCheckpoint:
        if not isinstance(raw, dict):
            raise ValueError("Recovery checkpoint must be a JSON object")
        if raw.get("schema_version") != cls.SCHEMA_VERSION:
            raise ValueError("Recovery checkpoint lacks supported integrity metadata")
        checkpoint_data = raw.get("checkpoint")
        digest = raw.get("checkpoint_sha256")
        if not isinstance(checkpoint_data, dict) or not isinstance(digest, str):
            raise ValueError("Recovery checkpoint integrity envelope is invalid")
        if cls._digest(checkpoint_data) != digest:
            raise ValueError("Recovery checkpoint integrity verification failed")
        state = checkpoint_data.get("state")
        if not isinstance(state, dict):
            raise ValueError("Recovery checkpoint state must be a JSON object")
        try:
            return RecoveryCheckpoint(
                task_id=str(checkpoint_data["task_id"]),
                phase=str(checkpoint_data["phase"]),
                state=dict(state),
                updated_at=str(checkpoint_data["updated_at"]),
            )
        except KeyError as exc:
            raise ValueError(f"Recovery checkpoint field is missing: {exc.args[0]}") from exc

    def _load_validated(self) -> RecoveryCheckpoint:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Recovery checkpoint contains invalid JSON") from exc
        return self._decode(raw)

    def save(
        self,
        task_id: str,
        phase: str,
        state: dict[str, Any],
    ) -> RecoveryCheckpoint:
        checkpoint = RecoveryCheckpoint(
            task_id,
            phase,
            state,
            datetime.now(UTC).isoformat(),
        )
        checkpoint_data = asdict(checkpoint)
        envelope = {
            "schema_version": self.SCHEMA_VERSION,
            "checkpoint": checkpoint_data,
            "checkpoint_sha256": self._digest(checkpoint_data),
        }
        payload = json.dumps(envelope, ensure_ascii=False, indent=2)

        self._fault("prepare")
        fd, temporary_name = tempfile.mkstemp(
            prefix=f".{self.path.name}.",
            suffix=".tmp",
            dir=self.path.parent,
            text=True,
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                self._fault("write")
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            self._fault("commit")
            temporary.replace(self.path)
            self._fault("verify")
            persisted = self._load_validated()
            if asdict(persisted) != checkpoint_data:
                raise OSError("Persisted recovery checkpoint differs from the requested state")
            self._fault("cleanup")
        finally:
            temporary.unlink(missing_ok=True)
        return checkpoint

    def load(self) -> RecoveryCheckpoint | None:
        if not self.path.exists():
            return None
        return self._load_validated()

    def resume(
        self,
        handler: Callable[[RecoveryCheckpoint], T],
        *,
        clear_on_success: bool = True,
    ) -> T | None:
        checkpoint = self.load()
        if checkpoint is None:
            return None
        result = handler(checkpoint)
        if clear_on_success:
            self.clear()
        return result

    def clear(self) -> None:
        self.path.unlink(missing_ok=True)
