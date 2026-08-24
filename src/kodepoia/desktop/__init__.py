"""Governed desktop-application contracts and boundaries for R12."""

from .app_model import (
    AdapterConformanceProjection, CommandContract, DesktopAppModel, DialogContract,
    DialogKind, RouteContract, ServiceContract, ServiceLifetime, StateField,
    StateValueKind, ValidationKind, ValidationRule, ViewContract, ViewModelContract,
    canonical_sample_app,
)
from .avalonia import (
    AvaloniaAcceptanceResult, AvaloniaAdapter, AvaloniaArtifact, AvaloniaTargetMatrix,
    canonical_avalonia_matrix, write_avalonia_acceptance_report,
)
from .boundary import DesktopBoundaryError, DesktopToolchainBoundary, validate_environment_overrides
from .contracts import (
    DesktopArchitecture, DesktopCapabilityReport, DesktopCapabilityState,
    DesktopFramework, DesktopOS, DesktopPackageKind, DesktopTargetProfile,
    DesktopToolKind, DesktopToolchainIdentity, canonical_sha256,
)
from .qt6 import (
    Qt6Adapter, QtAcceptanceResult, QtArtifact, QtDependencyDeclaration,
    QtGeneratedFile, QtKitIdentity, QtLicenseState, QtProjectManifest,
    write_qt_acceptance_report,
)
from .scaffold import (
    DesktopScaffoldEngine, DesktopTemplateManifest, FileOwnership, PreviewAction,
    RenderedFile, ScaffoldLineage, ScaffoldPreview, TemplateFile, TemplateValue,
    TemplateValueKind, WorkspaceManifest,
)
from .winui3 import (
    WinUi3Adapter, WinUiAcceptanceResult, WinUiArtifact, WinUiDeploymentContract,
    WinUiDeploymentMode, canonical_winui_deployment, write_winui_acceptance_report,
)
from .wpf import WpfAcceptanceResult, WpfAdapter, WpfArtifact, write_wpf_acceptance_report

__all__ = [
    "AdapterConformanceProjection", "AvaloniaAcceptanceResult", "AvaloniaAdapter",
    "AvaloniaArtifact", "AvaloniaTargetMatrix", "CommandContract", "DesktopAppModel",
    "DesktopArchitecture", "DesktopBoundaryError", "DesktopCapabilityReport",
    "DesktopCapabilityState", "DesktopFramework", "DesktopOS", "DesktopPackageKind",
    "DesktopScaffoldEngine", "DesktopTargetProfile", "DesktopTemplateManifest",
    "DesktopToolKind", "DesktopToolchainBoundary", "DesktopToolchainIdentity",
    "DialogContract", "DialogKind", "FileOwnership", "PreviewAction", "Qt6Adapter",
    "QtAcceptanceResult", "QtArtifact", "QtDependencyDeclaration", "QtGeneratedFile",
    "QtKitIdentity", "QtLicenseState", "QtProjectManifest", "RenderedFile",
    "RouteContract", "ScaffoldLineage", "ScaffoldPreview", "ServiceContract",
    "ServiceLifetime", "StateField", "StateValueKind", "TemplateFile", "TemplateValue",
    "TemplateValueKind", "ValidationKind", "ValidationRule", "ViewContract",
    "ViewModelContract", "WinUi3Adapter", "WinUiAcceptanceResult", "WinUiArtifact",
    "WinUiDeploymentContract", "WinUiDeploymentMode", "WorkspaceManifest",
    "WpfAcceptanceResult", "WpfAdapter", "WpfArtifact", "canonical_avalonia_matrix",
    "canonical_sample_app", "canonical_sha256", "canonical_winui_deployment",
    "validate_environment_overrides", "write_avalonia_acceptance_report",
    "write_qt_acceptance_report", "write_winui_acceptance_report",
    "write_wpf_acceptance_report",
]
