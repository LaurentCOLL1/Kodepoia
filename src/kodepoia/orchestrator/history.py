from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ORCHESTRATION_HISTORY_SCHEMA_VERSION = 1
GENESIS_DIGEST = "0" * 64


def _canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    )


def _sha256_payload(payload: Any) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class OrchestrationHistoryRecord:
    sequence: int
    event: str
    plan_digest_sha256: str
    task_id: str = ""
    task_digest_sha256: str = ""
    workspace_id: str = ""
    state: str = ""
    evidence_digest_sha256: str = ""
    detail: str = ""
    previous_digest_sha256: str = GENESIS_DIGEST
    schema_version: int = ORCHESTRATION_HISTORY_SCHEMA_VERSION
    digest_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != ORCHESTRATION_HISTORY_SCHEMA_VERSION:
            raise ValueError("Unsupported orchestration history schema version")
        if self.sequence < 1:
            raise ValueError("History sequence must be positive")
        if not self.event.strip():
            raise ValueError("History event must not be empty")
        if len(self.previous_digest_sha256) != 64:
            raise ValueError("previous_digest_sha256 must be a SHA-256 digest")
        object.__setattr__(self, "event", self.event.strip())
        object.__setattr__(self, "detail", self.detail.strip())
        object.__setattr__(self, "digest_sha256", _sha256_payload(self._payload_without_digest()))

    def _payload_without_digest(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "sequence": self.sequence,
            "event": self.event,
            "plan_digest_sha256": self.plan_digest_sha256,
            "task_id": self.task_id,
            "task_digest_sha256": self.task_digest_sha256,
            "workspace_id": self.workspace_id,
            "state": self.state,
            "evidence_digest_sha256": self.evidence_digest_sha256,
            "detail": self.detail,
            "previous_digest_sha256": self.previous_digest_sha256,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._payload_without_digest()
        payload["digest_sha256"] = self.digest_sha256
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> OrchestrationHistoryRecord:
        record = cls(
            schema_version=int(payload.get("schema_version", 0)),
            sequence=int(payload["sequence"]),
            event=str(payload["event"]),
            plan_digest_sha256=str(payload.get("plan_digest_sha256", "")),
            task_id=str(payload.get("task_id", "")),
            task_digest_sha256=str(payload.get("task_digest_sha256", "")),
            workspace_id=str(payload.get("workspace_id", "")),
            state=str(payload.get("state", "")),
            evidence_digest_sha256=str(payload.get("evidence_digest_sha256", "")),
            detail=str(payload.get("detail", "")),
            previous_digest_sha256=str(payload.get("previous_digest_sha256", GENESIS_DIGEST)),
        )
        if record.digest_sha256 != str(payload.get("digest_sha256", "")):
            raise ValueError("Orchestration history record digest mismatch")
        return record


class OrchestrationHistoryStore:
    """Append-only, hash-chained operational history for one Kodepoia project."""

    def __init__(self, project_root: Path | str) -> None:
        root = Path(project_root).resolve(strict=False)
        self.path = root / ".kodepoia" / "orchestration" / "history.jsonl"

    def records(self) -> tuple[OrchestrationHistoryRecord, ...]:
        if not self.path.exists():
            return ()
        records: list[OrchestrationHistoryRecord] = []
        previous = GENESIS_DIGEST
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError("Invalid orchestration history entry")
            record = OrchestrationHistoryRecord.from_dict(payload)
            if record.previous_digest_sha256 != previous:
                raise ValueError("Orchestration history chain mismatch")
            if record.sequence != len(records) + 1:
                raise ValueError("Orchestration history sequence mismatch")
            records.append(record)
            previous = record.digest_sha256
        return tuple(records)

    def append(
        self,
        *,
        event: str,
        plan_digest_sha256: str,
        task_id: str = "",
        task_digest_sha256: str = "",
        workspace_id: str = "",
        state: str = "",
        evidence_digest_sha256: str = "",
        detail: str = "",
    ) -> OrchestrationHistoryRecord:
        existing = self.records()
        previous = existing[-1].digest_sha256 if existing else GENESIS_DIGEST
        record = OrchestrationHistoryRecord(
            sequence=len(existing) + 1,
            event=event,
            plan_digest_sha256=plan_digest_sha256,
            task_id=task_id,
            task_digest_sha256=task_digest_sha256,
            workspace_id=workspace_id,
            state=state,
            evidence_digest_sha256=evidence_digest_sha256,
            detail=detail,
            previous_digest_sha256=previous,
        )
        payload = [item.to_dict() for item in existing] + [record.to_dict()]
        self._write_atomic(payload)
        return record

    def _write_atomic(self, records: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                prefix=".history.",
                suffix=".tmp",
                dir=self.path.parent,
                delete=False,
            ) as handle:
                temporary_path = Path(handle.name)
                for record in records:
                    handle.write(_canonical_json(record))
                    handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, self.path)
            temporary_path = None
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink()
                except OSError:
                    pass


__all__ = [
    "GENESIS_DIGEST",
    "ORCHESTRATION_HISTORY_SCHEMA_VERSION",
    "OrchestrationHistoryRecord",
    "OrchestrationHistoryStore",
]
