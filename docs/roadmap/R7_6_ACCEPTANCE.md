# Kodepoia — R7.6 acceptance

**Subdivision:** R7.6 — YouTube metadata + transcript ingestion  
**Status:** COMPLETE  
**Accepted implementation head:** `b623836b8f5bd39fce101eca7fe4653a996a9562`  
**Implementation PR:** #70  
**Implementation merge:** `15216b59e14d692ff1e850812d572632bad5a88b`  
**Manual:** CONDITIONAL — NOT TRIGGERED

## Exact-head CI evidence

All required gates ran against exact implementation head `b623836b8f5bd39fce101eca7fe4653a996a9562`:

- R0 Repository Guard #980 / run `32590863193`: **SUCCESS**;
- Python Core #954 / run `32590863199`: **SUCCESS**, 5/5 jobs;
- authoritative Ubuntu suite: **432 passed / 3 skipped / 46 warnings**;
- Python Core Windows test job: **SUCCESS**;
- package-build Ubuntu: **SUCCESS**;
- package-build Windows: **SUCCESS**;
- embedded KodeStudio UI job: **SUCCESS**;
- KodeStudio UI Smoke #921 / run `32590863191`: **SUCCESS**.

No failed, missing, cancelled, skipped-required or fabricated evidence is accepted as PASS.

## Accepted capability

R7.6 provides:

- strict YouTube video ID and supported video-URL normalization;
- exact-ID video metadata ingestion through a fixed YouTube Data API provider;
- observed title/description/channel/publication/duration/language/tag metadata;
- description-observed timestamp markers without claiming official chapter authority;
- an explicit transcript-provider contract independent of video metadata availability;
- deterministic transcript fixtures for CI/provider integration;
- an official OAuth-authorized caption path using `captions.list` followed by `captions.download?tfmt=vtt`;
- explicit language, human/automatic/forced/unknown track kind, caption ID, provider and last-updated provenance;
- bounded WebVTT cue ingestion with exact millisecond start/end ranges;
- timestamped ResearchCitation values linking transcript segments to the canonical video URL;
- fixed `www.googleapis.com:443` production network origin with R7.3 public-target resolution, pinned-IP TLS and Guardian NETWORK authorization;
- API key/OAuth secret references resolved through KodeSecrets only inside the transport;
- independent metadata/transcript READY/UNAVAILABLE/BLOCKED/NOT_APPLICABLE states;
- content-addressed persistence through the existing ResearchStore;
- ResearchGuard wrapping for metadata and transcript artifacts;
- versioned `youtube-research-v1` JSON Schema.

## Provider-contract invariants accepted

1. R7.6 does not claim arbitrary public transcript download through the official YouTube Data API.
2. `captions.list` is treated as caption-track metadata only; caption text is a distinct download operation.
3. Official caption download without a configured OAuth reference is `BLOCKED`, not READY or silently skipped.
4. Provider 401/403 for caption list/download is explicit `BLOCKED` permission evidence.
5. Metadata availability does not imply transcript availability; metadata may be READY while transcript is UNAVAILABLE/BLOCKED.
6. `include_transcript=false` is explicit `NOT_APPLICABLE`.
7. Caption track `ASR` maps to automatic, `standard` to human, `forced` to forced, and unknown values remain unknown.
8. Transcript timing is preserved in milliseconds and citations preserve exact segment anchors.
9. Provider video identity must exactly match the requested video ID.
10. Description timestamps are recorded as description-observed markers only; they are not promoted into provider-certified chapter structures.

## Security / architecture invariants accepted

- production YouTube access is GET-only on fixed provider endpoints;
- no model-supplied arbitrary method, body, header, host, proxy, cookie or login action exists;
- Guardian NETWORK authorization occurs before DNS/socket activity;
- provider DNS must resolve to public addresses and the R7.3 pinned-address TLS model is reused;
- API key/OAuth secret values do not enter model-facing request objects, artifacts, persisted evidence or Guardian target strings;
- prompt-like transcript/description content remains external evidence and passes through ResearchGuard;
- no browser automation, undocumented caption endpoint scraping, DRM/restriction bypass or account automation is implemented;
- no video/audio stream download, offline playback, audiovisual cache, `yt-dlp`, ffmpeg or subprocess helper exists in R7.6;
- STT and frame/media fallback remains reserved for R7.7.

## External reference context

Implementation was cross-checked against the current official YouTube Data API documentation for `videos.list`, `captions.list`, `captions.download`, caption-resource fields/track kinds and quota costs, plus YouTube API Developer Policies. These references guide provider behavior only; Kodepoia makes no legal conclusion, certification or universal-permission claim.

## Manual gate

R7.6 manual status is **CONDITIONAL NOT TRIGGERED**. Deterministic hosted acceptance proves the provider/transcript ingestion contract and fail-closed auth behavior without a live OAuth credential. A future acceptance that explicitly requires live official-caption download would trigger the manual gate and must use an authorized account with edit permission for the target video, least-privilege credential handling through KodeSecrets, and redacted evidence only.

## Rollback

Rollback is repository-local: remove/disable the R7.6 YouTube adapter, exports, schema and tests; remove optional YouTube secret references without deleting unrelated secrets; optionally purge YouTube research cache artifacts. R7.6 performs no mutation of videos, captions, channels or provider account state.
