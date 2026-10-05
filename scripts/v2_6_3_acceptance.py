from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tomllib
from pathlib import Path
from typing import Any

from kodepoia.release import CURRENT_RELEASE
from kodepoia.release.bundle import compare_release_bundles, verify_bundle_archive
from kodepoia.release.provenance import verify_release_evidence_files
from kodepoia.release.terminal_freeze import TERMINAL_RELEASE_FREEZE


def _check(name: str, condition: bool, detail: str) -> dict[str, object]:
    return {
        "name": name,
        "status": "PASS" if condition else "FAIL",
        "detail": detail,
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def _canonical_digest(payload: dict[str, object]) -> str:
    rendered = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _actual_paths(args: argparse.Namespace) -> dict[str, Path] | None:
    values = {
        "installer": args.installer,
        "installer_manifest": args.installer_manifest,
        "bundle_one": args.bundle_one,
        "bundle_two": args.bundle_two,
        "sbom": args.sbom,
        "provenance": args.provenance,
        "signing_evidence": args.signing_evidence,
        "windows_evidence": args.windows_evidence,
        "staged_release": args.staged_release,
    }
    supplied = [value is not None for value in values.values()]
    if not any(supplied):
        return None
    if not all(supplied):
        missing = sorted(name for name, value in values.items() if value is None)
        raise SystemExit("actual candidate mode requires all evidence paths: " + ", ".join(missing))
    return {name: Path(str(value)) for name, value in values.items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--repository", default="LaurentCOLL1/Kodepoia")
    parser.add_argument("--installer")
    parser.add_argument("--installer-manifest")
    parser.add_argument("--bundle-one")
    parser.add_argument("--bundle-two")
    parser.add_argument("--sbom")
    parser.add_argument("--provenance")
    parser.add_argument("--signing-evidence")
    parser.add_argument("--windows-evidence")
    parser.add_argument("--staged-release")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    source_sha = args.source_sha.strip().lower()
    observed_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        encoding="utf-8",
    ).strip().lower()

    def read(path: str) -> str:
        return (root / path).read_text(encoding="utf-8")

    freeze = TERMINAL_RELEASE_FREEZE
    target = freeze.successor_identity
    pyproject = tomllib.loads(read("pyproject.toml"))
    authority = read("docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md")
    state = read("docs/continuity/STATE.md")
    next_doc = read("docs/continuity/NEXT.md")
    roadmap = read("docs/roadmap/KODEPOIA_ROADMAP_V2.md")
    v26 = read("docs/roadmap/V2_6_HARDENING_NEXT_PUBLIC_WINDOWS_RELEASE.md")
    candidate_doc = read("docs/release/V2_6_3_TERMINAL_CANDIDATE.md")
    python_core = read(".github/workflows/python-core.yml")
    candidate_workflow = read(".github/workflows/v2-6-3-terminal-candidate.yml")
    production_targets = read(
        "docs/release/evidence/V2_6_4_PRETRANSITION_METADATA/targets.json"
    )

    checks = [
        _check(
            "exact_head",
            source_sha == observed_sha,
            "candidate evidence executes the exact requested PR head",
        ),
        _check(
            "current_authority",
            (
                "V2.6.3 — Exact-source Windows release candidate, SBOM, provenance "
                "and signing truth is now the only authorized implementation subdivision"
            )
            in state
            and "Current next action — V2.6.3 only" in next_doc
            and (
                "The only authorized implementation subdivision is **V2.6.3 — "
                "Exact-source Windows release candidate, SBOM, provenance and signing truth**"
            )
            in authority
            and "V2.6.3 CURRENT" in roadmap
            and (
                "V2.6.3 — Exact-source Windows release candidate, SBOM, provenance "
                "and signing truth is the only authorized implementation subdivision"
            )
            in v26,
            "V2.6.3 is the only authorized implementation subdivision",
        ),
        _check(
            "candidate_identity",
            target == CURRENT_RELEASE
            and CURRENT_RELEASE.public_version == "1.1.0"
            and CURRENT_RELEASE.pep440_version == "1.1.0"
            and CURRENT_RELEASE.channel == "stable"
            and CURRENT_RELEASE.build_type == "release"
            and pyproject["project"]["version"] == "1.1.0",
            "canonical source identity is the frozen stable 1.1.0 successor",
        ),
        _check(
            "public_baseline_preserved",
            freeze.public_baseline["public_version"] == "1.1.0-rc8"
            and freeze.public_baseline["tag"] == "v1.1.0-rc8"
            and freeze.public_baseline["production_signed"] is False,
            "last public distribution remains the accepted rc8 baseline",
        ),
        _check(
            "candidate_source_phase",
            freeze.successor["candidate_source_freeze_phase"] == "V2.6.3"
            and freeze.successor["candidate_source_sha"] is None
            and freeze.successor["source_binding"] == "exact-head",
            "historical V2.6.1 freeze defers exact candidate binding to V2.6.3",
        ),
        _check(
            "signing_truth",
            freeze.authenticode["production_signing_verified"] is False
            and freeze.authenticode[
                "production_signing_secret_provisioning_authorized"
            ]
            is False
            and freeze.authenticode["candidate_truth_rule"]
            == "report-exact-observed-signing-state",
            "production signing is not fabricated and secrets are not provisioned",
        ),
        _check(
            "production_tuf_unchanged",
            freeze.production_tuf_repository_observation[
                "production_metadata_mutation_authorized"
            ]
            is False
            and freeze.production_tuf_repository_observation["resolution_phase"]
            == "V2.6.4"
            and "channels/stable/windows-x86_64/1.1.0/" not in production_targets,
            "V2.6.3 does not create a live stable TUF target",
        ),
        _check(
            "candidate_ci_wiring",
            "Run V2.6.3 exact-source candidate synthetic acceptance" in python_core
            and "v2-6-3-terminal-candidate-" in python_core
            and "Build exact-source Windows candidate one" in candidate_workflow
            and "Build exact-source Windows candidate two" in candidate_workflow
            and "Run actual V2.6.3 exact-source candidate acceptance" in candidate_workflow,
            "synthetic Ubuntu/Windows and actual Windows exact-head evidence are mandatory",
        ),
        _check(
            "no_publication_contract",
            "No GitHub Release, public tag, public asset" in candidate_doc
            and "contents: read" in candidate_workflow
            and "gh release create" not in candidate_workflow
            and "git tag" not in candidate_workflow,
            "candidate construction has no public release write path",
        ),
    ]

    actual = _actual_paths(args)
    actual_summary: dict[str, object] | None = None
    if actual is not None:
        for name, path in actual.items():
            if not path.is_file() or path.stat().st_size <= 0:
                raise SystemExit(f"candidate evidence is missing or empty: {name}={path}")

        installer = actual["installer"]
        installer_manifest = _read_json(actual["installer_manifest"])
        installer_sha256 = _sha256_file(installer)
        installer_bytes = installer.stat().st_size
        bundle_one = verify_bundle_archive(
            actual["bundle_one"],
            expected_source_sha=source_sha,
        )
        bundle_two = verify_bundle_archive(
            actual["bundle_two"],
            expected_source_sha=source_sha,
        )
        comparison = compare_release_bundles(
            actual["bundle_one"],
            actual["bundle_two"],
            expected_source_sha=source_sha,
        )
        release_evidence = verify_release_evidence_files(
            actual["sbom"],
            actual["provenance"],
            expected_source_sha=source_sha,
            expected_repository=args.repository,
        )
        signing = _read_json(actual["signing_evidence"])
        windows = _read_json(actual["windows_evidence"])
        staged = _read_json(actual["staged_release"])

        installer_subjects = [
            item
            for item in signing.get("subjects", [])
            if isinstance(item, dict) and item.get("filename") == "KodepoiaSetup.exe"
        ]
        signing_installer = installer_subjects[0] if len(installer_subjects) == 1 else {}

        staged_attestation = staged.get("attestation")
        staged_github = staged.get("github_release")
        staged_tag = staged.get("tag_state")
        staged_signing = staged.get("signing")
        attestation_mode = (
            str(staged_attestation.get("verification_mode", ""))
            if isinstance(staged_attestation, dict)
            else ""
        )
        attestation_truth = (
            isinstance(staged_attestation, dict)
            and staged_attestation.get("verified") is True
            and attestation_mode in {"synthetic-offline", "github-cli"}
            and staged_attestation.get("live_verified")
            is (attestation_mode == "github-cli")
        )

        actual_checks = [
            _check(
                "installer_exact_source",
                installer_manifest.get("source_sha") == source_sha
                and installer_manifest.get("public_version") == "1.1.0"
                and installer_manifest.get("pep440_version") == "1.1.0"
                and installer_manifest.get("channel") == "stable"
                and installer_manifest.get("build_type") == "release"
                and installer_manifest.get("sha256") == installer_sha256
                and installer_manifest.get("production_signed") is False,
                "installer manifest binds stable 1.1.0 to the exact candidate SHA",
            ),
            _check(
                "installer_digest_and_length",
                installer_bytes > 0
                and len(installer_sha256) == 64
                and bundle_one["manifest"]["source_sha"] == source_sha,
                "candidate records the exact installer digest and byte length",
            ),
            _check(
                "bundle_sbom_provenance",
                bundle_one["manifest"]["release_identity"]
                == CURRENT_RELEASE.bind_source(source_sha).to_dict()
                and bundle_two["manifest"]["release_identity"]
                == CURRENT_RELEASE.bind_source(source_sha).to_dict()
                and "release_evidence" in bundle_one["manifest"]
                and release_evidence["sbom_sha256"]
                == bundle_one["manifest"]["release_evidence"]["sbom_sha256"]
                and release_evidence["provenance_sha256"]
                == bundle_one["manifest"]["release_evidence"]["provenance_sha256"],
                "both release bundles preserve exact identity, SBOM and provenance lineage",
            ),
            _check(
                "two_build_comparison",
                comparison["semantic_equivalent"] is True
                and comparison["source_sha"] == source_sha,
                "two-build R18 comparison proves semantic equivalence and reports binary equality",
            ),
            _check(
                "authenticode_observed_truth",
                signing.get("source_sha") == source_sha
                and signing.get("mode") == "unsigned"
                and signing.get("production_signed") is False
                and signing.get("public_trust_claim") is False
                and signing_installer.get("sha256") == installer_sha256
                and str(signing_installer.get("authenticode_status", "")).lower()
                == "notsigned",
                "candidate installer is truthfully recorded as unsigned",
            ),
            _check(
                "windows_clean_install_smoke_uninstall",
                windows.get("source_sha") == source_sha
                and windows.get("clean_install_smoke") is True
                and windows.get("clean_uninstall") is True
                and windows.get("project_data_mutation") is False,
                "exact candidate installs, launches packaged smoke and uninstalls cleanly",
            ),
            _check(
                "staged_release_exact_source",
                staged.get("state") == "staged"
                and staged.get("source_sha") == source_sha
                and staged.get("tag") == "v1.1.0"
                and isinstance(staged_github, dict)
                and staged_github.get("draft") is True
                and staged_github.get("target_commitish") == source_sha
                and staged_github.get("publication_triggered") is False
                and isinstance(staged_tag, dict)
                and staged_tag.get("tag_exists") is False
                and staged_tag.get("release_exists") is False
                and isinstance(staged_signing, dict)
                and staged_signing.get("mode") == "unsigned",
                "R18.5 staging is immutable, exact-source, draft-only and non-publishing",
            ),
            _check(
                "attestation_truth",
                attestation_truth,
                "attestation state is explicit: live GitHub verification or synthetic-offline",
            ),
        ]
        checks.extend(actual_checks)
        actual_summary = {
            "installer": {
                "filename": installer.name,
                "sha256": installer_sha256,
                "bytes": installer_bytes,
            },
            "bundle": {
                "filename": Path(bundle_one["archive_path"]).name,
                "sha256": bundle_one["archive_sha256"],
                "bytes": bundle_one["archive_size"],
                "manifest_sha256": bundle_one["manifest_sha256"],
                "payload_sha256": bundle_one["manifest"]["payload_sha256"],
                "semantic_sha256": bundle_one["manifest"]["semantic_sha256"],
            },
            "two_build": comparison,
            "release_evidence": release_evidence,
            "signing": {
                "mode": signing.get("mode"),
                "production_signed": signing.get("production_signed"),
                "public_trust_claim": signing.get("public_trust_claim"),
            },
            "attestation": {
                "verification_mode": attestation_mode,
                "live_verified": (
                    staged_attestation.get("live_verified")
                    if isinstance(staged_attestation, dict)
                    else False
                ),
            },
            "staged_release": {
                "stage_digest": staged.get("stage_digest"),
                "tag": staged.get("tag"),
                "state": staged.get("state"),
            },
        }

    passed = all(item["status"] == "PASS" for item in checks)
    payload: dict[str, object] = {
        "schema_version": 1,
        "subdivision": "V2.6.3",
        "title": (
            "Exact-source Windows release candidate, SBOM, provenance and signing truth"
        ),
        "mode": "actual-windows-candidate" if actual is not None else "synthetic-contract",
        "source_sha": source_sha,
        "observed_sha": observed_sha,
        "candidate_source_sha": source_sha,
        "public_baseline": dict(freeze.public_baseline),
        "candidate_identity": CURRENT_RELEASE.bind_source(source_sha).to_dict(),
        "actual_candidate": actual_summary,
        "checks": checks,
        "summary": {
            "passed": sum(item["status"] == "PASS" for item in checks),
            "total": len(checks),
        },
        "status": "PASS" if passed else "FAIL",
        "public_release_triggered": False,
        "public_tag_triggered": False,
        "public_asset_upload_triggered": False,
        "production_tuf_mutation_triggered": False,
        "live_updater_activation_triggered": False,
        "signing_secret_provisioned": False,
        "winget_submission_triggered": False,
    }
    payload["evidence_sha256"] = _canonical_digest(payload)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "
",
        encoding="utf-8",
        newline="
",
    )
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
