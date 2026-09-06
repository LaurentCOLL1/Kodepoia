from __future__ import annotations

from pathlib import Path

from kodepoia.release.integrated_acceptance import (
    ADVERSARIAL_CONTROLS,
    R17_FIXTURE_SHA,
    SUBDIVISION_AUTHORITIES,
    build_core_evidence,
    finalize_integrated_report,
)

SOURCE = "a" * 40


def _populate_authorities(root: Path) -> None:
    for paths in SUBDIVISION_AUTHORITIES.values():
        for relative in paths:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("authority\n", encoding="utf-8")


def _windows() -> dict[str, object]:
    return {
        "candidate_source_sha": SOURCE,
        "fixture_source_sha": R17_FIXTURE_SHA,
        "fixture_installer_sha256": "1" * 64,
        "candidate_installer_sha256": "2" * 64,
        "fixture_install_smoke": True,
        "candidate_upgrade_smoke": True,
        "candidate_manifest_source_match": True,
        "candidate_installer_digest_match": True,
        "uninstall_clean": True,
        "provider_effect_count": 0,
        "project_data_mutation": False,
        "production_signing_performed": False,
        "public_release_effect": False,
        "public_winget_submission": False,
    }


def test_core_evidence_accounts_for_all_subdivisions(tmp_path: Path) -> None:
    _populate_authorities(tmp_path)
    report = build_core_evidence(tmp_path, SOURCE, focused_regressions_passed=True)
    assert report["blockers"] == []
    assert report["critical_veto"] is False
    assert [item["subdivision"] for item in report["subdivision_accounting"]] == list(
        SUBDIVISION_AUTHORITIES
    )
    assert len(report["adversarial_controls"]) == len(ADVERSARIAL_CONTROLS)
    assert all(item["status"] == "PASS" for item in report["adversarial_controls"])


def test_core_evidence_fails_closed_when_authority_is_missing(tmp_path: Path) -> None:
    report = build_core_evidence(tmp_path, SOURCE, focused_regressions_passed=True)
    assert report["blockers"]
    assert any(item["status"] == "FAIL" for item in report["subdivision_accounting"])


def test_integrated_report_passes_only_with_full_windows_cycle(tmp_path: Path) -> None:
    _populate_authorities(tmp_path)
    core = build_core_evidence(tmp_path, SOURCE, focused_regressions_passed=True)
    report = finalize_integrated_report(SOURCE, core, _windows())
    assert report["status"] == "PASS"
    assert report["blockers"] == []
    assert report["critical_veto"] is False
    assert report["manual_intervention"] == "NONE"


def test_integrated_report_vetoes_unexpected_negative_acceptance(tmp_path: Path) -> None:
    _populate_authorities(tmp_path)
    core = build_core_evidence(tmp_path, SOURCE, focused_regressions_passed=True)
    core["adversarial_controls"][0]["observed"] = "ACCEPTED_UNEXPECTEDLY"
    report = finalize_integrated_report(SOURCE, core, _windows())
    assert report["status"] == "FAIL"
    assert report["critical_veto"] is True
    assert any("negative-control-unexpected-acceptance" in item for item in report["blockers"])


def test_integrated_report_vetoes_provider_effect(tmp_path: Path) -> None:
    _populate_authorities(tmp_path)
    core = build_core_evidence(tmp_path, SOURCE, focused_regressions_passed=True)
    windows = _windows()
    windows["provider_effect_count"] = 1
    report = finalize_integrated_report(SOURCE, core, windows)
    assert report["status"] == "FAIL"
    assert report["critical_veto"] is True
    assert "provider-effect-count-nonzero" in report["blockers"]
