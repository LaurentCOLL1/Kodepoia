# R15.7 — Gap diagnosis + governed TRAIN/NO_TRAIN decision engine

**Status:** COMPLETE — technical design implemented  
**Clean START / normalized R15.6 main:** `9ef6f704d54332203e820cd2bd85e3b4ac86910a`  
**START synchronization:** `07593e95380df6fb43bda299b7de7295c614d17f`  
**Immutable technical source:** `a9a967289bbede1ffd155567f3caaa201d1af772`  
**Manual:** NONE

## Objective

Implement the frozen R15.7 principle “build around the model, measure, then specialize”: a low benchmark score never triggers training by itself. The decision authority consumes immutable KodeBench, dataset and governance evidence and decides whether a measured gap is plausibly model-trainable or should first be fixed in tools, retrieval, routing, context or product logic.

## Implemented contracts

- `DecisionDisposition`: `TRAIN`, `NO_TRAIN`, `FIX_SYSTEM_FIRST`, `INSUFFICIENT_DATA`, `UNSUPPORTED`, `LICENSE_BLOCKED`, `BUDGET_BLOCKED`, `INCONCLUSIVE`;
- deterministic `DecisionPolicy` with a canonical policy digest;
- immutable `DiagnosticProbe` evidence for tool, retrieval, router, context and optional product diagnostics;
- explicit backend capability, budget and expected-impact vocabularies;
- `DecisionEvidence` binding benchmark reproducibility, contamination validity, dataset/base-model licence decisions, backend/budget/rollback state and named evidence digests;
- `GapRecord`, per-domain `AcceptanceTarget` and immutable `GapDecision` records with canonical decision digests and superseding-decision lineage;
- Draft 2020-12 schema `schemas/r15-7-gap-decision.schema.json`;
- structured `gap-decision` CLI that reads saved evidence and writes an immutable decision report without executing a model or training process.

## Ordered fail-closed decision gates

The engine implements the frozen order exactly:

1. reproducible immutable before-benchmark and resolved base-model digest;
2. valid train/evaluation contamination evidence;
3. system-vs-model diagnostics;
4. eligible training-data sufficiency for every target domain;
5. dataset and immutable base-model licence eligibility;
6. backend capability and declared resource/time budget;
7. rollback readiness.

A relevant tool/retrieval/router/context/product defect returns `FIX_SYSTEM_FIRST` before later data/licence/training gates. Missing or unknown diagnostic/backend/rollback evidence never becomes `TRAIN`. Unknown/review/denied licence evidence is `LICENSE_BLOCKED`. Missing or insufficient target-domain training examples is `INSUFFICIENT_DATA`. Unsupported backend and exceeded/undeclared budget remain distinct terminal states.

## Benchmark and dataset binding

R15.7 reuses R15.6 KodeBench v2 rather than creating a second benchmark authority. It validates/records suite, run-config, protected-holdout and report digests, rejects scorer-failure evidence, requires the selected base model to have an immutable model digest before training can be authorized, and derives measured task/domain gaps from that fixed report.

R15.7 consumes the R15.5 immutable dataset manifest surface. Only `train` entries count toward target-domain sufficiency. The decision records dataset ID/digest plus a canonical digest of the supplied manifest evidence; no dataset text is interpreted as executable configuration.

## Acceptance-target semantics

Critical target domains receive a hard minimum score of `1.0` in the R15.7 decision record. Non-critical target domains receive a deterministic minimum improvement target derived from the versioned decision policy. These are pre-training targets; R15.10 remains the authority that evaluates an actual candidate and enforces the critical-regression veto.

## Security and scope boundaries

R15.7 never executes training, installs ML dependencies, downloads models, mutates prompts/tools/router state, or treats model/dataset text as commands. The CLI is inspection/decision-only. Evidence remains digest-bound and superseding decisions cite the prior immutable decision instead of rewriting history.

## Rollback / recovery

Decision reports are derived immutable records. Reverting R15.7 removes the decision module/schema/CLI surface without modifying KodeBench, datasets, models or router state. A later decision with changed evidence supersedes rather than mutates an earlier decision.
