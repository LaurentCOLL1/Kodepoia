from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
R17_FIXTURE_SHA = "58e488d80e60d04fc675e305bc8f040a3ab2bb9c"

SUBDIVISION_AUTHORITIES: dict[str, tuple[str, ...]] = {
    "R18.1": (
        "scripts/r18_1_release_identity_acceptance.py",
        "tests/test_r18_release_identity.py",
    ),
    "R18.2": (
        "scripts/r18_2_release_bundle_acceptance.py",
        "tests/test_r18_release_bundle.py",
    ),
    "R18.3": (
        "scripts/r18_3_sbom_provenance_acceptance.py",
        "tests/test_r18_sbom_provenance.py",
    ),
    "R18.4": (
        "scripts/r18_4_authenticode_acceptance.py",
        "tests/test_r18_authenticode.py",
    ),
    "R18.5": (
        "scripts/r18_5_release_staging_acceptance.py",
        "tests/test_r18_5_release_promotion.py",
    ),
    "R18.6": (
        "scripts/r18_6_tuf_acceptance.py",
        "tests/test_r18_6_tuf_security.py",
        "tests/test_r18_6_update_trust.py",
    ),
    "R18.7": (
        "tests/test_r18_7_update_discovery.py",
        "tests/test_r18_7_kodestudio_updates.py",
    ),
    "R18.8": (
        "tests/test_r18_8_verified_delivery.py",
        "tests/test_r18_8_kodestudio_install.py",
    ),
    "R18.9": (
        "scripts/r18_9_winget_acceptance.py",
        "tests/test_r18_9_winget.py",
    ),
    "R18.10": (
        "scripts/r18_10_acceptance.py",
        "tests/test_r18_10_incident_drills.py",
        "tests/test_r18_10_kodestudio_incident.py",
    ),
}

SUBDIVISION_EVIDENCE_FILES = {
    subdivision: f"{subdivision.replace('.', '_')}.json" for subdivision in SUBDIVISION_AUTHORITIES
}

ADVERSARIAL_CONTROLS = (
    "tampered-bytes",
    "rollback-metadata",
    "freeze-metadata",
    "wrong-channel",
    "wrong-signature",
    "wrong-digest",
    "compromised-release",
)

WINDOWS_REQUIRED_TRUE = (
    "candidate_clean_install_smoke",
    "candidate_clean_install_uninstall_clean",
    "fixture_install_smoke",
    "candidate_upgrade_smoke",
    "candidate_manifest_source_match",
    "candidate_installer_digest_match",
    "upgrade_uninstall_clean",
)


def normalize_sha(value: str, *, field: str = "source_sha") -> str:
    normalized = value.strip().lower()
    if not SHA_RE.fullmatch(normalized):
        raise ValueError(f"{field} must be a lowercase-compatible 40-character Git SHA")
    return normalized


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def build_core_evidence(
    root: Path,
    evidence_dir: Path,
    source_sha: str,
    *,
    focused_regressions_passed: bool,
) -> dict[str, Any]:
    source = normalize_sha(source_sha)
    subdivisions: list[dict[str, Any]] = []
    blockers: list[str] = []

    for subdivision, relative_paths in SUBDIVISION_AUTHORITIES.items():
        missing = [path for path in relative_paths if not (root / path).is_file()]
        evidence_name = SUBDIVISION_EVIDENCE_FILES[subdivision]
        evidence_path = evidence_dir / evidence_name
        evidence = _read_json_object(evidence_path) if evidence_path.is_file() else {}
        evidence_source_match = evidence.get("source_sha") == source

        for path in missing:
            blockers.append(f"missing-authority:{subdivision}:{path}")
        if not evidence_path.is_file():
            blockers.append(f"missing-fresh-evidence:{subdivision}:{evidence_name}")
        elif not evidence_source_match:
            blockers.append(f"evidence-source-sha-mismatch:{subdivision}")

        status = "PASS" if not missing and evidence_path.is_file() and evidence_source_match else "FAIL"
        subdivisions.append(
            {
                "subdivision": subdivision,
                "authority_paths": list(relative_paths),
                "missing_paths": missing,
                "evidence_file": evidence_name,
                "evidence_source_match": evidence_source_match,
                "status": status,
            }
        )

    controls = [
        {
            "control": name,
            "expected": "REJECT",
            "observed": (
                "REJECTED_AS_EXPECTED"
                if focused_regressions_passed
                else "NOT_PROVEN"
            ),
            "status": "PASS" if focused_regressions_passed else "FAIL",
        }
        for name in ADVERSARIAL_CONTROLS
    ]
    if not focused_regressions_passed:
        blockers.append("focused-r18-regressions-not-proven")

    return {
        "schema_version": 1,
        "subdivision": "R18.11",
        "kind": "core-evidence",
        "source_sha": source,
        "subdivision_accounting": subdivisions,
        "focused_regressions": {
            "status": "PASS" if focused_regressions_passed else "FAIL",
            "covers": list(SUBDIVISION_AUTHORITIES),
        },
        "adversarial_controls": controls,
        "blockers": sorted(set(blockers)),
        "critical_veto": bool(blockers)
        or any(item["status"] != "PASS" for item in controls),
        "manual_intervention": "NONE",
        "production_effects": {
            "production_signing": "NOT_TRIGGERED",
            "public_github_release": "NOT_TRIGGERED",
            "production_tuf_custody_or_rotation": "NOT_TRIGGERED",
            "public_winget_submission": "NOT_TRIGGERED",
        },
    }


def finalize_integrated_report(
    source_sha: str,
    core: dict[str, Any],
    windows: dict[str, Any],
) -> dict[str, Any]:
    source = normalize_sha(source_sha)
    blockers: list[str] = []
    critical_veto = False

    if core.get("source_sha") != source:
        blockers.append("core-source-sha-mismatch")
        critical_veto = True
    if windows.get("candidate_source_sha") != source:
        blockers.append("windows-source-sha-mismatch")
        critical_veto = True
    if windows.get("fixture_source_sha") != R17_FIXTURE_SHA:
        blockers.append("windows-fixture-source-sha-mismatch")
        critical_veto = True

    subdivisions = core.get("subdivision_accounting")
    if not isinstance(subdivisions, list) or len(subdivisions) != 10:
        blockers.append("subdivision-accounting-incomplete")
        critical_veto = True
    else:
        seen = {
            item.get("subdivision")
            for item in subdivisions
            if isinstance(item, dict)
        }
        expected = set(SUBDIVISION_AUTHORITIES)
        if seen != expected:
            blockers.append("subdivision-accounting-set-mismatch")
            critical_veto = True
        for item in subdivisions:
            if not isinstance(item, dict) or item.get("status") != "PASS":
                name = (
                    item.get("subdivision", "unknown")
                    if isinstance(item, dict)
                    else "unknown"
                )
                blockers.append(f"subdivision-failed:{name}")

    focused = core.get("focused_regressions", {})
    if not isinstance(focused, dict) or focused.get("status") != "PASS":
        blockers.append("focused-regressions-failed")

    controls = core.get("adversarial_controls")
    if not isinstance(controls, list) or len(controls) != len(ADVERSARIAL_CONTROLS):
        blockers.append("adversarial-controls-incomplete")
        critical_veto = True
    else:
        for control in controls:
            if not isinstance(control, dict) or control.get("status") != "PASS":
                name = (
                    control.get("control", "unknown")
                    if isinstance(control, dict)
                    else "unknown"
                )
                blockers.append(f"negative-control-failed:{name}")
                critical_veto = True
            elif control.get("observed") != "REJECTED_AS_EXPECTED":
                name = control.get("control", "unknown")
                blockers.append(f"negative-control-unexpected-acceptance:{name}")
                critical_veto = True

    for key in WINDOWS_REQUIRED_TRUE:
        if windows.get(key) is not True:
            blockers.append(f"windows-cycle-failed:{key}")
            critical_veto = True

    for digest_key in ("fixture_installer_sha256", "candidate_installer_sha256"):
        digest = str(windows.get(digest_key, "")).strip().lower()
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            blockers.append(f"windows-invalid-digest:{digest_key}")
            critical_veto = True

    if windows.get("provider_effect_count") != 0:
        blockers.append("provider-effect-count-nonzero")
        critical_veto = True
    if windows.get("project_data_mutation") is not False:
        blockers.append("project-data-mutation-observed")
        critical_veto = True
    if windows.get("production_signing_performed") is not False:
        blockers.append("production-signing-unexpected")
        critical_veto = True
    if windows.get("public_release_effect") is not False:
        blockers.append("public-release-effect-unexpected")
        critical_veto = True
    if windows.get("public_winget_submission") is not False:
        blockers.append("public-winget-effect-unexpected")
        critical_veto = True

    inherited = core.get("blockers")
    if isinstance(inherited, list):
        blockers.extend(str(item) for item in inherited if str(item))

    blockers = sorted(set(blockers))
    if blockers:
        critical_veto = True

    return {
        "schema_version": 1,
        "subdivision": "R18.11",
        "status": "PASS" if not blockers and not critical_veto else "FAIL",
        "source_sha": source,
        "fixture_source_sha": R17_FIXTURE_SHA,
        "subdivision_accounting": (
            subdivisions if isinstance(subdivisions, list) else []
        ),
        "adversarial_controls": controls if isinstance(controls, list) else [],
        "windows_rc_cycle": windows,
        "blockers": blockers,
        "critical_veto": critical_veto,
        "manual_intervention": "NONE",
        "provider_effect_count": windows.get("provider_effect_count"),
        "project_data_mutation": windows.get("project_data_mutation"),
        "production_effects": {
            "production_signing": "NOT_TRIGGERED",
            "public_github_release": "NOT_TRIGGERED",
            "production_tuf_custody_or_rotation": "NOT_TRIGGERED",
            "public_winget_submission": "NOT_TRIGGERED",
        },
    }
