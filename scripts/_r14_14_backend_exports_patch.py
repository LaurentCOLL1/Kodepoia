from pathlib import Path

path = Path('src/kodepoia/backend/__init__.py')
text = path.read_text(encoding='utf-8')
if 'InMemoryLiveOpsService' in text:
    raise SystemExit('LiveOps exports already present')

import_anchor = '''from .local_config import (\n    BackendConfigOverlay,\n    BackendLocalConfig,\n    BackendLogLevel,\n    local_config_from_runtime_intents,\n)\nfrom .matchmaking import (\n'''
import_replacement = '''from .local_config import (\n    BackendConfigOverlay,\n    BackendLocalConfig,\n    BackendLogLevel,\n    local_config_from_runtime_intents,\n)\nfrom .liveops import (\n    CatalogProductReference,\n    ConfigSnapshotReference,\n    ContentManifestReference,\n    EventContractReference,\n    InMemoryLiveOpsService,\n    LiveOpsActivationRecord,\n    LiveOpsApproval,\n    LiveOpsAudience,\n    LiveOpsAudienceResult,\n    LiveOpsAuditRecord,\n    LiveOpsAuthorizationError,\n    LiveOpsCampaignDefinition,\n    LiveOpsCampaignState,\n    LiveOpsCapacityError,\n    LiveOpsPolicyError,\n    LiveOpsPreview,\n    LiveOpsRotation,\n    LiveOpsRuntimeRecord,\n    LiveOpsScheduleWindow,\n    LiveOpsSeasonDefinition,\n    LiveOpsSeasonReference,\n    LiveOpsStateError,\n    LiveOpsStateSnapshot,\n)\nfrom .matchmaking import (\n'''
if text.count(import_anchor) != 1:
    raise SystemExit('import anchor mismatch')
text = text.replace(import_anchor, import_replacement)

all_anchor = '''    "BackendScaffoldEngine",\n    "BackendWorkspaceManifest",\n    "PostgresAdapter",\n'''
all_replacement = '''    "BackendScaffoldEngine",\n    "BackendWorkspaceManifest",\n    "CatalogProductReference",\n    "ConfigSnapshotReference",\n    "ContentManifestReference",\n    "EventContractReference",\n    "InMemoryLiveOpsService",\n    "LiveOpsActivationRecord",\n    "LiveOpsApproval",\n    "LiveOpsAudience",\n    "LiveOpsAudienceResult",\n    "LiveOpsAuditRecord",\n    "LiveOpsAuthorizationError",\n    "LiveOpsCampaignDefinition",\n    "LiveOpsCampaignState",\n    "LiveOpsCapacityError",\n    "LiveOpsPolicyError",\n    "LiveOpsPreview",\n    "LiveOpsRotation",\n    "LiveOpsRuntimeRecord",\n    "LiveOpsScheduleWindow",\n    "LiveOpsSeasonDefinition",\n    "LiveOpsSeasonReference",\n    "LiveOpsStateError",\n    "LiveOpsStateSnapshot",\n    "PostgresAdapter",\n'''
if text.count(all_anchor) != 1:
    raise SystemExit('__all__ anchor mismatch')
text = text.replace(all_anchor, all_replacement)
path.write_text(text, encoding='utf-8')
