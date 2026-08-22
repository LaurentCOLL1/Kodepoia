from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit

from kodepoia.intelligence.research.contracts import (
    ResearchArtifact,
    ResearchFreshness,
    ResearchSource,
    ResearchSourceKind,
    ResearchStatus,
)
from kodepoia.intelligence.research.store import ResearchStore
from kodepoia.intelligence.research.web import (
    RawWebResponse,
    WebPolicy,
    WebPolicyViolation,
    _decode_body,
    _mime_and_charset,
    validate_raw_web_response,
)


def _canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    )


def _digest(payload: Any) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _timestamp(value: str, field_name: str) -> str:
    raw = value.strip()
    if not raw:
        return ""
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone")
    return raw


class CommunityPostState(StrEnum):
    VISIBLE = "visible"
    EDITED = "edited"
    DELETED = "deleted"
    REMOVED = "removed"
    UNKNOWN = "unknown"


class CommunityAuthorRole(StrEnum):
    COMMUNITY = "community"
    MODERATOR = "moderator"
    VENDOR_STAFF = "vendor_staff"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class CommunityQuote:
    text: str
    cite: str = ""
    source_post_id: str = ""
    source_author: str = ""
    depth: int = 1
    quote_id: str = field(init=False)

    def __post_init__(self) -> None:
        text = " ".join(self.text.split())
        if not text:
            raise ValueError("Community quote text must not be empty")
        if self.depth < 1:
            raise ValueError("Community quote depth must be positive")
        object.__setattr__(self, "text", text)
        object.__setattr__(
            self,
            "quote_id",
            _digest(
                {
                    "text": text,
                    "cite": self.cite.strip(),
                    "source_post_id": self.source_post_id.strip(),
                    "source_author": self.source_author.strip(),
                    "depth": self.depth,
                }
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "quote_id": self.quote_id,
            "text": self.text,
            "cite": self.cite,
            "source_post_id": self.source_post_id,
            "source_author": self.source_author,
            "depth": self.depth,
        }


@dataclass(frozen=True, slots=True)
class CommunityPost:
    post_id: str
    author: str
    body: str
    state: CommunityPostState = CommunityPostState.VISIBLE
    role: CommunityAuthorRole = CommunityAuthorRole.COMMUNITY
    display_name: str = ""
    created_at: str = ""
    updated_at: str = ""
    parent_post_id: str = ""
    permalink: str = ""
    quotes: tuple[CommunityQuote, ...] = ()
    score: int | None = None
    reaction_count: int | None = None
    evidence_id: str = field(init=False)

    def __post_init__(self) -> None:
        post_id = self.post_id.strip()
        if not post_id:
            raise ValueError("Community post ID must not be empty")
        body = "\n".join(line.rstrip() for line in self.body.strip().splitlines()).strip()
        if self.state in {CommunityPostState.DELETED, CommunityPostState.REMOVED}:
            body = ""
        elif not body and self.state is CommunityPostState.VISIBLE:
            raise ValueError("Visible community post must contain author text")
        created = _timestamp(self.created_at, "created_at")
        updated = _timestamp(self.updated_at, "updated_at")
        if self.score is not None and not isinstance(self.score, int):
            raise TypeError("Community score must be an integer when present")
        if self.reaction_count is not None and self.reaction_count < 0:
            raise ValueError("Community reaction count cannot be negative")
        object.__setattr__(self, "post_id", post_id)
        object.__setattr__(self, "body", body)
        object.__setattr__(self, "created_at", created)
        object.__setattr__(self, "updated_at", updated)
        object.__setattr__(
            self,
            "evidence_id",
            _digest(
                {
                    "post_id": post_id,
                    "author": self.author.strip(),
                    "display_name": self.display_name.strip(),
                    "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
                    "state": self.state.value,
                    "role": self.role.value,
                    "created_at": created,
                    "updated_at": updated,
                    "parent_post_id": self.parent_post_id.strip(),
                    "permalink": self.permalink.strip(),
                    "quotes": [quote.to_dict() for quote in self.quotes],
                    "score": self.score,
                    "reaction_count": self.reaction_count,
                }
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "post_id": self.post_id,
            "author": self.author,
            "display_name": self.display_name,
            "body": self.body,
            "state": self.state.value,
            "role": self.role.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "parent_post_id": self.parent_post_id,
            "permalink": self.permalink,
            "quotes": [quote.to_dict() for quote in self.quotes],
            "score": self.score,
            "reaction_count": self.reaction_count,
        }


@dataclass(frozen=True, slots=True)
class CommunityThread:
    source_url: str
    retrieved_at: str
    posts: tuple[CommunityPost, ...]
    title: str = ""
    platform: str = ""
    thread_id: str = field(init=False)

    def __post_init__(self) -> None:
        if not self.source_url.strip():
            raise ValueError("Community source URL must not be empty")
        _timestamp(self.retrieved_at, "retrieved_at")
        if not self.posts:
            raise ValueError("Community thread requires at least one normalized post")
        post_ids = [post.post_id for post in self.posts]
        if len(post_ids) != len(set(post_ids)):
            raise ValueError("Community post IDs must be unique within a thread")
        known = set(post_ids)
        for post in self.posts:
            if post.parent_post_id and post.parent_post_id not in known:
                raise ValueError("Community parent post ID must reference a post in the thread")
            if post.parent_post_id == post.post_id:
                raise ValueError("Community post cannot parent itself")
        object.__setattr__(
            self,
            "thread_id",
            _digest(
                {
                    "source_url": self.source_url.strip(),
                    "posts": [post.to_dict() for post in self.posts],
                }
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "thread_id": self.thread_id,
            "source_url": self.source_url,
            "retrieved_at": self.retrieved_at,
            "title": self.title,
            "platform": self.platform,
            "authority_class": "community",
            "posts": [post.to_dict() for post in self.posts],
        }


@dataclass(frozen=True, slots=True)
class CommunityResearchResult:
    status: ResearchStatus
    artifact: ResearchArtifact | None
    thread: CommunityThread | None
    reason: str = ""

    def __post_init__(self) -> None:
        if self.status is ResearchStatus.READY and (self.artifact is None or self.thread is None):
            raise ValueError("Ready community research requires artifact and thread")
        if self.artifact is None and self.thread is not None:
            raise ValueError("Community thread cannot be returned without an artifact")


@dataclass
class _QuoteFrame:
    cite: str
    source_post_id: str
    source_author: str
    depth: int
    parts: list[str] = field(default_factory=list)


@dataclass
class _PostFrame:
    post_id: str
    author: str
    display_name: str
    state: CommunityPostState
    role: CommunityAuthorRole
    parent_post_id: str
    permalink: str
    score: int | None
    reaction_count: int | None
    body_parts: list[str] = field(default_factory=list)
    quotes: list[CommunityQuote] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


class _CommunityHTMLParser(HTMLParser):
    _IGNORED = {"script", "style", "noscript", "template"}

    def __init__(self, source_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.source_url = source_url
        self.title_parts: list[str] = []
        self.posts: list[CommunityPost] = []
        self._ignored_depth = 0
        self._title_depth = 0
        self._article_depth = 0
        self._post: _PostFrame | None = None
        self._quotes: list[_QuoteFrame] = []

    @staticmethod
    def _integer(value: str) -> int | None:
        if not value.strip():
            return None
        try:
            return int(value)
        except ValueError:
            return None

    @staticmethod
    def _state(value: str) -> CommunityPostState:
        try:
            return CommunityPostState(value.strip().lower() or "visible")
        except ValueError:
            return CommunityPostState.UNKNOWN

    @staticmethod
    def _role(value: str) -> CommunityAuthorRole:
        try:
            return CommunityAuthorRole(value.strip().lower() or "community")
        except ValueError:
            return CommunityAuthorRole.UNKNOWN

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        attributes = {key.lower(): (value or "") for key, value in attrs}
        if lowered in self._IGNORED:
            self._ignored_depth += 1
            return
        if self._ignored_depth:
            return
        if lowered in {"h1", "title"} and self._post is None:
            self._title_depth += 1

        if lowered == "article":
            if self._post is None:
                post_id = attributes.get("data-post-id", "").strip() or attributes.get("id", "").strip()
                if not post_id:
                    post_id = f"post-{len(self.posts) + 1}"
                permalink = attributes.get("data-permalink", "").strip()
                if permalink:
                    permalink = urljoin(self.source_url, permalink)
                self._post = _PostFrame(
                    post_id=post_id,
                    author=attributes.get("data-author", "").strip(),
                    display_name=attributes.get("data-display-name", "").strip(),
                    state=self._state(attributes.get("data-state", "visible")),
                    role=self._role(attributes.get("data-role", "community")),
                    parent_post_id=attributes.get("data-parent-id", "").strip(),
                    permalink=permalink,
                    score=self._integer(attributes.get("data-score", "")),
                    reaction_count=self._integer(attributes.get("data-reactions", "")),
                )
                self._article_depth = 1
            else:
                self._article_depth += 1
            return

        if self._post is None:
            return

        if lowered == "blockquote":
            self._quotes.append(
                _QuoteFrame(
                    cite=attributes.get("cite", "").strip(),
                    source_post_id=attributes.get("data-source-post-id", "").strip(),
                    source_author=attributes.get("data-source-author", "").strip(),
                    depth=len(self._quotes) + 1,
                )
            )
            return

        if lowered == "time":
            value = attributes.get("datetime", "").strip()
            kind = attributes.get("data-kind", "created").strip().lower()
            if value:
                if kind == "updated":
                    self._post.updated_at = value
                else:
                    self._post.created_at = value

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered in self._IGNORED:
            if self._ignored_depth:
                self._ignored_depth -= 1
            return
        if self._ignored_depth:
            return
        if lowered in {"h1", "title"} and self._post is None and self._title_depth:
            self._title_depth -= 1
        if lowered == "blockquote" and self._post is not None and self._quotes:
            frame = self._quotes.pop()
            text = " ".join(" ".join(frame.parts).split())
            if text:
                self._post.quotes.append(
                    CommunityQuote(
                        text=text,
                        cite=frame.cite,
                        source_post_id=frame.source_post_id,
                        source_author=frame.source_author,
                        depth=frame.depth,
                    )
                )
            return
        if lowered == "article" and self._post is not None:
            self._article_depth -= 1
            if self._article_depth == 0:
                frame = self._post
                self._post = None
                body = " ".join(" ".join(frame.body_parts).split())
                self.posts.append(
                    CommunityPost(
                        post_id=frame.post_id,
                        author=frame.author,
                        display_name=frame.display_name,
                        body=body,
                        state=frame.state,
                        role=frame.role,
                        created_at=frame.created_at,
                        updated_at=frame.updated_at,
                        parent_post_id=frame.parent_post_id,
                        permalink=frame.permalink,
                        quotes=tuple(frame.quotes),
                        score=frame.score,
                        reaction_count=frame.reaction_count,
                    )
                )

    def handle_data(self, data: str) -> None:
        if self._ignored_depth or not data.strip():
            return
        if self._post is None:
            if self._title_depth:
                self.title_parts.append(data)
            return
        if self._quotes:
            # Quote text belongs only to the innermost quotation. This avoids
            # duplicating nested quoted material into the parent quote.
            self._quotes[-1].parts.append(data)
        else:
            self._post.body_parts.append(data)

    @property
    def title(self) -> str:
        return " ".join(" ".join(self.title_parts).split())


def normalize_community_html(
    response: RawWebResponse,
    *,
    retrieved_at: str,
    policy: WebPolicy,
    platform: str = "",
) -> CommunityThread:
    validate_raw_web_response(response, policy=policy)
    mime, charset = _mime_and_charset(response.header("Content-Type"))
    if mime not in {"text/html", "application/xhtml+xml"}:
        raise WebPolicyViolation("Community normalization requires HTML/XHTML evidence")
    html = _decode_body(response.body, charset)
    parser = _CommunityHTMLParser(response.url)
    parser.feed(html)
    parser.close()
    if not parser.posts:
        raise ValueError("Community HTML did not contain semantic article posts")
    return CommunityThread(
        source_url=response.url,
        retrieved_at=retrieved_at,
        posts=tuple(parser.posts),
        title=parser.title,
        platform=platform.strip(),
    )


@dataclass(slots=True)
class CommunityResearchClient:
    project_root: Path
    policy: WebPolicy = field(default_factory=WebPolicy)
    _store: ResearchStore = field(init=False, repr=False)

    def __post_init__(self) -> None:
        root = Path(self.project_root).resolve(strict=False)
        self.project_root = root
        self._store = ResearchStore(root)

    def normalize(
        self,
        response: RawWebResponse,
        *,
        retrieved_at: str,
        platform: str = "",
        persist_cache: bool = True,
    ) -> CommunityResearchResult:
        try:
            thread = normalize_community_html(
                response,
                retrieved_at=retrieved_at,
                policy=self.policy,
                platform=platform,
            )
        except ValueError as exc:
            return CommunityResearchResult(
                status=ResearchStatus.UNAVAILABLE,
                artifact=None,
                thread=None,
                reason=str(exc),
            )

        hostname = (urlsplit(thread.source_url).hostname or "").lower()
        content = _canonical_json(thread.to_dict())
        source = ResearchSource(
            kind=ResearchSourceKind.COMMUNITY,
            locator=thread.source_url,
            status=ResearchStatus.READY,
            title=thread.title,
            publisher=hostname,
        )
        candidate = ResearchArtifact.from_content(
            source=source,
            content=content,
            retrieved_at=retrieved_at,
            freshness=ResearchFreshness.UNKNOWN,
            metadata={
                "community_schema_version": 1,
                "platform": thread.platform,
                "authority_class": "community",
                "post_count": len(thread.posts),
                "popularity_is_authority": False,
            },
        )
        artifact = candidate
        if persist_cache:
            if self._store.has_artifact(candidate.artifact_id):
                artifact = self._store.load_artifact(candidate.artifact_id)
            else:
                self._store.save_artifact(candidate)
        return CommunityResearchResult(
            status=ResearchStatus.READY,
            artifact=artifact,
            thread=thread,
        )
