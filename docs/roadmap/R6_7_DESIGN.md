# R6.7 — KodeTechnicalDebt foundation — Design

**Parent plan:** `docs/roadmap/R6_PLAN.md`  
**Architecture:** v1.0 frozen  
**Manual intervention:** NONE

## Goal

Create a persistent, deterministic technical-debt contract so debt is observable, prioritized, traceable and regression-testable instead of remaining informal comments.

## Architecture boundary

R6.7 is evidence/quality infrastructure only. It does not execute arbitrary scanners, rewrite code, resolve debt automatically, alter Guardian/Sandbox/KillSwitch boundaries or make architecture decisions without ADR.

Persistent evidence is confined to:

`.kodepoia/diagnostics/technical_debt/`

through `WorkspaceBoundary`.

## Stable data model

### Lifecycle

`DebtState` has exactly:

- `open` — unresolved debt;
- `accepted` — consciously tolerated debt with mandatory rationale; still visible and penalized;
- `resolved` — fixed debt retained as history with required `resolved_at`.

Accepted debt is deliberately not equivalent to resolved debt. Accepted/resolved items cannot remain blocking. Open debt cannot carry a resolution timestamp or accepted rationale.

### Identity and duplicate detection

Each debt item has a human-stable `id` and a derived SHA-256 fingerprint from:

- category;
- normalized summary;
- normalized scope;
- normalized stable references.

The fingerprint excludes volatile timestamps, lifecycle state, owner and ranking values. Therefore the same debt keeps the same fingerprint while moving from open to accepted/resolved or while `last_seen` changes.

A report rejects duplicate IDs and duplicate fingerprints.

### References

Structured references may identify:

- file;
- symbol;
- test;
- requirement;
- issue;
- other stable referent.

Duplicate references inside an item are rejected.

### Priority

Priority is deterministic:

`severity_weight × impact × probability ÷ effort`

where severity weights are low=1, medium=2, high=3, critical=4 and impact/probability/effort are each integers 1–5.

Maximum priority is 100 (`4×5×5÷1`). Lower implementation effort raises actionable priority rather than hiding expensive-risk debt behind subjective labels.

### Report status

- any blocking open debt → `FAIL`;
- any non-resolved debt without blockers → `WARN`;
- no debt or resolved-only history → `PASS`.

A debt penalty sums full priority for open debt and 25% priority for accepted debt, capped at 100. Accepted debt therefore remains visible in Health rather than disappearing.

## KodeHealth integration

`KodeTechnicalDebt.to_health_metric()` emits the architecture dimension `technical_debt`:

- score = `100 - debt_penalty`;
- PASS/WARN/FAIL mirrors the structured debt report;
- blocking is true only when report blockers exist;
- counts, blockers, ranking and evidence hash remain in details.

## R6.3 regression integration

Each debt item maps to stable test ID:

`technical-debt:<debt-id>`

- resolved → PASS;
- open blocking → FAIL;
- open nonblocking / accepted → SKIP, preserving warning semantics.

Because R6.3 classifies a newly added failing test as a regression, newly introduced blocking debt is automatically regression evidence without adding another comparison engine.

## Evidence integrity

`TechnicalDebtReport` derives and validates:

- counts by lifecycle state;
- blocker IDs;
- active ranking;
- debt penalty;
- item priority and fingerprint;
- canonical SHA-256 evidence hash.

Round-trip loading rejects mismatched derived fields or tampering.

## Repository observations

R6.7 may document already observed warnings/notices with precise provenance, but it must not pretend that an unexecuted scanner produced them. `R6_7_KNOWN_DEBT.md` records candidates observed during earlier acceptance/CI work.

## Rollback

R6.7 is additive. Rollback removes the technical-debt module/schema/tests/docs and its quality exports, while preserving R6.1–R6.6 evidence. Existing `.kodepoia/diagnostics/technical_debt/` evidence is not deleted automatically.
