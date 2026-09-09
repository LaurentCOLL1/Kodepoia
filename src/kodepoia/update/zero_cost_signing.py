from __future__ import annotations

import base64
import hashlib
import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
)
from securesystemslib.signer import CryptoSigner, Signer
from tuf.api.metadata import Metadata, Root

from kodepoia.update.online_signing import (
    OnlineSignerConfig,
    OnlineSigningError,
    RootRotationPackage,
    build_root_rotation_package,
    verify_signed_root_rotation,
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


@dataclass(frozen=True, slots=True)
class RootSigningResult:
    signed_root_bytes: bytes
    signer_keyids: tuple[str, ...]
    verification: dict[str, object]

    def public_manifest(self, *, unsigned_root_bytes: bytes) -> dict[str, object]:
        return {
            "format": "kodepoia-r20-3-root-v2-signing-acceptance",
            "schema_version": 1,
            "unsigned_root_sha256": hashlib.sha256(unsigned_root_bytes).hexdigest(),
            "signed_root_sha256": hashlib.sha256(self.signed_root_bytes).hexdigest(),
            "signer_keyids": list(self.signer_keyids),
            "signature_count": len(self.signer_keyids),
            "old_root_threshold_verified": self.verification[
                "old_root_threshold_verified"
            ],
            "new_root_threshold_verified": self.verification[
                "new_root_threshold_verified"
            ],
            "offline_roles_preserved": self.verification["offline_roles_preserved"],
            "private_material_in_output": False,
            "production_effect": False,
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


def sign_root_rotation(
    *,
    current_root_bytes: bytes,
    unsigned_root_bytes: bytes,
    root_signers: Iterable[Signer],
) -> RootSigningResult:
    """Sign the exact Root N+1 payload with distinct current Root-authorized signers."""

    try:
        current = Metadata.from_bytes(current_root_bytes)
        candidate = Metadata.from_bytes(unsigned_root_bytes)
    except Exception as exc:
        raise OnlineSigningError(f"invalid Root metadata supplied for signing: {exc}") from exc
    if not isinstance(current.signed, Root) or not isinstance(candidate.signed, Root):
        raise OnlineSigningError("Root signing requires Root metadata")
    if candidate.signatures:
        raise OnlineSigningError("candidate Root must be unsigned before the ceremony")
    if candidate.signed.version != current.signed.version + 1:
        raise OnlineSigningError("candidate Root version must be exactly current version + 1")
    if candidate.signed.roles["root"] != current.signed.roles["root"]:
        raise OnlineSigningError("candidate Root changes the offline Root role policy")
    if candidate.signed.roles["targets"] != current.signed.roles["targets"]:
        raise OnlineSigningError("candidate Root changes the offline Targets role policy")

    authorized = set(current.signed.roles["root"].keyids)
    unique: dict[str, Signer] = {}
    for signer in root_signers:
        keyid = signer.public_key.keyid
        if keyid not in authorized:
            raise OnlineSigningError(
                f"signer {keyid} is not authorized by the current Root role"
            )
        unique.setdefault(keyid, signer)

    threshold = current.signed.roles["root"].threshold
    if len(unique) < threshold:
        raise OnlineSigningError(
            f"Root ceremony requires at least {threshold} distinct authorized signers"
        )

    for index, signer in enumerate(unique.values()):
        candidate.sign(signer, append=index > 0)
    signed_root_bytes = candidate.to_bytes() + b"\n"
    verification = verify_signed_root_rotation(
        current_root_bytes=current_root_bytes,
        candidate_root_bytes=signed_root_bytes,
    )
    return RootSigningResult(
        signed_root_bytes=signed_root_bytes,
        signer_keyids=tuple(unique),
        verification=verification,
    )
