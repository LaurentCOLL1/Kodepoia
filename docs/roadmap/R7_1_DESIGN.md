# R7.1 — KodeResearch contracts + ResearchGuard hardening — Design

**Phase:** R7.1  
**Status:** IN PROGRESS  
**Manual intervention:** NONE  
**Branch point:** `7279412ae751bce739317763462c4a48d7832122`  
**Architecture:** v1.0 frozen; no ADR required

## Objective

Establish the typed, deterministic and tamper-evident KodeResearch domain before any live network/provider adapter exists. R7.1 adds only contracts, guarded ingestion, project-confined persistence, schemas and tests. It does **not** add HTTP, GitHub, forum, YouTube, STT, media, subprocess or UI execution.

## Frozen boundaries

- external/research content is data, never agent instruction;
- the existing `kodepoia.core.research_guard.ResearchGuard` remains the single content trust boundary;
- project persistence uses the existing `kodepoia.kodecode.workspace.WorkspaceBoundary`;
- no new command, argv, cwd, host, URL fetch or network surface exists in R7.1;
- `.kodepoia/research/` is the only project-local persistence root introduced here;
- serialized derived IDs/hashes/guard indicators are recomputed and checked instead of trusted;
- missing/non-applicable/stale/blocked states remain explicit.

## Domain model

### Source and state enums

`ResearchSourceKind` enumerates exactly the source classes frozen by R7: `local`, `official_docs`, `web`, `github`, `community`, `youtube`.

`ResearchStatus` uses `unknown`, `ready`, `unavailable`, `not_applicable`, `blocked`, `stale`. `ready` means an artifact is structurally available for research; it is not a truth, safety or quality PASS.

`ResearchFreshness` uses `unknown`, `current`, `stale`, `not_applicable`.

`ResearchTrust` uses `untrusted` and `guarded`. `guarded` means content has been passed through the deterministic ResearchGuard envelope; it never means the content is allowed to issue agent instructions.

`ResearchFindingKind` distinguishes `source_fact` from `inference`.

### Stable/canonical identities

IDs use SHA-256 over canonical JSON (`sort_keys=True`, compact separators, UTF-8):

- request ID: query + selected source kinds + project scope + result bound;
- source ID: source kind + exact locator;
- artifact ID: source ID + content SHA-256;
- citation ID: artifact ID + locator + anchor range/label;
- finding ID: kind + claim + citation IDs;
- report digest: canonical report payload excluding the stored digest itself.

Timestamps are validated as timezone-aware ISO-8601 but do not silently become evidence of publication/version freshness.

## Guarded ingestion

`ResearchArtifact.from_content()` runs the existing `ResearchGuard` and stores:

- the original content;
- content SHA-256;
- deterministic guard version;
- suspicious flag and indicators;
- the guard instruction stating the material is untrusted data.

`ResearchArtifact.from_dict()` reruns the current schema-v1 guard computation over the stored original content and rejects any serialized guard fields, content digest, source ID or artifact ID that do not match recomputed evidence. R7.1 therefore cannot launder malicious text by editing serialized `suspicious=false`.

The existing guard is hardened with a version constant plus targeted role-override/tool-bypass indicators. Existing indicators and API behavior are preserved.

## Persistence

`ResearchStore` mirrors accepted R6 store patterns:

- root resolved once through `WorkspaceBoundary`;
- initialized project requires an existing `.kodepoia/` directory;
- research data lives under `.kodepoia/research/`;
- request/artifact/report names are derived only from canonical hex IDs;
- JSON writes are deterministic and atomic via a sibling temporary file followed by `Path.replace()`;
- load operations reconstruct typed contracts and therefore repeat tamper checks.

No user-provided path is joined directly to the filesystem by the store API.

## Schemas

R7.1 adds Draft 2020-12 schemas:

- `research-request-v1.schema.json`;
- `research-artifact-v1.schema.json`;
- `research-report-v1.schema.json`.

Runtime dataclass validation remains authoritative; schemas provide interoperable/documented validation and CI coverage.

## Acceptance matrix

R7.1 is accepted only if all are true on the exact final implementation head:

1. request/source/artifact/citation/finding/report contracts round-trip;
2. derived IDs, SHA-256, report digest and guarded fields reject tampering;
3. timezone-naive timestamps are rejected;
4. citation references to absent artifacts are rejected;
5. ResearchGuard catches the accepted injection fixtures without turning content into commands;
6. project store rejects uninitialized projects and remains confined under `.kodepoia/research/`;
7. schemas validate accepted examples and reject structurally invalid examples;
8. no network/process/UI implementation is present in the R7.1 package;
9. full R0 Repository Guard, Python Core and KodeStudio UI Smoke succeed on the exact final head;
10. manual intervention remains `NONE`.

## Rollback

R7.1 has no migration or remote mutation. Rollback removes the new research package, R7.1 schemas/tests/docs and restores the previous `research_guard.py`. Any fixture-created `.kodepoia/research/` data can be deleted without changing user source files.
