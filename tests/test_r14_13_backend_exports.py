from __future__ import annotations

import kodepoia.backend as backend


EXPECTED = (
    "ConsumerCheckpoint",
    "ConsumerDefinition",
    "DeadLetterRecord",
    "EventEnvelope",
    "EventFieldType",
    "EventPipelineAuthorizationError",
    "EventPipelineCapacityError",
    "EventPipelinePolicyError",
    "EventPipelineStateError",
    "EventPipelineStateSnapshot",
    "EventPrivacyClass",
    "EventSchemaDefinition",
    "EventSchemaField",
    "InMemoryEventPipelineService",
    "LocalEventStore",
    "OpenTelemetryEventBridge",
    "OpenTelemetryEventRecord",
    "ReplayRecord",
    "ReplayRequest",
    "StoredEvent",
    "cloudevent_mapping",
)


def test_event_pipeline_public_exports_are_available() -> None:
    for name in EXPECTED:
        assert hasattr(backend, name), name
        assert name in backend.__all__, name
