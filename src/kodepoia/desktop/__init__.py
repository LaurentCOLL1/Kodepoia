"""Governed desktop-application contracts and boundaries for R12."""

from .app_model import (
    AdapterConformanceProjection, CommandContract, DesktopAppModel, DialogContract,
    DialogKind, RouteContract, ServiceContract, ServiceLifetime, StateField,
    StateValueKind, ValidationKind, ValidationRule, ViewContract, ViewModelContract,
    canonical_sample_app,
)
from .async_runtime import (
    AsyncOperationDescriptor, AsyncOperationHandle, AsyncOperationKind,
    AsyncOperationRuntime, AsyncPolicy, CallbackLease, CancellationToken,
    CompletionGate, DispatcherBinding, DoubleCompletionError, OperationContext,
    OperationState, OperationTimeoutError, OwnerState, ProgressReporter,
    ProgressSnapshot, QueueCapacityError, StaleCallbackError, ThreadAffinity,
    UiThreadAffinityError, UiThreadDispatcher, canonical_dispatcher_binding,
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
from .ipc import (
    IpcAuthenticationError, IpcAuthorizationError, IpcAuthorizationPolicy,
    IpcEndpointClosedError, IpcEndpointIdentity, IpcEnvelope, IpcFrameTooLargeError,
    IpcMessageKind, IpcPeerIdentity, IpcPolicy, IpcProtocolError, IpcReplayError,
    IpcStaleVersionError, IpcTransportKind, LocalIpcEndpoint, ReplayWindow,
    canonical_local_transport, decode_frame, encode_frame, generate_auth_key,
    receive_envelope, send_envelope,
)
from .persistence import (
    ColumnDefinition, ComparisonOperator, DatabaseState, DatabaseStatus,
    ForeignKeyDefinition, MigrationGraph, MigrationOperation, MigrationOperationKind,
    MigrationPlan, MigrationStep, PersistenceGovernance, QueryFilter, QueryIntent,
    QueryOperation, SQLitePersistenceService, SQLitePolicy, SQLiteValueType,
    SchemaDefinition, TableDefinition,
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
from .tauri2 import (
    Tauri2Adapter, TauriAcceptanceResult, TauriArtifact, TauriDependencyDeclaration,
    TauriGeneratedFile, TauriKitIdentity, TauriLicenseState, TauriProjectManifest,
    TauriToolchainDiscovery, write_tauri_acceptance_report,
)
from .winui3 import (
    WinUi3Adapter, WinUiAcceptanceResult, WinUiArtifact, WinUiDeploymentContract,
    WinUiDeploymentMode, canonical_winui_deployment, write_winui_acceptance_report,
)
from .wpf import WpfAcceptanceResult, WpfAdapter, WpfArtifact, write_wpf_acceptance_report

__all__ = [
    "AdapterConformanceProjection", "AsyncOperationDescriptor", "AsyncOperationHandle",
    "AsyncOperationKind", "AsyncOperationRuntime", "AsyncPolicy", "AvaloniaAcceptanceResult",
    "AvaloniaAdapter", "AvaloniaArtifact", "AvaloniaTargetMatrix", "CallbackLease",
    "CancellationToken", "ColumnDefinition", "CommandContract", "ComparisonOperator",
    "CompletionGate", "DatabaseState", "DatabaseStatus", "DesktopAppModel",
    "DesktopArchitecture", "DesktopBoundaryError", "DesktopCapabilityReport",
    "DesktopCapabilityState", "DesktopFramework", "DesktopOS", "DesktopPackageKind",
    "DesktopScaffoldEngine", "DesktopTargetProfile", "DesktopTemplateManifest",
    "DesktopToolKind", "DesktopToolchainBoundary", "DesktopToolchainIdentity",
    "DialogContract", "DialogKind", "DispatcherBinding", "DoubleCompletionError",
    "FileOwnership", "ForeignKeyDefinition", "IpcAuthenticationError",
    "IpcAuthorizationError", "IpcAuthorizationPolicy", "IpcEndpointClosedError",
    "IpcEndpointIdentity", "IpcEnvelope", "IpcFrameTooLargeError", "IpcMessageKind",
    "IpcPeerIdentity", "IpcPolicy", "IpcProtocolError", "IpcReplayError",
    "IpcStaleVersionError", "IpcTransportKind", "LocalIpcEndpoint", "MigrationGraph",
    "MigrationOperation", "MigrationOperationKind", "MigrationPlan", "MigrationStep",
    "OperationContext", "OperationState", "OperationTimeoutError", "OwnerState",
    "PersistenceGovernance", "PreviewAction", "ProgressReporter", "ProgressSnapshot",
    "Qt6Adapter", "QtAcceptanceResult", "QtArtifact", "QtDependencyDeclaration",
    "QtGeneratedFile", "QtKitIdentity", "QtLicenseState", "QtProjectManifest",
    "QueryFilter", "QueryIntent", "QueryOperation", "QueueCapacityError", "RenderedFile",
    "ReplayWindow", "RouteContract", "SQLitePersistenceService", "SQLitePolicy",
    "SQLiteValueType", "ScaffoldLineage", "ScaffoldPreview", "SchemaDefinition",
    "ServiceContract", "ServiceLifetime", "StaleCallbackError", "StateField",
    "StateValueKind", "TableDefinition", "Tauri2Adapter", "TauriAcceptanceResult",
    "TauriArtifact", "TauriDependencyDeclaration", "TauriGeneratedFile",
    "TauriKitIdentity", "TauriLicenseState", "TauriProjectManifest",
    "TauriToolchainDiscovery", "TemplateFile", "TemplateValue", "TemplateValueKind",
    "ThreadAffinity", "UiThreadAffinityError", "UiThreadDispatcher", "ValidationKind",
    "ValidationRule", "ViewContract", "ViewModelContract", "WinUi3Adapter",
    "WinUiAcceptanceResult", "WinUiArtifact", "WinUiDeploymentContract",
    "WinUiDeploymentMode", "WorkspaceManifest", "WpfAcceptanceResult", "WpfAdapter",
    "WpfArtifact", "canonical_avalonia_matrix", "canonical_dispatcher_binding",
    "canonical_local_transport", "canonical_sample_app", "canonical_sha256",
    "canonical_winui_deployment", "decode_frame", "encode_frame", "generate_auth_key",
    "receive_envelope", "send_envelope", "validate_environment_overrides",
    "write_avalonia_acceptance_report", "write_qt_acceptance_report",
    "write_tauri_acceptance_report", "write_winui_acceptance_report",
    "write_wpf_acceptance_report",
]
