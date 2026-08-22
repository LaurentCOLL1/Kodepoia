# R7.9 — Research cache + Context/Memory orchestration — Acceptance

**Status: IN PROGRESS — do not mark COMPLETE before exact-head CI succeeds.**

## Scope

This acceptance covers the R7.9 frozen subdivision only: content-addressed research cache, query/result manifests, TTL/revalidation metadata, deduplication, bounded context selection, citation-preserving summaries, research-memory project scope and invalidation by source/version/hash.

## Frozen invariants under test

- Cache selection identity is derived from the normalized query, project-scope hash, source selectors, target-version constraint, version evidence and cache-policy digest. `request_id` remains provenance but is not itself a cache-selection dimension.
- Raw query text and raw project-scope names are not persisted in query cache manifests.
- A cache hit never rewrites `ResearchArtifact.retrieved_at`, `ResearchArtifact.freshness`, trust, guard evidence or source provenance.
- Cache TTL/freshness is a cache-reuse decision only; it does not manufacture source `CURRENT` evidence.
- Mutable source identities use the shorter configured TTL and become STALE after expiry unless revalidated.
- Revalidation can advance cache-age evidence only when source identity, declared/normalized version evidence and content identity are unchanged.
- Content/source/version/policy/target/query selector changes invalidate derived cache entries.
- Deduplication incorporates source identity, source-declared or normalized version evidence and content hash. Artifacts with identical historical artifact IDs but different source-declared versions are not silently collapsed.
- Cached reports are reloaded through `ResearchStore` typed validation; tampered report/artifact evidence fails closed.
- Context summaries are extractive, bounded, citation-preserving, redacted through `KodeSecrets`, and explicitly tagged external/untrusted/guarded rather than trusted instructions.
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

## Hosted acceptance

Required exact-head workflows:

- R0 Repository Guard — **PENDING**
- Python Core (all required jobs) — **PENDING**
- KodeStudio UI Smoke — **PENDING**

Authoritative suite count and run IDs will be written only after the exact final implementation head is green.

## Manual intervention

**NONE.**

## Completion rule

R7.9 remains IN PROGRESS until all exact-head hosted gates are successful and this document is normalized with the accepted head/run evidence. Only after the normalization merge may R7.10 begin.
