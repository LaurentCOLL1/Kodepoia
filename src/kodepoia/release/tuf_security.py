from __future__ import annotations

import copy
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from securesystemslib.signer import CryptoSigner, Signer
from tuf.api.metadata import Metadata, MetaFile, Root, Snapshot, TargetFile, Targets, Timestamp

TUF_STATE_FORMAT = "kodepoia-tuf-trusted-state"
TUF_STATE_SCHEMA_VERSION = 1
DEFAULT_TARGET_PATH = "releases/kodepoia-release.json"


class TufVerificationError(ValueError):
    """Raised when TUF metadata violates the R18.6 trust contract."""


@dataclass(frozen=True, slots=True)
class TrustedTufState:
    root_version: int
    timestamp_version: int
    snapshot_version: int
    targets_version: int
    target_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": TUF_STATE_FORMAT,
            "schema_version": TUF_STATE_SCHEMA_VERSION,
            "root_version": self.root_version,
            "timestamp_version": self.timestamp_version,
            "snapshot_version": self.snapshot_version,
            "targets_version": self.targets_version,
            "target_sha256": self.target_sha256,
        }


@dataclass(frozen=True, slots=True)
class SyntheticTufRepository:
    root: bytes
    timestamp: bytes
    snapshot: bytes
    targets: bytes
    target_path: str
    target_data: bytes

    def metadata_bytes(self) -> dict[str, bytes]:
        return {
            "root.json": self.root,
            "timestamp.json": self.timestamp,
            "snapshot.json": self.snapshot,
            "targets.json": self.targets,
        }


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _verify_role(
    trusted_root: Root,
    role: str,
    metadata: Metadata[Any],
) -> None:
    try:
        trusted_root.verify_delegate(role, metadata.signed_bytes, metadata.signatures)
    except Exception as exc:
        raise TufVerificationError(
            f"{role} metadata did not satisfy the trusted signature threshold: {exc}"
        ) from exc


def _parse(data: bytes, expected_type: type[Any], label: str) -> Metadata[Any]:
    try:
        metadata = Metadata.from_bytes(data)
    except Exception as exc:
        raise TufVerificationError(f"{label} metadata is not valid TUF JSON: {exc}") from exc
    if not isinstance(metadata.signed, expected_type):
        raise TufVerificationError(
            f"{label} metadata has unexpected signed type {metadata.signed.type!r}"
        )
    return metadata


class SyntheticTufRepositoryBuilder:
    """Create isolated signed TUF repositories for deterministic acceptance tests."""

    def __init__(self, *, root_threshold: int = 2) -> None:
        if root_threshold < 1:
            raise ValueError("root_threshold must be positive")
        self._root_signers: list[Signer] = [
            CryptoSigner.generate_ed25519() for _ in range(root_threshold)
        ]
        self._timestamp_signer: Signer = CryptoSigner.generate_ed25519()
        self._snapshot_signer: Signer = CryptoSigner.generate_ed25519()
        self._targets_signer: Signer = CryptoSigner.generate_ed25519()
        self._root_threshold = root_threshold

        safe_expiry = datetime(2035, 1, 1, tzinfo=UTC)
        root = Root(expires=safe_expiry, consistent_snapshot=False)
        for signer in self._root_signers:
            root.add_key(signer.public_key, "root")
        root.roles["root"].threshold = root_threshold
        root.add_key(self._timestamp_signer.public_key, "timestamp")
        root.add_key(self._snapshot_signer.public_key, "snapshot")
        root.add_key(self._targets_signer.public_key, "targets")
        self._root_template = root

    def build(
        self,
        *,
        root_version: int = 1,
        root_signature_count: int | None = None,
        timestamp_version: int = 1,
        snapshot_version: int = 1,
        targets_version: int = 1,
        expires: datetime | None = None,
        timestamp_expires: datetime | None = None,
        target_path: str = DEFAULT_TARGET_PATH,
        target_data: bytes = b'{"release":"v1.1.0-rc1"}\n',
        corrupt_targets_reference: bool = False,
        corrupt_snapshot_reference: bool = False,
    ) -> SyntheticTufRepository:
        expiry = _as_utc(expires or datetime(2035, 1, 1, tzinfo=UTC))
        timestamp_expiry = _as_utc(timestamp_expires or expiry)

        root_signed = Root.from_dict(copy.deepcopy(self._root_template.to_dict()))
        root_signed.version = root_version
        root_md = Metadata(root_signed)
        count = self._root_threshold if root_signature_count is None else root_signature_count
        if count < 0 or count > len(self._root_signers):
            raise ValueError("root_signature_count is outside available signer range")
        for signer in self._root_signers[:count]:
            root_md.sign(signer, append=True)
        root_bytes = root_md.to_bytes()

        targets_signed = Targets(version=targets_version, expires=expiry)
        targets_signed.targets[target_path] = TargetFile.from_data(
            target_path, target_data, ["sha256"]
        )
        targets_md = Metadata(targets_signed)
        targets_md.sign(self._targets_signer)
        targets_bytes = targets_md.to_bytes()

        if corrupt_targets_reference:
            targets_meta = MetaFile(
                version=targets_version,
                length=len(targets_bytes),
                hashes={"sha256": "0" * 64},
            )
        else:
            targets_meta = MetaFile.from_data(targets_version, targets_bytes, ["sha256"])
        snapshot_signed = Snapshot(
            version=snapshot_version,
            expires=expiry,
            meta={"targets.json": targets_meta},
        )
        snapshot_md = Metadata(snapshot_signed)
        snapshot_md.sign(self._snapshot_signer)
        snapshot_bytes = snapshot_md.to_bytes()

        if corrupt_snapshot_reference:
            snapshot_meta = MetaFile(
                version=snapshot_version,
                length=len(snapshot_bytes),
                hashes={"sha256": "0" * 64},
            )
        else:
            snapshot_meta = MetaFile.from_data(snapshot_version, snapshot_bytes, ["sha256"])
        timestamp_signed = Timestamp(
            version=timestamp_version,
            expires=timestamp_expiry,
            snapshot_meta=snapshot_meta,
        )
        timestamp_md = Metadata(timestamp_signed)
        timestamp_md.sign(self._timestamp_signer)
        timestamp_bytes = timestamp_md.to_bytes()

        return SyntheticTufRepository(
            root=root_bytes,
            timestamp=timestamp_bytes,
            snapshot=snapshot_bytes,
            targets=targets_bytes,
            target_path=target_path,
            target_data=target_data,
        )


class TufUpdateVerifier:
    """Verify top-level TUF metadata and persist trusted state fail-closed."""

    def __init__(self, state_dir: str | Path, *, reference_time: datetime) -> None:
        self.state_dir = Path(state_dir)
        self.reference_time = _as_utc(reference_time)

    def _trusted_path(self, name: str) -> Path:
        return self.state_dir / name

    def _load_trusted_bytes(self, name: str) -> bytes | None:
        path = self._trusted_path(name)
        return path.read_bytes() if path.is_file() else None

    def _persist(
        self,
        repository: SyntheticTufRepository,
        state: TrustedTufState,
    ) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        payloads = repository.metadata_bytes()
        payloads["state.json"] = (
            json.dumps(
                state.to_dict(),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
        for name, data in payloads.items():
            temp = self.state_dir / f".{name}.tmp"
            temp.write_bytes(data)
            os.replace(temp, self.state_dir / name)

    def load_state(self) -> TrustedTufState | None:
        path = self._trusted_path("state.json")
        if not path.is_file():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise TufVerificationError(f"trusted TUF state is unreadable: {exc}") from exc
        if payload.get("format") != TUF_STATE_FORMAT:
            raise TufVerificationError("trusted TUF state format is invalid")
        if payload.get("schema_version") != TUF_STATE_SCHEMA_VERSION:
            raise TufVerificationError("trusted TUF state schema version is unsupported")
        try:
            return TrustedTufState(
                root_version=int(payload["root_version"]),
                timestamp_version=int(payload["timestamp_version"]),
                snapshot_version=int(payload["snapshot_version"]),
                targets_version=int(payload["targets_version"]),
                target_sha256=str(payload["target_sha256"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise TufVerificationError("trusted TUF state fields are invalid") from exc

    def verify(
        self,
        repository: SyntheticTufRepository,
        *,
        bootstrap_root: bytes | None = None,
    ) -> TrustedTufState:
        trusted_root_bytes = self._load_trusted_bytes("root.json")
        if trusted_root_bytes is None:
            if bootstrap_root is None:
                raise TufVerificationError(
                    "bootstrap root is required when no trusted root is persisted"
                )
            trusted_root_bytes = bootstrap_root

        trusted_root_md = _parse(trusted_root_bytes, Root, "trusted root")
        candidate_root_md = _parse(repository.root, Root, "candidate root")
        trusted_root = trusted_root_md.signed
        candidate_root = candidate_root_md.signed

        if candidate_root.version < trusted_root.version:
            raise TufVerificationError("root rollback detected")
        if candidate_root.version == trusted_root.version:
            if repository.root != trusted_root_bytes:
                raise TufVerificationError("root metadata changed without a version increment")
        else:
            if candidate_root.version != trusted_root.version + 1:
                raise TufVerificationError("root version update is not sequential")
            _verify_role(trusted_root, "root", candidate_root_md)

        _verify_role(candidate_root, "root", candidate_root_md)
        if candidate_root.is_expired(self.reference_time):
            raise TufVerificationError("root metadata is expired (freeze protection)")

        timestamp_md = _parse(repository.timestamp, Timestamp, "timestamp")
        snapshot_md = _parse(repository.snapshot, Snapshot, "snapshot")
        targets_md = _parse(repository.targets, Targets, "targets")

        _verify_role(candidate_root, "timestamp", timestamp_md)
        _verify_role(candidate_root, "snapshot", snapshot_md)
        _verify_role(candidate_root, "targets", targets_md)

        timestamp = timestamp_md.signed
        snapshot = snapshot_md.signed
        targets = targets_md.signed

        for label, signed in (
            ("timestamp", timestamp),
            ("snapshot", snapshot),
            ("targets", targets),
        ):
            if signed.is_expired(self.reference_time):
                raise TufVerificationError(f"{label} metadata is expired (freeze protection)")

        previous = self.load_state()
        if previous is not None:
            if timestamp.version < previous.timestamp_version:
                raise TufVerificationError("timestamp rollback detected")
            if snapshot.version < previous.snapshot_version:
                raise TufVerificationError("snapshot rollback detected")
            if targets.version < previous.targets_version:
                raise TufVerificationError("targets rollback detected")

        if timestamp.snapshot_meta.version != snapshot.version:
            raise TufVerificationError("timestamp snapshot version does not match snapshot metadata")
        try:
            timestamp.snapshot_meta.verify_length_and_hashes(repository.snapshot)
        except Exception as exc:
            raise TufVerificationError(
                f"snapshot metadata hash/length reference mismatch: {exc}"
            ) from exc

        targets_meta = snapshot.meta.get("targets.json")
        if targets_meta is None:
            raise TufVerificationError("snapshot metadata does not reference targets.json")
        if targets_meta.version != targets.version:
            raise TufVerificationError("snapshot targets version does not match targets metadata")
        try:
            targets_meta.verify_length_and_hashes(repository.targets)
        except Exception as exc:
            raise TufVerificationError(
                f"targets metadata hash/length reference mismatch: {exc}"
            ) from exc

        target_info = targets.targets.get(repository.target_path)
        if target_info is None:
            raise TufVerificationError(
                f"targets metadata does not authorize {repository.target_path!r}"
            )
        try:
            target_info.verify_length_and_hashes(repository.target_data)
        except Exception as exc:
            raise TufVerificationError(f"target payload hash/length mismatch: {exc}") from exc

        state = TrustedTufState(
            root_version=candidate_root.version,
            timestamp_version=timestamp.version,
            snapshot_version=snapshot.version,
            targets_version=targets.version,
            target_sha256=_sha256_bytes(repository.target_data),
        )
        self._persist(repository, state)
        return state
