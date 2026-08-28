from __future__ import annotations

import re
import threading
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any, Callable, Mapping, Sequence

from .contracts import canonical_json_bytes, canonical_sha256

_STABLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_RESERVED_CLIENT_FIELDS = frozenset(
    {
        "authorization",
        "authorized",
        "event_sequence",
        "lease_id",
        "revision",
        "server_revision",
        "server_time_ms",
    }
)


class AuthorityPolicyError(ValueError):
    """Raised when a client/server authority contract is structurally unsafe."""


class AuthorityStateError(RuntimeError):
    """Raised when the authoritative state machine cannot preserve its invariants."""


class AuthorityBackpressureError(AuthorityStateError):
    """Raised when a realtime channel would exceed its governed capacity."""


class AuthorityResyncRequired(AuthorityStateError):
    """Raised when a reconnect cursor predates retained authoritative events."""


def _stable_id(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _STABLE_ID_RE.fullmatch(value) is None:
        raise AuthorityPolicyError(f"{field} must be a stable identifier")
    return value


def _bounded_int(value: int, *, field: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise AuthorityPolicyError(f"{field} must be an integer in [{minimum}, {maximum}]")
    return value


def _bounded_mapping(value: Mapping[str, Any], *, field: str, max_bytes: int) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise AuthorityPolicyError(f"{field} must be a mapping")
    normalized = dict(value)
    try:
        encoded = canonical_json_bytes(normalized)
    except ValueError as exc:
        raise AuthorityPolicyError(f"{field} must be canonical JSON data") from exc
    if len(encoded) > max_bytes:
        raise AuthorityPolicyError(f"{field} exceeds {max_bytes} bytes")
    return normalized


def _reject_reserved_client_fields(value: Any, *, path: str = "payload") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise AuthorityPolicyError(f"{path} keys must be strings")
            if key in _RESERVED_CLIENT_FIELDS:
                raise AuthorityPolicyError(f"client payload cannot set reserved field {key!r}")
            _reject_reserved_client_fields(nested, path=f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, nested in enumerate(value):
            _reject_reserved_client_fields(nested, path=f"{path}[{index}]")


class AuthorityCommandStatus(StrEnum):
    APPLIED = "applied"
    DUPLICATE = "duplicate"
    REJECTED = "rejected"


class AuthorityRejectReason(StrEnum):
    ACTOR_MISMATCH = "actor_mismatch"
    SESSION_MISMATCH = "session_mismatch"
    UNAUTHORIZED = "unauthorized"
    OBJECT_FORBIDDEN = "object_forbidden"
    UNKNOWN_COMMAND = "unknown_command"
    STALE_REVISION = "stale_revision"
    OUT_OF_ORDER = "out_of_order"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    LEASE_EXPIRED = "lease_expired"


class AuthorityTransportKind(StrEnum):
    REQUEST_RESPONSE = "request_response"
    REALTIME_STREAM = "realtime_stream"


@dataclass(frozen=True, slots=True)
class AuthorityDomainIdentity:
    domain_id: str

    def __post_init__(self) -> None:
        _stable_id(self.domain_id, field="domain_id")

    def canonical(self) -> dict[str, str]:
        return {"domain_id": self.domain_id}


@dataclass(frozen=True, slots=True)
class AuthorityActorContext:
    account_id: str
    session_id: str
    permissions: tuple[str, ...]
    authorized_object_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _stable_id(self.account_id, field="account_id")
        _stable_id(self.session_id, field="session_id")
        permissions: set[str] = set()
        for permission in self.permissions:
            if permission == "*":
                permissions.add(permission)
            else:
                permissions.add(_stable_id(permission, field="permission"))
        if not permissions:
            raise AuthorityPolicyError("at least one authority permission is required")
        object_ids = tuple(sorted({_stable_id(item, field="authorized_object_id") for item in self.authorized_object_ids}))
        object.__setattr__(self, "permissions", tuple(sorted(permissions)))
        object.__setattr__(self, "authorized_object_ids", object_ids)

    def can(self, command_type: str, target_id: str) -> bool:
        permission_ok = "*" in self.permissions or command_type in self.permissions
        object_ok = "*" in self.authorized_object_ids or target_id in self.authorized_object_ids
        return permission_ok and object_ok

    def canonical(self) -> dict[str, Any]:
        return {
            "account_id": self.account_id,
            "session_id": self.session_id,
            "permissions": list(self.permissions),
            "authorized_object_ids": list(self.authorized_object_ids),
        }


@dataclass(frozen=True, slots=True)
class AuthorityCommand:
    command_id: str
    domain_id: str
    actor_id: str
    session_id: str
    command_type: str
    target_id: str
    expected_revision: int
    sequence: int
    idempotency_key: str
    payload: Mapping[str, Any]
    max_payload_bytes: int = 64 * 1024

    def __post_init__(self) -> None:
        for field in (
            "command_id",
            "domain_id",
            "actor_id",
            "session_id",
            "command_type",
            "target_id",
            "idempotency_key",
        ):
            _stable_id(getattr(self, field), field=field)
        _bounded_int(self.expected_revision, field="expected_revision", minimum=0, maximum=2**63 - 1)
        _bounded_int(self.sequence, field="sequence", minimum=1, maximum=2**63 - 1)
        _bounded_int(self.max_payload_bytes, field="max_payload_bytes", minimum=1, maximum=4 * 1024 * 1024)
        payload = _bounded_mapping(self.payload, field="payload", max_bytes=self.max_payload_bytes)
        _reject_reserved_client_fields(payload)
        object.__setattr__(self, "payload", payload)

    def canonical(self) -> dict[str, Any]:
        return {
            "command_id": self.command_id,
            "domain_id": self.domain_id,
            "actor_id": self.actor_id,
            "session_id": self.session_id,
            "command_type": self.command_type,
            "target_id": self.target_id,
            "expected_revision": self.expected_revision,
            "sequence": self.sequence,
            "idempotency_key": self.idempotency_key,
            "payload": dict(self.payload),
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class AuthorityStateSnapshot:
    domain_id: str
    target_id: str
    revision: int
    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        _stable_id(self.domain_id, field="domain_id")
        _stable_id(self.target_id, field="target_id")
        _bounded_int(self.revision, field="revision", minimum=0, maximum=2**63 - 1)
        object.__setattr__(self, "payload", _bounded_mapping(self.payload, field="state payload", max_bytes=4 * 1024 * 1024))

    def canonical(self) -> dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "target_id": self.target_id,
            "revision": self.revision,
            "payload": dict(self.payload),
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class AuthorityEvent:
    event_id: str
    domain_id: str
    target_id: str
    command_id: str
    revision: int
    event_sequence: int
    event_type: str
    server_time_ms: int
    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        for field in ("event_id", "domain_id", "target_id", "command_id", "event_type"):
            _stable_id(getattr(self, field), field=field)
        _bounded_int(self.revision, field="revision", minimum=1, maximum=2**63 - 1)
        _bounded_int(self.event_sequence, field="event_sequence", minimum=1, maximum=2**63 - 1)
        _bounded_int(self.server_time_ms, field="server_time_ms", minimum=0, maximum=2**63 - 1)
        object.__setattr__(self, "payload", _bounded_mapping(self.payload, field="event payload", max_bytes=4 * 1024 * 1024))

    def canonical(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "domain_id": self.domain_id,
            "target_id": self.target_id,
            "command_id": self.command_id,
            "revision": self.revision,
            "event_sequence": self.event_sequence,
            "event_type": self.event_type,
            "server_time_ms": self.server_time_ms,
            "payload": dict(self.payload),
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class AuthorityCommandOutcome:
    command_id: str
    status: AuthorityCommandStatus
    reason: AuthorityRejectReason | None
    state: AuthorityStateSnapshot | None
    event: AuthorityEvent | None
    duplicate_of: str | None = None

    def __post_init__(self) -> None:
        _stable_id(self.command_id, field="command_id")
        if self.duplicate_of is not None:
            _stable_id(self.duplicate_of, field="duplicate_of")
        if self.status is AuthorityCommandStatus.REJECTED:
            if self.reason is None or self.state is not None or self.event is not None:
                raise AuthorityPolicyError("rejected outcome must contain only a reason")
        elif self.status is AuthorityCommandStatus.APPLIED:
            if self.reason is not None or self.state is None or self.event is None or self.duplicate_of is not None:
                raise AuthorityPolicyError("applied outcome must contain state and event")
        elif self.status is AuthorityCommandStatus.DUPLICATE:
            if self.reason is not None or self.state is None or self.event is None or self.duplicate_of is None:
                raise AuthorityPolicyError("duplicate outcome must point to the original command")

    @classmethod
    def rejected(cls, command_id: str, reason: AuthorityRejectReason) -> AuthorityCommandOutcome:
        return cls(command_id, AuthorityCommandStatus.REJECTED, reason, None, None)

    def canonical(self) -> dict[str, Any]:
        return {
            "command_id": self.command_id,
            "status": self.status.value,
            "reason": None if self.reason is None else self.reason.value,
            "state": None if self.state is None else self.state.canonical(),
            "event": None if self.event is None else self.event.canonical(),
            "duplicate_of": self.duplicate_of,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


AuthorityHandler = Callable[
    [Mapping[str, Any], Mapping[str, Any]],
    tuple[Mapping[str, Any], str, Mapping[str, Any]],
]


class InMemoryAuthorityStore:
    """Deterministic transactional fixture store used by local/core acceptance."""

    def __init__(self) -> None:
        self._states: dict[tuple[str, str], AuthorityStateSnapshot] = {}
        self._session_sequences: dict[tuple[str, str], int] = {}
        self._idempotency: dict[tuple[str, str], tuple[str, AuthorityCommandOutcome]] = {}
        self._events: list[AuthorityEvent] = []
        self._event_sequence = 0
        self._lock = threading.RLock()

    def snapshot(self, domain_id: str, target_id: str) -> AuthorityStateSnapshot:
        _stable_id(domain_id, field="domain_id")
        _stable_id(target_id, field="target_id")
        with self._lock:
            return self._states.get(
                (domain_id, target_id),
                AuthorityStateSnapshot(domain_id, target_id, 0, {}),
            )

    def events(self) -> tuple[AuthorityEvent, ...]:
        with self._lock:
            return tuple(self._events)

    def last_session_sequence(self, domain_id: str, session_id: str) -> int:
        with self._lock:
            return self._session_sequences.get((domain_id, session_id), 0)

    def _process_atomic(
        self,
        command: AuthorityCommand,
        handler: AuthorityHandler,
        *,
        server_time_ms: int,
    ) -> AuthorityCommandOutcome:
        with self._lock:
            idem_key = (command.domain_id, command.idempotency_key)
            command_digest = command.digest()
            existing = self._idempotency.get(idem_key)
            if existing is not None:
                existing_digest, existing_outcome = existing
                if existing_digest != command_digest:
                    return AuthorityCommandOutcome.rejected(
                        command.command_id,
                        AuthorityRejectReason.IDEMPOTENCY_CONFLICT,
                    )
                return replace(
                    existing_outcome,
                    status=AuthorityCommandStatus.DUPLICATE,
                    duplicate_of=existing_outcome.command_id,
                )

            sequence_key = (command.domain_id, command.session_id)
            next_sequence = self._session_sequences.get(sequence_key, 0) + 1
            if command.sequence != next_sequence:
                return AuthorityCommandOutcome.rejected(
                    command.command_id,
                    AuthorityRejectReason.OUT_OF_ORDER,
                )

            state_key = (command.domain_id, command.target_id)
            current = self._states.get(
                state_key,
                AuthorityStateSnapshot(command.domain_id, command.target_id, 0, {}),
            )
            if command.expected_revision != current.revision:
                return AuthorityCommandOutcome.rejected(
                    command.command_id,
                    AuthorityRejectReason.STALE_REVISION,
                )

            # Handler execution happens before any fixture mutation. Exceptions therefore
            # leave state, event sequence, idempotency and client sequence unchanged.
            new_payload, event_type, event_payload = handler(dict(current.payload), dict(command.payload))
            new_payload = _bounded_mapping(new_payload, field="handler state", max_bytes=4 * 1024 * 1024)
            event_payload = _bounded_mapping(event_payload, field="handler event", max_bytes=4 * 1024 * 1024)
            _stable_id(event_type, field="event_type")

            next_revision = current.revision + 1
            next_event_sequence = self._event_sequence + 1
            event_id = canonical_sha256(
                {
                    "domain_id": command.domain_id,
                    "command_id": command.command_id,
                    "revision": next_revision,
                    "event_sequence": next_event_sequence,
                }
            )[:32]
            state = AuthorityStateSnapshot(
                command.domain_id,
                command.target_id,
                next_revision,
                new_payload,
            )
            event = AuthorityEvent(
                event_id=event_id,
                domain_id=command.domain_id,
                target_id=command.target_id,
                command_id=command.command_id,
                revision=next_revision,
                event_sequence=next_event_sequence,
                event_type=event_type,
                server_time_ms=server_time_ms,
                payload=event_payload,
            )
            outcome = AuthorityCommandOutcome(
                command_id=command.command_id,
                status=AuthorityCommandStatus.APPLIED,
                reason=None,
                state=state,
                event=event,
            )

            self._states[state_key] = state
            self._session_sequences[sequence_key] = command.sequence
            self._event_sequence = next_event_sequence
            self._events.append(event)
            self._idempotency[idem_key] = (command_digest, outcome)
            return outcome


class AuthoritativeCommandProcessor:
    def __init__(
        self,
        store: InMemoryAuthorityStore,
        *,
        clock_ms: Callable[[], int],
        max_pending_commands: int = 128,
    ) -> None:
        self.store = store
        self._clock_ms = clock_ms
        self._handlers: dict[str, AuthorityHandler] = {}
        self._pending = 0
        self._pending_lock = threading.Lock()
        self.max_pending_commands = _bounded_int(
            max_pending_commands,
            field="max_pending_commands",
            minimum=1,
            maximum=65_536,
        )

    def register_handler(self, command_type: str, handler: AuthorityHandler) -> None:
        command_type = _stable_id(command_type, field="command_type")
        if command_type in self._handlers:
            raise AuthorityPolicyError(f"handler already registered for {command_type}")
        if not callable(handler):
            raise AuthorityPolicyError("authority handler must be callable")
        self._handlers[command_type] = handler

    def process(
        self,
        command: AuthorityCommand,
        actor: AuthorityActorContext,
    ) -> AuthorityCommandOutcome:
        with self._pending_lock:
            if self._pending >= self.max_pending_commands:
                raise AuthorityBackpressureError("authoritative command queue capacity reached")
            self._pending += 1
        try:
            if command.actor_id != actor.account_id:
                return AuthorityCommandOutcome.rejected(
                    command.command_id,
                    AuthorityRejectReason.ACTOR_MISMATCH,
                )
            if command.session_id != actor.session_id:
                return AuthorityCommandOutcome.rejected(
                    command.command_id,
                    AuthorityRejectReason.SESSION_MISMATCH,
                )
            permission_ok = "*" in actor.permissions or command.command_type in actor.permissions
            if not permission_ok:
                return AuthorityCommandOutcome.rejected(
                    command.command_id,
                    AuthorityRejectReason.UNAUTHORIZED,
                )
            object_ok = "*" in actor.authorized_object_ids or command.target_id in actor.authorized_object_ids
            if not object_ok:
                return AuthorityCommandOutcome.rejected(
                    command.command_id,
                    AuthorityRejectReason.OBJECT_FORBIDDEN,
                )
            handler = self._handlers.get(command.command_type)
            if handler is None:
                return AuthorityCommandOutcome.rejected(
                    command.command_id,
                    AuthorityRejectReason.UNKNOWN_COMMAND,
                )
            now = self._clock_ms()
            _bounded_int(now, field="server clock", minimum=0, maximum=2**63 - 1)
            return self.store._process_atomic(command, handler, server_time_ms=now)
        finally:
            with self._pending_lock:
                self._pending -= 1


@dataclass(frozen=True, slots=True)
class AuthorityLease:
    lease_id: str
    session_id: str
    issued_at_ms: int
    expires_at_ms: int
    resume_after_event_sequence: int

    def __post_init__(self) -> None:
        _stable_id(self.lease_id, field="lease_id")
        _stable_id(self.session_id, field="session_id")
        _bounded_int(self.issued_at_ms, field="issued_at_ms", minimum=0, maximum=2**63 - 1)
        _bounded_int(self.expires_at_ms, field="expires_at_ms", minimum=1, maximum=2**63 - 1)
        _bounded_int(
            self.resume_after_event_sequence,
            field="resume_after_event_sequence",
            minimum=0,
            maximum=2**63 - 1,
        )
        if self.expires_at_ms <= self.issued_at_ms:
            raise AuthorityPolicyError("lease expiry must follow issuance")

    def canonical(self) -> dict[str, Any]:
        return {
            "lease_id": self.lease_id,
            "session_id": self.session_id,
            "issued_at_ms": self.issued_at_ms,
            "expires_at_ms": self.expires_at_ms,
            "resume_after_event_sequence": self.resume_after_event_sequence,
        }


class AuthorityLeaseRegistry:
    def __init__(self, *, clock_ms: Callable[[], int], max_ttl_ms: int = 60_000) -> None:
        self._clock_ms = clock_ms
        self.max_ttl_ms = _bounded_int(max_ttl_ms, field="max_ttl_ms", minimum=1, maximum=3_600_000)
        self._counter = 0
        self._leases: dict[str, AuthorityLease] = {}
        self._lock = threading.Lock()

    def issue(self, session_id: str, *, ttl_ms: int, resume_after_event_sequence: int) -> AuthorityLease:
        _stable_id(session_id, field="session_id")
        ttl_ms = _bounded_int(ttl_ms, field="ttl_ms", minimum=1, maximum=self.max_ttl_ms)
        _bounded_int(
            resume_after_event_sequence,
            field="resume_after_event_sequence",
            minimum=0,
            maximum=2**63 - 1,
        )
        with self._lock:
            now = self._clock_ms()
            _bounded_int(now, field="server clock", minimum=0, maximum=2**63 - 1)
            self._counter += 1
            lease_id = canonical_sha256(
                {"session_id": session_id, "issued_at_ms": now, "counter": self._counter}
            )[:32]
            lease = AuthorityLease(
                lease_id,
                session_id,
                now,
                now + ttl_ms,
                resume_after_event_sequence,
            )
            self._leases[lease_id] = lease
            return lease

    def validate(self, lease_id: str, session_id: str) -> AuthorityLease:
        _stable_id(lease_id, field="lease_id")
        _stable_id(session_id, field="session_id")
        with self._lock:
            lease = self._leases.get(lease_id)
            now = self._clock_ms()
            if lease is None or lease.session_id != session_id or now >= lease.expires_at_ms:
                raise AuthorityStateError(AuthorityRejectReason.LEASE_EXPIRED.value)
            return lease

    def revoke(self, lease_id: str) -> None:
        _stable_id(lease_id, field="lease_id")
        with self._lock:
            self._leases.pop(lease_id, None)


@dataclass(frozen=True, slots=True)
class AuthorityTransportEnvelope:
    request_id: str
    transport: AuthorityTransportKind
    message_kind: str
    payload_digest: str
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        _stable_id(self.request_id, field="request_id")
        _stable_id(self.message_kind, field="message_kind")
        if not isinstance(self.payload_digest, str) or re.fullmatch(r"[0-9a-f]{64}", self.payload_digest) is None:
            raise AuthorityPolicyError("payload_digest must be lowercase SHA-256")
        if self.correlation_id is not None:
            _stable_id(self.correlation_id, field="correlation_id")

    def canonical(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "transport": self.transport.value,
            "message_kind": self.message_kind,
            "payload_digest": self.payload_digest,
            "correlation_id": self.correlation_id,
        }


class RealtimeAuthorityBuffer:
    """Bounded authoritative event buffer with explicit reconnect/resync semantics."""

    def __init__(self, *, max_events: int = 128, max_bytes: int = 2 * 1024 * 1024) -> None:
        self.max_events = _bounded_int(max_events, field="max_events", minimum=1, maximum=65_536)
        self.max_bytes = _bounded_int(max_bytes, field="max_bytes", minimum=1, maximum=64 * 1024 * 1024)
        self._events: list[AuthorityEvent] = []
        self._bytes = 0
        self._retention_floor = 0
        self._lock = threading.Lock()

    @staticmethod
    def _event_size(event: AuthorityEvent) -> int:
        return len(canonical_json_bytes(event.canonical()))

    def publish(self, event: AuthorityEvent) -> None:
        size = self._event_size(event)
        with self._lock:
            if self._events and event.event_sequence <= self._events[-1].event_sequence:
                raise AuthorityStateError("realtime events must be strictly increasing")
            if len(self._events) >= self.max_events or self._bytes + size > self.max_bytes:
                raise AuthorityBackpressureError("realtime event buffer capacity reached")
            self._events.append(event)
            self._bytes += size

    def acknowledge(self, event_sequence: int) -> None:
        _bounded_int(event_sequence, field="event_sequence", minimum=0, maximum=2**63 - 1)
        with self._lock:
            keep: list[AuthorityEvent] = []
            removed_floor = self._retention_floor
            size = 0
            for event in self._events:
                if event.event_sequence <= event_sequence:
                    removed_floor = max(removed_floor, event.event_sequence)
                else:
                    keep.append(event)
                    size += self._event_size(event)
            self._events = keep
            self._bytes = size
            self._retention_floor = removed_floor

    def resume(self, after_event_sequence: int) -> tuple[AuthorityEvent, ...]:
        _bounded_int(
            after_event_sequence,
            field="after_event_sequence",
            minimum=0,
            maximum=2**63 - 1,
        )
        with self._lock:
            if after_event_sequence < self._retention_floor:
                raise AuthorityResyncRequired("reconnect cursor predates retained authoritative history")
            return tuple(event for event in self._events if event.event_sequence > after_event_sequence)

    @property
    def pending_events(self) -> int:
        with self._lock:
            return len(self._events)

    @property
    def pending_bytes(self) -> int:
        with self._lock:
            return self._bytes
