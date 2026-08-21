from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, BinaryIO


class ProtocolError(RuntimeError):
    """Raised for malformed or oversized framed protocol messages."""


@dataclass(frozen=True, slots=True)
class FramingLimits:
    max_header_bytes: int = 8192
    max_content_bytes: int = 8 * 1024 * 1024


class ContentLengthJsonStream:
    """LSP/DAP compatible Content-Length framed JSON stream.

    LSP and DAP both use an ASCII header followed by a UTF-8 JSON body. This
    codec is deliberately transport-only; protocol-specific request semantics
    live in their respective clients.
    """

    def __init__(
        self,
        reader: BinaryIO,
        writer: BinaryIO,
        *,
        limits: FramingLimits | None = None,
    ) -> None:
        self.reader = reader
        self.writer = writer
        self.limits = limits or FramingLimits()

    def write(self, message: dict[str, Any]) -> None:
        payload = json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if len(payload) > self.limits.max_content_bytes:
            raise ProtocolError("Protocol message exceeds content limit")
        header = f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii")
        self.writer.write(header)
        self.writer.write(payload)
        self.writer.flush()

    def read(self) -> dict[str, Any]:
        headers = self._read_headers()
        raw_length = headers.get("content-length")
        if raw_length is None:
            raise ProtocolError("Missing Content-Length header")
        try:
            content_length = int(raw_length)
        except ValueError as exc:
            raise ProtocolError("Invalid Content-Length header") from exc
        if content_length < 0 or content_length > self.limits.max_content_bytes:
            raise ProtocolError("Protocol content length is outside allowed bounds")

        payload = self._read_exact(content_length)
        try:
            decoded = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProtocolError("Invalid UTF-8 JSON protocol body") from exc
        if not isinstance(decoded, dict):
            raise ProtocolError("Protocol JSON body must be an object")
        return decoded

    def _read_headers(self) -> dict[str, str]:
        buffer = bytearray()
        while not buffer.endswith(b"\r\n\r\n"):
            chunk = self.reader.read(1)
            if not chunk:
                raise EOFError("Protocol stream closed while reading headers")
            buffer.extend(chunk)
            if len(buffer) > self.limits.max_header_bytes:
                raise ProtocolError("Protocol headers exceed limit")

        header_text = bytes(buffer[:-4]).decode("ascii", errors="strict")
        headers: dict[str, str] = {}
        for line in header_text.split("\r\n"):
            if not line:
                continue
            if ":" not in line:
                raise ProtocolError("Malformed protocol header")
            name, value = line.split(":", 1)
            headers[name.strip().lower()] = value.strip()
        return headers

    def _read_exact(self, size: int) -> bytes:
        remaining = size
        chunks: list[bytes] = []
        while remaining:
            chunk = self.reader.read(remaining)
            if not chunk:
                raise EOFError("Protocol stream closed while reading body")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)
