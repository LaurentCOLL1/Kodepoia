from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping

_STABLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _stable_id(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _STABLE_ID_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be a stable identifier")
    return value


def _bounded_text(value: str, *, field: str, maximum: int = 512) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or "\x00" in value:
        raise ValueError(f"{field} must be non-empty, bounded text")
    return value


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    try:
        text = json.dumps(
            dict(payload),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("desktop canonical payload is not serializable") from exc
    return text.encode("utf-8")


def canonical_sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


class DesktopFramework(StrEnum):
    WPF = "wpf"
    WINUI3 = "winui3"
    AVALONIA = "avalonia"
    QT6 = "qt6"
    TAURI2 = "tauri2"


class DesktopOS(StrEnum):
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"


class DesktopArchitecture(StrEnum):
    X64 = "x64"
    ARM64 = "arm64"
    X86 = "x86"


class DesktopPackageKind(StrEnum):
    UNPACKAGED = "unpackaged"
    MSIX = "msix"
    MSI = "msi"
    ARCHIVE = "archive"


class DesktopToolKind(StrEnum):
    DOTNET = "dotnet"
    MSBUILD = "msbuild"
    CMAKE = "cmake"
    QT_PATHS = "qt_paths"
    CARGO = "cargo"
    RUSTC = "rustc"


class DesktopCapabilityState(StrEnum):
    NOT_PROBED = "NOT_PROBED"
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    UNSUPPORTED = "UNSUPPORTED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class DesktopTargetProfile:
    profile_id: str
    framework: DesktopFramework
    targets: tuple[DesktopOS, ...]
    architecture: DesktopArchitecture = DesktopArchitecture.X64
    package_kind: DesktopPackageKind = DesktopPackageKind.UNPACKAGED

    def __post_init__(self) -> None:
        _stable_id(self.profile_id, field="profile_id")
        normalized = tuple(sorted(set(self.targets), key=lambda item: item.value))
        if not normalized:
            raise ValueError("targets must contain at least one desktop OS")
        object.__setattr__(self, "targets", normalized)

        if self.framework in {DesktopFramework.WPF, DesktopFramework.WINUI3} and normalized != (
            DesktopOS.WINDOWS,
        ):
            raise ValueError(f"{self.framework.value} targets Windows only")
        if self.package_kind is DesktopPackageKind.MSIX and DesktopOS.WINDOWS not in normalized:
            raise ValueError("MSIX requires a Windows target")
        if self.package_kind is DesktopPackageKind.MSI and DesktopOS.WINDOWS not in normalized:
            raise ValueError("MSI requires a Windows target")

    def canonical(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "framework": self.framework.value,
            "targets": [item.value for item in self.targets],
            "architecture": self.architecture.value,
            "package_kind": self.package_kind.value,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class DesktopToolchainIdentity:
    tool_kind: DesktopToolKind
    executable_name: str
    executable_sha256: str
    version: str
    platform: DesktopOS
    architecture: DesktopArchitecture
    capabilities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _bounded_text(self.executable_name, field="executable_name", maximum=128)
        if _SHA256_RE.fullmatch(self.executable_sha256) is None:
            raise ValueError("executable_sha256 must be lowercase SHA-256")
        _bounded_text(self.version, field="version", maximum=128)
        normalized = tuple(sorted(set(self.capabilities)))
        if len(normalized) > 64:
            raise ValueError("capabilities must contain at most 64 entries")
        for item in normalized:
            _stable_id(item, field="capability")
        object.__setattr__(self, "capabilities", normalized)

    def canonical(self) -> dict[str, Any]:
        return {
            "tool_kind": self.tool_kind.value,
            "executable_name": self.executable_name,
            "executable_sha256": self.executable_sha256,
            "version": self.version,
            "platform": self.platform.value,
            "architecture": self.architecture.value,
            "capabilities": list(self.capabilities),
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class DesktopCapabilityReport:
    adapter_id: str
    state: DesktopCapabilityState
    toolchain: DesktopToolchainIdentity | None = None
    capabilities: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _stable_id(self.adapter_id, field="adapter_id")
        capabilities = tuple(sorted(set(self.capabilities)))
        blockers = tuple(sorted(set(self.blockers)))
        if len(capabilities) > 64 or len(blockers) > 64:
            raise ValueError("capability report entries are not bounded")
        for item in capabilities:
            _stable_id(item, field="capability")
        for item in blockers:
            _stable_id(item, field="blocker")

        if self.state is DesktopCapabilityState.AVAILABLE:
            if self.toolchain is None:
                raise ValueError("AVAILABLE requires a toolchain identity")
            if blockers:
                raise ValueError("AVAILABLE cannot contain blockers")
        elif self.state is DesktopCapabilityState.NOT_PROBED and self.toolchain is not None:
            raise ValueError("NOT_PROBED cannot contain a probed toolchain identity")
        elif self.state in {
            DesktopCapabilityState.UNAVAILABLE,
            DesktopCapabilityState.UNSUPPORTED,
            DesktopCapabilityState.BLOCKED,
            DesktopCapabilityState.FAILED,
        } and not blockers:
            raise ValueError(f"{self.state.value} requires at least one blocker")

        object.__setattr__(self, "capabilities", capabilities)
        object.__setattr__(self, "blockers", blockers)

    def canonical(self) -> dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "state": self.state.value,
            "toolchain": None if self.toolchain is None else self.toolchain.canonical(),
            "capabilities": list(self.capabilities),
            "blockers": list(self.blockers),
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())
