from __future__ import annotations

import re
import threading
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any, Callable, Mapping, Sequence

from .authority import AuthorityActorContext
from .contracts import canonical_json_bytes, canonical_sha256

_STABLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_RESERVED_CLIENT_FIELDS = frozenset(
    {
        "authorized",
        "expires_at_ms",
        "grant_id",
        "match_id",
        "presence_revision",
        "reservation_id",
        "revision",
        "server_time_ms",
        "status",
    }
)


class MatchmakingPolicyError(ValueError):
    """Raised when a matchmaking/lobby contract is structurally unsafe."""


class MatchmakingStateError(RuntimeError):
    """Raised when an authoritative matchmaking state transition is invalid."""


class MatchmakingAuthorizationError(MatchmakingStateError):
    """Raised when an authenticated actor lacks function/object authority."""


class MatchmakingCapacityError(MatchmakingStateError):
    """Raised when a governed lobby/queue/reservation capacity is exhausted."""


def _stable_id(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _STABLE_ID_RE.fullmatch(value) is None:
        raise MatchmakingPolicyError(f"{field} must be a stable identifier")
    return value


def _bounded_int(value: int, *, field: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise MatchmakingPolicyError(f"{field} must be an integer in [{minimum}, {maximum}]")
    return value


def _canonical_mapping(value: Mapping[str, Any], *, field: str, max_bytes: int) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise MatchmakingPolicyError(f"{field} must be a mapping")
    normalized = dict(value)
    try:
        encoded = canonical_json_bytes(normalized)
    except ValueError as exc:
        raise MatchmakingPolicyError(f"{field} must contain canonical JSON data") from exc
    if len(encoded) > max_bytes:
        raise MatchmakingPolicyError(f"{field} exceeds {max_bytes} bytes")
    _reject_reserved_fields(normalized, path=field)
    return normalized


def _reject_reserved_fields(value: Any, *, path: str) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise MatchmakingPolicyError(f"{path} keys must be strings")
            if key in _RESERVED_CLIENT_FIELDS:
                raise MatchmakingPolicyError(f"client data cannot set reserved field {key!r}")
            _reject_reserved_fields(nested, path=f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, nested in enumerate(value):
            _reject_reserved_fields(nested, path=f"{path}[{index}]")


def _now(clock_ms: Callable[[], int]) -> int:
    return _bounded_int(clock_ms(), field="server clock", minimum=0, maximum=2**63 - 1)


def _authorize(actor: AuthorityActorContext, permission: str, target_id: str) -> None:
    _stable_id(permission, field="permission")
    _stable_id(target_id, field="target_id")
    if not actor.can(permission, target_id):
        raise MatchmakingAuthorizationError("forbidden")


class LobbyRole(StrEnum):
    OWNER = "owner"
    MEMBER = "member"


class LobbyStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class TicketStatus(StrEnum):
    QUEUED = "queued"
    MATCHED = "matched"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ReservationStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class PresenceState(StrEnum):
    OFFLINE = "offline"
    ONLINE = "online"
    IN_LOBBY = "in_lobby"
    IN_MATCH = "in_match"


@dataclass(frozen=True, slots=True)
class LobbyMember:
    account_id: str
    session_id: str
    role: LobbyRole
    joined_at_ms: int

    def __post_init__(self) -> None:
        _stable_id(self.account_id, field="account_id")
        _stable_id(self.session_id, field="session_id")
        _bounded_int(self.joined_at_ms, field="joined_at_ms", minimum=0, maximum=2**63 - 1)

    def canonical(self) -> dict[str, Any]:
        return {
            "account_id": self.account_id,
            "session_id": self.session_id,
            "role": self.role.value,
            "joined_at_ms": self.joined_at_ms,
        }


@dataclass(frozen=True, slots=True)
class LobbySnapshot:
    lobby_id: str
    revision: int
    status: LobbyStatus
    max_members: int
    members: tuple[LobbyMember, ...]

    def __post_init__(self) -> None:
        _stable_id(self.lobby_id, field="lobby_id")
        _bounded_int(self.revision, field="revision", minimum=1, maximum=2**63 - 1)
        _bounded_int(self.max_members, field="max_members", minimum=1, maximum=512)
        if not self.members:
            raise MatchmakingPolicyError("lobby must contain an owner")
        if len(self.members) > self.max_members:
            raise MatchmakingPolicyError("lobby membership exceeds max_members")
        accounts = [member.account_id for member in self.members]
        if len(accounts) != len(set(accounts)):
            raise MatchmakingPolicyError("lobby member accounts must be unique")
        if sum(member.role is LobbyRole.OWNER for member in self.members) != 1:
            raise MatchmakingPolicyError("lobby must contain exactly one owner")

    def canonical(self) -> dict[str, Any]:
        return {
            "lobby_id": self.lobby_id,
            "revision": self.revision,
            "status": self.status.value,
            "max_members": self.max_members,
            "members": [member.canonical() for member in self.members],
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())

    def member(self, account_id: str) -> LobbyMember | None:
        for member in self.members:
            if member.account_id == account_id:
                return member
        return None


@dataclass(frozen=True, slots=True)
class MatchmakingTicket:
    ticket_id: str
    account_id: str
    session_id: str
    criteria: Mapping[str, Any]
    criteria_digest: str
    created_at_ms: int
    expires_at_ms: int
    queue_sequence: int
    revision: int
    status: TicketStatus
    match_id: str | None = None
    reservation_id: str | None = None

    def __post_init__(self) -> None:
        for field in ("ticket_id", "account_id", "session_id"):
            _stable_id(getattr(self, field), field=field)
        criteria = _canonical_mapping(self.criteria, field="criteria", max_bytes=16 * 1024)
        object.__setattr__(self, "criteria", criteria)
        expected_digest = canonical_sha256(criteria)
        if self.criteria_digest != expected_digest:
            raise MatchmakingPolicyError("criteria_digest does not match criteria")
        _bounded_int(self.created_at_ms, field="created_at_ms", minimum=0, maximum=2**63 - 1)
        _bounded_int(self.expires_at_ms, field="expires_at_ms", minimum=1, maximum=2**63 - 1)
        if self.expires_at_ms <= self.created_at_ms:
            raise MatchmakingPolicyError("ticket expiry must follow creation")
        _bounded_int(self.queue_sequence, field="queue_sequence", minimum=1, maximum=2**63 - 1)
        _bounded_int(self.revision, field="revision", minimum=1, maximum=2**63 - 1)
        if self.status is TicketStatus.MATCHED:
            if self.match_id is None or self.reservation_id is None:
                raise MatchmakingPolicyError("matched ticket requires match and reservation identities")
        elif self.match_id is not None or self.reservation_id is not None:
            raise MatchmakingPolicyError("unmatched ticket cannot carry match/reservation identity")
        if self.match_id is not None:
            _stable_id(self.match_id, field="match_id")
        if self.reservation_id is not None:
            _stable_id(self.reservation_id, field="reservation_id")

    def canonical(self) -> dict[str, Any]:
        return {
            "ticket_id": self.ticket_id,
            "account_id": self.account_id,
            "session_id": self.session_id,
            "criteria": dict(self.criteria),
            "criteria_digest": self.criteria_digest,
            "created_at_ms": self.created_at_ms,
            "expires_at_ms": self.expires_at_ms,
            "queue_sequence": self.queue_sequence,
            "revision": self.revision,
            "status": self.status.value,
            "match_id": self.match_id,
            "reservation_id": self.reservation_id,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class MatchReservation:
    reservation_id: str
    match_id: str
    ticket_ids: tuple[str, ...]
    account_ids: tuple[str, ...]
    session_ids: tuple[str, ...]
    criteria_digest: str
    created_at_ms: int
    expires_at_ms: int
    revision: int
    status: ReservationStatus

    def __post_init__(self) -> None:
        _stable_id(self.reservation_id, field="reservation_id")
        _stable_id(self.match_id, field="match_id")
        if not self.ticket_ids or len(self.ticket_ids) != len(self.account_ids) or len(self.ticket_ids) != len(self.session_ids):
            raise MatchmakingPolicyError("reservation identities must be non-empty and aligned")
        if len(set(self.ticket_ids)) != len(self.ticket_ids) or len(set(self.account_ids)) != len(self.account_ids):
            raise MatchmakingPolicyError("reservation ticket/account identities must be unique")
        for value in self.ticket_ids:
            _stable_id(value, field="ticket_id")
        for value in self.account_ids:
            _stable_id(value, field="account_id")
        for value in self.session_ids:
            _stable_id(value, field="session_id")
        if not isinstance(self.criteria_digest, str) or re.fullmatch(r"[0-9a-f]{64}", self.criteria_digest) is None:
            raise MatchmakingPolicyError("criteria_digest must be lowercase SHA-256")
        _bounded_int(self.created_at_ms, field="created_at_ms", minimum=0, maximum=2**63 - 1)
        _bounded_int(self.expires_at_ms, field="expires_at_ms", minimum=1, maximum=2**63 - 1)
        if self.expires_at_ms <= self.created_at_ms:
            raise MatchmakingPolicyError("reservation expiry must follow creation")
        _bounded_int(self.revision, field="revision", minimum=1, maximum=2**63 - 1)

    def canonical(self) -> dict[str, Any]:
        return {
            "reservation_id": self.reservation_id,
            "match_id": self.match_id,
            "ticket_ids": list(self.ticket_ids),
            "account_ids": list(self.account_ids),
            "session_ids": list(self.session_ids),
            "criteria_digest": self.criteria_digest,
            "created_at_ms": self.created_at_ms,
            "expires_at_ms": self.expires_at_ms,
            "revision": self.revision,
            "status": self.status.value,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class PresenceSnapshot:
    account_id: str
    session_id: str
    revision: int
    state: PresenceState
    lobby_id: str | None
    match_id: str | None
    server_time_ms: int

    def __post_init__(self) -> None:
        _stable_id(self.account_id, field="account_id")
        _stable_id(self.session_id, field="session_id")
        _bounded_int(self.revision, field="revision", minimum=1, maximum=2**63 - 1)
        _bounded_int(self.server_time_ms, field="server_time_ms", minimum=0, maximum=2**63 - 1)
        if self.lobby_id is not None:
            _stable_id(self.lobby_id, field="lobby_id")
        if self.match_id is not None:
            _stable_id(self.match_id, field="match_id")

    def canonical(self) -> dict[str, Any]:
        return {
            "account_id": self.account_id,
            "session_id": self.session_id,
            "revision": self.revision,
            "state": self.state.value,
            "lobby_id": self.lobby_id,
            "match_id": self.match_id,
            "server_time_ms": self.server_time_ms,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class ReconnectGrant:
    grant_id: str
    account_id: str
    session_id: str
    reservation_id: str
    match_id: str
    issued_at_ms: int
    expires_at_ms: int

    def __post_init__(self) -> None:
        for field in ("grant_id", "account_id", "session_id", "reservation_id", "match_id"):
            _stable_id(getattr(self, field), field=field)
        _bounded_int(self.issued_at_ms, field="issued_at_ms", minimum=0, maximum=2**63 - 1)
        _bounded_int(self.expires_at_ms, field="expires_at_ms", minimum=1, maximum=2**63 - 1)
        if self.expires_at_ms <= self.issued_at_ms:
            raise MatchmakingPolicyError("reconnect grant expiry must follow issuance")

    def canonical(self) -> dict[str, Any]:
        return {
            "grant_id": self.grant_id,
            "account_id": self.account_id,
            "session_id": self.session_id,
            "reservation_id": self.reservation_id,
            "match_id": self.match_id,
            "issued_at_ms": self.issued_at_ms,
            "expires_at_ms": self.expires_at_ms,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


class InMemoryMatchmakingService:
    """Deterministic authoritative R14.7 fixture service.

    The service is intentionally provider-neutral. All authoritative mutations happen
    under one lock so local/core acceptance can prove lifecycle invariants without
    pretending this fixture is an Internet-scale distributed matcher.
    """

    def __init__(
        self,
        *,
        clock_ms: Callable[[], int],
        max_queued_tickets: int = 1024,
        max_active_reservations: int = 512,
        max_ticket_ttl_ms: int = 300_000,
        max_reservation_ttl_ms: int = 120_000,
        max_reconnect_ttl_ms: int = 30_000,
    ) -> None:
        self._clock_ms = clock_ms
        self.max_queued_tickets = _bounded_int(max_queued_tickets, field="max_queued_tickets", minimum=1, maximum=100_000)
        self.max_active_reservations = _bounded_int(max_active_reservations, field="max_active_reservations", minimum=1, maximum=100_000)
        self.max_ticket_ttl_ms = _bounded_int(max_ticket_ttl_ms, field="max_ticket_ttl_ms", minimum=1, maximum=3_600_000)
        self.max_reservation_ttl_ms = _bounded_int(max_reservation_ttl_ms, field="max_reservation_ttl_ms", minimum=1, maximum=3_600_000)
        self.max_reconnect_ttl_ms = _bounded_int(max_reconnect_ttl_ms, field="max_reconnect_ttl_ms", minimum=1, maximum=600_000)
        self._lobbies: dict[str, LobbySnapshot] = {}
        self._tickets: dict[str, MatchmakingTicket] = {}
        self._ticket_request_digests: dict[str, str] = {}
        self._reservations: dict[str, MatchReservation] = {}
        self._presence: dict[str, PresenceSnapshot] = {}
        self._reconnect: dict[str, ReconnectGrant] = {}
        self._ticket_sequence = 0
        self._match_sequence = 0
        self._grant_sequence = 0
        self._lock = threading.RLock()

    def lobby(self, lobby_id: str) -> LobbySnapshot:
        _stable_id(lobby_id, field="lobby_id")
        with self._lock:
            lobby = self._lobbies.get(lobby_id)
            if lobby is None:
                raise MatchmakingStateError("lobby_not_found")
            return lobby

    def ticket(self, ticket_id: str) -> MatchmakingTicket:
        _stable_id(ticket_id, field="ticket_id")
        with self._lock:
            self._expire_locked(_now(self._clock_ms))
            ticket = self._tickets.get(ticket_id)
            if ticket is None:
                raise MatchmakingStateError("ticket_not_found")
            return ticket

    def reservation(self, reservation_id: str) -> MatchReservation:
        _stable_id(reservation_id, field="reservation_id")
        with self._lock:
            self._expire_locked(_now(self._clock_ms))
            reservation = self._reservations.get(reservation_id)
            if reservation is None:
                raise MatchmakingStateError("reservation_not_found")
            return reservation

    def presence(self, account_id: str) -> PresenceSnapshot | None:
        _stable_id(account_id, field="account_id")
        with self._lock:
            return self._presence.get(account_id)

    def lobbies(self) -> tuple[LobbySnapshot, ...]:
        with self._lock:
            return tuple(self._lobbies[key] for key in sorted(self._lobbies))

    def tickets(self) -> tuple[MatchmakingTicket, ...]:
        with self._lock:
            self._expire_locked(_now(self._clock_ms))
            return tuple(self._tickets[key] for key in sorted(self._tickets))

    def reservations(self) -> tuple[MatchReservation, ...]:
        with self._lock:
            self._expire_locked(_now(self._clock_ms))
            return tuple(self._reservations[key] for key in sorted(self._reservations))

    def create_lobby(self, lobby_id: str, actor: AuthorityActorContext, *, max_members: int = 4) -> LobbySnapshot:
        lobby_id = _stable_id(lobby_id, field="lobby_id")
        _authorize(actor, "lobby.create", lobby_id)
        max_members = _bounded_int(max_members, field="max_members", minimum=1, maximum=512)
        with self._lock:
            if lobby_id in self._lobbies:
                raise MatchmakingStateError("lobby_exists")
            now = _now(self._clock_ms)
            lobby = LobbySnapshot(
                lobby_id=lobby_id,
                revision=1,
                status=LobbyStatus.OPEN,
                max_members=max_members,
                members=(LobbyMember(actor.account_id, actor.session_id, LobbyRole.OWNER, now),),
            )
            self._lobbies[lobby_id] = lobby
            return lobby

    def join_lobby(self, lobby_id: str, actor: AuthorityActorContext) -> LobbySnapshot:
        lobby_id = _stable_id(lobby_id, field="lobby_id")
        _authorize(actor, "lobby.join", lobby_id)
        with self._lock:
            lobby = self._require_lobby_locked(lobby_id)
            existing = lobby.member(actor.account_id)
            if existing is not None:
                if existing.session_id != actor.session_id:
                    raise MatchmakingAuthorizationError("member_session_mismatch")
                return lobby
            if lobby.status is not LobbyStatus.OPEN:
                raise MatchmakingStateError("lobby_closed")
            if len(lobby.members) >= lobby.max_members:
                raise MatchmakingCapacityError("lobby_capacity")
            member = LobbyMember(actor.account_id, actor.session_id, LobbyRole.MEMBER, _now(self._clock_ms))
            updated = replace(lobby, revision=lobby.revision + 1, members=lobby.members + (member,))
            self._lobbies[lobby_id] = updated
            return updated

    def remove_member(self, lobby_id: str, member_account_id: str, actor: AuthorityActorContext) -> LobbySnapshot:
        lobby_id = _stable_id(lobby_id, field="lobby_id")
        member_account_id = _stable_id(member_account_id, field="member_account_id")
        _authorize(actor, "lobby.member.remove", lobby_id)
        with self._lock:
            lobby = self._require_lobby_locked(lobby_id)
            requester = lobby.member(actor.account_id)
            target = lobby.member(member_account_id)
            if requester is None or target is None:
                raise MatchmakingAuthorizationError("member_not_authorized")
            if target.role is LobbyRole.OWNER:
                raise MatchmakingStateError("owner_cannot_be_removed")
            if actor.account_id != member_account_id and requester.role is not LobbyRole.OWNER:
                raise MatchmakingAuthorizationError("owner_required")
            members = tuple(item for item in lobby.members if item.account_id != member_account_id)
            updated = replace(lobby, revision=lobby.revision + 1, members=members)
            self._lobbies[lobby_id] = updated
            return updated

    def close_lobby(self, lobby_id: str, actor: AuthorityActorContext) -> LobbySnapshot:
        lobby_id = _stable_id(lobby_id, field="lobby_id")
        _authorize(actor, "lobby.close", lobby_id)
        with self._lock:
            lobby = self._require_lobby_locked(lobby_id)
            requester = lobby.member(actor.account_id)
            if requester is None or requester.role is not LobbyRole.OWNER:
                raise MatchmakingAuthorizationError("owner_required")
            if lobby.status is LobbyStatus.CLOSED:
                return lobby
            updated = replace(lobby, revision=lobby.revision + 1, status=LobbyStatus.CLOSED)
            self._lobbies[lobby_id] = updated
            return updated

    def submit_ticket(
        self,
        ticket_id: str,
        actor: AuthorityActorContext,
        *,
        criteria: Mapping[str, Any],
        ttl_ms: int = 60_000,
    ) -> MatchmakingTicket:
        ticket_id = _stable_id(ticket_id, field="ticket_id")
        _authorize(actor, "matchmaking.ticket.create", ticket_id)
        ttl_ms = _bounded_int(ttl_ms, field="ttl_ms", minimum=1, maximum=self.max_ticket_ttl_ms)
        criteria = _canonical_mapping(criteria, field="criteria", max_bytes=16 * 1024)
        request = {
            "ticket_id": ticket_id,
            "account_id": actor.account_id,
            "session_id": actor.session_id,
            "criteria": criteria,
            "ttl_ms": ttl_ms,
        }
        request_digest = canonical_sha256(request)
        with self._lock:
            now = _now(self._clock_ms)
            self._expire_locked(now)
            existing = self._tickets.get(ticket_id)
            if existing is not None:
                if self._ticket_request_digests[ticket_id] != request_digest:
                    raise MatchmakingStateError("ticket_idempotency_conflict")
                return existing
            if self._queued_count_locked() >= self.max_queued_tickets:
                raise MatchmakingCapacityError("queue_capacity")
            self._ticket_sequence += 1
            ticket = MatchmakingTicket(
                ticket_id=ticket_id,
                account_id=actor.account_id,
                session_id=actor.session_id,
                criteria=criteria,
                criteria_digest=canonical_sha256(criteria),
                created_at_ms=now,
                expires_at_ms=now + ttl_ms,
                queue_sequence=self._ticket_sequence,
                revision=1,
                status=TicketStatus.QUEUED,
            )
            self._tickets[ticket_id] = ticket
            self._ticket_request_digests[ticket_id] = request_digest
            return ticket

    def cancel_ticket(self, ticket_id: str, actor: AuthorityActorContext) -> MatchmakingTicket:
        ticket_id = _stable_id(ticket_id, field="ticket_id")
        _authorize(actor, "matchmaking.ticket.cancel", ticket_id)
        with self._lock:
            self._expire_locked(_now(self._clock_ms))
            ticket = self._tickets.get(ticket_id)
            if ticket is None:
                raise MatchmakingStateError("ticket_not_found")
            if ticket.account_id != actor.account_id or ticket.session_id != actor.session_id:
                raise MatchmakingAuthorizationError("ticket_owner_mismatch")
            if ticket.status is TicketStatus.CANCELLED:
                return ticket
            if ticket.status is not TicketStatus.QUEUED:
                raise MatchmakingStateError("ticket_terminal")
            updated = replace(ticket, revision=ticket.revision + 1, status=TicketStatus.CANCELLED)
            self._tickets[ticket_id] = updated
            return updated

    def run_matchmaking(self, *, group_size: int = 2, reservation_ttl_ms: int = 30_000) -> tuple[MatchReservation, ...]:
        group_size = _bounded_int(group_size, field="group_size", minimum=2, maximum=64)
        reservation_ttl_ms = _bounded_int(
            reservation_ttl_ms,
            field="reservation_ttl_ms",
            minimum=1,
            maximum=self.max_reservation_ttl_ms,
        )
        with self._lock:
            now = _now(self._clock_ms)
            self._expire_locked(now)
            available_slots = self.max_active_reservations - self._active_reservation_count_locked()
            if available_slots <= 0 and self._queued_count_locked() >= group_size:
                raise MatchmakingCapacityError("reservation_capacity")

            grouped: dict[str, list[MatchmakingTicket]] = {}
            for ticket in self._tickets.values():
                if ticket.status is TicketStatus.QUEUED:
                    grouped.setdefault(ticket.criteria_digest, []).append(ticket)
            for tickets in grouped.values():
                tickets.sort(key=lambda item: (item.queue_sequence, item.ticket_id))

            created: list[MatchReservation] = []
            for criteria_digest in sorted(grouped):
                candidates = grouped[criteria_digest]
                while len(candidates) >= group_size and len(created) < available_slots:
                    selected = candidates[:group_size]
                    del candidates[:group_size]
                    self._match_sequence += 1
                    ticket_ids = tuple(ticket.ticket_id for ticket in selected)
                    match_id = "match-" + canonical_sha256(
                        {"sequence": self._match_sequence, "tickets": list(ticket_ids)}
                    )[:24]
                    reservation_id = "res-" + canonical_sha256(
                        {"match_id": match_id, "tickets": list(ticket_ids)}
                    )[:24]
                    reservation = MatchReservation(
                        reservation_id=reservation_id,
                        match_id=match_id,
                        ticket_ids=ticket_ids,
                        account_ids=tuple(ticket.account_id for ticket in selected),
                        session_ids=tuple(ticket.session_id for ticket in selected),
                        criteria_digest=criteria_digest,
                        created_at_ms=now,
                        expires_at_ms=now + reservation_ttl_ms,
                        revision=1,
                        status=ReservationStatus.ACTIVE,
                    )
                    self._reservations[reservation_id] = reservation
                    for ticket in selected:
                        self._tickets[ticket.ticket_id] = replace(
                            ticket,
                            revision=ticket.revision + 1,
                            status=TicketStatus.MATCHED,
                            match_id=match_id,
                            reservation_id=reservation_id,
                        )
                    created.append(reservation)
            return tuple(created)

    def update_presence(
        self,
        actor: AuthorityActorContext,
        *,
        expected_revision: int,
        state: PresenceState,
        lobby_id: str | None = None,
        match_id: str | None = None,
    ) -> PresenceSnapshot:
        _authorize(actor, "presence.update", actor.account_id)
        expected_revision = _bounded_int(
            expected_revision,
            field="expected_revision",
            minimum=0,
            maximum=2**63 - 1,
        )
        if lobby_id is not None:
            _stable_id(lobby_id, field="lobby_id")
        if match_id is not None:
            _stable_id(match_id, field="match_id")
        with self._lock:
            current = self._presence.get(actor.account_id)
            current_revision = 0 if current is None else current.revision
            if expected_revision != current_revision:
                raise MatchmakingStateError("stale_presence_revision")
            if lobby_id is not None:
                lobby = self._require_lobby_locked(lobby_id)
                member = lobby.member(actor.account_id)
                if member is None or member.session_id != actor.session_id:
                    raise MatchmakingAuthorizationError("lobby_membership_required")
            if match_id is not None and not self._actor_has_active_match_locked(actor, match_id):
                raise MatchmakingAuthorizationError("match_reservation_required")
            snapshot = PresenceSnapshot(
                account_id=actor.account_id,
                session_id=actor.session_id,
                revision=current_revision + 1,
                state=state,
                lobby_id=lobby_id,
                match_id=match_id,
                server_time_ms=_now(self._clock_ms),
            )
            self._presence[actor.account_id] = snapshot
            return snapshot

    def issue_reconnect(self, reservation_id: str, actor: AuthorityActorContext, *, ttl_ms: int = 5_000) -> ReconnectGrant:
        reservation_id = _stable_id(reservation_id, field="reservation_id")
        _authorize(actor, "matchmaking.reconnect.issue", reservation_id)
        ttl_ms = _bounded_int(ttl_ms, field="ttl_ms", minimum=1, maximum=self.max_reconnect_ttl_ms)
        with self._lock:
            now = _now(self._clock_ms)
            self._expire_locked(now)
            reservation = self._require_active_reservation_locked(reservation_id)
            self._require_reservation_actor_locked(reservation, actor)
            remaining = reservation.expires_at_ms - now
            if remaining <= 0:
                raise MatchmakingStateError("reservation_expired")
            effective_ttl = min(ttl_ms, remaining)
            self._grant_sequence += 1
            grant_id = "recon-" + canonical_sha256(
                {
                    "sequence": self._grant_sequence,
                    "reservation_id": reservation_id,
                    "account_id": actor.account_id,
                    "session_id": actor.session_id,
                    "issued_at_ms": now,
                }
            )[:24]
            grant = ReconnectGrant(
                grant_id=grant_id,
                account_id=actor.account_id,
                session_id=actor.session_id,
                reservation_id=reservation_id,
                match_id=reservation.match_id,
                issued_at_ms=now,
                expires_at_ms=now + effective_ttl,
            )
            self._reconnect[grant_id] = grant
            return grant

    def validate_reconnect(self, grant_id: str, actor: AuthorityActorContext) -> ReconnectGrant:
        grant_id = _stable_id(grant_id, field="grant_id")
        with self._lock:
            now = _now(self._clock_ms)
            self._expire_locked(now)
            grant = self._reconnect.get(grant_id)
            if grant is None:
                raise MatchmakingStateError("reconnect_not_found")
            if now >= grant.expires_at_ms:
                raise MatchmakingStateError("reconnect_expired")
            if grant.account_id != actor.account_id or grant.session_id != actor.session_id:
                raise MatchmakingAuthorizationError("reconnect_actor_mismatch")
            _authorize(actor, "matchmaking.reconnect.validate", grant.reservation_id)
            reservation = self._require_active_reservation_locked(grant.reservation_id)
            self._require_reservation_actor_locked(reservation, actor)
            if reservation.match_id != grant.match_id:
                raise MatchmakingStateError("reconnect_match_mismatch")
            return grant

    def state_digest(self) -> str:
        with self._lock:
            self._expire_locked(_now(self._clock_ms))
            return canonical_sha256(
                {
                    "lobbies": [self._lobbies[key].canonical() for key in sorted(self._lobbies)],
                    "tickets": [self._tickets[key].canonical() for key in sorted(self._tickets)],
                    "reservations": [self._reservations[key].canonical() for key in sorted(self._reservations)],
                    "presence": [self._presence[key].canonical() for key in sorted(self._presence)],
                }
            )

    def _require_lobby_locked(self, lobby_id: str) -> LobbySnapshot:
        lobby = self._lobbies.get(lobby_id)
        if lobby is None:
            raise MatchmakingStateError("lobby_not_found")
        return lobby

    def _require_active_reservation_locked(self, reservation_id: str) -> MatchReservation:
        reservation = self._reservations.get(reservation_id)
        if reservation is None:
            raise MatchmakingStateError("reservation_not_found")
        if reservation.status is not ReservationStatus.ACTIVE:
            raise MatchmakingStateError("reservation_expired")
        return reservation

    @staticmethod
    def _require_reservation_actor_locked(reservation: MatchReservation, actor: AuthorityActorContext) -> None:
        pairs = set(zip(reservation.account_ids, reservation.session_ids, strict=True))
        if (actor.account_id, actor.session_id) not in pairs:
            raise MatchmakingAuthorizationError("reservation_actor_mismatch")

    def _actor_has_active_match_locked(self, actor: AuthorityActorContext, match_id: str) -> bool:
        for reservation in self._reservations.values():
            if reservation.status is ReservationStatus.ACTIVE and reservation.match_id == match_id:
                try:
                    self._require_reservation_actor_locked(reservation, actor)
                except MatchmakingAuthorizationError:
                    return False
                return True
        return False

    def _queued_count_locked(self) -> int:
        return sum(ticket.status is TicketStatus.QUEUED for ticket in self._tickets.values())

    def _active_reservation_count_locked(self) -> int:
        return sum(reservation.status is ReservationStatus.ACTIVE for reservation in self._reservations.values())

    def _expire_locked(self, now: int) -> None:
        for ticket_id, ticket in tuple(self._tickets.items()):
            if ticket.status is TicketStatus.QUEUED and now >= ticket.expires_at_ms:
                self._tickets[ticket_id] = replace(
                    ticket,
                    revision=ticket.revision + 1,
                    status=TicketStatus.EXPIRED,
                )
        for reservation_id, reservation in tuple(self._reservations.items()):
            if reservation.status is ReservationStatus.ACTIVE and now >= reservation.expires_at_ms:
                self._reservations[reservation_id] = replace(
                    reservation,
                    revision=reservation.revision + 1,
                    status=ReservationStatus.EXPIRED,
                )
