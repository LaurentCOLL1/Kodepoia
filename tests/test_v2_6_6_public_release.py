from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "v2-6-6-public-release.yml"
TARGETS = ROOT / "update-repository" / "metadata" / "targets.json"
SNAPSHOT = ROOT / "update-repository" / "metadata" / "snapshot.json"
TIMESTAMP = ROOT / "update-repository" / "metadata" / "timestamp.json"

CANDIDATE_SHA = "46ed800888b4f19da9e984232dd1ad6cdb639cc1"
CANDIDATE_SHA256 = "8197bc9d8272b97394170a2c7c27b17c1e2f2849931587d21c7bdfda126da2ef"
CANDIDATE_BYTES = 38_834_833
STABLE_TARGET = (
    "channels/stable/windows-x86_64/1.1.0/"
    "46ed800888b4f19da9e984232dd1ad6cdb639cc1/KodepoiaSetup.exe"
)


def test_v266_publication_inputs_match_live_tuf_transition() -> None:
    targets = json.loads(TARGETS.read_text(encoding="utf-8"))
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    timestamp = json.loads(TIMESTAMP.read_text(encoding="utf-8"))

    assert targets["signed"]["version"] == 9
    assert snapshot["signed"]["version"] == 11
    assert timestamp["signed"]["version"] == 11

    target = targets["signed"]["targets"][STABLE_TARGET]
    assert target["length"] == CANDIDATE_BYTES
    assert target["hashes"]["sha256"] == CANDIDATE_SHA256
    assert target["custom"]["source_sha"] == CANDIDATE_SHA
    assert target["custom"]["public_version"] == "1.1.0"
    assert target["custom"]["channel"] == "stable"
    assert target["custom"]["authenticode_policy"] == "allow-unsigned"
    assert target["custom"]["withdrawn"] is False


def test_v266_public_release_workflow_is_manual_main_only_and_exact_source() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in source
    assert "github.ref == 'refs/heads/main'" in source
    assert "contents: write" in source
    assert "actions: read" in source
    assert "pull_request:" not in source
    assert "push:" not in source
    assert "create:" not in source

    assert "37151521725" in source
    assert "v2-6-3-windows-candidate-" + CANDIDATE_SHA in source
    assert CANDIDATE_SHA256 in source
    assert 'CANDIDATE_BYTES: "38834833"' in source
    assert "80192b517ebd6a607536f52892e5b23d05448138e63d7d222c30c7f4444dc3d8" in source

    assert 'gh release create "$TAG"' in source
    assert '--target "$CANDIDATE_SHA"' in source
    assert 'gh release upload "$TAG"' in source
    assert "--clobber" not in source
    assert 'gh release download "$TAG"' in source

    assert "production signing trust is claimed" in source
    assert "WinGet: not published for 1.1.0" in source
    assert "winget_submission" in source
    assert '"production_signed": False' in source


def test_v266_public_release_workflow_refuses_conflicting_immutable_state() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")

    assert "Conflicting immutable tag" in source
    assert "Existing release conflicts with immutable terminal release identity" in source
    assert "Conflicting duplicate KodepoiaSetup.exe assets" in source
    assert "public installer SHA-256 mismatch" in source
    assert "public installer byte length mismatch" in source
    assert "GitHub release asset size mismatch" in source


def test_v266_publication_workflow_rechecks_live_tuf_before_public_write() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    tuf_index = source.index("Verify coherent live production TUF v9 v11 v11")
    release_index = source.index("Create or recover exact immutable GitHub Release")
    assert tuf_index < release_index
    assert 'assert targets["signed"]["version"] == 9' in source
    assert 'assert snapshot["signed"]["version"] == 11' in source
    assert 'assert timestamp["signed"]["version"] == 11' in source
    assert "metadata is expired at publication time" in source
