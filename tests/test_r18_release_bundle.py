from __future__ import annotations

import json
import stat
import zipfile
from pathlib import Path

import pytest

from kodepoia.release.bundle import (
    MANIFEST_NAME,
    ZIP_TIMESTAMP,
    BundleVerificationError,
    ReleaseBundleError,
    build_release_bundle,
    compare_release_bundles,
    verify_bundle_archive,
)
from kodepoia.release.identity import CURRENT_RELEASE

SOURCE_SHA = "0123456789abcdef0123456789abcdef01234567"


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _installer_manifest(source_sha: str, installer: Path) -> dict[str, object]:
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


@pytest.fixture
def bundle_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "LICENSE").write_text("test license\n", encoding="utf-8", newline="\n")
    installer = tmp_path / "KodepoiaSetup.exe"
    installer.write_bytes(b"MZ-r18.2-test-installer\n")
    manifest = tmp_path / "installer-manifest.json"
    manifest.write_text(
        json.dumps(_installer_manifest(SOURCE_SHA, installer), sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return repo_root, installer, manifest


def _build(
    bundle_inputs: tuple[Path, Path, Path],
    output: Path,
    *,
    installer: Path | None = None,
    manifest: Path | None = None,
):
    repo_root, default_installer, default_manifest = bundle_inputs
    return build_release_bundle(
        installer_path=installer or default_installer,
        installer_manifest_path=manifest or default_manifest,
        source_sha=SOURCE_SHA,
        output_dir=output,
        repo_root=repo_root,
        repository="LaurentCOLL1/Kodepoia",
        workflow_ref="test-workflow",
        run_id="test",
        run_attempt="1",
    )


def _rewrite(
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
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload, mode in entries:
            info = zipfile.ZipInfo(name, ZIP_TIMESTAMP)
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | mode) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(
                info,
                payload,
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            )


def test_same_payload_produces_byte_identical_bundle(bundle_inputs, tmp_path: Path) -> None:
    first = _build(bundle_inputs, tmp_path / "one")
    second = _build(bundle_inputs, tmp_path / "two")
    comparison = compare_release_bundles(
        first.archive_path,
        second.archive_path,
        expected_source_sha=SOURCE_SHA,
    )
    assert comparison["semantic_equivalent"] is True
    assert comparison["payload_equal"] is True
    assert comparison["installer_binary_equal"] is True
    assert comparison["archive_binary_equal"] is True
    assert comparison["manifest_binary_equal"] is True


def test_manifest_binds_identity_hashes_sizes_and_policy_docs(bundle_inputs, tmp_path: Path) -> None:
    result = _build(bundle_inputs, tmp_path / "bundle")
    verified = verify_bundle_archive(result.archive_path, expected_source_sha=SOURCE_SHA)
    manifest = verified["manifest"]
    identity = CURRENT_RELEASE.bind_source(SOURCE_SHA).to_dict()
    assert manifest["release_identity"] == identity
    assert manifest["source_sha"] == SOURCE_SHA
    assert manifest["manifest_digest_binding"] == "external-sha256"
    assert manifest["installer_binary_reproducibility"] == "measured-not-assumed"
    assert {record["path"] for record in manifest["files"]} == {
        "KodepoiaSetup.exe",
        "LICENSE",
        "SHA256SUMS.txt",
        "release-notes.json",
    }
    assert all(record["size"] >= 0 for record in manifest["files"])
    assert all(len(record["sha256"]) == 64 for record in manifest["files"])


def test_tampered_installer_is_rejected(bundle_inputs, tmp_path: Path) -> None:
    result = _build(bundle_inputs, tmp_path / "bundle")
    with zipfile.ZipFile(result.archive_path, "r") as archive:
        payload = archive.read("KodepoiaSetup.exe")
    tampered = tmp_path / "tampered.zip"
    _rewrite(
        result.archive_path,
        tampered,
        replace={"KodepoiaSetup.exe": payload + b"tampered"},
    )
    with pytest.raises(BundleVerificationError):
        verify_bundle_archive(tampered, expected_source_sha=SOURCE_SHA)


def test_path_traversal_member_is_rejected(bundle_inputs, tmp_path: Path) -> None:
    result = _build(bundle_inputs, tmp_path / "bundle")
    attack = tmp_path / "traversal.zip"
    _rewrite(
        result.archive_path,
        attack,
        append=[("../escape.txt", b"escape", 0o644)],
    )
    with pytest.raises(BundleVerificationError):
        verify_bundle_archive(attack, expected_source_sha=SOURCE_SHA)


def test_duplicate_member_is_rejected(bundle_inputs, tmp_path: Path) -> None:
    result = _build(bundle_inputs, tmp_path / "bundle")
    with zipfile.ZipFile(result.archive_path, "r") as archive:
        payload = archive.read("KodepoiaSetup.exe")
    attack = tmp_path / "duplicate.zip"
    _rewrite(
        result.archive_path,
        attack,
        append=[("KodepoiaSetup.exe", payload, 0o755)],
    )
    with pytest.raises(BundleVerificationError):
        verify_bundle_archive(attack, expected_source_sha=SOURCE_SHA)


def test_unexpected_executable_is_rejected(bundle_inputs, tmp_path: Path) -> None:
    result = _build(bundle_inputs, tmp_path / "bundle")
    attack = tmp_path / "unexpected-executable.zip"
    _rewrite(
        result.archive_path,
        attack,
        append=[("evil.exe", b"MZevil", 0o755)],
    )
    with pytest.raises(BundleVerificationError):
        verify_bundle_archive(attack, expected_source_sha=SOURCE_SHA)


def test_casefold_collision_is_rejected(bundle_inputs, tmp_path: Path) -> None:
    result = _build(bundle_inputs, tmp_path / "bundle")
    attack = tmp_path / "collision.zip"
    _rewrite(
        result.archive_path,
        attack,
        append=[("license", b"collision", 0o644)],
    )
    with pytest.raises(BundleVerificationError):
        verify_bundle_archive(attack, expected_source_sha=SOURCE_SHA)


def test_expected_source_mismatch_is_rejected(bundle_inputs, tmp_path: Path) -> None:
    result = _build(bundle_inputs, tmp_path / "bundle")
    with pytest.raises(BundleVerificationError):
        verify_bundle_archive(result.archive_path, expected_source_sha="f" * 40)


def test_installer_binary_variance_preserves_semantic_equivalence(
    bundle_inputs,
    tmp_path: Path,
) -> None:
    first = _build(bundle_inputs, tmp_path / "one")
    repo_root, _, _ = bundle_inputs
    varied_installer = tmp_path / "varied" / "KodepoiaSetup.exe"
    varied_installer.parent.mkdir()
    varied_installer.write_bytes(b"MZ-r18.2-different-installer\n")
    varied_manifest = tmp_path / "varied-manifest.json"
    varied_manifest.write_text(
        json.dumps(_installer_manifest(SOURCE_SHA, varied_installer), sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    second = build_release_bundle(
        installer_path=varied_installer,
        installer_manifest_path=varied_manifest,
        source_sha=SOURCE_SHA,
        output_dir=tmp_path / "two",
        repo_root=repo_root,
        repository="LaurentCOLL1/Kodepoia",
        workflow_ref="test-workflow",
        run_id="test",
        run_attempt="1",
    )
    comparison = compare_release_bundles(
        first.archive_path,
        second.archive_path,
        expected_source_sha=SOURCE_SHA,
    )
    assert comparison["semantic_equivalent"] is True
    assert comparison["payload_equal"] is False
    assert comparison["installer_binary_equal"] is False
    assert comparison["archive_binary_equal"] is False


def test_installer_manifest_hash_mismatch_is_rejected(bundle_inputs, tmp_path: Path) -> None:
    repo_root, installer, manifest = bundle_inputs
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["sha256"] = "0" * 64
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ReleaseBundleError):
        build_release_bundle(
            installer_path=installer,
            installer_manifest_path=manifest,
            source_sha=SOURCE_SHA,
            output_dir=tmp_path / "bundle",
            repo_root=repo_root,
        )


def test_production_signed_installer_boundary_is_rejected(
    bundle_inputs,
    tmp_path: Path,
) -> None:
    repo_root, installer, manifest = bundle_inputs
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["production_signed"] = True
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ReleaseBundleError):
        build_release_bundle(
            installer_path=installer,
            installer_manifest_path=manifest,
            source_sha=SOURCE_SHA,
            output_dir=tmp_path / "bundle",
            repo_root=repo_root,
        )


def test_release_bundle_schema_is_machine_readable() -> None:
    path = Path("schemas/release_bundle_manifest.schema.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert payload["title"] == "Kodepoia ReleaseBundleManifest"
    assert payload["properties"]["manifest_digest_binding"]["const"] == "external-sha256"
    assert payload["properties"]["installer_binary_reproducibility"]["const"] == (
        "measured-not-assumed"
    )
    assert set(
        {
            "format",
            "schema_version",
            "source_sha",
            "platform",
            "release_identity",
            "archive_profile",
            "provenance",
            "files",
            "payload_sha256",
            "semantic_sha256",
            "manifest_digest_binding",
            "installer_binary_reproducibility",
        }
    ).issubset(payload["required"])


def test_archive_has_manifest_and_no_loose_unknown_files(bundle_inputs, tmp_path: Path) -> None:
    result = _build(bundle_inputs, tmp_path / "bundle")
    with zipfile.ZipFile(result.archive_path) as archive:
        assert MANIFEST_NAME in archive.namelist()
        assert archive.namelist() == sorted(archive.namelist())
