"""Governed desktop-application contracts and boundaries for R12."""

from .app_model import (
    AdapterConformanceProjection, CommandContract, DesktopAppModel, DialogContract,
    DialogKind, RouteContract, ServiceContract, ServiceLifetime, StateField,
    StateValueKind, ValidationKind, ValidationRule, ViewContract, ViewModelContract,
    canonical_sample_app,
)
from .boundary import DesktopBoundaryError, DesktopToolchainBoundary, validate_environment_overrides
from .contracts import (
    DesktopArchitecture, DesktopCapabilityReport, DesktopCapabilityState,
    DesktopFramework, DesktopOS, DesktopPackageKind, DesktopTargetProfile,
    DesktopToolKind, DesktopToolchainIdentity, canonical_sha256,
)
from .scaffold import (
    DesktopScaffoldEngine, DesktopTemplateManifest, FileOwnership, PreviewAction,
    RenderedFile, ScaffoldLineage, ScaffoldPreview, TemplateFile, TemplateValue,
    TemplateValueKind, WorkspaceManifest,
)
from .wpf import WpfAcceptanceResult, WpfAdapter, WpfArtifact, write_wpf_acceptance_report

__all__ = [
    "AdapterConformanceProjection", "CommandContract", "DesktopAppModel",
    "DesktopArchitecture", "DesktopBoundaryError", "DesktopCapabilityReport",
    "DesktopCapabilityState", "DesktopFramework", "DesktopOS", "DesktopPackageKind",
    "DesktopScaffoldEngine", "DesktopTargetProfile", "DesktopTemplateManifest",
    "DesktopToolKind", "DesktopToolchainBoundary", "DesktopToolchainIdentity",
    "DialogContract", "DialogKind", "FileOwnership", "PreviewAction", "RenderedFile",
    "RouteContract", "ScaffoldLineage", "ScaffoldPreview", "ServiceContract",
    "ServiceLifetime", "StateField", "StateValueKind", "TemplateFile", "TemplateValue",
    "TemplateValueKind", "ValidationKind", "ValidationRule", "ViewContract",
    "ViewModelContract", "WorkspaceManifest", "WpfAcceptanceResult", "WpfAdapter",
    "WpfArtifact", "canonical_sample_app", "canonical_sha256",
    "validate_environment_overrides", "write_wpf_acceptance_report",
]
