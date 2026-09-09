from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass
from typing import Mapping

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
)
from securesystemslib.signer import CryptoSigner, Signer

from kodepoia.update.online_signing import (
    OnlineSignerConfig,
    OnlineSigningError,
    RootRotationPackage,
    build_root_rotation_package,
)

ZERO_COST_PROVIDER = "github-environment-secret"
SNAPSHOT_SECRET_NAME = "TUF_SNAPSHOT_ED25519_SEED_B64"
TIMESTAMP_SECRET_NAME = "TUF_TIMESTAMP_ED25519_SEED_B64"
EXPECTED_SECRET_NAMES = {
    "snapshot": SNAPSHOT_SECRET_NAME,
    "timestamp": TIMESTAMP_SECRET_NAME,
}


@dataclass(frozen=True, slots=True)
class GeneratedOnlineKey:
    role: str
    secret_name: str
    secret_value_b64: str
    config: OnlineSignerConfig

    @property
    def public_sha256(self) -> str:
        keyval = self.config.public_key.keyval["public"].encode("utf-8")
        return hashlib.sha256(keyval).hexdigest()

    def public_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "provider": ZERO_COST_PROVIDER,
            "secret_name": self.secret_name,
            "keyid": self.config.keyid,
            "public_key": self.config.public_key.to_dict(),
            "public_sha256": self.public_sha256,
        }


@dataclass(frozen=True, slots=True)
class ZeroCostRotationMaterial:
    snapshot: GeneratedOnlineKey
    timestamp: GeneratedOnlineKey
    rotation: RootRotationPackage

    def public_manifest(self) -> dict[str, object]:
        return {
            "format": "kodepoia-r20-3-zero-cost-public-keys",
            "schema_version": 1,
            "provider": ZERO_COST_PROVIDER,
            "environment": "tuf-production-signing",
            "snapshot": self.snapshot.public_dict(),
            "timestamp": self.timestamp.public_dict(),
            "root_rotation_package_id": self.rotation.package_id,
            "private_material_in_manifest": False,
            "paid_provider_required": False,
        }


class GitHubEnvironmentSecretResolver:
    """Resolve low-authority Ed25519 online signers from process environment only."""

    def __init__(self, environ: Mapping[str, str] | None = None) -> None:
        self._environ = os.environ if environ is None else environ

    def __call__(self, config: OnlineSignerConfig) -> Signer:
        if config.provider != ZERO_COST_PROVIDER:
            raise OnlineSigningError(
                f"unsupported zero-cost signer provider: {config.provider!r}"
            )
        expected = EXPECTED_SECRET_NAMES.get(config.role)
        if expected is None or config.resource != expected:
            raise OnlineSigningError(
                f"unexpected GitHub secret resource for {config.role}: {config.resource!r}"
            )
        value = self._environ.get(config.resource)
        if value is None or not value.strip():
            raise OnlineSigningError(f"missing GitHub Actions secret: {config.resource}")
        if value != value.strip():
            raise OnlineSigningError(f"secret {config.resource} contains surrounding whitespace")
        try:
            seed = base64.b64decode(value, validate=True)
        except Exception as exc:
            raise OnlineSigningError(
                f"secret {config.resource} is not strict base64"
            ) from exc
        if len(seed) != 32:
            raise OnlineSigningError(
                f"secret {config.resource} must decode to exactly 32 bytes"
            )
        signer = CryptoSigner(Ed25519PrivateKey.from_private_bytes(seed))
        if signer.public_key.keyid != config.keyid:
            raise OnlineSigningError(
                f"secret {config.resource} does not match configured public key"
            )
        if signer.public_key.to_dict() != config.public_key.to_dict():
            raise OnlineSigningError(
                f"secret {config.resource} public key payload mismatch"
            )
        return signer


def generate_online_key(role: str) -> GeneratedOnlineKey:
    try:
        secret_name = EXPECTED_SECRET_NAMES[role]
    except KeyError as exc:
        raise OnlineSigningError(f"unsupported zero-cost online role: {role!r}") from exc

    private_key = Ed25519PrivateKey.generate()
    signer = CryptoSigner(private_key)
    seed = private_key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    secret_value_b64 = base64.b64encode(seed).decode("ascii")
    config = OnlineSignerConfig(
        role=role,
        provider=ZERO_COST_PROVIDER,
        resource=secret_name,
        public_key=signer.public_key,
    )
    return GeneratedOnlineKey(
        role=role,
        secret_name=secret_name,
        secret_value_b64=secret_value_b64,
        config=config,
    )


def prepare_zero_cost_rotation(*, current_root_bytes: bytes) -> ZeroCostRotationMaterial:
    snapshot = generate_online_key("snapshot")
    timestamp = generate_online_key("timestamp")
    if snapshot.config.keyid == timestamp.config.keyid:
        raise OnlineSigningError("generated Snapshot and Timestamp keys unexpectedly match")
    rotation = build_root_rotation_package(
        current_root_bytes=current_root_bytes,
        snapshot=snapshot.config,
        timestamp=timestamp.config,
    )
    return ZeroCostRotationMaterial(
        snapshot=snapshot,
        timestamp=timestamp,
        rotation=rotation,
    )
