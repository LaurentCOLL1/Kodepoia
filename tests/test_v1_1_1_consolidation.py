from __future__ import annotations

import json
import tomllib
from pathlib import Path

from kodepoia.release import CURRENT_RELEASE
from kodepoia.release.terminal_freeze import TERMINAL_RELEASE_FREEZE

ROOT = Path(__file__).resolve().parents[1]
TERMINAL_V2_MAIN = "913aef2cf4673a2c8b8b7874204fe1b11edcf225"


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v111_current_release_identity_advances_without_rewriting_v2_history() -> None:
    historical = TERMINAL_RELEASE_FREEZE.successor_identity

    assert historical.public_version == "1.1.0"
    assert historical.pep440_version == "1.1.0"
    assert CURRENT_RELEASE.public_version == "1.1.1"
    assert CURRENT_RELEASE.pep440_version == "1.1.1"
    assert CURRENT_RELEASE.channel == "stable"
    assert CURRENT_RELEASE.build_type == "release"
    assert CURRENT_RELEASE.is_newer_than(historical)

    pyproject = tomllib.loads(_read("pyproject.toml"))
    assert pyproject["project"]["version"] == "1.1.1"

    identity = json.loads(_read("src/kodepoia/release/release_identity.json"))
    assert identity["version"] == {
        "major": 1,
        "minor": 1,
        "patch": 1,
        "stage": "final",
        "serial": 0,
    }


def test_v111_authority_is_post_v2_release_maintenance_only() -> None:
    contract = _read("docs/release/V1_1_1_CONSOLIDATION.md")
    state = _read("docs/continuity/STATE.md")
    next_doc = _read("docs/continuity/NEXT.md")
    authority = _read("docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md")

    for source in (contract, state, next_doc, authority):
        assert "1.1.1" in source

    assert TERMINAL_V2_MAIN in contract
    assert "post-V2 maintenance consolidation release" in contract
    assert "does **not** create V2.7" in contract
    assert "authorize any new product capability" in contract.casefold()
    assert "offline Targets custody" in contract
    assert "1.1.0 -> 1.1.1" in contract


def test_v111_candidate_workflow_is_exact_source_and_non_publishing() -> None:
    workflow = _read(".github/workflows/v1-1-1-consolidation-candidate.yml")

    for marker in (
        "EVIDENCE_SHA: ${{ github.event.pull_request.head.sha || github.sha }}",
        f"TERMINAL_V2_MAIN_SHA: {TERMINAL_V2_MAIN}",
        "TARGET_TAG: v1.1.1",
        "TARGET_VERSION: 1.1.1",
        "Assert terminal V2 ancestry and release-only diff",
        "Verify v1.1.1 public namespace is absent",
        "Build 1.1.1 candidate one",
        "Build 1.1.1 candidate two",
        "Stage immutable 1.1.1 release description",
        "Clean install, packaged smoke and uninstall",
        "Emit 1.1.1 consolidation candidate evidence",
        "Upload 1.1.1 consolidation candidate evidence",
    ):
        assert marker in workflow, marker

    assert "permissions:\n  contents: read" in workflow
    assert "contents: write" not in workflow
    assert "gh release create" not in workflow
    assert "gh release upload" not in workflow
    assert "tuf_release_ceremony" not in workflow
    assert "signing-secret" not in workflow.casefold()


def test_v111_prepublication_tuf_truth_remains_1_1_0_baseline() -> None:
    root = json.loads(_read("update-repository/metadata/root.json"))
    targets = json.loads(_read("update-repository/metadata/targets.json"))
    snapshot = json.loads(_read("update-repository/metadata/snapshot.json"))
    timestamp = json.loads(_read("update-repository/metadata/timestamp.json"))

    assert root["signed"]["version"] == 2
    assert targets["signed"]["version"] == 9
    assert snapshot["signed"]["version"] == 11
    assert timestamp["signed"]["version"] == 11

    paths = set(targets["signed"]["targets"])
    assert any(path.startswith("channels/stable/windows-x86_64/1.1.0/") for path in paths)
    assert not any(path.startswith("channels/stable/windows-x86_64/1.1.1/") for path in paths)
