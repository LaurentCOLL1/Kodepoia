from __future__ import annotations

import hashlib
import html
import http.client
import json
import re
import socket
import ssl
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping, Protocol
from urllib.parse import parse_qs, urlencode, urlsplit

from kodepoia.core.guardian import ActionRequest, ActionType, DecisionKind, KodeGuardian
from kodepoia.core.secrets import KodeSecrets
from kodepoia.exceptions import PermissionDenied
from kodepoia.intelligence.research.contracts import (
    ResearchArtifact,
    ResearchCitation,
    ResearchFreshness,
    ResearchSource,
    ResearchSourceKind,
    ResearchStatus,
)
from kodepoia.intelligence.research.store import ResearchStore
from kodepoia.intelligence.research.web import (
    WebPolicy,
    WebTransportError,
    _PinnedHTTPSConnection,
    _default_resolver,
    resolve_public_target,
)

YOUTUBE_API_HOST = "www.googleapis.com"
YOUTUBE_CANONICAL_HOST = "www.youtube.com"
_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_CAPTION_ID_RE = re.compile(r"^[A-Za-z0-9_.-]{1,256}$")
_VTT_TAG_RE = re.compile(r"<[^>]+>")
_DESCRIPTION_MARKER_RE = re.compile(
    r"^\s*(?P<stamp>(?:\d{1,3}:)?\d{1,2}:\d{2})\s+(?P<title>\S.*)$"
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


def _require_timestamp(value: str, field_name: str) -> str:
    raw = value.strip()
    if not raw:
        raise ValueError(f"{field_name} must not be empty")
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone")
    return raw


def _optional_timestamp(value: str, field_name: str) -> str:
    return "" if not value.strip() else _require_timestamp(value, field_name)


class YouTubeProviderError(RuntimeError):
    """Base error for fixed YouTube provider access."""


class YouTubeCredentialUnavailable(YouTubeProviderError):
    """Raised when a configured provider credential reference cannot be resolved."""


class YouTubeProviderBlocked(YouTubeProviderError):
    """Raised when provider authorization/policy blocks the requested read."""


class TranscriptTrackKind(StrEnum):
    HUMAN = "human"
    AUTOMATIC = "automatic"
    FORCED = "forced"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class YouTubeCredentialRef:
    namespace: str
    key: str

    def __post_init__(self) -> None:
        if not self.namespace.strip() or not self.key.strip():
            raise ValueError("YouTube credential reference requires namespace and key")


@dataclass(frozen=True, slots=True)
class YouTubeLocator:
    video_id: str
    canonical_url: str = field(init=False)

    def __post_init__(self) -> None:
        if not _VIDEO_ID_RE.fullmatch(self.video_id):
            raise ValueError("Invalid YouTube video ID")
        object.__setattr__(
            self,
            "canonical_url",
            f"https://{YOUTUBE_CANONICAL_HOST}/watch?v={self.video_id}",
        )

    @classmethod
    def parse(cls, value: str) -> YouTubeLocator:
        raw = value.strip()
        if _VIDEO_ID_RE.fullmatch(raw):
            return cls(raw)
        parsed = urlsplit(raw)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
            raise ValueError("YouTube locator must be a video ID or HTTP(S) YouTube URL")
        host = parsed.hostname.lower().rstrip(".")
        video_id = ""
        if host in {"youtu.be", "www.youtu.be"}:
            video_id = parsed.path.strip("/").split("/", 1)[0]
        elif host in {
            "youtube.com",
            "www.youtube.com",
            "m.youtube.com",
            "music.youtube.com",
        }:
            parts = [part for part in parsed.path.split("/") if part]
            if parsed.path.rstrip("/") == "/watch":
                video_id = parse_qs(parsed.query).get("v", [""])[0]
            elif len(parts) >= 2 and parts[0] in {"shorts", "embed", "live"}:
                video_id = parts[1]
        elif host in {"youtube-nocookie.com", "www.youtube-nocookie.com"}:
            parts = [part for part in parsed.path.split("/") if part]
            if len(parts) >= 2 and parts[0] == "embed":
                video_id = parts[1]
        if not _VIDEO_ID_RE.fullmatch(video_id):
            raise ValueError("YouTube URL does not contain a valid video ID")
        return cls(video_id)

    def timestamp_url(self, start_ms: int) -> str:
        if start_ms < 0:
            raise ValueError("YouTube timestamp cannot be negative")
        return f"{self.canonical_url}&t={start_ms // 1000}s"


@dataclass(frozen=True, slots=True)
class YouTubeChapterMarker:
    start_ms: int
    title: str
    source: str = "description"
    marker_id: str = field(init=False)

    def __post_init__(self) -> None:
        if self.start_ms < 0:
            raise ValueError("Chapter marker timestamp cannot be negative")
        title = " ".join(self.title.split())
        if not title:
            raise ValueError("Chapter marker title must not be empty")
        object.__setattr__(self, "title", title)
        object.__setattr__(
            self,
            "marker_id",
            _digest({"start_ms": self.start_ms, "title": title, "source": self.source}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "marker_id": self.marker_id,
            "start_ms": self.start_ms,
            "title": self.title,
            "source": self.source,
        }


def _description_timestamp_ms(value: str) -> int:
    parts = value.split(":")
    if len(parts) not in {2, 3}:
        raise ValueError("Invalid description timestamp")
    numbers = [int(part) for part in parts]
    if len(parts) == 2:
        minutes, seconds = numbers
        if seconds >= 60:
            raise ValueError("Invalid description timestamp seconds")
        return (minutes * 60 + seconds) * 1000
    hours, minutes, seconds = numbers
    if minutes >= 60 or seconds >= 60:
        raise ValueError("Invalid description timestamp component")
    return (hours * 3600 + minutes * 60 + seconds) * 1000


def extract_description_markers(description: str) -> tuple[YouTubeChapterMarker, ...]:
    markers: list[YouTubeChapterMarker] = []
    previous = -1
    for line in description.splitlines():
        match = _DESCRIPTION_MARKER_RE.match(line)
        if not match:
            continue
        try:
            start_ms = _description_timestamp_ms(match.group("stamp"))
        except ValueError:
            continue
        if start_ms <= previous:
            continue
        markers.append(
            YouTubeChapterMarker(
                start_ms=start_ms,
                title=match.group("title"),
                source="description",
            )
        )
        previous = start_ms
    return tuple(markers)


@dataclass(frozen=True, slots=True)
class YouTubeVideoMetadata:
    video_id: str
    title: str
    description: str
    channel_id: str
    channel_title: str
    published_at: str
    duration: str = ""
    default_language: str = ""
    default_audio_language: str = ""
    tags: tuple[str, ...] = ()
    chapter_markers: tuple[YouTubeChapterMarker, ...] = ()
    metadata_id: str = field(init=False)

    def __post_init__(self) -> None:
        YouTubeLocator(self.video_id)
        published = _optional_timestamp(self.published_at, "published_at")
        object.__setattr__(self, "published_at", published)
        object.__setattr__(
            self,
            "metadata_id",
            _digest(
                {
                    "video_id": self.video_id,
                    "title": self.title,
                    "description": self.description,
                    "channel_id": self.channel_id,
                    "channel_title": self.channel_title,
                    "published_at": published,
                    "duration": self.duration,
                    "default_language": self.default_language,
                    "default_audio_language": self.default_audio_language,
                    "tags": list(self.tags),
                    "chapter_markers": [item.to_dict() for item in self.chapter_markers],
                }
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "metadata_id": self.metadata_id,
            "video_id": self.video_id,
            "title": self.title,
            "description": self.description,
            "channel_id": self.channel_id,
            "channel_title": self.channel_title,
            "published_at": self.published_at,
            "duration": self.duration,
            "default_language": self.default_language,
            "default_audio_language": self.default_audio_language,
            "tags": list(self.tags),
            "chapter_markers": [item.to_dict() for item in self.chapter_markers],
        }


@dataclass(frozen=True, slots=True)
class YouTubeTranscriptSegment:
    start_ms: int
    end_ms: int
    text: str
    segment_id: str = field(init=False)

    def __post_init__(self) -> None:
        if self.start_ms < 0 or self.end_ms <= self.start_ms:
            raise ValueError("Transcript segment time range is invalid")
        text = " ".join(self.text.split())
        if not text:
            raise ValueError("Transcript segment text must not be empty")
        object.__setattr__(self, "text", text)
        object.__setattr__(
            self,
            "segment_id",
            _digest({"start_ms": self.start_ms, "end_ms": self.end_ms, "text": text}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "text": self.text,
        }


@dataclass(frozen=True, slots=True)
class YouTubeTranscriptTrack:
    video_id: str
    language: str
    kind: TranscriptTrackKind
    provider: str
    segments: tuple[YouTubeTranscriptSegment, ...]
    caption_id: str = ""
    name: str = ""
    last_updated: str = ""
    track_id: str = field(init=False)

    def __post_init__(self) -> None:
        YouTubeLocator(self.video_id)
        if not self.language.strip():
            raise ValueError("Transcript track language must not be empty")
        if not self.provider.strip():
            raise ValueError("Transcript track provider must not be empty")
        if not self.segments:
            raise ValueError("Transcript track requires at least one segment")
        previous_start = -1
        for segment in self.segments:
            if segment.start_ms < previous_start:
                raise ValueError("Transcript segments must be ordered by start time")
            previous_start = segment.start_ms
        updated = _optional_timestamp(self.last_updated, "last_updated")
        object.__setattr__(self, "last_updated", updated)
        object.__setattr__(
            self,
            "track_id",
            _digest(
                {
                    "video_id": self.video_id,
                    "language": self.language,
                    "kind": self.kind.value,
                    "provider": self.provider,
                    "caption_id": self.caption_id,
                    "name": self.name,
                    "last_updated": updated,
                    "segments": [segment.to_dict() for segment in self.segments],
                }
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "track_id": self.track_id,
            "video_id": self.video_id,
            "language": self.language,
            "kind": self.kind.value,
            "provider": self.provider,
            "caption_id": self.caption_id,
            "name": self.name,
            "last_updated": self.last_updated,
            "segments": [segment.to_dict() for segment in self.segments],
        }


@dataclass(frozen=True, slots=True)
class YouTubeProviderResult:
    status: ResearchStatus
    metadata: YouTubeVideoMetadata | None = None
    transcript: YouTubeTranscriptTrack | None = None
    reason: str = ""

    def __post_init__(self) -> None:
        available = self.metadata is not None or self.transcript is not None
        if self.status is ResearchStatus.READY and not available:
            raise ValueError("Ready YouTube provider result requires evidence")
        if self.metadata is not None and self.transcript is not None:
            raise ValueError("YouTube provider result must contain one evidence type")


@dataclass(frozen=True, slots=True)
class YouTubeResearchResult:
    locator: YouTubeLocator
    metadata_status: ResearchStatus
    transcript_status: ResearchStatus
    metadata: YouTubeVideoMetadata | None = None
    transcript: YouTubeTranscriptTrack | None = None
    metadata_artifact: ResearchArtifact | None = None
    transcript_artifact: ResearchArtifact | None = None
    metadata_reason: str = ""
    transcript_reason: str = ""

    @property
    def transcript_citations(self) -> tuple[ResearchCitation, ...]:
        if self.transcript is None or self.transcript_artifact is None:
            return ()
        return tuple(
            ResearchCitation(
                artifact_id=self.transcript_artifact.artifact_id,
                locator=self.locator.timestamp_url(segment.start_ms),
                anchor_start=f"ms:{segment.start_ms}",
                anchor_end=f"ms:{segment.end_ms}",
                label=f"{self.transcript.language}/{self.transcript.kind.value}",
            )
            for segment in self.transcript.segments
        )

    def evidence_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "video_id": self.locator.video_id,
            "canonical_url": self.locator.canonical_url,
            "metadata_status": self.metadata_status.value,
            "transcript_status": self.transcript_status.value,
            "metadata": None if self.metadata is None else self.metadata.to_dict(),
            "transcript": None if self.transcript is None else self.transcript.to_dict(),
            "metadata_reason": self.metadata_reason,
            "transcript_reason": self.transcript_reason,
        }


@dataclass(frozen=True, slots=True)
class YouTubeApiResponse:
    status_code: int
    headers: Mapping[str, str]
    body: bytes

    def header(self, name: str) -> str:
        wanted = name.lower()
        for key, value in self.headers.items():
            if key.lower() == wanted:
                return str(value)
        return ""


class YouTubeProviderTransport(Protocol):
    def fetch_video(
        self,
        video_id: str,
        *,
        api_key_ref: YouTubeCredentialRef | None,
    ) -> YouTubeApiResponse: ...

    def list_captions(
        self,
        video_id: str,
        *,
        oauth_ref: YouTubeCredentialRef,
    ) -> YouTubeApiResponse: ...

    def download_caption_vtt(
        self,
        caption_id: str,
        *,
        oauth_ref: YouTubeCredentialRef,
    ) -> YouTubeApiResponse: ...


@dataclass(slots=True)
class FixtureYouTubeTransport:
    videos: dict[str, YouTubeApiResponse] = field(default_factory=dict)
    caption_lists: dict[str, YouTubeApiResponse] = field(default_factory=dict)
    captions: dict[str, YouTubeApiResponse] = field(default_factory=dict)
    requests: list[tuple[str, str]] = field(default_factory=list)

    def fetch_video(
        self,
        video_id: str,
        *,
        api_key_ref: YouTubeCredentialRef | None,
    ) -> YouTubeApiResponse:
        del api_key_ref
        self.requests.append(("videos.list", video_id))
        return self.videos.get(
            video_id,
            YouTubeApiResponse(404, {"Content-Type": "application/json"}, b"{}"),
        )

    def list_captions(
        self,
        video_id: str,
        *,
        oauth_ref: YouTubeCredentialRef,
    ) -> YouTubeApiResponse:
        del oauth_ref
        self.requests.append(("captions.list", video_id))
        return self.caption_lists.get(
            video_id,
            YouTubeApiResponse(404, {"Content-Type": "application/json"}, b"{}"),
        )

    def download_caption_vtt(
        self,
        caption_id: str,
        *,
        oauth_ref: YouTubeCredentialRef,
    ) -> YouTubeApiResponse:
        del oauth_ref
        self.requests.append(("captions.download", caption_id))
        return self.captions.get(
            caption_id,
            YouTubeApiResponse(404, {"Content-Type": "application/octet-stream"}, b""),
        )


@dataclass(slots=True)
class GuardedYouTubeApiTransport:
    guardian: KodeGuardian
    secrets: KodeSecrets
    policy: WebPolicy = field(
        default_factory=lambda: WebPolicy(
            allowed_ports=(443,),
            max_response_bytes=2 * 1024 * 1024,
            min_host_interval_seconds=0.0,
        )
    )
    resolver: Any = _default_resolver
    user_agent: str = "KodepoiaResearch/0.1"

    def _credential(self, reference: YouTubeCredentialRef, label: str) -> str:
        value = self.secrets.delegated_get(reference.namespace, reference.key)
        if not value:
            raise YouTubeCredentialUnavailable(f"YouTube {label} credential is unavailable")
        return value

    def _get(
        self,
        *,
        endpoint_label: str,
        path: str,
        params: dict[str, str],
        api_key_ref: YouTubeCredentialRef | None = None,
        oauth_ref: YouTubeCredentialRef | None = None,
        accept: str,
        max_bytes: int,
    ) -> YouTubeApiResponse:
        sanitized_target = f"https://{YOUTUBE_API_HOST}{path}"
        decision = self.guardian.authorize(
            ActionRequest(
                action=ActionType.NETWORK,
                actor="KodeResearch.YouTube",
                target=sanitized_target,
                metadata={"provider": "youtube", "endpoint": endpoint_label},
            )
        )
        if decision.kind is not DecisionKind.ALLOW:
            raise PermissionDenied(f"Guardian denied YouTube research: {decision.reason}")

        target = resolve_public_target(
            f"https://{YOUTUBE_API_HOST}/",
            policy=self.policy,
            resolver=self.resolver,
        )
        query = dict(params)
        if api_key_ref is not None:
            query["key"] = self._credential(api_key_ref, "API-key")
        headers = {
            "Host": YOUTUBE_API_HOST,
            "User-Agent": self.user_agent,
            "Accept": accept,
            "Accept-Encoding": "identity",
            "Connection": "close",
        }
        if oauth_ref is not None:
            headers["Authorization"] = f"Bearer {self._credential(oauth_ref, 'OAuth')}"
        request_path = path
        if query:
            request_path += "?" + urlencode(query)
        connection = _PinnedHTTPSConnection(
            target.address,
            server_hostname=YOUTUBE_API_HOST,
            port=443,
            timeout=self.policy.timeout_seconds,
            context=ssl.create_default_context(),
        )
        try:
            connection.request("GET", request_path, headers=headers)
            response = connection.getresponse()
            encoding = response.getheader("Content-Encoding", "").strip().lower()
            if encoding not in {"", "identity"}:
                raise YouTubeProviderError("Encoded YouTube API responses are not accepted")
            declared = response.getheader("Content-Length")
            if declared:
                try:
                    if int(declared) > max_bytes:
                        raise YouTubeProviderError("YouTube API response exceeds configured limit")
                except ValueError:
                    pass
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise YouTubeProviderError("YouTube API response exceeds configured byte limit")
            return YouTubeApiResponse(
                status_code=int(response.status),
                headers={key: value for key, value in response.getheaders()},
                body=body,
            )
        except (socket.timeout, TimeoutError) as exc:
            raise WebTransportError("YouTube API request timed out") from exc
        except (OSError, http.client.HTTPException, ssl.SSLError) as exc:
            raise WebTransportError(f"YouTube API request failed: {type(exc).__name__}") from exc
        finally:
            connection.close()

    def fetch_video(
        self,
        video_id: str,
        *,
        api_key_ref: YouTubeCredentialRef | None,
    ) -> YouTubeApiResponse:
        YouTubeLocator(video_id)
        if api_key_ref is None:
            raise YouTubeCredentialUnavailable("YouTube Data API key reference is required")
        return self._get(
            endpoint_label="videos.list",
            path="/youtube/v3/videos",
            params={"part": "snippet,contentDetails", "id": video_id},
            api_key_ref=api_key_ref,
            accept="application/json",
            max_bytes=min(self.policy.max_response_bytes, 1024 * 1024),
        )

    def list_captions(
        self,
        video_id: str,
        *,
        oauth_ref: YouTubeCredentialRef,
    ) -> YouTubeApiResponse:
        YouTubeLocator(video_id)
        return self._get(
            endpoint_label="captions.list",
            path="/youtube/v3/captions",
            params={"part": "id,snippet", "videoId": video_id},
            oauth_ref=oauth_ref,
            accept="application/json",
            max_bytes=min(self.policy.max_response_bytes, 1024 * 1024),
        )

    def download_caption_vtt(
        self,
        caption_id: str,
        *,
        oauth_ref: YouTubeCredentialRef,
    ) -> YouTubeApiResponse:
        if not _CAPTION_ID_RE.fullmatch(caption_id):
            raise ValueError("Invalid YouTube caption ID")
        return self._get(
            endpoint_label="captions.download",
            path=f"/youtube/v3/captions/{caption_id}",
            params={"tfmt": "vtt"},
            oauth_ref=oauth_ref,
            accept="text/vtt,application/octet-stream",
            max_bytes=min(self.policy.max_response_bytes, 2 * 1024 * 1024),
        )


def _json_response(response: YouTubeApiResponse) -> dict[str, Any]:
    content_type = response.header("Content-Type").split(";", 1)[0].strip().lower()
    if content_type not in {"application/json", "application/problem+json", ""}:
        raise YouTubeProviderError("YouTube API JSON endpoint returned an unexpected MIME type")
    try:
        payload = json.loads(response.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise YouTubeProviderError("YouTube API returned invalid UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise YouTubeProviderError("YouTube API response must be a JSON object")
    return payload


@dataclass(slots=True)
class YouTubeDataApiMetadataProvider:
    transport: YouTubeProviderTransport
    api_key_ref: YouTubeCredentialRef | None = None

    def fetch(self, video_id: str) -> YouTubeProviderResult:
        YouTubeLocator(video_id)
        try:
            response = self.transport.fetch_video(video_id, api_key_ref=self.api_key_ref)
        except YouTubeCredentialUnavailable as exc:
            return YouTubeProviderResult(ResearchStatus.BLOCKED, reason=str(exc))
        if response.status_code in {401, 403}:
            return YouTubeProviderResult(ResearchStatus.BLOCKED, reason="youtube_metadata_forbidden")
        if response.status_code == 404:
            return YouTubeProviderResult(ResearchStatus.UNAVAILABLE, reason="video_not_found")
        if not 200 <= response.status_code < 300:
            return YouTubeProviderResult(
                ResearchStatus.UNAVAILABLE,
                reason=f"youtube_metadata_http_{response.status_code}",
            )
        payload = _json_response(response)
        items = payload.get("items")
        if not isinstance(items, list) or not items:
            return YouTubeProviderResult(ResearchStatus.UNAVAILABLE, reason="video_not_found")
        item = items[0]
        if not isinstance(item, dict) or str(item.get("id", "")) != video_id:
            return YouTubeProviderResult(ResearchStatus.UNAVAILABLE, reason="video_identity_mismatch")
        snippet = item.get("snippet") if isinstance(item.get("snippet"), dict) else {}
        content_details = (
            item.get("contentDetails") if isinstance(item.get("contentDetails"), dict) else {}
        )
        description = str(snippet.get("description", ""))
        tags_raw = snippet.get("tags")
        tags = tuple(str(tag) for tag in tags_raw) if isinstance(tags_raw, list) else ()
        metadata = YouTubeVideoMetadata(
            video_id=video_id,
            title=str(snippet.get("title", "")),
            description=description,
            channel_id=str(snippet.get("channelId", "")),
            channel_title=str(snippet.get("channelTitle", "")),
            published_at=str(snippet.get("publishedAt", "")),
            duration=str(content_details.get("duration", "")),
            default_language=str(snippet.get("defaultLanguage", "")),
            default_audio_language=str(snippet.get("defaultAudioLanguage", "")),
            tags=tags,
            chapter_markers=extract_description_markers(description),
        )
        return YouTubeProviderResult(ResearchStatus.READY, metadata=metadata)


def _vtt_time_ms(value: str) -> int:
    raw = value.strip().replace(",", ".")
    parts = raw.split(":")
    if len(parts) == 2:
        hours = 0
        minute_text, second_text = parts
    elif len(parts) == 3:
        hour_text, minute_text, second_text = parts
        hours = int(hour_text)
    else:
        raise ValueError("Invalid WebVTT timestamp")
    minutes = int(minute_text)
    if "." in second_text:
        seconds_text, fraction = second_text.split(".", 1)
    else:
        seconds_text, fraction = second_text, "0"
    seconds = int(seconds_text)
    if minutes >= 60 or seconds >= 60:
        raise ValueError("Invalid WebVTT timestamp component")
    milliseconds = int((fraction + "000")[:3])
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + milliseconds


def parse_webvtt(content: str) -> tuple[YouTubeTranscriptSegment, ...]:
    normalized = content.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    lines = normalized.split("\n")
    index = 0
    if lines and lines[0].strip().startswith("WEBVTT"):
        index = 1
    segments: list[YouTubeTranscriptSegment] = []
    while index < len(lines):
        while index < len(lines) and not lines[index].strip():
            index += 1
        if index >= len(lines):
            break
        if lines[index].lstrip().startswith(("NOTE", "STYLE", "REGION")):
            index += 1
            while index < len(lines) and lines[index].strip():
                index += 1
            continue
        timing_index = index
        if "-->" not in lines[timing_index]:
            timing_index += 1
        if timing_index >= len(lines) or "-->" not in lines[timing_index]:
            index += 1
            continue
        timing = lines[timing_index]
        start_text, end_and_settings = timing.split("-->", 1)
        end_text = end_and_settings.strip().split()[0]
        try:
            start_ms = _vtt_time_ms(start_text)
            end_ms = _vtt_time_ms(end_text)
        except (ValueError, IndexError):
            index = timing_index + 1
            continue
        payload_lines: list[str] = []
        index = timing_index + 1
        while index < len(lines) and lines[index].strip():
            payload_lines.append(lines[index])
            index += 1
        text = html.unescape(_VTT_TAG_RE.sub("", " ".join(payload_lines)))
        text = " ".join(text.split())
        if text and end_ms > start_ms:
            segments.append(
                YouTubeTranscriptSegment(start_ms=start_ms, end_ms=end_ms, text=text)
            )
    return tuple(segments)


def _track_kind(value: str) -> TranscriptTrackKind:
    lowered = value.strip().lower()
    if lowered == "asr":
        return TranscriptTrackKind.AUTOMATIC
    if lowered == "standard":
        return TranscriptTrackKind.HUMAN
    if lowered == "forced":
        return TranscriptTrackKind.FORCED
    return TranscriptTrackKind.UNKNOWN


@dataclass(slots=True)
class YouTubeAuthorizedCaptionProvider:
    transport: YouTubeProviderTransport
    oauth_ref: YouTubeCredentialRef | None

    def fetch(
        self,
        video_id: str,
        *,
        preferred_languages: tuple[str, ...] = (),
    ) -> YouTubeProviderResult:
        YouTubeLocator(video_id)
        if self.oauth_ref is None:
            return YouTubeProviderResult(
                ResearchStatus.BLOCKED,
                reason="youtube_caption_oauth_required",
            )
        try:
            response = self.transport.list_captions(video_id, oauth_ref=self.oauth_ref)
        except YouTubeCredentialUnavailable as exc:
            return YouTubeProviderResult(ResearchStatus.BLOCKED, reason=str(exc))
        if response.status_code in {401, 403}:
            return YouTubeProviderResult(
                ResearchStatus.BLOCKED,
                reason="youtube_caption_permission_required",
            )
        if response.status_code == 404:
            return YouTubeProviderResult(ResearchStatus.UNAVAILABLE, reason="caption_not_found")
        if not 200 <= response.status_code < 300:
            return YouTubeProviderResult(
                ResearchStatus.UNAVAILABLE,
                reason=f"youtube_caption_list_http_{response.status_code}",
            )
        payload = _json_response(response)
        raw_items = payload.get("items")
        items = [item for item in raw_items if isinstance(item, dict)] if isinstance(raw_items, list) else []
        candidates: list[dict[str, Any]] = []
        for item in items:
            snippet = item.get("snippet") if isinstance(item.get("snippet"), dict) else {}
            if str(snippet.get("videoId", "")) != video_id:
                continue
            if bool(snippet.get("isDraft", False)):
                continue
            if str(snippet.get("status", "serving")) not in {"", "serving"}:
                continue
            caption_id = str(item.get("id", ""))
            if not _CAPTION_ID_RE.fullmatch(caption_id):
                continue
            candidates.append(item)
        if not candidates:
            return YouTubeProviderResult(ResearchStatus.UNAVAILABLE, reason="no_accessible_caption_track")

        preferred = [language.strip().lower() for language in preferred_languages if language.strip()]
        chosen = candidates[0]
        for language in preferred:
            match = next(
                (
                    item
                    for item in candidates
                    if str(item.get("snippet", {}).get("language", "")).lower() == language
                ),
                None,
            )
            if match is not None:
                chosen = match
                break
        snippet = chosen.get("snippet") if isinstance(chosen.get("snippet"), dict) else {}
        caption_id = str(chosen["id"])
        try:
            downloaded = self.transport.download_caption_vtt(caption_id, oauth_ref=self.oauth_ref)
        except YouTubeCredentialUnavailable as exc:
            return YouTubeProviderResult(ResearchStatus.BLOCKED, reason=str(exc))
        if downloaded.status_code in {401, 403}:
            return YouTubeProviderResult(
                ResearchStatus.BLOCKED,
                reason="youtube_caption_download_permission_required",
            )
        if downloaded.status_code == 404:
            return YouTubeProviderResult(ResearchStatus.UNAVAILABLE, reason="caption_not_found")
        if not 200 <= downloaded.status_code < 300:
            return YouTubeProviderResult(
                ResearchStatus.UNAVAILABLE,
                reason=f"youtube_caption_download_http_{downloaded.status_code}",
            )
        try:
            transcript_text = downloaded.body.decode("utf-8")
        except UnicodeDecodeError:
            return YouTubeProviderResult(ResearchStatus.UNAVAILABLE, reason="caption_invalid_utf8")
        segments = parse_webvtt(transcript_text)
        if not segments:
            return YouTubeProviderResult(ResearchStatus.UNAVAILABLE, reason="caption_empty_or_invalid_vtt")
        track = YouTubeTranscriptTrack(
            video_id=video_id,
            language=str(snippet.get("language", "und")) or "und",
            kind=_track_kind(str(snippet.get("trackKind", ""))),
            provider="youtube-data-api-authorized-captions",
            segments=segments,
            caption_id=caption_id,
            name=str(snippet.get("name", "")),
            last_updated=str(snippet.get("lastUpdated", "")),
        )
        return YouTubeProviderResult(ResearchStatus.READY, transcript=track)


@dataclass(slots=True)
class FixtureTranscriptProvider:
    tracks: dict[str, YouTubeTranscriptTrack] = field(default_factory=dict)
    blocked: set[str] = field(default_factory=set)

    def fetch(
        self,
        video_id: str,
        *,
        preferred_languages: tuple[str, ...] = (),
    ) -> YouTubeProviderResult:
        del preferred_languages
        YouTubeLocator(video_id)
        if video_id in self.blocked:
            return YouTubeProviderResult(ResearchStatus.BLOCKED, reason="fixture_transcript_blocked")
        track = self.tracks.get(video_id)
        if track is None:
            return YouTubeProviderResult(ResearchStatus.UNAVAILABLE, reason="transcript_unavailable")
        return YouTubeProviderResult(ResearchStatus.READY, transcript=track)


class YouTubeMetadataProvider(Protocol):
    def fetch(self, video_id: str) -> YouTubeProviderResult: ...


class YouTubeTranscriptProvider(Protocol):
    def fetch(
        self,
        video_id: str,
        *,
        preferred_languages: tuple[str, ...] = (),
    ) -> YouTubeProviderResult: ...


@dataclass(slots=True)
class YouTubeResearchClient:
    project_root: Path
    metadata_provider: YouTubeMetadataProvider
    transcript_provider: YouTubeTranscriptProvider | None = None
    _store: ResearchStore = field(init=False, repr=False)

    def __post_init__(self) -> None:
        root = Path(self.project_root).resolve(strict=False)
        self.project_root = root
        self._store = ResearchStore(root)

    def _persist(self, candidate: ResearchArtifact, enabled: bool) -> ResearchArtifact:
        if not enabled:
            return candidate
        if self._store.has_artifact(candidate.artifact_id):
            return self._store.load_artifact(candidate.artifact_id)
        self._store.save_artifact(candidate)
        return candidate

    def research(
        self,
        value: str,
        *,
        retrieved_at: str,
        preferred_languages: tuple[str, ...] = (),
        include_transcript: bool = True,
        persist_cache: bool = True,
    ) -> YouTubeResearchResult:
        stamp = _require_timestamp(retrieved_at, "retrieved_at")
        locator = YouTubeLocator.parse(value)
        metadata_result = self.metadata_provider.fetch(locator.video_id)
        metadata = metadata_result.metadata
        metadata_artifact: ResearchArtifact | None = None
        if metadata is not None:
            source = ResearchSource(
                kind=ResearchSourceKind.YOUTUBE,
                locator=locator.canonical_url,
                status=ResearchStatus.READY,
                title=metadata.title,
                publisher=metadata.channel_title,
                product="YouTube",
                published_at=metadata.published_at or None,
            )
            candidate = ResearchArtifact.from_content(
                source=source,
                content=_canonical_json(metadata.to_dict()),
                retrieved_at=stamp,
                freshness=ResearchFreshness.UNKNOWN,
                metadata={
                    "youtube_evidence_kind": "video_metadata",
                    "metadata_schema_version": 1,
                    "video_id": locator.video_id,
                },
            )
            metadata_artifact = self._persist(candidate, persist_cache)

        transcript_result = YouTubeProviderResult(
            ResearchStatus.NOT_APPLICABLE,
            reason="transcript_not_requested",
        )
        if include_transcript:
            if self.transcript_provider is None:
                transcript_result = YouTubeProviderResult(
                    ResearchStatus.UNAVAILABLE,
                    reason="transcript_provider_unconfigured",
                )
            else:
                transcript_result = self.transcript_provider.fetch(
                    locator.video_id,
                    preferred_languages=preferred_languages,
                )
        transcript = transcript_result.transcript
        transcript_artifact: ResearchArtifact | None = None
        if transcript is not None:
            source = ResearchSource(
                kind=ResearchSourceKind.YOUTUBE,
                locator=locator.canonical_url,
                status=ResearchStatus.READY,
                title=(metadata.title if metadata is not None else f"YouTube {locator.video_id}"),
                publisher=(metadata.channel_title if metadata is not None else "YouTube"),
                product="YouTube transcript",
            )
            candidate = ResearchArtifact.from_content(
                source=source,
                content=_canonical_json(transcript.to_dict()),
                retrieved_at=stamp,
                freshness=ResearchFreshness.UNKNOWN,
                metadata={
                    "youtube_evidence_kind": "transcript",
                    "transcript_schema_version": 1,
                    "video_id": locator.video_id,
                    "language": transcript.language,
                    "track_kind": transcript.kind.value,
                    "provider": transcript.provider,
                },
            )
            transcript_artifact = self._persist(candidate, persist_cache)

        return YouTubeResearchResult(
            locator=locator,
            metadata_status=metadata_result.status,
            transcript_status=transcript_result.status,
            metadata=metadata,
            transcript=transcript,
            metadata_artifact=metadata_artifact,
            transcript_artifact=transcript_artifact,
            metadata_reason=metadata_result.reason,
            transcript_reason=transcript_result.reason,
        )
