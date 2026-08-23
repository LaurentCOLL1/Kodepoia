from __future__ import annotations

import base64
import hashlib
import http.client
import json
import os
import socket
import ssl
import struct
from dataclasses import dataclass
from typing import Any
from urllib.parse import SplitResult, urlencode, urlsplit

from .boundary import ComfyEndpoint
from .contracts import ComfyTransportLimits
from .errors import ComfyProtocolError, ComfyResourceError, ComfyUnavailableError

_WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
_MAX_HTTP_REDIRECTS = 3
_MAX_HTTP_HEADER_BYTES = 64 * 1024
_MAX_DISCARDED_ERROR_BYTES = 64 * 1024


@dataclass(frozen=True, slots=True)
class _HTTPPayload:
    status: int
    headers: tuple[tuple[str, str], ...]
    body: bytes


class _FixedHTTPTransport:
    def __init__(self, endpoint: ComfyEndpoint, limits: ComfyTransportLimits) -> None:
        self.endpoint = endpoint
        self.limits = limits

    def get_json_value(self, path: str, *, query: dict[str, str] | None = None) -> Any:
        payload = self._get(path, query=query, max_bytes=self.limits.max_json_bytes)
        try:
            return json.loads(payload.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ComfyProtocolError("ComfyUI returned malformed UTF-8 JSON") from exc

    def get_json(self, path: str, *, query: dict[str, str] | None = None) -> dict[str, Any]:
        decoded = self.get_json_value(path, query=query)
        if not isinstance(decoded, dict):
            raise ComfyProtocolError("ComfyUI JSON response must be an object")
        return decoded

    def get_bytes(self, path: str, *, query: dict[str, str]) -> bytes:
        return self._get(path, query=query, max_bytes=self.limits.max_binary_bytes).body

    def _get(
        self,
        path: str,
        *,
        query: dict[str, str] | None,
        max_bytes: int,
    ) -> _HTTPPayload:
        if not path.startswith("/") or "?" in path or "#" in path:
            raise ComfyProtocolError("Internal ComfyUI route is invalid")
        request_target = path
        if query:
            request_target = f"{path}?{urlencode(query, doseq=False)}"
        return self._request_target(request_target, max_bytes=max_bytes, redirects=0)

    def _connection(self) -> http.client.HTTPConnection:
        if self.endpoint.scheme == "https":
            return http.client.HTTPSConnection(
                self.endpoint.host,
                self.endpoint.port,
                timeout=self.limits.connect_timeout_seconds,
                context=ssl.create_default_context(),
            )
        return http.client.HTTPConnection(
            self.endpoint.host,
            self.endpoint.port,
            timeout=self.limits.connect_timeout_seconds,
        )

    def _request_target(self, target: str, *, max_bytes: int, redirects: int) -> _HTTPPayload:
        connection = self._connection()
        try:
            connection.request("GET", target, headers={"Accept": "application/json"})
            if connection.sock is not None:
                connection.sock.settimeout(self.limits.read_timeout_seconds)
            response = connection.getresponse()
            headers = tuple((str(key), str(value)) for key, value in response.getheaders())

            if 300 <= response.status < 400:
                location = response.getheader("Location")
                response.read(_MAX_DISCARDED_ERROR_BYTES + 1)
                if location is None:
                    raise ComfyProtocolError("ComfyUI redirect omitted Location")
                if redirects >= _MAX_HTTP_REDIRECTS:
                    raise ComfyProtocolError("ComfyUI redirect limit exceeded")
                absolute = self.endpoint.validate_redirect(location)
                parts = urlsplit(absolute)
                next_target = self._target_from_parts(parts)
                return self._request_target(next_target, max_bytes=max_bytes, redirects=redirects + 1)

            if not 200 <= response.status < 300:
                response.read(_MAX_DISCARDED_ERROR_BYTES + 1)
                raise ComfyProtocolError(f"ComfyUI HTTP request failed with status {response.status}")

            declared_length = response.getheader("Content-Length")
            if declared_length is not None:
                try:
                    declared = int(declared_length)
                except ValueError as exc:
                    raise ComfyProtocolError("ComfyUI returned an invalid Content-Length") from exc
                if declared < 0 or declared > max_bytes:
                    raise ComfyResourceError("ComfyUI response exceeds the accepted byte bound")

            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise ComfyResourceError("ComfyUI response exceeds the accepted byte bound")
            return _HTTPPayload(status=response.status, headers=headers, body=body)
        except (TimeoutError, socket.timeout, ConnectionError, OSError) as exc:
            raise ComfyUnavailableError(f"ComfyUI unavailable at {self.endpoint.origin}: {exc}") from exc
        finally:
            connection.close()

    @staticmethod
    def _target_from_parts(parts: SplitResult) -> str:
        path = parts.path or "/"
        return f"{path}?{parts.query}" if parts.query else path


class _WebSocketClosed(ComfyUnavailableError):
    pass


class _WebSocketConnection:
    def __init__(self, sock: socket.socket, limits: ComfyTransportLimits) -> None:
        self._sock = sock
        self._limits = limits
        self._fragment_opcode: int | None = None
        self._fragments = bytearray()

    @classmethod
    def connect(
        cls,
        endpoint: ComfyEndpoint,
        limits: ComfyTransportLimits,
        *,
        client_id: str,
    ) -> "_WebSocketConnection":
        raw_socket: socket.socket | None = None
        try:
            raw_socket = socket.create_connection(
                (endpoint.host, endpoint.port),
                timeout=limits.connect_timeout_seconds,
            )
            sock: socket.socket
            if endpoint.scheme == "https":
                context = ssl.create_default_context()
                sock = context.wrap_socket(raw_socket, server_hostname=endpoint.host)
            else:
                sock = raw_socket
            sock.settimeout(limits.read_timeout_seconds)
            key = base64.b64encode(os.urandom(16)).decode("ascii")
            if ":" in endpoint.host:
                host_header = f"[{endpoint.host}]:{endpoint.port}"
            else:
                host_header = f"{endpoint.host}:{endpoint.port}"
            target = f"/ws?{urlencode({'clientId': client_id})}"
            request = (
                f"GET {target} HTTP/1.1\r\n"
                f"Host: {host_header}\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Key: {key}\r\n"
                "Sec-WebSocket-Version: 13\r\n"
                "\r\n"
            ).encode("ascii")
            sock.sendall(request)
            status, headers = cls._read_handshake(sock)
            if status != 101:
                location = headers.get("location")
                if location is not None:
                    endpoint.validate_redirect(location)
                    raise ComfyProtocolError("ComfyUI WebSocket redirect is not accepted by R9.2")
                raise ComfyProtocolError(f"ComfyUI WebSocket handshake failed with status {status}")
            if headers.get("upgrade", "").lower() != "websocket":
                raise ComfyProtocolError("ComfyUI WebSocket handshake omitted Upgrade: websocket")
            if "upgrade" not in headers.get("connection", "").lower():
                raise ComfyProtocolError("ComfyUI WebSocket handshake omitted Connection: Upgrade")
            expected_accept = base64.b64encode(
                hashlib.sha1(f"{key}{_WS_GUID}".encode("ascii"), usedforsecurity=False).digest()
            ).decode("ascii")
            if headers.get("sec-websocket-accept") != expected_accept:
                raise ComfyProtocolError("ComfyUI WebSocket handshake accept key is invalid")
            return cls(sock, limits)
        except (TimeoutError, socket.timeout, ConnectionError, OSError) as exc:
            if raw_socket is not None:
                raw_socket.close()
            raise ComfyUnavailableError(f"ComfyUI WebSocket unavailable: {exc}") from exc
        except Exception:
            if raw_socket is not None:
                raw_socket.close()
            raise

    @staticmethod
    def _read_handshake(sock: socket.socket) -> tuple[int, dict[str, str]]:
        # Read through the header terminator one byte at a time. This prevents
        # over-reading a first WebSocket frame that the peer may coalesce with
        # the HTTP 101 response in the same TCP packet.
        buffer = bytearray()
        while not buffer.endswith(b"\r\n\r\n"):
            if len(buffer) >= _MAX_HTTP_HEADER_BYTES:
                raise ComfyResourceError("ComfyUI WebSocket handshake headers exceed the accepted bound")
            chunk = sock.recv(1)
            if not chunk:
                raise _WebSocketClosed("ComfyUI closed during WebSocket handshake")
            buffer.extend(chunk)
        header_bytes = bytes(buffer[:-4])
        try:
            lines = header_bytes.decode("iso-8859-1").split("\r\n")
            status_parts = lines[0].split(" ", 2)
            if not status_parts[0].startswith("HTTP/"):
                raise ValueError("missing HTTP status prefix")
            status = int(status_parts[1])
        except (UnicodeDecodeError, ValueError, IndexError) as exc:
            raise ComfyProtocolError("Malformed ComfyUI WebSocket HTTP handshake") from exc
        headers: dict[str, str] = {}
        for line in lines[1:]:
            if ":" not in line:
                raise ComfyProtocolError("Malformed ComfyUI WebSocket response header")
            key, value = line.split(":", 1)
            normalized_key = key.strip().lower()
            if not normalized_key:
                raise ComfyProtocolError("Malformed empty ComfyUI WebSocket response header name")
            headers[normalized_key] = value.strip()
        return status, headers

    def close(self) -> None:
        try:
            self._send_control(0x8, b"")
        except OSError:
            pass
        finally:
            self._sock.close()

    def recv_message(self) -> str | bytes:
        while True:
            fin, opcode, payload = self._recv_frame()
            if opcode == 0x8:
                raise _WebSocketClosed("ComfyUI closed the WebSocket")
            if opcode == 0x9:
                self._send_control(0xA, payload)
                continue
            if opcode == 0xA:
                continue
            if opcode not in {0x0, 0x1, 0x2}:
                raise ComfyProtocolError(f"Unsupported ComfyUI WebSocket opcode {opcode}")

            if opcode in {0x1, 0x2}:
                if self._fragment_opcode is not None:
                    raise ComfyProtocolError("WebSocket message started before prior fragments completed")
                if fin:
                    return self._decode_message(opcode, payload)
                self._fragment_opcode = opcode
                self._fragments = bytearray(payload)
                continue

            if self._fragment_opcode is None:
                raise ComfyProtocolError("Unexpected WebSocket continuation frame")
            self._fragments.extend(payload)
            if len(self._fragments) > self._limits.max_websocket_frame_bytes:
                raise ComfyResourceError("Fragmented WebSocket message exceeds the accepted byte bound")
            if fin:
                complete_opcode = self._fragment_opcode
                complete = bytes(self._fragments)
                self._fragment_opcode = None
                self._fragments.clear()
                return self._decode_message(complete_opcode, complete)

    def _recv_frame(self) -> tuple[bool, int, bytes]:
        try:
            first, second = self._recv_exact(2)
            fin = bool(first & 0x80)
            rsv = first & 0x70
            opcode = first & 0x0F
            masked = bool(second & 0x80)
            length_marker = second & 0x7F
            if rsv:
                raise ComfyProtocolError("Unexpected WebSocket RSV bits")
            if masked:
                raise ComfyProtocolError("ComfyUI server WebSocket frames must not be masked")
            if length_marker == 126:
                payload_length = struct.unpack("!H", self._recv_exact(2))[0]
            elif length_marker == 127:
                payload_length = struct.unpack("!Q", self._recv_exact(8))[0]
                if payload_length & (1 << 63):
                    raise ComfyProtocolError("Invalid WebSocket 64-bit payload length")
            else:
                payload_length = length_marker
            if opcode >= 0x8 and (not fin or payload_length > 125):
                raise ComfyProtocolError("Invalid fragmented/oversized WebSocket control frame")
            if payload_length > self._limits.max_websocket_frame_bytes:
                raise ComfyResourceError("ComfyUI WebSocket frame exceeds the accepted byte bound")
            payload = self._recv_exact(payload_length)
            return fin, opcode, payload
        except socket.timeout as exc:
            raise ComfyUnavailableError("Timed out while reading ComfyUI WebSocket") from exc
        except OSError as exc:
            raise _WebSocketClosed(f"ComfyUI WebSocket read failed: {exc}") from exc

    def _recv_exact(self, length: int) -> bytes:
        if length == 0:
            return b""
        chunks = bytearray()
        while len(chunks) < length:
            chunk = self._sock.recv(min(16384, length - len(chunks)))
            if not chunk:
                raise _WebSocketClosed("ComfyUI WebSocket closed mid-frame")
            chunks.extend(chunk)
        return bytes(chunks)

    @staticmethod
    def _decode_message(opcode: int, payload: bytes) -> str | bytes:
        if opcode == 0x2:
            return payload
        try:
            return payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ComfyProtocolError("ComfyUI WebSocket text frame is not valid UTF-8") from exc

    def _send_control(self, opcode: int, payload: bytes) -> None:
        if len(payload) > 125:
            raise ComfyProtocolError("WebSocket control payload exceeds 125 bytes")
        mask = os.urandom(4)
        masked = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
        header = bytes((0x80 | opcode, 0x80 | len(payload)))
        self._sock.sendall(header + mask + masked)
