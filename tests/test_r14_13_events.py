from __future__ import annotations

from dataclasses import replace

import pytest

from kodepoia.backend.authority import AuthorityActorContext
from kodepoia.backend.contracts import BackendEnvironmentKind
from kodepoia.backend.event_pipeline import (
    ConsumerDefinition,
    EventEnvelope,
    EventFieldType,
    EventPipelineAuthorizationError,
    EventPipelineCapacityError,
    EventPipelinePolicyError,
    EventPipelineStateError,
    EventPrivacyClass,
    EventSchemaDefinition,
    EventSchemaField,
    InMemoryEventPipelineService,
    LocalEventStore,
    OpenTelemetryEventBridge,
    ReplayRequest,
    cloudevent_mapping,
)


class Clock:
    def __init__(self, value: int = 1_700_000_000_000) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value


OBJECTS = (
    "consumer.analytics",
    "consumer.dead",
    "consumer.restart",
    "production",
    "schema.gameplay",
    "schema.prod",
    "stream.gameplay",
    "stream.other",
    "stream.prod",
    "test",
)


def actor(*, permissions: tuple[str, ...] = ("*",), objects: tuple[str, ...] = OBJECTS) -> AuthorityActorContext:
    return AuthorityActorContext(
        account_id="operator",
        session_id="session-1",
        permissions=permissions,
        authorized_object_ids=objects,
    )


def schema(
    *,
    schema_id: str = "schema.gameplay",
    event_type: str = "gameplay.action",
    environment: BackendEnvironmentKind = BackendEnvironmentKind.TEST,
    max_payload_bytes: int = 4096,
) -> EventSchemaDefinition:
    return EventSchemaDefinition(
        schema_id=schema_id,
        event_type=event_type,
        version=1,
        environment=environment,
        fields=(
            EventSchemaField("action", EventFieldType.STRING, privacy=EventPrivacyClass.PUBLIC),
            EventSchemaField("score", EventFieldType.INTEGER, privacy=EventPrivacyClass.INTERNAL),
            EventSchemaField("email", EventFieldType.STRING, required=False, privacy=EventPrivacyClass.SENSITIVE),
        ),
        max_payload_bytes=max_payload_bytes,
    )


def envelope(
    event_id: str,
    source_sequence: int,
    *,
    stream_id: str = "stream.gameplay",
    schema_id: str = "schema.gameplay",
    event_type: str = "gameplay.action",
    environment: BackendEnvironmentKind = BackendEnvironmentKind.TEST,
    source: str = "server.gameplay",
    payload: dict[str, object] | None = None,
) -> EventEnvelope:
    return EventEnvelope(
        event_id=event_id,
        stream_id=stream_id,
        event_type=event_type,
        schema_id=schema_id,
        schema_version=1,
        environment=environment,
        source=source,
        source_sequence=source_sequence,
        occurred_at_ms=1_700_000_000_000 + source_sequence,
        subject_id="account.42",
        trace_id=f"{source_sequence:032x}",
        span_id=f"{source_sequence:016x}",
        payload=payload or {"action": "jump", "score": source_sequence},
    )


def service(*, store: LocalEventStore | None = None, max_replay_events: int = 8) -> tuple[InMemoryEventPipelineService, Clock]:
    clock = Clock()
    svc = InMemoryEventPipelineService(
        clock_ms=clock,
        store=store or LocalEventStore(max_schemas=16, max_events=64, max_retained_payload_bytes=64 * 1024),
        max_consumers=16,
        max_replay_events=max_replay_events,
        max_replay_records=16,
        max_dead_letters=16,
        max_trace_records=256,
    )
    return svc, clock


def register(svc: InMemoryEventPipelineService, definition: EventSchemaDefinition | None = None) -> EventSchemaDefinition:
    item = definition or schema()
    return svc.register_schema(actor(), item)


def test_schema_is_immutable_typed_and_rejects_unknown_or_wrong_fields() -> None:
    item = schema()
    assert item.digest() == replace(item).digest()
    assert item.validate_payload({"action": "jump", "score": 3})["score"] == 3
    with pytest.raises(EventPipelinePolicyError, match="unknown_payload_field"):
        item.validate_payload({"action": "jump", "score": 3, "other": True})
    with pytest.raises(EventPipelinePolicyError, match="payload_field_type_mismatch"):
        item.validate_payload({"action": "jump", "score": "3"})


def test_secret_and_high_risk_schema_fields_fail_closed() -> None:
    with pytest.raises(EventPipelinePolicyError, match="secret_payload_fields_forbidden"):
        EventSchemaField("safe_name", EventFieldType.STRING, privacy=EventPrivacyClass.SECRET)
    with pytest.raises(EventPipelinePolicyError, match="high_risk_payload_field_forbidden"):
        EventSchemaField("access_token", EventFieldType.STRING, privacy=EventPrivacyClass.PUBLIC)


def test_append_is_idempotent_and_event_id_rebind_is_rejected() -> None:
    svc, _clock = service()
    register(svc)
    first = svc.append_event(actor(), envelope("event.1", 1))
    duplicate = svc.append_event(actor(), envelope("event.1", 1))
    assert duplicate == first
    with pytest.raises(EventPipelineStateError, match="event_id_conflict"):
        svc.append_event(actor(), envelope("event.1", 2, payload={"action": "run", "score": 2}))


def test_source_sequence_out_of_order_is_rejected_without_affecting_duplicate_replay() -> None:
    svc, _clock = service()
    register(svc)
    svc.append_event(actor(), envelope("event.2", 2))
    assert svc.append_event(actor(), envelope("event.2", 2)).stream_sequence == 1
    with pytest.raises(EventPipelineStateError, match="source_sequence_out_of_order"):
        svc.append_event(actor(), envelope("event.1", 1))


def test_function_and_object_authorization_are_enforced() -> None:
    svc, _clock = service()
    restricted = actor(permissions=("events.consume",))
    with pytest.raises(EventPipelineAuthorizationError, match="forbidden"):
        svc.register_schema(restricted, schema())
    register(svc)
    no_stream = actor(objects=("schema.gameplay", "test"))
    with pytest.raises(EventPipelineAuthorizationError, match="forbidden"):
        svc.append_event(no_stream, envelope("event.1", 1))


def test_environment_isolation_rejects_schema_cross_use() -> None:
    svc, _clock = service()
    register(svc)
    prod = schema(schema_id="schema.prod", environment=BackendEnvironmentKind.PRODUCTION)
    svc.register_schema(actor(), prod)
    with pytest.raises(EventPipelineStateError, match="schema_not_found"):
        svc.append_event(
            actor(),
            envelope(
                "event.prod",
                1,
                stream_id="stream.prod",
                schema_id="schema.gameplay",
                environment=BackendEnvironmentKind.PRODUCTION,
            ),
        )


def test_at_least_once_polling_and_ordered_idempotent_acknowledgement() -> None:
    svc, clock = service()
    register(svc)
    one = svc.append_event(actor(), envelope("event.1", 1))
    two = svc.append_event(actor(), envelope("event.2", 2))
    definition = ConsumerDefinition("consumer.analytics", "stream.gameplay", BackendEnvironmentKind.TEST)
    svc.register_consumer(actor(), definition)
    assert svc.poll(actor(), definition.consumer_id, limit=2) == (one, two)
    assert svc.poll(actor(), definition.consumer_id, limit=2) == (one, two)
    with pytest.raises(EventPipelineStateError, match="acknowledgement_out_of_order"):
        svc.acknowledge(actor(), definition.consumer_id, stream_sequence=2, event_id="event.2")
    clock.value += 1
    cp1 = svc.acknowledge(actor(), definition.consumer_id, stream_sequence=1, event_id="event.1")
    assert cp1.sequence == 1
    assert svc.acknowledge(actor(), definition.consumer_id, stream_sequence=1, event_id="event.1") == cp1
    with pytest.raises(EventPipelineStateError, match="acknowledgement_rebind"):
        svc.acknowledge(actor(), definition.consumer_id, stream_sequence=1, event_id="event.2")
    assert svc.poll(actor(), definition.consumer_id) == (two,)


def test_checkpoint_can_restart_consumer_on_same_append_only_store() -> None:
    store = LocalEventStore(max_schemas=8, max_events=16, max_retained_payload_bytes=16 * 1024)
    first, _clock = service(store=store)
    register(first)
    first.append_event(actor(), envelope("event.1", 1))
    second_event = first.append_event(actor(), envelope("event.2", 2))
    definition = ConsumerDefinition("consumer.restart", "stream.gameplay", BackendEnvironmentKind.TEST)
    first.register_consumer(actor(), definition)
    checkpoint = first.acknowledge(actor(), definition.consumer_id, stream_sequence=1, event_id="event.1")

    restarted, _clock2 = service(store=store)
    restored = restarted.register_consumer(actor(), definition, checkpoint=checkpoint)
    assert restored == checkpoint
    assert restarted.poll(actor(), definition.consumer_id) == (second_event,)


def test_dead_letter_is_bounded_idempotent_and_advances_checkpoint_after_threshold() -> None:
    svc, _clock = service()
    register(svc)
    first = svc.append_event(actor(), envelope("event.1", 1))
    second = svc.append_event(actor(), envelope("event.2", 2))
    definition = ConsumerDefinition("consumer.dead", "stream.gameplay", BackendEnvironmentKind.TEST, max_delivery_attempts=3)
    svc.register_consumer(actor(), definition)
    assert svc.record_delivery_failure(actor(), definition.consumer_id, stream_sequence=1, event_id="event.1", reason_code="handler.failed") is None
    assert svc.record_delivery_failure(actor(), definition.consumer_id, stream_sequence=1, event_id="event.1", reason_code="handler.failed") is None
    dead = svc.record_delivery_failure(actor(), definition.consumer_id, stream_sequence=1, event_id="event.1", reason_code="handler.failed")
    assert dead is not None and dead.attempt_count == 3 and dead.event_digest == first.digest()
    assert svc.record_delivery_failure(actor(), definition.consumer_id, stream_sequence=1, event_id="event.1", reason_code="handler.failed") == dead
    assert svc.consumer_checkpoint(definition.consumer_id).sequence == 1
    assert svc.poll(actor(), definition.consumer_id) == (second,)


def test_replay_dry_run_and_execution_do_not_mutate_consumer_checkpoint() -> None:
    svc, _clock = service()
    register(svc)
    for index in range(1, 4):
        svc.append_event(actor(), envelope(f"event.{index}", index))
    definition = ConsumerDefinition("consumer.analytics", "stream.gameplay", BackendEnvironmentKind.TEST)
    svc.register_consumer(actor(), definition)
    before = svc.consumer_checkpoint(definition.consumer_id)
    preview_request = ReplayRequest("replay.preview", BackendEnvironmentKind.TEST, "stream.gameplay", 1, 3, True, "incident.review")
    preview, preview_events = svc.replay(actor(), preview_request)
    assert preview.executed is False and len(preview_events) == 3
    assert svc.consumer_checkpoint(definition.consumer_id) == before
    execute_request = ReplayRequest("replay.execute", BackendEnvironmentKind.TEST, "stream.gameplay", 1, 2, False, "repair.test")
    executed, events = svc.replay(actor(), execute_request)
    assert executed.executed is True and len(events) == 2
    assert svc.consumer_checkpoint(definition.consumer_id) == before
    assert svc.replay(actor(), execute_request)[0] == executed
    with pytest.raises(EventPipelineStateError, match="replay_id_conflict"):
        svc.replay(actor(), replace(execute_request, end_sequence=3))


def test_replay_event_budget_is_enforced() -> None:
    svc, _clock = service(max_replay_events=2)
    register(svc)
    for index in range(1, 4):
        svc.append_event(actor(), envelope(f"event.{index}", index))
    with pytest.raises(EventPipelineCapacityError, match="replay_event_capacity"):
        svc.replay(actor(), ReplayRequest("replay.large", BackendEnvironmentKind.TEST, "stream.gameplay", 1, 3, True, "budget.test"))


def test_retention_cannot_drop_uncheckpointed_history_then_prunes_safely() -> None:
    svc, _clock = service()
    register(svc)
    for index in range(1, 4):
        svc.append_event(actor(), envelope(f"event.{index}", index))
    definition = ConsumerDefinition("consumer.analytics", "stream.gameplay", BackendEnvironmentKind.TEST)
    svc.register_consumer(actor(), definition)
    with pytest.raises(EventPipelineStateError, match="retention_would_drop_uncheckpointed"):
        svc.prune_retention(actor(), environment=BackendEnvironmentKind.TEST, stream_id="stream.gameplay", before_sequence=3)
    svc.acknowledge(actor(), definition.consumer_id, stream_sequence=1, event_id="event.1")
    svc.acknowledge(actor(), definition.consumer_id, stream_sequence=2, event_id="event.2")
    removed, removed_bytes = svc.prune_retention(actor(), environment=BackendEnvironmentKind.TEST, stream_id="stream.gameplay", before_sequence=3)
    assert removed == 2 and removed_bytes > 0
    assert tuple(item.envelope.event_id for item in svc.poll(actor(), definition.consumer_id)) == ("event.3",)


def test_pruned_event_identity_cannot_be_reused() -> None:
    svc, _clock = service()
    register(svc)
    svc.append_event(actor(), envelope("event.1", 1))
    svc.prune_retention(actor(), environment=BackendEnvironmentKind.TEST, stream_id="stream.gameplay", before_sequence=2)
    with pytest.raises(EventPipelineStateError, match="event_already_pruned"):
        svc.append_event(actor(), envelope("event.1", 1))


def test_otel_bridge_redacts_sensitive_payload_and_hashes_subject() -> None:
    svc, _clock = service()
    item = register(svc)
    stored = svc.append_event(
        actor(),
        envelope("event.1", 1, payload={"action": "login", "score": 7, "email": "person@example.invalid"}),
    )
    exported = OpenTelemetryEventBridge().export(item, stored)
    assert exported.body["email"] == "[REDACTED]"
    rendered = str(exported.canonical())
    assert "person@example.invalid" not in rendered
    assert "account.42" not in rendered
    assert exported.attributes["subject.sha256"]
    assert exported.trace_id == stored.envelope.trace_id


def test_cloudevent_mapping_is_stable_v1_shape() -> None:
    svc, _clock = service()
    register(svc)
    stored = svc.append_event(actor(), envelope("event.1", 1))
    mapped = cloudevent_mapping(stored)
    assert mapped["specversion"] == "1.0"
    assert mapped["id"] == "event.1"
    assert mapped["source"] == "urn:kodepoia:server.gameplay"
    assert mapped["type"] == "gameplay.action"
    assert mapped["dataschema"] == "urn:kodepoia:event-schema:schema.gameplay:1"
    assert mapped["data"] == {"action": "jump", "score": 1}


def test_schema_event_and_payload_capacities_fail_closed() -> None:
    tiny_store = LocalEventStore(max_schemas=1, max_events=1, max_retained_payload_bytes=64)
    svc, _clock = service(store=tiny_store)
    register(svc, schema(max_payload_bytes=64))
    with pytest.raises(EventPipelineCapacityError, match="schema_capacity"):
        svc.register_schema(actor(), schema(schema_id="schema.prod", environment=BackendEnvironmentKind.PRODUCTION))
    svc.append_event(actor(), envelope("event.1", 1, payload={"action": "x", "score": 1}))
    with pytest.raises(EventPipelineCapacityError, match="event_capacity|retained_payload_capacity"):
        svc.append_event(actor(), envelope("event.2", 2, payload={"action": "y", "score": 2}))


def test_state_snapshot_and_evidence_are_redacted_and_deterministic() -> None:
    svc, _clock = service()
    register(svc)
    svc.append_event(actor(), envelope("event.1", 1, payload={"action": "login", "score": 7, "email": "person@example.invalid"}))
    state = svc.state_snapshot()
    assert state.digest() == svc.state_snapshot().digest()
    evidence = svc.redacted_evidence()
    assert evidence["provider_live_claim"] is False
    assert evidence["secrets_exposed"] is False
    assert evidence["pii_exposed"] is False
    assert evidence["raw_payloads_exposed"] is False
    assert "person@example.invalid" not in str(evidence)
