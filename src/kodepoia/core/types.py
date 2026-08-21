from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DecisionStatus(StrEnum):
    ALLOW = "allow"
    CONFIRM = "confirm"
    DENY = "deny"


class ActionKind(StrEnum):
    FILE_READ = "file.read"
    FILE_WRITE = "file.write"
    FILE_DELETE = "file.delete"
    PROCESS_RUN = "process.run"
    NETWORK_REQUEST = "network.request"
    PACKAGE_INSTALL = "package.install"
    PLUGIN_INSTALL = "plugin.install"
    SECRET_READ = "secret.read"
    SECRET_WRITE = "secret.write"
    BACKUP_CREATE = "backup.create"
    BACKUP_RESTORE = "backup.restore"
    RESEARCH_INGEST = "research.ingest"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ActionRequest:
    kind: ActionKind
    actor: str
    project_root: Path | None = None
    target: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: uuid4().hex)


@dataclass(frozen=True, slots=True)
class GuardianDecision:
    status: DecisionStatus
    risk: RiskLevel
    reason: str
    request_id: str
    rule_id: str
    requires_snapshot: bool = False
    expires_after_seconds: int | None = None
