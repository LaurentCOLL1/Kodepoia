from __future__ import annotations

import hashlib
import json
import tempfile
from datetime import datetime
from pathlib import Path

from kodepoia.release.identity import ReleaseIdentity
from kodepoia.release.incident import run_synthetic_incident_drills
from kodepoia.release.tuf_transition_staging import (
    REFERENCE_TIME,
    build_transition_request,
    production_observation,
    validate_transition_request,
)
from kodepoia.update.corrective import (
    AUTHENTICODE_POLICY_ALLOW_UNSIGNED,
    PolicyUpdateDiscoveryCandidate,
    PolicyVerifiedUpdateDownloader,
)
from kodepoia.update.delivery import (
    AuthenticodeVerifier,
    InstallerIdentityVerifier,
    MemoryStreamingTargetTransport,
)
from kodepoia.update.discovery import UpdateDiscoveryCandidate, UpdateDiscoveryService
from kodepoia.update.trust import (
    MemoryUpdateTransport,
    PackagedRootPin,
    SyntheticUpdateRepositoryBuilder,
    UpdateTargetSpec,
)

RC8_PUBLIC_VERSION = "1.1.0-rc8"
RC8_SOURCE_SHA = "fa787ab7ef76f2556b56ac1f058916a1425455af"
RC8_INSTALLER_BYTES = 37_730_750
RC8_INSTALLER_SHA256 = "6d4a02dc448b075341baf4b6fb0caf4d0a116e1b82a6937a5911efc863611422"

CANDIDATE_PUBLIC_VERSION = "1.1.0"
CANDIDATE_SOURCE_SHA = "46ed800888b4f19da9e984232dd1ad6cdb639cc1"
CANDIDATE_INSTALLER_BYTES = 38_834_833
CANDIDATE_INSTALLER_SHA256 = (
    "8197bc9d8272b97394170a2c7c27b17c1e2f2849931587d21c7bdfda126da2ef"
)
CANDIDATE_V263_EVIDENCE_SHA256 = (
    "80192b517ebd6a607536f52892e5b23d05448138e63d7d222c30c7f4444dc3d8"
)
V263_ARTIFACT_RUN_ID = 37_151_521_725
V263_ARTIFACT_ID = 11_284_279_492
V263_ARTIFACT_NAME = (
    "v2-6-3-windows-candidate-46ed800888b4f19da9e984232dd1ad6cdb639cc1"
)

V264_ACCEPTED_HEAD = "addbaf43b286f825ce42a11176c6647d15748845"
V264_REQUEST_SHA256 = "a44914e80fb2fafb6b03f2a9847a78805b1ccb2a87fafedae9199f66c88bacea"

PUBLIC_TAG = "v1.1.0"
TARGET_PATH = (
    "channels/stable/windows-x86_64/1.1.0/"
    "46ed800888b4f19da9e984232dd1ad6cdb639cc1/KodepoiaSetup.exe"
)


def _canonical_digest(payload: dict[str, object]) -> str:
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _release_identity(*, public_version: str) -> ReleaseIdentity:
    if public_version == RC8_PUBLIC_VERSION:
        return ReleaseIdentity(
            schema_version=1,
            product="Kodepoia",
            package="kodepoia",
            channel="beta",
            build_type="prerelease",
            source_binding="exact-head",
            major=1,
            minor=1,
            patch=0,
            stage="rc",
            serial=8,
        )
    if public_version == CANDIDATE_PUBLIC_VERSION:
        return ReleaseIdentity(
            schema_version=1,
            product="Kodepoia",
            package="kodepoia",
            channel="stable",
            build_type="release",
            source_binding="exact-head",
            major=1,
            minor=1,
            patch=0,
            stage="final",
            serial=0,
        )
    raise ValueError(f"unsupported V2.6.5 installed version: {public_version!r}")


def candidate_target() -> UpdateTargetSpec:
    target = UpdateTargetSpec(
        channel="stable",
        platform="windows-x86_64",
        public_version=CANDIDATE_PUBLIC_VERSION,
        source_sha=CANDIDATE_SOURCE_SHA,
        filename="KodepoiaSetup.exe",
    )
    if target.path != TARGET_PATH:
        raise ValueError("frozen V2.6.5 target path drift")
    return target


def reconstruct_v264_request(repository_root: Path) -> dict[str, object]:
    observation = production_observation(
        repository_root / "update-repository" / "metadata",
        reference_time=REFERENCE_TIME,
    )
    request = build_transition_request(V264_ACCEPTED_HEAD, observation)
    validate_transition_request(request)
    if request.get("request_sha256") != V264_REQUEST_SHA256:
        raise ValueError("accepted V2.6.4 transition request digest drift")
    target = dict(request["requested_target"])
    if target.get("path") != TARGET_PATH:
        raise ValueError("accepted V2.6.4 target path drift")
    if target.get("length") != CANDIDATE_INSTALLER_BYTES:
        raise ValueError("accepted V2.6.4 target length drift")
    if target.get("sha256") != CANDIDATE_INSTALLER_SHA256:
        raise ValueError("accepted V2.6.4 target hash drift")
    custom = dict(target.get("custom") or {})
    if custom.get("authenticode_policy") != AUTHENTICODE_POLICY_ALLOW_UNSIGNED:
        raise ValueError("accepted V2.6.4 Authenticode policy drift")
    return request


def validate_frozen_installer(
    path: Path,
    *,
    expected_size: int,
    expected_sha256: str,
    label: str,
) -> dict[str, object]:
    if not path.is_file():
        raise ValueError(f"{label} installer is missing: {path}")
    size = path.stat().st_size
    digest = _file_sha256(path)
    if size != expected_size:
        raise ValueError(f"{label} installer length mismatch: {size} != {expected_size}")
    if digest != expected_sha256:
        raise ValueError(f"{label} installer SHA-256 mismatch: {digest}")
    return {"path": str(path), "size_bytes": size, "sha256": digest}


def validate_v263_evidence(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if payload.get("status") != "PASS":
        raise ValueError("V2.6.3 accepted candidate evidence is not PASS")
    if payload.get("candidate_source_sha") != CANDIDATE_SOURCE_SHA:
        raise ValueError("V2.6.3 candidate source SHA drift")
    if payload.get("evidence_sha256") != CANDIDATE_V263_EVIDENCE_SHA256:
        raise ValueError("V2.6.3 evidence digest drift")
    return payload


def synthetic_transition_status(
    *,
    installer: bytes,
    installed_public_version: str,
    state_dir: Path,
    reference_time: datetime = REFERENCE_TIME,
) -> tuple[str, UpdateDiscoveryCandidate | None]:
    target = candidate_target()
    repository = SyntheticUpdateRepositoryBuilder().build(
        target,
        installer,
        timestamp_version=11,
        snapshot_version=11,
        targets_version=9,
    )
    transport = MemoryUpdateTransport.from_repository(repository)
    service = UpdateDiscoveryService(
        state_dir,
        root_pin=PackagedRootPin.from_root(repository.root),
        transport=transport,
        platform="windows-x86_64",
        installed_release=_release_identity(public_version=installed_public_version),
        reference_time=reference_time,
    )
    result = service.check("stable")
    return result.status, result.candidate


def _policy_candidate(candidate: UpdateDiscoveryCandidate) -> PolicyUpdateDiscoveryCandidate:
    return PolicyUpdateDiscoveryCandidate(
        target=candidate.target,
        size_bytes=candidate.size_bytes,
        sha256=candidate.sha256,
        source_verification_state=candidate.source_verification_state,
        release_notes_summary=candidate.release_notes_summary,
        signing_status=candidate.signing_status,
        provenance_status=candidate.provenance_status,
        withdrawn=candidate.withdrawn,
        authenticode_policy=AUTHENTICODE_POLICY_ALLOW_UNSIGNED,
    )


def build_contract_report(
    development_sha: str,
    *,
    repository_root: Path,
) -> dict[str, object]:
    request = reconstruct_v264_request(repository_root)
    fixture = b"v2.6.5 cross-platform contract fixture\n"
    with tempfile.TemporaryDirectory(prefix="kodepoia-v265-contract-rc8-") as temp:
        rc8_status, rc8_candidate = synthetic_transition_status(
            installer=fixture,
            installed_public_version=RC8_PUBLIC_VERSION,
            state_dir=Path(temp),
        )
    with tempfile.TemporaryDirectory(prefix="kodepoia-v265-contract-stable-") as temp:
        stable_status, stable_candidate = synthetic_transition_status(
            installer=fixture,
            installed_public_version=CANDIDATE_PUBLIC_VERSION,
            state_dir=Path(temp),
        )
    checks = {
        "v264_request_digest_exact": request["request_sha256"] == V264_REQUEST_SHA256,
        "candidate_target_exact": dict(request["requested_target"])["path"] == TARGET_PATH,
        "candidate_hash_exact": (
            dict(request["requested_target"])["sha256"] == CANDIDATE_INSTALLER_SHA256
        ),
        "candidate_length_exact": (
            dict(request["requested_target"])["length"] == CANDIDATE_INSTALLER_BYTES
        ),
        "rc8_to_stable_contract": (
            rc8_status == "update-available"
            and rc8_candidate is not None
            and rc8_candidate.target.path == TARGET_PATH
        ),
        "stable_post_upgrade_contract": (
            stable_status == "up-to-date"
            and stable_candidate is not None
            and stable_candidate.target.path == TARGET_PATH
        ),
        "synthetic_fixture_not_production_proof": True,
        "live_effects_forbidden": True,
    }
    failed = [name for name, passed in checks.items() if not passed]
    report: dict[str, object] = {
        "schema_version": 1,
        "subdivision": "V2.6.5",
        "mode": "contract",
        "development_source_sha": development_sha.lower(),
        "release_candidate_source_sha": CANDIDATE_SOURCE_SHA,
        "v264_request_sha256": request["request_sha256"],
        "checks": checks,
        "summary": {"passed": len(checks) - len(failed), "total": len(checks), "failed": failed},
        "status": "PASS" if not failed else "FAIL",
        "fixture_only": True,
        "production_proof": False,
        "public_release_triggered": False,
        "production_tuf_mutation_triggered": False,
        "live_updater_activation_triggered": False,
    }
    report["evidence_sha256"] = _canonical_digest(report)
    return report


def build_windows_preflight(
    development_sha: str,
    *,
    repository_root: Path,
    rc8_installer: Path,
    candidate_installer: Path,
    v263_evidence: Path,
    stage_dir: Path,
    authenticode: AuthenticodeVerifier,
    identity: InstallerIdentityVerifier,
) -> dict[str, object]:
    rc8 = validate_frozen_installer(
        rc8_installer,
        expected_size=RC8_INSTALLER_BYTES,
        expected_sha256=RC8_INSTALLER_SHA256,
        label="rc8",
    )
    candidate_file = validate_frozen_installer(
        candidate_installer,
        expected_size=CANDIDATE_INSTALLER_BYTES,
        expected_sha256=CANDIDATE_INSTALLER_SHA256,
        label="candidate",
    )
    validate_v263_evidence(v263_evidence)
    request = reconstruct_v264_request(repository_root)

    candidate_bytes = candidate_installer.read_bytes()
    with tempfile.TemporaryDirectory(prefix="kodepoia-v265-discovery-") as temp:
        status, candidate = synthetic_transition_status(
            installer=candidate_bytes,
            installed_public_version=RC8_PUBLIC_VERSION,
            state_dir=Path(temp),
        )
    if status != "update-available" or candidate is None:
        raise ValueError(f"rc8 -> stable staged discovery failed: {status}")
    if candidate.target.path != TARGET_PATH:
        raise ValueError("staged discovery selected the wrong target")
    if candidate.sha256 != CANDIDATE_INSTALLER_SHA256:
        raise ValueError("staged discovery candidate hash drift")
    if candidate.size_bytes != CANDIDATE_INSTALLER_BYTES:
        raise ValueError("staged discovery candidate length drift")

    stage_dir.mkdir(parents=True, exist_ok=True)
    downloader = PolicyVerifiedUpdateDownloader(
        stage_dir,
        authenticode=authenticode,
        identity=identity,
    )
    staged = downloader.stage(
        _policy_candidate(candidate),
        MemoryStreamingTargetTransport({candidate.target.path: candidate_bytes}),
    )
    if staged.sha256 != CANDIDATE_INSTALLER_SHA256:
        raise ValueError("staged verified candidate hash drift")
    if staged.size_bytes != CANDIDATE_INSTALLER_BYTES:
        raise ValueError("staged verified candidate length drift")
    if staged.public_version != CANDIDATE_PUBLIC_VERSION:
        raise ValueError("staged verified candidate version drift")
    if staged.source_sha != CANDIDATE_SOURCE_SHA:
        raise ValueError("staged verified candidate source drift")

    return {
        "schema_version": 1,
        "subdivision": "V2.6.5",
        "development_source_sha": development_sha.lower(),
        "fixture_only_tuf": True,
        "production_proof": False,
        "rc8_installer": rc8,
        "candidate_installer": candidate_file,
        "v263_evidence_sha256": CANDIDATE_V263_EVIDENCE_SHA256,
        "v264_request_sha256": request["request_sha256"],
        "discovery_status": status,
        "discovered_target": candidate.target.to_dict(),
        "staged_artifact": staged.to_dict(),
        "authenticode_policy": AUTHENTICODE_POLICY_ALLOW_UNSIGNED,
        "status": "PASS",
        "public_release_triggered": False,
        "public_tag_triggered": False,
        "public_asset_upload_triggered": False,
        "production_tuf_mutation_triggered": False,
        "live_updater_activation_triggered": False,
        "signing_secret_provisioned": False,
        "winget_submission_triggered": False,
    }


def build_final_report(
    development_sha: str,
    *,
    repository_root: Path,
    preflight_path: Path,
    windows_evidence_path: Path,
    candidate_installer: Path,
) -> dict[str, object]:
    preflight = json.loads(preflight_path.read_text(encoding="utf-8-sig"))
    windows = json.loads(windows_evidence_path.read_text(encoding="utf-8-sig"))
    candidate = validate_frozen_installer(
        candidate_installer,
        expected_size=CANDIDATE_INSTALLER_BYTES,
        expected_sha256=CANDIDATE_INSTALLER_SHA256,
        label="staged candidate",
    )
    request = reconstruct_v264_request(repository_root)

    with tempfile.TemporaryDirectory(prefix="kodepoia-v265-post-upgrade-") as temp:
        post_status, post_candidate = synthetic_transition_status(
            installer=candidate_installer.read_bytes(),
            installed_public_version=CANDIDATE_PUBLIC_VERSION,
            state_dir=Path(temp),
        )
    with tempfile.TemporaryDirectory(prefix="kodepoia-v265-incident-") as temp:
        incident = run_synthetic_incident_drills(
            source_sha=development_sha.lower(),
            work_dir=Path(temp),
        ).to_dict()
    scenarios = {
        str(item["scenario_id"]): item
        for item in incident.get("scenarios", [])
        if isinstance(item, dict) and "scenario_id" in item
    }
    recovery = scenarios.get("RECOVERY-LAST-KNOWN-GOOD-01", {})

    checks = {
        "exact_rc8_public_baseline": (
            dict(preflight.get("rc8_installer") or {}).get("size_bytes") == RC8_INSTALLER_BYTES
            and dict(preflight.get("rc8_installer") or {}).get("sha256")
            == RC8_INSTALLER_SHA256
        ),
        "exact_frozen_candidate": (
            candidate["size_bytes"] == CANDIDATE_INSTALLER_BYTES
            and candidate["sha256"] == CANDIDATE_INSTALLER_SHA256
            and preflight.get("v263_evidence_sha256") == CANDIDATE_V263_EVIDENCE_SHA256
        ),
        "accepted_v264_transition_request": (
            request["request_sha256"] == V264_REQUEST_SHA256
            and preflight.get("v264_request_sha256") == V264_REQUEST_SHA256
        ),
        "isolated_verified_staging": (
            preflight.get("fixture_only_tuf") is True
            and preflight.get("production_proof") is False
            and preflight.get("discovery_status") == "update-available"
            and dict(preflight.get("staged_artifact") or {}).get("sha256")
            == CANDIDATE_INSTALLER_SHA256
        ),
        "rc8_clean_install": (
            windows.get("rc8_install_exit_code") == 0
            and windows.get("rc8_installed_version") == RC8_PUBLIC_VERSION
            and windows.get("rc8_packaged_smoke") is True
        ),
        "verified_upgrade_handoff": (
            windows.get("candidate_update_exit_code") == 0
            and windows.get("candidate_relaunch_observed") is True
            and windows.get("upgraded_version") == CANDIDATE_PUBLIC_VERSION
            and windows.get("candidate_packaged_smoke") is True
        ),
        "candidate_clean_install": (
            windows.get("candidate_clean_install_exit_code") == 0
            and windows.get("candidate_clean_installed_version") == CANDIDATE_PUBLIC_VERSION
            and windows.get("candidate_clean_install_smoke") is True
            and windows.get("candidate_clean_uninstall_exit_code") == 0
            and windows.get("candidate_clean_executable_removed") is True
        ),
        "post_upgrade_update_check": (
            post_status == "up-to-date"
            and post_candidate is not None
            and post_candidate.target.path == TARGET_PATH
        ),
        "custom_install_directory_preserved": (
            windows.get("custom_install_directory_preserved") is True
            and windows.get("default_install_directory_unused") is True
        ),
        "project_settings_user_data_preserved": (
            windows.get("project_sentinel_preserved_after_upgrade") is True
            and windows.get("user_data_sentinel_preserved_after_upgrade") is True
            and windows.get("settings_sentinel_preserved_after_upgrade") is True
            and windows.get("project_sentinel_preserved_after_uninstall") is True
            and windows.get("user_data_sentinel_preserved_after_uninstall") is True
            and windows.get("settings_sentinel_preserved_after_uninstall") is True
        ),
        "uninstall_behavior": (
            windows.get("uninstall_exit_code") == 0
            and windows.get("installed_executable_removed") is True
        ),
        "incident_recovery_rehearsal": (
            incident.get("status") == "PASS"
            and incident.get("critical_bypass_count") == 0
            and recovery.get("passed") is True
            and recovery.get("actual_verdict") == "RECOVER"
        ),
        "no_live_or_public_effect": (
            preflight.get("public_release_triggered") is False
            and preflight.get("public_tag_triggered") is False
            and preflight.get("public_asset_upload_triggered") is False
            and preflight.get("production_tuf_mutation_triggered") is False
            and preflight.get("live_updater_activation_triggered") is False
            and preflight.get("signing_secret_provisioned") is False
            and preflight.get("winget_submission_triggered") is False
            and windows.get("public_release_effect") is False
            and windows.get("production_tuf_mutation") is False
        ),
    }
    failed = [name for name, passed in checks.items() if not passed]
    publication_inputs = {
        "public_version": CANDIDATE_PUBLIC_VERSION,
        "tag": PUBLIC_TAG,
        "source_sha": CANDIDATE_SOURCE_SHA,
        "installer": "KodepoiaSetup.exe",
        "installer_size": CANDIDATE_INSTALLER_BYTES,
        "installer_sha256": CANDIDATE_INSTALLER_SHA256,
        "target_path": TARGET_PATH,
        "authenticode_policy": AUTHENTICODE_POLICY_ALLOW_UNSIGNED,
        "production_signed": False,
        "winget_decision": "out",
        "v263_evidence_sha256": CANDIDATE_V263_EVIDENCE_SHA256,
        "v264_request_sha256": V264_REQUEST_SHA256,
    }
    report: dict[str, object] = {
        "schema_version": 1,
        "subdivision": "V2.6.5",
        "title": "Installed Windows release rehearsal and pre-publication go/no-go",
        "development_source_sha": development_sha.lower(),
        "release_candidate_source_sha": CANDIDATE_SOURCE_SHA,
        "checks": checks,
        "summary": {"passed": len(checks) - len(failed), "total": len(checks), "failed": failed},
        "critical_veto": bool(failed),
        "go_no_go": "GO" if not failed else "NO-GO",
        "status": "PASS" if not failed else "FAIL",
        "post_upgrade_staged_status": post_status,
        "incident_recovery": {
            "status": incident.get("status"),
            "critical_bypass_count": incident.get("critical_bypass_count"),
            "recovery_last_known_good": recovery,
        },
        "publication_inputs": publication_inputs,
        "publication_inputs_sha256": _canonical_digest(publication_inputs),
        "public_release_triggered": False,
        "public_tag_triggered": False,
        "public_asset_upload_triggered": False,
        "production_tuf_mutation_triggered": False,
        "live_updater_activation_triggered": False,
        "signing_secret_provisioned": False,
        "winget_submission_triggered": False,
        "manual_intervention_required": False,
    }
    report["evidence_sha256"] = _canonical_digest(report)
    return report


__all__ = [
    "CANDIDATE_INSTALLER_BYTES",
    "CANDIDATE_INSTALLER_SHA256",
    "CANDIDATE_PUBLIC_VERSION",
    "CANDIDATE_SOURCE_SHA",
    "CANDIDATE_V263_EVIDENCE_SHA256",
    "PUBLIC_TAG",
    "RC8_INSTALLER_BYTES",
    "RC8_INSTALLER_SHA256",
    "RC8_PUBLIC_VERSION",
    "RC8_SOURCE_SHA",
    "TARGET_PATH",
    "V263_ARTIFACT_ID",
    "V263_ARTIFACT_NAME",
    "V263_ARTIFACT_RUN_ID",
    "V264_ACCEPTED_HEAD",
    "V264_REQUEST_SHA256",
    "build_contract_report",
    "build_final_report",
    "build_windows_preflight",
    "candidate_target",
    "reconstruct_v264_request",
    "synthetic_transition_status",
    "validate_frozen_installer",
    "validate_v263_evidence",
]
