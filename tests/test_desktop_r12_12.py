from __future__ import annotations

import json
import struct
import threading
from pathlib import Path

import pytest

from kodepoia.desktop.ipc import (
    IpcAuthenticationError,
    IpcAuthorizationError,
    IpcAuthorizationPolicy,
    IpcEnvelope,
    IpcFrameTooLargeError,
    IpcMessageKind,
    IpcPeerIdentity,
    IpcPolicy,
    IpcProtocolError,
    IpcReplayError,
    IpcStaleVersionError,
    IpcTransportKind,
    LocalIpcEndpoint,
    ReplayWindow,
    canonical_local_transport,
    decode_frame,
    encode_frame,
    receive_envelope,
    send_envelope,
)


def _peer(*, session: str = "session-a", role: str = "worker") -> IpcPeerIdentity:
    return IpcPeerIdentity("peer-a", session, role)


def _message(
    message_id: str = "msg-1",
    *,
    version: int = 1,
    method: str = "project.status",
    peer: IpcPeerIdentity | None = None,
    payload: dict[str, object] | None = None,
) -> IpcEnvelope:
    return IpcEnvelope(
        version,
        message_id,
        IpcMessageKind.REQUEST,
        method,
        peer or _peer(),
        payload or {"value": 7},
    )


def test_policy_and_endpoint_identity_are_bounded_and_deterministic() -> None:
    policy = IpcPolicy(protocol_version=3, max_frame_bytes=4096, replay_window=12)
    assert policy.digest == IpcPolicy(
        protocol_version=3, max_frame_bytes=4096, replay_window=12
    ).digest
    with pytest.raises(ValueError, match="local-only"):
        from kodepoia.desktop.ipc import IpcEndpointIdentity

        IpcEndpointIdentity(
            "desktop", "session-a", IpcTransportKind.UNIX_DOMAIN_SOCKET, local_only=False
        )


def test_signed_frame_roundtrip_and_tamper_fail_closed() -> None:
    key = b"k" * 32
    policy = IpcPolicy(max_frame_bytes=4096)
    frame = encode_frame(_message(), key, policy)
    decoded = decode_frame(frame, key, policy)
    assert decoded.canonical() == _message().canonical()

    length = struct.unpack(">I", frame[:4])[0]
    outer = json.loads(frame[4:].decode("utf-8"))
    outer["body"]["payload"]["value"] = 8
    tampered = json.dumps(
        outer, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    assert len(tampered) == length
    with pytest.raises(IpcAuthenticationError):
        decode_frame(struct.pack(">I", len(tampered)) + tampered, key, policy)


def test_version_replay_session_role_and_method_are_enforced() -> None:
    key = b"a" * 32
    policy = IpcPolicy(protocol_version=1, max_frame_bytes=4096, replay_window=2)
    replay = ReplayWindow(2)
    authz = IpcAuthorizationPolicy("session-a", ("worker",), ("project.status",))
    frame = encode_frame(_message("msg-1"), key, policy)
    assert decode_frame(frame, key, policy, replay_window=replay, authorization=authz).message_id == "msg-1"
    with pytest.raises(IpcReplayError):
        decode_frame(frame, key, policy, replay_window=replay, authorization=authz)

    wrong_session = encode_frame(_message("msg-2", peer=_peer(session="session-b")), key, policy)
    with pytest.raises(IpcAuthorizationError, match="session"):
        decode_frame(wrong_session, key, policy, authorization=authz)

    wrong_role = encode_frame(_message("msg-3", peer=_peer(role="admin")), key, policy)
    with pytest.raises(IpcAuthorizationError, match="role"):
        decode_frame(wrong_role, key, policy, authorization=authz)

    wrong_method = encode_frame(_message("msg-4", method="project.delete"), key, policy)
    with pytest.raises(IpcAuthorizationError, match="method"):
        decode_frame(wrong_method, key, policy, authorization=authz)

    stale_policy = IpcPolicy(protocol_version=2, max_frame_bytes=4096)
    with pytest.raises(IpcStaleVersionError):
        encode_frame(_message("msg-5"), key, stale_policy)


def test_truncated_malformed_overlong_and_oversized_frames_fail_closed() -> None:
    key = b"b" * 32
    policy = IpcPolicy(max_frame_bytes=512)
    with pytest.raises(IpcProtocolError, match="truncated"):
        decode_frame(b"x", key, policy)
    with pytest.raises(IpcFrameTooLargeError):
        decode_frame(struct.pack(">I", 513) + b"{}", key, policy)
    with pytest.raises(IpcProtocolError, match="truncated or overlong"):
        decode_frame(struct.pack(">I", 10) + b"{}", key, policy)
    malformed = b"not-json"
    with pytest.raises(IpcProtocolError, match="JSON"):
        decode_frame(struct.pack(">I", len(malformed)) + malformed, key, policy)

    huge = _message("huge", payload={"blob": "x" * 1000})
    with pytest.raises(IpcFrameTooLargeError):
        encode_frame(huge, key, policy)


def test_auth_key_is_required_and_never_serialized() -> None:
    policy = IpcPolicy(max_frame_bytes=4096)
    with pytest.raises(ValueError, match="minimum length"):
        encode_frame(_message(), b"short", policy)
    key = b"secret-value-that-must-not-appear!!"
    frame = encode_frame(_message(), key, policy)
    assert key not in frame


def test_real_local_transport_roundtrip_and_cleanup(tmp_path: Path) -> None:
    del tmp_path  # endpoint allocator owns its private runtime location
    policy = IpcPolicy(max_frame_bytes=4096)
    key = b"c" * 32
    authz = IpcAuthorizationPolicy("session-a", ("worker",), ("project.status",))
    endpoint = LocalIpcEndpoint.allocate("r12-12", "session-a")
    assert endpoint.identity.transport is canonical_local_transport()
    assert endpoint.identity.local_only
    if endpoint.identity.transport is IpcTransportKind.WINDOWS_NAMED_PIPE:
        assert endpoint.family == "AF_PIPE"
        assert endpoint.address.startswith("\\\\.\\pipe\\")
    else:
        assert endpoint.family == "AF_UNIX"
        assert endpoint._runtime_dir is not None
        runtime_dir = endpoint._runtime_dir

    listener = endpoint.open_listener(key, policy)
    server_error: list[BaseException] = []

    def server() -> None:
        try:
            with listener.accept() as connection:
                request = receive_envelope(
                    connection,
                    key,
                    policy,
                    replay_window=ReplayWindow(policy.replay_window),
                    authorization=authz,
                )
                response = IpcEnvelope(
                    1,
                    "response-1",
                    IpcMessageKind.RESPONSE,
                    request.method,
                    _peer(),
                    {"ok": True},
                    correlation_id=request.message_id,
                )
                send_envelope(connection, response, key, policy)
        except BaseException as exc:  # captured for deterministic join assertion
            server_error.append(exc)

    thread = threading.Thread(target=server, name="r12-12-ipc-server", daemon=False)
    thread.start()
    with endpoint.connect(key, policy) as client:
        send_envelope(client, _message("request-1"), key, policy)
        response = receive_envelope(client, key, policy)
    thread.join(timeout=10)
    assert not thread.is_alive()
    assert not server_error
    assert response.correlation_id == "request-1"
    assert response.payload == {"ok": True}

    endpoint.close()
    assert endpoint.closed
    if endpoint.identity.transport is IpcTransportKind.UNIX_DOMAIN_SOCKET:
        assert not runtime_dir.exists()


def test_transport_has_no_network_fallback() -> None:
    endpoint = LocalIpcEndpoint.allocate("local-only", "session-a")
    try:
        assert endpoint.family in {"AF_PIPE", "AF_UNIX"}
        assert endpoint.family != "AF_INET"
        assert endpoint.identity.local_only is True
    finally:
        endpoint.close()
