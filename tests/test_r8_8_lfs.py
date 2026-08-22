from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path

import pytest

from kodepoia.assets import (
    GitLfsService,
    LfsCapabilityState,
    LfsObjectState,
    LfsPointer,
    LfsPointerError,
    LfsWorkingState,
    REQUIRED_HEAVY_PATTERNS,
    parse_lfs_pointer,
)
from kodepoia.core.sandbox import SandboxResult
from kodepoia.kodecode.workspace import WorkspaceBoundary


def _pointer_bytes(payload: bytes) -> bytes:
    return LfsPointer(hashlib.sha256(payload).hexdigest(), len(payload)).canonical_bytes()


def _git(root: Path, *args: str) -> str:
    env = os.environ.copy()
    env.update({"GIT_AUTHOR_NAME": "Kodepoia CI", "GIT_AUTHOR_EMAIL": "ci@example.invalid", "GIT_COMMITTER_NAME": "Kodepoia CI", "GIT_COMMITTER_EMAIL": "ci@example.invalid"})
    result = subprocess.run(["git", *args], cwd=root, env=env, text=True, capture_output=True, check=True)
    return result.stdout


def test_pointer_roundtrip_is_canonical_and_malformed_forms_fail() -> None:
    payload = b"fixture-heavy-asset"
    pointer = LfsPointer(hashlib.sha256(payload).hexdigest(), len(payload))
    assert parse_lfs_pointer(pointer.canonical_bytes()) == pointer
    with pytest.raises(LfsPointerError):
        parse_lfs_pointer(pointer.canonical_bytes().replace(b"sha256:", b"sha1:"))
    with pytest.raises(LfsPointerError):
        parse_lfs_pointer(pointer.canonical_bytes().replace(b"size 19", b"size -1"))
    with pytest.raises(LfsPointerError):
        parse_lfs_pointer(pointer.canonical_bytes().rstrip(b"\n"), strict=True)


def test_missing_local_object_is_distinct_from_invalid_pointer(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init")
    (root / ".gitattributes").write_text("*.bin filter=lfs diff=lfs merge=lfs -text\n", encoding="utf-8")
    payload = b"large-content"
    pointer = _pointer_bytes(payload)
    (root / "asset.bin").write_bytes(pointer)
    _git(root, "add", ".gitattributes")
    subprocess.run(["git", "-c", "filter.lfs.clean=cat", "-c", "filter.lfs.required=false", "add", "asset.bin"], cwd=root, check=True, capture_output=True)

    diagnostic = GitLfsService(WorkspaceBoundary(root)).diagnose("asset.bin")
    assert diagnostic.pointer_state.value == "valid"
    assert diagnostic.object_state is LfsObjectState.MISSING
    assert diagnostic.working_state is LfsWorkingState.POINTER_ONLY

    bad = pointer.replace(b"sha256:", b"sha1:")
    (root / "asset.bin").write_bytes(bad)
    subprocess.run(["git", "-c", "filter.lfs.clean=cat", "-c", "filter.lfs.required=false", "add", "asset.bin"], cwd=root, check=True, capture_output=True)
    invalid = GitLfsService(WorkspaceBoundary(root)).diagnose("asset.bin")
    assert invalid.pointer_state.value == "invalid"
    assert invalid.object_state is LfsObjectState.UNAVAILABLE


def test_hydrated_content_oid_and_size_are_verified(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init")
    (root / ".gitattributes").write_text("*.bin filter=lfs diff=lfs merge=lfs -text\n", encoding="utf-8")
    payload = b"hydrated-bytes"
    pointer = _pointer_bytes(payload)
    (root / "asset.bin").write_bytes(pointer)
    subprocess.run(["git", "-c", "filter.lfs.clean=cat", "-c", "filter.lfs.required=false", "add", ".gitattributes", "asset.bin"], cwd=root, check=True, capture_output=True)
    (root / "asset.bin").write_bytes(payload)

    diagnostic = GitLfsService(WorkspaceBoundary(root)).diagnose("asset.bin")
    assert diagnostic.working_state is LfsWorkingState.HYDRATED_MATCH
    (root / "asset.bin").write_bytes(payload + b"tamper")
    mismatch = GitLfsService(WorkspaceBoundary(root)).diagnose("asset.bin")
    assert mismatch.working_state is LfsWorkingState.HYDRATED_MISMATCH


def test_tracking_update_requires_confirmation_and_is_audited(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init")
    (root / ".gitattributes").write_text("* text=auto\n", encoding="utf-8")
    service = GitLfsService(WorkspaceBoundary(root))
    proposal = service.propose_tracking("*.blend")
    assert proposal.endswith("filter=lfs diff=lfs merge=lfs -text")
    with pytest.raises(PermissionError):
        service.apply_tracking("*.blend", confirmed=False)
    service.apply_tracking("*.blend", confirmed=True)
    assert "*.blend filter=lfs diff=lfs merge=lfs -text" in (root / ".gitattributes").read_text(encoding="utf-8")
    assert service.audit.verify() is True


def test_repository_heavy_asset_policy_remains_complete() -> None:
    service = GitLfsService(WorkspaceBoundary(Path.cwd()))
    assert service.required_policy_gaps() == ()
    assert {item.pattern for item in service.tracking_rules()} >= set(REQUIRED_HEAVY_PATTERNS)


class _RecordingSandbox:
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    def run(self, argv, *, cwd=None, timeout=60.0, env=None):
        self.calls.append(tuple(str(item) for item in argv))
        if tuple(argv[1:]) == ("lfs", "version"):
            return SandboxResult(0, "git-lfs/3.7.0 (fixture)\n", "")
        if tuple(argv[1:]) == ("lfs", "ls-files", "--name-only"):
            return SandboxResult(0, "assets/a.blend\n", "")
        return SandboxResult(1, "", "unsupported fixture command")


def test_capability_and_listing_use_only_fixed_local_lfs_commands(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    sandbox = _RecordingSandbox()
    service = GitLfsService(WorkspaceBoundary(root), sandbox=sandbox)  # type: ignore[arg-type]
    capability = service.capability()
    assert capability.state is LfsCapabilityState.AVAILABLE
    assert capability.version == "3.7.0"
    assert service.lfs_files() == ("assets/a.blend",)
    assert sandbox.calls == [
        ("git", "lfs", "version"),
        ("git", "lfs", "version"),
        ("git", "lfs", "ls-files", "--name-only"),
    ]
    assert not any("fetch" in call or "push" in call or "pull" in call for call in sandbox.calls)
