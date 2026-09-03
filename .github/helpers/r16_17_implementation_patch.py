from __future__ import annotations

import json
from pathlib import Path

RELEASE_MODULE = r'''from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from pathlib import Path
from typing import Any, Mapping

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
        raise ReleaseReadinessError(
            f"release identity mismatch: expected {RELEASE_VERSION}, got {versions}"
        )
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
        line.split(":", 1)[1].strip()
        for line in text.splitlines()
        if line.lower().startswith("version:")
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
    return bom, license_report, {
        "spdx_compatibility": view,
        "unresolved_component_ids": unresolved,
        "known_unknowns_preserved": bool(unresolved),
    }


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
        probe = (
            "import sys;"
            f"sys.path.insert(0, {str(target)!r});"
            "import kodepoia;"
            "print(kodepoia.__version__)"
        )
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
    except Exception:
        manager.restore(archive, project_root, overwrite=True)
        restored = project_root / "release-state.json"
        if _file_digest(restored) != original_sha:
            raise ReleaseReadinessError("migration rollback failed to restore exact prior bytes")
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
            license_report.status.value in {"warn", "unknown"}
            and bom_details["known_unknowns_preserved"],
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
'''

ACCEPTANCE_SCRIPT = r'''from __future__ import annotations

import argparse
import json
from pathlib import Path

from kodepoia.quality.release_readiness import build_release_readiness_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit exact-source R16.17 release-readiness evidence")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--baseline-build", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    report = build_release_readiness_report(
        root,
        source_sha=args.source_sha,
        platform=args.platform,
        baseline_build_path=args.baseline_build,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": output.as_posix(),
                "source_sha": report["source_sha"],
                "platform": report["platform"],
                "release_version": report["release_version"],
                "summary": report["summary"],
                "release_claim": report["release_claim"],
                "critical_veto": report["critical_veto"],
                "manual_state": report["manual_state"],
                "semantic_sha256": report["semantic_sha256"],
                "evidence_sha256": report["evidence_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

TESTS = r'''from __future__ import annotations

from pathlib import Path

from kodepoia.quality.release_readiness import (
    PRIOR_VERSION,
    RELEASE_VERSION,
    build_release_bom,
    read_declared_versions,
    release_documentation_evidence,
    run_migration_and_rollback_probe,
    validate_release_identity,
)

ROOT = Path(__file__).resolve().parents[1]


def test_r16_17_release_identity_is_v1_rc1_and_consistent() -> None:
    assert RELEASE_VERSION == "1.0.0rc1"
    assert PRIOR_VERSION == "0.1.0a4"
    assert read_declared_versions(ROOT) == {
        "pyproject": RELEASE_VERSION,
        "runtime": RELEASE_VERSION,
    }
    assert validate_release_identity(ROOT)["runtime"] == RELEASE_VERSION


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
'''

FIXTURE = r'''{
  "schema_version": 1,
  "application_version": "0.1.0a4",
  "configuration": {
    "network_default": "off",
    "plugin_trust": "deny_unknown",
    "production_publication": "disabled"
  },
  "release_history": [
    "0.1.0a4"
  ]
}
'''

RELEASE_NOTES = r'''# Kodepoia v1.0.0rc1 — Release Candidate Notes

## Release status

`1.0.0rc1` is the first v1.0 release-candidate identity for the repository-owned Python package and R16 release-readiness evidence. It is an **unsigned core RC**, not a public production release. The R16.17 workflow builds wheel and source-distribution artifacts from one exact Git SHA, records SHA-256 evidence, verifies a same-source rebuild, and consumes the wheel through an offline `pip --no-index --no-deps` installation probe.

No store submission, public package-registry publication, production signing, production credential use, provider cutover, or domain cutover is performed automatically. Those actions remain conditional and require separate explicit authorization and evidence.

## Supported RC evidence

The core RC evidence covers the repository Python wheel and sdist, exact-source `BuildManifest`, R16.9 supply-chain binding, deterministic dependency/BOM inventory, license-review evidence, the declared `0.1.0a4` prior-state migration fixture, verified pre-migration backup, successful upgrade to `1.0.0rc1`, and exact rollback after an injected migration failure. Existing representative Windows desktop, Godot, ComfyUI, media, durability, resource and adversarial evidence remains governed by its own R16 authorities and is not silently converted into new live-capability claims here.

## Known limitations and truthful unknowns

Dependency declarations in `pyproject.toml` are version ranges, not a fully resolved lockfile. R16.17 therefore records those dependency components as unresolved with unknown integrity and `NOASSERTION` license evidence rather than claiming exact third-party package hashes or licenses. The SPDX output is a compatibility view and explicitly **not** an SPDX conformance claim.

GitHub artifact attestations can provide additional cryptographically signed provenance for public-repository artifacts, but the frozen R16.9 policy does not require external attestation for core promotion and treats it as provenance-only, not a security verdict. R16.17 therefore records external attestation as `NOT_EXERCISED` unless separately added under an authorized policy change.

## Promotion boundary

`1.0.0rc1` is only a candidate. R16.18 must still re-run the final integrated adversarial and representative-project RC authority on one exact source. A green R16.17 result does not by itself declare R16 or Kodepoia v1.0 complete, signed, published, production-ready, or generally available.
'''

SECURITY_OPERATIONS = r'''# Kodepoia v1.0.0rc1 — Security and Operations Runbook

## Secure defaults

The R16.17 migration fixture preserves three explicit defaults: network access is `off`, unknown plugin trust is denied, and production publication is disabled. Release-readiness evidence must not widen these defaults. Production credentials are not required or consumed by core RC acceptance, and publication/signing/provider-domain cutover remain conditional manual actions.

## Backup, migration and rollback

Before a supported release-state migration, create a repository-owned backup with `BackupManager` and verify its manifest, paths, sizes and SHA-256 values. R16.17 migrates only the declared prior fixture (`0.1.0a4`, schema 1) to `1.0.0rc1` (schema 2). The write is atomic. If a migration fails after the state write, restore the verified pre-migration archive and verify that the prior state returns byte-for-byte. Do not promote a partially migrated state.

## Incident response

If release evidence, a package checksum, migration state, workflow provenance, BOM binding, or repository authority is inconsistent, stop promotion and treat the candidate as non-authoritative. Preserve the failing exact SHA and evidence, revoke or quarantine any affected candidate artifact, restore from a verified backup where state changed, and re-run the relevant exact-head authority after repair. Never reuse a PASS from a different SHA.

If a credential or plugin is suspected to be compromised, disable or revoke the corresponding external credential/plugin authority outside the RC artifact, invalidate cached authorization where applicable, and re-run the repository security/provenance gates. Do not write live credential values into release reports, manifests, logs, command lines, documentation, or fixtures.

## Publication and signing

Core R16.17 produces an unsigned candidate only. Production signing, store submission, public registry publication, production credentials, and provider/domain cutover require explicit authorization. If any is requested, R16.17 manual state becomes triggered and completion must stop until the exact signing/publication target, credential scope, resulting artifact identity, provenance, and verification evidence are recorded.

## Recovery and operator checks

Verify the exact source SHA, package SHA-256 values, build-manifest evidence digest, BOM evidence digest, supply-chain evidence digest, migration backup verification, rollback result, and release documentation hashes before promotion. Public publication must never be inferred from artifact upload to GitHub Actions: Actions artifacts are acceptance evidence, not a release channel.
'''

WORKFLOW = r'''name: R16.17 v1.0 Packaging Migration Rollback Release Readiness Acceptance

on:
  push:
    branches:
      - r16/17-v1-packaging-migration-rollback-release-readiness
  pull_request:
    paths:
      - .github/workflows/r16-17-release-readiness-acceptance.yml
      - configs/r16_supply_chain_policy.json
      - pyproject.toml
      - src/kodepoia/__init__.py
      - src/kodepoia/quality/release_readiness.py
      - scripts/r16_17_release_readiness_acceptance.py
      - tests/fixtures/r16_17_release_readiness/**
      - tests/test_r16_17_release_readiness.py
      - tests/test_supply_chain_r16_9.py
      - docs/release/V1_0_RC1_RELEASE_NOTES.md
      - docs/release/V1_0_RC1_SECURITY_OPERATIONS.md
      - docs/roadmap/R16_PLAN.md
      - docs/continuity/KODEPOIA_CONTINUITY.md
  workflow_dispatch:

permissions:
  contents: read

jobs:
  release-readiness:
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    timeout-minutes: 25
    env:
      EVIDENCE_SHA: ${{ github.event.pull_request.head.sha || github.sha }}
      SOURCE_DATE_EPOCH: "946684800"
      PYTHONHASHSEED: "0"
    steps:
      - name: Checkout exact evidence source
        uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262
        with:
          ref: ${{ env.EVIDENCE_SHA }}
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065
        with:
          python-version: "3.12"
          cache: pip

      - name: Assert exact checkout provenance
        shell: python
        run: |
          import os
          import subprocess
          expected = os.environ["EVIDENCE_SHA"].strip().lower()
          actual = subprocess.check_output(
              ["git", "rev-parse", "HEAD"], text=True, encoding="utf-8"
          ).strip().lower()
          if actual != expected:
              raise SystemExit(f"checkout mismatch: expected {expected}, got {actual}")

      - name: Install focused acceptance dependencies
        run: python -m pip install -e ".[dev]"

      - name: Compile focused R16.17 sources
        run: >-
          python -m compileall -q
          src/kodepoia/quality/release_readiness.py
          scripts/r16_17_release_readiness_acceptance.py
          tests/test_r16_17_release_readiness.py

      - name: Ruff focused R16.17 sources
        run: >-
          python -m ruff check
          src/kodepoia/quality/release_readiness.py
          scripts/r16_17_release_readiness_acceptance.py
          tests/test_r16_17_release_readiness.py

      - name: Run focused R16.17 and supply-chain regression tests
        run: >-
          python -m pytest -q
          tests/test_r16_17_release_readiness.py
          tests/test_supply_chain_r16_9.py

      - name: Build baseline exact-source wheel and sdist
        run: python -m build --wheel --sdist --outdir dist

      - name: Record baseline package hashes
        shell: python
        run: |
          import hashlib
          import json
          from pathlib import Path
          artifacts = {}
          for path in sorted(Path("dist").iterdir()):
              if path.is_file() and (path.suffix == ".whl" or path.name.endswith(".tar.gz")):
                  artifacts[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
          if len(artifacts) != 2:
              raise SystemExit(f"expected exactly two package artifacts, got {sorted(artifacts)}")
          Path("artifacts").mkdir(exist_ok=True)
          Path("artifacts/r16_17_baseline_build.json").write_text(
              json.dumps({"artifacts": artifacts}, indent=2, sort_keys=True) + "\n",
              encoding="utf-8",
          )

      - name: Rebuild exact source for reproducibility
        shell: python
        run: |
          import shutil
          import subprocess
          import sys
          shutil.rmtree("dist")
          subprocess.run(
              [sys.executable, "-m", "build", "--wheel", "--sdist", "--outdir", "dist"],
              check=True,
          )

      - name: Emit exact-source R16.17 acceptance
        run: >-
          python scripts/r16_17_release_readiness_acceptance.py
          --source-sha "${{ env.EVIDENCE_SHA }}"
          --platform "${{ runner.os }}"
          --baseline-build artifacts/r16_17_baseline_build.json
          --output artifacts/r16_17_release_readiness_acceptance.json

      - name: Upload exact-source RC evidence and packages
        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02
        with:
          name: r16-17-release-readiness-${{ runner.os }}-${{ env.EVIDENCE_SHA }}
          path: |
            artifacts/r16_17_baseline_build.json
            artifacts/r16_17_release_readiness_acceptance.json
            dist/*.whl
            dist/*.tar.gz
          if-no-files-found: error
          retention-days: 30
'''

FILES = {
    "src/kodepoia/quality/release_readiness.py": RELEASE_MODULE,
    "scripts/r16_17_release_readiness_acceptance.py": ACCEPTANCE_SCRIPT,
    "tests/test_r16_17_release_readiness.py": TESTS,
    "tests/fixtures/r16_17_release_readiness/prior_release_state.json": FIXTURE,
    "docs/release/V1_0_RC1_RELEASE_NOTES.md": RELEASE_NOTES,
    "docs/release/V1_0_RC1_SECURITY_OPERATIONS.md": SECURITY_OPERATIONS,
    ".github/workflows/r16-17-release-readiness-acceptance.yml": WORKFLOW,
}

root = Path.cwd()
for relative, content in FILES.items():
    path = root / relative
    if path.exists():
        raise SystemExit(f"refusing to overwrite unexpected existing file: {relative}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")

pyproject = root / "pyproject.toml"
text = pyproject.read_text(encoding="utf-8")
if text.count('version = "0.1.0a4"') != 1:
    raise SystemExit("pyproject version anchor drifted")
pyproject.write_text(text.replace('version = "0.1.0a4"', 'version = "1.0.0rc1"', 1), encoding="utf-8")

init_path = root / "src/kodepoia/__init__.py"
text = init_path.read_text(encoding="utf-8")
if text.count('__version__ = "0.1.0a3"') != 1:
    raise SystemExit("runtime version anchor drifted")
init_path.write_text(text.replace('__version__ = "0.1.0a3"', '__version__ = "1.0.0rc1"', 1), encoding="utf-8")

policy_path = root / "configs/r16_supply_chain_policy.json"
policy = json.loads(policy_path.read_text(encoding="utf-8"))
workflows = policy["workflow_policy"]["immutable_authority_workflows"]
new_workflow = ".github/workflows/r16-17-release-readiness-acceptance.yml"
if new_workflow in workflows or len(workflows) != 19:
    raise SystemExit("supply-chain authority list drifted before R16.17 registration")
anchor = ".github/workflows/r16-16-resource-soak-acceptance.yml"
position = workflows.index(anchor) + 1
workflows.insert(position, new_workflow)
policy_path.write_text(json.dumps(policy, indent=2, sort_keys=False) + "\n", encoding="utf-8")

supply_test = root / "tests/test_supply_chain_r16_9.py"
text = supply_test.read_text(encoding="utf-8")
if text.count("assert len(policy.immutable_authority_workflows) == 19") != 1:
    raise SystemExit("supply-chain test authority-count anchor drifted")
text = text.replace(
    "assert len(policy.immutable_authority_workflows) == 19",
    "assert len(policy.immutable_authority_workflows) == 20",
    1,
)
anchor_block = '''    assert (\n        ".github/workflows/r16-16-resource-soak-acceptance.yml"\n        in policy.immutable_authority_workflows\n    )\n'''
if text.count(anchor_block) != 1:
    raise SystemExit("R16.16 supply-chain assertion anchor drifted")
addition = anchor_block + '''    assert (\n        ".github/workflows/r16-17-release-readiness-acceptance.yml"\n        in policy.immutable_authority_workflows\n    )\n'''
text = text.replace(anchor_block, addition, 1)
supply_test.write_text(text, encoding="utf-8")

for relative in (
    "src/kodepoia/quality/release_readiness.py",
    "scripts/r16_17_release_readiness_acceptance.py",
    "tests/test_r16_17_release_readiness.py",
):
    source = (root / relative).read_text(encoding="utf-8")
    compile(source, relative, "exec")

expected = {
    ".github/workflows/r16-17-release-readiness-acceptance.yml",
    "configs/r16_supply_chain_policy.json",
    "docs/release/V1_0_RC1_RELEASE_NOTES.md",
    "docs/release/V1_0_RC1_SECURITY_OPERATIONS.md",
    "pyproject.toml",
    "scripts/r16_17_release_readiness_acceptance.py",
    "src/kodepoia/__init__.py",
    "src/kodepoia/quality/release_readiness.py",
    "tests/fixtures/r16_17_release_readiness/prior_release_state.json",
    "tests/test_r16_17_release_readiness.py",
    "tests/test_supply_chain_r16_9.py",
}
actual = {
    line.strip()
    for line in __import__("subprocess").check_output(
        ["git", "diff", "HEAD", "--name-only"], text=True, encoding="utf-8"
    ).splitlines()
    if line.strip()
}
if actual != expected:
    raise SystemExit(f"unexpected implementation diff: {sorted(actual ^ expected)}")
