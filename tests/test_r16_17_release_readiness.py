from __future__ import annotations

import tomllib
from pathlib import Path

import kodepoia
from kodepoia.quality.release_readiness import (
    PRIOR_VERSION,
    RELEASE_VERSION,
    build_release_bom,
    release_documentation_evidence,
    run_migration_and_rollback_probe,
)
from kodepoia.release import CURRENT_RELEASE

ROOT = Path(__file__).resolve().parents[1]


def test_r16_17_release_baseline_remains_frozen_while_current_identity_advances() -> None:
    # R16.17 is historical evidence for the v1.0 RC baseline. R18.1 must not
    # rewrite that history, but the repository's current release identity is
    # now independently governed by the canonical release resolver.
    assert RELEASE_VERSION == "1.0.0rc1"
    assert PRIOR_VERSION == "0.1.0a4"

    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == CURRENT_RELEASE.pep440_version
    assert kodepoia.__version__ == CURRENT_RELEASE.pep440_version
    assert CURRENT_RELEASE.pep440_version == "1.1.0rc1"
    assert CURRENT_RELEASE.public_version == "1.1.0-rc1"


def test_r16_17_migration_and_failed_migration_rollback_are_exact() -> None:
    result = run_migration_and_rollback_probe(ROOT)
    assert result["success"]["status"] == "migrated"
    assert result["success"]["from_version"] == PRIOR_VERSION
    assert result["success"]["to_version"] == RELEASE_VERSION
    assert result["success"]["state_schema"] == 2
    assert result["success"]["backup_verified"] is True
    assert result["failure_recovery"]["status"] == "rolled_back"
    assert result["failure_recovery"]["backup_verified"] is True
    assert result["rollback_exact"] is True
    assert len(result["failure_recovery"]["restored_sha256"]) == 64


def test_r16_17_bom_and_license_unknowns_remain_truthful() -> None:
    bom, license_report, details = build_release_bom(ROOT)
    assert bom.inventory_complete is True
    assert bom.status.value == "warn"
    assert details["known_unknowns_preserved"] is True
    assert details["unresolved_component_ids"]
    assert details["spdx_compatibility"]["conformance_claim"] is False
    assert license_report.status.value == "warn"
    assert license_report.counts["unknown"] > 0
    assert not license_report.blockers


def test_r16_17_release_documentation_is_integrity_bound() -> None:
    docs = release_documentation_evidence(ROOT)
    assert set(docs) == {"release_notes", "security_operations"}
    assert all(item["bytes"] >= 400 for item in docs.values())
    assert all(len(item["sha256"]) == 64 for item in docs.values())
