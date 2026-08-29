from __future__ import annotations

import kodepoia.backend as backend


EXPECTED = (
    "CatalogProductReference",
    "ConfigSnapshotReference",
    "ContentManifestReference",
    "EventContractReference",
    "InMemoryLiveOpsService",
    "LiveOpsActivationRecord",
    "LiveOpsApproval",
    "LiveOpsAudience",
    "LiveOpsAudienceResult",
    "LiveOpsAuditRecord",
    "LiveOpsAuthorizationError",
    "LiveOpsCampaignDefinition",
    "LiveOpsCampaignState",
    "LiveOpsCapacityError",
    "LiveOpsPolicyError",
    "LiveOpsPreview",
    "LiveOpsRotation",
    "LiveOpsRuntimeRecord",
    "LiveOpsScheduleWindow",
    "LiveOpsSeasonDefinition",
    "LiveOpsSeasonReference",
    "LiveOpsStateError",
    "LiveOpsStateSnapshot",
)


def test_liveops_public_exports_are_available() -> None:
    for name in EXPECTED:
        assert hasattr(backend, name), name
        assert name in backend.__all__, name
