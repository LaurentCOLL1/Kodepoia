# R7.1 — KodeResearch contracts + ResearchGuard hardening — Acceptance

**Status:** PASS / COMPLETE  
**Accepted implementation head:** `a6e9cf9f6db717155c311f4ded1ad5fb744b70ca`  
**Implementation PR:** #60  
**Implementation merge:** `86a5453b2fd8ce414e73277199fdd55bd210aeba`  
**Manual intervention:** NONE

## Accepted scope

R7.1 establishes the non-network KodeResearch foundation only:

- typed `ResearchRequest`, `ResearchSource`, `ResearchArtifact`, `ResearchCitation`, `ResearchFinding` and `ResearchReport` contracts;
- explicit source/status/freshness/trust/finding enums for the frozen R7 source classes;
- canonical SHA-256 identities and report digest;
- guarded artifact ingestion through the existing `ResearchGuard`;
- ResearchGuard versioning plus targeted role-override/tool-bypass indicators;
- project-confined `.kodepoia/research/` persistence through the existing `WorkspaceBoundary`;
- deterministic atomic JSON writes;
- Draft 2020-12 schemas for request, artifact and report;
- focused round-trip, tamper, injection, schema and persistence tests.

No HTTP transport, GitHub provider, forum adapter, YouTube provider, STT/media helper, subprocess surface or Research UI was introduced by R7.1.

## Exact-head hosted evidence

All required workflows ran against the exact accepted implementation head `a6e9cf9f6db717155c311f4ded1ad5fb744b70ca`:

- R0 Repository Guard — run #959 / `32584754313` — SUCCESS, Ubuntu + Windows;
- Python Core — run #933 / `32584754311` — SUCCESS, 5/5 jobs;
- KodeStudio UI Smoke — run #900 / `32584754325` — SUCCESS, Windows.

Authoritative Ubuntu Python Core pytest evidence: **310 passed / 3 skipped / 46 warnings**. The run completed successfully; skipped tests and warnings were not treated as fabricated PASS evidence and did not replace any R7.1 required test.

## Acceptance invariants verified

1. request/source/artifact/citation/finding/report objects round-trip through deterministic serialized forms;
2. canonical request/source/artifact/citation/finding identifiers and report digest are recomputed rather than trusted;
3. artifact content SHA-256 is recomputed from UTF-8 source content;
4. serialized guard evidence is recomputed from original content, so changing `suspicious` or indicators cannot launder instruction-like material;
5. timestamp fields reject timezone-naive values;
6. source facts require citations and reports reject citations to absent artifacts;
7. initialized-project persistence remains under `.kodepoia/research/` through `WorkspaceBoundary` and accepts only SHA-256-derived store identifiers;
8. schemas validate canonical examples and reject missing required report digest evidence;
9. external instruction-like fixture text remains stored as data and is explicitly marked suspicious;
10. R7.1 exposes no live network or external-process execution path.

## ResearchGuard trust statement

`guarded` means that material has passed through the deterministic ResearchGuard envelope. It does **not** mean the external material is trusted to instruct the agent, authorize tools or modify policy. External research remains data.

## Manual gate

**NONE.** No local/manual action is required for R7.1 acceptance.

## Decision

**PASS. R7.1 is COMPLETE.** The next planned subdivision is **R7.2 — Local + official documentation research**. R7.2 must reuse these contracts and the existing WorkspaceBoundary/ResearchGuard foundations; it must not introduce general Web behavior reserved for R7.3.
