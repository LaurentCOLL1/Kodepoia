from __future__ import annotations

import codecs
import hashlib
import http.client
import ipaddress
import socket
import ssl
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Protocol
from urllib.parse import SplitResult, urljoin, urlsplit, urlunsplit

from kodepoia.core.guardian import ActionRequest, ActionType, DecisionKind, KodeGuardian
from kodepoia.exceptions import PermissionDenied
from kodepoia.intelligence.research.contracts import (
    ResearchArtifact,
    ResearchFreshness,
    ResearchSource,
    ResearchSourceKind,
    ResearchStatus,
)
from kodepoia.intelligence.research.store import ResearchStore


class WebResearchError(RuntimeError):
    """Base error for governed Web research."""


class WebPolicyViolation(PermissionError, WebResearchError):
    """Raised when a URL/response violates the deterministic Web safety policy."""


class WebTransportError(WebResearchError):
    """Raised when the bounded network transport cannot complete a request."""


class WebRateLimitExceeded(WebResearchError):
    """Raised rather than sleeping/retrying when the configured host cadence is exceeded."""


@dataclass(frozen=True, slots=True)
class WebPolicy:
    timeout_seconds: float = 10.0
    max_response_bytes: int = 2 * 1024 * 1024
    max_redirects: int = 5
    min_host_interval_seconds: float = 0.25
    allowed_ports: tuple[int, ...] = (80, 443)
    allowed_mime_types: tuple[str, ...] = (
        "text/html",
        "text/plain",
        "application/json",
        "application/xml",
        "text/xml",
        "application/xhtml+xml",
    )

    def __post_init__(self) -> None:
        if not 0.1 <= self.timeout_seconds <= 60.0:
            raise ValueError("Web timeout must be between 0.1 and 60 seconds")
        if not 1 <= self.max_response_bytes <= 16 * 1024 * 1024:
            raise ValueError("Web response limit must be between 1 byte and 16 MiB")
        if not 0 <= self.max_redirects <= 10:
            raise ValueError("Web redirect limit must be between 0 and 10")
        if not 0.0 <= self.min_host_interval_seconds <= 60.0:
            raise ValueError("Web host interval must be between 0 and 60 seconds")
        if not self.allowed_ports or any(not 1 <= port <= 65535 for port in self.allowed_ports):
            raise ValueError("Web policy must define valid allowed ports")
        if not self.allowed_mime_types:
            raise ValueError("Web policy must define at least one allowed MIME type")


@dataclass(frozen=True, slots=True)
class WebRequest:
    url: str
    retrieved_at: str
    persist_cache: bool = True

    def __post_init__(self) -> None:
        if not self.url.strip():
            raise ValueError("Web request URL must not be empty")
        _require_timestamp(self.retrieved_at, "retrieved_at")


@dataclass(frozen=True, slots=True)
class ResolvedWebTarget:
    normalized_url: str
    scheme: str
    hostname: str
    port: int
    address: str

    @property
    def host_header(self) -> str:
        rendered = f"[{self.hostname}]" if ":" in self.hostname else self.hostname
        default_port = 443 if self.scheme == "https" else 80
        return rendered if self.port == default_port else f"{rendered}:{self.port}"


@dataclass(frozen=True, slots=True)
class RawWebResponse:
    url: str
    status_code: int
    headers: Mapping[str, str]
    body: bytes

    def header(self, name: str) -> str:
        wanted = name.lower()
        for key, value in self.headers.items():
            if key.lower() == wanted:
                return str(value)
        return ""


@dataclass(frozen=True, slots=True)
class WebSection:
    heading: str
    text: str
    index: int

    def __post_init__(self) -> None:
        if self.index < 0:
            raise ValueError("Web section index must be non-negative")


@dataclass(frozen=True, slots=True)
class ExtractedWebDocument:
    text: str
    title: str = ""
    author: str = ""
    canonical_url: str = ""
    published_at: str | None = None
    updated_at: str | None = None
    sections: tuple[WebSection, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WebResearchResult:
    status: ResearchStatus
    artifact: ResearchArtifact | None
    final_url: str
    redirects: tuple[str, ...] = ()
    sections: tuple[WebSection, ...] = ()
    reason: str = ""

    def __post_init__(self) -> None:
        if self.status is ResearchStatus.READY and self.artifact is None:
            raise ValueError("Ready Web research requires an artifact")
        if self.artifact is None and self.sections:
            raise ValueError("Web sections require an artifact")


class SingleRequestTransport(Protocol):
    def send(self, target: ResolvedWebTarget, *, policy: WebPolicy) -> RawWebResponse: ...


Resolver = Callable[[str, int], tuple[str, ...]]


def _require_timestamp(value: str, field_name: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone")


def _default_resolver(hostname: str, port: int) -> tuple[str, ...]:
    try:
        answers = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise WebTransportError(f"DNS resolution failed for {hostname}") from exc
    addresses = tuple(dict.fromkeys(answer[4][0] for answer in answers))
    if not addresses:
        raise WebTransportError(f"DNS resolution returned no addresses for {hostname}")
    return addresses


def _normalize_url(url: str) -> tuple[str, SplitResult]:
    raw = url.strip()
    if any(ord(character) < 32 or ord(character) == 127 for character in raw):
        raise WebPolicyViolation("Web URL contains control characters")
    parsed = urlsplit(raw)
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise WebPolicyViolation("Only HTTP(S) research URLs are allowed")
    if parsed.username is not None or parsed.password is not None:
        raise WebPolicyViolation("Credential-bearing Web URLs are forbidden")
    if not parsed.hostname:
        raise WebPolicyViolation("Web URL requires a hostname")
    try:
        hostname = parsed.hostname.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise WebPolicyViolation("Web hostname is not valid IDNA") from exc
    if hostname == "localhost" or hostname.endswith(".localhost") or hostname.endswith(".local"):
        raise WebPolicyViolation("Local hostnames are forbidden for Web research")
    try:
        port = parsed.port
    except ValueError as exc:
        raise WebPolicyViolation("Web URL port is invalid") from exc
    default_port = 443 if scheme == "https" else 80
    port = port or default_port
    netloc_host = f"[{hostname}]" if ":" in hostname else hostname
    netloc = netloc_host if port == default_port else f"{netloc_host}:{port}"
    path = parsed.path or "/"
    normalized = urlunsplit((scheme, netloc, path, parsed.query, ""))
    return normalized, urlsplit(normalized)


def _require_global_address(value: str) -> str:
    try:
        address = ipaddress.ip_address(value)
    except ValueError as exc:
        raise WebPolicyViolation(f"DNS returned an invalid IP address: {value}") from exc
    if not address.is_global:
        raise WebPolicyViolation(f"Non-public Web target is forbidden: {address}")
    return address.compressed


def resolve_public_target(
    url: str,
    *,
    policy: WebPolicy,
    resolver: Resolver = _default_resolver,
) -> ResolvedWebTarget:
    normalized, parsed = _normalize_url(url)
    hostname = parsed.hostname
    assert hostname is not None
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if port not in policy.allowed_ports:
        raise WebPolicyViolation(f"Web target port is not allowed: {port}")

    literal: str | None = None
    try:
        literal = ipaddress.ip_address(hostname).compressed
    except ValueError:
        pass
    addresses = (literal,) if literal is not None else resolver(hostname, port)
    validated = tuple(_require_global_address(address) for address in addresses)
    if not validated:
        raise WebPolicyViolation("Web target did not resolve to a public address")
    return ResolvedWebTarget(
        normalized_url=normalized,
        scheme=parsed.scheme,
        hostname=hostname,
        port=port,
        address=validated[0],
    )


@dataclass(slots=True)
class HostRateLimiter:
    min_interval_seconds: float
    clock: Callable[[], float] = time.monotonic
    _last: dict[str, float] = field(default_factory=dict, init=False, repr=False)

    def acquire(self, hostname: str) -> None:
        if self.min_interval_seconds <= 0:
            return
        now = float(self.clock())
        previous = self._last.get(hostname)
        if previous is not None and now - previous < self.min_interval_seconds:
            raise WebRateLimitExceeded(
                f"Web host rate limit requires {self.min_interval_seconds:.3f}s between requests"
            )
        self._last[hostname] = now


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(
        self,
        connect_host: str,
        *,
        server_hostname: str,
        port: int,
        timeout: float,
        context: ssl.SSLContext,
    ) -> None:
        super().__init__(connect_host, port=port, timeout=timeout, context=context)
        self._kodepoia_server_hostname = server_hostname

    def connect(self) -> None:
        self.sock = socket.create_connection(
            (self.host, self.port),
            self.timeout,
            self.source_address,
        )
        self.sock = self._context.wrap_socket(
            self.sock,
            server_hostname=self._kodepoia_server_hostname,
        )


@dataclass(slots=True)
class GuardedHttpTransport:
    guardian: KodeGuardian
    user_agent: str = "KodepoiaResearch/0.1"

    def send(self, target: ResolvedWebTarget, *, policy: WebPolicy) -> RawWebResponse:
        decision = self.guardian.authorize(
            ActionRequest(
                action=ActionType.NETWORK,
                actor="KodeResearch.Web",
                target=target.normalized_url,
                metadata={"host": target.hostname, "port": target.port},
            )
        )
        if decision.kind is not DecisionKind.ALLOW:
            raise PermissionDenied(f"Guardian denied Web research: {decision.reason}")

        parsed = urlsplit(target.normalized_url)
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"
        headers = {
            "Host": target.host_header,
            "User-Agent": self.user_agent,
            "Accept": "text/html,text/plain,application/json,application/xml,text/xml,application/xhtml+xml",
            "Accept-Encoding": "identity",
            "Connection": "close",
        }
        connection: http.client.HTTPConnection
        if target.scheme == "https":
            connection = _PinnedHTTPSConnection(
                target.address,
                server_hostname=target.hostname,
                port=target.port,
                timeout=policy.timeout_seconds,
                context=ssl.create_default_context(),
            )
        else:
            connection = http.client.HTTPConnection(
                target.address,
                port=target.port,
                timeout=policy.timeout_seconds,
            )
        try:
            connection.request("GET", path, headers=headers)
            response = connection.getresponse()
            response_headers = {key: value for key, value in response.getheaders()}
            content_encoding = response.getheader("Content-Encoding", "").strip().lower()
            if content_encoding not in {"", "identity"}:
                raise WebPolicyViolation("Encoded/compressed Web responses are not accepted")
            content_type = response.getheader("Content-Type", "")
            mime, _ = _mime_and_charset(content_type)
            if 200 <= int(response.status) < 300:
                if not mime:
                    raise WebPolicyViolation("Web response is missing Content-Type")
                if mime not in policy.allowed_mime_types:
                    raise WebPolicyViolation(f"Web response MIME type is not allowed: {mime}")
            content_length = response.getheader("Content-Length")
            if content_length:
                try:
                    declared = int(content_length)
                except ValueError:
                    declared = -1
                if declared > policy.max_response_bytes:
                    raise WebPolicyViolation("Web response Content-Length exceeds configured limit")
            body = response.read(policy.max_response_bytes + 1)
            if len(body) > policy.max_response_bytes:
                raise WebPolicyViolation("Web response exceeds configured byte limit")
            return RawWebResponse(
                url=target.normalized_url,
                status_code=int(response.status),
                headers=response_headers,
                body=body,
            )
        except (socket.timeout, TimeoutError) as exc:
            raise WebTransportError("Web request timed out") from exc
        except (OSError, http.client.HTTPException, ssl.SSLError) as exc:
            raise WebTransportError(f"Web request failed: {type(exc).__name__}") from exc
        finally:
            connection.close()


@dataclass(slots=True)
class FixtureWebTransport:
    """Deterministic, no-network transport for CI and unit tests."""

    routes: dict[str, tuple[RawWebResponse, ...]]
    requests: list[str] = field(default_factory=list)
    _offsets: dict[str, int] = field(default_factory=dict, init=False, repr=False)

    def send(self, target: ResolvedWebTarget, *, policy: WebPolicy) -> RawWebResponse:
        del policy
        url = target.normalized_url
        self.requests.append(url)
        responses = self.routes.get(url)
        if not responses:
            raise WebTransportError(f"No fixture response configured for {url}")
        offset = self._offsets.get(url, 0)
        if offset >= len(responses):
            raise WebTransportError(f"Fixture response queue exhausted for {url}")
        self._offsets[url] = offset + 1
        response = responses[offset]
        return RawWebResponse(
            url=url,
            status_code=response.status_code,
            headers=dict(response.headers),
            body=bytes(response.body),
        )


class _HTMLTextExtractor(HTMLParser):
    _IGNORED = {"script", "style", "noscript", "template"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.body_parts: list[str] = []
        self.sections: list[tuple[str, list[str]]] = [("", [])]
        self._ignored_depth = 0
        self._title_depth = 0
        self._heading_tag: str | None = None
        self._heading_parts: list[str] = []
        self.author = ""
        self.canonical = ""
        self.published_raw = ""
        self.updated_raw = ""
        self.robots = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        attributes = {key.lower(): (value or "") for key, value in attrs}
        if lowered in self._IGNORED:
            self._ignored_depth += 1
            return
        if self._ignored_depth:
            return
        if lowered == "title":
            self._title_depth += 1
        if lowered in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._heading_tag = lowered
            self._heading_parts = []
        if lowered == "link":
            rel = {token.lower() for token in attributes.get("rel", "").split()}
            if "canonical" in rel and attributes.get("href"):
                self.canonical = attributes["href"].strip()
        if lowered == "meta":
            name = (attributes.get("name") or attributes.get("property") or "").lower()
            content = attributes.get("content", "").strip()
            if name in {"author", "article:author"} and content:
                self.author = content
            elif name == "robots" and content:
                self.robots = content
            elif name in {
                "article:published_time",
                "date",
                "datepublished",
                "date.published",
            } and content:
                self.published_raw = content
            elif name in {
                "article:modified_time",
                "last-modified",
                "datemodified",
                "date.modified",
            } and content:
                self.updated_raw = content

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered in self._IGNORED:
            if self._ignored_depth:
                self._ignored_depth -= 1
            return
        if self._ignored_depth:
            return
        if lowered == "title" and self._title_depth:
            self._title_depth -= 1
        if self._heading_tag == lowered:
            heading = " ".join(part.strip() for part in self._heading_parts if part.strip()).strip()
            if heading:
                self.sections.append((heading, []))
            self._heading_tag = None
            self._heading_parts = []

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        cleaned = " ".join(data.split())
        if not cleaned:
            return
        if self._title_depth:
            self.title_parts.append(cleaned)
        if self._heading_tag is not None:
            self._heading_parts.append(cleaned)
        self.body_parts.append(cleaned)
        self.sections[-1][1].append(cleaned)

    def document(self) -> ExtractedWebDocument:
        title = " ".join(self.title_parts).strip()
        text = "\n".join(self.body_parts).strip()
        sections = tuple(
            WebSection(
                heading=heading,
                text="\n".join(parts).strip(),
                index=index,
            )
            for index, (heading, parts) in enumerate(self.sections)
            if parts
        )
        published = _evidenced_timestamp(self.published_raw)
        updated = _evidenced_timestamp(self.updated_raw)
        metadata: dict[str, str] = {}
        if self.published_raw and published is None:
            metadata["published_at_raw"] = self.published_raw
        if self.updated_raw and updated is None:
            metadata["updated_at_raw"] = self.updated_raw
        if self.robots:
            metadata["robots"] = self.robots
        return ExtractedWebDocument(
            text=text,
            title=title,
            author=self.author,
            canonical_url=self.canonical,
            published_at=published,
            updated_at=updated,
            sections=sections,
            metadata=metadata,
        )


def _evidenced_timestamp(value: str) -> str | None:
    candidate = value.strip()
    if not candidate:
        return None
    try:
        parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.isoformat().replace("+00:00", "Z")


def _mime_and_charset(content_type: str) -> tuple[str, str]:
    parts = [part.strip() for part in content_type.split(";")]
    mime = parts[0].lower() if parts else ""
    charset = "utf-8"
    for item in parts[1:]:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        if key.strip().lower() == "charset":
            charset = value.strip().strip("\"'") or "utf-8"
    return mime, charset


def _decode_body(body: bytes, charset: str) -> str:
    try:
        codecs.lookup(charset)
    except LookupError as exc:
        raise WebPolicyViolation(f"Unsupported Web response charset: {charset}") from exc
    try:
        return body.decode(charset, errors="strict")
    except UnicodeDecodeError as exc:
        raise WebPolicyViolation("Web response body is not valid in its declared charset") from exc


def validate_raw_web_response(response: RawWebResponse, *, policy: WebPolicy) -> None:
    if len(response.body) > policy.max_response_bytes:
        raise WebPolicyViolation("Web response exceeds configured byte limit")
    content_length = response.header("Content-Length").strip()
    if content_length:
        try:
            declared = int(content_length)
        except ValueError as exc:
            raise WebPolicyViolation("Web response Content-Length is invalid") from exc
        if declared < 0:
            raise WebPolicyViolation("Web response Content-Length is invalid")
        if declared > policy.max_response_bytes:
            raise WebPolicyViolation("Web response Content-Length exceeds configured limit")
    content_encoding = response.header("Content-Encoding").strip().lower()
    if content_encoding not in {"", "identity"}:
        raise WebPolicyViolation("Encoded/compressed Web responses are not accepted")
    mime, _ = _mime_and_charset(response.header("Content-Type"))
    if 200 <= response.status_code < 300:
        if not mime:
            raise WebPolicyViolation("Web response is missing Content-Type")
        if mime not in policy.allowed_mime_types:
            raise WebPolicyViolation(f"Web response MIME type is not allowed: {mime}")


def extract_web_document(response: RawWebResponse, *, policy: WebPolicy) -> ExtractedWebDocument:
    validate_raw_web_response(response, policy=policy)
    mime, charset = _mime_and_charset(response.header("Content-Type"))
    text = _decode_body(response.body, charset)
    if mime in {"text/html", "application/xhtml+xml"}:
        parser = _HTMLTextExtractor()
        parser.feed(text)
        parser.close()
        return parser.document()
    return ExtractedWebDocument(text=text)


@dataclass(slots=True)
class WebResearchClient:
    project_root: Path
    transport: SingleRequestTransport
    policy: WebPolicy = field(default_factory=WebPolicy)
    resolver: Resolver = _default_resolver
    rate_limiter: HostRateLimiter | None = None
    _store: ResearchStore = field(init=False, repr=False)

    def __post_init__(self) -> None:
        root = Path(self.project_root).resolve(strict=False)
        if self.rate_limiter is None:
            self.rate_limiter = HostRateLimiter(self.policy.min_host_interval_seconds)
        self.project_root = root
        self._store = ResearchStore(root)

    @staticmethod
    def _unavailable(final_url: str, redirects: tuple[str, ...], reason: str) -> WebResearchResult:
        return WebResearchResult(
            status=ResearchStatus.UNAVAILABLE,
            artifact=None,
            final_url=final_url,
            redirects=redirects,
            reason=reason,
        )

    def research(self, request: WebRequest) -> WebResearchResult:
        current_url = request.url
        redirects: list[str] = []
        response: RawWebResponse | None = None
        rate_limited_hosts: set[str] = set()

        for hop in range(self.policy.max_redirects + 1):
            target = resolve_public_target(
                current_url,
                policy=self.policy,
                resolver=self.resolver,
            )
            if target.hostname not in rate_limited_hosts:
                assert self.rate_limiter is not None
                self.rate_limiter.acquire(target.hostname)
                rate_limited_hosts.add(target.hostname)
            response = self.transport.send(target, policy=self.policy)
            validate_raw_web_response(response, policy=self.policy)
            status = response.status_code
            if status in {301, 302, 303, 307, 308}:
                location = response.header("Location").strip()
                if not location:
                    return self._unavailable(
                        target.normalized_url,
                        tuple(redirects),
                        "redirect_missing_location",
                    )
                if hop >= self.policy.max_redirects:
                    raise WebPolicyViolation("Web redirect limit exceeded")
                next_url = urljoin(target.normalized_url, location)
                next_target = resolve_public_target(
                    next_url,
                    policy=self.policy,
                    resolver=self.resolver,
                )
                redirects.append(next_target.normalized_url)
                current_url = next_target.normalized_url
                continue
            if 400 <= status <= 599:
                return self._unavailable(
                    target.normalized_url,
                    tuple(redirects),
                    f"http_status_{status}",
                )
            if status < 200 or status >= 300:
                return self._unavailable(
                    target.normalized_url,
                    tuple(redirects),
                    f"unsupported_http_status_{status}",
                )
            break

        if response is None:
            raise WebTransportError("Web transport produced no response")
        final_target = resolve_public_target(
            response.url,
            policy=self.policy,
            resolver=self.resolver,
        )
        document = extract_web_document(response, policy=self.policy)

        canonical_url = ""
        canonical_rejected = False
        if document.canonical_url:
            canonical_candidate = urljoin(final_target.normalized_url, document.canonical_url)
            try:
                canonical_url = resolve_public_target(
                    canonical_candidate,
                    policy=self.policy,
                    resolver=self.resolver,
                ).normalized_url
            except (WebPolicyViolation, WebTransportError):
                canonical_rejected = True

        content_type, charset = _mime_and_charset(response.header("Content-Type"))
        metadata = dict(document.metadata)
        metadata.update(
            {
                "web_schema_version": 1,
                "content_type": content_type,
                "charset": charset.lower(),
                "raw_sha256": hashlib.sha256(response.body).hexdigest(),
                "http_status": response.status_code,
                "redirect_chain": list(redirects),
            }
        )
        etag = response.header("ETag").strip()
        last_modified = response.header("Last-Modified").strip()
        if etag:
            metadata["etag"] = etag
        if last_modified:
            metadata["last_modified"] = last_modified
        if canonical_url:
            metadata["canonical_url"] = canonical_url
        if canonical_rejected:
            metadata["canonical_url_rejected"] = True
        x_robots = response.header("X-Robots-Tag").strip()
        if x_robots:
            metadata["x_robots_tag"] = x_robots

        source = ResearchSource(
            kind=ResearchSourceKind.WEB,
            locator=final_target.normalized_url,
            status=ResearchStatus.READY,
            title=document.title,
            author=document.author,
            published_at=document.published_at,
            updated_at=document.updated_at,
        )
        candidate = ResearchArtifact.from_content(
            source=source,
            content=document.text,
            retrieved_at=request.retrieved_at,
            freshness=ResearchFreshness.UNKNOWN,
            metadata=metadata,
        )
        artifact = candidate
        if request.persist_cache:
            if self._store.has_artifact(candidate.artifact_id):
                artifact = self._store.load_artifact(candidate.artifact_id)
            else:
                self._store.save_artifact(candidate)
        return WebResearchResult(
            status=ResearchStatus.READY,
            artifact=artifact,
            final_url=final_target.normalized_url,
            redirects=tuple(redirects),
            sections=document.sections,
        )