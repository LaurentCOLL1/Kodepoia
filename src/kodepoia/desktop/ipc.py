from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import shutil
import struct
import sys
import tempfile
from collections import deque
from dataclasses import dataclass, field
from enum import StrEnum
from multiprocessing.connection import Client, Connection, Listener
from pathlib import Path
from typing import Any, Mapping

from .contracts import canonical_sha256

_STABLE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_METHOD = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,127}$")
_MAX_FRAME_HARD_LIMIT = 8 * 1024 * 1024
_MIN_AUTH_KEY_BYTES = 32
_HEADER = struct.Struct(">I")


def _require_stable(value: str, field_name: str) -> str:
    if not isinstance(value, str) or _STABLE_ID.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a stable identifier")
    return value


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            dict(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("IPC payload is not canonically serializable") from exc


class IpcTransportKind(StrEnum):
    WINDOWS_NAMED_PIPE = "windows_named_pipe"
    UNIX_DOMAIN_SOCKET = "unix_domain_socket"


class IpcMessageKind(StrEnum):
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    ERROR = "error"


class IpcProtocolError(RuntimeError):
    pass


class IpcAuthenticationError(IpcProtocolError):
    pass


class IpcAuthorizationError(IpcProtocolError):
    pass


class IpcReplayError(IpcProtocolError):
    pass


class IpcFrameTooLargeError(IpcProtocolError):
    pass


class IpcStaleVersionError(IpcProtocolError):
    pass


class IpcEndpointClosedError(IpcProtocolError):
    pass


@dataclass(frozen=True, slots=True)
class IpcPolicy:
    protocol_version: int = 1
    max_frame_bytes: int = 1024 * 1024
    replay_window: int = 256
    auth_key_min_bytes: int = _MIN_AUTH_KEY_BYTES
    max_method_count: int = 128

    def __post_init__(self) -> None:
        if self.protocol_version < 1 or self.protocol_version > 65_535:
            raise ValueError("protocol_version must be in [1, 65535]")
        if not (256 <= self.max_frame_bytes <= _MAX_FRAME_HARD_LIMIT):
            raise ValueError("max_frame_bytes is outside the bounded IPC range")
        if not (1 <= self.replay_window <= 16_384):
            raise ValueError("replay_window is outside the bounded IPC range")
        if not (_MIN_AUTH_KEY_BYTES <= self.auth_key_min_bytes <= 4096):
            raise ValueError("auth_key_min_bytes is outside the bounded IPC range")
        if not (1 <= self.max_method_count <= 4096):
            raise ValueError("max_method_count is outside the bounded IPC range")

    def canonical(self) -> dict[str, int]:
        return {
            "auth_key_min_bytes": self.auth_key_min_bytes,
            "max_frame_bytes": self.max_frame_bytes,
            "max_method_count": self.max_method_count,
            "protocol_version": self.protocol_version,
            "replay_window": self.replay_window,
        }

    @property
    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class IpcEndpointIdentity:
    endpoint_id: str
    session_id: str
    transport: IpcTransportKind
    local_only: bool = True

    def __post_init__(self) -> None:
        _require_stable(self.endpoint_id, "endpoint_id")
        _require_stable(self.session_id, "session_id")
        if not self.local_only:
            raise ValueError("R12 IPC endpoints must be local-only")

    def canonical(self) -> dict[str, object]:
        return {
            "endpoint_id": self.endpoint_id,
            "local_only": self.local_only,
            "session_id": self.session_id,
            "transport": self.transport.value,
        }

    @property
    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class IpcPeerIdentity:
    peer_id: str
    session_id: str
    role: str

    def __post_init__(self) -> None:
        _require_stable(self.peer_id, "peer_id")
        _require_stable(self.session_id, "session_id")
        _require_stable(self.role, "role")

    def canonical(self) -> dict[str, str]:
        return {
            "peer_id": self.peer_id,
            "role": self.role,
            "session_id": self.session_id,
        }


@dataclass(frozen=True, slots=True)
class IpcEnvelope:
    protocol_version: int
    message_id: str
    kind: IpcMessageKind
    method: str
    peer: IpcPeerIdentity
    payload: Mapping[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        if self.protocol_version < 1:
            raise ValueError("protocol_version must be positive")
        _require_stable(self.message_id, "message_id")
        if _METHOD.fullmatch(self.method) is None:
            raise ValueError("method must be a bounded method identifier")
        if self.correlation_id is not None:
            _require_stable(self.correlation_id, "correlation_id")
        _canonical_bytes(dict(self.payload))

    def canonical(self) -> dict[str, Any]:
        return {
            "correlation_id": self.correlation_id,
            "kind": self.kind.value,
            "message_id": self.message_id,
            "method": self.method,
            "payload": dict(self.payload),
            "peer": self.peer.canonical(),
            "protocol_version": self.protocol_version,
        }

    @classmethod
    def from_canonical(cls, raw: Mapping[str, Any]) -> IpcEnvelope:
        try:
            peer_raw = raw["peer"]
            if not isinstance(peer_raw, Mapping):
                raise TypeError("peer")
            payload = raw.get("payload", {})
            if not isinstance(payload, Mapping):
                raise TypeError("payload")
            return cls(
                protocol_version=int(raw["protocol_version"]),
                message_id=str(raw["message_id"]),
                kind=IpcMessageKind(str(raw["kind"])),
                method=str(raw["method"]),
                peer=IpcPeerIdentity(
                    peer_id=str(peer_raw["peer_id"]),
                    session_id=str(peer_raw["session_id"]),
                    role=str(peer_raw["role"]),
                ),
                payload=dict(payload),
                correlation_id=(
                    None if raw.get("correlation_id") is None else str(raw["correlation_id"])
                ),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise IpcProtocolError("malformed IPC envelope") from exc


@dataclass(frozen=True, slots=True)
class IpcAuthorizationPolicy:
    session_id: str
    allowed_roles: tuple[str, ...]
    allowed_methods: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_stable(self.session_id, "session_id")
        roles = tuple(sorted(set(self.allowed_roles)))
        methods = tuple(sorted(set(self.allowed_methods)))
        if not roles or not methods:
            raise ValueError("authorization policy requires roles and methods")
        for role in roles:
            _require_stable(role, "role")
        for method in methods:
            if _METHOD.fullmatch(method) is None:
                raise ValueError("invalid allowed method")
        object.__setattr__(self, "allowed_roles", roles)
        object.__setattr__(self, "allowed_methods", methods)

    def authorize(self, envelope: IpcEnvelope) -> None:
        if envelope.peer.session_id != self.session_id:
            raise IpcAuthorizationError("peer session is not authorized")
        if envelope.peer.role not in self.allowed_roles:
            raise IpcAuthorizationError("peer role is not authorized")
        if envelope.method not in self.allowed_methods:
            raise IpcAuthorizationError("IPC method is not authorized")


class ReplayWindow:
    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("replay capacity must be positive")
        self._capacity = capacity
        self._order: deque[str] = deque()
        self._known: set[str] = set()

    def accept(self, message_id: str) -> None:
        _require_stable(message_id, "message_id")
        if message_id in self._known:
            raise IpcReplayError("replayed IPC message")
        self._known.add(message_id)
        self._order.append(message_id)
        while len(self._order) > self._capacity:
            evicted = self._order.popleft()
            self._known.discard(evicted)

    @property
    def size(self) -> int:
        return len(self._order)


def _validate_auth_key(auth_key: bytes, policy: IpcPolicy) -> None:
    if not isinstance(auth_key, bytes) or len(auth_key) < policy.auth_key_min_bytes:
        raise ValueError("IPC auth key does not satisfy the minimum length")


def encode_frame(envelope: IpcEnvelope, auth_key: bytes, policy: IpcPolicy) -> bytes:
    _validate_auth_key(auth_key, policy)
    if envelope.protocol_version != policy.protocol_version:
        raise IpcStaleVersionError("IPC protocol version mismatch")
    body = _canonical_bytes(envelope.canonical())
    mac = hmac.new(auth_key, body, hashlib.sha256).hexdigest()
    outer = _canonical_bytes({"body": envelope.canonical(), "mac": mac})
    if len(outer) > policy.max_frame_bytes:
        raise IpcFrameTooLargeError("IPC frame exceeds configured maximum")
    return _HEADER.pack(len(outer)) + outer


def decode_frame(
    frame: bytes,
    auth_key: bytes,
    policy: IpcPolicy,
    *,
    replay_window: ReplayWindow | None = None,
    authorization: IpcAuthorizationPolicy | None = None,
) -> IpcEnvelope:
    _validate_auth_key(auth_key, policy)
    if not isinstance(frame, bytes) or len(frame) < _HEADER.size:
        raise IpcProtocolError("truncated IPC frame")
    declared = _HEADER.unpack(frame[: _HEADER.size])[0]
    body = frame[_HEADER.size :]
    if declared > policy.max_frame_bytes:
        raise IpcFrameTooLargeError("declared IPC frame exceeds configured maximum")
    if declared != len(body):
        raise IpcProtocolError("truncated or overlong IPC frame")
    try:
        outer = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IpcProtocolError("malformed IPC frame JSON") from exc
    if not isinstance(outer, dict) or set(outer) != {"body", "mac"}:
        raise IpcProtocolError("malformed IPC signed envelope")
    raw_body = outer["body"]
    if not isinstance(raw_body, dict) or not isinstance(outer["mac"], str):
        raise IpcProtocolError("malformed IPC signed envelope")
    canonical = _canonical_bytes(raw_body)
    expected = hmac.new(auth_key, canonical, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, outer["mac"]):
        raise IpcAuthenticationError("IPC message authentication failed")
    envelope = IpcEnvelope.from_canonical(raw_body)
    if envelope.protocol_version != policy.protocol_version:
        raise IpcStaleVersionError("IPC protocol version mismatch")
    if authorization is not None:
        authorization.authorize(envelope)
    if replay_window is not None:
        replay_window.accept(envelope.message_id)
    return envelope


@dataclass(slots=True)
class LocalIpcEndpoint:
    identity: IpcEndpointIdentity
    address: str
    family: str
    _runtime_dir: Path | None = None
    _listener: Listener | None = None
    _closed: bool = False

    @classmethod
    def allocate(cls, endpoint_id: str, session_id: str) -> LocalIpcEndpoint:
        _require_stable(endpoint_id, "endpoint_id")
        _require_stable(session_id, "session_id")
        suffix = secrets.token_hex(8)
        if sys.platform == "win32":
            transport = IpcTransportKind.WINDOWS_NAMED_PIPE
            family = "AF_PIPE"
            safe = f"kodepoia-{session_id}-{endpoint_id}-{suffix}"[:220]
            address = rf"\\.\pipe\{safe}"
            runtime_dir = None
        else:
            transport = IpcTransportKind.UNIX_DOMAIN_SOCKET
            family = "AF_UNIX"
            runtime_dir = Path(tempfile.mkdtemp(prefix="kodepoia-ipc-"))
            address = str(runtime_dir / f"{endpoint_id}-{suffix}.sock")
        identity = IpcEndpointIdentity(endpoint_id, session_id, transport)
        return cls(identity, address, family, runtime_dir)

    def open_listener(self, auth_key: bytes, policy: IpcPolicy) -> Listener:
        if self._closed:
            raise IpcEndpointClosedError("IPC endpoint is closed")
        _validate_auth_key(auth_key, policy)
        if self._listener is not None:
            raise IpcProtocolError("IPC listener already open")
        self._listener = Listener(self.address, family=self.family, authkey=auth_key)
        return self._listener

    def connect(self, auth_key: bytes, policy: IpcPolicy) -> Connection:
        if self._closed:
            raise IpcEndpointClosedError("IPC endpoint is closed")
        _validate_auth_key(auth_key, policy)
        return Client(self.address, family=self.family, authkey=auth_key)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._listener is not None:
            self._listener.close()
            self._listener = None
        if self._runtime_dir is not None:
            shutil.rmtree(self._runtime_dir, ignore_errors=True)

    def __enter__(self) -> LocalIpcEndpoint:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    @property
    def closed(self) -> bool:
        return self._closed


def send_envelope(
    connection: Connection,
    envelope: IpcEnvelope,
    auth_key: bytes,
    policy: IpcPolicy,
) -> None:
    connection.send_bytes(encode_frame(envelope, auth_key, policy))


def receive_envelope(
    connection: Connection,
    auth_key: bytes,
    policy: IpcPolicy,
    *,
    replay_window: ReplayWindow | None = None,
    authorization: IpcAuthorizationPolicy | None = None,
) -> IpcEnvelope:
    try:
        frame = connection.recv_bytes(maxlength=policy.max_frame_bytes + _HEADER.size)
    except OSError as exc:
        raise IpcFrameTooLargeError("IPC transport rejected an oversized frame") from exc
    return decode_frame(
        frame,
        auth_key,
        policy,
        replay_window=replay_window,
        authorization=authorization,
    )


def canonical_local_transport() -> IpcTransportKind:
    return (
        IpcTransportKind.WINDOWS_NAMED_PIPE
        if sys.platform == "win32"
        else IpcTransportKind.UNIX_DOMAIN_SOCKET
    )


def generate_auth_key(length: int = 32) -> bytes:
    if not (_MIN_AUTH_KEY_BYTES <= length <= 4096):
        raise ValueError("auth key length is outside the bounded IPC range")
    return os.urandom(length)
