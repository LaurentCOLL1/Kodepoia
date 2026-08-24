"""Governed desktop-application contracts and boundaries for R12."""

from .boundary import DesktopBoundaryError, DesktopToolchainBoundary, validate_environment_overrides
from .contracts import (
    DesktopArchitecture,
    DesktopCapabilityReport,
    DesktopCapabilityState,
    DesktopFramework,
    DesktopOS,
    DesktopPackageKind,
    DesktopTargetProfile,
    DesktopToolKind,
    DesktopToolchainIdentity,
    canonical_sha256,
)

__all__ = [
    "DesktopArchitecture",
    "DesktopBoundaryError",
    "DesktopCapabilityReport",
    "DesktopCapabilityState",
    "DesktopFramework",
    "DesktopOS",
    "DesktopPackageKind",
    "DesktopTargetProfile",
    "DesktopToolKind",
    "DesktopToolchainBoundary",
    "DesktopToolchainIdentity",
    "canonical_sha256",
    "validate_environment_overrides",
]
