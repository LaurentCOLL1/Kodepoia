# R7.9 — Research cache + Context/Memory orchestration — Acceptance

**Status: ACCEPTED / COMPLETE**

## Accepted implementation

- Exact accepted head: `80390f95a11e5b3d4353b16eada26f10204bb4fa`
- Implementation PR: #76
- Implementation merge: `5406887055117e7fea5cdd27579fb27b41051ed1`
- Manual intervention: **NONE**

## Scope

R7.9 implements the frozen subdivision only: content-addressed research cache, query/result manifests, TTL/revalidation metadata, deduplication, bounded context selection, citation-preserving summaries, project-scoped research memory and invalidation by source/version/hash.

## Accepted invariants

- Cache selection identity is derived from normalized query, project-scope hash, source selectors, target-version constraint, version evidence and cache-policy digest. `request_id` remains provenance but is not itself a cache-selection dimension.
- Raw query text and raw project-scope names are not persisted in query cache manifests.
- A cache hit never rewrites `ResearchArtifact.retrieved_at`, `ResearchArtifact.freshness`, trust, guard evidence or source provenance.
- Cache TTL/freshness is a cache-reuse decision only; it does not manufacture source `CURRENT` evidence.
- Mutable source identities use the shorter configured TTL and become STALE after expiry unless revalidated.
- Revalidation can advance cache-age evidence only when source identity, declared/normalized version evidence and content identity are unchanged.
- Content/source/version/policy/target/query selector changes invalidate derived cache entries.
- Deduplication incorporates source identity, source-declared and normalized version evidence plus content hash. Historical artifact-ID collisions cannot silently merge distinct declared-version evidence.
- Cached reports reload through `ResearchStore` typed validation; tampered report/artifact evidence fails closed.
- Context summaries are extractive, bounded, citation-preserving, secret-redacted and explicitly tagged external/untrusted/guarded rather than trusted instructions.
- Oversized findings are deterministically trimmed to the largest entry that actually fits the configured rendered-context bound; they are not dropped merely because a fixed overhead estimate was wrong.
- Suspicious ResearchGuard evidence survives cache/context round-trip.
- Research-to-memory write is explicit, project-scoped and uses governance with `allow_global_memory=false` and `allow_training_dataset=false`; no automatic promotion to validated/global Experience occurs.
- Context and memory adapters add no new network/process/tool surface.

## Deliverables

- `src/kodepoia/intelligence/research/cache.py`
- `src/kodepoia/intelligence/research/cache_runtime.py`
- `src/kodepoia/intelligence/research/orchestration.py`
- `schemas/research-query-cache-v1.schema.json`
- `schemas/research-result-cache-v1.schema.json`
- `schemas/research-context-summary-v1.schema.json`
- `tests/test_r7_9_cache_context_memory.py`
- `docs/roadmap/R7_9_DESIGN.md`

## Exact-head hosted acceptance

All authoritative workflows succeeded on `80390f95a11e5b3d4353b16eada26f10204bb4fa`:

- R0 Repository Guard #1018 / `32596697106` — **SUCCESS**
- Python Core #992 / `32596697107` — **SUCCESS 5/5**
  - Ubuntu authoritative suite: **483 passed / 4 skipped / 46 warnings**
  - Ubuntu package build: SUCCESS
  - Windows Python Core: SUCCESS
  - Windows package build: SUCCESS
  - embedded KodeStudio UI Windows: SUCCESS
- KodeStudio UI Smoke #959 / `32596697121` — **SUCCESS**

## Rejected candidate evidence

The earlier exact head `2a092335ca3dc7d7fb39fc9e1ef177f0c9d16251` was **not accepted**. Python Core #990 exposed two R7.9 defects: version-evidence ambiguity during deduplication when historical artifact IDs collided, and bounded-context logic that could omit an oversized finding instead of trimming it to the real rendered budget. Both defects were corrected on the same branch; the accepted head above reran the full authoritative gates successfully.

## Manual intervention

**NONE — SATISFIED by definition; no manual gate was required.**

## Completion rule

R7.9 is COMPLETE after this normalization is merged with its own exact-head repository/Python/UI gates. Only then may **R7.10 — CLI + KodeStudio Research UX** begin.
