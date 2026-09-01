from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from kodepoia.exceptions import PolicyDenied
from kodepoia.kodecode.quarantine import (
    QuarantinedKodeCodeExecutor,
    WorkspaceOperation,
    WorkspacePreflight,
    WorkspaceTrustState,
)


def test_new_workspace_is_quarantined_but_readable(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("build instructions only\n", encoding="utf-8")
    preflight = WorkspacePreflight(tmp_path)

    summary = preflight.require(WorkspaceOperation.READ)

    assert summary.state is WorkspaceTrustState.QUARANTINED
    assert summary.scanned_files == 1
    with pytest.raises(PolicyDenied, match="workspace is quarantined"):
        preflight.require(WorkspaceOperation.EXECUTE)


def test_exact_fingerprint_approval_and_material_change_invalidation(tmp_path: Path) -> None:
    source = tmp_path / "main.py"
    source.write_text("print('safe')\n", encoding="utf-8")
    preflight = WorkspacePreflight(tmp_path)
    initial = preflight.inspect()

    approved = preflight.require(
        WorkspaceOperation.WRITE,
        approved_fingerprint=initial.workspace_fingerprint,
    )
    assert approved.state is WorkspaceTrustState.APPROVED

    source.write_text("print('changed')\n", encoding="utf-8")
    changed = preflight.inspect(approved_fingerprint=initial.workspace_fingerprint)
    assert changed.state is WorkspaceTrustState.QUARANTINED
    assert changed.workspace_fingerprint != initial.workspace_fingerprint
    with pytest.raises(PolicyDenied, match="workspace is quarantined"):
        preflight.require(
            WorkspaceOperation.EXECUTE,
            approved_fingerprint=initial.workspace_fingerprint,
        )


def test_malicious_metadata_is_reported_without_execution_or_content_leak(tmp_path: Path) -> None:
    marker = tmp_path / "PWNED"
    script = tmp_path / "bootstrap.sh"
    sentinel = "SYNTHETIC_SECRET_CANARY_R16_3"
    script.write_text(f"touch {marker}\n# {sentinel}\n", encoding="utf-8")
    (tmp_path / ".gitmodules").write_text(
        '[submodule "outside"]\npath = deps/outside\nurl = https://example.invalid/repo.git\n',
        encoding="utf-8",
    )
    (tmp_path / "package.json").write_text(
        '{"scripts":{"postinstall":"./bootstrap.sh"},"permissions":"network"}\n',
        encoding="utf-8",
    )
    (tmp_path / "payload.zip").write_bytes(b"not-a-real-archive")

    summary = WorkspacePreflight(tmp_path).inspect()
    payload = json.dumps(summary.to_dict(), sort_keys=True)
    kinds = {item.kind for item in summary.findings}

    assert summary.state is WorkspaceTrustState.QUARANTINED
    assert {"executable-file", "external-reference", "task-metadata", "archive"} <= kinds
    assert not marker.exists()
    assert sentinel not in payload
    assert "example.invalid" not in payload


def test_external_symlink_escape_is_blocked_when_supported(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("outside\n", encoding="utf-8")
    link = tmp_path / "escape"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable on this runner")

    summary = WorkspacePreflight(tmp_path).inspect()

    assert summary.state is WorkspaceTrustState.BLOCKED
    assert summary.critical_veto is True
    assert any(item.id == "R16.3.WS.SYMLINK_ESCAPE" for item in summary.findings)
    with pytest.raises(PolicyDenied, match="critical preflight"):
        WorkspacePreflight(tmp_path).require(
            WorkspaceOperation.WRITE,
            approved_fingerprint=summary.workspace_fingerprint,
        )


def test_scan_bounds_fail_closed(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")

    summary = WorkspacePreflight(tmp_path, max_files=1).inspect()

    assert summary.state is WorkspaceTrustState.BLOCKED
    assert any(item.id == "R16.3.WS.BOUNDS" for item in summary.findings)


@dataclass
class _FakePolicy:
    effect: Any


class _FakeExecutor:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.calls: list[str] = []

    def policy(self, tool_name: str) -> _FakePolicy:
        effect = {
            "read": SimpleNamespace(value="read"),
            "write": SimpleNamespace(value="write"),
            "execute": SimpleNamespace(value="execute"),
        }[tool_name]
        return _FakePolicy(effect)

    def invoke(self, tool_name: str, arguments: dict[str, Any] | None = None, **kwargs: Any) -> str:
        self.calls.append(tool_name)
        return f"called:{tool_name}"


def test_quarantined_executor_separates_read_from_execution(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("print('data')\n", encoding="utf-8")
    inner = _FakeExecutor(tmp_path)
    executor = QuarantinedKodeCodeExecutor(inner)

    assert executor.invoke("read") == "called:read"
    with pytest.raises(PolicyDenied, match="workspace is quarantined"):
        executor.invoke("execute")
    assert inner.calls == ["read"]

    fingerprint = executor.inspect().workspace_fingerprint
    approved = executor.approve(fingerprint)
    assert approved.state is WorkspaceTrustState.APPROVED
    assert executor.invoke("execute") == "called:execute"
    assert inner.calls == ["read", "execute"]


def test_critical_workspace_cannot_be_approved(tmp_path: Path) -> None:
    (tmp_path / "large.bin").write_bytes(b"x" * 16)
    executor = QuarantinedKodeCodeExecutor(
        _FakeExecutor(tmp_path),
        preflight=WorkspacePreflight(tmp_path, max_bytes=8),
    )
    summary = executor.inspect()

    assert summary.state is WorkspaceTrustState.BLOCKED
    with pytest.raises(PolicyDenied, match="cannot be approved"):
        executor.approve(summary.workspace_fingerprint)
