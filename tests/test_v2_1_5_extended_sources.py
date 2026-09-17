from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from kodepoia.intelligence.research.community import CommunityResearchClient
from kodepoia.intelligence.research.contracts import ResearchStatus
from kodepoia.intelligence.research.evidence import EvidenceLifecycle
from kodepoia.intelligence.research.extended_sources import ExtendedSourceCoordinator
from kodepoia.intelligence.research.service import ResearchOperationStatus, ResearchViewItem
from kodepoia.intelligence.research.web import RawWebResponse
from kodepoia.intelligence.research.youtube import (
    TranscriptTrackKind,
    YouTubeProviderResult,
    YouTubeResearchClient,
    YouTubeTranscriptSegment,
    YouTubeTranscriptTrack,
    YouTubeVideoMetadata,
)

VIDEO_ID = "dQw4w9WgXcQ"
STAMP_1 = "2026-09-17T20:00:00Z"
STAMP_2 = "2026-09-17T20:05:00Z"


def _project(tmp_path: Path) -> Path:
    (tmp_path / ".kodepoia").mkdir()
    return tmp_path


@dataclass
class _MetadataProvider:
    title: str = "Research video"

    def fetch(self, video_id: str) -> YouTubeProviderResult:
        assert video_id == VIDEO_ID
        return YouTubeProviderResult(
            ResearchStatus.READY,
            metadata=YouTubeVideoMetadata(
                video_id=video_id,
                title=self.title,
                description="0:00 Intro\n0:04 Evidence",
                channel_id="channel-1",
                channel_title="Research Channel",
                published_at="2026-09-17T10:00:00Z",
            ),
        )


@dataclass
class _TranscriptProvider:
    text: str = "first transcript fact"
    available: bool = True

    def fetch(self, video_id: str, *, preferred_languages: tuple[str, ...] = ()) -> YouTubeProviderResult:
        assert video_id == VIDEO_ID
        del preferred_languages
        if not self.available:
            return YouTubeProviderResult(ResearchStatus.UNAVAILABLE, reason="transcript_unavailable")
        return YouTubeProviderResult(
            ResearchStatus.READY,
            transcript=YouTubeTranscriptTrack(
                video_id=video_id,
                language="en",
                kind=TranscriptTrackKind.HUMAN,
                provider="fixture-provider-caption",
                segments=(YouTubeTranscriptSegment(0, 4000, self.text),),
                caption_id="caption-1",
            ),
        )


def _youtube_coordinator(tmp_path: Path, transcript: _TranscriptProvider | None = None) -> ExtendedSourceCoordinator:
    root = _project(tmp_path)
    youtube = YouTubeResearchClient(
        root,
        metadata_provider=_MetadataProvider(),
        transcript_provider=transcript,
    )
    return ExtendedSourceCoordinator(root, youtube_client=youtube)


def test_youtube_search_descriptors_are_candidate_only() -> None:
    payload = {
        "items": [
            {
                "id": {"kind": "youtube#video", "videoId": VIDEO_ID},
                "snippet": {
                    "title": "Candidate video",
                    "description": "Descriptor only",
                    "channelId": "channel-1",
                    "channelTitle": "Research Channel",
                    "publishedAt": "2026-09-17T10:00:00Z",
                },
            },
            {"id": {"kind": "youtube#channel", "channelId": "channel-1"}, "snippet": {}},
        ]
    }
    items = ExtendedSourceCoordinator.youtube_search_candidates(payload)
    assert len(items) == 1
    item = items[0]
    assert item.source_kind == "youtube"
    assert item.trust == "candidate-only"
    assert item.freshness == "unfetched"
    assert item.artifact_id == ""
    assert item.reason.startswith("descriptor_only_not_fetched:youtube-search:")


def test_guarded_discovery_reclassifies_media_and_community_without_fetching() -> None:
    descriptors = (
        ResearchViewItem(
            source_kind="web",
            source_id="a" * 64,
            locator=f"https://www.youtube.com/watch?v={VIDEO_ID}",
            status=ResearchOperationStatus.READY,
            freshness="unfetched",
            trust="candidate-only",
            title="video",
        ),
        ResearchViewItem(
            source_kind="web",
            source_id="b" * 64,
            locator="https://www.reddit.com/r/example/comments/abc/thread/",
            status=ResearchOperationStatus.READY,
            freshness="unfetched",
            trust="candidate-only",
            title="thread",
        ),
    )
    result = ExtendedSourceCoordinator.classify_discovery(descriptors)
    assert [item.source_kind for item in result] == ["youtube", "community"]
    assert all(item.artifact_id == "" and item.trust == "candidate-only" for item in result)


def test_youtube_fetch_persists_metadata_transcript_and_revision_lineage(tmp_path: Path) -> None:
    transcript = _TranscriptProvider()
    coordinator = _youtube_coordinator(tmp_path, transcript)
    first = coordinator.fetch_youtube(VIDEO_ID, retrieved_at=STAMP_1)
    assert first.status is ResearchOperationStatus.READY
    assert len(first.items) == 2
    assert all(item.artifact_id and item.trust == "guarded" for item in first.items)
    assert first.metadata["transcript_authority"] == "provider-caption-only"
    assert first.metadata["stt_fallback_trusted"] is False
    assert first.metadata["frame_extraction_trusted"] is False

    transcript.text = "second transcript fact"
    second = coordinator.fetch_youtube(VIDEO_ID, retrieved_at=STAMP_2)
    assert second.status is ResearchOperationStatus.READY
    transcript_items = [item for item in first.items + second.items if item.reason == "fetched:youtube-transcript"]
    assert len({item.artifact_id for item in transcript_items}) == 2

    workspace = coordinator.workspace(first.items + second.items)
    youtube_rows = [row for row in workspace.rows if row.source_kind == "youtube"]
    assert youtube_rows
    assert all(row.lifecycle is EvidenceLifecycle.FETCHED for row in youtube_rows)
    assert max(len(row.lineage_revision_ids) for row in youtube_rows) >= 2


def test_unavailable_transcript_is_explicit_and_not_replaced_by_stt(tmp_path: Path) -> None:
    coordinator = _youtube_coordinator(tmp_path, transcript=None)
    result = coordinator.fetch_youtube(VIDEO_ID, retrieved_at=STAMP_1)
    assert result.status is ResearchOperationStatus.READY
    assert result.reason == "youtube_fetched_partial"
    assert result.metadata["transcript_status"] == "unavailable"
    assert result.metadata["transcript_reason"] == "transcript_provider_unconfigured"
    assert result.metadata["stt_fallback_trusted"] is False
    assert len(result.items) == 1


def test_community_thread_enters_same_store_with_parent_relationships(tmp_path: Path) -> None:
    root = _project(tmp_path)
    community = CommunityResearchClient(root)
    coordinator = ExtendedSourceCoordinator(root, community_client=community)
    body = b"""<!doctype html><html><head><title>Thread title</title></head><body>
    <article data-post-id='p1' data-author='alice' data-score='99'>
      <time datetime='2026-09-17T10:00:00Z'></time><p>Source fact one.</p>
    </article>
    <article data-post-id='p2' data-author='bob' data-parent-id='p1' data-reactions='5'>
      <time datetime='2026-09-17T10:02:00Z'></time><p>Reply fact.</p>
      <blockquote data-source-post-id='p1' data-source-author='alice'>Source fact one.</blockquote>
    </article>
    </body></html>"""
    response = RawWebResponse(
        url="https://forum.example.org/t/research/42",
        status_code=200,
        headers={"Content-Type": "text/html; charset=utf-8"},
        body=body,
    )
    result = coordinator.fetch_community(response, retrieved_at=STAMP_1, platform="fixture-forum")
    assert result.status is ResearchOperationStatus.READY
    assert result.metadata["typed_relationships"] is True
    assert result.metadata["popularity_is_authority"] is False
    assert result.metadata["post_count"] == 2
    assert len(result.items) == 1
    assert result.items[0].source_kind == "community"
    workspace = coordinator.workspace(result.items)
    assert workspace.rows[0].lifecycle is EvidenceLifecycle.FETCHED
    assert workspace.rows[0].artifact_id == result.items[0].artifact_id


def test_community_candidate_stays_unfetched_until_explicit_fetch() -> None:
    item = ExtendedSourceCoordinator.community_candidate(
        "https://www.reddit.com/r/example/comments/abc/thread/",
        title="Candidate thread",
    )
    assert item.source_kind == "community"
    assert item.artifact_id == ""
    assert item.trust == "candidate-only"
    assert item.freshness == "unfetched"
