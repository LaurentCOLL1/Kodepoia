from __future__ import annotations

import hashlib
import json
import re
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Callable, Mapping, Sequence

from .authority import AuthorityActorContext
from .contracts import BackendEnvironmentKind, canonical_json_bytes, canonical_sha256

_STABLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,191}$")
_TRACE_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_SPAN_ID_RE = re.compile(r"^[0-9a-f]{16}$")
_HIGH_RISK_FIELD_TOKENS = frozenset(
    {
        "authorization",
        "cookie",
        "credential",
        "password",
        "private_key",
        "refresh_token",
        "secret",
        "session_token",
        "token",
    }
)


class EventPipelinePolicyError(ValueError):
    pass


class EventPipelineStateError(RuntimeError):
    pass


class EventPipelineAuthorizationError(PermissionError):
    pass


class EventPipelineCapacityError(EventPipelineStateError):
    pass


class EventFieldType(StrEnum):
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"


class EventPrivacyClass(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    SENSITIVE = "sensitive"
    SECRET = "secret"


@dataclass(frozen=True, slots=True)
class EventSchemaField:
    name: str
    value_type: EventFieldType
    required: bool = True
    privacy: EventPrivacyClass = EventPrivacyClass.INTERNAL

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _stable_id(self.name, field="field_name"))
        if not isinstance(self.value_type, EventFieldType):
            raise EventPipelinePolicyError("invalid_field_type")
        if not isinstance(self.required, bool):
            raise EventPipelinePolicyError("invalid_field_required")
        if not isinstance(self.privacy, EventPrivacyClass):
            raise EventPipelinePolicyError("invalid_field_privacy")
        lowered = self.name.lower()
        if self.privacy is EventPrivacyClass.SECRET:
            raise EventPipelinePolicyError("secret_payload_fields_forbidden")
        if any(token in lowered for token in _HIGH_RISK_FIELD_TOKENS):
            raise EventPipelinePolicyError("high_risk_payload_field_forbidden")

    def canonical(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value_type": self.value_type.value,
            "required": self.required,
            "privacy": self.privacy.value,
        }


@dataclass(frozen=True, slots=True)
class EventSchemaDefinition:
    schema_id: str
    event_type: str
    version: int
    environment: BackendEnvironmentKind
    fields: tuple[EventSchemaField, ...]
    max_payload_bytes: int = 64 * 1024

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_id", _stable_id(self.schema_id, field="schema_id"))
        object.__setattr__(self, "event_type", _stable_id(self.event_type, field="event_type"))
        object.__setattr__(self, "version", _positive_int(self.version, field="schema_version"))
        if not isinstance(self.environment, BackendEnvironmentKind):
            raise EventPipelinePolicyError("invalid_environment")
        if not isinstance(self.fields, tuple) or not self.fields:
            raise EventPipelinePolicyError("schema_fields_required")
        if any(not isinstance(item, EventSchemaField) for item in self.fields):
            raise EventPipelinePolicyError("invalid_schema_field")
        names = [item.name for item in self.fields]
        if len(names) != len(set(names)):
            raise EventPipelinePolicyError("duplicate_schema_field")
        object.__setattr__(self, "fields", tuple(sorted(self.fields, key=lambda item: item.name)))
        object.__setattr__(
            self,
            "max_payload_bytes",
            _positive_int(self.max_payload_bytes, field="max_payload_bytes", maximum=4 * 1024 * 1024),
        )

    def canonical(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "event_type": self.event_type,
            "version": self.version,
            "environment": self.environment.value,
            "fields": [item.canonical() for item in self.fields],
            "max_payload_bytes": self.max_payload_bytes,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())

    def validate_payload(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        normalized = _canonical_mapping(payload, field="payload", max_bytes=self.max_payload_bytes)
        by_name = {item.name: item for item in self.fields}
        unknown = sorted(set(normalized) - set(by_name))
        if unknown:
            raise EventPipelinePolicyError("unknown_payload_field")
        missing = sorted(item.name for item in self.fields if item.required and item.name not in normalized)
        if missing:
            raise EventPipelinePolicyError("required_payload_field_missing")
        for key, value in normalized.items():
            if not _matches_field_type(value, by_name[key].value_type):
                raise EventPipelinePolicyError("payload_field_type_mismatch")
        return normalized

    def redacted_payload(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        normalized = self.validate_payload(payload)
        by_name = {item.name: item for item in self.fields}
        return {
            key: "[REDACTED]" if by_name[key].privacy is EventPrivacyClass.SENSITIVE else _thaw_json(value)
            for key, value in normalized.items()
        }


@dataclass(frozen=True, slots=True)
class EventEnvelope:
    event_id: str
    stream_id: str
    event_type: str
    schema_id: str
    schema_version: int
    environment: BackendEnvironmentKind
    source: str
    source_sequence: int
    occurred_at_ms: int
    subject_id: str
    trace_id: str
    span_id: str
    payload: Mapping[str, Any]
    max_payload_bytes: int = 4 * 1024 * 1024

    def __post_init__(self) -> None:
        for field in ("event_id", "stream_id", "event_type", "schema_id", "source", "subject_id"):
            object.__setattr__(self, field, _stable_id(getattr(self, field), field=field))
        object.__setattr__(self, "schema_version", _positive_int(self.schema_version, field="schema_version"))
        if not isinstance(self.environment, BackendEnvironmentKind):
            raise EventPipelinePolicyError("invalid_environment")
        object.__setattr__(self, "source_sequence", _positive_int(self.source_sequence, field="source_sequence"))
        object.__setattr__(self, "occurred_at_ms", _non_negative_int(self.occurred_at_ms, field="occurred_at_ms"))
        if not isinstance(self.trace_id, str) or _TRACE_ID_RE.fullmatch(self.trace_id) is None:
            raise EventPipelinePolicyError("invalid_trace_id")
        if not isinstance(self.span_id, str) or _SPAN_ID_RE.fullmatch(self.span_id) is None:
            raise EventPipelinePolicyError("invalid_span_id")
        object.__setattr__(
            self,
            "max_payload_bytes",
            _positive_int(self.max_payload_bytes, field="max_payload_bytes", maximum=4 * 1024 * 1024),
        )
        object.__setattr__(self, "payload", _canonical_mapping(self.payload, field="payload", max_bytes=self.max_payload_bytes))

    def canonical(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "stream_id": self.stream_id,
            "event_type": self.event_type,
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "environment": self.environment.value,
            "source": self.source,
            "source_sequence": self.source_sequence,
            "occurred_at_ms": self.occurred_at_ms,
            "subject_id": self.subject_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "payload": _thaw_json(self.payload),
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class StoredEvent:
    stream_sequence: int
    envelope: EventEnvelope

    def __post_init__(self) -> None:
        object.__setattr__(self, "stream_sequence", _positive_int(self.stream_sequence, field="stream_sequence"))
        if not isinstance(self.envelope, EventEnvelope):
            raise EventPipelinePolicyError("invalid_event_envelope")

    def canonical(self) -> dict[str, Any]:
        return {"stream_sequence": self.stream_sequence, "envelope": self.envelope.canonical()}

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class ConsumerDefinition:
    consumer_id: str
    stream_id: str
    environment: BackendEnvironmentKind
    max_delivery_attempts: int = 3

    def __post_init__(self) -> None:
        object.__setattr__(self, "consumer_id", _stable_id(self.consumer_id, field="consumer_id"))
        object.__setattr__(self, "stream_id", _stable_id(self.stream_id, field="stream_id"))
        if not isinstance(self.environment, BackendEnvironmentKind):
            raise EventPipelinePolicyError("invalid_environment")
        object.__setattr__(
            self,
            "max_delivery_attempts",
            _positive_int(self.max_delivery_attempts, field="max_delivery_attempts", maximum=32),
        )

    def canonical(self) -> dict[str, Any]:
        return {
            "consumer_id": self.consumer_id,
            "stream_id": self.stream_id,
            "environment": self.environment.value,
            "max_delivery_attempts": self.max_delivery_attempts,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class ConsumerCheckpoint:
    consumer_id: str
    stream_id: str
    environment: BackendEnvironmentKind
    sequence: int
    updated_at_ms: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "consumer_id", _stable_id(self.consumer_id, field="consumer_id"))
        object.__setattr__(self, "stream_id", _stable_id(self.stream_id, field="stream_id"))
        if not isinstance(self.environment, BackendEnvironmentKind):
            raise EventPipelinePolicyError("invalid_environment")
        object.__setattr__(self, "sequence", _non_negative_int(self.sequence, field="checkpoint_sequence"))
        object.__setattr__(self, "updated_at_ms", _non_negative_int(self.updated_at_ms, field="updated_at_ms"))

    def canonical(self) -> dict[str, Any]:
        return {
            "consumer_id": self.consumer_id,
            "stream_id": self.stream_id,
            "environment": self.environment.value,
            "sequence": self.sequence,
            "updated_at_ms": self.updated_at_ms,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class DeadLetterRecord:
    dead_letter_id: str
    consumer_id: str
    event_id: str
    event_digest: str
    stream_sequence: int
    attempt_count: int
    reason_code: str
    created_at_ms: int

    def __post_init__(self) -> None:
        for field in ("dead_letter_id", "consumer_id", "event_id", "reason_code"):
            object.__setattr__(self, field, _stable_id(getattr(self, field), field=field))
        object.__setattr__(self, "stream_sequence", _positive_int(self.stream_sequence, field="stream_sequence"))
        object.__setattr__(self, "attempt_count", _positive_int(self.attempt_count, field="attempt_count", maximum=32))
        object.__setattr__(self, "created_at_ms", _non_negative_int(self.created_at_ms, field="created_at_ms"))
        if not isinstance(self.event_digest, str) or re.fullmatch(r"[0-9a-f]{64}", self.event_digest) is None:
            raise EventPipelinePolicyError("invalid_event_digest")

    def canonical(self) -> dict[str, Any]:
        return {
            "dead_letter_id": self.dead_letter_id,
            "consumer_id": self.consumer_id,
            "event_id": self.event_id,
            "event_digest": self.event_digest,
            "stream_sequence": self.stream_sequence,
            "attempt_count": self.attempt_count,
            "reason_code": self.reason_code,
            "created_at_ms": self.created_at_ms,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class ReplayRequest:
    replay_id: str
    environment: BackendEnvironmentKind
    stream_id: str
    start_sequence: int
    end_sequence: int
    dry_run: bool
    reason_code: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "replay_id", _stable_id(self.replay_id, field="replay_id"))
        if not isinstance(self.environment, BackendEnvironmentKind):
            raise EventPipelinePolicyError("invalid_environment")
        object.__setattr__(self, "stream_id", _stable_id(self.stream_id, field="stream_id"))
        start = _positive_int(self.start_sequence, field="start_sequence")
        end = _positive_int(self.end_sequence, field="end_sequence")
        if end < start:
            raise EventPipelinePolicyError("invalid_replay_range")
        if not isinstance(self.dry_run, bool):
            raise EventPipelinePolicyError("invalid_dry_run")
        object.__setattr__(self, "reason_code", _stable_id(self.reason_code, field="reason_code"))

    def canonical(self) -> dict[str, Any]:
        return {
            "replay_id": self.replay_id,
            "environment": self.environment.value,
            "stream_id": self.stream_id,
            "start_sequence": self.start_sequence,
            "end_sequence": self.end_sequence,
            "dry_run": self.dry_run,
            "reason_code": self.reason_code,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class ReplayRecord:
    request_digest: str
    replay_id: str
    event_count: int
    event_digest: str
    executed: bool
    created_at_ms: int

    def canonical(self) -> dict[str, Any]:
        return {
            "request_digest": self.request_digest,
            "replay_id": self.replay_id,
            "event_count": self.event_count,
            "event_digest": self.event_digest,
            "executed": self.executed,
            "created_at_ms": self.created_at_ms,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class OpenTelemetryEventRecord:
    time_unix_nano: int
    trace_id: str
    span_id: str
    attributes: Mapping[str, Any]
    body: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "time_unix_nano", _non_negative_int(self.time_unix_nano, field="time_unix_nano"))
        if _TRACE_ID_RE.fullmatch(self.trace_id) is None or _SPAN_ID_RE.fullmatch(self.span_id) is None:
            raise EventPipelinePolicyError("invalid_otel_trace_context")
        object.__setattr__(self, "attributes", _canonical_mapping(self.attributes, field="otel_attributes", max_bytes=64 * 1024))
        object.__setattr__(self, "body", _canonical_mapping(self.body, field="otel_body", max_bytes=4 * 1024 * 1024))

    def canonical(self) -> dict[str, Any]:
        return {
            "time_unix_nano": self.time_unix_nano,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "attributes": _thaw_json(self.attributes),
            "body": _thaw_json(self.body),
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class EventPipelineStateSnapshot:
    schema_digests: tuple[str, ...]
    event_digests: tuple[str, ...]
    checkpoint_digests: tuple[str, ...]
    dead_letter_digests: tuple[str, ...]
    replay_digests: tuple[str, ...]
    trace_digest: str
    retained_payload_bytes: int

    def canonical(self) -> dict[str, Any]:
        return {
            "schema_digests": list(self.schema_digests),
            "event_digests": list(self.event_digests),
            "checkpoint_digests": list(self.checkpoint_digests),
            "dead_letter_digests": list(self.dead_letter_digests),
            "replay_digests": list(self.replay_digests),
            "trace_digest": self.trace_digest,
            "retained_payload_bytes": self.retained_payload_bytes,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


class LocalEventStore:
    def __init__(self, *, max_schemas: int = 128, max_events: int = 100_000, max_retained_payload_bytes: int = 64 * 1024 * 1024) -> None:
        self.max_schemas = _positive_int(max_schemas, field="max_schemas", maximum=1_000_000)
        self.max_events = _positive_int(max_events, field="max_events", maximum=10_000_000)
        self.max_retained_payload_bytes = _positive_int(
            max_retained_payload_bytes,
            field="max_retained_payload_bytes",
            maximum=2**50,
        )
        self._schemas: dict[tuple[BackendEnvironmentKind, str, int], EventSchemaDefinition] = {}
        self._schema_versions: dict[tuple[BackendEnvironmentKind, str], dict[int, str]] = {}
        self._streams: dict[tuple[BackendEnvironmentKind, str], list[StoredEvent]] = {}
        self._next_sequence: dict[tuple[BackendEnvironmentKind, str], int] = {}
        self._source_sequence: dict[tuple[BackendEnvironmentKind, str, str], int] = {}
        self._event_identity: dict[str, tuple[str, BackendEnvironmentKind, str, int, StoredEvent | None]] = {}
        self._lock = threading.RLock()

    @property
    def retained_payload_bytes(self) -> int:
        return sum(len(canonical_json_bytes(_thaw_json(item.envelope.payload))) for values in self._streams.values() for item in values)

    def register_schema(self, schema: EventSchemaDefinition) -> EventSchemaDefinition:
        if not isinstance(schema, EventSchemaDefinition):
            raise EventPipelinePolicyError("invalid_schema")
        key = (schema.environment, schema.schema_id, schema.version)
        with self._lock:
            existing = self._schemas.get(key)
            if existing is not None:
                if existing != schema:
                    raise EventPipelineStateError("schema_identity_conflict")
                return existing
            if len(self._schemas) >= self.max_schemas:
                raise EventPipelineCapacityError("schema_capacity")
            versions = self._schema_versions.setdefault((schema.environment, schema.schema_id), {})
            existing_digest = versions.get(schema.version)
            if existing_digest is not None and existing_digest != schema.digest():
                raise EventPipelineStateError("schema_version_conflict")
            self._schemas[key] = schema
            versions[schema.version] = schema.digest()
            return schema

    def schema(self, environment: BackendEnvironmentKind, schema_id: str, version: int) -> EventSchemaDefinition:
        if not isinstance(environment, BackendEnvironmentKind):
            raise EventPipelinePolicyError("invalid_environment")
        schema_id = _stable_id(schema_id, field="schema_id")
        version = _positive_int(version, field="schema_version")
        try:
            return self._schemas[(environment, schema_id, version)]
        except KeyError as exc:
            raise EventPipelineStateError("schema_not_found") from exc

    def append(self, envelope: EventEnvelope) -> tuple[StoredEvent, bool]:
        if not isinstance(envelope, EventEnvelope):
            raise EventPipelinePolicyError("invalid_event_envelope")
        schema = self.schema(envelope.environment, envelope.schema_id, envelope.schema_version)
        if schema.event_type != envelope.event_type:
            raise EventPipelinePolicyError("event_type_schema_mismatch")
        schema.validate_payload(envelope.payload)
        event_digest = envelope.digest()
        with self._lock:
            identity = self._event_identity.get(envelope.event_id)
            if identity is not None:
                prior_digest, prior_env, prior_stream, _prior_sequence, prior_event = identity
                if prior_digest != event_digest or prior_env is not envelope.environment or prior_stream != envelope.stream_id:
                    raise EventPipelineStateError("event_id_conflict")
                if prior_event is None:
                    raise EventPipelineStateError("event_already_pruned")
                return prior_event, True
            source_key = (envelope.environment, envelope.stream_id, envelope.source)
            previous_source_sequence = self._source_sequence.get(source_key, 0)
            if envelope.source_sequence <= previous_source_sequence:
                raise EventPipelineStateError("source_sequence_out_of_order")
            total_retained_events = sum(len(values) for values in self._streams.values())
            if total_retained_events >= self.max_events:
                raise EventPipelineCapacityError("event_capacity")
            payload_bytes = len(canonical_json_bytes(_thaw_json(envelope.payload)))
            if self.retained_payload_bytes + payload_bytes > self.max_retained_payload_bytes:
                raise EventPipelineCapacityError("retained_payload_capacity")
            stream_key = (envelope.environment, envelope.stream_id)
            sequence = self._next_sequence.get(stream_key, 0) + 1
            stored = StoredEvent(stream_sequence=sequence, envelope=envelope)
            self._streams.setdefault(stream_key, []).append(stored)
            self._next_sequence[stream_key] = sequence
            self._source_sequence[source_key] = envelope.source_sequence
            self._event_identity[envelope.event_id] = (event_digest, envelope.environment, envelope.stream_id, sequence, stored)
            return stored, False

    def latest_sequence(self, environment: BackendEnvironmentKind, stream_id: str) -> int:
        return self._next_sequence.get((environment, _stable_id(stream_id, field="stream_id")), 0)

    def earliest_retained_sequence(self, environment: BackendEnvironmentKind, stream_id: str) -> int | None:
        values = self._streams.get((environment, _stable_id(stream_id, field="stream_id")), ())
        return values[0].stream_sequence if values else None

    def events_after(self, environment: BackendEnvironmentKind, stream_id: str, sequence: int, *, limit: int) -> tuple[StoredEvent, ...]:
        sequence = _non_negative_int(sequence, field="sequence")
        limit = _positive_int(limit, field="limit", maximum=10_000)
        values = self._streams.get((environment, _stable_id(stream_id, field="stream_id")), ())
        return tuple(item for item in values if item.stream_sequence > sequence)[:limit]

    def events_range(self, environment: BackendEnvironmentKind, stream_id: str, start: int, end: int) -> tuple[StoredEvent, ...]:
        start = _positive_int(start, field="start_sequence")
        end = _positive_int(end, field="end_sequence")
        if end < start:
            raise EventPipelinePolicyError("invalid_event_range")
        values = self._streams.get((environment, _stable_id(stream_id, field="stream_id")), ())
        return tuple(item for item in values if start <= item.stream_sequence <= end)

    def event_at(self, environment: BackendEnvironmentKind, stream_id: str, sequence: int) -> StoredEvent:
        sequence = _positive_int(sequence, field="stream_sequence")
        for item in self._streams.get((environment, _stable_id(stream_id, field="stream_id")), ()):
            if item.stream_sequence == sequence:
                return item
        raise EventPipelineStateError("event_not_retained")

    def prune_before(self, environment: BackendEnvironmentKind, stream_id: str, before_sequence: int) -> tuple[int, int]:
        before_sequence = _positive_int(before_sequence, field="before_sequence")
        key = (environment, _stable_id(stream_id, field="stream_id"))
        with self._lock:
            current = list(self._streams.get(key, ()))
            removed = [item for item in current if item.stream_sequence < before_sequence]
            kept = [item for item in current if item.stream_sequence >= before_sequence]
            removed_bytes = sum(len(canonical_json_bytes(_thaw_json(item.envelope.payload))) for item in removed)
            for item in removed:
                digest, env, stream, sequence, _stored = self._event_identity[item.envelope.event_id]
                self._event_identity[item.envelope.event_id] = (digest, env, stream, sequence, None)
            self._streams[key] = kept
            return len(removed), removed_bytes

    def schema_digests(self) -> tuple[str, ...]:
        return tuple(sorted(item.digest() for item in self._schemas.values()))

    def event_digests(self) -> tuple[str, ...]:
        values = [item.digest() for stream in self._streams.values() for item in stream]
        return tuple(sorted(values))


class OpenTelemetryEventBridge:
    def export(self, schema: EventSchemaDefinition, stored: StoredEvent) -> OpenTelemetryEventRecord:
        if schema.environment is not stored.envelope.environment or schema.schema_id != stored.envelope.schema_id or schema.version != stored.envelope.schema_version:
            raise EventPipelinePolicyError("otel_schema_mismatch")
        body = schema.redacted_payload(stored.envelope.payload)
        attributes = {
            "event.id": stored.envelope.event_id,
            "event.name": stored.envelope.event_type,
            "event.schema.id": stored.envelope.schema_id,
            "event.schema.version": stored.envelope.schema_version,
            "event.sequence": stored.stream_sequence,
            "event.source": stored.envelope.source,
            "event.stream": stored.envelope.stream_id,
            "subject.sha256": hashlib.sha256(stored.envelope.subject_id.encode("utf-8")).hexdigest(),
        }
        return OpenTelemetryEventRecord(
            time_unix_nano=stored.envelope.occurred_at_ms * 1_000_000,
            trace_id=stored.envelope.trace_id,
            span_id=stored.envelope.span_id,
            attributes=attributes,
            body=body,
        )


def cloudevent_mapping(stored: StoredEvent) -> dict[str, Any]:
    if not isinstance(stored, StoredEvent):
        raise EventPipelinePolicyError("invalid_stored_event")
    event = stored.envelope
    instant = datetime.fromtimestamp(event.occurred_at_ms / 1000, tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    return {
        "specversion": "1.0",
        "id": event.event_id,
        "source": f"urn:kodepoia:{event.source}",
        "type": event.event_type,
        "subject": event.subject_id,
        "time": instant,
        "dataschema": f"urn:kodepoia:event-schema:{event.schema_id}:{event.schema_version}",
        "datacontenttype": "application/json",
        "data": _thaw_json(event.payload),
    }


class InMemoryEventPipelineService:
    def __init__(
        self,
        *,
        clock_ms: Callable[[], int],
        store: LocalEventStore | None = None,
        max_consumers: int = 256,
        max_replay_events: int = 1_000,
        max_replay_records: int = 1_000,
        max_dead_letters: int = 10_000,
        max_trace_records: int = 100_000,
    ) -> None:
        self.clock_ms = clock_ms
        self.store = store or LocalEventStore()
        self.max_consumers = _positive_int(max_consumers, field="max_consumers", maximum=1_000_000)
        self.max_replay_events = _positive_int(max_replay_events, field="max_replay_events", maximum=1_000_000)
        self.max_replay_records = _positive_int(max_replay_records, field="max_replay_records", maximum=1_000_000)
        self.max_dead_letters = _positive_int(max_dead_letters, field="max_dead_letters", maximum=1_000_000)
        self.max_trace_records = _positive_int(max_trace_records, field="max_trace_records", maximum=10_000_000)
        self._consumers: dict[str, ConsumerDefinition] = {}
        self._checkpoints: dict[str, ConsumerCheckpoint] = {}
        self._acked_ids: dict[tuple[str, int], str] = {}
        self._attempts: dict[tuple[str, str], int] = {}
        self._dead_letters: dict[tuple[str, str], DeadLetterRecord] = {}
        self._replays: dict[str, tuple[ReplayRequest, ReplayRecord]] = {}
        self._trace: list[dict[str, Any]] = []
        self._lock = threading.RLock()

    @staticmethod
    def _authorize(actor: AuthorityActorContext, permission: str, target_id: str) -> None:
        if not actor.can(permission, target_id):
            raise EventPipelineAuthorizationError("forbidden")

    def _now(self) -> int:
        return _non_negative_int(self.clock_ms(), field="server_clock")

    def _append_trace(self, event: Mapping[str, Any]) -> None:
        if len(self._trace) >= self.max_trace_records:
            raise EventPipelineCapacityError("trace_capacity")
        sanitized = dict(event)
        if any(key in sanitized for key in ("payload", "subject_id", "secret", "token")):
            raise EventPipelinePolicyError("unsafe_trace_field")
        self._trace.append(sanitized)

    def register_schema(self, actor: AuthorityActorContext, schema: EventSchemaDefinition) -> EventSchemaDefinition:
        self._authorize(actor, "events.schema.register", schema.schema_id)
        result = self.store.register_schema(schema)
        self._append_trace({"event": "schema_registered", "schema_id": schema.schema_id, "schema_digest": schema.digest(), "environment": schema.environment.value})
        return result

    def append_event(self, actor: AuthorityActorContext, envelope: EventEnvelope) -> StoredEvent:
        self._authorize(actor, "events.event.append", envelope.stream_id)
        stored, duplicate = self.store.append(envelope)
        self._append_trace(
            {
                "event": "event_duplicate" if duplicate else "event_appended",
                "event_id": envelope.event_id,
                "stream_id": envelope.stream_id,
                "stream_sequence": stored.stream_sequence,
                "event_digest": stored.digest(),
                "environment": envelope.environment.value,
            }
        )
        return stored

    def register_consumer(
        self,
        actor: AuthorityActorContext,
        definition: ConsumerDefinition,
        *,
        checkpoint: ConsumerCheckpoint | None = None,
    ) -> ConsumerCheckpoint:
        self._authorize(actor, "events.consumer.register", definition.consumer_id)
        with self._lock:
            existing = self._consumers.get(definition.consumer_id)
            if existing is not None and existing != definition:
                raise EventPipelineStateError("consumer_id_conflict")
            if existing is None and len(self._consumers) >= self.max_consumers:
                raise EventPipelineCapacityError("consumer_capacity")
            if checkpoint is not None:
                if (
                    checkpoint.consumer_id != definition.consumer_id
                    or checkpoint.stream_id != definition.stream_id
                    or checkpoint.environment is not definition.environment
                ):
                    raise EventPipelinePolicyError("checkpoint_consumer_mismatch")
                latest = self.store.latest_sequence(definition.environment, definition.stream_id)
                if checkpoint.sequence > latest:
                    raise EventPipelinePolicyError("checkpoint_ahead_of_stream")
                earliest = self.store.earliest_retained_sequence(definition.environment, definition.stream_id)
                if earliest is not None and checkpoint.sequence < earliest - 1:
                    raise EventPipelineStateError("checkpoint_too_old")
                initial = checkpoint
            else:
                initial = ConsumerCheckpoint(
                    consumer_id=definition.consumer_id,
                    stream_id=definition.stream_id,
                    environment=definition.environment,
                    sequence=0,
                    updated_at_ms=self._now(),
                )
            self._consumers[definition.consumer_id] = definition
            current = self._checkpoints.get(definition.consumer_id)
            if current is None:
                self._checkpoints[definition.consumer_id] = initial
            elif current != initial and checkpoint is not None:
                raise EventPipelineStateError("checkpoint_restore_conflict")
            result = self._checkpoints[definition.consumer_id]
            self._append_trace({"event": "consumer_registered", "consumer_id": definition.consumer_id, "checkpoint": result.sequence})
            return result

    def consumer_checkpoint(self, consumer_id: str) -> ConsumerCheckpoint:
        consumer_id = _stable_id(consumer_id, field="consumer_id")
        try:
            return self._checkpoints[consumer_id]
        except KeyError as exc:
            raise EventPipelineStateError("consumer_not_found") from exc

    def poll(self, actor: AuthorityActorContext, consumer_id: str, *, limit: int = 100) -> tuple[StoredEvent, ...]:
        consumer_id = _stable_id(consumer_id, field="consumer_id")
        self._authorize(actor, "events.consume", consumer_id)
        try:
            definition = self._consumers[consumer_id]
            checkpoint = self._checkpoints[consumer_id]
        except KeyError as exc:
            raise EventPipelineStateError("consumer_not_found") from exc
        events = self.store.events_after(definition.environment, definition.stream_id, checkpoint.sequence, limit=limit)
        self._append_trace({"event": "consumer_polled", "consumer_id": consumer_id, "after_sequence": checkpoint.sequence, "count": len(events)})
        return events

    def acknowledge(self, actor: AuthorityActorContext, consumer_id: str, *, stream_sequence: int, event_id: str) -> ConsumerCheckpoint:
        consumer_id = _stable_id(consumer_id, field="consumer_id")
        event_id = _stable_id(event_id, field="event_id")
        stream_sequence = _positive_int(stream_sequence, field="stream_sequence")
        self._authorize(actor, "events.consume", consumer_id)
        definition = self._consumers.get(consumer_id)
        checkpoint = self._checkpoints.get(consumer_id)
        if definition is None or checkpoint is None:
            raise EventPipelineStateError("consumer_not_found")
        if stream_sequence <= checkpoint.sequence:
            if self._acked_ids.get((consumer_id, stream_sequence)) != event_id:
                raise EventPipelineStateError("acknowledgement_rebind")
            return checkpoint
        if stream_sequence != checkpoint.sequence + 1:
            raise EventPipelineStateError("acknowledgement_out_of_order")
        stored = self.store.event_at(definition.environment, definition.stream_id, stream_sequence)
        if stored.envelope.event_id != event_id:
            raise EventPipelineStateError("acknowledgement_event_mismatch")
        updated = ConsumerCheckpoint(
            consumer_id=consumer_id,
            stream_id=definition.stream_id,
            environment=definition.environment,
            sequence=stream_sequence,
            updated_at_ms=self._now(),
        )
        self._checkpoints[consumer_id] = updated
        self._acked_ids[(consumer_id, stream_sequence)] = event_id
        self._attempts.pop((consumer_id, event_id), None)
        self._append_trace({"event": "event_acknowledged", "consumer_id": consumer_id, "event_id": event_id, "stream_sequence": stream_sequence})
        return updated

    def record_delivery_failure(
        self,
        actor: AuthorityActorContext,
        consumer_id: str,
        *,
        stream_sequence: int,
        event_id: str,
        reason_code: str,
    ) -> DeadLetterRecord | None:
        consumer_id = _stable_id(consumer_id, field="consumer_id")
        event_id = _stable_id(event_id, field="event_id")
        reason_code = _stable_id(reason_code, field="reason_code")
        stream_sequence = _positive_int(stream_sequence, field="stream_sequence")
        self._authorize(actor, "events.consume", consumer_id)
        definition = self._consumers.get(consumer_id)
        checkpoint = self._checkpoints.get(consumer_id)
        if definition is None or checkpoint is None:
            raise EventPipelineStateError("consumer_not_found")
        existing = self._dead_letters.get((consumer_id, event_id))
        if existing is not None:
            if existing.stream_sequence != stream_sequence:
                raise EventPipelineStateError("dead_letter_rebind")
            return existing
        if stream_sequence != checkpoint.sequence + 1:
            raise EventPipelineStateError("delivery_failure_out_of_order")
        stored = self.store.event_at(definition.environment, definition.stream_id, stream_sequence)
        if stored.envelope.event_id != event_id:
            raise EventPipelineStateError("delivery_failure_event_mismatch")
        key = (consumer_id, event_id)
        attempts = self._attempts.get(key, 0) + 1
        self._attempts[key] = attempts
        if attempts < definition.max_delivery_attempts:
            self._append_trace({"event": "delivery_failed", "consumer_id": consumer_id, "event_id": event_id, "attempt": attempts, "reason_code": reason_code})
            return None
        if len(self._dead_letters) >= self.max_dead_letters:
            raise EventPipelineCapacityError("dead_letter_capacity")
        record = DeadLetterRecord(
            dead_letter_id=f"dlq.{consumer_id}.{stream_sequence}",
            consumer_id=consumer_id,
            event_id=event_id,
            event_digest=stored.digest(),
            stream_sequence=stream_sequence,
            attempt_count=attempts,
            reason_code=reason_code,
            created_at_ms=self._now(),
        )
        self._dead_letters[key] = record
        self._checkpoints[consumer_id] = ConsumerCheckpoint(
            consumer_id=consumer_id,
            stream_id=definition.stream_id,
            environment=definition.environment,
            sequence=stream_sequence,
            updated_at_ms=self._now(),
        )
        self._acked_ids[(consumer_id, stream_sequence)] = event_id
        self._append_trace({"event": "event_dead_lettered", "consumer_id": consumer_id, "event_id": event_id, "dead_letter_digest": record.digest()})
        return record

    def replay(self, actor: AuthorityActorContext, request: ReplayRequest) -> tuple[ReplayRecord, tuple[StoredEvent, ...]]:
        self._authorize(actor, "events.replay", request.stream_id)
        existing = self._replays.get(request.replay_id)
        if existing is not None:
            prior_request, prior_record = existing
            if prior_request != request:
                raise EventPipelineStateError("replay_id_conflict")
            events = self.store.events_range(request.environment, request.stream_id, request.start_sequence, request.end_sequence)
            return prior_record, events
        if len(self._replays) >= self.max_replay_records:
            raise EventPipelineCapacityError("replay_record_capacity")
        events = self.store.events_range(request.environment, request.stream_id, request.start_sequence, request.end_sequence)
        if len(events) > self.max_replay_events:
            raise EventPipelineCapacityError("replay_event_capacity")
        if not events:
            raise EventPipelineStateError("replay_range_empty")
        digest = canonical_sha256([item.digest() for item in events])
        record = ReplayRecord(
            request_digest=request.digest(),
            replay_id=request.replay_id,
            event_count=len(events),
            event_digest=digest,
            executed=not request.dry_run,
            created_at_ms=self._now(),
        )
        self._replays[request.replay_id] = (request, record)
        self._append_trace(
            {
                "event": "replay_previewed" if request.dry_run else "replay_executed",
                "replay_id": request.replay_id,
                "stream_id": request.stream_id,
                "count": len(events),
                "event_digest": digest,
            }
        )
        return record, events

    def prune_retention(
        self,
        actor: AuthorityActorContext,
        *,
        environment: BackendEnvironmentKind,
        stream_id: str,
        before_sequence: int,
    ) -> tuple[int, int]:
        stream_id = _stable_id(stream_id, field="stream_id")
        before_sequence = _positive_int(before_sequence, field="before_sequence")
        self._authorize(actor, "events.retention.prune", stream_id)
        checkpoints = [
            cp.sequence
            for consumer_id, cp in self._checkpoints.items()
            if self._consumers[consumer_id].environment is environment and self._consumers[consumer_id].stream_id == stream_id
        ]
        required_sequence = before_sequence - 1
        if any(sequence < required_sequence for sequence in checkpoints):
            raise EventPipelineStateError("retention_would_drop_uncheckpointed")
        removed_count, removed_bytes = self.store.prune_before(environment, stream_id, before_sequence)
        self._append_trace(
            {
                "event": "retention_pruned",
                "environment": environment.value,
                "stream_id": stream_id,
                "before_sequence": before_sequence,
                "removed_count": removed_count,
                "removed_bytes": removed_bytes,
            }
        )
        return removed_count, removed_bytes

    def state_snapshot(self) -> EventPipelineStateSnapshot:
        checkpoints = tuple(sorted(item.digest() for item in self._checkpoints.values()))
        dead_letters = tuple(sorted(item.digest() for item in self._dead_letters.values()))
        replays = tuple(sorted(record.digest() for _request, record in self._replays.values()))
        trace_digest = canonical_sha256(self._trace)
        return EventPipelineStateSnapshot(
            schema_digests=self.store.schema_digests(),
            event_digests=self.store.event_digests(),
            checkpoint_digests=checkpoints,
            dead_letter_digests=dead_letters,
            replay_digests=replays,
            trace_digest=trace_digest,
            retained_payload_bytes=self.store.retained_payload_bytes,
        )

    def redacted_evidence(self) -> dict[str, Any]:
        snapshot = self.state_snapshot()
        return {
            "provider_live_claim": False,
            "secrets_exposed": False,
            "pii_exposed": False,
            "raw_payloads_exposed": False,
            "schema_count": len(snapshot.schema_digests),
            "retained_event_count": len(snapshot.event_digests),
            "checkpoint_count": len(snapshot.checkpoint_digests),
            "dead_letter_count": len(snapshot.dead_letter_digests),
            "replay_count": len(snapshot.replay_digests),
            "retained_payload_bytes": snapshot.retained_payload_bytes,
            "state_digest": snapshot.digest(),
            "trace_digest": snapshot.trace_digest,
        }


def _stable_id(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _STABLE_ID_RE.fullmatch(value) is None:
        raise EventPipelinePolicyError(f"invalid_{field}")
    return value


def _positive_int(value: int, *, field: str, maximum: int = 2**63 - 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
        raise EventPipelinePolicyError(f"invalid_{field}")
    return value


def _non_negative_int(value: int, *, field: str, maximum: int = 2**63 - 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
        raise EventPipelinePolicyError(f"invalid_{field}")
    return value


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze_json(nested) for key, nested in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_json(item) for item in value)
    return value


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw_json(nested) for key, nested in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def _canonical_mapping(value: Mapping[str, Any], *, field: str, max_bytes: int) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise EventPipelinePolicyError(f"invalid_{field}")
    try:
        encoded = canonical_json_bytes(dict(value))
        roundtrip = json.loads(encoded.decode("utf-8"))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise EventPipelinePolicyError(f"invalid_{field}") from exc
    if len(encoded) > max_bytes:
        raise EventPipelineCapacityError(f"{field}_bytes_capacity")
    if not isinstance(roundtrip, dict) or any(not isinstance(key, str) for key in roundtrip):
        raise EventPipelinePolicyError(f"invalid_{field}")
    return _freeze_json(roundtrip)


def _matches_field_type(value: Any, value_type: EventFieldType) -> bool:
    if value_type is EventFieldType.STRING:
        return isinstance(value, str)
    if value_type is EventFieldType.INTEGER:
        return isinstance(value, int) and not isinstance(value, bool)
    if value_type is EventFieldType.NUMBER:
        return (isinstance(value, int) and not isinstance(value, bool)) or isinstance(value, float)
    if value_type is EventFieldType.BOOLEAN:
        return isinstance(value, bool)
    if value_type is EventFieldType.OBJECT:
        return isinstance(value, Mapping)
    if value_type is EventFieldType.ARRAY:
        return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray, Mapping))
    return False
