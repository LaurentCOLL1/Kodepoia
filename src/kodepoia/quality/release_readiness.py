from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from kodepoia.core.backup import BackupManager
from kodepoia.quality.build import BuildManifest, BuildStatus, KodeBuild
from kodepoia.quality.license_bom import (
    KodeBOM,
    LicenseAssertion,
    LicenseAssertionState,
    LicensePolicy,
    LicensePolicyAction,
    LicenseReport,
)
from kodepoia.quality.supply_chain import (
    AttestationState,
    SupplyChainManifest,
    SupplyChainStatus,
)

RELEASE_VERSION = "1.0.0rc1"
PRIOR_VERSION = "0.1.0a4"
RELEASE_ID = "kodepoia-v1.0.0rc1"
PRIOR_FIXTURE = Path("tests/fixtures/r16_17_release_readiness/prior_release_state.json")
RELEASE_NOTES = Path("docs/release/V1_0_RC1_RELEASE_NOTES.md")
SECURITY_OPERATIONS = Path("docs/release/V1_0_RC1_SECURITY_OPERATIONS.md")
_SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
_VERSION_RE = re.compile(r'^__version__\s*=\s*"([^"]+)"\s*$', re.MULTILINE)
PROJECT_LICENSE_TEXT = "All rights reserved - private development"


class ReleaseReadinessError(ValueError):
    pass


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _case(name: str, passed: bool, detail: str, *, critical: bool = True) -> dict[str, Any]:
    return {
        "name": name,
        "pass": bool(passed),
        "critical": bool(critical),
        "detail": detail,
    }


def read_declared_versions(repo_root: str | Path) -> dict[str, str]:
    root = Path(repo_root).resolve(strict=True)
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    project_version = str((pyproject.get("project") or {}).get("version", "")).strip()
    init_text = (root / "src/kodepoia/__init__.py").read_text(encoding="utf-8")
    match = _VERSION_RE.search(init_text)
    runtime_version = match.group(1).strip() if match else ""
    return {"pyproject": project_version, "runtime": runtime_version}


def validate_release_identity(repo_root: str | Path) -> dict[str, str]:
    versions = read_declared_versions(repo_root)
    if versions != {"pyproject": RELEASE_VERSION, "runtime": RELEASE_VERSION}:
        raise ReleaseReadinessError(f"release identity mismatch: expected {RELEASE_VERSION}, got {versions}")
    return versions


def _wheel_metadata_version(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            metadata_names = sorted(
                name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
            )
            if len(metadata_names) != 1:
                raise ReleaseReadinessError("wheel must contain exactly one dist-info/METADATA")
            text = archive.read(metadata_names[0]).decode("utf-8")
    except (OSError, UnicodeDecodeError, zipfile.BadZipFile, KeyError) as exc:
        raise ReleaseReadinessError(f"cannot inspect wheel metadata: {exc}") from exc
    versions = [
        line.split(":", 1)[1].strip() for line in text.splitlines() if line.lower().startswith("version:")
    ]
    if len(versions) != 1:
        raise ReleaseReadinessError("wheel metadata must contain exactly one Version field")
    return versions[0]


def _artifact_hashes(dist: Path) -> dict[str, str]:
    if not dist.is_dir():
        raise ReleaseReadinessError(f"distribution directory missing: {dist}")
    values = {
        path.name: _file_digest(path)
        for path in sorted(dist.iterdir())
        if path.is_file() and (path.suffix == ".whl" or path.name.endswith(".tar.gz"))
    }
    if len(values) != 2:
        raise ReleaseReadinessError("release build requires exactly one wheel and one sdist")
    return values


def load_baseline_build(path: str | Path) -> dict[str, str]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != {"artifacts"}:
        raise ReleaseReadinessError("baseline build hash document is invalid")
    raw = payload["artifacts"]
    if not isinstance(raw, dict) or len(raw) != 2:
        raise ReleaseReadinessError("baseline build must contain exactly two artifacts")
    values = {str(name): str(digest).lower() for name, digest in raw.items()}
    if any(re.fullmatch(r"[0-9a-f]{64}", digest) is None for digest in values.values()):
        raise ReleaseReadinessError("baseline artifact digest is invalid")
    return dict(sorted(values.items()))


def build_release_manifest(
    repo_root: str | Path,
    *,
    source_sha: str,
    platform: str,
    baseline_build_path: str | Path,
) -> tuple[BuildManifest, dict[str, Any]]:
    root = Path(repo_root).resolve(strict=True)
    source = source_sha.strip().lower()
    if _SHA40_RE.fullmatch(source) is None:
        raise ReleaseReadinessError("source_sha must be a 40-character Git SHA")
    validate_release_identity(root)
    manifest = KodeBuild.collect(
        root,
        source_sha=source,
        platform=platform,
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        metadata={
            "release_id": RELEASE_ID,
            "release_version": RELEASE_VERSION,
            "signing_state": "UNSIGNED",
            "publication_state": "NOT_REQUESTED",
            "attestation_state": "NOT_EXERCISED",
            "source_date_epoch": os.environ.get("SOURCE_DATE_EPOCH", ""),
        },
    )
    if manifest.status is not BuildStatus.PASS:
        raise ReleaseReadinessError(f"build manifest is not PASS: {manifest.blockers}")
    wheels = [item for item in manifest.artifacts if item.name.endswith(".whl")]
    sdists = [item for item in manifest.artifacts if item.name.endswith(".tar.gz")]
    if len(wheels) != 1 or len(sdists) != 1:
        raise ReleaseReadinessError("release manifest requires one wheel and one sdist")
    wheel_path = root / "dist" / wheels[0].name
    wheel_version = _wheel_metadata_version(wheel_path)
    if wheel_version != RELEASE_VERSION or RELEASE_VERSION.replace("-", "_") not in wheel_path.name:
        raise ReleaseReadinessError(
            f"wheel identity mismatch: metadata={wheel_version}, file={wheel_path.name}"
        )
    current_hashes = _artifact_hashes(root / "dist")
    baseline_hashes = load_baseline_build(baseline_build_path)
    reproducible = current_hashes == baseline_hashes
    reproducibility = {
        "baseline_artifacts": baseline_hashes,
        "current_artifacts": current_hashes,
        "same_os_rebuild_identical": reproducible,
    }
    if not reproducible:
        raise ReleaseReadinessError("same-source package rebuild is not byte-identical")
    return manifest, reproducibility


def _project_license_assertion() -> LicenseAssertion:
    return LicenseAssertion(
        state=LicenseAssertionState.SPDX_EXPRESSION,
        evidence_source="pyproject.toml project.license.text",
        expression="LicenseRef-Kodepoia-Proprietary",
        rationale="Repository metadata declares private all-rights-reserved development.",
        custom_text_sha256=hashlib.sha256(PROJECT_LICENSE_TEXT.encode("utf-8")).hexdigest(),
    )


def build_release_bom(repo_root: str | Path) -> tuple[Any, LicenseReport, dict[str, Any]]:
    root = Path(repo_root).resolve(strict=True)
    bom = KodeBOM.from_pyproject(root, project_license=_project_license_assertion())
    policy = LicensePolicy(
        name="r16.17-release-license-review",
        rules=(),
        default_action=LicensePolicyAction.UNKNOWN,
    )
    license_report = LicenseReport.build(bom, policy)
    view = KodeBOM.spdx_compatibility_view(bom)
    unresolved = sorted(item.id for item in bom.components if item.resolution.value == "unresolved")
    return (
        bom,
        license_report,
        {
            "spdx_compatibility": view,
            "unresolved_component_ids": unresolved,
            "known_unknowns_preserved": bool(unresolved),
        },
    )


def run_install_consume_probe(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve(strict=True)
    wheels = sorted(path for path in (root / "dist").glob("*.whl") if path.is_file())
    if len(wheels) != 1:
        raise ReleaseReadinessError("install probe requires exactly one wheel")
    with tempfile.TemporaryDirectory(prefix="kodepoia-r16-17-install-") as raw:
        temp = Path(raw)
        target = temp / "site"
        command = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-deps",
            "--no-index",
            "--target",
            str(target),
            str(wheels[0]),
        ]
        installed = subprocess.run(
            command,
            cwd=temp,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if installed.returncode != 0:
            raise ReleaseReadinessError(
                "offline wheel install failed: " + (installed.stderr or installed.stdout)[-2000:]
            )
        probe = f"import sys;sys.path.insert(0, {str(target)!r});import kodepoia;print(kodepoia.__version__)"
        consumed = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=temp,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        version = consumed.stdout.strip()
        if consumed.returncode != 0 or version != RELEASE_VERSION:
            raise ReleaseReadinessError(
                f"installed wheel consumption failed: rc={consumed.returncode}, version={version!r}"
            )
        return {
            "wheel": wheels[0].name,
            "offline": True,
            "no_dependencies_installed": True,
            "imported_version": version,
        }


def _load_prior_fixture(repo_root: Path) -> dict[str, Any]:
    payload = json.loads((repo_root / PRIOR_FIXTURE).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version",
        "application_version",
        "configuration",
        "release_history",
    }:
        raise ReleaseReadinessError("prior release fixture schema is invalid")
    if payload["schema_version"] != 1 or payload["application_version"] != PRIOR_VERSION:
        raise ReleaseReadinessError("prior release fixture identity drifted")
    configuration = payload["configuration"]
    if not isinstance(configuration, dict) or configuration != {
        "network_default": "off",
        "plugin_trust": "deny_unknown",
        "production_publication": "disabled",
    }:
        raise ReleaseReadinessError("prior release secure defaults drifted")
    if payload["release_history"] != [PRIOR_VERSION]:
        raise ReleaseReadinessError("prior release history drifted")
    return payload


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _migrated_payload(prior: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "application_version": RELEASE_VERSION,
        "configuration": dict(prior["configuration"]),
        "release_history": [PRIOR_VERSION, RELEASE_VERSION],
        "migration_history": [f"{PRIOR_VERSION}-to-{RELEASE_VERSION}"],
    }


def migrate_prior_release_state(
    project_root: Path,
    backup_root: Path,
    *,
    inject_failure: bool = False,
) -> dict[str, Any]:
    state_path = project_root / "release-state.json"
    prior = json.loads(state_path.read_text(encoding="utf-8"))
    if prior.get("application_version") != PRIOR_VERSION or prior.get("schema_version") != 1:
        raise ReleaseReadinessError("migration source state is not the declared prior release")
    original_sha = _file_digest(state_path)
    manager = BackupManager(backup_root)
    archive = manager.create_archive(project_root, label="r16-17-pre-migration")
    if not manager.verify(archive):
        raise ReleaseReadinessError("pre-migration backup verification failed")
    try:
        migrated = _migrated_payload(prior)
        _write_json_atomic(state_path, migrated)
        if inject_failure:
            raise RuntimeError("synthetic post-write migration failure")
        round_trip = json.loads(state_path.read_text(encoding="utf-8"))
        if round_trip != migrated:
            raise ReleaseReadinessError("migrated state round-trip mismatch")
        return {
            "status": "migrated",
            "from_version": PRIOR_VERSION,
            "to_version": RELEASE_VERSION,
            "state_schema": 2,
            "backup_verified": True,
            "backup_archive_sha256": _file_digest(archive),
            "state_sha256": _file_digest(state_path),
        }
    except Exception as exc:
        manager.restore(archive, project_root, overwrite=True)
        restored = project_root / "release-state.json"
        if _file_digest(restored) != original_sha:
            raise ReleaseReadinessError("migration rollback failed to restore exact prior bytes") from exc
        if inject_failure:
            return {
                "status": "rolled_back",
                "from_version": PRIOR_VERSION,
                "to_version": RELEASE_VERSION,
                "backup_verified": True,
                "restored_sha256": original_sha,
            }
        raise


def run_migration_and_rollback_probe(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve(strict=True)
    prior = _load_prior_fixture(root)
    with tempfile.TemporaryDirectory(prefix="kodepoia-r16-17-migrate-") as raw:
        temp = Path(raw)
        success_root = temp / "success"
        success_root.mkdir()
        _write_json_atomic(success_root / "release-state.json", prior)
        success = migrate_prior_release_state(success_root, temp / "backups-success")
        failure_root = temp / "failure"
        failure_root.mkdir()
        _write_json_atomic(failure_root / "release-state.json", prior)
        original_sha = _file_digest(failure_root / "release-state.json")
        rollback = migrate_prior_release_state(
            failure_root,
            temp / "backups-failure",
            inject_failure=True,
        )
        restored_sha = _file_digest(failure_root / "release-state.json")
        if rollback["status"] != "rolled_back" or restored_sha != original_sha:
            raise ReleaseReadinessError("failed migration did not restore exact prior state")
        return {"success": success, "failure_recovery": rollback, "rollback_exact": True}


def release_documentation_evidence(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve(strict=True)
    evidence: dict[str, Any] = {}
    for label, relative in (
        ("release_notes", RELEASE_NOTES),
        ("security_operations", SECURITY_OPERATIONS),
    ):
        path = root / relative
        text = path.read_text(encoding="utf-8")
        if len(text.strip()) < 400:
            raise ReleaseReadinessError(f"{relative} is too small to be authoritative RC documentation")
        evidence[label] = {
            "path": relative.as_posix(),
            "sha256": _file_digest(path),
            "bytes": path.stat().st_size,
        }
    return evidence


def build_release_readiness_report(
    repo_root: str | Path,
    *,
    source_sha: str,
    platform: str,
    baseline_build_path: str | Path,
) -> dict[str, Any]:
    root = Path(repo_root).resolve(strict=True)
    identity = validate_release_identity(root)
    build_manifest, reproducibility = build_release_manifest(
        root,
        source_sha=source_sha,
        platform=platform,
        baseline_build_path=baseline_build_path,
    )
    bom, license_report, bom_details = build_release_bom(root)
    supply = SupplyChainManifest.from_release_evidence(
        root,
        source_sha=source_sha,
        build_manifest=build_manifest,
        bom_report=bom,
        external_attestation=AttestationState.NOT_EXERCISED,
    )
    supply.assert_promotable(expected_source_sha=source_sha)
    install = run_install_consume_probe(root)
    migration = run_migration_and_rollback_probe(root)
    docs = release_documentation_evidence(root)
    cases = [
        _case("release_identity_consistent", identity["pyproject"] == RELEASE_VERSION, RELEASE_VERSION),
        _case(
            "source_bound_build_manifest",
            build_manifest.status is BuildStatus.PASS and build_manifest.source_sha == source_sha.lower(),
            build_manifest.evidence_sha256,
        ),
        _case(
            "reproducible_same_os_packages",
            reproducibility["same_os_rebuild_identical"],
            _digest(reproducibility["current_artifacts"]),
        ),
        _case("unsigned_core_rc_is_explicit", True, "UNSIGNED / publication NOT_REQUESTED"),
        _case(
            "offline_wheel_install_consume",
            install["imported_version"] == RELEASE_VERSION,
            install["wheel"],
        ),
        _case("declared_prior_migration", migration["success"]["status"] == "migrated", PRIOR_VERSION),
        _case(
            "failed_migration_exact_rollback",
            migration["rollback_exact"],
            migration["failure_recovery"]["restored_sha256"],
        ),
        _case("bom_evidence_bound", bom.status.value != "fail", bom.evidence_sha256),
        _case(
            "license_unknowns_not_laundered",
            license_report.status.value in {"warn", "unknown"} and bom_details["known_unknowns_preserved"],
            license_report.evidence_sha256,
        ),
        _case(
            "spdx_view_is_nonconformant_claim",
            bom_details["spdx_compatibility"]["conformance_claim"] is False,
            "SPDX compatibility view only",
        ),
        _case(
            "supply_chain_promotable",
            supply.status is SupplyChainStatus.PASS,
            supply.evidence_sha256,
        ),
        _case("release_security_operations_docs", len(docs) == 2, _digest(docs)),
        _case(
            "production_publication_not_triggered",
            True,
            "conditional optional actions remain NOT_TRIGGERED",
        ),
    ]
    failed_critical = [item["name"] for item in cases if item["critical"] and not item["pass"]]
    semantic_payload = {
        "release_id": RELEASE_ID,
        "release_version": RELEASE_VERSION,
        "prior_version": PRIOR_VERSION,
        "source_sha": source_sha.lower(),
        "build_artifact_sha256": reproducibility["current_artifacts"],
        "build_manifest_evidence_sha256": build_manifest.evidence_sha256,
        "bom_evidence_sha256": bom.evidence_sha256,
        "license_evidence_sha256": license_report.evidence_sha256,
        "supply_chain_evidence_sha256": supply.evidence_sha256,
        "documentation": docs,
        "migration": migration,
        "optional_actions": {
            "production_signing": "NOT_TRIGGERED",
            "store_submission": "NOT_TRIGGERED",
            "public_registry_publication": "NOT_TRIGGERED",
            "production_credentials": "NOT_USED",
            "provider_domain_cutover": "NOT_TRIGGERED",
            "external_artifact_attestation": "NOT_EXERCISED",
        },
    }
    report = {
        "schema_version": 1,
        "phase": "R16.17",
        "source_sha": source_sha.lower(),
        "platform": platform,
        "release_id": RELEASE_ID,
        "release_version": RELEASE_VERSION,
        "prior_version": PRIOR_VERSION,
        "release_claim": not failed_critical,
        "critical_veto": bool(failed_critical),
        "core_manual_required": False,
        "manual_state": "CONDITIONAL_NOT_TRIGGERED",
        "public_release_performed": False,
        "network_publication_calls": 0,
        "production_credentials_used": False,
        "build_manifest": build_manifest.to_dict(),
        "reproducibility": reproducibility,
        "install_probe": install,
        "bom": bom.to_dict(),
        "license_report": license_report.to_dict(),
        "spdx_compatibility": bom_details["spdx_compatibility"],
        "supply_chain_manifest": supply.to_dict(),
        "migration": migration,
        "documentation": docs,
        "optional_actions": semantic_payload["optional_actions"],
        "cases": cases,
        "summary": {
            "total": len(cases),
            "passed": sum(bool(item["pass"]) for item in cases),
            "failed": sum(not bool(item["pass"]) for item in cases),
            "critical_failed": len(failed_critical),
        },
        "semantic_sha256": _digest(semantic_payload),
    }
    report["evidence_sha256"] = _digest(report)
    if not report["release_claim"]:
        raise ReleaseReadinessError(f"R16.17 critical acceptance failed: {failed_critical}")
    return report
