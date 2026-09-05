from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import zipfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from kodepoia.release.identity import CURRENT_RELEASE
from kodepoia.release.provenance import (
    ATTESTATION_SEMANTICS,
    PROVENANCE_NAME,
    SBOM_NAME,
    SPDX_PREDICATE_TYPE,
    ReleaseEvidenceError,
    verify_release_evidence_files,
    verify_release_evidence_payloads,
)

BUNDLE_FORMAT = "kodepoia-release-bundle"
BUNDLE_SCHEMA_VERSION = 1
MANIFEST_NAME = "release-bundle-manifest.json"
CHECKSUMS_NAME = "SHA256SUMS.txt"
RELEASE_NOTES_NAME = "release-notes.json"
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
_SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_EXECUTABLE_SUFFIXES = {
    ".bat",
    ".cmd",
    ".com",
    ".dll",
    ".exe",
    ".msi",
    ".ps1",
    ".scr",
}
_ALLOWED_ROLES = {
    "installer",
    "checksums",
    "license",
    "notice",
    "release-notes",
    "sbom",
    "provenance",
}
_POLICY_NOTICE_NAMES = (
    "NOTICE",
    "NOTICE.md",
    "THIRD_PARTY_NOTICES",
    "THIRD_PARTY_NOTICES.md",
)


class ReleaseBundleError(ValueError):
    """Raised when a release bundle cannot be built."""


class BundleVerificationError(ReleaseBundleError):
    """Raised when a release bundle fails verification."""


@dataclass(frozen=True)
class BundleBuildResult:
    archive_path: Path
    archive_sha256: str
    archive_size: int
    manifest_sha256: str
    payload_sha256: str
    semantic_sha256: str
    manifest: dict[str, Any]


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    rendered = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return (rendered + "\n").encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_source_sha(source_sha: str) -> str:
    normalized = source_sha.strip().lower()
    if not _SOURCE_SHA_RE.fullmatch(normalized):
        raise ReleaseBundleError(
            "source SHA must be an exact lowercase-compatible 40-character hexadecimal Git commit"
        )
    return normalized


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseBundleError(f"unable to read JSON document {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ReleaseBundleError(f"JSON document {path} must contain an object")
    return payload


def _safe_archive_path(name: str) -> str:
    if not name or "\x00" in name:
        raise BundleVerificationError("archive member path must not be empty or contain NUL")
    if "\\" in name:
        raise BundleVerificationError(f"archive member path must use '/' separators: {name!r}")
    if name.startswith("/") or name.endswith("/"):
        raise BundleVerificationError(f"archive member must be a relative regular file: {name!r}")
    parts = name.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise BundleVerificationError(f"unsafe archive member path: {name!r}")
    if any(":" in part for part in parts):
        raise BundleVerificationError(f"archive member path must not contain ':' components: {name!r}")
    if any(part.endswith((" ", ".")) for part in parts):
        raise BundleVerificationError(
            f"archive member path must not end a component with space or dot: {name!r}"
        )
    return name


def _canonical_release_identity(source_sha: str) -> dict[str, Any]:
    return CURRENT_RELEASE.bind_source(source_sha).to_dict()


def _validate_installer_manifest(
    installer_path: Path,
    installer_manifest: Mapping[str, Any],
    source_sha: str,
) -> dict[str, Any]:
    identity = _canonical_release_identity(source_sha)
    required_matches = {
        "source_sha": source_sha,
        "public_version": identity["public_version"],
        "pep440_version": identity["pep440_version"],
        "installer_version": identity["installer_version"],
        "channel": identity["channel"],
        "build_type": identity["build_type"],
        "package": identity["package"],
    }
    for key, expected in required_matches.items():
        actual = installer_manifest.get(key)
        if actual != expected:
            raise ReleaseBundleError(
                f"installer manifest {key!r} mismatch: expected {expected!r}, got {actual!r}"
            )

    if installer_manifest.get("installer") != "KodepoiaSetup.exe":
        raise ReleaseBundleError("installer manifest must bind exactly KodepoiaSetup.exe")
    if installer_path.name != "KodepoiaSetup.exe":
        raise ReleaseBundleError("release bundle installer filename must be KodepoiaSetup.exe")
    if installer_manifest.get("production_signed") is not False:
        raise ReleaseBundleError(
            "R18.2 accepts only the unsigned deterministic payload boundary; "
            "production signing is out of scope"
        )

    expected_hash = str(installer_manifest.get("sha256", "")).strip().lower()
    if not _SHA256_RE.fullmatch(expected_hash):
        raise ReleaseBundleError("installer manifest requires a lowercase SHA-256 digest")
    actual_hash = _sha256_file(installer_path)
    if actual_hash != expected_hash:
        raise ReleaseBundleError(
            f"installer digest mismatch: manifest {expected_hash}, actual {actual_hash}"
        )
    return identity


def _default_provenance(
    workflow_ref: str | None,
    run_id: str | None,
    run_attempt: str | None,
    repository: str | None,
) -> dict[str, str]:
    return {
        "repository": repository or os.getenv("GITHUB_REPOSITORY", "local"),
        "workflow_ref": workflow_ref or os.getenv("GITHUB_WORKFLOW_REF", "local"),
        "run_id": run_id or os.getenv("GITHUB_RUN_ID", "local"),
        "run_attempt": run_attempt or os.getenv("GITHUB_RUN_ATTEMPT", "local"),
    }


def _release_notes_payload(
    identity: Mapping[str, Any],
    provenance: Mapping[str, str],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "product": identity["product"],
        "package": identity["package"],
        "source_sha": identity["source_sha"],
        "public_version": identity["public_version"],
        "pep440_version": identity["pep440_version"],
        "installer_version": identity["installer_version"],
        "channel": identity["channel"],
        "build_type": identity["build_type"],
        "release_candidate": True,
        "production_signed": False,
        "github_release_published": False,
        "winget_published": False,
        "template": "docs/release/RELEASE_NOTES_TEMPLATE.md",
        "provenance": dict(provenance),
    }


def _policy_documents(repo_root: Path) -> list[tuple[str, str, bytes]]:
    license_path = repo_root / "LICENSE"
    if not license_path.is_file():
        raise ReleaseBundleError("repository policy requires LICENSE in every release bundle")
    docs: list[tuple[str, str, bytes]] = [
        ("LICENSE", "license", license_path.read_bytes()),
    ]
    for name in _POLICY_NOTICE_NAMES:
        path = repo_root / name
        if path.is_file():
            docs.append((name, "notice", path.read_bytes()))
    return docs


def _file_record(path: str, role: str, payload: bytes) -> dict[str, Any]:
    _safe_archive_path(path)
    if role not in _ALLOWED_ROLES:
        raise ReleaseBundleError(f"unsupported release bundle role: {role!r}")
    return {
        "path": path,
        "role": role,
        "sha256": _sha256_bytes(payload),
        "size": len(payload),
    }


def _payload_digest(
    release_identity: Mapping[str, Any],
    records: Sequence[Mapping[str, Any]],
) -> str:
    material = {
        "release_identity": dict(release_identity),
        "files": [dict(record) for record in records],
    }
    return _sha256_bytes(_canonical_json_bytes(material))


def _semantic_digest(
    release_identity: Mapping[str, Any],
    records: Sequence[Mapping[str, Any]],
) -> str:
    semantic_records: list[dict[str, Any]] = []
    for record in records:
        item = {
            "path": record["path"],
            "role": record["role"],
        }
        if record["role"] not in {"installer", "checksums"}:
            item["sha256"] = record["sha256"]
            item["size"] = record["size"]
        semantic_records.append(item)
    material = {
        "release_identity": dict(release_identity),
        "files": semantic_records,
    }
    return _sha256_bytes(_canonical_json_bytes(material))


def _checksums_payload(records: Sequence[Mapping[str, Any]]) -> bytes:
    lines = [f"{record['sha256']}  {record['path']}" for record in records]
    return ("\n".join(lines) + "\n").encode("utf-8")


def _archive_profile() -> dict[str, Any]:
    return {
        "entry_order": "lexicographic",
        "timestamp": "1980-01-01T00:00:00",
        "regular_file_mode": "0644",
        "installer_mode": "0755",
        "compression": "deflate-9",
        "deterministic_given_identical_payload": True,
    }


def _mode_for_path(path: str, role: str) -> int:
    if path == "KodepoiaSetup.exe" and role == "installer":
        return 0o755
    return 0o644


def _write_deterministic_zip(
    archive_path: Path,
    payloads: Mapping[str, tuple[str, bytes]],
    manifest_bytes: bytes,
) -> None:
    archive_entries: dict[str, tuple[str, bytes]] = dict(payloads)
    archive_entries[MANIFEST_NAME] = ("manifest", manifest_bytes)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        archive_path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
        allowZip64=True,
    ) as archive:
        for name in sorted(archive_entries):
            role, payload = archive_entries[name]
            info = zipfile.ZipInfo(filename=name, date_time=ZIP_TIMESTAMP)
            info.create_system = 3
            mode = 0o644 if role == "manifest" else _mode_for_path(name, role)
            info.external_attr = (stat.S_IFREG | mode) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, payload, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build_release_bundle(
    *,
    installer_path: str | Path,
    installer_manifest_path: str | Path,
    source_sha: str,
    output_dir: str | Path,
    repo_root: str | Path = ".",
    workflow_ref: str | None = None,
    run_id: str | None = None,
    run_attempt: str | None = None,
    repository: str | None = None,
    sbom_path: str | Path | None = None,
    provenance_path: str | Path | None = None,
) -> BundleBuildResult:
    source_sha = _validate_source_sha(source_sha)
    installer = Path(installer_path)
    installer_manifest_file = Path(installer_manifest_path)
    root = Path(repo_root)
    if not installer.is_file():
        raise ReleaseBundleError(f"installer does not exist: {installer}")
    if not installer_manifest_file.is_file():
        raise ReleaseBundleError(
            f"installer manifest does not exist: {installer_manifest_file}"
        )

    installer_manifest = _read_json(installer_manifest_file)
    identity = _validate_installer_manifest(installer, installer_manifest, source_sha)
    provenance = _default_provenance(workflow_ref, run_id, run_attempt, repository)
    evidence_summary: dict[str, Any] | None = None
    if (sbom_path is None) != (provenance_path is None):
        raise ReleaseBundleError("R18.3 SBOM and provenance files must be supplied together")
    if sbom_path is not None and provenance_path is not None:
        try:
            evidence_summary = verify_release_evidence_files(
                sbom_path,
                provenance_path,
                expected_source_sha=source_sha,
                expected_repository=provenance["repository"],
            )
        except (OSError, ReleaseEvidenceError) as exc:
            raise ReleaseBundleError(f"invalid R18.3 release evidence: {exc}") from exc

    payloads: dict[str, tuple[str, bytes]] = {
        "KodepoiaSetup.exe": ("installer", installer.read_bytes()),
        RELEASE_NOTES_NAME: (
            "release-notes",
            _canonical_json_bytes(_release_notes_payload(identity, provenance)),
        ),
    }
    if evidence_summary is not None:
        payloads[SBOM_NAME] = ("sbom", Path(sbom_path).read_bytes())
        payloads[PROVENANCE_NAME] = ("provenance", Path(provenance_path).read_bytes())
    for path, role, payload in _policy_documents(root):
        payloads[path] = (role, payload)

    pre_checksum_records = [
        _file_record(path, role, payload)
        for path, (role, payload) in sorted(payloads.items())
    ]
    payloads[CHECKSUMS_NAME] = (
        "checksums",
        _checksums_payload(pre_checksum_records),
    )
    records = [
        _file_record(path, role, payload)
        for path, (role, payload) in sorted(payloads.items())
    ]

    manifest: dict[str, Any] = {
        "format": BUNDLE_FORMAT,
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "source_sha": source_sha,
        "platform": "windows",
        "release_identity": identity,
        "archive_profile": _archive_profile(),
        "provenance": provenance,
        "files": records,
        "payload_sha256": _payload_digest(identity, records),
        "semantic_sha256": _semantic_digest(identity, records),
        "manifest_digest_binding": "external-sha256",
        "installer_binary_reproducibility": "measured-not-assumed",
    }
    if evidence_summary is not None:
        manifest["release_evidence"] = {
            "sbom_path": SBOM_NAME,
            "sbom_sha256": evidence_summary["sbom_sha256"],
            "provenance_path": PROVENANCE_NAME,
            "provenance_sha256": evidence_summary["provenance_sha256"],
            "sbom_predicate_type": SPDX_PREDICATE_TYPE,
            "attestation_semantics": ATTESTATION_SEMANTICS,
        }
    manifest_bytes = _canonical_json_bytes(manifest)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    archive_name = f"Kodepoia-{identity['public_version']}-windows.zip"
    archive_path = output / archive_name
    _write_deterministic_zip(archive_path, payloads, manifest_bytes)

    verified = verify_bundle_archive(archive_path, expected_source_sha=source_sha)
    return BundleBuildResult(
        archive_path=archive_path,
        archive_sha256=_sha256_file(archive_path),
        archive_size=archive_path.stat().st_size,
        manifest_sha256=verified["manifest_sha256"],
        payload_sha256=verified["manifest"]["payload_sha256"],
        semantic_sha256=verified["manifest"]["semantic_sha256"],
        manifest=verified["manifest"],
    )


def _parse_manifest_bytes(payload: bytes) -> dict[str, Any]:
    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BundleVerificationError(f"invalid bundle manifest JSON: {exc}") from exc
    if not isinstance(decoded, dict):
        raise BundleVerificationError("bundle manifest root must be an object")
    return decoded


def _validate_manifest_structure(
    manifest: Mapping[str, Any],
    expected_source_sha: str | None,
) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    if manifest.get("format") != BUNDLE_FORMAT:
        raise BundleVerificationError("unsupported release bundle format")
    if manifest.get("schema_version") != BUNDLE_SCHEMA_VERSION:
        raise BundleVerificationError("unsupported release bundle schema version")

    source_sha = _validate_source_sha(str(manifest.get("source_sha", "")))
    if expected_source_sha is not None:
        expected = _validate_source_sha(expected_source_sha)
        if source_sha != expected:
            raise BundleVerificationError(
                f"bundle source SHA mismatch: expected {expected}, got {source_sha}"
            )
    if manifest.get("platform") != "windows":
        raise BundleVerificationError("R18.2 bundle platform must be windows")
    if manifest.get("manifest_digest_binding") != "external-sha256":
        raise BundleVerificationError("manifest digest must use the external SHA-256 binding")
    if manifest.get("installer_binary_reproducibility") != "measured-not-assumed":
        raise BundleVerificationError("installer binary reproducibility policy mismatch")
    if manifest.get("archive_profile") != _archive_profile():
        raise BundleVerificationError("deterministic archive profile mismatch")

    expected_identity = _canonical_release_identity(source_sha)
    identity = manifest.get("release_identity")
    if identity != expected_identity:
        raise BundleVerificationError("bundle release identity does not match canonical authority")

    provenance = manifest.get("provenance")
    if not isinstance(provenance, dict):
        raise BundleVerificationError("bundle provenance must be an object")
    required_provenance = {"repository", "workflow_ref", "run_id", "run_attempt"}
    if set(provenance) != required_provenance:
        raise BundleVerificationError("bundle provenance fields are incomplete or unexpected")
    if any(not isinstance(provenance[key], str) or not provenance[key] for key in required_provenance):
        raise BundleVerificationError("bundle provenance fields must be non-empty strings")

    raw_files = manifest.get("files")
    if not isinstance(raw_files, list) or len(raw_files) < 4:
        raise BundleVerificationError("bundle manifest must enumerate at least four payload files")
    records: list[dict[str, Any]] = []
    names: set[str] = set()
    folded: set[str] = set()
    for raw in raw_files:
        if not isinstance(raw, dict) or set(raw) != {"path", "role", "sha256", "size"}:
            raise BundleVerificationError("bundle file record fields are invalid")
        path = _safe_archive_path(str(raw["path"]))
        role = str(raw["role"])
        digest = str(raw["sha256"])
        size = raw["size"]
        if role not in _ALLOWED_ROLES:
            raise BundleVerificationError(f"unsupported bundle role: {role!r}")
        if not _SHA256_RE.fullmatch(digest):
            raise BundleVerificationError(f"invalid SHA-256 for {path!r}")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            raise BundleVerificationError(f"invalid size for {path!r}")
        if path in names:
            raise BundleVerificationError(f"duplicate manifest path: {path!r}")
        folded_name = path.casefold()
        if folded_name in folded:
            raise BundleVerificationError(f"case-insensitive manifest path collision: {path!r}")
        names.add(path)
        folded.add(folded_name)
        records.append(
            {
                "path": path,
                "role": role,
                "sha256": digest,
                "size": size,
            }
        )
    if records != sorted(records, key=lambda record: record["path"]):
        raise BundleVerificationError("bundle manifest file records must be lexicographically ordered")

    release_evidence = manifest.get("release_evidence")
    evidence_records = [
        record for record in records if record["role"] in {"sbom", "provenance"}
    ]
    if release_evidence is None:
        if evidence_records:
            raise BundleVerificationError("release evidence files require release_evidence manifest binding")
    else:
        required_evidence = {
            "sbom_path",
            "sbom_sha256",
            "provenance_path",
            "provenance_sha256",
            "sbom_predicate_type",
            "attestation_semantics",
        }
        if not isinstance(release_evidence, dict) or set(release_evidence) != required_evidence:
            raise BundleVerificationError("release_evidence fields are incomplete or unexpected")
        if (
            release_evidence["sbom_path"] != SBOM_NAME
            or release_evidence["provenance_path"] != PROVENANCE_NAME
        ):
            raise BundleVerificationError("release evidence paths are not canonical")
        if release_evidence["sbom_predicate_type"] != SPDX_PREDICATE_TYPE:
            raise BundleVerificationError("release SBOM predicate type mismatch")
        if release_evidence["attestation_semantics"] != ATTESTATION_SEMANTICS:
            raise BundleVerificationError("release attestation semantics mismatch")
        evidence_by_role = {record["role"]: record for record in evidence_records}
        if set(evidence_by_role) != {"sbom", "provenance"}:
            raise BundleVerificationError(
                "release bundle must contain exactly one SBOM and provenance record"
            )
        if (
            evidence_by_role["sbom"]["path"] != SBOM_NAME
            or evidence_by_role["provenance"]["path"] != PROVENANCE_NAME
        ):
            raise BundleVerificationError("release evidence record paths mismatch")
        if evidence_by_role["sbom"]["sha256"] != release_evidence["sbom_sha256"]:
            raise BundleVerificationError("release SBOM manifest digest binding mismatch")
        if (
            evidence_by_role["provenance"]["sha256"]
            != release_evidence["provenance_sha256"]
        ):
            raise BundleVerificationError("release provenance manifest digest binding mismatch")

    if not _SHA256_RE.fullmatch(str(manifest.get("payload_sha256", ""))):
        raise BundleVerificationError("bundle payload SHA-256 is invalid")
    if not _SHA256_RE.fullmatch(str(manifest.get("semantic_sha256", ""))):
        raise BundleVerificationError("bundle semantic SHA-256 is invalid")
    return source_sha, expected_identity, records


def _mode_from_zip_info(info: zipfile.ZipInfo) -> int:
    return (info.external_attr >> 16) & 0o7777


def _parse_checksums(payload: bytes) -> dict[str, str]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BundleVerificationError("SHA256SUMS.txt must be UTF-8") from exc
    parsed: dict[str, str] = {}
    for line in text.splitlines():
        if not line:
            continue
        digest, separator, path = line.partition("  ")
        if not separator or not _SHA256_RE.fullmatch(digest):
            raise BundleVerificationError(f"invalid checksum line: {line!r}")
        _safe_archive_path(path)
        if path in parsed or path.casefold() in {name.casefold() for name in parsed}:
            raise BundleVerificationError(f"duplicate checksum path: {path!r}")
        parsed[path] = digest
    return parsed


def verify_bundle_archive(
    archive_path: str | Path,
    *,
    expected_source_sha: str | None = None,
) -> dict[str, Any]:
    archive_file = Path(archive_path)
    if not archive_file.is_file():
        raise BundleVerificationError(f"bundle archive does not exist: {archive_file}")

    try:
        archive = zipfile.ZipFile(archive_file, mode="r")
    except (OSError, zipfile.BadZipFile) as exc:
        raise BundleVerificationError(f"unable to open bundle archive: {exc}") from exc

    with archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            raise BundleVerificationError("archive contains duplicate member names")
        if len({name.casefold() for name in names}) != len(names):
            raise BundleVerificationError("archive contains case-insensitive member collisions")
        for info in infos:
            _safe_archive_path(info.filename)
            if info.is_dir():
                raise BundleVerificationError("archive must not contain directory entries")
            unix_mode = (info.external_attr >> 16) & 0o170000
            if unix_mode == stat.S_IFLNK:
                raise BundleVerificationError(f"archive must not contain symlinks: {info.filename!r}")
            if info.date_time != ZIP_TIMESTAMP:
                raise BundleVerificationError(
                    f"archive member timestamp is not deterministic: {info.filename!r}"
                )
            if info.compress_type != zipfile.ZIP_DEFLATED:
                raise BundleVerificationError(
                    f"archive member compression is not DEFLATE: {info.filename!r}"
                )
            if info.create_system != 3:
                raise BundleVerificationError(
                    f"archive member does not use canonical Unix metadata: {info.filename!r}"
                )
        if names != sorted(names):
            raise BundleVerificationError("archive members must be lexicographically ordered")
        if MANIFEST_NAME not in names:
            raise BundleVerificationError("bundle manifest is missing")

        manifest_bytes = archive.read(MANIFEST_NAME)
        manifest = _parse_manifest_bytes(manifest_bytes)
        source_sha, identity, records = _validate_manifest_structure(
            manifest, expected_source_sha
        )
        record_by_path = {record["path"]: record for record in records}
        expected_names = set(record_by_path) | {MANIFEST_NAME}
        if set(names) != expected_names:
            unexpected = sorted(set(names) - expected_names)
            missing = sorted(expected_names - set(names))
            raise BundleVerificationError(
                f"archive contents do not match manifest; unexpected={unexpected}, missing={missing}"
            )

        executable_records = [
            record
            for record in records
            if Path(record["path"]).suffix.lower() in _EXECUTABLE_SUFFIXES
        ]
        if executable_records != [
            record_by_path.get("KodepoiaSetup.exe")
        ] or executable_records[0]["role"] != "installer":
            raise BundleVerificationError(
                "bundle must contain exactly one executable payload: KodepoiaSetup.exe"
            )

        payload_bytes: dict[str, bytes] = {}
        for info in infos:
            if info.filename == MANIFEST_NAME:
                expected_mode = 0o644
            else:
                record = record_by_path[info.filename]
                expected_mode = _mode_for_path(record["path"], record["role"])
            if _mode_from_zip_info(info) != expected_mode:
                raise BundleVerificationError(
                    f"archive member mode mismatch for {info.filename!r}"
                )

        for record in records:
            payload = archive.read(record["path"])
            payload_bytes[record["path"]] = payload
            if len(payload) != record["size"]:
                raise BundleVerificationError(
                    f"payload size mismatch for {record['path']!r}"
                )
            if _sha256_bytes(payload) != record["sha256"]:
                raise BundleVerificationError(
                    f"payload digest mismatch for {record['path']!r}"
                )

        installer_records = [
            record for record in records if record["role"] == "installer"
        ]
        if installer_records != [record_by_path.get("KodepoiaSetup.exe")]:
            raise BundleVerificationError("manifest must contain exactly one installer record")
        if not any(record["role"] == "license" and record["path"] == "LICENSE" for record in records):
            raise BundleVerificationError("bundle must contain the repository LICENSE")
        if not any(record["role"] == "release-notes" for record in records):
            raise BundleVerificationError("bundle must contain release-notes metadata")
        if not any(record["role"] == "checksums" and record["path"] == CHECKSUMS_NAME for record in records):
            raise BundleVerificationError("bundle must contain SHA256SUMS.txt")

        checksums = _parse_checksums(payload_bytes[CHECKSUMS_NAME])
        checksummed_records = {
            record["path"]: record["sha256"]
            for record in records
            if record["path"] != CHECKSUMS_NAME
        }
        if checksums != checksummed_records:
            raise BundleVerificationError("SHA256SUMS.txt does not exactly bind non-checksum payloads")

        release_evidence = manifest.get("release_evidence")
        if release_evidence is not None:
            try:
                verified_evidence = verify_release_evidence_payloads(
                    payload_bytes[SBOM_NAME],
                    payload_bytes[PROVENANCE_NAME],
                    expected_source_sha=source_sha,
                    expected_repository=manifest["provenance"]["repository"],
                )
            except (KeyError, ReleaseEvidenceError) as exc:
                raise BundleVerificationError(
                    f"release evidence payload verification failed: {exc}"
                ) from exc
            if verified_evidence["sbom_sha256"] != release_evidence["sbom_sha256"]:
                raise BundleVerificationError("release SBOM payload digest mismatch")
            if (
                verified_evidence["provenance_sha256"]
                != release_evidence["provenance_sha256"]
            ):
                raise BundleVerificationError("release provenance payload digest mismatch")

        try:
            release_notes = json.loads(payload_bytes[RELEASE_NOTES_NAME].decode("utf-8"))
        except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BundleVerificationError("release-notes metadata is invalid") from exc
        if not isinstance(release_notes, dict):
            raise BundleVerificationError("release-notes metadata root must be an object")
        if release_notes.get("source_sha") != source_sha:
            raise BundleVerificationError("release-notes source SHA mismatch")
        if release_notes.get("production_signed") is not False:
            raise BundleVerificationError("R18.2 release notes must remain unsigned")
        if release_notes.get("github_release_published") is not False:
            raise BundleVerificationError("R18.2 must not claim GitHub Release publication")
        if release_notes.get("winget_published") is not False:
            raise BundleVerificationError("R18.2 must not claim WinGet publication")

        payload_digest = _payload_digest(identity, records)
        if payload_digest != manifest["payload_sha256"]:
            raise BundleVerificationError("bundle payload digest mismatch")
        semantic_digest = _semantic_digest(identity, records)
        if semantic_digest != manifest["semantic_sha256"]:
            raise BundleVerificationError("bundle semantic digest mismatch")

    return {
        "archive_path": str(archive_file),
        "archive_sha256": _sha256_file(archive_file),
        "archive_size": archive_file.stat().st_size,
        "manifest_sha256": _sha256_bytes(manifest_bytes),
        "source_sha": source_sha,
        "manifest": manifest,
    }


def read_bundle_manifest(
    archive_path: str | Path,
    *,
    expected_source_sha: str | None = None,
) -> dict[str, Any]:
    return verify_bundle_archive(
        archive_path,
        expected_source_sha=expected_source_sha,
    )["manifest"]


def compare_release_bundles(
    first: str | Path,
    second: str | Path,
    *,
    expected_source_sha: str,
) -> dict[str, Any]:
    first_result = verify_bundle_archive(first, expected_source_sha=expected_source_sha)
    second_result = verify_bundle_archive(second, expected_source_sha=expected_source_sha)
    first_manifest = first_result["manifest"]
    second_manifest = second_result["manifest"]

    def installer_digest(manifest: Mapping[str, Any]) -> str:
        installer_records = [
            record for record in manifest["files"] if record["role"] == "installer"
        ]
        if len(installer_records) != 1:
            raise BundleVerificationError("comparison requires exactly one installer record")
        return installer_records[0]["sha256"]

    return {
        "source_sha": _validate_source_sha(expected_source_sha),
        "semantic_equivalent": (
            first_manifest["semantic_sha256"] == second_manifest["semantic_sha256"]
        ),
        "payload_equal": (
            first_manifest["payload_sha256"] == second_manifest["payload_sha256"]
        ),
        "installer_binary_equal": (
            installer_digest(first_manifest) == installer_digest(second_manifest)
        ),
        "archive_binary_equal": (
            first_result["archive_sha256"] == second_result["archive_sha256"]
        ),
        "manifest_binary_equal": (
            first_result["manifest_sha256"] == second_result["manifest_sha256"]
        ),
        "first": {
            "archive_sha256": first_result["archive_sha256"],
            "archive_size": first_result["archive_size"],
            "manifest_sha256": first_result["manifest_sha256"],
            "payload_sha256": first_manifest["payload_sha256"],
            "semantic_sha256": first_manifest["semantic_sha256"],
            "installer_sha256": installer_digest(first_manifest),
        },
        "second": {
            "archive_sha256": second_result["archive_sha256"],
            "archive_size": second_result["archive_size"],
            "manifest_sha256": second_result["manifest_sha256"],
            "payload_sha256": second_manifest["payload_sha256"],
            "semantic_sha256": second_manifest["semantic_sha256"],
            "installer_sha256": installer_digest(second_manifest),
        },
    }
