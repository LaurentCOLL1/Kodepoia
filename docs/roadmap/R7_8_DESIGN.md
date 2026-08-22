# Kodepoia — R7.8 design

**Subdivision:** R7.8 — Version-awareness + provenance/conflict model  
**Manual:** NONE  
**Architecture:** v1.0 frozen; derived research layer only

## Objective

R7.8 makes accepted research evidence explicitly version-aware without rewriting the source artifacts produced by R7.1–R7.7. The layer records what version evidence actually exists, how it relates to the project target, whether a source identity is mutable, whether freshness is evidenced, and where claims agree, conflict or have an explicit supersession relationship.

R7.8 does not decide truth with an LLM, does not migrate/upgrade a project, does not hide contradictory evidence, and does not add network/process/UI behavior.

## Derived-layer boundary

R7.8 is intentionally additive and reversible:

- `ResearchArtifact`, `ResearchCitation`, `ResearchFinding` and Project DNA remain source evidence and are not mutated;
- R7.8 creates derived `VersionObservation`, `TargetVersionConstraint`, `SourceIdentity`, `VersionedClaim`, `SupersessionLink`, `ConflictGroup` and `VersionProvenanceReport` values;
- derived IDs and the report digest are canonical SHA-256 values and are recomputed on deserialization;
- rollback removes the derived version/provenance layer while leaving original artifacts/citations intact.

No ADR is required because no frozen architecture foundation is changed.

## Version evidence kinds

`VersionEvidenceKind` has four distinct states:

- `EXACT`: a source or project field directly states a scalar version;
- `RANGE`: evidence directly states a bounded interval represented structurally as `VersionInterval`;
- `INFERRED`: the version is derived from non-exact evidence and must retain both evidence references and an explicit inference reason;
- `UNKNOWN`: there is no defensible version claim.

An inferred observation is never promoted into `EXACT`, even when its inferred value happens to equal the target. It evaluates to `INFERRED_MATCH`, not `EXACT_MATCH`.

Target constraints deliberately reject `INFERRED`; Kodepoia must not silently infer what version a project targets.

## Version schemes are explicit evidence

R7.8 does not assume every product follows one versioning scheme. `VersionScheme` is explicit:

- `OPAQUE`: exact string identity only; ordering/range comparisons are UNKNOWN unless equality alone is sufficient;
- `SEMVER`: strict SemVer 2.0.0 shape and precedence rules;
- `PEP440`: conservative Python packaging support.

The scheme is supplied by the caller/provider policy; R7.8 never guesses it from punctuation or product name.

### SemVer behavior

For SemVer:

- exact identity compares all parsed components including build metadata;
- ordered/range comparison follows SemVer precedence, where build metadata does not affect precedence;
- prerelease identifiers follow SemVer numeric/lexical precedence;
- malformed/non-SemVer values remain evidence but comparisons return `UNKNOWN` rather than inventing an ordering.

This deliberately distinguishes identity from precedence: `1.2.3+build.1` and `1.2.3+build.2` have equal precedence but are not the same exact stated identifier.

### PEP 440 behavior

The current R7.8 implementation intentionally supports ordered comparison only for simple numeric release segments (`N(.N)*`) and uses PEP 440 zero-padding semantics, so `1.0` and `1.0.0` compare equal. More complex pre/dev/post/local/epoch shapes are preserved as source strings but return `UNKNOWN` for cross-value comparison unless raw normalized identity is sufficient.

This is conservative by design. R7.8 does not claim a home-grown partial parser is equivalent to the complete PEP 440 specification and introduces no new runtime packaging dependency in this subdivision.

## Project DNA target integration

`target_constraint_from_project_dna()` consumes existing Project DNA fields only:

- `engine` supplies product identity;
- an explicit non-empty `engine_version` becomes an `EXACT` target with evidence refs `project_dna:engine` and `project_dna:engine_version`;
- an engine with no version becomes `UNKNOWN`;
- no engine returns no target constraint.

The adapter validates Project DNA but does not modify it. The caller must explicitly provide the version scheme. This avoids silently interpreting `engine_version` under SemVer/PEP 440 when the engine may use another scheme.

## Version relationship is separate from freshness

`VersionRelation` is independent of `ResearchFreshness`:

- `EXACT_MATCH`
- `RANGE_MATCH`
- `INFERRED_MATCH`
- `MISMATCH`
- `UNKNOWN`

A source may be version-relevant but stale, or fresh but have unknown version evidence. Unknown version evidence never becomes an exact/current version match.

## Freshness evidence

Freshness never comes from merely reading a cache again.

`FreshnessEvidence` distinguishes source mutability:

- mutable source: current/stale assessment requires an explicit `validated_at` revalidation timestamp;
- immutable/unknown source identity: assessment uses explicit observed/updated evidence;
- missing timestamp evidence yields `UNKNOWN`;
- a future timestamp yields `UNKNOWN`;
- policy thresholds are explicit `FreshnessPolicy` values.

The existing `ResearchArtifact.retrieved_at` may be retained as provenance but is not silently substituted for mutable-source revalidation.

## Mutable and immutable source identity

`SourceIdentity` records:

- locator;
- `MUTABLE`, `IMMUTABLE` or `UNKNOWN`;
- optional existing source ID;
- immutable revision when known;
- content/snapshot SHA-256 when known;
- explicit evidence references.

An identity declared `IMMUTABLE` requires either revision evidence or a snapshot digest. A mutable Git branch/forum page cannot be treated as immutable merely because it was once cached.

## Claims, conflicts and supersession

`VersionedClaim` binds a claim to:

- the original finding identity/kind;
- a visible claim key/value;
- version observation;
- source identity;
- citation IDs;
- freshness;
- version relation;
- optional explicit authority rank.

Source-fact claims require citation evidence.

`ConflictGroup` is deterministic:

- one claim -> `UNRESOLVED`;
- multiple claims with the same visible value -> `AGREEMENT`;
- multiple claims with distinct visible values -> `CONFLICT`.

A `SupersessionLink` requires explicit evidence and a reason. It does **not** erase the older claim or convert a conflict into agreement. The conflict group retains both claims and references the supersession link.

## Ranking is not truth arbitration

`rank_claims()` is a deterministic presentation input only. It sorts all claims using explicit fields:

1. version relation;
2. explicit authority rank, when supplied;
3. freshness;
4. immutable/mutable identity;
5. deterministic claim ID tie-break.

It never deletes contradictory claims. There is no popularity, vote, reaction, source-count or LLM-confidence field that automatically manufactures authority.

## Persisted schema and anti-tamper behavior

`schemas/research-version-provenance-v1.schema.json` validates the serialized report surface. `VersionProvenanceReport.from_dict()` recomputes:

- observation/constraint/identity/claim/link/group IDs;
- conflict groups from visible claims and links;
- final canonical report digest.

Tampered claim values, IDs, links, groups or digest evidence fail closed.

## Network/process/security surface

R7.8 adds:

- no HTTP provider;
- no file crawler;
- no subprocess;
- no credential handling;
- no arbitrary model command/argv/cwd/host;
- no KodeStudio UI.

Existing ResearchGuard/WorkspaceBoundary/Guardian/ProcessSandbox boundaries remain unchanged because R7.8 consumes already accepted evidence in memory.

## Acceptance matrix

R7.8 acceptance must prove at minimum:

- exact/range/inferred/unknown survive round-trip distinctly;
- inferred never becomes exact;
- Project DNA exact and unknown targets are consumed without mutation;
- SemVer exact identity vs precedence/build metadata distinction;
- SemVer prerelease/range behavior and malformed input -> UNKNOWN;
- conservative PEP 440 simple-release zero-padding behavior;
- opaque versions never gain fabricated ordering;
- artifact with no version remains UNKNOWN even if artifact freshness is CURRENT;
- mutable freshness requires explicit revalidation evidence;
- future/missing freshness evidence -> UNKNOWN;
- immutable identity requires revision or digest evidence;
- old/new contradictory claims remain visible with supersession link;
- agreement and single-source unresolved states are explicit;
- ranking retains every contradictory claim and uses only explicit fields;
- source facts require citations;
- JSON Schema accepts canonical reports;
- round-trip preserves exact/inferred distinctions and digest;
- tampering/missing observation/missing identity references fail closed;
- R0 Repository Guard, Python Core and KodeStudio UI Smoke are SUCCESS on the exact final implementation head.

## External standard context

R7.8 was cross-checked against:

- Semantic Versioning 2.0.0 for strict SemVer identifier and precedence semantics, especially prerelease ordering and the rule that build metadata does not affect precedence;
- the current Python Packaging Authority version-specifier specification (PEP 440 interoperability specification), especially numeric release-segment comparison/zero-padding and the existence of richer pre/post/dev/local/epoch syntax.

These standards are reference context only. Kodepoia records the selected version scheme and does not assume all ecosystems are SemVer or PEP 440.

## Manual gate

**NONE.** Deterministic fixtures and exact-head hosted CI are sufficient for R7.8.

## Rollback

Remove `versioning.py`, its exports, schema, tests and R7.8 documentation. Original R7.1–R7.7 research artifacts/citations and Project DNA remain unchanged.
