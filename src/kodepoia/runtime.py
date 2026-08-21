from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .core.audit import AuditLog
from .core.backup import KodeBackup
from .core.governance import KodeDataGovernance
from .core.guardian import KodeGuardian
from .core.paths import AppPaths
from .core.permissions import PermissionPolicy
from .core.recovery import KodeRecovery
from .core.research_guard import KodeResearchGuard
from .core.safe_change import SafeChangeManager
from .core.sandbox import KodeSandbox, SandboxProfile
from .core.schema import KodeSchema
from .core.secrets import MemorySecretStore, SecretBroker, WindowsCredentialManagerStore


@dataclass(slots=True)
class KodeRuntime:
    paths: AppPaths
    audit: AuditLog
    guardian: KodeGuardian
    sandbox: KodeSandbox
    secrets: SecretBroker
    schema: KodeSchema
    governance: KodeDataGovernance
    backup: KodeBackup
    recovery: KodeRecovery
    research_guard: KodeResearchGuard
    safe_change: SafeChangeManager

    @classmethod
    def build(cls, paths: AppPaths | None = None, *, sandbox_roots: tuple[Path, ...] | None = None) -> "KodeRuntime":
        paths = (paths or AppPaths.default()).ensure()
        audit = AuditLog(paths.data / "audit" / "audit.jsonl")
        guardian = KodeGuardian(PermissionPolicy.default(), audit)
        roots = sandbox_roots or (Path.cwd().resolve(),)
        allowed = frozenset({Path(os.environ.get("COMSPEC", "cmd.exe")).name, "python", "python.exe", "git", "git.exe", "godot", "godot.exe"})
        sandbox = KodeSandbox(guardian, SandboxProfile(allowed, tuple(roots)))
        if os.name == "nt":
            secret_store = WindowsCredentialManagerStore()
        else:
            secret_store = MemorySecretStore()
        secrets = SecretBroker(guardian, secret_store)
        schema = KodeSchema()
        governance = KodeDataGovernance()
        backup = KodeBackup(guardian, paths.data / "backups")
        recovery = KodeRecovery(paths.data / "recovery")
        research_guard = KodeResearchGuard(guardian)
        safe_change = SafeChangeManager(guardian, paths.data / "safe-change")
        return cls(paths, audit, guardian, sandbox, secrets, schema, governance, backup, recovery, research_guard, safe_change)
