# R15.6 — KodeBench v2 design

**Status:** COMPLETE — technical design implemented  
**Clean START / branch point:** `097e99db28508cd1c53eadfe00b2b33576a445af`  
**Immutable technical source:** `ae856396faa964fee19ee39e461bc7de4e775cd9`  
**Manual:** NONE

## Objective

Extend the accepted R3 `BaselineBench` into a deterministic KodeBench v2 authority without breaking `bench-models` or `r3-accept`. R15.6 makes later specialization measurable by domain and criticality while keeping failures and resource costs explicit.

## Implemented architecture

- immutable suite, task, scorer, run-config, model/runtime, outcome and report contracts;
- canonical JSON + SHA-256 identities for suite/task/prompt/scorer/config/report evidence;
- exact, contains/forbidden, regex, JSON-schema, tool-call and repository-code-owned custom scorers;
- domain/critical scoring, repeat/seed variance and explicit PASS / WRONG_ANSWER / MODEL_FAILURE / CAPABILITY_UNAVAILABLE / SCORER_FAILURE categories;
- elapsed/load/total/tokens-per-second/token-count/model-size/VRAM evidence when available;
- strict report comparisons requiring identical suite/config/protection digests and exposing critical regressions;
- R15.4 `ProtectedHoldoutRegistry` binding, with safe holdout IDs/digests and prompt/response digests rather than protected raw text in persisted reports;
- strict Draft 2020-12 report schema and `kodebench-compare` CLI;
- `baseline_compat_suite()` and execution through the existing R3 `BaselineBench`.

## Reproducibility and security contract

Comparable runs bind stable suite/scorer definitions, repeats/seeds/options, model/runtime identity and the protected-holdout manifest. Historical scores are immutable. Benchmark/model text never becomes a shell command, and custom scorer callables cannot be imported from benchmark data. Missing holdout authority, mismatched model identity, incomparable reports or scorer failures fail closed or remain separately classified.

## Informative external methodology baseline

MLCommons/MLPerf is used only as an informative reproducibility reference for fixed configurations, traceable results and comparable conditions. NIST TEVV material is used only as an informative reference for structured evidence-backed evaluation. Neither overrides frozen R15 repository governance.

- https://mlcommons.org/benchmarks/
- https://www.nist.gov/artificial-intelligence

## START synchronization repair note

Continuity was correctly changed to `R15.6 IN_PROGRESS` before implementation bytes. `R15_PLAN.md`'s checkpoint/table row was inadvertently left at its older `PLANNED` wording in that START work cycle. This END-sync repairs that stale plan state explicitly; it does not claim the plan had been synchronized earlier. Technical-source gates remain technical evidence only, and fresh exact-head R15.6/R0/Python/UI gates are mandatory on the repaired final END tree.
