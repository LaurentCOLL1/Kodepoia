from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

PROMOTION_FORMAT = "kodepoia-github-release-promotion"
PROMOTION_SCHEMA_VERSION = 1
ATTESTATION_PROVIDER = "github-artifact-attestations"
ATTESTATION_SEMANTICS = "provenance_only_not_security_verdict"
DEFAULT_REPOSITORY = "LaurentCOLL1/Kodepoia"

_SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_TAG_RE = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+(?:-(?:a|b|rc)[1-9][0-9]*)?$")
_ALLOWED_SIGNING_MODES = {"unsigned", "test", "production"}
_ALLOWED_ATTESTATION_MODES = {"github-cli", "synthetic-offline"}


class ReleasePromotionError(ValueError):
    """Raised when an R18.5 release staging or promotion contract is violated."""


class PromotionState(StrEnum):
    DRAFT = "draft"
    STAGED = "staged"
    PUBLISHED = "published"


@dataclass(frozen=True, slots=True)
class ReleaseAsset:
    name: str
    sha256: str
    size: int

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "sha256": self.sha256, "size": self.size}


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


def _require_source_sha(value: str) -> str:
    normalized = value.strip().lower()
    if not _SOURCE_SHA_RE.fullmatch(normalized):
        raise ReleasePromotionError(
            "source SHA must be an exact 40-character hexadecimal Git commit"
        )
    return normalized


def _require_sha256(value: object, *, label: str) -> str:
    normalized = str(value).strip().lower()
    if not _SHA256_RE.fullmatch(normalized):
        raise ReleasePromotionError(f"{label} must be a lowercase SHA-256 digest")
    return normalized


def _require_non_empty(value: object, *, label: str) -> str:
    text = str(value).strip()
    if not text:
        raise ReleasePromotionError(f"{label} must be a non-empty string")
    return text


def _expected_tag(identity: Mapping[str, Any]) -> str:
    public_version = _require_non_empty(
        identity.get("public_version"), label="release public version"
    )
    tag = f"v{public_version}"
    if not _TAG_RE.fullmatch(tag):
        raise ReleasePromotionError(f"canonical release tag is invalid: {tag!r}")
    return tag


def _validated_identity(
    manifest: Mapping[str, Any],
    *,
    source_sha: str,
) -> dict[str, Any]:
    identity = manifest.get("release_identity")
    if not isinstance(identity, Mapping):
        raise ReleasePromotionError("bundle manifest release_identity is missing")
    if identity.get("source_sha") != source_sha:
        raise ReleasePromotionError("bundle release identity source SHA mismatch")
    if identity.get("source_binding") != "exact-head":
        raise ReleasePromotionError("release identity must remain exact-head bound")
    channel = identity.get("channel")
    build_type = identity.get("build_type")
    allowed_pairs = {
        ("stable", "release"),
        ("beta", "prerelease"),
        ("nightly", "development"),
    }
    if (channel, build_type) not in allowed_pairs:
        raise ReleasePromotionError("release channel/build_type pairing is invalid")
    return dict(identity)


def _validated_bundle(
    verified_bundle: Mapping[str, Any],
    *,
    source_sha: str,
    repository: str,
) -> tuple[dict[str, Any], dict[str, Any], ReleaseAsset]:
    if verified_bundle.get("source_sha") != source_sha:
        raise ReleasePromotionError("verified bundle source SHA mismatch")
    manifest = verified_bundle.get("manifest")
    if not isinstance(manifest, Mapping):
        raise ReleasePromotionError("verified bundle manifest is missing")
    if manifest.get("source_sha") != source_sha:
        raise ReleasePromotionError("bundle manifest source SHA mismatch")
    if manifest.get("format") != "kodepoia-release-bundle":
        raise ReleasePromotionError("unsupported release bundle format")
    if manifest.get("schema_version") != 1:
        raise ReleasePromotionError("unsupported release bundle schema version")
    provenance = manifest.get("provenance")
    if not isinstance(provenance, Mapping):
        raise ReleasePromotionError("bundle provenance is missing")
    if provenance.get("repository") != repository:
        raise ReleasePromotionError("bundle repository provenance mismatch")
    evidence = manifest.get("release_evidence")
    if not isinstance(evidence, Mapping):
        raise ReleasePromotionError(
            "R18.5 staging requires R18.3 SBOM/provenance evidence in the bundle"
        )
    if evidence.get("attestation_semantics") != ATTESTATION_SEMANTICS:
        raise ReleasePromotionError("bundle attestation semantics mismatch")
    identity = _validated_identity(manifest, source_sha=source_sha)

    archive_path = _require_non_empty(
        verified_bundle.get("archive_path"), label="verified bundle archive path"
    )
    archive_name = Path(archive_path).name
    archive_digest = _require_sha256(
        verified_bundle.get("archive_sha256"), label="verified bundle archive digest"
    )
    archive_size = verified_bundle.get("archive_size")
    if not isinstance(archive_size, int) or isinstance(archive_size, bool) or archive_size <= 0:
        raise ReleasePromotionError("verified bundle archive size must be a positive integer")

    manifest_digest = _require_sha256(
        verified_bundle.get("manifest_sha256"), label="bundle manifest digest"
    )
    if not _SHA256_RE.fullmatch(str(manifest.get("payload_sha256", ""))):
        raise ReleasePromotionError("bundle payload digest is invalid")
    if not _SHA256_RE.fullmatch(str(manifest.get("semantic_sha256", ""))):
        raise ReleasePromotionError("bundle semantic digest is invalid")
    bundle_summary = {
        "manifest_sha256": manifest_digest,
        "payload_sha256": str(manifest["payload_sha256"]),
        "semantic_sha256": str(manifest["semantic_sha256"]),
        "release_evidence": dict(evidence),
    }
    return identity, bundle_summary, ReleaseAsset(archive_name, archive_digest, archive_size)


def _validated_signing_evidence(
    evidence: Mapping[str, Any],
    *,
    source_sha: str,
) -> dict[str, Any]:
    if evidence.get("schema_version") != 1:
        raise ReleasePromotionError("unsupported R18.4 signing evidence schema")
    if evidence.get("source_sha") != source_sha:
        raise ReleasePromotionError("signing evidence source SHA mismatch")
    mode = str(evidence.get("mode", ""))
    if mode not in _ALLOWED_SIGNING_MODES:
        raise ReleasePromotionError("signing evidence mode is invalid")
    production_signed = evidence.get("production_signed")
    public_trust_claim = evidence.get("public_trust_claim")
    if not isinstance(production_signed, bool) or not isinstance(public_trust_claim, bool):
        raise ReleasePromotionError("signing truth flags must be booleans")
    expected_production = mode == "production"
    if production_signed is not expected_production:
        raise ReleasePromotionError("signing mode contradicts production_signed")
    if public_trust_claim is not expected_production:
        raise ReleasePromotionError("signing mode contradicts public_trust_claim")

    subjects = evidence.get("subjects")
    if not isinstance(subjects, Sequence) or isinstance(subjects, (str, bytes)) or not subjects:
        raise ReleasePromotionError("signing evidence requires subject records")
    installer_seen = False
    for subject in subjects:
        if not isinstance(subject, Mapping):
            raise ReleasePromotionError("signing subject record is invalid")
        filename = str(subject.get("filename", ""))
        _require_sha256(subject.get("sha256"), label=f"signing digest for {filename or 'subject'}")
        if (
            filename == "KodepoiaSetup.exe"
            or filename.endswith("/KodepoiaSetup.exe")
            or filename.endswith("\\KodepoiaSetup.exe")
        ):
            installer_seen = True
        if mode == "unsigned":
            if str(subject.get("authenticode_status", "")).lower() != "notsigned":
                raise ReleasePromotionError("unsigned signing evidence contains a signed subject")
        else:
            if str(subject.get("authenticode_status", "")).lower() != "valid":
                raise ReleasePromotionError("signed subject Authenticode status is not Valid")
            if subject.get("signtool_verified") is not True:
                raise ReleasePromotionError("signed subject lacks SignTool verification")
            if subject.get("timestamp_verified") is not True:
                raise ReleasePromotionError("signed subject lacks RFC3161 timestamp verification")
    if not installer_seen:
        raise ReleasePromotionError("signing evidence does not bind KodepoiaSetup.exe")

    return {
        "mode": mode,
        "production_signed": production_signed,
        "public_trust_claim": public_trust_claim,
        "hash_algorithm": str(evidence.get("hash_algorithm", "")),
        "timestamp_protocol": str(evidence.get("timestamp_protocol", "")),
        "subjects_total": len(subjects),
    }


def _validated_attestation_receipt(
    receipt: Mapping[str, Any],
    *,
    source_sha: str,
    repository: str,
    asset: ReleaseAsset,
) -> dict[str, Any]:
    if receipt.get("schema_version") != 1:
        raise ReleasePromotionError("unsupported attestation verification receipt schema")
    if receipt.get("provider") != ATTESTATION_PROVIDER:
        raise ReleasePromotionError("attestation provider mismatch")
    if receipt.get("semantics") != ATTESTATION_SEMANTICS:
        raise ReleasePromotionError("attestation semantics must remain provenance-only")
    if receipt.get("repository") != repository:
        raise ReleasePromotionError("attestation repository mismatch")
    if receipt.get("source_sha") != source_sha:
        raise ReleasePromotionError("attestation source SHA mismatch")
    if receipt.get("verified") is not True:
        raise ReleasePromotionError("required release artifact attestation is not verified")
    mode = str(receipt.get("verification_mode", ""))
    if mode not in _ALLOWED_ATTESTATION_MODES:
        raise ReleasePromotionError("attestation verification mode is invalid")
    subjects = receipt.get("subjects")
    if not isinstance(subjects, Sequence) or isinstance(subjects, (str, bytes)):
        raise ReleasePromotionError("attestation receipt subjects are invalid")
    canonical = [asset.to_dict()]
    normalized: list[dict[str, Any]] = []
    for subject in subjects:
        if not isinstance(subject, Mapping):
            raise ReleasePromotionError("attestation subject record is invalid")
        name = _require_non_empty(subject.get("name"), label="attestation subject name")
        digest = _require_sha256(
            subject.get("sha256"), label=f"attestation digest for {name}"
        )
        size = subject.get("size")
        if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
            raise ReleasePromotionError("attestation subject size must be a positive integer")
        normalized.append({"name": name, "sha256": digest, "size": size})
    if normalized != canonical:
        raise ReleasePromotionError(
            "attestation receipt must bind exactly the manifest-approved release archive"
        )
    return {
        "provider": ATTESTATION_PROVIDER,
        "semantics": ATTESTATION_SEMANTICS,
        "verification_mode": mode,
        "verified": True,
        "live_verified": mode == "github-cli",
    }


def _validated_tag_state(
    tag_state: Mapping[str, Any],
    *,
    expected_tag: str,
) -> dict[str, Any]:
    observed_tag = str(tag_state.get("tag", expected_tag))
    if observed_tag != expected_tag:
        raise ReleasePromotionError("tag-state snapshot does not describe the canonical tag")
    tag_exists = tag_state.get("tag_exists")
    release_exists = tag_state.get("release_exists")
    if not isinstance(tag_exists, bool) or not isinstance(release_exists, bool):
        raise ReleasePromotionError("tag-state existence flags must be booleans")
    if tag_exists or release_exists:
        raise ReleasePromotionError(
            "mutable tag/release reuse is forbidden; use published-release verification instead"
        )
    return {
        "tag": expected_tag,
        "tag_exists": False,
        "release_exists": False,
        "immutable_release_capability": str(
            tag_state.get("immutable_release_capability", "unknown")
        ),
    }


def _stage_digest(payload: Mapping[str, Any]) -> str:
    material = dict(payload)
    material.pop("stage_digest", None)
    return _sha256_bytes(_canonical_json_bytes(material))


def stage_verified_release(
    *,
    verified_bundle: Mapping[str, Any],
    source_sha: str,
    repository: str,
    signing_evidence: Mapping[str, Any],
    attestation_receipt: Mapping[str, Any],
    tag_state: Mapping[str, Any],
) -> dict[str, Any]:
    source = _require_source_sha(source_sha)
    repo = _require_non_empty(repository, label="repository")
    identity, bundle, asset = _validated_bundle(
        verified_bundle, source_sha=source, repository=repo
    )
    signing = _validated_signing_evidence(signing_evidence, source_sha=source)
    attestation = _validated_attestation_receipt(
        attestation_receipt,
        source_sha=source,
        repository=repo,
        asset=asset,
    )
    tag = _expected_tag(identity)
    tag_snapshot = _validated_tag_state(tag_state, expected_tag=tag)

    channel = str(identity["channel"])
    build_type = str(identity["build_type"])
    prerelease = build_type != "release"
    make_latest = channel == "stable" and not prerelease

    staged: dict[str, Any] = {
        "format": PROMOTION_FORMAT,
        "schema_version": PROMOTION_SCHEMA_VERSION,
        "state": PromotionState.STAGED.value,
        "repository": repo,
        "source_sha": source,
        "tag": tag,
        "release_name": f"{identity['product']} {identity['public_version']}",
        "release_identity": identity,
        "bundle": bundle,
        "assets": [asset.to_dict()],
        "signing": signing,
        "attestation": attestation,
        "tag_state": tag_snapshot,
        "github_release": {
            "draft": True,
            "prerelease": prerelease,
            "make_latest": make_latest,
            "generate_release_notes": False,
            "target_commitish": source,
            "publication_triggered": False,
            "release_id": None,
            "immutable_verified": False,
        },
        "effect_boundary": {
            "public_publish_requires_explicit_authorization": True,
            "approved_stage_digest_required": True,
            "repository_immutability_setting_not_assumed": True,
        },
    }
    staged["stage_digest"] = _stage_digest(staged)
    return staged


def stage_release_archive(
    *,
    archive_path: str | Path,
    source_sha: str,
    repository: str = DEFAULT_REPOSITORY,
    signing_evidence: Mapping[str, Any],
    attestation_receipt: Mapping[str, Any],
    tag_state: Mapping[str, Any],
) -> dict[str, Any]:
    source = _require_source_sha(source_sha)
    archive = Path(archive_path)
    if not archive.is_file():
        raise ReleasePromotionError(f"release archive does not exist: {archive}")
    from kodepoia.release.bundle import verify_bundle_archive

    verified = verify_bundle_archive(archive, expected_source_sha=source)
    if verified["archive_sha256"] != _sha256_file(archive):
        raise ReleasePromotionError("release archive changed after bundle verification")
    return stage_verified_release(
        verified_bundle=verified,
        source_sha=source,
        repository=repository,
        signing_evidence=signing_evidence,
        attestation_receipt=attestation_receipt,
        tag_state=tag_state,
    )


def build_publish_request(
    staged: Mapping[str, Any],
    *,
    approved_stage_digest: str,
) -> dict[str, Any]:
    if staged.get("format") != PROMOTION_FORMAT or staged.get("schema_version") != 1:
        raise ReleasePromotionError("unsupported staged release document")
    if staged.get("state") != PromotionState.STAGED.value:
        raise ReleasePromotionError("only a staged release can produce a publish request")
    actual = _stage_digest(staged)
    recorded = _require_sha256(staged.get("stage_digest"), label="recorded stage digest")
    approved = _require_sha256(approved_stage_digest, label="approved stage digest")
    if recorded != actual:
        raise ReleasePromotionError("staged release digest binding is invalid")
    if approved != recorded:
        raise ReleasePromotionError("publication approval does not match exact staged candidate")

    github_release = staged.get("github_release")
    if not isinstance(github_release, Mapping):
        raise ReleasePromotionError("staged GitHub release contract is missing")
    if github_release.get("publication_triggered") is not False:
        raise ReleasePromotionError("staged document already claims publication")
    assets = staged.get("assets")
    if not isinstance(assets, list) or len(assets) != 1:
        raise ReleasePromotionError("publish request requires exactly one approved release asset")

    return {
        "method": "POST",
        "endpoint": f"/repos/{staged['repository']}/releases",
        "body": {
            "tag_name": staged["tag"],
            "target_commitish": staged["source_sha"],
            "name": staged["release_name"],
            "draft": True,
            "prerelease": bool(github_release["prerelease"]),
            "generate_release_notes": False,
            "make_latest": "true" if github_release["make_latest"] else "false",
        },
        "approved_assets": list(assets),
        "approved_stage_digest": approved,
        "effect": "create-draft-only",
        "public_publish": False,
    }


def verify_published_release(
    staged: Mapping[str, Any],
    *,
    release_snapshot: Mapping[str, Any],
    require_immutable: bool,
) -> dict[str, Any]:
    recorded = _require_sha256(staged.get("stage_digest"), label="recorded stage digest")
    if recorded != _stage_digest(staged):
        raise ReleasePromotionError("staged release digest binding is invalid")
    if staged.get("state") != PromotionState.STAGED.value:
        raise ReleasePromotionError("published verification requires the exact staged authority")

    expected = {
        "tag_name": staged["tag"],
        "target_commitish": staged["source_sha"],
        "name": staged["release_name"],
    }
    for key, value in expected.items():
        if release_snapshot.get(key) != value:
            raise ReleasePromotionError(f"published release {key} mismatch")
    if release_snapshot.get("draft") is not False:
        raise ReleasePromotionError("published release is still draft")
    if release_snapshot.get("prerelease") is not staged["github_release"]["prerelease"]:
        raise ReleasePromotionError("published release prerelease flag mismatch")
    immutable = release_snapshot.get("immutable")
    if not isinstance(immutable, bool):
        raise ReleasePromotionError("published release immutable flag is missing")
    if require_immutable and not immutable:
        raise ReleasePromotionError("repository requires immutable release verification")

    snapshot_assets = release_snapshot.get("assets")
    if not isinstance(snapshot_assets, Sequence) or isinstance(snapshot_assets, (str, bytes)):
        raise ReleasePromotionError("published release assets are invalid")
    actual_assets = []
    for asset in snapshot_assets:
        if not isinstance(asset, Mapping):
            raise ReleasePromotionError("published release asset record is invalid")
        digest = str(asset.get("digest", ""))
        prefix = "sha256:"
        if not digest.startswith(prefix):
            raise ReleasePromotionError("published release asset digest is not SHA-256")
        actual_assets.append(
            {
                "name": str(asset.get("name", "")),
                "sha256": _require_sha256(
                    digest[len(prefix) :], label="published asset digest"
                ),
                "size": asset.get("size"),
            }
        )
    if actual_assets != staged["assets"]:
        raise ReleasePromotionError("published release assets do not match staged authority")

    release_id = release_snapshot.get("id")
    if not isinstance(release_id, int) or isinstance(release_id, bool) or release_id <= 0:
        raise ReleasePromotionError("published release ID is invalid")
    return {
        "state": PromotionState.PUBLISHED.value,
        "release_id": release_id,
        "tag": staged["tag"],
        "source_sha": staged["source_sha"],
        "immutable": immutable,
        "assets_verified": True,
        "stage_digest": recorded,
    }


__all__ = [
    "ATTESTATION_PROVIDER",
    "ATTESTATION_SEMANTICS",
    "DEFAULT_REPOSITORY",
    "PROMOTION_FORMAT",
    "PROMOTION_SCHEMA_VERSION",
    "PromotionState",
    "ReleaseAsset",
    "ReleasePromotionError",
    "build_publish_request",
    "stage_release_archive",
    "stage_verified_release",
    "verify_published_release",
]
