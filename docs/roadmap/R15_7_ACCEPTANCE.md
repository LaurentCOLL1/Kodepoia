# R15.7 — Acceptance record

**Acceptance state:** COMPLETE — TECHNICAL ACCEPTANCE RECORDED; FINAL END GATES REQUIRED  
**Clean START:** `9ef6f704d54332203e820cd2bd85e3b4ac86910a`  
**START synchronization:** `07593e95380df6fb43bda299b7de7295c614d17f`  
**Immutable technical source:** `a9a967289bbede1ffd155567f3caaa201d1af772`  
**Manual:** NONE

## Acceptance contract

R15.7 is merge-eligible only when the final documented END-head proves that identical immutable evidence yields the same decision; all frozen terminal dispositions are covered; unknown licence/data/backend evidence fails closed; a reproducible before-benchmark and immutable base-model identity are mandatory; critical targets are explicit; system defects produce `FIX_SYSTEM_FIRST`; and no training or router/tool mutation occurs.

## Technical evidence

Technical source `a9a967289bbede1ffd155567f3caaa201d1af772` passed all required technical qualification gates on the same exact head:

- R15.7 Gap Decision Acceptance #2 / `33299136312`: SUCCESS Ubuntu + Windows; R3/R15.6 compatibility, R15.7 focused/adversarial tests, Ruff, import ordering, compileall, CLI help and Draft 2020-12 schema validation;
- R0 Repository Guard #2134 / `33299136336`: SUCCESS Ubuntu + Windows;
- Python Core #2109 / `33299136316`: SUCCESS 5/5;
- KodeStudio UI Smoke #2074 / `33299136461`: SUCCESS.

## Required behavioral coverage

- deterministic `TRAIN` with explicit target domains, immutable base identity, dataset evidence, adapter method and acceptance targets;
- `NO_TRAIN` when no measured gap exists or expected model-training impact is explicitly low;
- `FIX_SYSTEM_FIRST` when relevant tool/retrieval/router/context/product diagnostics show a defect, before later training gates;
- `INSUFFICIENT_DATA` for missing or below-policy target-domain train data;
- `LICENSE_BLOCKED` for dataset/base-model `DENY`, `REVIEW` or `UNKNOWN` licence evidence;
- `UNSUPPORTED` for an explicitly unsupported backend;
- `BUDGET_BLOCKED` for exceeded or undeclared budget evidence;
- `INCONCLUSIVE` for missing reproducibility/contamination/diagnostic/backend/rollback or unresolved base identity evidence;
- scorer-failure benchmark evidence is rejected as invalid diagnosis evidence;
- superseding-decision lineage and JSON schema validation;
- CLI inspection performs no training/model execution.

## Final-END rule

The technical runs above prove the implementation source only. This END synchronization changes authoritative documentation, so fresh exact-head R15.7 Acceptance, R0 Repository Guard, full Python Core and KodeStudio UI Smoke are required on the final documented END tree before merge with `expected_head_sha`.

## Rollback / recovery

No model, dataset, router or training state is changed by R15.7. Rollback removes the derived decision surface and preserves all immutable input evidence.
