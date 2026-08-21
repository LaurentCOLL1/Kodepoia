from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable

from .types import ActionKind, ActionRequest, DecisionStatus, RiskLevel


@dataclass(frozen=True, slots=True)
class PermissionRule:
    rule_id: str
    kind: ActionKind
    status: DecisionStatus
    risk: RiskLevel
    actor_pattern: str = "*"
    target_within_project: bool | None = None
    requires_snapshot: bool = False
    reason: str = "policy rule"

    def matches(self, request: ActionRequest) -> bool:
        if self.kind is not request.kind:
            return False
        if not fnmatch(request.actor, self.actor_pattern):
            return False
        if self.target_within_project is None:
            return True
        return _target_is_within_project(request) is self.target_within_project


def _target_is_within_project(request: ActionRequest) -> bool:
    if request.project_root is None or not request.target:
        return False
    try:
        root = request.project_root.resolve(strict=False)
        target = Path(request.target).resolve(strict=False)
        return target == root or target.is_relative_to(root)
    except (OSError, RuntimeError, ValueError):
        return False


class PermissionPolicy:
    """Ordered, default-deny capability policy used by KodeGuardian."""

    def __init__(self, rules: Iterable[PermissionRule] = ()) -> None:
        self._rules = tuple(rules)

    @property
    def rules(self) -> tuple[PermissionRule, ...]:
        return self._rules

    def find_rule(self, request: ActionRequest) -> PermissionRule | None:
        for rule in self._rules:
            if rule.matches(request):
                return rule
        return None

    @classmethod
    def default(cls) -> "PermissionPolicy":
        return cls((
            PermissionRule("deny-brain-secret-read", ActionKind.SECRET_READ, DecisionStatus.DENY, RiskLevel.CRITICAL, actor_pattern="*brain*", reason="raw secrets are never exposed to a language model"),
            PermissionRule("allow-secret-broker-read", ActionKind.SECRET_READ, DecisionStatus.ALLOW, RiskLevel.MEDIUM, actor_pattern="kodepoia.secret-broker", reason="secret access is delegated to the secret broker"),
            PermissionRule("allow-secret-broker-write", ActionKind.SECRET_WRITE, DecisionStatus.CONFIRM, RiskLevel.HIGH, actor_pattern="kodepoia.secret-broker", reason="storing or replacing a secret requires user approval"),
            PermissionRule("allow-project-read", ActionKind.FILE_READ, DecisionStatus.ALLOW, RiskLevel.LOW, target_within_project=True, reason="project reads are allowed inside the declared project root"),
            PermissionRule("allow-project-write-with-snapshot", ActionKind.FILE_WRITE, DecisionStatus.ALLOW, RiskLevel.MEDIUM, target_within_project=True, requires_snapshot=True, reason="project writes are allowed only with recoverable pre-image protection"),
            PermissionRule("confirm-project-delete", ActionKind.FILE_DELETE, DecisionStatus.CONFIRM, RiskLevel.HIGH, target_within_project=True, requires_snapshot=True, reason="deleting project data is destructive"),
            PermissionRule("confirm-process-run", ActionKind.PROCESS_RUN, DecisionStatus.CONFIRM, RiskLevel.HIGH, reason="process execution crosses the model/process trust boundary"),
            PermissionRule("confirm-network", ActionKind.NETWORK_REQUEST, DecisionStatus.CONFIRM, RiskLevel.MEDIUM, reason="network access can disclose data and is not implicit"),
            PermissionRule("confirm-package-install", ActionKind.PACKAGE_INSTALL, DecisionStatus.CONFIRM, RiskLevel.HIGH, reason="package installation changes the execution environment"),
            PermissionRule("confirm-plugin-install", ActionKind.PLUGIN_INSTALL, DecisionStatus.CONFIRM, RiskLevel.CRITICAL, reason="plugins may execute third-party code"),
            PermissionRule("allow-backup-create", ActionKind.BACKUP_CREATE, DecisionStatus.ALLOW, RiskLevel.LOW, reason="creating a local recovery snapshot is safe"),
            PermissionRule("confirm-backup-restore", ActionKind.BACKUP_RESTORE, DecisionStatus.CONFIRM, RiskLevel.HIGH, reason="restoring a snapshot overwrites current state"),
            PermissionRule("allow-research-ingest", ActionKind.RESEARCH_INGEST, DecisionStatus.ALLOW, RiskLevel.LOW, reason="research content is accepted only as untrusted data"),
        ))
