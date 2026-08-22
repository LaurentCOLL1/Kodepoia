# Kodepoia — R7.8 acceptance

**Subdivision:** R7.8 — Version-awareness + provenance/conflict model  
**Status:** COMPLETE  
**Accepted implementation head:** `deb5de415541004fb07bfbc6d955e9d76d717533`  
**Implementation PR:** #74  
**Implementation merge:** `f0de53379d6a8eb1883137946db4f2731cb9830a`  
**Manual:** NONE

## Exact-head CI evidence

All required hosted gates ran against exact implementation head `deb5de415541004fb07bfbc6d955e9d76d717533`:

- R0 Repository Guard #1001 / run `32595358745`: **SUCCESS**;
- Python Core #975 / run `32595358772`: **SUCCESS**, 5/5 jobs;
- authoritative Ubuntu suite: **460 passed / 4 skipped / 46 warnings**;
- Python Core Windows test job: **SUCCESS**;
- package-build Ubuntu: **SUCCESS**;
- package-build Windows: **SUCCESS**;
- embedded KodeStudio UI job: **SUCCESS**;
- KodeStudio UI Smoke #942 / run `32595358734`: **SUCCESS**.

Manual intervention was **NONE** and no conditional provider gate was triggered.

## Accepted capability

R7.8 adds a derived version/provenance layer without mutating R7.1–R7.7 artifacts or Project DNA:

- `VersionEvidenceKind`: `EXACT`, `RANGE`, `INFERRED`, `UNKNOWN`;
- explicit `VersionScheme`: `OPAQUE`, `SEMVER`, `PEP440`;
- structural `VersionInterval` instead of guessing arbitrary ecosystem range syntax;
- Project DNA engine/engine_version adapter that never silently infers the scheme or rewrites DNA;
- `VersionRelation`: exact/range/inferred match, mismatch, unknown;
- freshness assessment independent of version match;
- mutable/immutable/unknown source identity;
- explicit freshness evidence and revalidation requirements for mutable sources;
- versioned claims bound to finding/citation/source/version evidence;
- deterministic agreement/conflict/unresolved groups;
- explicit supersession links that do not erase contradictory claims;
- deterministic ranking inputs from explicit version relation, authority rank, freshness and mutability only;
- versioned JSON Schema and canonical SHA-256 IDs/report digest;
- fail-closed roundtrip and tamper detection.

## Accepted version semantics

### Exact / inferred

An inferred version requires evidence references and an inference reason. Even if its value equals the project target it remains `INFERRED_MATCH`; it is never promoted to `EXACT_MATCH`.

Project target constraints reject `INFERRED`. A target is exact/range only when explicit evidence exists; otherwise it remains unknown.

### SemVer

The SemVer path uses strict `major.minor.patch` parsing with prerelease/build components:

- exact identifier comparison retains build metadata as part of the exact stated identifier;
- ordered/range comparison follows SemVer precedence, where build metadata does not affect precedence;
- prerelease numeric and lexical precedence is preserved;
- malformed values are retained as source evidence but comparison returns `UNKNOWN` instead of inventing an ordering.

### PEP 440

R7.8 intentionally implements only conservative ordered comparison for simple numeric release segments (`N(.N)*`) with zero-padding semantics, so `1.0` and `1.0.0` compare equal. Rich pre/dev/post/local/epoch shapes are preserved but cross-value comparison remains `UNKNOWN` unless identity is directly defensible.

No new runtime packaging dependency was added and Kodepoia does not claim this conservative comparator implements all of PEP 440.

### Opaque

Opaque schemes support direct exact identity only. Distinct opaque values are a mismatch for an exact target, while ordering/range interpretation remains `UNKNOWN`.

## Freshness and source identity invariants

- version relation and freshness are separate axes;
- artifact/cache retrieval time cannot silently refresh a mutable source;
- mutable sources require explicit `validated_at` evidence for current/stale assessment;
- missing or future freshness evidence yields `UNKNOWN`;
- an immutable identity requires an immutable revision or snapshot digest;
- a mutable branch/forum page is not converted into an immutable source merely because a snapshot was cached;
- artifact-derived identities retain source/content digest provenance.

## Conflict and supersession invariants

- one visible claim for a key -> `UNRESOLVED`;
- multiple claims with the same visible value -> `AGREEMENT`;
- multiple distinct visible values -> `CONFLICT`;
- an explicit supersession link records older/newer claim IDs, reason and evidence refs;
- supersession never deletes the old claim and never converts distinct visible values into agreement;
- source-fact claims require citation evidence;
- source count, votes, reactions or popularity are not authority inputs.

## Ranking invariant

`rank_claims()` is presentation ordering, not truth arbitration. It returns every claim and uses only explicit fields: version relation, optional authority rank, freshness, source mutability and deterministic claim-ID tie-break.

Contradictory evidence remains available after ranking.

## Project DNA invariant

R7.8 consumes existing `ProjectDNA.engine` and `ProjectDNA.engine_version` only:

- explicit engine version -> exact target evidence;
- engine without version -> unknown target version;
- no engine -> no derived target constraint;
- caller supplies the version scheme explicitly;
- Project DNA is validated but not mutated.

## Persisted evidence / anti-tamper

`research-version-provenance-v1.schema.json` covers target, observations, identities, claims, supersession links, conflict groups and report digest.

`VersionProvenanceReport.from_dict()` recomputes canonical IDs, conflict groups and the final digest; mutated claims, missing observation/identity references, inconsistent groups or digest tampering fail closed.

## External reference context

Implementation/design were cross-checked with:

- Semantic Versioning 2.0.0 for strict version shape, prerelease precedence and build-metadata precedence behavior;
- the Python Packaging Authority version-specifier/PEP 440 interoperability specification, particularly release-segment zero padding and the existence of richer version syntax.

Those specifications are reference context. Kodepoia stores the chosen scheme explicitly and never assumes a universal versioning standard.

## Security / architecture review

R7.8 adds no network fetcher, subprocess, credential handling, arbitrary host/argv/cwd surface or UI. It consumes already accepted guarded evidence in memory. Existing ResearchGuard, WorkspaceBoundary, Guardian, ProcessSandbox, KillSwitch, Secrets and exact-head acceptance boundaries are unchanged.

No ADR was required because no frozen architecture foundation changed.

## Rollback

Remove `versioning.py`, its package exports, `research-version-provenance-v1.schema.json`, R7.8 tests and R7.8 documentation. Original Project DNA and R7.1–R7.7 artifacts/citations remain unchanged.
