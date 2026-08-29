from __future__ import annotations

import http.client
import ipaddress
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote, unquote, urlsplit

from .content_delivery import (
    ContentDeliveryCapacityError,
    ContentDeliveryPolicyError,
    ContentDeliveryStateError,
    ContentFetchResponse,
    LocalContentProvider,
)

_STABLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,191}$")
_RANGE_RE = re.compile(r"^bytes=(\d+)-(\d*)$")
_CONTENT_RANGE_RE = re.compile(r"^bytes (\d+)-(\d+)/(\d+)$")


def _object_id(value: str) -> str:
    if not isinstance(value, str) or _STABLE_ID_RE.fullmatch(value) is None:
        raise ContentDeliveryPolicyError("invalid_object_id")
    return value


def _range_values(start: int, end_exclusive: int | None) -> tuple[int, int | None]:
    if isinstance(start, bool) or not isinstance(start, int) or start < 0:
        raise ContentDeliveryPolicyError("invalid_range_start")
    if end_exclusive is not None:
        if isinstance(end_exclusive, bool) or not isinstance(end_exclusive, int) or end_exclusive <= start:
            raise ContentDeliveryPolicyError("invalid_range_end")
    return start, end_exclusive


class LoopbackHttpContentFixture:
    """Explicit loopback-only HTTP fixture for deterministic R14.12 acceptance."""

    def __init__(self, provider: LocalContentProvider) -> None:
        if not isinstance(provider, LocalContentProvider):
            raise ContentDeliveryPolicyError("invalid_loopback_provider")
        self.provider = provider
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def base_url(self) -> str:
        if self._server is None:
            raise ContentDeliveryStateError("loopback_http_fixture_not_started")
        host, port = self._server.server_address[:2]
        return f"http://{host}:{port}"

    def start(self) -> LoopbackHttpContentFixture:
        if self._server is not None:
            return self

        provider = self.provider

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, _format: str, *args: object) -> None:
                return

            def _finish(
                self,
                *,
                status: int,
                response: ContentFetchResponse,
                payload: bytes,
                content_range: str | None = None,
            ) -> None:
                self.send_response(status)
                self.send_header("ETag", response.etag)
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(len(payload)))
                if content_range is not None:
                    self.send_header("Content-Range", content_range)
                self.send_header("Connection", "close")
                self.end_headers()
                if payload:
                    self.wfile.write(payload)

            def _range_not_satisfiable(self, total_size: int) -> None:
                self.send_response(416)
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Content-Range", f"bytes */{total_size}")
                self.send_header("Content-Length", "0")
                self.send_header("Connection", "close")
                self.end_headers()

            def do_GET(self) -> None:  # noqa: N802
                parsed = urlsplit(self.path)
                prefix = "/objects/"
                if parsed.query or parsed.fragment or not parsed.path.startswith(prefix):
                    self.send_error(404)
                    return
                encoded_object_id = parsed.path[len(prefix) :]
                if not encoded_object_id or "/" in encoded_object_id:
                    self.send_error(404)
                    return
                try:
                    object_id = _object_id(unquote(encoded_object_id))
                    full = provider.fetch(object_id)
                except (ContentDeliveryPolicyError, ContentDeliveryStateError):
                    self.send_error(404)
                    return
                if full is None:
                    self.send_error(500)
                    return

                if self.headers.get("If-None-Match") == full.etag:
                    self.send_response(304)
                    self.send_header("ETag", full.etag)
                    self.send_header("Accept-Ranges", "bytes")
                    self.send_header("Content-Length", "0")
                    self.send_header("Connection", "close")
                    self.end_headers()
                    return

                range_header = self.headers.get("Range")
                if range_header is None:
                    self._finish(status=200, response=full, payload=full.payload)
                    return

                match = _RANGE_RE.fullmatch(range_header.strip())
                if match is None:
                    self._range_not_satisfiable(full.total_size)
                    return
                start = int(match.group(1))
                if start >= full.total_size:
                    self._range_not_satisfiable(full.total_size)
                    return
                end_inclusive = full.total_size - 1 if match.group(2) == "" else int(match.group(2))
                if end_inclusive < start:
                    self._range_not_satisfiable(full.total_size)
                    return
                end_exclusive = min(end_inclusive + 1, full.total_size)

                if_range = self.headers.get("If-Range")
                if if_range is not None and if_range != full.etag:
                    self._finish(status=200, response=full, payload=full.payload)
                    return

                try:
                    partial = provider.fetch(
                        object_id,
                        start=start,
                        end_exclusive=end_exclusive,
                        if_range=if_range,
                    )
                except (ContentDeliveryPolicyError, ContentDeliveryStateError):
                    self._range_not_satisfiable(full.total_size)
                    return
                if partial is None:
                    self.send_error(500)
                    return
                self._finish(
                    status=206,
                    response=partial,
                    payload=partial.payload,
                    content_range=f"bytes {partial.start}-{partial.end_exclusive - 1}/{partial.total_size}",
                )

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.daemon_threads = True
        thread = threading.Thread(
            target=server.serve_forever,
            name="kodepoia-r14-12-loopback-http",
            daemon=True,
        )
        self._server = server
        self._thread = thread
        thread.start()
        return self

    def stop(self) -> None:
        server = self._server
        thread = self._thread
        if server is None:
            return
        self._server = None
        self._thread = None
        server.shutdown()
        server.server_close()
        if thread is not None:
            thread.join(timeout=5.0)

    def __enter__(self) -> LoopbackHttpContentFixture:
        return self.start()

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.stop()


class LoopbackHttpContentProvider:
    """HTTP content provider restricted to a literal loopback IP endpoint."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: float = 2.0,
        max_response_bytes: int = 64 * 1024 * 1024,
    ) -> None:
        if not isinstance(base_url, str):
            raise ContentDeliveryPolicyError("invalid_loopback_endpoint")
        parsed = urlsplit(base_url)
        if (
            parsed.scheme != "http"
            or parsed.hostname is None
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or parsed.path not in ("", "/")
        ):
            raise ContentDeliveryPolicyError("invalid_loopback_endpoint")
        try:
            address = ipaddress.ip_address(parsed.hostname)
        except ValueError as exc:
            raise ContentDeliveryPolicyError("loopback_ip_literal_required") from exc
        if not address.is_loopback:
            raise ContentDeliveryPolicyError("loopback_endpoint_required")
        try:
            port = parsed.port
        except ValueError as exc:
            raise ContentDeliveryPolicyError("invalid_loopback_endpoint") from exc
        if port is None or not 1 <= port <= 65535:
            raise ContentDeliveryPolicyError("loopback_port_required")
        if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or not 0 < timeout_seconds <= 30:
            raise ContentDeliveryPolicyError("invalid_http_timeout")
        if (
            isinstance(max_response_bytes, bool)
            or not isinstance(max_response_bytes, int)
            or not 1 <= max_response_bytes <= 2**40
        ):
            raise ContentDeliveryPolicyError("invalid_max_response_bytes")
        self.host = parsed.hostname
        self.port = port
        self.timeout_seconds = float(timeout_seconds)
        self.max_response_bytes = max_response_bytes

    def fetch(
        self,
        object_id: str,
        *,
        if_none_match: str | None = None,
        start: int = 0,
        end_exclusive: int | None = None,
        if_range: str | None = None,
    ) -> ContentFetchResponse | None:
        object_id = _object_id(object_id)
        start, end_exclusive = _range_values(start, end_exclusive)
        range_requested = start != 0 or end_exclusive is not None
        if if_range is not None and not range_requested:
            raise ContentDeliveryPolicyError("if_range_requires_range")

        headers = {"Connection": "close"}
        if if_none_match is not None:
            headers["If-None-Match"] = if_none_match
        if range_requested:
            range_end = "" if end_exclusive is None else str(end_exclusive - 1)
            headers["Range"] = f"bytes={start}-{range_end}"
            if if_range is not None:
                headers["If-Range"] = if_range

        connection = http.client.HTTPConnection(self.host, self.port, timeout=self.timeout_seconds)
        try:
            connection.request("GET", f"/objects/{quote(object_id, safe='')}", headers=headers)
            response = connection.getresponse()
            if response.status == 304:
                response.read()
                return None
            if response.status == 404:
                response.read()
                raise ContentDeliveryStateError("object_not_found")
            if response.status == 416:
                response.read()
                raise ContentDeliveryPolicyError("range_not_satisfiable")
            if response.status not in (200, 206):
                response.read()
                raise ContentDeliveryStateError("unexpected_http_status")

            content_length_header = response.getheader("Content-Length")
            if content_length_header is None or not content_length_header.isdigit():
                raise ContentDeliveryStateError("http_content_length_required")
            content_length = int(content_length_header)
            if content_length > self.max_response_bytes:
                raise ContentDeliveryCapacityError("http_response_capacity")
            payload = response.read(self.max_response_bytes + 1)
            if len(payload) > self.max_response_bytes:
                raise ContentDeliveryCapacityError("http_response_capacity")
            if len(payload) != content_length:
                raise ContentDeliveryStateError("http_content_length_mismatch")
            etag = response.getheader("ETag")
            if etag is None:
                raise ContentDeliveryStateError("http_etag_required")

            if response.status == 200:
                return ContentFetchResponse(
                    object_id=object_id,
                    etag=etag,
                    total_size=content_length,
                    start=0,
                    end_exclusive=content_length,
                    payload=payload,
                )

            content_range = response.getheader("Content-Range")
            match = _CONTENT_RANGE_RE.fullmatch(content_range or "")
            if match is None:
                raise ContentDeliveryStateError("invalid_http_content_range")
            range_start = int(match.group(1))
            range_end_inclusive = int(match.group(2))
            total_size = int(match.group(3))
            if (
                range_end_inclusive < range_start
                or range_end_inclusive >= total_size
                or range_end_inclusive + 1 - range_start != content_length
            ):
                raise ContentDeliveryStateError("invalid_http_content_range")
            return ContentFetchResponse(
                object_id=object_id,
                etag=etag,
                total_size=total_size,
                start=range_start,
                end_exclusive=range_end_inclusive + 1,
                payload=payload,
            )
        except (OSError, TimeoutError, http.client.HTTPException) as exc:
            raise ContentDeliveryStateError("loopback_http_unavailable") from exc
        finally:
            connection.close()
