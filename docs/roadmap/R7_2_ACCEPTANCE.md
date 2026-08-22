# R7.2 — Local + official documentation research — Acceptance

**Status:** COMPLETE / PASS  
**Accepted implementation head:** `9101e686a32b24bb33a23d7ac578bf25570e115e`  
**Implementation PR:** #62  
**Implementation merge:** `25741ab9c39300483b62eb2cc07b9d2c9fcfb20c`  
**Manual intervention:** NONE

## Accepted scope

R7.2 provides the offline-first local/official-document research layer required by the frozen R7 plan:

- UTF-8 local `.txt`, Markdown, JSON and YAML research;
- exact workspace-confined provenance through the existing `WorkspaceBoundary`;
- deterministic line/heading chunks and `ResearchCitation` reconstruction;
- content-addressed artifact cache reuse without rewriting the original retrieval timestamp;
- versioned official-document manifests describing local snapshots only;
- official snapshot confinement through a second `WorkspaceBoundary` rooted at the configured snapshot tree;
- exact `CURRENT` / `STALE` / `UNKNOWN` freshness semantics;
- explicit `UNAVAILABLE` results for unsupported/invalid formats;
- guarded external-like content remains data and never becomes agent instructions.

No general HTTP transport, browser, GitHub provider, community/forum provider, YouTube, STT/media or subprocess surface was introduced. Official HTTPS URLs are provenance only in R7.2.

## Exact-head hosted evidence

All final required gates ran against accepted head `9101e686a32b24bb33a23d7ac578bf25570e115e`:

- R0 Repository Guard — run #964 / `32585721455` — SUCCESS, Ubuntu + Windows;
- Python Core — run #938 / `32585721645` — SUCCESS, 5/5 jobs:
  - `python-core-windows-latest` — SUCCESS;
  - `python-core-ubuntu-latest` — SUCCESS;
  - `package-build-windows-latest` — SUCCESS;
  - `package-build-ubuntu-latest` — SUCCESS;
  - embedded `kodestudio-ui-windows` — SUCCESS;
- KodeStudio UI Smoke — run #905 / `32585721536` — SUCCESS.

PR #62 was merged only after those final exact-head gates succeeded, with `expected_head_sha=9101e686a32b24bb33a23d7ac578bf25570e115e`.

## Regression discovered and corrected during acceptance

The preceding candidate head `61eb6fbaf73066274249b3e490695bb0d4ff122c` was **not accepted**. Python Core #937 failed only on Windows because the manifest path validator did not classify the POSIX-rooted path `/absolute/docs` as absolute under Windows path semantics. The failing run reported `1 failed, 335 passed, 6 skipped` on Windows while Ubuntu passed.

The final implementation validates local snapshot roots against native `Path`, `PurePosixPath` and `PureWindowsPath` semantics. This ensures POSIX absolute roots, Windows drive/UNC-style absolute roots and parent traversal are rejected consistently on every supported host platform. The final exact-head CI then passed completely.

## Acceptance invariants

- supported local formats become guarded `ResearchArtifact` evidence;
- malformed JSON/YAML, invalid UTF-8, oversized and unsupported inputs remain explicit `UNAVAILABLE`;
- workspace and snapshot-root traversal/symlink escapes are policy violations, not silently downgraded to availability failures;
- canonical official HTTPS locators do not trigger network access;
- Markdown citations preserve deterministic 1-based line anchors and heading labels;
- exact-content cache reuse preserves original retrieval evidence;
- version mismatch is `STALE`; missing version relation is `UNKNOWN`;
- official-document manifest runtime validation and JSON Schema represent the same bounded offline configuration model;
- cross-platform absolute path validation is deterministic;
- no R7.3 network capability has leaked into R7.2.

## Rollback

R7.2 can be rolled back by removing the document adapters, manifest schema, focused tests and design/acceptance documentation. Content-addressed R7.2 artifacts under `.kodepoia/research/` are inert cached research data and may be deleted without modifying source documentation. R7.1 contracts and store remain independently valid.

## Decision

**PASS / COMPLETE.** R7.2 satisfies its frozen acceptance gates with manual intervention `NONE`. The next authorized subdivision after normalization is **R7.3 — Governed Web fetch + extraction**.