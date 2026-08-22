# R8.5 — Semantic asset search + hybrid ranking — Design

R8.5 implements the frozen semantic-search scope without changing the accepted R3 embedding provider contract.

- `SearchDocumentBuilder` derives rebuildable text/facets from canonical asset record/revision data, project references, provenance, lineage, human description and explicit technical/license metadata.
- `AssetSearchIndex` persists documents/vectors separately under the Vault `search/` area. Canonical asset manifests and immutable object bytes are never rewritten by search indexing.
- Every vector is bound to `(provider, model, provider contract version, document digest)`. Provider/model or metadata changes therefore make an old vector `STALE` instead of silently reusing it.
- Hybrid ranking policy v1 is explicit: 0.40 lexical + 0.60 cosine semantic score. Structured facets are exact filters applied before ranking, and `blocked` documents are excluded by default regardless of similarity.
- Lexical fallback is deterministic and remains available when no embedding provider exists or the accepted provider reports `BrainUnavailable`. R8.5 therefore has no mandatory remote/cloud dependency.
- `OllamaEmbeddingProvider` is only an adapter over the existing R3 `OllamaClient.embed` method; it introduces no second network client and no new host/model-download surface.
- The accepted R3 client already targets Ollama `/api/embed`. Current official Ollama documentation continues to describe `/api/embed` as the embedding endpoint for semantic search/retrieval use cases, consistent with this bridge.
- SQLite FTS5/BM25 remains a possible future lexical-index optimization, but R8.5 correctness does not depend on FTS5 being compiled into every platform build; the authoritative fallback is platform-independent.

## Manual gate

**CONDITIONAL NOT TRIGGERED** for this implementation. Hosted CI can authoritatively validate hybrid orchestration with deterministic fixture vectors and can compatibility-test the R3 `OllamaClient.embed` bridge without changing the provider contract or requiring a new hardware-local embedding model.
