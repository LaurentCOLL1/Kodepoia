from pathlib import Path

from kodepoia.core.guardian import ActionRequest, ActionType, DecisionKind, KodeGuardian
from kodepoia.core.permissions import Capability, PermissionGrant, PermissionSet


def guardian(tmp_path: Path) -> KodeGuardian:
    permissions = PermissionSet()
    for capability in [Capability.FILE_READ, Capability.FILE_WRITE, Capability.FILE_DELETE]:
        permissions.grant(PermissionGrant(capability, roots=(tmp_path,)))
    permissions.grant(PermissionGrant(Capability.PROCESS_EXECUTE, executables=("python", "python.exe")))
    permissions.grant(PermissionGrant(Capability.NETWORK))
    permissions.grant(PermissionGrant(Capability.INSTALL))
    permissions.grant(PermissionGrant(Capability.SECRET_WRITE))
    return KodeGuardian(permissions)


def test_read_is_allowed(tmp_path: Path) -> None:
    decision = guardian(tmp_path).authorize(
        ActionRequest(ActionType.READ, "test", str(tmp_path / "a.txt"))
    )
    assert decision.kind is DecisionKind.ALLOW


def test_bulk_delete_requires_exact_bound_approval(tmp_path: Path) -> None:
    request = ActionRequest(ActionType.DELETE, "test", str(tmp_path), destructive_count=50)
    decision = guardian(tmp_path).authorize(request)
    assert decision.kind is DecisionKind.CONFIRM
    legacy_boolean = guardian(tmp_path).authorize(request, confirmed=True)
    assert legacy_boolean.kind is DecisionKind.CONFIRM
    assert "non-authoritative" in legacy_boolean.reason


def test_downloaded_unsandboxed_execution_is_denied(tmp_path: Path) -> None:
    request = ActionRequest(
        ActionType.EXECUTE,
        "test",
        downloaded=True,
        sandboxed=False,
        metadata={"executable": "python"},
    )
    assert guardian(tmp_path).authorize(request).kind is DecisionKind.DENY
