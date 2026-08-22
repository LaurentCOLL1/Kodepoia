# R8.5 — Semantic asset search + hybrid ranking — Acceptance

**Status:** COMPLETE / ACCEPTED  
**Manual intervention:** CONDITIONAL NOT TRIGGERED

## Accepted implementation

- Exact implementation head: `08c90bd8d52a7dd2dfc8da6ce94f6731701469f6`.
- PR: #89.
- Merge SHA: `9bb1f169d7f1534b0068ad43691accf1b6a5e14a`.

## Authoritative CI on the exact head

- R0 Repository Guard #1052 / `32602982436`: SUCCESS.
- Python Core #1026 / `32602982445`: SUCCESS 5/5.
- Ubuntu authoritative suite: `542 passed / 5 skipped / 46 warnings`.
- KodeStudio UI Smoke #993 / `32602982448`: SUCCESS.

## Accepted scope

Rebuildable search documents/index, vectors bound to provider/model/provider-contract-version/document digest, explicit `CURRENT`/`STALE`/`MISSING`/`UNAVAILABLE` vector states, exact structured facet filtering, policy filtering of blocked assets before ranking, deterministic lexical fallback, versioned hybrid lexical + cosine ranking and a narrow adapter over the accepted R3 `OllamaClient.embed` contract.

The search index is separate from canonical Vault manifests/objects and can be deleted/rebuilt without source loss. A provider/model or source-metadata change cannot silently reuse a stale vector.

## Manual gate outcome

The conditional manual gate was **NOT TRIGGERED**. R8.5 did not change the accepted R3 EMBED provider contract and did not require a new hardware-local embedding model. Hosted CI provided authoritative orchestration evidence using deterministic fixture embeddings and a compatibility test of the existing Ollama embedding bridge. No user-side command, model download, model file, credential or secret was required.
