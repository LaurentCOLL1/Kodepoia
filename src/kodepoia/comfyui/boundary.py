from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import SplitResult, urljoin, urlsplit

from .errors import ComfyBoundaryError

_ALLOWED_SCHEMES = frozenset({"http", "https"})
_ALLOWED_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1"})


def _validated_parts(url: str, *, allow_route: bool) -> SplitResult:
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError as exc:
        raise ComfyBoundaryError("Malformed ComfyUI endpoint") from exc

    scheme = parts.scheme.lower()
    if scheme not in _ALLOWED_SCHEMES:
        raise ComfyBoundaryError("ComfyUI endpoint scheme must be http or https")
    if parts.username is not None or parts.password is not None:
        raise ComfyBoundaryError("ComfyUI endpoint credentials are not allowed")
    if parts.hostname not in _ALLOWED_LOOPBACK_HOSTS:
        raise ComfyBoundaryError("ComfyUI endpoint must use an explicit accepted loopback literal")
    if port is None:
        raise ComfyBoundaryError("ComfyUI endpoint must include an explicit port")
    if not 1 <= port <= 65535:
        raise ComfyBoundaryError("ComfyUI endpoint port is out of range")
    if parts.fragment:
        raise ComfyBoundaryError("ComfyUI endpoint fragments are not allowed")
    if allow_route:
        return parts
    if parts.query:
        raise ComfyBoundaryError("ComfyUI origin queries are not allowed")
    if parts.path not in {"", "/"}:
        raise ComfyBoundaryError("ComfyUI origin must not contain a route path")
    return parts


def _origin_tuple(parts: SplitResult) -> tuple[str, str, int]:
    port = parts.port
    if port is None or parts.hostname is None:
        raise ComfyBoundaryError("ComfyUI endpoint origin is incomplete")
    return parts.scheme.lower(), parts.hostname, port


@dataclass(frozen=True, slots=True)
class ComfyEndpoint:
    scheme: str
    host: str
    port: int

    def __post_init__(self) -> None:
        candidate_host = f"[{self.host}]" if ":" in self.host else self.host
        normalized = self.parse(f"{self.scheme}://{candidate_host}:{self.port}")
        object.__setattr__(self, "scheme", normalized.scheme)
        object.__setattr__(self, "host", normalized.host)
        object.__setattr__(self, "port", normalized.port)

    @classmethod
    def parse(cls, origin: str) -> "ComfyEndpoint":
        if not isinstance(origin, str) or not origin:
            raise ComfyBoundaryError("ComfyUI origin must be a non-empty string")
        parts = _validated_parts(origin, allow_route=False)
        if parts.hostname is None or parts.port is None:
            raise ComfyBoundaryError("ComfyUI origin is incomplete")
        instance = object.__new__(cls)
        object.__setattr__(instance, "scheme", parts.scheme.lower())
        object.__setattr__(instance, "host", parts.hostname)
        object.__setattr__(instance, "port", parts.port)
        return instance

    @property
    def origin(self) -> str:
        host = f"[{self.host}]" if ":" in self.host else self.host
        return f"{self.scheme}://{host}:{self.port}"

    @property
    def websocket_origin(self) -> str:
        websocket_scheme = "wss" if self.scheme == "https" else "ws"
        host = f"[{self.host}]" if ":" in self.host else self.host
        return f"{websocket_scheme}://{host}:{self.port}"

    def validate_redirect(self, location: str) -> str:
        if not isinstance(location, str) or not location:
            raise ComfyBoundaryError("Redirect location must be a non-empty string")
        absolute = urljoin(f"{self.origin}/", location)
        target = _validated_parts(absolute, allow_route=True)
        if _origin_tuple(target) != (self.scheme, self.host, self.port):
            raise ComfyBoundaryError("ComfyUI redirect attempted to leave the accepted loopback origin")
        return absolute

    def canonical(self) -> dict[str, object]:
        return {"scheme": self.scheme, "host": self.host, "port": self.port, "origin": self.origin}
