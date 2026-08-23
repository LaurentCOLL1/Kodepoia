# R8.11 — Adversarial hardening + R8 integrated acceptance — Acceptance

**Status:** ACCEPTED / PENDING INTEGRATED EVIDENCE AND MERGE  
**Manual intervention:** CONDITIONAL NOT TRIGGERED

## Accepted implementation head

- Exact accepted implementation head: `d1589cf94545b854f995e7b6706c4b67e9b7ac1a`.
- Base normalized R8.10 main: `32c9dc413a89b74cd702c25b21a257cfc21d3cfc`.
- PR: #101.
- Merge SHA: PENDING.

No later implementation code is accepted unless the complete R0/Python/UI gate set is rerun and this document is deliberately superseded together with the integrated evidence.

## Authoritative implementation CI

On exact implementation head `d1589cf94545b854f995e7b6706c4b67e9b7ac1a`:

- R0 Repository Guard #1092 / `32621457672`: SUCCESS Ubuntu + Windows.
- Python Core #1066 / `32621457675`: SUCCESS 5/5.
- Ubuntu authoritative suite: `587 passed / 7 skipped / 46 warnings`.
- Package build/evidence: SUCCESS Ubuntu + Windows inside Python Core #1066.
- Python Core integrated Windows KodeStudio smoke: SUCCESS.
- KodeStudio UI Smoke #1033 / `32621457788`: SUCCESS.

The warning baseline remains 46; R8.11 did not hide or add a deprecation-warning regression.

## Adversarial result

R8.11 adds explicit cross-subsystem evidence for:

- forged/tampered revision manifests fail closed and are reported corrupt during index rebuild;
- poisoned rebuildable SQLite revision metadata is replaced from canonical manifests;
- transform outputs escaping managed staging cannot be promoted;
- transform cache hits cannot redirect a request to a different logical output asset;
- hostile instruction-shaped description/license metadata remains search data and governance-blocked rather than acquiring authority;
- option-shaped Git filenames remain data because structured path operations retain the `--` path boundary;
- malformed, oversized and non-canonical Git LFS pointers fail closed;
- pre-cancelled rebuild preserves canonical manifest/object evidence;
- failed/tampered materialization cannot replace an existing target or leave a promoted temporary target;
- a bounded many-asset fixture exercises Vault/index behavior using only tiny generated files.

The full Python regression suite also re-executes the accepted R8.1–R8.10 tests, including Vault boundary/symlink checks, duplicate non-destructive behavior, semantic fallback/stale embeddings, license/BOM blocked export, VCS/LFS diagnostics and Godot source/import bridge invariants.

## Hardening defect found and corrected

The first R8.11 candidate `28fe9610bcdf9d92a4e6aa0367441b342bfd288b` was intentionally not accepted. Python Ubuntu reported two failures:

1. a real transform-cache integrity defect: a cache hit produced for one logical output asset could be returned for another logical output asset when inputs/recipe/tool/environment matched;
2. one adversarial test expected an empty tuple while the accepted search API returns an empty list.

The gate was not weakened. Production `TransformService` was hardened so a cache HIT now additionally binds the serialized request/output evidence and canonical revision evidence to:

- exact input revision IDs;
- canonical recipe;
- exact tool identity;
- exact environment identity;
- requested logical output asset;
- output revision content hash/length;
- DERIVED role and expected output kind;
- exact transform-input lineage;
- transform provenance and READY status.

Old cache documents lacking the new `output_asset_id` evidence become STALE and are rebuilt through the accepted staging/promotion path; the existing R8.3 cache key contract itself was not silently redefined.

The search assertion was corrected to the existing list return type; no production search/governance behavior changed.

## R8-specific integrated acceptance contracts

R8.11 adds `kodepoia.assets.acceptance` and `schemas/r8-integration-report-v1.schema.json` rather than modifying the frozen R7 Research acceptance model.

The R8 report requires exactly R8.1 through R8.11 in order. For every subdivision it binds:

- canonical `docs/roadmap/R8_<n>_ACCEPTANCE.md` source;
- Git blob SHA-256;
- exact byte length;
- accepted implementation head;
- manual state;
- explicit manual-state reason;
- derived manual satisfaction.

Passing integrated evidence cannot contain explicit or derived blockers. R8.11's accepted implementation head must equal the report `source_sha`.

Repository validation reloads canonical acceptance bytes from `git show HEAD:<path>` and recalculates length/hash before trusting the checked-in report.

## Manual state

R8.11's frozen manual mode is CONDITIONAL. It resolves to **CONDITIONAL NOT TRIGGERED** because:

- R8.5's embedding-model conditional remained NOT TRIGGERED and no new authoritative embedding contract/model was introduced by R8.11;
- R8.8's Git LFS conditional remained NOT TRIGGERED and hosted CI exercised the accepted LFS parser/policy surface without requiring a new environment-specific manual proof;
- R8.9's environment-specific Godot gate is already **REQUIRED SATISFIED** by its authoritative Godot 4.7.2 local acceptance evidence;
- R8.11 integrated report generation/verification and the full standard CI matrix are executable in hosted CI.

No inherited unresolved manual gate exists, so the conditional R8.11 manual procedure is not triggered.

## Remaining integrated-evidence sequence

This acceptance document deliberately fixes the R8.11 implementation head before creating `R8_INTEGRATED_ACCEPTANCE.json`, avoiding a self-referential commit identity.

Remaining steps before PR #101 can merge:

1. add the deterministic R8 integrated generator/verifier and Python Core Linux hook;
2. let the verifier print the canonical candidate while `docs/roadmap/R8_INTEGRATED_ACCEPTANCE.json` is absent;
3. check in that exact candidate and synchronize continuity;
4. rerun R0 Repository Guard, full Python Core and KodeStudio UI Smoke on one final exact evidence head;
5. require the checked-in integrated report to validate `status=pass` and `blockers=[]` from canonical Git blobs;
6. merge PR #101 only after those final exact-head gates succeed;
7. post-merge, update continuity only (or regenerate/reaccept the integrated report if any canonical acceptance document is changed) and pass the normalization gates before declaring R8 COMPLETE.

## Result

R8.11 implementation is **ACCEPTED** on exact head `d1589cf94545b854f995e7b6706c4b67e9b7ac1a`. Integrated evidence and PR merge are still pending. R9 remains NOT STARTED and unauthorized.