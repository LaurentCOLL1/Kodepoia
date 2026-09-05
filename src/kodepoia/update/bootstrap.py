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


@dataclass(frozen=True, slots=True)
class PackagedRootMaterial:
    root_bytes: bytes
    pin: PackagedRootPin
    purpose: str
    production_trust_claim: bool
    private_keys_persisted: bool


def _load_manifest() -> dict[str, object]:
    resource = files("kodepoia.update").joinpath(_SYNTHETIC_ROOT_MANIFEST_RESOURCE)
    try:
        payload = json.loads(resource.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TufVerificationError(f"packaged root manifest is unreadable: {exc}") from exc
    if not isinstance(payload, dict):
        raise TufVerificationError("packaged root manifest must be a JSON object")
    return payload


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

    manifest = _load_manifest()
    if manifest.get("schema_version") != 1:
        raise TufVerificationError("packaged root manifest schema version is unsupported")
    if manifest.get("purpose") != "synthetic-acceptance-only":
        raise TufVerificationError("packaged root purpose is not synthetic acceptance")
    if manifest.get("production_trust_claim") is not False:
        raise TufVerificationError("synthetic packaged root must not claim production trust")
    if manifest.get("private_keys_persisted") is not False:
        raise TufVerificationError("synthetic packaged root manifest claims persisted private keys")

    digest = hashlib.sha256(root_bytes).hexdigest()
    if manifest.get("root_sha256") != digest:
        raise TufVerificationError("packaged root digest does not match its manifest")

    pin = PackagedRootPin.from_root(root_bytes)
    if manifest.get("root_version") != pin.version:
        raise TufVerificationError("packaged root version does not match its manifest")

    metadata = Metadata.from_bytes(root_bytes)
    if not isinstance(metadata.signed, Root):
        raise TufVerificationError("packaged root resource is not TUF root metadata")
    try:
        metadata.signed.verify_delegate(
            "root",
            metadata.signed_bytes,
            metadata.signatures,
        )
    except Exception as exc:
        raise TufVerificationError(
            f"packaged root does not satisfy its own signature threshold: {exc}"
        ) from exc

    return PackagedRootMaterial(
        root_bytes=root_bytes,
        pin=pin,
        purpose="synthetic-acceptance-only",
        production_trust_claim=False,
        private_keys_persisted=False,
    )
