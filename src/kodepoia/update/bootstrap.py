from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from importlib.resources import files

from tuf.api.metadata import Metadata, Root

from kodepoia.release.tuf_security import TufVerificationError
from kodepoia.update.trust import PackagedRootPin

_SYNTHETIC_ROOT_RESOURCE = "trusted_root.synthetic.json"
_SYNTHETIC_ROOT_MANIFEST_RESOURCE = "trusted_root.synthetic.manifest.json"
_PRODUCTION_ROOT_RESOURCE = "trusted_root.production.json"
_PRODUCTION_ROOT_MANIFEST_RESOURCE = "trusted_root.production.manifest.json"


@dataclass(frozen=True, slots=True)
class PackagedRootMaterial:
    root_bytes: bytes
    pin: PackagedRootPin
    purpose: str
    production_trust_claim: bool
    private_keys_persisted: bool


def _load_manifest(resource_name: str, *, label: str) -> dict[str, object]:
    resource = files("kodepoia.update").joinpath(resource_name)
    try:
        payload = json.loads(resource.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TufVerificationError(f"{label} root manifest is unreadable: {exc}") from exc
    if not isinstance(payload, dict):
        raise TufVerificationError(f"{label} root manifest must be a JSON object")
    return payload


def _verify_root_material(root_bytes: bytes, manifest: dict[str, object], *, label: str) -> PackagedRootPin:
    digest = hashlib.sha256(root_bytes).hexdigest()
    if manifest.get("root_sha256") != digest:
        raise TufVerificationError(f"{label} root digest does not match its manifest")

    pin = PackagedRootPin.from_root(root_bytes)
    if manifest.get("root_version") != pin.version:
        raise TufVerificationError(f"{label} root version does not match its manifest")

    metadata = Metadata.from_bytes(root_bytes)
    if not isinstance(metadata.signed, Root):
        raise TufVerificationError(f"{label} root resource is not TUF root metadata")
    try:
        metadata.signed.verify_delegate(
            "root",
            metadata.signed_bytes,
            metadata.signatures,
        )
    except Exception as exc:
        raise TufVerificationError(
            f"{label} root does not satisfy its own signature threshold: {exc}"
        ) from exc
    return pin


def load_synthetic_packaged_root(*, allow_synthetic: bool = False) -> PackagedRootMaterial:
    """Load the embedded acceptance root only after an explicit synthetic opt-in."""

    if not allow_synthetic:
        raise TufVerificationError(
            "synthetic packaged root is acceptance-only and requires allow_synthetic=True"
        )

    resource = files("kodepoia.update").joinpath(_SYNTHETIC_ROOT_RESOURCE)
    try:
        root_bytes = resource.read_bytes()
    except OSError as exc:
        raise TufVerificationError(f"packaged synthetic root is unreadable: {exc}") from exc

    manifest = _load_manifest(_SYNTHETIC_ROOT_MANIFEST_RESOURCE, label="synthetic packaged")
    if manifest.get("schema_version") != 1:
        raise TufVerificationError("packaged root manifest schema version is unsupported")
    if manifest.get("purpose") != "synthetic-acceptance-only":
        raise TufVerificationError("packaged root purpose is not synthetic acceptance")
    if manifest.get("production_trust_claim") is not False:
        raise TufVerificationError("synthetic packaged root must not claim production trust")
    if manifest.get("private_keys_persisted") is not False:
        raise TufVerificationError("synthetic packaged root manifest claims persisted private keys")

    pin = _verify_root_material(root_bytes, manifest, label="packaged synthetic")

    return PackagedRootMaterial(
        root_bytes=root_bytes,
        pin=pin,
        purpose="synthetic-acceptance-only",
        production_trust_claim=False,
        private_keys_persisted=False,
    )


def load_production_packaged_root() -> PackagedRootMaterial:
    """Load the real beta/release root, failing closed until real-key bootstrap is complete."""

    manifest = _load_manifest(_PRODUCTION_ROOT_MANIFEST_RESOURCE, label="production packaged")
    if manifest.get("schema_version") != 1:
        raise TufVerificationError("production root manifest schema version is unsupported")
    if manifest.get("purpose") != "production-beta-release-trust-anchor":
        raise TufVerificationError("production root manifest purpose is invalid")
    if manifest.get("private_keys_persisted") is not False:
        raise TufVerificationError("production root manifest claims persisted private keys")
    if manifest.get("synthetic_trust_allowed") is not False:
        raise TufVerificationError("production root manifest must explicitly forbid synthetic trust")

    state = manifest.get("state")
    if state != "active":
        if manifest.get("production_trust_claim") is not False:
            raise TufVerificationError("pending production root must not claim production trust")
        raise TufVerificationError("production packaged root is pending real-key bootstrap")
    if manifest.get("production_trust_claim") is not True:
        raise TufVerificationError("active production root must explicitly claim production trust")

    resource = files("kodepoia.update").joinpath(_PRODUCTION_ROOT_RESOURCE)
    try:
        root_bytes = resource.read_bytes()
    except OSError as exc:
        raise TufVerificationError(f"packaged production root is unreadable: {exc}") from exc

    synthetic_resource = files("kodepoia.update").joinpath(_SYNTHETIC_ROOT_RESOURCE)
    try:
        synthetic_root_bytes = synthetic_resource.read_bytes()
    except OSError as exc:
        raise TufVerificationError(f"packaged synthetic root is unreadable: {exc}") from exc
    if root_bytes == synthetic_root_bytes:
        raise TufVerificationError("production packaged root must be distinct from synthetic trust")
    if hashlib.sha256(root_bytes).digest() == hashlib.sha256(synthetic_root_bytes).digest():
        raise TufVerificationError("production packaged root digest matches synthetic trust")

    pin = _verify_root_material(root_bytes, manifest, label="packaged production")
    return PackagedRootMaterial(
        root_bytes=root_bytes,
        pin=pin,
        purpose="production-beta-release-trust-anchor",
        production_trust_claim=True,
        private_keys_persisted=False,
    )
