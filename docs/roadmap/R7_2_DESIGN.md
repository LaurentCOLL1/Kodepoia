# R7.2 — Local + official documentation research — Design

**Status:** IN PROGRESS  
**Manual intervention:** NONE  
**Branch point:** `69249993cf9a2a45c1d3f89f0540e6f37c882929`  
**Depends on:** R7.1 COMPLETE

## Objective

Provide deterministic, offline-first research over project/local documentation and explicitly configured local snapshots of official documentation. R7.2 must preserve exact source provenance, line/section citations, content hashes and version/freshness state without introducing the general Web transport reserved for R7.3.

## Supported local formats

R7.2 supports UTF-8:

- `.txt`;
- `.md` / `.markdown`;
- `.json` with parse validation;
- `.yaml` / `.yml` with safe YAML parse validation.

Unsupported formats, including PDF/OCR in this subdivision, return explicit `UNAVAILABLE` instead of guessed extraction. No new parser/OCR dependency is added.

## Local adapter

`LocalDocumentAdapter`:

- resolves every source path through the existing project `WorkspaceBoundary`;
- rejects absolute paths, `..` escapes and existing symlinks resolving outside the project;
- requires an initialized `.kodepoia/` project when cache persistence is requested;
- enforces a bounded maximum source byte size before reading;
- decodes UTF-8 strictly;
- validates JSON/YAML syntax while preserving the exact original text as evidence;
- creates an R7.1 `ResearchArtifact` and persists it through `ResearchStore`;
- reuses an existing content-addressed artifact when the exact artifact ID is already cached;
- chunks evidence with deterministic 1-based line anchors and Markdown heading labels.

Local locators use stable `project:///<relative-posix-path>` identities and never expose an absolute host path in persisted research evidence.

## Official documentation manifest

`OfficialDocsManifest` is a versioned YAML/JSON-compatible contract describing local snapshots of authoritative documentation. Each entry contains:

- stable key;
- local snapshot root relative to the project;
- canonical HTTPS base URL;
- publisher;
- product;
- optional exact version.

Manifest validation rejects duplicate keys, absolute/escaping local roots, non-HTTPS canonical bases, URL credentials, query/fragment-bearing base URLs and missing hosts. The manifest is configuration/provenance only: it does not authorize network access.

`OfficialDocsAdapter` resolves requested snapshot files through a second `WorkspaceBoundary` rooted at the configured snapshot directory. Therefore a path or symlink may not escape the official snapshot root even if its target remains elsewhere inside the wider project.

Canonical official locators are reconstructed from the manifest HTTPS base plus the normalized relative snapshot path. This is provenance; R7.2 never performs an HTTP request.

## Chunking and citations

`DocumentChunk` carries:

- artifact ID;
- deterministic chunk ID;
- exact content;
- 1-based `line_start` / `line_end`;
- current Markdown heading label when available;
- `ResearchCitation` reconstructed as `L<start>`–`L<end>` against the source locator.

Chunks never rewrite the source artifact. Markdown headings are observed for labels only. Bounded line grouping is deterministic for the same source bytes and chunk size.

## Version/freshness semantics

R7.2 performs only exact version comparison; richer version inference is reserved for R7.8:

- local documents without a target/version relation: `NOT_APPLICABLE` freshness;
- official snapshot with missing source or target version: `UNKNOWN`;
- exact source version == target version: `CURRENT`;
- different non-empty exact strings: `STALE`, and source status is `STALE`.

Cache replay preserves the artifact's original `retrieved_at` and does not pretend the cache was freshly retrieved.

## Failure semantics

Unsupported extension, oversized document, invalid UTF-8, invalid JSON/YAML or missing regular file returns a `DocumentResearchResult` with explicit `UNAVAILABLE`, no artifact/chunks and a deterministic reason code/message. Workspace policy violations are not converted into `UNAVAILABLE`; they propagate as `WorkspaceViolation` so security denial remains distinguishable from format availability.

## Acceptance gates

R7.2 is accepted only if exact-head CI proves:

1. supported formats become guarded artifacts;
2. unsupported/invalid formats are explicit `UNAVAILABLE`;
3. absolute, traversal and symlink escapes are rejected;
4. official snapshot paths cannot escape their manifest root;
5. official canonical locators never trigger network access;
6. exact Markdown line anchors and heading labels reconstruct correctly;
7. exact-content second reads report cache reuse and preserve original retrieval timestamp;
8. source version mismatch becomes `STALE`, missing version evidence stays `UNKNOWN`;
9. manifest schema and runtime validation agree on valid/invalid fixtures;
10. R0, Python Core and KodeStudio UI Smoke are SUCCESS on the exact implementation head;
11. manual intervention remains NONE.

## Rollback

Remove the R7.2 document adapters/manifest schema/tests/design. Cached R7.2 artifacts under `.kodepoia/research/` are content-addressed inert research data and may be deleted without modifying source documentation. R7.1 contracts/store remain intact.
