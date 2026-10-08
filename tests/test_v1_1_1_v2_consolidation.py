from __future__ import annotations

import json
import tomllib
from pathlib import Path

from kodepoia.release import CURRENT_RELEASE
from kodepoia.release.terminal_freeze import TERMINAL_RELEASE_FREEZE

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_current_release_is_1_1_1_stable_consolidation() -> None:
    assert CURRENT_RELEASE.public_version == "1.1.1"
    assert CURRENT_RELEASE.pep440_version == "1.1.1"
    assert CURRENT_RELEASE.channel == "stable"
    assert CURRENT_RELEASE.build_type == "release"
    assert CURRENT_RELEASE.is_newer_than(TERMINAL_RELEASE_FREEZE.successor_identity)

    pyproject = tomllib.loads(_read("pyproject.toml"))
    identity = json.loads(_read("src/kodepoia/release/release_identity.json"))
    assert pyproject["project"]["version"] == "1.1.1"
    assert identity["version"]["patch"] == 1


def test_v2_terminal_history_remains_frozen_at_1_1_0() -> None:
    freeze = TERMINAL_RELEASE_FREEZE
    assert freeze.successor_identity.public_version == "1.1.0"
    assert freeze.successor["tag"] == "v1.1.0"
    assert freeze.windows_installer["target_path_template"] == (
        "channels/stable/windows-x86_64/1.1.0/{source_sha}/KodepoiaSetup.exe"
    )
    assert freeze.no_new_feature_freeze["v2_7_authorized"] is False
    assert freeze.no_new_feature_freeze["r20_7_authorized"] is False


def test_consolidation_candidate_workflow_is_exact_source_and_non_publishing() -> None:
    workflow = _read(".github/workflows/v1-1-1-v2-consolidation-candidate.yml")
    for marker in (
        "EVIDENCE_SHA: ${{ github.event.pull_request.head.sha || github.sha }}",
        "Checkout exact consolidation source",
        "Assert exact checkout provenance",
        "Verify public 1.1.0 baseline and coherent 1.1.1 namespace",
        "Build exact-source consolidation candidate one",
        "Build exact-source consolidation candidate two",
        "Run R18 two-build semantic comparison",
        "Clean install packaged smoke and uninstall",
        "Emit 1.1.1 consolidation candidate evidence",
        "Upload 1.1.1 consolidation candidate evidence",
    ):
        assert marker in workflow, marker

    # Publication is immutable, so later PR checks must accept only the exact
    # frozen tag and single public installer, not claim that a live tag is absent.
    assert "Half-published 1.1.1 namespace" in workflow
    assert "Published 1.1.1 source drift" in workflow
    assert "Published 1.1.1 installer SHA256 drift" in workflow
    assert 'target_namespace_coherent = $true' in workflow
    assert '"target_namespace_coherent": baseline["target_namespace_coherent"] is True' in workflow

    assert "permissions:\n  contents: read" in workflow
    assert "contents: write" not in workflow
    assert "gh release create" not in workflow
    assert "gh release upload" not in workflow
    assert "git tag" not in workflow
    assert "tuf_release_ceremony" not in workflow


def test_consolidation_authority_does_not_reopen_v2() -> None:
    authority = _read("docs/release/V1_1_1_V2_CONSOLIDATION.md")
    assert "does not reopen V2" in authority
    assert "does not authorize V2.7, R20.7" in authority
    assert "1.1.0 -> 1.1.1" in authority
    assert "offline Targets custody ceremony" in authority
