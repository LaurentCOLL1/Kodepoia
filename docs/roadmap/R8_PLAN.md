# Kodepoia — R8 detailed phase plan

**Phase:** R8  
**Roadmap title:** Vault / AssetPipeline / VCS  
**Status:** PLANNING  
**Phase planning started:** 2026-08-22  
**Architecture:** v1.0 frozen  
**Source of truth at planning branch point:** normalized `main` `b98832b339902527bce8a5ea95b5a08a19839a40`

## Purpose and authority

R8 implements the frozen inter-project asset-management layer without changing Kodepoia's foundations. The phase covers a local-first Vault, asset identity and revisioning, reuse scope/preservation, duplicate and semantic discovery, explicit source-vs-derived lineage, reproducible transforms/cache/rebuild, and asset-aware Git/Git LFS integration.

This file is the exhaustive execution/recovery plan for R8. The R8.1–R8.11 subdivision structure becomes frozen when this plan is merged. No subdivision may be silently added, removed, merged, split or renumbered. Any scope change must update this plan and `docs/continuity/KODEPOIA_CONTINUITY.md` in the same work cycle; any foundation change requires an ADR.

R8.1 MUST NOT begin before this plan is merged to `main` with R0 Repository Guard, full Python Core and KodeStudio UI Smoke successful on the exact final planning head.

## Phase objective

Deliver a deterministic, auditable and reusable asset layer that lets multiple Kodepoia projects share source assets safely without losing provenance, license state, versions or project-local ownership. Derived assets must be reproducible from recorded source revisions and transform recipes. The system must detect exact and supported near-duplicates, provide semantic discovery using the accepted R3 embedding/retrieval boundary, and expose asset-aware VCS/LFS health without giving the model arbitrary filesystem, Git, shell or network control.

R8 must enable later phases to consume assets through stable contracts:

- R9 ComfyUI can produce derived 2D assets through registered transform/provider adapters;
- R10 Blender can produce derived 3D assets while preserving source/revision lineage;
- R11 audio/voice/cinematics can store source and generated media with the same provenance/rebuild rules;
- R12+ application/platform phases can reuse licensed UI/media assets without bypassing governance.

Out of scope for R8: ComfyUI workflow execution and VRAM scheduling (R9), Blender authoring/retarget/LOD generation (R10), audio/TTS/cinematics generation (R11), cloud object storage/synchronization, arbitrary remote asset marketplaces, package-manager replacement, general Git hosting administration, repository history rewriting, automatic license legal conclusions, and model fine-tuning.

## Permanent phase-wide architecture and governance boundaries

Every R8 subdivision must preserve all accepted R1–R7 boundaries:

- `WorkspaceBoundary` remains authoritative for project-local roots. R8 may create a dedicated Vault boundary only by composing the same path-confinement semantics around an explicitly configured local Vault root; it must not weaken or reinterpret `WorkspaceBoundary`.
- No implicit scan of arbitrary user directories, drives, home folders, network shares or repositories. Every source root and target root must be explicit and authorized.
- `ProcessSandbox` + global KillSwitch for every external executable (`git`, `git-lfs`, Godot import helpers or later registered transform tools).
- Guardian + `PermissionSet` authorization for mutations, external processes, network access and destructive operations.
- SafeChange snapshots, Backup/Recovery and AuditLog where durable Vault/index/VCS mutations require rollback.
- `KodeSecrets` only for optional credentials; no secret value in manifests, asset metadata, prompts, logs, cache keys or evidence.
- R6 Health/Budget/DataGovernance/AppSecurity/Privacy/License-BOM contracts remain in force.
- Structured Tool APIs only. No model-supplied arbitrary executable, argv, cwd, environment, refspec, remote URL, Git config key, filesystem path outside authorized roots, or network host.
- Versioned schemas for every persisted R8 manifest/index/export/evidence record.
- Explicit `UNKNOWN`, `N/A`, `UNAVAILABLE`, `BLOCKED`, `STALE`, `MISSING` and `CORRUPT` states where applicable. Missing bytes, metadata, LFS objects or embeddings never manufacture readiness.
- Exact SHA-256/content-length verification for immutable asset bytes and persisted evidence when identity depends on content.
- Source assets are never silently overwritten by derived outputs; cached/derived data is disposable only when rebuildability has been proven.
- Existing R7 external-content trust model remains unchanged: imported metadata/descriptions/license text are data/evidence, never agent instructions.
- ADR required if implementation would alter a frozen foundation rather than add an R8-scoped capability.

## Storage and trust model

R8 uses four distinct concepts and MUST keep them separate:

1. **Project asset reference** — project-local declaration that a project uses a specific Vault asset revision or local source asset.
2. **Vault metadata/revision** — immutable identity/provenance/reuse metadata for one revision.
3. **Vault object bytes** — content-addressed immutable bytes, verified by SHA-256 before acceptance.
4. **Derived/cache output** — result of a transform recipe, keyed by source identities + recipe/tool/config identity; it is not a new source unless explicitly promoted through a governed operation.

A Vault root is local storage explicitly configured by the user/application. It must be confined with boundary semantics equivalent to `WorkspaceBoundary`. Project code may hold references to Vault identities, but a project must remain portable: missing Vault content is represented explicitly and must be relinkable/exportable according to policy.

The canonical object layout planned for R8 is content-addressed, e.g. `objects/sha256/<prefix>/<digest>`, with versioned metadata/manifests and a transactional SQLite index under the Vault root. Exact physical paths are implementation details frozen in R8.1 schemas once accepted; callers use asset/revision IDs, not object paths.

## Asset identity and revision principles

- `AssetId` identifies a logical asset across revisions.
- `AssetRevisionId` identifies one immutable revision and is derived from canonical metadata plus verified content identity, not timestamps alone.
- `content_sha256` identifies exact bytes.
- Revisions are append-only. Replacing bytes creates a new revision.
- Metadata corrections that change canonical provenance/license/reuse semantics create a metadata revision or explicit supersession record; no in-place history erasure.
- Source and derived roles are explicit.
- Lineage edges record input revision(s), transform recipe identity, tool/provider version, deterministic settings, output digest and creation evidence.
- Friendly names/tags are mutable index metadata but never asset identity.

## Reuse scope and preservation policy

R8 must model reuse and preservation independently:

- reuse scope: `PROJECT_ONLY`, `VAULT_LOCAL`, `EXPORTABLE` (names may be normalized during R8.1 but semantics must remain distinct);
- preservation: source pinning/retention, derived-cache evictability, project-reference protection and explicit deletion state;
- license/governance policy can further restrict effective reuse regardless of requested scope;
- an asset with unknown or conflicting license/provenance cannot be silently promoted to unrestricted inter-project reuse.

Deletion must be two-phase where references exist: mark/request, dependency/reference analysis, then governed removal. Orphan cleanup never deletes pinned source revisions or the last recoverable source of a project reference.

## Reproducibility model

A derived result is considered reproducible only when the manifest captures, at minimum:

- exact input asset revision IDs/content digests;
- transform/recipe ID and schema version;
- tool/provider identity and exact version or immutable build identity when available;
- normalized deterministic settings/parameters;
- relevant platform/runtime context when it can affect bytes;
- output content digest(s);
- dependency digests for side inputs;
- non-deterministic flag and seed where applicable;
- timestamp as evidence only, never as identity.

A cache hit is valid only if its recipe key and output digest verify. A stale/corrupt entry is rebuilt or surfaced as `CORRUPT`/`UNAVAILABLE`; it is never trusted because a path exists.

## VCS / Git LFS model

R8 extends the accepted R4 Git/worktree surface; it does not replace it. Existing `GitWorktreeTool` already confines Git execution through `ProcessSandbox` and validates refs. R8 adds asset-aware structured operations and health checks on top of that pattern.

Git LFS is treated as a VCS transport/storage mechanism, not as Vault identity. A valid LFS pointer contains an object ID and size; pointer validity does not prove that the corresponding LFS object is locally or remotely available. R8 must therefore distinguish `POINTER_VALID`, `OBJECT_PRESENT`, `OBJECT_MISSING`, `LFS_UNAVAILABLE`, `TRACKING_MISMATCH` and related states.

Repository `.gitattributes` remains repository-owned source of truth for tracking rules. R8 may propose or safely mutate tracking rules only through a governed SafeChange operation and must never rely on a hidden global Git attributes configuration.

History-rewriting operations such as `git lfs migrate import` are explicitly out of normal R8 automation. If ever required, they need a separately reviewed user-directed migration plan and are not an acceptance shortcut.

## External-reference planning notes (non-normative)

The R8 design is informed by current official documentation checked during planning:

- GitHub documents Git LFS as storing pointer files in Git while large objects are stored separately; the pointer records spec version, SHA-256 OID and size.
- GitHub recommends committing repository `.gitattributes` rules so clones/forks share the same LFS tracking behavior.
- Godot 4.7 separates source assets from generated import/cache state; Kodepoia already ignores `.godot/` and `.import/`, which is compatible with R8's source/derived separation.
- Godot 4.7 exposes a headless `--import` path and importer-specific settings, allowing later R8 Godot rebuild verification to reuse the accepted R5 process boundary instead of inventing a new execution surface.

These references guide compatibility but do not override the frozen Kodepoia architecture or accepted evidence.

## Global prerequisites

Before R8.1 implementation begins:

- R1–R7 are COMPLETE on normalized `main`;
- `docs/roadmap/R7_INTEGRATED_ACCEPTANCE.json` remains valid and R7 integrated acceptance stays PASS;
- Python baseline remains 3.12.x unless a separately accepted compatibility change is made;
- R3 KodeMemory/embedding/semantic retrieval and model registry remain available for R8 semantic discovery;
- R4 structured files/search/patch/Git worktree tooling remains accepted;
- R5 Godot 4.7.x process/import automation remains accepted for the Godot bridge;
- R6 License/BOM, Health, Budget, Regression, CI, Privacy, AppSecurity and patch/rollback contracts remain accepted;
- R7 provenance/version/trust semantics remain available for research-derived source metadata;
- the existing repository Git LFS policy in `.gitattributes` is preserved unless R8.8 explicitly validates and safely evolves it;
- no new mandatory remote service is introduced;
- no asset bytes or model weights are committed to Kodepoia merely to make CI pass; fixtures stay small and deterministic.

## Complete subdivision index

| ID | Title | Status | Manual intervention | Depends on |
| --- | --- | --- | --- | --- |
| R8.1 | Asset/Vault contracts, identity, schemas + boundary | PLANNED | NONE | R7 COMPLETE + planning PR merged |
| R8.2 | Inter-project Vault store, revisions, reuse + preservation | PLANNED | NONE | R8.1 |
| R8.3 | Source/derived lineage + reproducible transform cache/rebuild | PLANNED | NONE | R8.1–R8.2 |
| R8.4 | Duplicate + near-duplicate detection | PLANNED | NONE | R8.1–R8.3 |
| R8.5 | Semantic asset search + hybrid ranking | PLANNED | CONDITIONAL | R8.1–R8.4 + R3 semantic retrieval |
| R8.6 | Provenance, license/BOM + governed reuse/export | PLANNED | NONE | R8.1–R8.5 + R6 + R7 |
| R8.7 | Asset-aware Git/VCS integration | PLANNED | NONE | R8.1–R8.6 + R4 |
| R8.8 | Git LFS tracking, pointer/object integrity + diagnostics | PLANNED | CONDITIONAL | R8.7 |
| R8.9 | Godot 4.7 source/import bridge + rebuild verification | PLANNED | CONDITIONAL | R8.3 + R8.6–R8.8 + R5 |
| R8.10 | CLI + KodeStudio Vault/Asset/VCS UX | PLANNED | NONE | R8.1–R8.9 |
| R8.11 | Adversarial hardening + R8 integrated acceptance | PLANNED | CONDITIONAL | R8.1–R8.10 |

---

# R8.1 — Asset/Vault contracts, identity, schemas + boundary

## Objective and rationale

Create one typed asset domain before storage, search or VCS behavior exists. Establish immutable identity/revision rules and a safe boundary for an explicitly configured local inter-project Vault root without modifying the semantics of project `WorkspaceBoundary`.

## In scope

- `AssetId`, `AssetRevisionId`, `AssetRecord`, `AssetRevision`, `AssetRole`, `AssetKind`, `ReuseScope`, `PreservationPolicy`, `AssetStatus` and typed provenance/lineage references;
- canonical SHA-256/content-length representation;
- source vs derived role;
- project reference contract;
- versioned JSON schemas for manifests/revisions/project references;
- a dedicated Vault boundary composed from the accepted path-confinement behavior;
- explicit path/symlink/absolute/traversal rejection;
- canonical serialization and tamper rejection;
- R8 package namespace, expected to be `src/kodepoia/assets/` unless repository review identifies a better already-existing home without architecture change.

## Out of scope

No inter-project copy/store operations, transforms, embeddings, Git/LFS mutation or UI.

## Detailed implementation plan

Implement frozen dataclasses/enums/contracts and schema serializers. IDs use canonical normalized records and verified digests. The Vault boundary accepts an explicit root from trusted application configuration, resolves all managed subpaths beneath it and rejects symlink escapes in the same fail-closed style as `WorkspaceBoundary`. Do not add a generic arbitrary-root file API to the model. Persisted manifests recompute derived identity fields when loaded; caller-provided digests are verified against bytes before a revision can reach READY.

## Deliverables

- `src/kodepoia/assets/` contracts/boundary/serialization modules;
- versioned schemas under `schemas/`;
- unit/tamper/path-boundary tests;
- `docs/roadmap/R8_1_DESIGN.md` and `R8_1_ACCEPTANCE.md`;
- public API exports only for stable typed contracts.

## Acceptance gates / Definition of Done

R0, full Python Core and UI Smoke SUCCESS on exact head; schema round-trip; deterministic ID generation; Windows/Unix path cases; traversal/absolute/symlink escape rejection; hash mismatch fails closed; no process/network surface introduced.

## Validation and evidence

Accepted head SHA, workflow run IDs, test counts, schema IDs/versions, representative manifest digest and boundary negative-test evidence.

## Rollback / recovery

Remove R8 contracts/schemas and restore exports. No irreversible durable state exists yet.

## Risks and regression traps

Identity depending on mutable names/paths; trusting serialized hash fields; symlink TOCTOU; case-fold differences across filesystems; inventing a second generic filesystem escape hatch.

## Manual intervention

**NONE**.

---

# R8.2 — Inter-project Vault store, revisions, reuse + preservation

## Objective and rationale

Implement the durable local Vault and safe project linking so multiple projects can reuse exact source revisions without uncontrolled copying, hidden mutation or loss of provenance.

## In scope

- content-addressed object store;
- transactional SQLite metadata/index;
- ingest/import from an authorized project path;
- exact byte verification before commit;
- immutable revisions and logical asset supersession;
- project reference/link records;
- reuse scope and preservation/pinning;
- reference counts/dependency queries as derived index data, never trusted identity;
- safe export/materialization into an authorized project path;
- two-phase delete/orphan collection with protection rules;
- atomic writes and crash recovery.

## Out of scope

Near-duplicate scoring, semantic embeddings, external downloads, Git history operations and transform execution.

## Detailed implementation plan

Use SHA-256-addressed immutable blobs and versioned manifests. Ingest stages bytes in a managed temporary area, hashes and size-checks them, records provenance, then atomically promotes the object and commits metadata transactionally. If an object hash already exists, reuse bytes but create/attach the correct logical revision metadata rather than silently collapsing distinct provenance records. Materialization verifies content before copy/link and never uses uncontrolled symlinks. Prefer copy or explicitly safe platform-aware link strategy only after capability tests; behavior must be deterministic and recoverable.

Deletion first computes live project/lineage/pin references. Source revisions referenced by projects or required to rebuild preserved outputs cannot be removed automatically. Index rebuild from manifests must be possible after SQLite loss/corruption.

## Deliverables

Vault store/index/service modules, migration/version handling, fixtures, crash/recovery/index-rebuild tests, CLI-internal service APIs, design/acceptance docs.

## Acceptance gates / Definition of Done

Cross-project reuse fixture; duplicate bytes stored once; distinct provenance retained; crash simulation leaves no READY record pointing to missing/corrupt bytes; reference protection works; index rebuild reproduces canonical state; path and permission failures explicit; R0/Python/UI gates pass.

## Validation and evidence

Exact head, run IDs, fixture hashes, object/revision counts before/after dedup, recovery report and acceptance evidence.

## Rollback / recovery

Restore metadata DB from Backup/SafeChange or rebuild from immutable manifests; staged/incomplete objects are quarantined/removed; source project files are never mutated during ingest.

## Risks and regression traps

Hash-before-write TOCTOU, partial copies, hardlink mutation hazards, Windows file-lock behavior, unsafe cross-volume assumptions, treating refcounts as authoritative identity, accidental deletion of only source copy.

## Manual intervention

**NONE**.

---

# R8.3 — Source/derived lineage + reproducible transform cache/rebuild

## Objective and rationale

Provide the AssetPipeline core: derived bytes are explicit products of source revisions and versioned transform recipes, with deterministic cache keys and rebuild evidence.

## In scope

- `TransformRecipe`, `TransformInput`, `TransformOutput`, `ToolIdentity`, `RebuildRecord`, `DeterminismState`;
- lineage DAG and cycle rejection;
- normalized recipe/config hashing;
- cache key from exact inputs + recipe + tool/provider identity + relevant environment;
- atomic derived-output staging/promotion;
- cache verify/hit/miss/stale/corrupt states;
- rebuild planning and execution API;
- registered fixed transform adapters only;
- ProcessSandbox/Guardian/KillSwitch for external executables;
- pure-Python deterministic fixture transform for CI.

## Out of scope

ComfyUI workflows, Blender operations, audio/TTS generation and arbitrary user-supplied command templates.

## Detailed implementation plan

Create a transform registry whose adapters own executable/template definitions. Model/user requests select a registered transform ID and typed parameters; they never supply argv/cwd/executable. Build a canonical recipe key, verify all input revisions, execute into a managed staging directory, hash outputs, persist lineage/evidence, then promote. On cancellation or failure, no READY derived revision is created. Rebuild re-resolves exact input revisions and refuses if required source/tool identity is unavailable unless the manifest explicitly allows a documented non-reproducible state.

## Deliverables

Transform contracts/registry/executor/cache/lineage modules, schemas, deterministic fixture adapter, cancellation/corruption tests, design/acceptance docs.

## Acceptance gates / Definition of Done

Identical inputs/recipe/tool identity produce same cache key; cache hit verifies bytes; changed input/setting/tool invalidates key; missing source blocks rebuild; cycle detection; cancellation leaves no promoted output; ProcessSandbox argument surface fixed; R0/Python/UI pass.

## Validation and evidence

Exact SHA, run IDs, recipe/input/output digests, cache hit/miss evidence, rebuild equivalence hash and cancellation evidence.

## Rollback / recovery

Derived/cache outputs can be removed only after lineage proves source preservation; index/manifests restore from canonical records; external source assets untouched.

## Risks and regression traps

Cache poisoning, environment-dependent nondeterminism, timestamp leakage into identity, hidden tool defaults, mutable source paths, output promotion before hash verification, cancellation after partial promotion.

## Manual intervention

**NONE** — authoritative acceptance uses deterministic fixtures and existing sandbox contracts; real provider-specific transforms belong to later phases.

---

# R8.4 — Duplicate + near-duplicate detection

## Objective and rationale

Prevent Vault bloat and confusing asset variants while distinguishing exact byte identity from probabilistic/similarity evidence.

## In scope

- exact duplicate groups via SHA-256;
- logical-duplicate/provenance-aware grouping;
- pluggable typed fingerprints for supported asset kinds;
- built-in deterministic metadata/text fingerprint baseline;
- supported image perceptual fingerprint only if dependency review keeps CI/local footprint acceptable; otherwise capability is explicit `UNAVAILABLE` until an accepted adapter exists;
- near-duplicate candidate score with threshold/version metadata;
- user/governance decision records for merge/keep-separate/supersede;
- no destructive auto-merge.

## Out of scope

Claiming semantic equivalence from a similarity score, automatic deletion of variants, model-generated licensing conclusions, heavy vision/audio/3D analysis reserved for later provider phases.

## Detailed implementation plan

Run exact hashing at ingest and asynchronously/explicitly compute optional fingerprints from immutable revisions. Fingerprint algorithms carry algorithm/version identity. Candidate similarity is evidence only; exact duplicates may share bytes automatically, but logical records/provenance remain distinct until governed consolidation. A changed fingerprint implementation never silently rewrites old evidence; recomputation creates a new fingerprint version.

## Deliverables

Duplicate service, fingerprint registry, schemas, candidate reports, fixtures and threshold/regression tests, design/acceptance docs.

## Acceptance gates / Definition of Done

Exact duplicate detection has zero false negatives for identical bytes; distinct provenance preserved; near-duplicate result includes algorithm/version/score/threshold; no candidate auto-deleted/merged; deterministic fixture ranking; R0/Python/UI pass.

## Validation and evidence

Exact SHA, workflow runs, duplicate group fixtures, fingerprint version/score reports and false-positive guard tests.

## Rollback / recovery

Drop/recompute fingerprint index without touching canonical asset objects/revisions. Consolidation decisions remain auditable and reversible while source revisions are preserved.

## Risks and regression traps

Conflating byte duplicate with same creative work; perceptual collisions; format-specific metadata noise; algorithm drift; accidental destructive dedup of assets with different provenance/license obligations.

## Manual intervention

**NONE**.

---

# R8.5 — Semantic asset search + hybrid ranking

## Objective and rationale

Make large inter-project Vaults discoverable by meaning, not only filenames, while reusing the accepted R3 local embedding/semantic retrieval contracts and retaining deterministic lexical/facet fallback.

## In scope

- searchable document derived from asset name, tags, human description, technical metadata, provenance, license fields and lineage summaries;
- local embedding generation through the accepted R3 `EMBED` role/provider boundary;
- embedding model/provider identity attached to vectors;
- hybrid lexical + semantic + structured facet filtering;
- filters for asset kind, source/derived, project, reuse scope, license state, tool lineage, dimensions/duration/format where known;
- deterministic fallback when embedding provider is unavailable;
- stale-vector detection/reindex when source metadata or embedding identity changes;
- no external/cloud embedding requirement.

## Out of scope

Vision/audio/3D multimodal embedding requirements, remote search service, opaque ranking that hides license/reuse blockers.

## Detailed implementation plan

Reuse the R3 semantic/vector boundary rather than creating a second embedding stack. Vault asset documents are normalized and embedded by a selected accepted EMBED model. Store vector identity/version separately from canonical asset manifests so vectors can be rebuilt. Query combines lexical score, semantic similarity and exact facets with a versioned ranking policy. Governance filters (BLOCKED reuse/license) are applied as policy, not merely ranking penalties.

## Deliverables

Search document builder/index/search service, embedding adapter bridge, hybrid ranking policy/schema, reindex tests, deterministic fake embedding fixture plus accepted-provider compatibility tests, design/acceptance docs.

## Acceptance gates / Definition of Done

Semantic fixture retrieves relevant assets beyond exact keyword overlap; lexical fallback works when embeddings unavailable; provider/model change marks vectors stale; filters are exact; governance-blocked assets cannot be accidentally promoted by high similarity; R0/Python/UI pass.

## Validation and evidence

Exact head, runs, ranking fixtures, model/provider identity, lexical fallback evidence and reindex report.

## Rollback / recovery

Delete/rebuild vector/search indexes from canonical manifests; no asset bytes or source metadata are lost.

## Risks and regression traps

Embedding drift, stale vectors, hidden remote calls, semantic score treated as truth, ranking instability, large-vector memory/disk budgets.

## Manual intervention

**CONDITIONAL** — normally NOT TRIGGERED because R3 already accepted the local embedding/model boundary and CI can validate R8 orchestration with deterministic fixtures. It becomes REQUIRED only if implementation changes the accepted EMBED provider contract or if authoritative acceptance depends on a new hardware-local embedding model not covered by R3 evidence. If triggered, run only the documented R8.5 local acceptance command on the exact candidate head and return redacted JSON/log evidence; never provide model files or secrets.

---

# R8.6 — Provenance, license/BOM + governed reuse/export

## Objective and rationale

Make inter-project reuse safe by preserving where an asset came from, what rights/attribution evidence is known, and whether export/reuse is allowed under Kodepoia policy.

## In scope

- provenance chain: local source, generated source, R7 research locator, imported package/repository, creator/publisher fields where evidenced;
- license state and evidence references;
- integration with R6 License/BOM records rather than a separate legal engine;
- attribution/notice fields and export report;
- policy outcomes `ALLOW`/`WARN`/`BLOCK` (exact enum may align with existing R6 types);
- unknown/conflicting license/provenance handling;
- reuse-scope downgrade when governance requires it;
- project BOM contribution from referenced assets;
- source/derived lineage inheritance rules without inventing rights.

## Out of scope

Legal advice, automatic resolution of ambiguous licenses, scraping license text outside R7 governed research, remote marketplace account automation.

## Detailed implementation plan

Bridge canonical R8 asset revisions into R6 `license_bom`/governance primitives. Imported evidence remains cited to exact provenance. Derived assets inherit source obligations as explicit dependencies unless an authoritative transformation/license record states otherwise. Export/materialization checks policy before writing. Unknown/conflicting records remain visible and cannot become unrestricted reuse by default.

## Deliverables

Provenance/license bridge, export manifest/notice report, policy tests, BOM integration tests, design/acceptance docs.

## Acceptance gates / Definition of Done

Unknown license does not silently become reusable/exportable; required attribution appears in export evidence; conflicting source obligations remain visible; derived asset retains source dependency; project BOM includes referenced Vault assets; R0/Python/UI pass.

## Validation and evidence

Exact head, run IDs, fixture BOM/export report, policy decision matrix and provenance-chain examples.

## Rollback / recovery

Governance indexes/reports can be rebuilt from canonical asset/provenance records; blocked exports leave no partial target output after rollback.

## Risks and regression traps

Treating a URL/name as legal proof, losing license obligations through derivation, conflating reuse scope with license permission, leaking personal/private source paths in exported reports.

## Manual intervention

**NONE**.

---

# R8.7 — Asset-aware Git/VCS integration

## Objective and rationale

Provide structured VCS awareness for assets and manifests while reusing the accepted R4 Git execution boundary. Kodepoia must know whether source assets/manifests are tracked, modified, ignored or conflicted without becoming a general arbitrary Git shell.

## In scope

- repository discovery only from an authorized project root;
- typed status for tracked/untracked/modified/deleted/conflicted/ignored files;
- exact HEAD/branch metadata;
- asset revision ↔ repository path/commit evidence;
- safe structured stage/unstage operations for explicitly selected authorized paths if allowed by Guardian;
- asset-aware diff metadata (binary changed/hash/size; no fake text diff for binaries);
- worktree compatibility with existing `GitWorktreeTool`;
- SafeChange/Audit around VCS mutations;
- no remote push required for acceptance.

## Out of scope

Arbitrary Git subcommands/config/refspecs, force-push, branch deletion, merge/rebase automation, remote credential management, repository history rewriting.

## Detailed implementation plan

Create an asset VCS adapter that owns fixed Git porcelain commands and parsers. Inputs are validated repository-relative paths and typed operations. Reuse `ProcessSandbox` and existing Git ref validation patterns. Binary asset change identity is recomputed from bytes and compared to Vault revision metadata. All mutation operations snapshot relevant index/manifests first and are auditable.

## Deliverables

VCS contracts/adapter, porcelain parser tests, binary status fixtures, worktree integration tests, design/acceptance docs.

## Acceptance gates / Definition of Done

Detached HEAD/dirty/conflict states explicit; path escape impossible; binary modifications detected; no arbitrary flags/commands; cancellation/timeouts safe; existing R4 Git tests continue passing; R0/Python/UI pass.

## Validation and evidence

Exact SHA, workflow runs, fixture repository HEAD/status matrix, sandbox argv audit and rollback evidence.

## Rollback / recovery

Unstage/restore only through explicit safe operations; Vault canonical objects are never mutated by Git rollback. Failed stage operations restore metadata snapshots as needed.

## Risks and regression traps

Porcelain parsing drift, Windows path quoting, nested repositories/submodules, worktree path confusion, Git filters affecting working-tree bytes, accidental command injection through ref/path.

## Manual intervention

**NONE**.

---

# R8.8 — Git LFS tracking, pointer/object integrity + diagnostics

## Objective and rationale

Make large binary asset versioning reliable and diagnosable. Detect mis-tracked assets, malformed pointers and missing LFS objects without pretending that Git pointer presence equals asset availability.

## In scope

- Git LFS capability/version detection through fixed `git lfs` commands in ProcessSandbox;
- parse/validate LFS v1 pointer fields (version, SHA-256 OID, size);
- compare pointer OID/size to hydrated working-tree bytes when available;
- repository `.gitattributes` tracking inspection;
- diagnostics for heavy binary types and policy mismatches;
- safe proposal/update of repository tracking rules with SafeChange + explicit confirmation/policy;
- `git lfs ls-files`/status diagnostics when available;
- explicit offline/missing-object states;
- current Kodepoia `.gitattributes` heavy-asset policy regression coverage.

## Out of scope

Automatic LFS server provisioning, billing management, hidden downloads, credential capture, forced remote fetch/push, `git lfs migrate import` history rewriting.

## Detailed implementation plan

Implement an LFS inspector/parser independent of the external binary for pointer parsing. External `git lfs` is optional for richer diagnostics. Tracking policy reads repository `.gitattributes` from the authorized repo and computes expected matching behavior. Any mutation updates `.gitattributes` through SafeChange; no global attributes changes. Missing git-lfs produces `UNAVAILABLE` rather than failure of unrelated Vault features.

## Deliverables

LFS pointer/parser/diagnostic service, `.gitattributes` policy checks, malformed/missing-object fixtures, capability doctor output, design/acceptance docs.

## Acceptance gates / Definition of Done

Valid pointer round-trip; malformed pointer rejected; size/OID mismatch detected; missing object distinct from invalid pointer; tracking mismatch visible; no hidden network call; current `.gitattributes` policy remains valid; R0/Python/UI pass.

## Validation and evidence

Exact head, workflow runs, git/git-lfs versions when available, pointer fixture hashes, tracking matrix and diagnostic report.

## Rollback / recovery

Revert `.gitattributes` via SafeChange snapshot; no history rewrite and no remote mutation. Local diagnostic state is rebuildable.

## Risks and regression traps

Treating pointer text as hydrated bytes, global-vs-repository attribute differences, filter behavior on checkout, missing LFS executable, large-object bandwidth assumptions, accidentally exposing remote credentials.

## Manual intervention

**CONDITIONAL** — normally NOT TRIGGERED if hosted CI has sufficient Git/LFS capability to execute the authoritative local-repository fixture. If an end-to-end real LFS remote upload/fetch becomes necessary to prove a defect that local fixtures cannot cover, the user must run a separately documented test on the exact head against a disposable repository/branch using existing credentials outside chat. Evidence must contain only run/status/OID/size data; no token, credential helper output or private URL. No history migration is allowed as part of this gate.

---

# R8.9 — Godot 4.7 source/import bridge + rebuild verification

## Objective and rationale

Connect R8 source/derived semantics to Kodepoia's accepted Godot 4.7 workflow so Godot import caches remain disposable derived state while original art/source files retain Vault/VCS identity.

## In scope

- classify project source assets vs Godot-generated `.godot/` / legacy `.import/` cache state;
- capture relevant import settings/sidecar metadata required to reproduce imports;
- invoke accepted R5 headless Godot import through its existing fixed process adapter, not raw subprocess;
- rebuild derived import cache from preserved source fixture;
- verify expected project/source references and resulting import readiness;
- never Vault-pin transient `.godot` cache as source;
- project portability diagnostics for missing Vault references/materialized source files.

## Out of scope

Authoring 2D/3D art, Blender conversion, ComfyUI generation, runtime asset streaming, changing Godot's importer implementation.

## Detailed implementation plan

Reuse R5 Godot executable discovery/sandbox/Guardian behavior. R8 records source revision + relevant import settings as lineage evidence but treats Godot cache bytes as disposable unless a specific generated artifact is intentionally promoted. Use small deterministic project fixtures. Rebuild deletes only managed generated cache state, invokes headless import, validates project parse/import status and records evidence without committing `.godot/`.

## Deliverables

Godot asset bridge, classification/import-manifest schema, deterministic fixture project, rebuild verification tests, design/acceptance docs.

## Acceptance gates / Definition of Done

Source asset survives cache purge; `.godot/`/`.import/` not classified as source; headless rebuild succeeds where Godot capability exists; missing Godot yields explicit `UNAVAILABLE` rather than corrupting Vault state; existing R5 tests pass; R0/Python/UI pass.

## Validation and evidence

Exact SHA, runs, Godot version/capability, source digest, import settings digest, rebuild report and project parse evidence.

## Rollback / recovery

Restore project/source files from SafeChange if any materialization changed; generated cache may be purged/rebuilt; Vault source revision remains immutable.

## Risks and regression traps

Godot importer version drift, nondeterministic generated cache bytes, accidentally versioning `.godot`, imported material extraction creating source-like files, platform-specific import settings.

## Manual intervention

**CONDITIONAL** — normally NOT TRIGGERED when existing R5 CI/local Godot capability can prove the fixture. If hosted CI cannot execute the exact Godot 4.7 import path required for acceptance, run the documented R8.9 local acceptance command on the exact head with the already accepted Godot installation. Return only the generated acceptance JSON/log; no project secrets or unrelated files.

---

# R8.10 — CLI + KodeStudio Vault/Asset/VCS UX

## Objective and rationale

Expose R8 through one service layer with transparent provenance, duplicate/search/lineage/VCS/LFS states and safe user controls.

## In scope

- one `AssetService`/equivalent used by CLI and Qt;
- CLI commands for vault doctor/status, ingest, list/show, search, duplicates, lineage, rebuild, materialize/export, VCS status and LFS doctor;
- KodeStudio Vault browser/search panel;
- filters/facets and asset detail view;
- source/derived lineage visualization;
- duplicate candidate groups with non-destructive decisions;
- license/reuse warnings;
- VCS/LFS health badges/states;
- cancellable long operations with progress/budget information;
- destructive actions require explicit confirmation and service authorization;
- no Qt-side direct Git/process/socket/secret handling.

## Out of scope

Full digital-asset-management collaboration server, cloud sync, marketplace browser, R9/R10 authoring UI.

## Detailed implementation plan

Qt and CLI call the same typed service. UI models receive sanitized structured records only. Search/background fingerprint/rebuild operations expose cancellation tokens and terminate before READY persistence on cancel. Details show exact revision/content ID, provenance/license state and rebuildability. Dangerous delete/export/tracking mutations use preview/plan → confirm → execute → evidence flow.

## Deliverables

Service façade, CLI parser/commands, KodeStudio models/widgets, UI smoke extensions, cancellation/progress tests, docs/help and acceptance file.

## Acceptance gates / Definition of Done

CLI/Qt parity for core read operations; UI does not bypass service; cancellation safe; no UI thread blocking on large scans; blocked/unknown license and missing LFS/source states visible; R0/Python/UI smoke all pass.

## Validation and evidence

Exact SHA, workflow runs, CLI JSON samples, UI smoke assertions/screenshots only if required, cancellation evidence.

## Rollback / recovery

Disable/remove UI/CLI routes while preserving canonical Vault data; partial operations remain recoverable via service transaction records.

## Risks and regression traps

UI freeze, accidental bulk delete, hidden background scan of unapproved roots, model seeing raw local absolute paths unnecessarily, mismatch between CLI and UI policy.

## Manual intervention

**NONE**.

---

# R8.11 — Adversarial hardening + R8 integrated acceptance

## Objective and rationale

Prove that the complete R8 stack is safe, deterministic, recoverable and correctly connected to R3/R4/R5/R6/R7 before R9 begins.

## In scope

Adversarial/cross-subsystem tests for:

- Vault traversal, absolute path, symlink/junction and cross-root escape;
- malicious filenames, Windows reserved/path normalization edge cases;
- source mutation between hash and promotion;
- forged manifest/digest/revision IDs;
- SQLite/index corruption and rebuild;
- cache poisoning and transform output tampering;
- lineage cycles and missing source revisions;
- duplicate/fingerprint collision candidates with no destructive auto-merge;
- embedding provider absence/stale vectors and governance filters;
- prompt injection in imported description/license/provenance text;
- VCS path/ref/option injection attempts;
- malformed/oversized Git LFS pointer and missing LFS objects;
- cancellation/KillSwitch during ingest/transform/rebuild/Git operations;
- license/BOM conflicts and blocked export;
- Godot cache purge/rebuild without source loss;
- crash/recovery around atomic promotion and deletion;
- large asset count/storage budget fixtures without committing heavy binaries.

Create a canonical `docs/roadmap/R8_INTEGRATED_ACCEPTANCE.json` that enumerates exactly R8.1–R8.11, links each acceptance document by Git blob SHA-256/byte length, records accepted implementation heads/manual states, computes blockers and emits a deterministic evidence digest. Add repository validation that regenerates/verifies this evidence from `git show HEAD:path` and fails closed on mismatch, following the proven R7 pattern without copying R7 identities.

## Out of scope

R9 implementation, live cloud storage, destructive real-repository migrations, unsupported provider claims.

## Detailed implementation plan

Run all focused R8 tests plus full regression. Add integrated repository evidence verifier and CI hook before pytest. Validate manual-state satisfaction explicitly. All potentially environment-specific capabilities must be either proven, explicitly `UNAVAILABLE`, or have their documented CONDITIONAL gate resolved; none may be inferred.

## Deliverables

Adversarial tests, integrated acceptance generator/verifier, `R8_INTEGRATED_ACCEPTANCE.json`, `R8_11_ACCEPTANCE.md`, phase completion evidence, continuity updates and final normalization if required.

## Acceptance gates / Definition of Done

- R8.1–R8.10 individually COMPLETE with exact-head evidence;
- R8.11 exact head passes R0 Repository Guard, full Python Core on required matrix and KodeStudio UI Smoke;
- all authoritative manual states explicitly satisfied or CONDITIONAL NOT TRIGGERED with reason;
- integrated report `status=pass`, `blockers=[]`, deterministic digest;
- R1–R7 acceptance regressions remain green;
- no large real asset/model artifacts committed to repository;
- PR merged before R8 phase may be declared COMPLETE;
- post-merge continuity normalization records final accepted `main` state.

## Validation and evidence

Accepted R8.11 head SHA, PR/merge SHA, R0/Python/UI workflow run IDs/conclusions, per-job test counts, integrated report digest, manual evidence summary, any local tool versions used and normalization merge if applicable.

## Rollback / recovery

If integrated acceptance fails, do not mark R8 COMPLETE and do not start R9. Revert only the failing R8 change through normal PR/SafeChange procedures, preserve immutable source Vault data, regenerate evidence only after a corrected exact head passes all gates.

## Risks and regression traps

Passing mocked behavior while a required real provider remains unproven; evidence generated from working tree instead of exact Git blobs; stale acceptance docs; manual state inferred from silence; index/cache cleanup deleting source; LFS remote assumptions; regressions to R4 Git or R5 Godot boundaries.

## Manual intervention

**CONDITIONAL** — normally NOT TRIGGERED if all environment-specific gates from R8.5/R8.8/R8.9 are already authoritatively satisfied and hosted CI can execute integrated acceptance. If triggered, the exact commands/evidence are inherited from the unresolved subdivision gate; R8.11 itself must not invent a new broad manual procedure. Never send secrets, model weights, private assets or unrelated repository content.

---

## Phase completion rule

R8 can be marked COMPLETE only when every R8.1–R8.11 row is COMPLETE with authoritative evidence, all required/triggered manual gates are explicitly satisfied, and the canonical integrated report passes on the exact accepted R8.11 head. The final merged `main` continuity must record the phase-closing evidence before R9 planning starts.

No hidden, implied or undocumented subdivision may be used to claim completion. No R9 implementation may begin directly after R8.11; R9 must first follow the permanent phase-start rule and merge an exhaustive `R9_PLAN.md`.

## Planning acceptance gate

This R8 plan itself is accepted only when, on one exact final planning head containing both this file and synchronized `docs/continuity/KODEPOIA_CONTINUITY.md`:

1. R0 Repository Guard is SUCCESS;
2. full Python Core is SUCCESS for all configured jobs;
3. KodeStudio UI Smoke is SUCCESS;
4. the planning PR is merged to `main`;
5. continuity is normalized with the accepted planning head/PR/merge evidence before R8.1 begins if the merge commit changes the source-of-truth SHA.

Until then, **R8 remains PLANNING and R8.1 is forbidden**.

## Ongoing maintenance rule

Update `R8_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md` in the same work cycle whenever subdivision scope/status, manual prerequisites, acceptance requirements, important recovered defects or ordering changes. Any change to frozen architecture requires an ADR before implementation proceeds.
