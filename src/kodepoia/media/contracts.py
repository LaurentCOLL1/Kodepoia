from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._:-]{0,127}$")
_LOCALE_RE = re.compile(r"^[A-Za-z]{2,3}(?:[-_][A-Za-z]{2}|[-_][A-Za-z0-9]{4,8})*$")


def bounded_text(value: str, *, field: str, maximum: int, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if (not allow_empty and not value) or len(value) > maximum:
        raise ValueError(f"{field} has invalid length")
    if _CONTROL_RE.search(value):
        raise ValueError(f"{field} must not contain control characters")
    return value


def sha256_hex(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be lowercase SHA-256 hex")
    return value


def stable_id(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _ID_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be a stable identifier")
    return value


class MediaState(StrEnum):
    UNKNOWN = "UNKNOWN"
    NA = "N/A"
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    BLOCKED = "BLOCKED"
    STALE = "STALE"
    MISSING = "MISSING"
    CORRUPT = "CORRUPT"
    UNSUPPORTED = "UNSUPPORTED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    RIGHTS_BLOCKED = "RIGHTS_BLOCKED"
    CONFLICTED = "CONFLICTED"
    MIGRATION_REQUIRED = "MIGRATION_REQUIRED"
    PASS = "PASS"
    WARN = "WARN"


class MediaRuntimeKind(StrEnum):
    FFPROBE = "ffprobe"
    FFMPEG = "ffmpeg"
    TTS = "tts"
    GODOT = "godot"


@dataclass(frozen=True, slots=True)
class AudioSourceIdentity:
    revision_id: str
    sha256: str
    bytes: int
    container: str
    codec: str
    sample_rate_hz: int
    channels: int
    duration_seconds: float

    def __post_init__(self) -> None:
        stable_id(self.revision_id, field="revision_id")
        sha256_hex(self.sha256, field="sha256")
        if isinstance(self.bytes, bool) or not isinstance(self.bytes, int) or self.bytes < 0:
            raise ValueError("bytes must be a non-negative integer")
        for name in ("container", "codec"):
            bounded_text(getattr(self, name), field=name, maximum=64)
        if isinstance(self.sample_rate_hz, bool) or not isinstance(self.sample_rate_hz, int) or self.sample_rate_hz <= 0:
            raise ValueError("sample_rate_hz must be positive")
        if isinstance(self.channels, bool) or not isinstance(self.channels, int) or not 1 <= self.channels <= 32:
            raise ValueError("channels must be between 1 and 32")
        if not math.isfinite(self.duration_seconds) or self.duration_seconds < 0:
            raise ValueError("duration_seconds must be finite and non-negative")

    def canonical(self) -> dict[str, Any]:
        return {"revision_id": self.revision_id, "sha256": self.sha256, "bytes": self.bytes, "container": self.container, "codec": self.codec, "sample_rate_hz": self.sample_rate_hz, "channels": self.channels, "duration_seconds": self.duration_seconds}


@dataclass(frozen=True, slots=True)
class AudioQAReport:
    profile_id: str
    source_sha256: str
    state: MediaState
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        stable_id(self.profile_id, field="profile_id")
        sha256_hex(self.source_sha256, field="source_sha256")
        if self.state not in {MediaState.PASS, MediaState.WARN, MediaState.BLOCKED, MediaState.BUDGET_EXCEEDED, MediaState.CORRUPT}:
            raise ValueError("invalid AudioQAReport state")
        object.__setattr__(self, "blockers", tuple(sorted(set(self.blockers))))
        object.__setattr__(self, "warnings", tuple(sorted(set(self.warnings))))
        for value in self.blockers + self.warnings:
            stable_id(value, field="qa_code")

    def canonical(self) -> dict[str, Any]:
        return {"profile_id": self.profile_id, "source_sha256": self.source_sha256, "state": self.state.value, "blockers": list(self.blockers), "warnings": list(self.warnings)}


@dataclass(frozen=True, slots=True)
class VoiceRuntimeIdentity:
    backend: str
    version: str
    platform: str
    executable_sha256: str | None
    capabilities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        stable_id(self.backend, field="backend")
        bounded_text(self.version, field="version", maximum=128)
        bounded_text(self.platform, field="platform", maximum=128)
        if self.executable_sha256 is not None:
            sha256_hex(self.executable_sha256, field="executable_sha256")
        for item in self.capabilities:
            stable_id(item, field="capability")
        object.__setattr__(self, "capabilities", tuple(sorted(set(self.capabilities))))

    def canonical(self) -> dict[str, Any]:
        return {"backend": self.backend, "version": self.version, "platform": self.platform, "executable_sha256": self.executable_sha256, "capabilities": list(self.capabilities)}


@dataclass(frozen=True, slots=True)
class VoiceModelIdentity:
    model_sha256: str
    config_sha256: str
    locale: str
    provenance_id: str
    license_id: str
    state: MediaState = MediaState.AVAILABLE

    def __post_init__(self) -> None:
        sha256_hex(self.model_sha256, field="model_sha256")
        sha256_hex(self.config_sha256, field="config_sha256")
        if _LOCALE_RE.fullmatch(self.locale) is None:
            raise ValueError("locale is invalid")
        stable_id(self.provenance_id, field="provenance_id")
        stable_id(self.license_id, field="license_id")
        if self.state not in {MediaState.AVAILABLE, MediaState.RIGHTS_BLOCKED, MediaState.UNAVAILABLE, MediaState.STALE}:
            raise ValueError("invalid voice model state")

    def canonical(self) -> dict[str, Any]:
        return {"model_sha256": self.model_sha256, "config_sha256": self.config_sha256, "locale": self.locale.replace("_", "-"), "provenance_id": self.provenance_id, "license_id": self.license_id, "state": self.state.value}


@dataclass(frozen=True, slots=True)
class RootReference:
    kind: str
    identity: str
    sha256: str | None = None

    def __post_init__(self) -> None:
        stable_id(self.kind, field="kind")
        stable_id(self.identity, field="identity")
        if self.sha256 is not None:
            sha256_hex(self.sha256, field="sha256")

    def canonical(self) -> dict[str, Any]:
        return {"kind": self.kind, "identity": self.identity, "sha256": self.sha256}


@dataclass(frozen=True, slots=True)
class MediaProcessLimits:
    wall_time_seconds: float = 120.0
    max_stdout_bytes: int = 2 * 1024 * 1024
    max_stderr_bytes: int = 2 * 1024 * 1024
    max_result_bytes: int = 8 * 1024 * 1024
    max_output_bytes: int = 256 * 1024 * 1024

    def __post_init__(self) -> None:
        if not math.isfinite(self.wall_time_seconds) or self.wall_time_seconds <= 0:
            raise ValueError("wall_time_seconds must be finite and positive")
        for name in ("max_stdout_bytes", "max_stderr_bytes", "max_result_bytes", "max_output_bytes"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")

    def canonical(self) -> dict[str, Any]:
        return {"wall_time_seconds": self.wall_time_seconds, "max_stdout_bytes": self.max_stdout_bytes, "max_stderr_bytes": self.max_stderr_bytes, "max_result_bytes": self.max_result_bytes, "max_output_bytes": self.max_output_bytes}
