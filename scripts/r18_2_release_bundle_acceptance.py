from __future__ import annotations

import argparse
import hashlib
import json
import stat
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from kodepoia.release.bundle import (
    ZIP_TIMESTAMP,
    BundleVerificationError,
    build_release_bundle,
    compare_release_bundles,
    verify_bundle_archive,
)
from kodepoia.release.identity import CURRENT_RELEASE


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def _write_info(
    archive: zipfile.ZipFile,
    name: str,
    payload: bytes,
    *,
    mode: int = 0o644,
) -> None:
    info = zipfile.ZipInfo(name, ZIP_TIMESTAMP)
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | mode) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(info, payload, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def _rewrite_archive(
    source: Path,
    target: Path,
    *,
    replace: dict[str, bytes] | None = None,
    append: list[tuple[str, bytes, int]] | None = None,
) -> None:
    replace = replace or {}
    append = append or []
    with zipfile.ZipFile(source, "r") as original:
        entries = [
            (
                info.filename,
                replace.get(info.filename, original.read(info.filename)),
                (info.external_attr >> 16) & 0o7777,
            )
            for info in original.infolist()
        ]
    entries.extend(append)
    with zipfile.ZipFile(
        target,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for name, payload, mode in entries:
            _write_info(archive, name, payload, mode=mode)


def _expect_rejected(path: Path, source_sha: str) -> str:
    try:
        verify_bundle_archive(path, expected_source_sha=source_sha)
    except BundleVerificationError as exc:
        return str(exc)
    raise AssertionError(f"negative control unexpectedly verified: {path.name}")


def _installer_manifest(source_sha: str, installer: Path) -> dict[str, Any]:
    identity = CURRENT_RELEASE.bind_source(source_sha).to_dict()
    return {
        "version": identity["installer_version"],
        "public_version": identity["public_version"],
        "pep440_version": identity["pep440_version"],
        "installer_version": identity["installer_version"],
        "channel": identity["channel"],
        "build_type": identity["build_type"],
        "package": identity["package"],
        "source_sha": source_sha,
        "release_identity_schema": identity["schema_version"],
        "installer": "KodepoiaSetup.exe",
        "sha256": _sha256(installer),
        "standalone_executable": "KodepoiaStudio.exe",
        "production_signed": False,
    }


def _schema_evidence(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "schemas" / "release_bundle_manifest.schema.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise AssertionError("release bundle manifest schema must use JSON Schema 2020-12")
    if payload.get("title") != "Kodepoia ReleaseBundleManifest":
        raise AssertionError("release bundle manifest schema title mismatch")
    return {
        "path": str(path.as_posix()),
        "sha256": _sha256(path),
        "draft": payload["$schema"],
        "title": payload["title"],
    }


def _run_synthetic(source_sha: str, repo_root: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="kodepoia-r18-2-") as tmp_name:
        tmp = Path(tmp_name)
        synthetic_root = tmp / "repo"
        synthetic_root.mkdir()
        (synthetic_root / "LICENSE").write_text(
            "Kodepoia synthetic R18.2 acceptance license.\n",
            encoding="utf-8",
            newline="\n",
        )
        installer = tmp / "KodepoiaSetup.exe"
        installer.write_bytes(b"MZ\x90\x00KODEPOIA-R18.2-SYNTHETIC-INSTALLER\n")
        installer_manifest_path = tmp / "installer-manifest.json"
        installer_manifest_path.write_text(
            _canonical_json(_installer_manifest(source_sha, installer)),
            encoding="utf-8",
            newline="\n",
        )

        provenance = {
            "repository": "LaurentCOLL1/Kodepoia",
            "workflow_ref": "synthetic-r18.2",
            "run_id": "synthetic",
            "run_attempt": "1",
        }
        first = build_release_bundle(
            installer_path=installer,
            installer_manifest_path=installer_manifest_path,
            source_sha=source_sha,
            output_dir=tmp / "first",
            repo_root=synthetic_root,
            **provenance,
        )
        second = build_release_bundle(
            installer_path=installer,
            installer_manifest_path=installer_manifest_path,
            source_sha=source_sha,
            output_dir=tmp / "second",
            repo_root=synthetic_root,
            **provenance,
        )
        comparison = compare_release_bundles(
            first.archive_path,
            second.archive_path,
            expected_source_sha=source_sha,
        )
        if not all(
            comparison[key]
            for key in (
                "semantic_equivalent",
                "payload_equal",
                "installer_binary_equal",
                "archive_binary_equal",
                "manifest_binary_equal",
            )
        ):
            raise AssertionError("identical synthetic payloads must produce byte-identical bundles")

        valid = verify_bundle_archive(first.archive_path, expected_source_sha=source_sha)
        manifest = valid["manifest"]
        if manifest["manifest_digest_binding"] != "external-sha256":
            raise AssertionError("manifest digest must be externally bound")
        if manifest["installer_binary_reproducibility"] != "measured-not-assumed":
            raise AssertionError("installer reproducibility must be measured, not assumed")

        negative: dict[str, str] = {}

        with zipfile.ZipFile(first.archive_path, "r") as archive:
            installer_payload = archive.read("KodepoiaSetup.exe")
        tampered = tmp / "tampered.zip"
        _rewrite_archive(
            first.archive_path,
            tampered,
            replace={"KodepoiaSetup.exe": installer_payload + b"TAMPER"},
        )
        negative["tampered_installer"] = _expect_rejected(tampered, source_sha)

        traversal = tmp / "traversal.zip"
        _rewrite_archive(
            first.archive_path,
            traversal,
            append=[("../escape.txt", b"escape", 0o644)],
        )
        negative["path_traversal"] = _expect_rejected(traversal, source_sha)

        duplicate = tmp / "duplicate.zip"
        _rewrite_archive(
            first.archive_path,
            duplicate,
            append=[("KodepoiaSetup.exe", installer_payload, 0o755)],
        )
        negative["duplicate_member"] = _expect_rejected(duplicate, source_sha)

        unexpected_executable = tmp / "unexpected-executable.zip"
        _rewrite_archive(
            first.archive_path,
            unexpected_executable,
            append=[("evil.exe", b"MZevil", 0o755)],
        )
        negative["unexpected_executable"] = _expect_rejected(
            unexpected_executable,
            source_sha,
        )

        collision = tmp / "casefold-collision.zip"
        _rewrite_archive(
            first.archive_path,
            collision,
            append=[("license", b"collision", 0o644)],
        )
        negative["casefold_collision"] = _expect_rejected(collision, source_sha)

        wrong_source = "f" * 40 if source_sha != "f" * 40 else "e" * 40
        try:
            verify_bundle_archive(first.archive_path, expected_source_sha=wrong_source)
        except BundleVerificationError as exc:
            negative["source_sha_mismatch"] = str(exc)
        else:
            raise AssertionError("wrong expected source SHA unexpectedly verified")

        changed_installer = tmp / "KodepoiaSetup-changed.exe"
        changed_installer.write_bytes(installer.read_bytes() + b"BINARY-VARIANCE")
        changed_manifest = tmp / "installer-manifest-changed.json"
        changed_payload = _installer_manifest(source_sha, changed_installer)
        changed_payload["installer"] = "KodepoiaSetup.exe"
        changed_manifest.write_text(
            _canonical_json(changed_payload),
            encoding="utf-8",
            newline="\n",
        )
        canonical_changed_installer = tmp / "changed" / "KodepoiaSetup.exe"
        canonical_changed_installer.parent.mkdir()
        canonical_changed_installer.write_bytes(changed_installer.read_bytes())
        varied = build_release_bundle(
            installer_path=canonical_changed_installer,
            installer_manifest_path=changed_manifest,
            source_sha=source_sha,
            output_dir=tmp / "varied",
            repo_root=synthetic_root,
            **provenance,
        )
        variance = compare_release_bundles(
            first.archive_path,
            varied.archive_path,
            expected_source_sha=source_sha,
        )
        if not variance["semantic_equivalent"]:
            raise AssertionError("installer-only binary variance must preserve semantic equivalence")
        if variance["payload_equal"] or variance["installer_binary_equal"]:
            raise AssertionError("installer binary variance must change payload and installer digests")

        return {
            "status": "PASS",
            "mode": "synthetic",
            "source_sha": source_sha,
            "bundle": {
                "archive_sha256": valid["archive_sha256"],
                "archive_size": valid["archive_size"],
                "manifest_sha256": valid["manifest_sha256"],
                "payload_sha256": manifest["payload_sha256"],
                "semantic_sha256": manifest["semantic_sha256"],
            },
            "same_payload_comparison": comparison,
            "installer_variance_comparison": variance,
            "negative_controls": negative,
            "schema": _schema_evidence(repo_root),
            "manual_intervention": "NONE",
            "production_signing": "NOT_TRIGGERED",
            "public_github_release": "NOT_TRIGGERED",
            "public_winget_submission": "NOT_TRIGGERED",
        }


def _run_actual(
    source_sha: str,
    first: Path,
    second: Path,
    repo_root: Path,
) -> dict[str, Any]:
    first_result = verify_bundle_archive(first, expected_source_sha=source_sha)
    second_result = verify_bundle_archive(second, expected_source_sha=source_sha)
    comparison = compare_release_bundles(
        first,
        second,
        expected_source_sha=source_sha,
    )
    if not comparison["semantic_equivalent"]:
        raise AssertionError("two exact-source Windows builds are not semantically equivalent")
    binary_reproducibility = (
        "observed-identical"
        if comparison["installer_binary_equal"]
        else "platform-variance-observed"
    )
    return {
        "status": "PASS",
        "mode": "actual-windows-two-build",
        "source_sha": source_sha,
        "bundle_one": {
            "archive_sha256": first_result["archive_sha256"],
            "archive_size": first_result["archive_size"],
            "manifest_sha256": first_result["manifest_sha256"],
            "payload_sha256": first_result["manifest"]["payload_sha256"],
            "semantic_sha256": first_result["manifest"]["semantic_sha256"],
        },
        "bundle_two": {
            "archive_sha256": second_result["archive_sha256"],
            "archive_size": second_result["archive_size"],
            "manifest_sha256": second_result["manifest_sha256"],
            "payload_sha256": second_result["manifest"]["payload_sha256"],
            "semantic_sha256": second_result["manifest"]["semantic_sha256"],
        },
        "comparison": comparison,
        "installer_binary_reproducibility": binary_reproducibility,
        "schema": _schema_evidence(repo_root),
        "manual_intervention": "NONE",
        "production_signing": "NOT_TRIGGERED",
        "public_github_release": "NOT_TRIGGERED",
        "public_winget_submission": "NOT_TRIGGERED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit exact-source R18.2 deterministic release bundle acceptance."
    )
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--bundle-one")
    parser.add_argument("--bundle-two")
    args = parser.parse_args()

    first = Path(args.bundle_one) if args.bundle_one else None
    second = Path(args.bundle_two) if args.bundle_two else None
    if (first is None) != (second is None):
        parser.error("--bundle-one and --bundle-two must be supplied together")

    repo_root = Path(args.repo_root)
    if first is None:
        report = _run_synthetic(args.source_sha, repo_root)
    else:
        report = _run_actual(args.source_sha, first, second, repo_root)

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
