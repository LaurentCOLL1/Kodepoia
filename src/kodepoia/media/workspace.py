from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable


class WorkspaceState(StrEnum):
    READY = "READY"
    READY_WITH_ACCEPTED_EVIDENCE = "READY_WITH_ACCEPTED_EVIDENCE"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_PROBED = "NOT_PROBED"


@dataclass(frozen=True, slots=True)
class R11Capability:
    group: str
    title: str
    subdivision: str
    state: WorkspaceState
    runtime_state: WorkspaceState = WorkspaceState.NOT_PROBED
    accepted_evidence: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    operations: tuple[str, ...] = ("status",)

    def to_dict(self) -> dict[str, object]:
        return {
            "group": self.group,
            "title": self.title,
            "subdivision": self.subdivision,
            "state": self.state.value,
            "runtime_state": self.runtime_state.value,
            "accepted_evidence": list(self.accepted_evidence),
            "blockers": list(self.blockers),
            "operations": list(self.operations),
        }


_CAPABILITIES = (
    R11Capability("audio", "Audio", "R11.2", WorkspaceState.READY),
    R11Capability("cues", "Music / SFX / Foley cues", "R11.3", WorkspaceState.READY),
    R11Capability("voice", "Voice profiles", "R11.4", WorkspaceState.READY),
    R11Capability(
        "synthesis",
        "Local speech synthesis",
        "R11.5",
        WorkspaceState.READY_WITH_ACCEPTED_EVIDENCE,
        accepted_evidence=("docs/roadmap/R11_5_LOCAL_ACCEPTANCE.json",),
        operations=("status", "synthesis-status"),
    ),
    R11Capability("alignment", "Speech alignment / visemes", "R11.6", WorkspaceState.READY),
    R11Capability("facial", "Facial performance / LOD", "R11.7", WorkspaceState.READY),
    R11Capability("cinematics", "Cinematics", "R11.8-R11.9", WorkspaceState.READY_WITH_ACCEPTED_EVIDENCE,
        accepted_evidence=("docs/roadmap/R11_9_LOCAL_ACCEPTANCE.json",),
        operations=("status", "capture-status"),
    ),
    R11Capability("continuity", "Continuity Bridge", "R11.10", WorkspaceState.READY),
    R11Capability("franchise", "Franchise DNA", "R11.11", WorkspaceState.READY),
    R11Capability("canon", "Canon", "R11.11", WorkspaceState.READY),
    R11Capability("savebridge", "Persistence / SaveBridge", "R11.12", WorkspaceState.READY),
)


class R11WorkspaceService:
    """Read-only R11 capability surface shared by CLI and KodeStudio.

    The service intentionally does not probe external runtimes or expose raw
    process arguments. Runtime execution stays inside the already accepted R11
    domain adapters; this layer only presents accepted capability/evidence state.
    """

    schema_version = 1

    def __init__(self, capabilities: Iterable[R11Capability] | None = None) -> None:
        selected = tuple(capabilities or _CAPABILITIES)
        names = [item.group for item in selected]
        if len(names) != len(set(names)):
            raise ValueError("R11 capability groups must be unique")
        self._capabilities = {item.group: item for item in selected}

    @property
    def groups(self) -> tuple[str, ...]:
        return tuple(self._capabilities)

    def capability(self, group: str) -> R11Capability:
        try:
            return self._capabilities[group]
        except KeyError as exc:
            raise ValueError(f"Unknown R11 capability group: {group}") from exc

    def status_payload(self, group: str) -> dict[str, object]:
        item = self.capability(group)
        return {
            "schema_version": self.schema_version,
            "operation": "status",
            **item.to_dict(),
        }

    def summary_payload(self) -> dict[str, object]:
        capabilities = [self._capabilities[name].to_dict() for name in self.groups]
        blockers = [
            {"group": item.group, "blocker": blocker}
            for item in self._capabilities.values()
            for blocker in item.blockers
        ]
        return {
            "schema_version": self.schema_version,
            "operation": "summary",
            "state": WorkspaceState.BLOCKED.value if blockers else WorkspaceState.READY.value,
            "capabilities": capabilities,
            "blockers": blockers,
        }

    def exit_code_for(self, group: str) -> int:
        state = self.capability(group).state
        return 0 if state in {WorkspaceState.READY, WorkspaceState.READY_WITH_ACCEPTED_EVIDENCE} else 2


__all__ = ["R11Capability", "R11WorkspaceService", "WorkspaceState"]
