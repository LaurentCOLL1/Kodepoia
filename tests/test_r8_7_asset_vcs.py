from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from kodepoia.assets import (
    AssetId,
    AssetKind,
    AssetVcsService,
    ProvenanceRef,
    ReuseScope,
    VcsFileState,
    VaultBoundary,
    VaultStore,
)
from kodepoia.kodecode.workspace import WorkspaceBoundary


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update({"GIT_AUTHOR_NAME": "Kodepoia CI", "GIT_AUTHOR_EMAIL": "ci@example.invalid", "GIT_COMMITTER_NAME": "Kodepoia CI", "GIT_COMMITTER_EMAIL": "ci@example.invalid"})
    return subprocess.run(["git", *args], cwd=root, env=env, text=True, capture_output=True, check=check)


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init")
    (root / ".gitignore").write_text("ignored.bin\n", encoding="utf-8")
    (root / "tracked.txt").write_text("alpha\n", encoding="utf-8")
    (root / "binary.bin").write_bytes(b"\x00\x01\x02")
    _git(root, "add", ".gitignore", "tracked.txt", "binary.bin")
    _git(root, "commit", "-m", "fixture")
    return root


def test_repository_status_is_typed_and_reports_ignored_untracked_modified(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "tracked.txt").write_text("beta\n", encoding="utf-8")
    (root / "new.txt").write_text("new\n", encoding="utf-8")
    (root / "ignored.bin").write_bytes(b"ignored")
    service = AssetVcsService(WorkspaceBoundary(root))

    status = service.repository_status()
    states = {item.path: item.state for item in status.files}
    assert status.head_sha and len(status.head_sha) == 40
    assert status.branch is not None
    assert states["tracked.txt"] is VcsFileState.MODIFIED
    assert states["new.txt"] is VcsFileState.UNTRACKED
    assert states["ignored.bin"] is VcsFileState.IGNORED


def test_binary_diff_never_fabricates_text_line_counts(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "binary.bin").write_bytes(b"\x00\xff\x02\x03")
    stat = AssetVcsService(WorkspaceBoundary(root)).diff_stat("binary.bin")
    assert stat.binary is True
    assert stat.added_lines is None
    assert stat.deleted_lines is None


def test_stage_and_unstage_are_explicit_audited_and_snapshotted(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "tracked.txt").write_text("changed\n", encoding="utf-8")
    service = AssetVcsService(WorkspaceBoundary(root))

    stage_snapshot = service.stage(["tracked.txt"])
    assert stage_snapshot is not None
    assert service.diff_stat("tracked.txt", staged=True).added_lines is not None
    unstage_snapshot = service.unstage(["tracked.txt"])
    assert unstage_snapshot is not None
    assert service.audit.verify() is True
    audit = (root / ".kodepoia" / "audit" / "asset-vcs.jsonl").read_text(encoding="utf-8")
    assert '"action": "stage"' in audit and '"action": "unstage"' in audit


def test_asset_vcs_rejects_path_escape_and_git_metadata(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    service = AssetVcsService(WorkspaceBoundary(root))
    with pytest.raises((ValueError, PermissionError)):
        service.stage(["../escape.txt"])
    with pytest.raises(ValueError):
        service.stage([".git/index"])


def test_vault_revision_to_path_commit_evidence(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    vault = tmp_path / "vault"
    store = VaultStore(VaultBoundary(vault))
    revision = store.ingest(
        project_boundary=WorkspaceBoundary(root),
        source_path="tracked.txt",
        asset_id=AssetId.from_seed("vcs", "tracked.txt"),
        kind=AssetKind.DOCUMENT,
        display_name="tracked.txt",
        provenance=(ProvenanceRef("repository", "fixture"),),
        reuse_scope=ReuseScope.VAULT_LOCAL,
    )
    service = AssetVcsService(WorkspaceBoundary(root), store=store)
    evidence = service.asset_evidence(revision.revision_id, "tracked.txt")
    assert evidence.tracked is True
    assert evidence.matches_revision is True
    assert evidence.last_commit_sha is not None
