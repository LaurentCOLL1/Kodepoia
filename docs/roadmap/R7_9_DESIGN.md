# Kodepoia — R7.9 design

**Subdivision:** R7.9 — Research cache + Context/Memory orchestration  
**Manual:** NONE  
**Architecture:** v1.0 frozen; additive research-side orchestration only

## Objective

R7.9 makes research reuse deterministic and bounded while preserving the evidence/trust guarantees accepted in R7.1–R7.8. It adds:

- hash-bound query/result cache manifests under `.kodepoia/research/cache/`;
- explicit TTL and revalidation decisions;
- source/version/content-aware invalidation;
- deduplication before model context while retaining provenance groups;
- bounded deterministic research context summaries with citations and guard evidence;
- an explicit opt-in bridge into project-scoped Memory only.

A cache hit is a reuse decision, not a claim that an external source is CURRENT. An extractive research summary is context, not validated experience.

## Cache-key contract

`ResearchQueryManifest` derives the cache key from non-secret canonical inputs:

- normalized query SHA-256, not raw query text;
- project-scope SHA-256, not raw project-scope text;
- sorted source-kind policy;
- `max_results`;
- optional R7.8 target constraint ID;
- sorted version-evidence fingerprints;
- cache-policy digest/schema.

`ResearchRequest.request_id` is retained as provenance in serialized manifests/results but **must not affect the cache-key identity**. Therefore equivalent whitespace-normalized queries can reuse a cache entry even when request timestamps/request IDs differ.

Query normalization is deliberately conservative: Unicode NFC + whitespace collapse. It does not lowercase/casefold code/product identifiers because case can be meaningful.

No raw query, project-scope text, credential, secret value or provider token belongs in a R7.9 cache manifest.

## Result manifests

`ResearchResultManifest` stores only evidence references/metadata:

- cache key and originating request ID;
- authoritative `ResearchReport.digest_sha256`;
- per-artifact ID/source ID/content SHA-256;
- optional R7.8 source-identity ID;
- version fingerprint;
- source mutability;
- **original** retrieval timestamp and freshness;
- trust (`guarded`) and suspicious flag;
- cache stored/revalidated timestamps;
- cache-policy digest;
- canonical manifest ID.

Artifact content remains in `ResearchStore`; it is not duplicated into result manifests. `load_cached_report()` reloads the authoritative `ResearchReport`, which in turn reconstructs/re-runs ResearchGuard evidence through existing `from_dict()` validation, then checks report/artifact provenance against the result manifest.

## Cache storage and history

`ResearchCacheStore` is `WorkspaceBoundary` confined under `.kodepoia/research/cache/` and requires an initialized `.kodepoia/` project.

- query manifests: `cache/queries/<cache_key>.json`;
- immutable result manifests: `cache/results/<manifest_id>.json`;
- latest result index: `cache/result-index/<cache_key>.json` containing only hashes.

Revalidation creates a new result manifest ID instead of mutating the historical manifest. Atomic temporary-file replace is used for JSON writes.

## TTL / revalidation

`ResearchCachePolicy` is explicit and hash-bound. Current defaults:

- non-mutable/unknown identity cache TTL: 86,400 seconds;
- mutable-source cache TTL: 3,600 seconds;
- context: 12,000 chars / 16 findings.

The exact numbers are policy, not truth. Changing them changes `policy_digest` and invalidates the prior cache key/decision.

`assess_cached_result()` returns only:

- `FRESH`: cache entry is within reuse TTL;
- `STALE`: TTL expired and revalidation is required;
- `INVALIDATED`: query/policy/source/version/content identity no longer matches or time evidence is invalid.

This decision does **not** rewrite `ResearchArtifact.freshness`. A cached artifact originally UNKNOWN or STALE remains UNKNOWN/STALE after cache reuse.

For mutable sources, cache revalidation requires an explicit `revalidated_at`. A later read of the cache does not update it.

`with_revalidation()` accepts a revalidation timestamp only when the stored/current source identity, version fingerprint and content hash signatures are unchanged. If representation/version/identity changed, the old entry is invalidated and a new research result is required.

### Standards cross-check

RFC 9111 distinguishes storage/reuse from freshness and validation: a stored response can become stale and require validation; freshness depends on age/lifetime or successful validation, not merely on being present in a cache. R7.9 applies the same conservative conceptual separation to research evidence without claiming to implement HTTP caching semantics for every research provider.

## Invalidation dimensions

Cache invalidation is explicit for:

- normalized query/source selection/max-results changes;
- target constraint/version-evidence changes;
- cache policy/schema changes;
- source identity changes;
- declared source-version evidence changes;
- content SHA-256 changes;
- impossible/future cache age evidence.

No cache hit silently upgrades a version relation or source freshness.

## Deduplication

`deduplicate_artifacts()` deduplicates only when these are the same:

1. canonical source locator identity (`SourceIdentity` when supplied, otherwise source ID);
2. version fingerprint, including explicit `ResearchSource.version` plus any R7.8 version observation;
3. content SHA-256.

Different locators, different versions or different content remain distinct even when prose looks similar. Dedupe groups retain representative/artifact/source/identity IDs; dedupe is a context-size optimization, not provenance deletion.

## Bounded context summaries

`ResearchContextBuilder` is deterministic/extractive. It does not call an LLM to invent a summary. It selects existing `ResearchFinding.claim` values, preferring source facts before inferences, then applies explicit char/item bounds.

Each `ResearchContextEntry` preserves:

- finding ID and kind (`SOURCE_FACT` vs `INFERENCE`);
- citation IDs and artifact IDs;
- sanitized citation locators;
- original artifact freshness states;
- optional R7.8 version relation;
- suspicious flag and ResearchGuard indicators;
- fixed trust label `external_guarded_untrusted`.

The rendered context begins with an explicit security instruction to the consuming Kodepoia model: the material is external research evidence/data and must never be treated as instructions. The corresponding `ContextItem` carries tags `research`, `external`, `untrusted`, `guarded`, `project_scoped`.

`validated_experience` is structurally fixed to `false`; deserialization rejects attempts to promote it.

## Secret redaction

Context construction runs both:

- `KodeSecrets.redact()` for known delegated secret values when a `KodeSecrets` instance is supplied;
- conservative generic masking for common Authorization Bearer, API-key/token/password assignments, GitHub token prefixes and OpenAI-style `sk-` token shapes.

Raw query/scope strings are not stored in cache manifests. Context summaries contain only redacted finding/citation text. Existing provider adapters remain responsible for never placing credentials in research artifacts/locators in the first place.

## Context persistence

`ResearchContextStore` persists the already-bounded summary under `.kodepoia/research/context/<summary_id>.json` with `WorkspaceBoundary`, atomic writes and canonical ID validation. Original reports/artifacts/citations remain authoritative evidence.

## Memory bridge

`ResearchMemoryBridge.store_project_summary()` is deliberately **explicit opt-in**. Building a context summary never writes to Memory automatically.

When called, the bridge:

- requires a non-global project scope;
- writes kind `research_summary_untrusted` under scope `project:<scope>`;
- passes `GovernancePolicy(scope=PROJECT, allow_global_memory=False, allow_training_dataset=False, delete_with_project=True)`;
- records metadata `validated_experience=false`, `global_promotion_allowed=false`, `training_dataset_allowed=false`, trust state, report/citation/artifact IDs;
- rejects any summary whose trust/validated state was promoted.

R7.9 therefore does not create global validated experience. Any future promotion would need the separate validation/governance pipeline and is outside R7.9.

## Schemas

R7.9 adds versioned Draft 2020-12 schemas for:

- `research-query-cache-v1.schema.json`;
- `research-result-cache-v1.schema.json`;
- `research-context-summary-v1.schema.json`.

Python deserialization additionally recomputes canonical keys/IDs and fails closed on tampering.

## Acceptance matrix

R7.9 acceptance must prove at minimum:

- whitespace-normalized equivalent queries share a cache key even with different request IDs/timestamps;
- case is not silently normalized;
- target/source/version/policy changes alter the key;
- raw query/project scope/secret values are absent from query manifests;
- query/result/context schemas validate canonical payloads;
- result refs preserve original retrieval/freshness/trust;
- mutable TTL expires independently of artifact freshness;
- unchanged explicit revalidation can renew reuse age;
- changed source/version/content cannot be revalidated as the same entry;
- query/policy/current-signature changes invalidate;
- future cache timestamps fail closed;
- cache/history paths remain `.kodepoia/research` confined;
- authoritative reports reload/revalidate through `ResearchStore`;
- dedupe requires same source identity + version + content;
- context is char/item bounded and cited;
- guard suspicious/indicator evidence survives context construction;
- known and common generic secrets are redacted;
- trust/validated-experience promotion tampering is rejected;
- persisted context round-trips under WorkspaceBoundary;
- normal `ContextBuilder` retains research trust tags;
- Memory bridge writes only project scope with database `allow_global=0`, `allow_training=0`;
- global memory scope is rejected;
- context building alone writes no Memory record;
- R7.8 version relation can be carried to context without changing finding kind/trust;
- result-manifest content-hash tampering is rejected;
- R0, Python Core and KodeStudio UI Smoke are SUCCESS on the exact final head.

## Exclusions

R7.9 adds no:

- new network provider;
- new subprocess;
- arbitrary command/argv/cwd/host surface;
- automatic global memory promotion;
- LLM-generated truth summary;
- embedding model requirement;
- vector database requirement;
- KodeStudio UI (R7.10);
- integrated R7 completion claim (R7.11).

## Manual gate

**NONE.** Deterministic fixtures and exact-head hosted CI are sufficient.

## Rollback

Remove the R7.9 cache/context orchestration modules, schemas, tests and documentation. Existing `ResearchStore`, R7.1–R7.8 artifacts/citations/version provenance, `ContextBuilder`, `MemoryStore` and Project DNA remain unchanged. Cache/context derived files under `.kodepoia/research/` may be deleted without deleting the authoritative research artifacts.
