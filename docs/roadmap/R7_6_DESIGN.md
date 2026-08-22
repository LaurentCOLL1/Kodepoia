# Kodepoia — R7.6 design

**Subdivision:** R7.6 — YouTube metadata + transcript ingestion  
**Architecture:** v1.0 frozen  
**Manual gate:** CONDITIONAL  
**Foundation change:** NONE

## Objective

Add provenance-preserving YouTube video metadata and transcript ingestion without inventing public caption access that the official API does not provide. Metadata retrieval and transcript acquisition are deliberately separate capabilities. R7.6 does not download or cache audiovisual media and does not add STT/frame extraction; those local-media hooks belong to R7.7.

## Official provider constraints used by this design

Current YouTube Data API documentation establishes the following provider behavior:

- `videos.list` is a read-only GET endpoint for video resources. R7.6 requests only `snippet,contentDetails` for an exact video ID; current documented quota cost is 1 unit.
- `captions.list` returns caption-track resources/metadata, **not the actual caption text**. The documented method requires authorization and currently costs 50 quota units.
- `captions.download` returns the caption track and supports output formats including WebVTT through `tfmt=vtt`; it requires OAuth authorization and the user to have permission to edit the video. Current documented quota cost is 200 units.
- Caption resources expose evidence such as `videoId`, `language`, `trackKind`, `lastUpdated`, `status`, `isDraft` and name. `trackKind` includes `ASR`, `forced` and `standard`.

Reference context:

- https://developers.google.com/youtube/v3/docs/videos/list
- https://developers.google.com/youtube/v3/docs/captions/list
- https://developers.google.com/youtube/v3/docs/captions/download
- https://developers.google.com/youtube/v3/docs/captions
- https://developers.google.com/youtube/v3/determine_quota_cost
- https://developers.google.com/youtube/terms/developer-policies

These references constrain implementation behavior only. Kodepoia does not infer a legal conclusion, certification or universal permission from them.

## Video locator contract

`YouTubeLocator` accepts only:

- an exact 11-character YouTube video ID;
- known HTTP(S) YouTube video URL shapes: `watch?v=`, `youtu.be`, `shorts/`, `embed/`, `live/`, mobile/music watch URLs, and `youtube-nocookie.com/embed/`.

The result is normalized to `https://www.youtube.com/watch?v=<video_id>`. Unrecognized hosts, channel/playlist URLs and invalid IDs fail rather than guessing. Transcript citations derive deterministic timestamp locators from the canonical video URL plus explicit millisecond anchors.

## Metadata provider

`YouTubeDataApiMetadataProvider` consumes a typed `YouTubeProviderTransport` and an optional API-key secret reference. The production `GuardedYouTubeApiTransport`:

- fixes the origin to `https://www.googleapis.com:443`;
- performs GET-only requests to fixed Data API endpoint paths;
- reuses R7.3 public-DNS validation and pinned-IP TLS connection behavior;
- requires existing Guardian `Capability.NETWORK` authorization before DNS/socket activity;
- resolves API keys through `KodeSecrets` only inside the transport;
- never exposes the key in model-facing requests, artifacts, evidence or Guardian target text;
- applies bounded timeout/response size and rejects compressed provider responses.

Metadata parsing verifies that the returned item ID exactly matches the requested video ID. Observed fields include title, description, channel ID/title, publication time, duration, languages and tags. Description timestamp markers such as `0:00 Intro` are retained as **description-observed markers**; R7.6 does not claim they are authoritative YouTube chapter objects.

## Transcript-provider separation

`YouTubeTranscriptProvider` is an explicit provider contract. A transcript is never inferred merely because a video exists.

Two implementations establish the R7.6 baseline:

1. `FixtureTranscriptProvider` — deterministic provider used by hosted CI and downstream adapters/tests. It proves the ingestion contract without requiring a real account or claiming a public transcript API.
2. `YouTubeAuthorizedCaptionProvider` — official Data API caption path for an OAuth-authorized context. It first calls `captions.list`, selects an accessible non-draft serving track, then calls `captions.download?tfmt=vtt`. If OAuth is absent or the provider returns 401/403, the result is explicit `BLOCKED`, never a fabricated transcript.

R7.6 intentionally does **not** implement scraping of undocumented caption endpoints, browser-login automation, cookie extraction, DRM/restriction bypass, or generic media/downloader helpers.

## Caption-track provenance

`YouTubeTranscriptTrack` records:

- exact video ID;
- language;
- normalized track kind: human / automatic / forced / unknown;
- provider identifier;
- provider caption ID when available;
- track name and last-updated evidence when available;
- ordered timestamped transcript segments;
- canonical track digest.

The authorized caption adapter maps documented `trackKind=ASR` to `automatic`, `standard` to `human`, `forced` to `forced`, and preserves unknown values as `unknown` rather than guessing.

## WebVTT ingestion

The bounded WebVTT parser preserves cue start/end times and visible text while:

- accepting optional cue identifiers;
- ignoring VTT NOTE/STYLE/REGION blocks as transcript speech;
- stripping markup tags and decoding entities;
- rejecting/ignoring malformed cue timestamps rather than fabricating timing;
- requiring non-empty text and positive cue duration.

Each accepted segment yields a `ResearchCitation` whose locator is the canonical YouTube timestamp URL and whose anchors are `ms:<start>` / `ms:<end>`.

## Trust boundary and persistence

Metadata and transcript payloads become distinct `ResearchArtifact` values with `ResearchSourceKind.YOUTUBE`. Every artifact is constructed through the existing R7.1 `ResearchGuard` so instruction-like transcript/description content remains external evidence, never agent instruction.

Persistent evidence uses the existing content-addressed `ResearchStore` under `.kodepoia/research/`. Metadata and transcript status are independent: for example, metadata may be `READY` while transcript is `UNAVAILABLE` or `BLOCKED`. `include_transcript=false` is explicit `NOT_APPLICABLE`. No absence is silently promoted to READY.

Freshness remains `UNKNOWN` in R7.6 because retrieval alone does not prove currentness. Cross-source/version/freshness reasoning remains R7.8.

## Audiovisual-media boundary

R7.6 fetches provider JSON and an authorized caption text file only. It does not retrieve video/audio streams, create offline playback, cache audiovisual copies, or invoke `yt-dlp`, ffmpeg, a browser, a subprocess, or arbitrary helper arguments. The YouTube API Developer Policies are treated as provider-policy context for keeping audiovisual download/storage out of this phase. Local STT and frame extraction, when explicitly designed and manually accepted, remain R7.7.

## Manual gate

R7.6 manual status is **CONDITIONAL**.

Normal acceptance does not trigger the manual gate because deterministic fixtures can prove:

- metadata parsing and exact video identity;
- transcript track/timing/language provenance;
- official-caption auth/permission fail-closed behavior;
- WebVTT parsing;
- ResearchGuard handling;
- schema/persistence/network-permission invariants.

The conditional gate is triggered only if acceptance explicitly requires a live authenticated YouTube caption download. Such a test must use an authorized account with edit permission for the target video, least-privilege credential handling through `KodeSecrets`, no credential persistence, and redacted evidence only.

## Machine schema

`schemas/youtube-research-v1.schema.json` constrains video IDs, canonical locator shape, independent metadata/transcript statuses, metadata fields, track kind, segment timestamps and canonical digest shapes. Schema validation supplements but does not replace runtime identity/hash invariants.

## Deterministic tests

R7.6 tests cover:

- accepted/rejected video-ID and URL shapes;
- description-marker extraction;
- exact metadata identity and blocked provider states;
- WebVTT timing/text normalization;
- human/automatic caption-kind mapping;
- preferred-language caption selection;
- OAuth absent/forbidden -> BLOCKED;
- metadata READY + transcript UNAVAILABLE independence;
- transcript NOT_APPLICABLE when not requested;
- hostile transcript text remains guarded data;
- timestamp citations and millisecond anchors;
- content-addressed cache behavior;
- JSON Schema acceptance/tamper rejection;
- production network permission denial before resolver/socket;
- absence of credential references from persisted evidence.

## Deliverables

- `src/kodepoia/intelligence/research/youtube.py`;
- public exports in `src/kodepoia/intelligence/research/__init__.py`;
- `schemas/youtube-research-v1.schema.json`;
- `tests/test_r7_6_youtube.py`;
- this design document;
- post-acceptance `R7_6_ACCEPTANCE.md`, R7 status and continuity synchronization.

## Acceptance

R7.6 is COMPLETE only after R0 Repository Guard, Python Core all jobs and KodeStudio UI Smoke are SUCCESS on the exact final implementation head, with the conditional manual gate either explicitly satisfied or explicitly not triggered.

## Rollback

Remove/disable the R7.6 YouTube adapter, exports, schema and tests; remove optional YouTube credential references without deleting unrelated secrets; optionally purge YouTube research cache artifacts. No video/account/provider state is mutated by the read-only design.
