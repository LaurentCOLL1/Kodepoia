from __future__ import annotations

import base64
import hashlib
import http.client
import json
import re
import socket
import ssl
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote, urlencode, urlsplit

from kodepoia.core.guardian import ActionRequest, ActionType, DecisionKind, KodeGuardian
from kodepoia.core.secrets import KodeSecrets
from kodepoia.exceptions import PermissionDenied
from kodepoia.intelligence.research.contracts import (
    ResearchArtifact,
    ResearchFreshness,
    ResearchSource,
    ResearchSourceKind,
    ResearchStatus,
)
from kodepoia.intelligence.research.store import ResearchStore
from kodepoia.intelligence.research.web import (
    HostRateLimiter,
    RawWebResponse,
    ResolvedWebTarget,
    Resolver,
    SingleRequestTransport,
    WebPolicy,
    WebPolicyViolation,
    WebTransportError,
    _PinnedHTTPSConnection,
    resolve_public_target,
    validate_raw_web_response,
)

GITHUB_API_HOST = "api.github.com"
GITHUB_API_VERSION = "2022-11-28"
_NAME = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")
_OBJECT_SHA = re.compile(r"^(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})$")


class GitHubResourceKind(StrEnum):
    REPOSITORY = "repository"
    FILE = "file"
    BLOB = "blob"
    COMMIT = "commit"
    RELEASES = "releases"
    TAGS = "tags"
    ISSUE = "issue"
    ISSUE_COMMENTS = "issue_comments"
    PULL_REQUEST = "pull_request"
    PULL_COMMENTS = "pull_comments"


@dataclass(frozen=True, slots=True)
class GitHubCredentialRef:
    namespace: str
    key: str

    def __post_init__(self) -> None:
        if not self.namespace.strip() or not self.key.strip():
            raise ValueError("GitHub credential namespace/key must not be empty")


@dataclass(frozen=True, slots=True)
class GitHubResearchRequest:
    owner: str
    repo: str
    kind: GitHubResourceKind
    retrieved_at: str
    path: str = ""
    ref: str = ""
    number: int | None = None
    max_pages: int = 3
    persist_cache: bool = True

    def __post_init__(self) -> None:
        owner = self.owner.strip()
        repo = self.repo.strip()
        if not _NAME.fullmatch(owner) or owner in {".", ".."}:
            raise ValueError("GitHub owner is invalid")
        if not _NAME.fullmatch(repo) or repo in {".", ".."}:
            raise ValueError("GitHub repository name is invalid")
        if not 1 <= self.max_pages <= 10:
            raise ValueError("GitHub max_pages must be between 1 and 10")
        if self.number is not None and self.number < 1:
            raise ValueError("GitHub issue/PR number must be positive")
        if any(ord(character) < 32 or ord(character) == 127 for character in self.ref):
            raise ValueError("GitHub ref contains control characters")
        try:
            timestamp = datetime.fromisoformat(self.retrieved_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("GitHub retrieved_at must be ISO-8601") from exc
        if timestamp.tzinfo is None:
            raise ValueError("GitHub retrieved_at must include a timezone")

        requires_number = {
            GitHubResourceKind.ISSUE,
            GitHubResourceKind.ISSUE_COMMENTS,
            GitHubResourceKind.PULL_REQUEST,
            GitHubResourceKind.PULL_COMMENTS,
        }
        if self.kind in requires_number and self.number is None:
            raise ValueError(f"{self.kind.value} requires a number")
        if self.kind not in requires_number and self.number is not None:
            raise ValueError(f"{self.kind.value} does not accept a number")

        path = self.path.strip().replace("\\", "/")
        if self.kind is GitHubResourceKind.FILE:
            if not path:
                raise ValueError("GitHub file research requires a path")
            parsed_path = PurePosixPath(path)
            if parsed_path.is_absolute() or ".." in parsed_path.parts:
                raise ValueError("GitHub file path must be repository-relative")
        elif path:
            raise ValueError(f"{self.kind.value} does not accept a file path")

        if self.kind is GitHubResourceKind.BLOB:
            if not _OBJECT_SHA.fullmatch(self.ref.strip()):
                raise ValueError("GitHub blob research requires an exact object SHA")
        object.__setattr__(self, "owner", owner)
        object.__setattr__(self, "repo", repo)
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "ref", self.ref.strip())


@dataclass(frozen=True, slots=True)
class GitHubRateLimit:
    limit: int | None = None
    remaining: int | None = None
    used: int | None = None
    reset_epoch: int | None = None
    resource: str = ""
    retry_after: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "limit": self.limit,
            "remaining": self.remaining,
            "used": self.used,
            "reset_epoch": self.reset_epoch,
            "resource": self.resource,
            "retry_after": self.retry_after,
        }


@dataclass(frozen=True, slots=True)
class GitHubResearchResult:
    status: ResearchStatus
    artifact: ResearchArtifact | None
    reason: str = ""
    exact_commit_sha: str = ""
    pages: int = 0
    pagination_truncated: bool = False
    rate_limits: tuple[GitHubRateLimit, ...] = ()

    def __post_init__(self) -> None:
        if self.status is ResearchStatus.READY and self.artifact is None:
            raise ValueError("Ready GitHub research requires an artifact")
        if self.pages < 0:
            raise ValueError("GitHub result pages cannot be negative")


def _int_header(response: RawWebResponse, name: str) -> int | None:
    value = response.header(name).strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _rate_limit(response: RawWebResponse) -> GitHubRateLimit:
    return GitHubRateLimit(
        limit=_int_header(response, "X-RateLimit-Limit"),
        remaining=_int_header(response, "X-RateLimit-Remaining"),
        used=_int_header(response, "X-RateLimit-Used"),
        reset_epoch=_int_header(response, "X-RateLimit-Reset"),
        resource=response.header("X-RateLimit-Resource").strip(),
        retry_after=response.header("Retry-After").strip(),
    )


def _has_next_link(response: RawWebResponse) -> bool:
    link = response.header("Link")
    for item in link.split(","):
        parts = [part.strip() for part in item.split(";")]
        if len(parts) < 2:
            continue
        relations = " ".join(parts[1:]).lower()
        if 'rel="next"' in relations or "rel=next" in relations:
            return True
    return False


def _canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    )


def _github_url(owner: str, repo: str, suffix: str = "") -> str:
    base = f"https://github.com/{quote(owner, safe='')}/{quote(repo, safe='')}"
    return f"{base}/{suffix.lstrip('/')}" if suffix else base


def _api_url(owner: str, repo: str, suffix: str = "", query: dict[str, Any] | None = None) -> str:
    base = (
        f"https://{GITHUB_API_HOST}/repos/"
        f"{quote(owner, safe='')}/{quote(repo, safe='')}"
    )
    if suffix:
        base = f"{base}/{suffix.lstrip('/')}"
    if query:
        base = f"{base}?{urlencode(query)}"
    return base


@dataclass(slots=True)
class GitHubApiTransport:
    """Narrow production GitHub REST transport; no generic delegated headers are exposed."""

    guardian: KodeGuardian
    secrets: KodeSecrets | None = None
    credential_ref: GitHubCredentialRef | None = None
    user_agent: str = "KodepoiaResearch/0.1"

    def send(self, target: ResolvedWebTarget, *, policy: WebPolicy) -> RawWebResponse:
        if (
            target.scheme != "https"
            or target.hostname != GITHUB_API_HOST
            or target.port != 443
        ):
            raise WebPolicyViolation("GitHub API transport is bound to https://api.github.com:443")

        decision = self.guardian.authorize(
            ActionRequest(
                action=ActionType.NETWORK,
                actor="KodeResearch.GitHub",
                target=target.normalized_url,
                metadata={"host": target.hostname, "port": target.port},
            )
        )
        if decision.kind is not DecisionKind.ALLOW:
            raise PermissionDenied(f"Guardian denied GitHub research: {decision.reason}")

        token: str | None = None
        if self.credential_ref is not None:
            if self.secrets is None:
                raise PermissionDenied("GitHub credential reference requires KodeSecrets")
            token = self.secrets.delegated_get(
                self.credential_ref.namespace,
                self.credential_ref.key,
            )
            if not token:
                raise PermissionDenied("Configured GitHub credential is unavailable")

        parsed = urlsplit(target.normalized_url)
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"
        headers = {
            "Host": target.host_header,
            "User-Agent": self.user_agent,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "Accept-Encoding": "identity",
            "Connection": "close",
        }
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"

        connection = _PinnedHTTPSConnection(
            target.address,
            server_hostname=target.hostname,
            port=443,
            timeout=policy.timeout_seconds,
            context=ssl.create_default_context(),
        )
        try:
            connection.request("GET", path, headers=headers)
            response = connection.getresponse()
            response_headers = {key: value for key, value in response.getheaders()}
            content_encoding = response.getheader("Content-Encoding", "").strip().lower()
            if content_encoding not in {"", "identity"}:
                raise WebPolicyViolation("Encoded/compressed GitHub responses are not accepted")
            content_length = response.getheader("Content-Length")
            if content_length:
                try:
                    declared = int(content_length)
                except ValueError:
                    declared = -1
                if declared > policy.max_response_bytes:
                    raise WebPolicyViolation("GitHub response Content-Length exceeds configured limit")
            body = response.read(policy.max_response_bytes + 1)
            if len(body) > policy.max_response_bytes:
                raise WebPolicyViolation("GitHub response exceeds configured byte limit")
            return RawWebResponse(
                url=target.normalized_url,
                status_code=int(response.status),
                headers=response_headers,
                body=body,
            )
        except (socket.timeout, TimeoutError) as exc:
            raise WebTransportError("GitHub request timed out") from exc
        except (OSError, http.client.HTTPException, ssl.SSLError) as exc:
            raise WebTransportError(f"GitHub request failed: {type(exc).__name__}") from exc
        finally:
            if token is not None and self.secrets is not None:
                token = None
            connection.close()


@dataclass(slots=True)
class GitHubResearchClient:
    project_root: Path
    transport: SingleRequestTransport
    policy: WebPolicy = field(
        default_factory=lambda: WebPolicy(
            min_host_interval_seconds=0.25,
            allowed_ports=(443,),
            allowed_mime_types=("application/json", "application/vnd.github+json"),
        )
    )
    resolver: Resolver | None = None
    rate_limiter: HostRateLimiter | None = None
    max_decoded_file_bytes: int = 2 * 1024 * 1024
    _store: ResearchStore = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.project_root = Path(self.project_root).resolve(strict=False)
        self._store = ResearchStore(self.project_root)
        if self.rate_limiter is None:
            self.rate_limiter = HostRateLimiter(self.policy.min_host_interval_seconds)
        if not 1 <= self.max_decoded_file_bytes <= 16 * 1024 * 1024:
            raise ValueError("GitHub decoded file limit must be between 1 byte and 16 MiB")

    def _target(self, url: str) -> ResolvedWebTarget:
        resolver = self.resolver
        if resolver is None:
            return resolve_public_target(url, policy=self.policy)
        return resolve_public_target(url, policy=self.policy, resolver=resolver)

    def _send(self, url: str) -> RawWebResponse:
        target = self._target(url)
        if target.hostname != GITHUB_API_HOST or target.scheme != "https" or target.port != 443:
            raise WebPolicyViolation("GitHub research target escaped the fixed API origin")
        response = self.transport.send(target, policy=self.policy)
        validate_raw_web_response(response, policy=self.policy)
        if 300 <= response.status_code < 400:
            raise WebPolicyViolation("GitHub API redirects are not followed")
        return response

    @staticmethod
    def _payload(response: RawWebResponse) -> Any:
        try:
            return json.loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise WebPolicyViolation("GitHub API response is not valid UTF-8 JSON") from exc

    @staticmethod
    def _status_reason(response: RawWebResponse) -> str | None:
        if response.status_code in {403, 429}:
            remaining = _int_header(response, "X-RateLimit-Remaining")
            if remaining == 0 or response.status_code == 429:
                return "rate_limited"
        if 400 <= response.status_code <= 599:
            return f"http_status_{response.status_code}"
        if response.status_code < 200 or response.status_code >= 300:
            return f"unsupported_http_status_{response.status_code}"
        return None

    def _single_json(self, url: str) -> tuple[RawWebResponse, Any, GitHubRateLimit]:
        response = self._send(url)
        reason = self._status_reason(response)
        if reason is not None:
            raise _GitHubUnavailable(reason, response)
        return response, self._payload(response), _rate_limit(response)

    def _paged_json(
        self,
        request: GitHubResearchRequest,
        suffix: str,
    ) -> tuple[list[Any], list[str], tuple[GitHubRateLimit, ...], bool]:
        items: list[Any] = []
        page_urls: list[str] = []
        limits: list[GitHubRateLimit] = []
        truncated = False
        for page in range(1, request.max_pages + 1):
            url = _api_url(
                request.owner,
                request.repo,
                suffix,
                {"per_page": 100, "page": page},
            )
            response = self._send(url)
            reason = self._status_reason(response)
            if reason is not None:
                raise _GitHubUnavailable(reason, response)
            payload = self._payload(response)
            if not isinstance(payload, list):
                raise WebPolicyViolation("Paginated GitHub endpoint did not return a JSON array")
            items.extend(payload)
            page_urls.append(url)
            limits.append(_rate_limit(response))
            has_next = _has_next_link(response)
            if not has_next:
                break
            if page == request.max_pages:
                truncated = True
        return items, page_urls, tuple(limits), truncated

    def _resolve_commit(
        self,
        request: GitHubResearchRequest,
        ref: str,
    ) -> tuple[str, GitHubRateLimit, str]:
        safe_ref = quote(ref or "HEAD", safe="")
        url = _api_url(request.owner, request.repo, f"commits/{safe_ref}")
        response, payload, limit = self._single_json(url)
        if not isinstance(payload, dict) or not isinstance(payload.get("sha"), str):
            raise WebPolicyViolation("GitHub commit response is missing exact SHA")
        sha = payload["sha"].lower()
        if not _OBJECT_SHA.fullmatch(sha):
            raise WebPolicyViolation("GitHub commit response contains an invalid SHA")
        return sha, limit, url

    def _decode_content(
        self,
        payload: Any,
        *,
        label: str,
    ) -> str:
        if not isinstance(payload, dict):
            raise _GitHubContentUnavailable(f"{label}_not_object")
        if payload.get("encoding") != "base64" or not isinstance(payload.get("content"), str):
            raise _GitHubContentUnavailable(f"{label}_content_unavailable")
        try:
            raw = base64.b64decode(payload["content"], validate=False)
        except (ValueError, TypeError) as exc:
            raise WebPolicyViolation(f"{label} base64 payload is invalid") from exc
        if len(raw) > self.max_decoded_file_bytes:
            raise _GitHubContentUnavailable(f"{label}_too_large")
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise _GitHubContentUnavailable(f"{label}_non_text") from exc

    def research(self, request: GitHubResearchRequest) -> GitHubResearchResult:
        assert self.rate_limiter is not None
        self.rate_limiter.acquire(GITHUB_API_HOST)
        rate_limits: list[GitHubRateLimit] = []
        api_urls: list[str] = []
        exact_commit_sha = ""
        truncated = False
        pages = 0

        try:
            if request.kind is GitHubResourceKind.REPOSITORY:
                url = _api_url(request.owner, request.repo)
                _, payload, limit = self._single_json(url)
                rate_limits.append(limit)
                api_urls.append(url)
                content = _canonical_json(payload)
                locator = _github_url(request.owner, request.repo)
                pages = 1
            elif request.kind is GitHubResourceKind.COMMIT:
                ref = request.ref or "HEAD"
                url = _api_url(
                    request.owner,
                    request.repo,
                    f"commits/{quote(ref, safe='')}",
                )
                _, payload, limit = self._single_json(url)
                if not isinstance(payload, dict) or not isinstance(payload.get("sha"), str):
                    raise WebPolicyViolation("GitHub commit response is missing exact SHA")
                exact_commit_sha = payload["sha"].lower()
                if not _OBJECT_SHA.fullmatch(exact_commit_sha):
                    raise WebPolicyViolation("GitHub commit response contains an invalid SHA")
                rate_limits.append(limit)
                api_urls.append(url)
                content = _canonical_json(payload)
                locator = _github_url(
                    request.owner,
                    request.repo,
                    f"commit/{exact_commit_sha}",
                )
                pages = 1
            elif request.kind is GitHubResourceKind.FILE:
                exact_commit_sha, limit, commit_url = self._resolve_commit(
                    request,
                    request.ref or "HEAD",
                )
                rate_limits.append(limit)
                api_urls.append(commit_url)
                file_url = _api_url(
                    request.owner,
                    request.repo,
                    f"contents/{quote(request.path, safe='/')}",
                    {"ref": exact_commit_sha},
                )
                _, payload, limit = self._single_json(file_url)
                rate_limits.append(limit)
                api_urls.append(file_url)
                if not isinstance(payload, dict) or payload.get("type") != "file":
                    raise _GitHubContentUnavailable("not_regular_file")
                pages = 2
                content = self._decode_content(payload, label="file")
                locator = _github_url(
                    request.owner,
                    request.repo,
                    f"blob/{exact_commit_sha}/{quote(request.path, safe='/')}",
                )
            elif request.kind is GitHubResourceKind.BLOB:
                blob_sha = request.ref.lower()
                blob_url = _api_url(
                    request.owner,
                    request.repo,
                    f"git/blobs/{quote(blob_sha, safe='')}",
                )
                _, payload, limit = self._single_json(blob_url)
                rate_limits.append(limit)
                api_urls.append(blob_url)
                pages = 1
                content = self._decode_content(payload, label="blob")
                locator = blob_url
            elif request.kind in {
                GitHubResourceKind.RELEASES,
                GitHubResourceKind.TAGS,
                GitHubResourceKind.ISSUE_COMMENTS,
                GitHubResourceKind.PULL_COMMENTS,
            }:
                if request.kind is GitHubResourceKind.RELEASES:
                    suffix = "releases"
                    locator = _github_url(request.owner, request.repo, "releases")
                elif request.kind is GitHubResourceKind.TAGS:
                    suffix = "tags"
                    locator = _github_url(request.owner, request.repo, "tags")
                elif request.kind is GitHubResourceKind.ISSUE_COMMENTS:
                    assert request.number is not None
                    suffix = f"issues/{request.number}/comments"
                    locator = _github_url(
                        request.owner,
                        request.repo,
                        f"issues/{request.number}",
                    )
                else:
                    assert request.number is not None
                    suffix = f"pulls/{request.number}/comments"
                    locator = _github_url(
                        request.owner,
                        request.repo,
                        f"pull/{request.number}",
                    )
                payload, urls, limits, truncated = self._paged_json(request, suffix)
                content = _canonical_json(payload)
                api_urls.extend(urls)
                rate_limits.extend(limits)
                pages = len(urls)
            elif request.kind in {
                GitHubResourceKind.ISSUE,
                GitHubResourceKind.PULL_REQUEST,
            }:
                assert request.number is not None
                if request.kind is GitHubResourceKind.ISSUE:
                    suffix = f"issues/{request.number}"
                    locator = _github_url(
                        request.owner,
                        request.repo,
                        f"issues/{request.number}",
                    )
                else:
                    suffix = f"pulls/{request.number}"
                    locator = _github_url(
                        request.owner,
                        request.repo,
                        f"pull/{request.number}",
                    )
                url = _api_url(request.owner, request.repo, suffix)
                _, payload, limit = self._single_json(url)
                content = _canonical_json(payload)
                api_urls.append(url)
                rate_limits.append(limit)
                pages = 1
            else:
                raise ValueError(f"Unsupported GitHub resource kind: {request.kind}")
        except _GitHubUnavailable as exc:
            return GitHubResearchResult(
                status=ResearchStatus.UNAVAILABLE,
                artifact=None,
                reason=exc.reason,
                pages=0,
                rate_limits=(_rate_limit(exc.response),),
            )
        except _GitHubContentUnavailable as exc:
            return GitHubResearchResult(
                status=ResearchStatus.UNAVAILABLE,
                artifact=None,
                reason=exc.reason,
                exact_commit_sha=exact_commit_sha,
                pages=pages,
                rate_limits=tuple(rate_limits),
            )

        metadata: dict[str, Any] = {
            "github_schema_version": 1,
            "owner": request.owner,
            "repo": request.repo,
            "resource_kind": request.kind.value,
            "api_urls": api_urls,
            "api_version": GITHUB_API_VERSION,
            "pages": pages,
            "pagination_truncated": truncated,
            "rate_limits": [limit.to_dict() for limit in rate_limits],
            "exact_commit_sha": exact_commit_sha,
        }
        source = ResearchSource(
            kind=ResearchSourceKind.GITHUB,
            locator=locator,
            status=ResearchStatus.READY,
            publisher="GitHub",
            title=f"{request.owner}/{request.repo} {request.kind.value}",
        )
        candidate = ResearchArtifact.from_content(
            source=source,
            content=content,
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
        return GitHubResearchResult(
            status=ResearchStatus.READY,
            artifact=artifact,
            exact_commit_sha=exact_commit_sha,
            pages=pages,
            pagination_truncated=truncated,
            rate_limits=tuple(rate_limits),
        )


class _GitHubUnavailable(Exception):
    def __init__(self, reason: str, response: RawWebResponse) -> None:
        super().__init__(reason)
        self.reason = reason
        self.response = response


class _GitHubContentUnavailable(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason
