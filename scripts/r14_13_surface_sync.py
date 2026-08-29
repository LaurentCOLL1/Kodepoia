from pathlib import Path

init_path = Path("src/kodepoia/backend/__init__.py")
text = init_path.read_text(encoding="utf-8")

import_anchor = "from .governance import (\n"
assert text.count(import_anchor) == 1, text.count(import_anchor)
assert "from .event_pipeline import (" not in text

import_block = """from .event_pipeline import (
    ConsumerCheckpoint,
    ConsumerDefinition,
    DeadLetterRecord,
    EventEnvelope,
    EventFieldType,
    EventPipelineAuthorizationError,
    EventPipelineCapacityError,
    EventPipelinePolicyError,
    EventPipelineStateError,
    EventPipelineStateSnapshot,
    EventPrivacyClass,
    EventSchemaDefinition,
    EventSchemaField,
    InMemoryEventPipelineService,
    LocalEventStore,
    OpenTelemetryEventBridge,
    OpenTelemetryEventRecord,
    ReplayRecord,
    ReplayRequest,
    StoredEvent,
    cloudevent_mapping,
)
"""
text = text.replace(import_anchor, import_block + import_anchor)

all_anchor = '    "InMemoryMatchmakingService",\n'
assert text.count(all_anchor) == 1, text.count(all_anchor)
exports = """    "ConsumerCheckpoint",
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
"""
for name in (
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
):
    assert f'    "{name}",\n' not in text, name
text = text.replace(all_anchor, exports + all_anchor)
init_path.write_text(text, encoding="utf-8")
