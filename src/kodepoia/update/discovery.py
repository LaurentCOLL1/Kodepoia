from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tuf.api.metadata import Metadata, Root, Snapshot, Targets, Timestamp

from kodepoia.release.identity import CURRENT_RELEASE, ReleaseIdentity
from kodepoia.release.tuf_security import TufVerificationError
from kodepoia.update.trust import (
    PackagedRootPin,
    UpdateTargetSpec,
    UpdateTransport,
    UpdateTransportError,
    UpdateTransportOffline,
)

DISCOVERY_CHANNELS = ("stable", "beta")
DISCOVERY_STATE_FORMAT = "kodepoia-update-discovery-state"
DISCOVERY_STATE_SCHEMA_VERSION = 1
_VERSION_RE = re.compile(
    r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    r"(?:-(?P<stage>a|b|rc)(?P<serial>\d+))?$"
)
_STAGE_RANK = {"a": 0, "b": 1, "rc": 2, "final": 3}


class UpdateMetadataExpired(TufVerificationError):
    """Raised when trusted update metadata is cryptographically valid but expired."""


@dataclass(frozen=True, slots=True)
class DiscoveryTrustedState:
    root_version: int
    timestamp_version: int
    snapshot_version: int
    targets_version: int

    def to_dict(self) -> dict[str, object]:
        return {
            "format": DISCOVERY_STATE_FORMAT,
            "schema_version": DISCOVERY_STATE_SCHEMA_VERSION,
            "root_version": self.root_version,
            "timestamp_version": self.timestamp_version,
            "snapshot_version": self.snapshot_version,
            "targets_version": self.targets_version,
        }


@dataclass(frozen=True, slots=True)
class UpdateDiscoveryCandidate:
    target: UpdateTargetSpec
    size_bytes: int
    sha256: str
    source_verification_state: str = "tuf-verified-metadata"
    release_notes_summary: str = "Not published in trusted update metadata."
    signing_status: str = "not-evaluated-during-discovery"
    provenance_status: str = "not-evaluated-during-discovery"
    withdrawn: bool = False


@dataclass(frozen=True, slots=True)
class UpdateDiscoveryResult:
    status: str
    candidate: UpdateDiscoveryCandidate | None
    detail: str


@dataclass(frozen=True, slots=True)
class _VerifiedMetadata:
    state: DiscoveryTrustedState
    targets: Targets


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


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


def _verify_role(trusted_root: Root, role: str, metadata: Metadata[Any]) -> None:
    try:
        trusted_root.verify_delegate(role, metadata.signed_bytes, metadata.signatures)
    except Exception as exc:
        raise TufVerificationError(
            f"{role} metadata did not satisfy the trusted signature threshold: {exc}"
        ) from exc


def _version_key(public_version: str) -> tuple[int, int, int, int, int]:
    match = _VERSION_RE.fullmatch(public_version.strip())
    if match is None:
        raise ValueError(f"unsupported public update version: {public_version!r}")
    stage = match.group("stage") or "final"
    serial = int(match.group("serial") or 0)
    return (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
        _STAGE_RANK[stage],
        serial,
    )


def _release_version_key(release: ReleaseIdentity) -> tuple[int, int, int, int, int]:
    return _version_key(release.public_version)


class TufMetadataDiscoveryVerifier:
    """Verify TUF metadata for discovery without fetching an installer target."""

    def __init__(
        self,
        state_dir: str | Path,
        *,
        root_pin: PackagedRootPin,
        reference_time: datetime,
    ) -> None:
        self.state_dir = Path(state_dir)
        self.root_pin = root_pin
        self.reference_time = _as_utc(reference_time)

    def _path(self, name: str) -> Path:
        return self.state_dir / name

    def _load_state(self) -> DiscoveryTrustedState | None:
        path = self._path("state.json")
        if not path.is_file():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise TufVerificationError(f"trusted discovery state is unreadable: {exc}") from exc
        if not isinstance(payload, dict):
            raise TufVerificationError("trusted discovery state is malformed")
        if payload.get("format") != DISCOVERY_STATE_FORMAT:
            raise TufVerificationError("trusted discovery state format is invalid")
        if payload.get("schema_version") != DISCOVERY_STATE_SCHEMA_VERSION:
            raise TufVerificationError("trusted discovery state schema version is unsupported")
        try:
            return DiscoveryTrustedState(
                root_version=int(payload["root_version"]),
                timestamp_version=int(payload["timestamp_version"]),
                snapshot_version=int(payload["snapshot_version"]),
                targets_version=int(payload["targets_version"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise TufVerificationError("trusted discovery state fields are invalid") from exc

    def _persist(self, metadata: dict[str, bytes], state: DiscoveryTrustedState) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        payloads = dict(metadata)
        payloads["state.json"] = (
            json.dumps(state.to_dict(), sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        for name, data in payloads.items():
            temp = self.state_dir / f".{name}.tmp"
            temp.write_bytes(data)
            os.replace(temp, self.state_dir / name)

    def verify(self, metadata: dict[str, bytes]) -> _VerifiedMetadata:
        required = ("root.json", "timestamp.json", "snapshot.json", "targets.json")
        missing = [name for name in required if name not in metadata]
        if missing:
            raise UpdateTransportError(f"metadata response is missing {missing[0]!r}")

        persisted_root = self._path("root.json")
        trusted_root_bytes = persisted_root.read_bytes() if persisted_root.is_file() else None
        if trusted_root_bytes is None:
            self.root_pin.verify(metadata["root.json"])
            trusted_root_bytes = metadata["root.json"]

        trusted_root_md = _parse(trusted_root_bytes, Root, "trusted root")
        candidate_root_md = _parse(metadata["root.json"], Root, "candidate root")
        trusted_root = trusted_root_md.signed
        candidate_root = candidate_root_md.signed

        if candidate_root.version < trusted_root.version:
            raise TufVerificationError("root rollback detected")
        if candidate_root.version == trusted_root.version:
            if metadata["root.json"] != trusted_root_bytes:
                raise TufVerificationError("root metadata changed without a version increment")
        else:
            if candidate_root.version != trusted_root.version + 1:
                raise TufVerificationError("root version update is not sequential")
            _verify_role(trusted_root, "root", candidate_root_md)
        _verify_role(candidate_root, "root", candidate_root_md)
        if candidate_root.is_expired(self.reference_time):
            raise UpdateMetadataExpired("root metadata is expired")

        timestamp_md = _parse(metadata["timestamp.json"], Timestamp, "timestamp")
        snapshot_md = _parse(metadata["snapshot.json"], Snapshot, "snapshot")
        targets_md = _parse(metadata["targets.json"], Targets, "targets")
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
                raise UpdateMetadataExpired(f"{label} metadata is expired")

        previous = self._load_state()
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
            timestamp.snapshot_meta.verify_length_and_hashes(metadata["snapshot.json"])
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
            targets_meta.verify_length_and_hashes(metadata["targets.json"])
        except Exception as exc:
            raise TufVerificationError(
                f"targets metadata hash/length reference mismatch: {exc}"
            ) from exc

        state = DiscoveryTrustedState(
            root_version=candidate_root.version,
            timestamp_version=timestamp.version,
            snapshot_version=snapshot.version,
            targets_version=targets.version,
        )
        self._persist({name: metadata[name] for name in required}, state)
        return _VerifiedMetadata(state=state, targets=targets)


class UpdateDiscoveryService:
    """Channel-aware R18.7 discovery service: metadata in, trusted UX state out."""

    def __init__(
        self,
        state_dir: str | Path,
        *,
        root_pin: PackagedRootPin,
        transport: UpdateTransport,
        platform: str = "windows-x86_64",
        installed_release: ReleaseIdentity = CURRENT_RELEASE,
        reference_time: datetime | None = None,
    ) -> None:
        self.transport = transport
        self.platform = platform.strip().lower()
        if not self.platform or "/" in self.platform or "\\" in self.platform:
            raise ValueError("update platform must be a path-safe identifier")
        self.installed_release = installed_release
        self.verifier = TufMetadataDiscoveryVerifier(
            Path(state_dir) / "tuf-discovery",
            root_pin=root_pin,
            reference_time=reference_time or datetime.now(UTC),
        )

    def _metadata(self) -> dict[str, bytes]:
        return {
            name: self.transport.fetch_metadata(name)
            for name in ("root.json", "timestamp.json", "snapshot.json", "targets.json")
        }

    def _candidate(self, targets: Targets, channel: str) -> UpdateDiscoveryCandidate | None:
        prefix = f"channels/{channel}/{self.platform}/"
        matches: list[tuple[tuple[int, int, int, int, int], UpdateDiscoveryCandidate]] = []
        for path, target_info in targets.targets.items():
            if not path.startswith(prefix):
                continue
            parts = path.split("/")
            if len(parts) != 6 or parts[0] != "channels" or parts[1] != channel:
                raise TufVerificationError(f"malformed authorized update target path: {path!r}")
            _, _, platform, public_version, source_sha, filename = parts
            target = UpdateTargetSpec(
                channel=channel,
                platform=platform,
                public_version=public_version,
                source_sha=source_sha,
                filename=filename,
            )
            digest = target_info.hashes.get("sha256")
            if digest is None or len(digest) != 64:
                raise TufVerificationError(f"authorized target lacks SHA-256: {path!r}")
            custom = target_info.custom if isinstance(target_info.custom, dict) else {}
            notes = custom.get("release_notes_summary")
            signing = custom.get("signing_status")
            provenance = custom.get("provenance_status")
            candidate = UpdateDiscoveryCandidate(
                target=target,
                size_bytes=target_info.length,
                sha256=digest,
                release_notes_summary=(
                    str(notes).strip() if notes else "Not published in trusted update metadata."
                ),
                signing_status=str(signing).strip() if signing else "not-evaluated-during-discovery",
                provenance_status=(
                    str(provenance).strip() if provenance else "not-evaluated-during-discovery"
                ),
                withdrawn=custom.get("withdrawn") is True,
            )
            matches.append((_version_key(public_version), candidate))
        if not matches:
            return None
        matches.sort(key=lambda item: item[0], reverse=True)
        return matches[0][1]

    def check(self, channel: str) -> UpdateDiscoveryResult:
        selected = channel.strip().lower()
        if selected not in DISCOVERY_CHANNELS:
            return UpdateDiscoveryResult(
                status="channel-unavailable",
                candidate=None,
                detail=f"unsupported discovery channel: {selected}",
            )
        try:
            verified = self.verifier.verify(self._metadata())
            candidate = self._candidate(verified.targets, selected)
        except UpdateTransportOffline as exc:
            return UpdateDiscoveryResult(status="offline", candidate=None, detail=str(exc))
        except UpdateMetadataExpired as exc:
            return UpdateDiscoveryResult(
                status="metadata-expired", candidate=None, detail=str(exc)
            )
        except (UpdateTransportError, TufVerificationError, ValueError) as exc:
            return UpdateDiscoveryResult(
                status="verification-failed", candidate=None, detail=str(exc)
            )

        if candidate is None:
            return UpdateDiscoveryResult(
                status="channel-unavailable",
                candidate=None,
                detail=f"no trusted {selected} target is available for {self.platform}",
            )
        if candidate.withdrawn:
            return UpdateDiscoveryResult(
                status="update-withdrawn",
                candidate=candidate,
                detail="the newest trusted target is marked withdrawn",
            )
        if _version_key(candidate.target.public_version) > _release_version_key(
            self.installed_release
        ):
            return UpdateDiscoveryResult(
                status="update-available",
                candidate=candidate,
                detail="trusted metadata authorizes a newer update",
            )
        return UpdateDiscoveryResult(
            status="up-to-date",
            candidate=candidate,
            detail="installed version is current for the selected channel",
        )
