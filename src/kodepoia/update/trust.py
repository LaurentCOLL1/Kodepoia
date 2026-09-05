from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from securesystemslib.signer import CryptoSigner, Signer
from tuf.api.metadata import Metadata, Root

from kodepoia.release.identity import ReleaseIdentity
from kodepoia.release.tuf_security import (
    SyntheticTufRepository,
    SyntheticTufRepositoryBuilder,
    TrustedTufState,
    TufUpdateVerifier,
    TufVerificationError,
)


class UpdateTransportOffline(ConnectionError):
    """Raised when an update transport cannot reach its repository."""


class UpdateTransportError(RuntimeError):
    """Raised for malformed or incomplete transport responses."""


@dataclass(frozen=True, slots=True)
class PackagedRootPin:
    version: int
    sha256: str

    def __post_init__(self) -> None:
        digest = self.sha256.strip().lower()
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise ValueError("trusted-root SHA-256 must be 64 lowercase hexadecimal characters")
        if self.version < 1:
            raise ValueError("trusted-root version must be positive")
        object.__setattr__(self, "sha256", digest)

    @classmethod
    def from_root(cls, root_bytes: bytes) -> PackagedRootPin:
        metadata = Metadata.from_bytes(root_bytes)
        if not isinstance(metadata.signed, Root):
            raise ValueError("packaged trust anchor is not root metadata")
        return cls(
            version=metadata.signed.version,
            sha256=hashlib.sha256(root_bytes).hexdigest(),
        )

    def verify(self, root_bytes: bytes) -> None:
        metadata = Metadata.from_bytes(root_bytes)
        if not isinstance(metadata.signed, Root):
            raise TufVerificationError("bootstrap trust anchor is not root metadata")
        digest = hashlib.sha256(root_bytes).hexdigest()
        if metadata.signed.version != self.version:
            raise TufVerificationError(
                f"bootstrap root version mismatch: expected {self.version}, got {metadata.signed.version}"
            )
        if digest != self.sha256:
            raise TufVerificationError("bootstrap root does not match packaged trusted-root pin")


@dataclass(frozen=True, slots=True)
class UpdateTargetSpec:
    channel: str
    platform: str
    public_version: str
    source_sha: str
    filename: str = "KodepoiaSetup.exe"

    def __post_init__(self) -> None:
        channel = self.channel.strip().lower()
        platform = self.platform.strip().lower()
        source_sha = self.source_sha.strip().lower()
        if channel not in {"stable", "beta", "nightly"}:
            raise ValueError(f"unsupported update channel: {channel}")
        if not platform or "/" in platform or "\\" in platform:
            raise ValueError("update platform must be a non-empty path-safe identifier")
        if len(source_sha) != 40 or any(c not in "0123456789abcdef" for c in source_sha):
            raise ValueError("update source SHA must be an exact lowercase Git commit")
        if not self.public_version.strip() or "/" in self.public_version:
            raise ValueError("public version must be non-empty and path-safe")
        if not self.filename.strip() or "/" in self.filename or "\\" in self.filename:
            raise ValueError("target filename must be a path-safe basename")
        object.__setattr__(self, "channel", channel)
        object.__setattr__(self, "platform", platform)
        object.__setattr__(self, "source_sha", source_sha)

    @classmethod
    def from_release(
        cls,
        release: ReleaseIdentity,
        *,
        source_sha: str,
        platform: str,
        filename: str = "KodepoiaSetup.exe",
    ) -> UpdateTargetSpec:
        return cls(
            channel=release.channel,
            platform=platform,
            public_version=release.public_version,
            source_sha=source_sha,
            filename=filename,
        )

    @property
    def path(self) -> str:
        return (
            f"channels/{self.channel}/{self.platform}/{self.public_version}/"
            f"{self.source_sha}/{self.filename}"
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "channel": self.channel,
            "platform": self.platform,
            "public_version": self.public_version,
            "source_sha": self.source_sha,
            "filename": self.filename,
            "path": self.path,
        }


@dataclass(frozen=True, slots=True)
class UpdateCandidate:
    target: UpdateTargetSpec
    size_bytes: int
    sha256: str
    tuf_state: TrustedTufState

    def to_dict(self) -> dict[str, object]:
        return {
            "target": self.target.to_dict(),
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "tuf_state": self.tuf_state.to_dict(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> UpdateCandidate:
        target_payload = payload.get("target")
        state_payload = payload.get("tuf_state")
        if not isinstance(target_payload, dict) or not isinstance(state_payload, dict):
            raise ValueError("cached update candidate is malformed")
        target = UpdateTargetSpec(
            channel=str(target_payload["channel"]),
            platform=str(target_payload["platform"]),
            public_version=str(target_payload["public_version"]),
            source_sha=str(target_payload["source_sha"]),
            filename=str(target_payload["filename"]),
        )
        state = TrustedTufState(
            root_version=int(state_payload["root_version"]),
            timestamp_version=int(state_payload["timestamp_version"]),
            snapshot_version=int(state_payload["snapshot_version"]),
            targets_version=int(state_payload["targets_version"]),
            target_sha256=str(state_payload["target_sha256"]),
        )
        return cls(
            target=target,
            size_bytes=int(payload["size_bytes"]),
            sha256=str(payload["sha256"]),
            tuf_state=state,
        )


@dataclass(frozen=True, slots=True)
class UpdateCheckResult:
    status: str
    candidate: UpdateCandidate | None
    detail: str


class UpdateTransport(Protocol):
    def fetch_metadata(self, name: str) -> bytes: ...

    def fetch_target(self, path: str) -> bytes: ...


@dataclass(slots=True)
class MemoryUpdateTransport:
    metadata: dict[str, bytes]
    targets: dict[str, bytes]
    online: bool = True

    @classmethod
    def from_repository(cls, repository: SyntheticTufRepository) -> MemoryUpdateTransport:
        return cls(
            metadata=repository.metadata_bytes(),
            targets={repository.target_path: repository.target_data},
        )

    def fetch_metadata(self, name: str) -> bytes:
        if not self.online:
            raise UpdateTransportOffline("metadata transport is offline")
        try:
            return self.metadata[name]
        except KeyError as exc:
            raise UpdateTransportError(f"metadata response is missing {name!r}") from exc

    def fetch_target(self, path: str) -> bytes:
        if not self.online:
            raise UpdateTransportOffline("target transport is offline")
        try:
            return self.targets[path]
        except KeyError as exc:
            raise UpdateTransportError(f"repository does not expose target {path!r}") from exc


class SyntheticUpdateRepositoryBuilder:
    """R18.6 product-level synthetic repository with channel/platform target paths."""

    def __init__(self, *, root_threshold: int = 2) -> None:
        self._core = SyntheticTufRepositoryBuilder(root_threshold=root_threshold)
        self._root_threshold = root_threshold
        self._previous_root_signers: list[Signer] = []

    def rotate_root_keys(self) -> None:
        self._previous_root_signers = list(self._core._root_signers)
        new_signers: list[Signer] = [
            CryptoSigner.generate_ed25519() for _ in range(self._root_threshold)
        ]
        safe_expiry = datetime(2035, 1, 1, tzinfo=UTC)
        root = Root(expires=safe_expiry, consistent_snapshot=False)
        for signer in new_signers:
            root.add_key(signer.public_key, "root")
        root.roles["root"].threshold = self._root_threshold
        root.add_key(self._core._timestamp_signer.public_key, "timestamp")
        root.add_key(self._core._snapshot_signer.public_key, "snapshot")
        root.add_key(self._core._targets_signer.public_key, "targets")
        self._core._root_signers = new_signers
        self._core._root_template = root

    def build(
        self,
        target: UpdateTargetSpec,
        installer: bytes,
        *,
        root_version: int = 1,
        timestamp_version: int = 1,
        snapshot_version: int = 1,
        targets_version: int = 1,
        timestamp_expires: datetime | None = None,
    ) -> SyntheticTufRepository:
        repository = self._core.build(
            root_version=root_version,
            timestamp_version=timestamp_version,
            snapshot_version=snapshot_version,
            targets_version=targets_version,
            timestamp_expires=timestamp_expires,
            target_path=target.path,
            target_data=installer,
        )
        if not self._previous_root_signers:
            return repository

        root_metadata = Metadata.from_bytes(repository.root)
        for signer in self._previous_root_signers:
            root_metadata.sign(signer, append=True)
        return replace(repository, root=root_metadata.to_bytes())


class UpdateClient:
    """Structured R18.6 update verifier that never trusts transport data directly."""

    def __init__(
        self,
        state_dir: str | Path,
        *,
        root_pin: PackagedRootPin,
        reference_time: datetime,
    ) -> None:
        self.state_dir = Path(state_dir)
        self.root_pin = root_pin
        self.verifier = TufUpdateVerifier(self.state_dir / "tuf", reference_time=reference_time)
        self._candidate_path = self.state_dir / "verified-update-candidate.json"

    def _load_cached_candidate(self) -> UpdateCandidate | None:
        if not self._candidate_path.is_file():
            return None
        try:
            payload = json.loads(self._candidate_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                return None
            return UpdateCandidate.from_dict(payload)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            return None

    def _persist_candidate(self, candidate: UpdateCandidate) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        temp = self.state_dir / ".verified-update-candidate.json.tmp"
        temp.write_text(
            json.dumps(candidate.to_dict(), sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        os.replace(temp, self._candidate_path)

    def verify_refresh(
        self,
        transport: UpdateTransport,
        target: UpdateTargetSpec,
    ) -> UpdateCandidate:
        root = transport.fetch_metadata("root.json")
        timestamp = transport.fetch_metadata("timestamp.json")
        snapshot = transport.fetch_metadata("snapshot.json")
        targets = transport.fetch_metadata("targets.json")
        installer = transport.fetch_target(target.path)

        bootstrap_root: bytes | None = None
        if not (self.state_dir / "tuf" / "root.json").is_file():
            self.root_pin.verify(root)
            bootstrap_root = root

        repository = SyntheticTufRepository(
            root=root,
            timestamp=timestamp,
            snapshot=snapshot,
            targets=targets,
            target_path=target.path,
            target_data=installer,
        )
        state = self.verifier.verify(repository, bootstrap_root=bootstrap_root)
        candidate = UpdateCandidate(
            target=target,
            size_bytes=len(installer),
            sha256=hashlib.sha256(installer).hexdigest(),
            tuf_state=state,
        )
        self._persist_candidate(candidate)
        return candidate

    def check(
        self,
        transport: UpdateTransport,
        target: UpdateTargetSpec,
    ) -> UpdateCheckResult:
        try:
            candidate = self.verify_refresh(transport, target)
        except UpdateTransportOffline as exc:
            cached = self._load_cached_candidate()
            return UpdateCheckResult(
                status="offline-cached" if cached is not None else "offline-no-cache",
                candidate=cached,
                detail=str(exc),
            )
        except (UpdateTransportError, TufVerificationError, ValueError) as exc:
            return UpdateCheckResult(
                status="verification-failed",
                candidate=self._load_cached_candidate(),
                detail=str(exc),
            )
        return UpdateCheckResult(status="verified", candidate=candidate, detail="TUF verification passed")
