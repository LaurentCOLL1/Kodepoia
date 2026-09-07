from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from urllib.parse import quote, urlsplit, urlunsplit

import urllib3
from urllib3.exceptions import ConnectTimeoutError, HTTPError, NewConnectionError, ReadTimeoutError, SSLError
from urllib3.util import Timeout

from kodepoia.update.trust import UpdateTargetSpec, UpdateTransportError, UpdateTransportOffline

DEFAULT_METADATA_BASE_URL = (
    "https://raw.githubusercontent.com/LaurentCOLL1/Kodepoia/main/update-repository/metadata/"
)
DEFAULT_RELEASE_ASSET_BASE_URL = (
    "https://github.com/LaurentCOLL1/Kodepoia/releases/download/"
)
DEFAULT_METADATA_BYTES = 1024 * 1024
DEFAULT_TARGET_BYTES = 1024 * 1024 * 1024
TOP_LEVEL_METADATA = frozenset({"root.json", "targets.json", "snapshot.json", "timestamp.json"})
DEFAULT_TARGET_REDIRECT_HOSTS = frozenset(
    {
        "github.com",
        "release-assets.githubusercontent.com",
        "objects.githubusercontent.com",
    }
)


@dataclass(frozen=True, slots=True)
class NetworkTransportPolicy:
    metadata_base_url: str = DEFAULT_METADATA_BASE_URL
    release_asset_base_url: str = DEFAULT_RELEASE_ASSET_BASE_URL
    connect_timeout_seconds: float = 5.0
    read_timeout_seconds: float = 20.0
    max_metadata_bytes: int = DEFAULT_METADATA_BYTES
    max_target_bytes: int = DEFAULT_TARGET_BYTES
    max_redirects: int = 3
    target_redirect_hosts: frozenset[str] = DEFAULT_TARGET_REDIRECT_HOSTS

    def __post_init__(self) -> None:
        metadata = _normalized_https_base(self.metadata_base_url, "metadata")
        release = _normalized_https_base(self.release_asset_base_url, "release asset")
        if self.connect_timeout_seconds <= 0 or self.read_timeout_seconds <= 0:
            raise ValueError("update transport timeouts must be positive")
        if self.max_metadata_bytes <= 0 or self.max_target_bytes <= 0:
            raise ValueError("update transport size ceilings must be positive")
        if self.max_redirects < 0:
            raise ValueError("update transport redirect limit cannot be negative")
        hosts = frozenset(host.strip().lower() for host in self.target_redirect_hosts if host.strip())
        if not hosts:
            raise ValueError("at least one target redirect host must be authorized")
        object.__setattr__(self, "metadata_base_url", metadata)
        object.__setattr__(self, "release_asset_base_url", release)
        object.__setattr__(self, "target_redirect_hosts", hosts)


def _normalized_https_base(value: str, label: str) -> str:
    parsed = urlsplit(value.strip())
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise ValueError(f"update {label} base URL must be absolute HTTPS")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError(f"update {label} base URL cannot contain credentials, query or fragment")
    path = parsed.path if parsed.path.endswith("/") else f"{parsed.path}/"
    return urlunsplit(("https", parsed.netloc, path, "", ""))


def _origin(url: str) -> tuple[str, str, int]:
    parsed = urlsplit(url)
    return parsed.scheme.lower(), (parsed.hostname or "").lower(), parsed.port or 443


def _safe_metadata_name(name: str) -> str:
    value = name.strip()
    if value not in TOP_LEVEL_METADATA:
        raise UpdateTransportError(f"metadata name is not authorized: {value!r}")
    return value


def _target_from_path(path: str) -> UpdateTargetSpec:
    if "\\" in path:
        raise UpdateTransportError("target path cannot contain backslashes")
    parts = path.split("/")
    if len(parts) != 6 or parts[0] != "channels":
        raise UpdateTransportError("target path is not a canonical Kodepoia update target")
    try:
        target = UpdateTargetSpec(
            channel=parts[1],
            platform=parts[2],
            public_version=parts[3],
            source_sha=parts[4],
            filename=parts[5],
        )
    except ValueError as exc:
        raise UpdateTransportError(f"target path is invalid: {exc}") from exc
    if target.path != path:
        raise UpdateTransportError("target path is not canonically encoded")
    return target


class NetworkUpdateTransport:
    """R19.3 bounded HTTPS transport for TUF metadata and GitHub release targets.

    Redirects are never followed implicitly. Metadata must remain on its exact
    configured HTTPS origin and repository path. Installer redirects are only
    allowed to explicitly declared GitHub asset-delivery hosts.
    """

    def __init__(
        self,
        policy: NetworkTransportPolicy | None = None,
        *,
        pool: urllib3.PoolManager | None = None,
    ) -> None:
        self.policy = policy or NetworkTransportPolicy()
        self.pool = pool or urllib3.PoolManager(cert_reqs="CERT_REQUIRED")
        self.timeout = Timeout(
            connect=self.policy.connect_timeout_seconds,
            read=self.policy.read_timeout_seconds,
        )
        self._metadata_origin = _origin(self.policy.metadata_base_url)
        self._metadata_path = urlsplit(self.policy.metadata_base_url).path
        self._release_origin = _origin(self.policy.release_asset_base_url)

    def _metadata_url(self, name: str) -> str:
        safe = _safe_metadata_name(name)
        return f"{self.policy.metadata_base_url}{quote(safe, safe='-._~')}"

    def _target_url(self, path: str) -> str:
        target = _target_from_path(path)
        tag = quote(f"v{target.public_version}", safe="-._~")
        filename = quote(target.filename, safe="-._~")
        return f"{self.policy.release_asset_base_url}{tag}/{filename}"

    def _redirect_allowed(self, current: str, target: str, *, metadata: bool) -> bool:
        parsed = urlsplit(target)
        if parsed.scheme.lower() != "https" or not parsed.hostname or parsed.username or parsed.password:
            return False
        if metadata:
            return _origin(target) == self._metadata_origin and parsed.path.startswith(self._metadata_path)
        host = parsed.hostname.lower()
        return _origin(current) == self._release_origin and host in self.policy.target_redirect_hosts or (
            urlsplit(current).hostname or ""
        ).lower() in self.policy.target_redirect_hosts and host in self.policy.target_redirect_hosts

    def _request(self, url: str, *, metadata: bool):
        current = url
        for redirect_count in range(self.policy.max_redirects + 1):
            try:
                response = self.pool.request(
                    "GET",
                    current,
                    headers={"User-Agent": "Kodepoia-Updater/1", "Accept-Encoding": "identity"},
                    timeout=self.timeout,
                    preload_content=False,
                    redirect=False,
                    retries=False,
                )
            except (ConnectTimeoutError, ReadTimeoutError, NewConnectionError) as exc:
                raise UpdateTransportOffline("update repository is offline or timed out") from exc
            except SSLError as exc:
                raise UpdateTransportError("update repository TLS verification failed") from exc
            except HTTPError as exc:
                raise UpdateTransportError("update repository transport failed") from exc

            status = int(getattr(response, "status", 0))
            if status in {301, 302, 303, 307, 308}:
                location = response.headers.get("location")
                response.release_conn()
                if redirect_count >= self.policy.max_redirects:
                    raise UpdateTransportError("update repository redirect limit exceeded")
                if not location:
                    raise UpdateTransportError("update repository redirect is missing Location")
                next_url = urllib3.util.url.parse_url(current).url
                from urllib.parse import urljoin

                next_url = urljoin(next_url, location)
                if not self._redirect_allowed(current, next_url, metadata=metadata):
                    raise UpdateTransportError("update repository redirect escaped an authorized HTTPS origin")
                current = next_url
                continue
            if status in {408, 429, 502, 503, 504}:
                response.release_conn()
                raise UpdateTransportOffline(f"update repository is temporarily unavailable (HTTP {status})")
            if status != 200:
                response.release_conn()
                raise UpdateTransportError(f"update repository returned HTTP {status}")
            return response
        raise UpdateTransportError("update repository redirect limit exceeded")

    @staticmethod
    def _content_length(response) -> int | None:
        value = response.headers.get("content-length")
        if value is None:
            return None
        try:
            length = int(value)
        except (TypeError, ValueError) as exc:
            raise UpdateTransportError("update repository returned an invalid Content-Length") from exc
        if length < 0:
            raise UpdateTransportError("update repository returned a negative Content-Length")
        return length

    def _read_bounded(self, response, *, maximum: int, label: str) -> bytes:
        declared = self._content_length(response)
        if declared is not None and declared > maximum:
            response.release_conn()
            raise UpdateTransportError(f"{label} exceeds the configured size ceiling")
        data = bytearray()
        try:
            while True:
                chunk = response.read(min(64 * 1024, maximum + 1 - len(data)), decode_content=False)
                if not chunk:
                    break
                data.extend(chunk)
                if len(data) > maximum:
                    raise UpdateTransportError(f"{label} exceeds the configured size ceiling")
        except ReadTimeoutError as exc:
            raise UpdateTransportOffline("update repository read timed out") from exc
        except HTTPError as exc:
            raise UpdateTransportError("update repository response read failed") from exc
        finally:
            response.release_conn()
        return bytes(data)

    def fetch_metadata(self, name: str) -> bytes:
        response = self._request(self._metadata_url(name), metadata=True)
        return self._read_bounded(
            response,
            maximum=self.policy.max_metadata_bytes,
            label="update metadata",
        )

    def fetch_target(self, path: str) -> bytes:
        response = self._request(self._target_url(path), metadata=False)
        return self._read_bounded(
            response,
            maximum=self.policy.max_target_bytes,
            label="update target",
        )

    def iter_target(self, path: str, *, chunk_size: int) -> Iterable[bytes]:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        response = self._request(self._target_url(path), metadata=False)
        declared = self._content_length(response)
        if declared is not None and declared > self.policy.max_target_bytes:
            response.release_conn()
            raise UpdateTransportError("update target exceeds the configured size ceiling")
        total = 0
        try:
            while True:
                try:
                    chunk = response.read(chunk_size, decode_content=False)
                except ReadTimeoutError as exc:
                    raise UpdateTransportOffline("update repository read timed out") from exc
                if not chunk:
                    break
                total += len(chunk)
                if total > self.policy.max_target_bytes:
                    raise UpdateTransportError("update target exceeds the configured size ceiling")
                yield bytes(chunk)
        finally:
            response.release_conn()
