from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

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


AUTHORIZED_OBJECTS = (
    "consumer.analytics",
    "consumer.dead",
    "consumer.restart",
    "schema.gameplay",
    "schema.prod",
    "stream.gameplay",
    "stream.prod",
    "test",
    "production",
)


def actor(
    *,
    permissions: tuple[str, ...] = ("*",),
    objects: tuple[str, ...] = AUTHORIZED_OBJECTS,
) -> AuthorityActorContext:
    return AuthorityActorContext(
        account_id="acceptance-operator",
        session_id="acceptance-session",
        permissions=permissions,
        authorized_object_ids=objects,
    )


def schema(
    *,
    schema_id: str = "schema.gameplay",
    environment: BackendEnvironmentKind = BackendEnvironmentKind.TEST,
    max_payload_bytes: int = 4096,
) -> EventSchemaDefinition:
    return EventSchemaDefinition(
        schema_id=schema_id,
        event_type="gameplay.action",
        version=1,
        environment=environment,
        fields=(
            EventSchemaField("action", EventFieldType.STRING, privacy=EventPrivacyClass.PUBLIC),
            EventSchemaField("score", EventFieldType.INTEGER, privacy=EventPrivacyClass.INTERNAL),
            EventSchemaField(
                "email",
                EventFieldType.STRING,
                required=False,
                privacy=EventPrivacyClass.SENSITIVE,
            ),
        ),
        max_payload_bytes=max_payload_bytes,
    )


def envelope(
    event_id: str,
    source_sequence: int,
    *,
    stream_id: str = "stream.gameplay",
    schema_id: str = "schema.gameplay",
    environment: BackendEnvironmentKind = BackendEnvironmentKind.TEST,
    payload: dict[str, object] | None = None,
) -> EventEnvelope:
    return EventEnvelope(
        event_id=event_id,
        stream_id=stream_id,
        event_type="gameplay.action",
        schema_id=schema_id,
        schema_version=1,
        environment=environment,
        source="server.gameplay",
        source_sequence=source_sequence,
        occurred_at_ms=1_700_000_000_000 + source_sequence,
        subject_id="account.42",
        trace_id=f"{source_sequence:032x}",
        span_id=f"{source_sequence:016x}",
        payload=payload or {"action": "jump", "score": source_sequence},
    )


def expected_exception(
    exc_type: type[BaseException],
    fn,
    text: str | None = None,
) -> bool:
    try:
        fn()
    except exc_type as exc:
        return text is None or text in str(exc)
    return False


def run(source_sha: str) -> dict[str, object]:
    if len(source_sha) != 40 or any(char not in "0123456789abcdef" for char in source_sha):
        raise ValueError("source_sha must be a lowercase 40-character Git SHA")

    clock = Clock()
    store = LocalEventStore(
        max_schemas=16,
        max_events=64,
        max_retained_payload_bytes=64 * 1024,
    )
    service = InMemoryEventPipelineService(
        clock_ms=clock,
        store=store,
        max_consumers=16,
        max_replay_events=8,
        max_replay_records=16,
        max_dead_letters=16,
        max_trace_records=256,
    )
    who = actor()
    definition = schema()
    service.register_schema(who, definition)

    checks: dict[str, bool] = {}
    checks["immutable_schema_identity"] = definition.digest() == replace(definition).digest()
    checks["secret_field_rejected"] = expected_exception(
        EventPipelinePolicyError,
        lambda: EventSchemaField(
            "safe_name",
            EventFieldType.STRING,
            privacy=EventPrivacyClass.SECRET,
        ),
        "secret_payload_fields_forbidden",
    )
    checks["credential_field_rejected"] = expected_exception(
        EventPipelinePolicyError,
        lambda: EventSchemaField(
            "access_token",
            EventFieldType.STRING,
            privacy=EventPrivacyClass.PUBLIC,
        ),
        "high_risk_payload_field_forbidden",
    )
    checks["unknown_payload_field_rejected"] = expected_exception(
        EventPipelinePolicyError,
        lambda: definition.validate_payload(
            {"action": "jump", "score": 1, "unexpected": True}
        ),
        "unknown_payload_field",
    )

    first_envelope = envelope(
        "event.1",
        1,
        payload={
            "action": "login",
            "score": 7,
            "email": "person@example.invalid",
        },
    )
    first = service.append_event(who, first_envelope)
    second = service.append_event(who, envelope("event.2", 2))
    third = service.append_event(who, envelope("event.3", 3))
    checks["immutable_event_identity"] = first.digest() == service.append_event(
        who, first_envelope
    ).digest()
    checks["duplicate_deduped"] = service.store.latest_sequence(
        BackendEnvironmentKind.TEST, "stream.gameplay"
    ) == 3
    checks["event_id_rebind_rejected"] = expected_exception(
        EventPipelineStateError,
        lambda: service.append_event(
            who,
            envelope(
                "event.1",
                4,
                payload={"action": "run", "score": 4},
            ),
        ),
        "event_id_conflict",
    )
    checks["source_out_of_order_rejected"] = expected_exception(
        EventPipelineStateError,
        lambda: service.append_event(who, envelope("event.old", 2)),
        "source_sequence_out_of_order",
    )

    restricted = actor(permissions=("events.consume",))
    checks["function_authorization"] = expected_exception(
        EventPipelineAuthorizationError,
        lambda: service.register_schema(restricted, schema(schema_id="schema.prod")),
        "forbidden",
    )
    no_stream = actor(objects=("schema.gameplay", "test"))
    checks["object_authorization"] = expected_exception(
        EventPipelineAuthorizationError,
        lambda: service.append_event(no_stream, envelope("event.object", 5)),
        "forbidden",
    )
    checks["environment_isolation"] = expected_exception(
        EventPipelineStateError,
        lambda: service.append_event(
            who,
            envelope(
                "event.prod",
                1,
                stream_id="stream.prod",
                schema_id="schema.gameplay",
                environment=BackendEnvironmentKind.PRODUCTION,
            ),
        ),
        "schema_not_found",
    )

    analytics = ConsumerDefinition(
        "consumer.analytics",
        "stream.gameplay",
        BackendEnvironmentKind.TEST,
    )
    service.register_consumer(who, analytics)
    first_poll = service.poll(who, analytics.consumer_id, limit=3)
    second_poll = service.poll(who, analytics.consumer_id, limit=3)
    checks["at_least_once_redelivery"] = first_poll == second_poll == (
        first,
        second,
        third,
    )
    checks["ordered_checkpoint_ack"] = (
        expected_exception(
            EventPipelineStateError,
            lambda: service.acknowledge(
                who,
                analytics.consumer_id,
                stream_sequence=2,
                event_id="event.2",
            ),
            "acknowledgement_out_of_order",
        )
        and service.acknowledge(
            who,
            analytics.consumer_id,
            stream_sequence=1,
            event_id="event.1",
        ).sequence
        == 1
        and service.acknowledge(
            who,
            analytics.consumer_id,
            stream_sequence=1,
            event_id="event.1",
        ).sequence
        == 1
        and expected_exception(
            EventPipelineStateError,
            lambda: service.acknowledge(
                who,
                analytics.consumer_id,
                stream_sequence=1,
                event_id="event.2",
            ),
            "acknowledgement_rebind",
        )
    )
    clock.value += 1
    analytics_cp = service.acknowledge(
        who,
        analytics.consumer_id,
        stream_sequence=2,
        event_id="event.2",
    )

    restarted = InMemoryEventPipelineService(
        clock_ms=clock,
        store=store,
        max_consumers=16,
        max_replay_events=8,
        max_replay_records=16,
        max_dead_letters=16,
        max_trace_records=256,
    )
    restart_definition = ConsumerDefinition(
        "consumer.restart",
        "stream.gameplay",
        BackendEnvironmentKind.TEST,
    )
    restart_checkpoint = replace(
        analytics_cp,
        consumer_id="consumer.restart",
    )
    restored = restarted.register_consumer(
        who,
        restart_definition,
        checkpoint=restart_checkpoint,
    )
    checks["restart_checkpoint_restore"] = (
        restored.sequence == 2
        and restarted.poll(who, restart_definition.consumer_id) == (third,)
    )

    dead = ConsumerDefinition(
        "consumer.dead",
        "stream.gameplay",
        BackendEnvironmentKind.TEST,
        max_delivery_attempts=3,
    )
    service.register_consumer(who, dead)
    dead_first = service.record_delivery_failure(
        who,
        dead.consumer_id,
        stream_sequence=1,
        event_id="event.1",
        reason_code="handler.failed",
    )
    dead_second = service.record_delivery_failure(
        who,
        dead.consumer_id,
        stream_sequence=1,
        event_id="event.1",
        reason_code="handler.failed",
    )
    dead_record = service.record_delivery_failure(
        who,
        dead.consumer_id,
        stream_sequence=1,
        event_id="event.1",
        reason_code="handler.failed",
    )
    checks["dead_letter_after_threshold"] = (
        dead_first is None
        and dead_second is None
        and dead_record is not None
        and dead_record.attempt_count == 3
        and service.consumer_checkpoint(dead.consumer_id).sequence == 1
    )
    service.acknowledge(
        who,
        dead.consumer_id,
        stream_sequence=2,
        event_id="event.2",
    )

    before_replay = service.consumer_checkpoint(analytics.consumer_id)
    preview_request = ReplayRequest(
        "replay.preview",
        BackendEnvironmentKind.TEST,
        "stream.gameplay",
        1,
        3,
        True,
        "incident.review",
    )
    preview, preview_events = service.replay(who, preview_request)
    checks["replay_dry_run_non_mutating"] = (
        preview.executed is False
        and len(preview_events) == 3
        and service.consumer_checkpoint(analytics.consumer_id) == before_replay
    )
    execute_request = ReplayRequest(
        "replay.execute",
        BackendEnvironmentKind.TEST,
        "stream.gameplay",
        1,
        2,
        False,
        "repair.test",
    )
    executed, execute_events = service.replay(who, execute_request)
    checks["replay_execution_checkpoint_safe"] = (
        executed.executed is True
        and len(execute_events) == 2
        and service.consumer_checkpoint(analytics.consumer_id) == before_replay
    )
    checks["replay_id_rebind_rejected"] = expected_exception(
        EventPipelineStateError,
        lambda: service.replay(
            who,
            replace(execute_request, end_sequence=3),
        ),
        "replay_id_conflict",
    )

    checks["retention_guard"] = expected_exception(
        EventPipelineStateError,
        lambda: service.prune_retention(
            who,
            environment=BackendEnvironmentKind.TEST,
            stream_id="stream.gameplay",
            before_sequence=4,
        ),
        "retention_would_drop_uncheckpointed",
    )
    removed_count, removed_bytes = service.prune_retention(
        who,
        environment=BackendEnvironmentKind.TEST,
        stream_id="stream.gameplay",
        before_sequence=3,
    )
    checks["retention_prune_after_checkpoint"] = (
        removed_count == 2
        and removed_bytes > 0
        and tuple(
            item.envelope.event_id
            for item in service.poll(who, analytics.consumer_id)
        )
        == ("event.3",)
    )
    checks["pruned_identity_non_reusable"] = expected_exception(
        EventPipelineStateError,
        lambda: service.append_event(who, first_envelope),
        "event_already_pruned",
    )

    exported = OpenTelemetryEventBridge().export(definition, first)
    rendered_export = json.dumps(exported.canonical(), sort_keys=True)
    checks["otel_redaction"] = (
        exported.body["email"] == "[REDACTED]"
        and "person@example.invalid" not in rendered_export
        and "account.42" not in rendered_export
        and bool(exported.attributes["subject.sha256"])
        and exported.trace_id == first.envelope.trace_id
    )
    mapped = cloudevent_mapping(first)
    checks["cloudevent_v1_interop_shape"] = (
        mapped["specversion"] == "1.0"
        and mapped["id"] == "event.1"
        and mapped["source"] == "urn:kodepoia:server.gameplay"
        and mapped["type"] == "gameplay.action"
        and mapped["dataschema"]
        == "urn:kodepoia:event-schema:schema.gameplay:1"
        and mapped["data"]["action"] == "login"
    )

    tiny_store = LocalEventStore(
        max_schemas=1,
        max_events=1,
        max_retained_payload_bytes=64,
    )
    tiny = InMemoryEventPipelineService(
        clock_ms=clock,
        store=tiny_store,
        max_consumers=1,
        max_replay_events=1,
        max_replay_records=1,
        max_dead_letters=1,
        max_trace_records=32,
    )
    tiny.register_schema(who, schema(max_payload_bytes=64))
    tiny.append_event(
        who,
        envelope(
            "event.tiny.1",
            1,
            payload={"action": "x", "score": 1},
        ),
    )
    checks["bounded_capacity"] = expected_exception(
        EventPipelineCapacityError,
        lambda: tiny.append_event(
            who,
            envelope(
                "event.tiny.2",
                2,
                payload={"action": "y", "score": 2},
            ),
        ),
    )

    redacted = service.redacted_evidence()
    rendered_evidence = json.dumps(redacted, sort_keys=True).lower()
    checks["redacted_evidence"] = (
        redacted["provider_live_claim"] is False
        and redacted["secrets_exposed"] is False
        and redacted["pii_exposed"] is False
        and redacted["raw_payloads_exposed"] is False
        and "person@example.invalid" not in rendered_evidence
        and "account.42" not in rendered_evidence
    )

    if not all(checks.values()):
        failed = sorted(name for name, ok in checks.items() if not ok)
        raise AssertionError(f"R14.13 acceptance checks failed: {failed}")

    state = service.state_snapshot()
    latest = store.latest_sequence(
        BackendEnvironmentKind.TEST,
        "stream.gameplay",
    )
    analytics_checkpoint = service.consumer_checkpoint(analytics.consumer_id)
    assert dead_record is not None
    evidence = {
        "schema_version": 1,
        "source_sha": source_sha,
        "status": "pass",
        "checks": checks,
        "digests": {
            "schema": definition.digest(),
            "event": first.digest(),
            "checkpoint": analytics_checkpoint.digest(),
            "dead_letter": dead_record.digest(),
            "replay_preview": preview.digest(),
            "replay_execute": executed.digest(),
            "otel": exported.digest(),
            "state": state.digest(),
            "trace": state.trace_digest,
        },
        "counts": {
            "retained_events": len(state.event_digests),
            "schemas": len(state.schema_digests),
            "checkpoints": len(state.checkpoint_digests),
            "dead_letters": len(state.dead_letter_digests),
            "replays": len(state.replay_digests),
            "consumer_lag_events": latest - analytics_checkpoint.sequence,
            "retained_payload_bytes": state.retained_payload_bytes,
            "acceptance_events_appended": 3,
        },
        "budgets": {
            "max_schemas": store.max_schemas,
            "max_events": store.max_events,
            "max_retained_payload_bytes": store.max_retained_payload_bytes,
            "max_consumers": service.max_consumers,
            "max_replay_events": service.max_replay_events,
            "max_replay_records": service.max_replay_records,
            "max_dead_letters": service.max_dead_letters,
            "max_trace_records": service.max_trace_records,
        },
        "manual_state": "none",
        "provider_live_claim": False,
        "external_broker_required": False,
        "otel_collector_required": False,
        "secrets_exposed": False,
        "pii_exposed": False,
        "raw_payloads_exposed": False,
    }
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate deterministic R14.13 event pipeline acceptance evidence"
    )
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    evidence = run(args.source_sha)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
