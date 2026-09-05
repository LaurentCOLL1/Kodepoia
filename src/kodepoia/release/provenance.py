from __future__ import annotations

import hashlib
import importlib.metadata as metadata
import json
import os
import re
import tomllib
from collections import deque
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SPDX_VERSION = "SPDX-2.3"
SPDX_DATA_LICENSE = "CC0-1.0"
SPDX_PREDICATE_TYPE = "https://spdx.dev/Document/v2.3"
SBOM_NAME = "release-sbom.spdx.json"
PROVENANCE_NAME = "release-provenance.json"
PROVENANCE_FORMAT = "kodepoia-release-provenance"
PROVENANCE_SCHEMA_VERSION = 1
ATTESTATION_PROVIDER = "github-artifact-attestations"
ATTESTATION_SEMANTICS = "provenance_only_not_security_verdict"

_SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REQUIREMENT_NAME_RE = re.compile(r"^\s*([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)")


class ReleaseEvidenceError(ValueError):
    """Raised when release SBOM/provenance evidence is invalid."""


@dataclass(frozen=True, slots=True)
class ReleaseEvidenceResult:
    sbom_path: Path
    sbom_sha256: str
    provenance_path: Path
    provenance_sha256: str
    packages_total: int
    runtime_roots: tuple[str, ...]
    unresolved_roots: tuple[str, ...]


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


def _require_source_sha(value: str) -> str:
    normalized = value.strip().lower()
    if not _SHA40_RE.fullmatch(normalized):
        raise ReleaseEvidenceError("source SHA must be a 40-character hexadecimal Git commit")
    return normalized


def _canonical_name(value: str) -> str:
    normalized = re.sub(r"[-_.]+", "-", value.strip()).lower()
    if not normalized or not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", normalized):
        raise ReleaseEvidenceError(f"invalid Python distribution name: {value!r}")
    return normalized


def _requirement_name(value: str) -> str | None:
    match = _REQUIREMENT_NAME_RE.match(value)
    return _canonical_name(match.group(1)) if match else None


def _spdx_id(name: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9.-]+", "-", name).strip("-.") or "package"
    return f"SPDXRef-Package-{safe}"


def _created_at(value: str | None) -> str:
    if value:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        epoch = os.getenv("SOURCE_DATE_EPOCH")
        if epoch:
            parsed = datetime.fromtimestamp(int(epoch), tz=UTC)
        else:
            parsed = datetime(1980, 1, 1, tzinfo=UTC)
    if parsed.tzinfo is None:
        raise ReleaseEvidenceError("SBOM creation time must include a timezone")
    return parsed.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _project_metadata(
    repo_root: Path,
    optional_groups: Sequence[str],
) -> tuple[str, str, tuple[str, ...]]:
    pyproject = repo_root / "pyproject.toml"
    payload = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    project = dict(payload.get("project") or {})
    name = _canonical_name(str(project.get("name", "")))
    version = str(project.get("version", "")).strip()
    if not version:
        raise ReleaseEvidenceError("pyproject project.version is required")

    requirements = [str(value) for value in project.get("dependencies", [])]
    optional = dict(project.get("optional-dependencies") or {})
    for group in optional_groups:
        if group not in optional:
            raise ReleaseEvidenceError(f"unknown optional dependency group: {group}")
        requirements.extend(str(value) for value in optional[group])
    roots = tuple(
        sorted(
            {
                name_value
                for requirement in requirements
                if (name_value := _requirement_name(requirement)) is not None
            }
        )
    )
    return name, version, roots


def _distribution(name: str) -> metadata.Distribution | None:
    try:
        return metadata.distribution(name)
    except metadata.PackageNotFoundError:
        return None


def _runtime_inventory(
    project_name: str,
    project_version: str,
    roots: Sequence[str],
) -> tuple[list[dict[str, Any]], list[dict[str, str]], tuple[str, ...]]:
    packages: dict[str, dict[str, Any]] = {
        project_name: {
            "name": project_name,
            "version": project_version,
            "license": "NOASSERTION",
            "dependencies": tuple(roots),
            "resolved": True,
        }
    }
    unresolved_roots: set[str] = set()
    queue: deque[str] = deque(roots)
    visited: set[str] = set()

    while queue:
        requested = queue.popleft()
        canonical = _canonical_name(requested)
        if canonical in visited:
            continue
        visited.add(canonical)
        dist = _distribution(canonical)
        if dist is None:
            if canonical in roots:
                unresolved_roots.add(canonical)
            packages[canonical] = {
                "name": canonical,
                "version": "",
                "license": "NOASSERTION",
                "dependencies": (),
                "resolved": False,
            }
            continue

        metadata_name = _canonical_name(str(dist.metadata.get("Name") or canonical))
        requirements: set[str] = set()
        for requirement in dist.requires or ():
            dep_name = _requirement_name(requirement)
            if dep_name is None:
                continue
            if _distribution(dep_name) is None:
                continue
            requirements.add(dep_name)
            if dep_name not in visited:
                queue.append(dep_name)
        license_expression = str(dist.metadata.get("License-Expression") or "").strip()
        packages[metadata_name] = {
            "name": metadata_name,
            "version": str(dist.version),
            "license": license_expression or "NOASSERTION",
            "dependencies": tuple(sorted(requirements)),
            "resolved": True,
        }

    spdx_packages: list[dict[str, Any]] = []
    relationships: list[dict[str, str]] = []
    for name in sorted(packages):
        item = packages[name]
        package: dict[str, Any] = {
            "SPDXID": _spdx_id(name),
            "name": name,
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": False,
            "licenseConcluded": "NOASSERTION",
            "licenseDeclared": item["license"],
            "copyrightText": "NOASSERTION",
            "comment": (
                "Resolved from installed Python distribution metadata."
                if item["resolved"]
                else "Declared runtime dependency was not resolved in this build environment."
            ),
        }
        if item["version"]:
            package["versionInfo"] = item["version"]
            package["externalRefs"] = [
                {
                    "referenceCategory": "PACKAGE-MANAGER",
                    "referenceType": "purl",
                    "referenceLocator": f"pkg:pypi/{name}@{item['version']}",
                }
            ]
        spdx_packages.append(package)
        for dependency in item["dependencies"]:
            if dependency not in packages:
                continue
            relationships.append(
                {
                    "spdxElementId": _spdx_id(name),
                    "relationshipType": "DEPENDS_ON",
                    "relatedSpdxElement": _spdx_id(dependency),
                }
            )

    relationships.append(
        {
            "spdxElementId": "SPDXRef-DOCUMENT",
            "relationshipType": "DESCRIBES",
            "relatedSpdxElement": _spdx_id(project_name),
        }
    )
    relationships.sort(
        key=lambda item: (
            item["spdxElementId"],
            item["relationshipType"],
            item["relatedSpdxElement"],
        )
    )
    return spdx_packages, relationships, tuple(sorted(unresolved_roots))


def build_spdx_sbom(
    *,
    repo_root: str | Path,
    source_sha: str,
    repository: str,
    optional_groups: Sequence[str] = ("ui", "code"),
    created_at: str | None = None,
) -> dict[str, Any]:
    root = Path(repo_root)
    source = _require_source_sha(source_sha)
    project_name, project_version, roots = _project_metadata(root, optional_groups)
    packages, relationships, unresolved_roots = _runtime_inventory(
        project_name,
        project_version,
        roots,
    )
    return {
        "spdxVersion": SPDX_VERSION,
        "dataLicense": SPDX_DATA_LICENSE,
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"Kodepoia-{project_version}-release-sbom",
        "documentNamespace": f"https://github.com/{repository}/attestations/spdx/{source}",
        "creationInfo": {
            "created": _created_at(created_at),
            "creators": ["Tool: Kodepoia R18.3 release SBOM generator"],
        },
        "documentDescribes": [_spdx_id(project_name)],
        "packages": packages,
        "relationships": relationships,
        "documentComment": (
            "Release-runtime Python inventory derived from declared project dependencies and the ui/code "
            "runtime groups, recursively resolved against installed distribution metadata. Native/runtime "
            "members embedded by Nuitka/Inno are not recursively exploded here; this document therefore "
            "does not claim a complete native-file inventory. Unresolved declared roots are retained with "
            f"NOASSERTION semantics: {', '.join(unresolved_roots) if unresolved_roots else 'none'}."
        ),
    }


def validate_spdx_sbom(
    payload: Mapping[str, Any],
    *,
    expected_source_sha: str,
    expected_repository: str,
) -> dict[str, Any]:
    source = _require_source_sha(expected_source_sha)
    if payload.get("spdxVersion") != SPDX_VERSION:
        raise ReleaseEvidenceError("release SBOM must use SPDX-2.3")
    if payload.get("dataLicense") != SPDX_DATA_LICENSE:
        raise ReleaseEvidenceError("release SBOM must use SPDX data license CC0-1.0")
    if payload.get("SPDXID") != "SPDXRef-DOCUMENT":
        raise ReleaseEvidenceError("release SBOM document SPDXID mismatch")
    expected_namespace = f"https://github.com/{expected_repository}/attestations/spdx/{source}"
    if payload.get("documentNamespace") != expected_namespace:
        raise ReleaseEvidenceError("release SBOM namespace does not bind exact repository/source")
    packages = payload.get("packages")
    if not isinstance(packages, list) or not packages:
        raise ReleaseEvidenceError("release SBOM must enumerate packages")
    ids: set[str] = set()
    unresolved = 0
    for package in packages:
        if not isinstance(package, dict):
            raise ReleaseEvidenceError("release SBOM package record must be an object")
        spdx_id = str(package.get("SPDXID", ""))
        if not spdx_id.startswith("SPDXRef-Package-") or spdx_id in ids:
            raise ReleaseEvidenceError("release SBOM package SPDXIDs must be unique")
        ids.add(spdx_id)
        if package.get("filesAnalyzed") is not False:
            raise ReleaseEvidenceError("release SBOM package file analysis must remain explicitly false")
        if not package.get("versionInfo"):
            unresolved += 1
    describes = payload.get("documentDescribes")
    if not isinstance(describes, list) or len(describes) != 1 or describes[0] not in ids:
        raise ReleaseEvidenceError("release SBOM must describe exactly the Kodepoia package")
    return {
        "packages_total": len(packages),
        "packages_unresolved": unresolved,
        "predicate_type": SPDX_PREDICATE_TYPE,
        "inventory_complete": False,
    }


def build_release_provenance(
    *,
    source_sha: str,
    repository: str,
    workflow_ref: str,
    run_id: str,
    run_attempt: str,
    sbom_sha256: str,
    runtime_roots: Sequence[str],
    unresolved_roots: Sequence[str],
) -> dict[str, Any]:
    source = _require_source_sha(source_sha)
    sbom_digest = sbom_sha256.strip().lower()
    if not _SHA256_RE.fullmatch(sbom_digest):
        raise ReleaseEvidenceError("SBOM digest must be a lowercase SHA-256")
    required_strings = {
        "repository": repository,
        "workflow_ref": workflow_ref,
        "run_id": run_id,
        "run_attempt": run_attempt,
    }
    if any(not value.strip() for value in required_strings.values()):
        raise ReleaseEvidenceError("release provenance workflow fields must be non-empty")
    return {
        "format": PROVENANCE_FORMAT,
        "schema_version": PROVENANCE_SCHEMA_VERSION,
        "source_sha": source,
        **required_strings,
        "sbom": {
            "path": SBOM_NAME,
            "sha256": sbom_digest,
            "predicate_type": SPDX_PREDICATE_TYPE,
        },
        "inventory": {
            "scope": "release-runtime-python-plus-release-bundle-files",
            "complete": False,
            "runtime_roots": sorted({_canonical_name(value) for value in runtime_roots}),
            "unresolved_roots": sorted({_canonical_name(value) for value in unresolved_roots}),
            "native_embedded_inventory": "not-recursively-enumerated",
        },
        "external_attestation": {
            "provider": ATTESTATION_PROVIDER,
            "expected": True,
            "semantics": ATTESTATION_SEMANTICS,
        },
        "production_signed": False,
        "github_release_published": False,
        "winget_published": False,
    }


def validate_release_provenance(
    payload: Mapping[str, Any],
    *,
    expected_source_sha: str,
    expected_repository: str,
    expected_sbom_sha256: str,
) -> dict[str, Any]:
    source = _require_source_sha(expected_source_sha)
    if payload.get("format") != PROVENANCE_FORMAT:
        raise ReleaseEvidenceError("release provenance format mismatch")
    if payload.get("schema_version") != PROVENANCE_SCHEMA_VERSION:
        raise ReleaseEvidenceError("release provenance schema version mismatch")
    if payload.get("source_sha") != source:
        raise ReleaseEvidenceError("release provenance source SHA mismatch")
    if payload.get("repository") != expected_repository:
        raise ReleaseEvidenceError("release provenance repository mismatch")
    sbom = payload.get("sbom")
    if not isinstance(sbom, dict):
        raise ReleaseEvidenceError("release provenance SBOM binding is missing")
    if sbom.get("path") != SBOM_NAME or sbom.get("predicate_type") != SPDX_PREDICATE_TYPE:
        raise ReleaseEvidenceError("release provenance SBOM predicate/path mismatch")
    if sbom.get("sha256") != expected_sbom_sha256:
        raise ReleaseEvidenceError("release provenance SBOM digest mismatch")
    attestation = payload.get("external_attestation")
    if not isinstance(attestation, dict):
        raise ReleaseEvidenceError("release provenance attestation policy is missing")
    if attestation.get("provider") != ATTESTATION_PROVIDER:
        raise ReleaseEvidenceError("release provenance attestation provider mismatch")
    if attestation.get("expected") is not True:
        raise ReleaseEvidenceError("release provenance must require external artifact attestation")
    if attestation.get("semantics") != ATTESTATION_SEMANTICS:
        raise ReleaseEvidenceError("attestation semantics must remain provenance-only")
    inventory = payload.get("inventory")
    if not isinstance(inventory, dict) or inventory.get("complete") is not False:
        raise ReleaseEvidenceError("release provenance must not claim complete inventory")
    if payload.get("production_signed") is not False:
        raise ReleaseEvidenceError("R18.3 must not claim production signing")
    if payload.get("github_release_published") is not False:
        raise ReleaseEvidenceError("R18.3 must not claim GitHub Release publication")
    if payload.get("winget_published") is not False:
        raise ReleaseEvidenceError("R18.3 must not claim WinGet publication")
    return {
        "attestation_provider": ATTESTATION_PROVIDER,
        "attestation_semantics": ATTESTATION_SEMANTICS,
        "inventory_complete": False,
    }


def verify_release_evidence_payloads(
    sbom_bytes: bytes,
    provenance_bytes: bytes,
    *,
    expected_source_sha: str,
    expected_repository: str,
) -> dict[str, Any]:
    try:
        sbom = json.loads(sbom_bytes.decode("utf-8"))
        provenance = json.loads(provenance_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReleaseEvidenceError(f"release evidence JSON is invalid: {exc}") from exc
    if not isinstance(sbom, dict) or not isinstance(provenance, dict):
        raise ReleaseEvidenceError("release evidence roots must be JSON objects")
    sbom_sha256 = _sha256_bytes(sbom_bytes)
    sbom_summary = validate_spdx_sbom(
        sbom,
        expected_source_sha=expected_source_sha,
        expected_repository=expected_repository,
    )
    provenance_summary = validate_release_provenance(
        provenance,
        expected_source_sha=expected_source_sha,
        expected_repository=expected_repository,
        expected_sbom_sha256=sbom_sha256,
    )
    return {
        "sbom_sha256": sbom_sha256,
        "provenance_sha256": _sha256_bytes(provenance_bytes),
        "sbom": sbom_summary,
        "provenance": provenance_summary,
    }


def verify_release_evidence_files(
    sbom_path: str | Path,
    provenance_path: str | Path,
    *,
    expected_source_sha: str,
    expected_repository: str,
) -> dict[str, Any]:
    return verify_release_evidence_payloads(
        Path(sbom_path).read_bytes(),
        Path(provenance_path).read_bytes(),
        expected_source_sha=expected_source_sha,
        expected_repository=expected_repository,
    )


def write_release_evidence(
    *,
    repo_root: str | Path,
    output_dir: str | Path,
    source_sha: str,
    repository: str,
    workflow_ref: str,
    run_id: str,
    run_attempt: str,
    optional_groups: Sequence[str] = ("ui", "code"),
    created_at: str | None = None,
) -> ReleaseEvidenceResult:
    root = Path(repo_root)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    project_name, _project_version, roots = _project_metadata(root, optional_groups)
    sbom = build_spdx_sbom(
        repo_root=root,
        source_sha=source_sha,
        repository=repository,
        optional_groups=optional_groups,
        created_at=created_at,
    )
    sbom_bytes = _canonical_json_bytes(sbom)
    sbom_path = output / SBOM_NAME
    sbom_path.write_bytes(sbom_bytes)
    unresolved = tuple(
        sorted(
            package["name"]
            for package in sbom["packages"]
            if package["SPDXID"] != _spdx_id(project_name) and not package.get("versionInfo")
        )
    )
    provenance = build_release_provenance(
        source_sha=source_sha,
        repository=repository,
        workflow_ref=workflow_ref,
        run_id=run_id,
        run_attempt=run_attempt,
        sbom_sha256=_sha256_bytes(sbom_bytes),
        runtime_roots=roots,
        unresolved_roots=unresolved,
    )
    provenance_bytes = _canonical_json_bytes(provenance)
    provenance_path = output / PROVENANCE_NAME
    provenance_path.write_bytes(provenance_bytes)
    summary = verify_release_evidence_payloads(
        sbom_bytes,
        provenance_bytes,
        expected_source_sha=source_sha,
        expected_repository=repository,
    )
    return ReleaseEvidenceResult(
        sbom_path=sbom_path,
        sbom_sha256=summary["sbom_sha256"],
        provenance_path=provenance_path,
        provenance_sha256=summary["provenance_sha256"],
        packages_total=summary["sbom"]["packages_total"],
        runtime_roots=roots,
        unresolved_roots=unresolved,
    )
