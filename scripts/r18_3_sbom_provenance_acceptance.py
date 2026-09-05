from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

from kodepoia.release.bundle import verify_bundle_archive
from kodepoia.release.provenance import (
    ATTESTATION_SEMANTICS,
    PROVENANCE_NAME,
    SBOM_NAME,
    SPDX_PREDICATE_TYPE,
    ReleaseEvidenceError,
    verify_release_evidence_files,
    write_release_evidence,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _synthetic(source_sha: str, repo_root: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="kodepoia-r18-3-") as tmp_name:
        output = Path(tmp_name) / "evidence"
        result = write_release_evidence(
            repo_root=repo_root,
            output_dir=output,
            source_sha=source_sha,
            repository="LaurentCOLL1/Kodepoia",
            workflow_ref="synthetic-r18.3",
            run_id="synthetic",
            run_attempt="1",
            optional_groups=(),
            created_at="2026-09-05T00:00:00Z",
        )
        verified = verify_release_evidence_files(
            result.sbom_path,
            result.provenance_path,
            expected_source_sha=source_sha,
            expected_repository="LaurentCOLL1/Kodepoia",
        )

        tampered_sbom = output / "tampered.spdx.json"
        tampered_sbom.write_bytes(result.sbom_path.read_bytes() + b" ")
        negative = ""
        try:
            verify_release_evidence_files(
                tampered_sbom,
                result.provenance_path,
                expected_source_sha=source_sha,
                expected_repository="LaurentCOLL1/Kodepoia",
            )
        except ReleaseEvidenceError as exc:
            negative = str(exc)
        if not negative:
            raise AssertionError("tampered SBOM unexpectedly verified")

        return {
            "status": "PASS",
            "mode": "synthetic",
            "source_sha": source_sha,
            "sbom": {
                "path": SBOM_NAME,
                "sha256": result.sbom_sha256,
                "predicate_type": SPDX_PREDICATE_TYPE,
                "packages_total": result.packages_total,
                "runtime_roots": list(result.runtime_roots),
                "unresolved_roots": list(result.unresolved_roots),
                "inventory_complete": False,
            },
            "provenance": {
                "path": PROVENANCE_NAME,
                "sha256": result.provenance_sha256,
                "attestation_semantics": ATTESTATION_SEMANTICS,
            },
            "verified": verified,
            "negative_controls": {"tampered_sbom": negative},
            "manual_intervention": "NONE",
            "production_signing": "NOT_TRIGGERED",
            "public_github_release": "NOT_TRIGGERED",
            "public_winget_submission": "NOT_TRIGGERED",
        }


def _actual(
    source_sha: str,
    bundle: Path,
    sbom: Path,
    provenance: Path,
    repository: str,
    *,
    build_attestation_verified: bool,
    sbom_attestation_verified: bool,
    tamper_negative_verified: bool,
) -> dict[str, Any]:
    evidence = verify_release_evidence_files(
        sbom,
        provenance,
        expected_source_sha=source_sha,
        expected_repository=repository,
    )
    bundle_result = verify_bundle_archive(bundle, expected_source_sha=source_sha)
    manifest = bundle_result["manifest"]
    release_evidence = manifest.get("release_evidence")
    if not isinstance(release_evidence, dict):
        raise AssertionError("actual R18.3 bundle does not expose release_evidence binding")
    if release_evidence.get("sbom_sha256") != evidence["sbom_sha256"]:
        raise AssertionError("bundle SBOM digest binding mismatch")
    if release_evidence.get("provenance_sha256") != evidence["provenance_sha256"]:
        raise AssertionError("bundle provenance digest binding mismatch")
    if not build_attestation_verified:
        raise AssertionError("GitHub build provenance attestation was not verified")
    if not sbom_attestation_verified:
        raise AssertionError("GitHub SPDX SBOM attestation was not verified")
    if not tamper_negative_verified:
        raise AssertionError("modified-subject attestation negative control was not verified")

    return {
        "status": "PASS",
        "mode": "actual-github-attestation",
        "source_sha": source_sha,
        "bundle": {
            "path": str(bundle),
            "sha256": bundle_result["archive_sha256"],
            "size": bundle_result["archive_size"],
            "manifest_sha256": bundle_result["manifest_sha256"],
        },
        "sbom": {
            "path": str(sbom),
            "sha256": _sha256(sbom),
            "predicate_type": SPDX_PREDICATE_TYPE,
            **evidence["sbom"],
        },
        "provenance": {
            "path": str(provenance),
            "sha256": _sha256(provenance),
            **evidence["provenance"],
        },
        "attestation": {
            "provider": "github-artifact-attestations",
            "build_provenance_verified": True,
            "sbom_attestation_verified": True,
            "modified_subject_rejected": True,
            "semantics": ATTESTATION_SEMANTICS,
        },
        "manual_intervention": "NONE",
        "production_signing": "NOT_TRIGGERED",
        "public_github_release": "NOT_TRIGGERED",
        "public_winget_submission": "NOT_TRIGGERED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit exact-source R18.3 acceptance evidence.")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--repository", default="LaurentCOLL1/Kodepoia")
    parser.add_argument("--bundle")
    parser.add_argument("--sbom")
    parser.add_argument("--provenance")
    parser.add_argument("--build-attestation-verified", action="store_true")
    parser.add_argument("--sbom-attestation-verified", action="store_true")
    parser.add_argument("--tamper-negative-verified", action="store_true")
    args = parser.parse_args()

    actual_args = (args.bundle, args.sbom, args.provenance)
    if any(actual_args) and not all(actual_args):
        parser.error("--bundle, --sbom and --provenance must be supplied together")

    if args.bundle:
        report = _actual(
            args.source_sha,
            Path(args.bundle),
            Path(args.sbom),
            Path(args.provenance),
            args.repository,
            build_attestation_verified=args.build_attestation_verified,
            sbom_attestation_verified=args.sbom_attestation_verified,
            tamper_negative_verified=args.tamper_negative_verified,
        )
    else:
        report = _synthetic(args.source_sha, Path(args.repo_root))

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
