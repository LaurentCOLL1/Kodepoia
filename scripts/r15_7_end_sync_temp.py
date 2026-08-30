from pathlib import Path

start_main = "9ef6f704d54332203e820cd2bd85e3b4ac86910a"
start_sync = "07593e95380df6fb43bda299b7de7295c614d17f"
technical = "a9a967289bbede1ffd155567f3caaa201d1af772"

Path("docs/roadmap/R15_7_DESIGN.md").write_text(
    f'''# R15.7 — Gap diagnosis + governed TRAIN/NO_TRAIN decision engine

**Status:** COMPLETE — technical design implemented  
**Clean START / normalized R15.6 main:** `{start_main}`  
**START synchronization:** `{start_sync}`  
**Immutable technical source:** `{technical}`  
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
''',
    encoding="utf-8",
    newline="\n",
)

Path("docs/roadmap/R15_7_ACCEPTANCE.md").write_text(
    f'''# R15.7 — Acceptance record

**Acceptance state:** COMPLETE — TECHNICAL ACCEPTANCE RECORDED; FINAL END GATES REQUIRED  
**Clean START:** `{start_main}`  
**START synchronization:** `{start_sync}`  
**Immutable technical source:** `{technical}`  
**Manual:** NONE

## Acceptance contract

R15.7 is merge-eligible only when the final documented END-head proves that identical immutable evidence yields the same decision; all frozen terminal dispositions are covered; unknown licence/data/backend evidence fails closed; a reproducible before-benchmark and immutable base-model identity are mandatory; critical targets are explicit; system defects produce `FIX_SYSTEM_FIRST`; and no training or router/tool mutation occurs.

## Technical evidence

Technical source `{technical}` passed all required technical qualification gates on the same exact head:

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
''',
    encoding="utf-8",
    newline="\n",
)

plan = Path("docs/roadmap/R15_PLAN.md")
text = plan.read_text(encoding="utf-8")
lines = text.splitlines()
checkpoint_count = 0
row_count = 0
for index, line in enumerate(lines):
    if line.startswith("**Execution checkpoint:**"):
        lines[index] = (
            "**Execution checkpoint:** R1–R14 are COMPLETE + NORMALIZED; R15 planning is ACCEPTED + NORMALIZED. "
            "R15.1–R15.6 are COMPLETE + NORMALIZED. R15.7 is COMPLETE on this documented END candidate after "
            f"technical qualification of `{technical}`; fresh exact-head R15.7/R0/Python/UI gates, expected-head "
            "merge and one continuity-only normalization remain required before R15.8. R15.8–R15.17 remain PLANNED."
        )
        checkpoint_count += 1
    if line.startswith("| R15.7 |"):
        parts = line.split("|")
        parts[3] = " COMPLETE "
        lines[index] = "|".join(parts)
        row_count += 1
if (checkpoint_count, row_count) != (1, 1):
    raise SystemExit(
        f"plan END marker mismatch: checkpoint={checkpoint_count} r15.7={row_count}"
    )
text = "\n".join(lines) + "\n"
start = text.index("# R15.7 —")
end = text.index("# R15.8 —", start)
section = text[start:end]
marker = "## Completion record\n\nTo be appended when accepted."
if section.count(marker) != 1:
    raise SystemExit(f"unexpected R15.7 completion marker count: {section.count(marker)}")
completion = f'''## Completion record

**COMPLETE — technical acceptance recorded; fresh final-END gates required before merge.**

- clean START / normalized R15.6 main: `{start_main}`;
- START synchronization before implementation: `{start_sync}`;
- immutable technical source: `{technical}`;
- R15.7 Acceptance #2 / `33299136312`: SUCCESS Ubuntu + Windows;
- R0 Repository Guard #2134 / `33299136336`: SUCCESS Ubuntu + Windows;
- Python Core #2109 / `33299136316`: SUCCESS 5/5;
- KodeStudio UI Smoke #2074 / `33299136461`: SUCCESS;
- deterministic ordered gates cover benchmark reproducibility, contamination validity, system diagnostics, data sufficiency, dataset/base licence, backend/budget and rollback readiness;
- `FIX_SYSTEM_FIRST` precedes training/data/licence gates when a relevant system defect explains the measured gap;
- R15.7 executes no training and mutates no model/router/tool state;
- manual state: `NONE`;
- the exact final documented END-head must receive fresh R15.7/R0/Python/UI evidence before protected merge; technical-source evidence is not reused for that decision.
'''
section = section.replace(marker, completion, 1)
plan.write_text(text[:start] + section + text[end:], encoding="utf-8", newline="\n")

continuity = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
text = continuity.read_text(encoding="utf-8")
lines = text.splitlines()
lines[0] = (
    "> Kodepoia, architecture v1.0 gelée. **R1–R14 COMPLETE + NORMALIZED. R15 planning ACCEPTED + NORMALIZED. "
    "R15.1–R15.6 COMPLETE + NORMALIZED; R15.7 COMPLETE; R15.8–R15.17 PLANNED.** "
    f"R15.7 clean START `{start_main}`; START-sync `{start_sync}`; immutable technical source `{technical}` passed "
    "R15.7 #2 / `33299136312` SUCCESS Ubuntu + Windows, R0 #2134 / `33299136336` SUCCESS Ubuntu + Windows, "
    "Python Core #2109 / `33299136316` SUCCESS 5/5 and UI #2074 / `33299136461` SUCCESS. Fresh exact-head "
    "R15.7/R0/Python/UI on the documented END tree, protected expected-head merge and exactly one continuity-only "
    "normalization remain required before R15.8. Manual NONE."
)
entry = (
    f"- R15.7 : **COMPLETE** — clean START / normalized R15.6 main `{start_main}`; START-sync `{start_sync}` "
    f"preceded implementation; immutable technical source `{technical}`; R15.7 #2 / `33299136312` SUCCESS "
    "Ubuntu + Windows, R0 #2134 / `33299136336` SUCCESS Ubuntu + Windows, Python Core #2109 / `33299136316` "
    "SUCCESS 5/5 and UI #2074 / `33299136461` SUCCESS; deterministic ordered gap-decision authority implements "
    "TRAIN/NO_TRAIN/FIX_SYSTEM_FIRST/INSUFFICIENT_DATA/UNSUPPORTED/LICENSE_BLOCKED/BUDGET_BLOCKED/INCONCLUSIVE, "
    "requires immutable benchmark/base/dataset evidence, diagnoses tool/retrieval/router/context before training, and "
    "executes no training. Manual NONE. Fresh exact-head R15.7/R0/Python/UI on the documented END tree, exact-head "
    "PR #309 merge and one continuity-only normalization remain required before R15.8."
)
entry_count = 0
row_count = 0
next_count = 0
for index, line in enumerate(lines):
    if line.startswith("- R15.7 :"):
        lines[index] = entry
        entry_count += 1
    if line.startswith("| R15.7 |"):
        lines[index] = "| R15.7 | COMPLETE | NONE |"
        row_count += 1
    if line == "## Next authorized action":
        for candidate in range(index + 1, min(index + 6, len(lines))):
            if lines[candidate].startswith("**"):
                lines[candidate] = (
                    f"**R15.7 technical source `{technical}` is qualified and END authority is synchronized. "
                    "Require fresh exact-head R15.7 Acceptance + R0 Repository Guard + full Python Core + KodeStudio UI "
                    "Smoke on the final documented PR #309 head, then merge only with `expected_head_sha`. After merge, "
                    "perform exactly one continuity-only normalization that does not modify `docs/roadmap/R15_PLAN.md`; "
                    "only the resulting normalized `main` authorizes R15.8 START-sync. Manual NONE.**"
                )
                next_count += 1
                break
if entry_count == 0:
    # Insert immediately after the existing R15.6 global-state entry.
    for index, line in enumerate(lines):
        if line.startswith("- R15.6 :"):
            lines.insert(index + 1, entry)
            entry_count = 1
            break
if (entry_count, row_count, next_count) != (1, 1, 1):
    raise SystemExit(
        f"continuity END marker mismatch: entry={entry_count} row={row_count} next={next_count}"
    )
continuity.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
