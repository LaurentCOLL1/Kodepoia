# R8.5 — Semantic asset search + hybrid ranking — Acceptance

**Status:** CANDIDATE / PENDING EXACT-HEAD CI  
**Manual intervention:** CONDITIONAL — expected NOT TRIGGERED

Candidate scope: rebuildable search documents/index, provider/model/version-bound vectors, stale-vector detection, exact facet/governance filters, deterministic lexical fallback, hybrid lexical/cosine ranking and a narrow bridge to the accepted R3 Ollama embedding client.

The conditional manual gate is NOT expected to trigger because this candidate does not alter the accepted EMBED provider contract and does not require a new hardware-local embedding model for authoritative acceptance. Deterministic fixture embeddings validate orchestration in hosted CI. Final accepted SHA, PR/merge, workflow IDs and suite counts are recorded only after R0, full Python Core and KodeStudio UI Smoke all succeed on the same exact candidate head.
