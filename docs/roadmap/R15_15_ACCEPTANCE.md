# R15.15 — CLI + KodeStudio Experience/Bench/Tune UX acceptance

Status: COMPLETE / END-sync closed; final exact-head re-gates pending.

R15.15 exposes the frozen R15 Experience/Bench/Tune pipeline through structured, backend-independent CLI and KodeStudio workflows. It does not expose a raw shell, raw secret editor, quarantined private content viewer or public model upload surface.

## Frozen UX contract

- eight structured domains are exposed: Experience, Dataset, Bench, Gap, Training, Conversion, Ollama and Registry;
- the catalog covers status/curation, dataset build/inspect, KodeBench run/compare, gap diagnosis, training doctor/plan/run/status/cancel, conversion doctor/status, Ollama status and registry candidates/promote/rollback;
- mutating actions default to a non-mutating dry-run in the CLI and require both an explicit execution mode and confirmation before a configured backend handler can be invoked;
- absent mutation backends fail closed and never silently mutate state;
- evidence exports are project-scoped, SHA-256-bound and recursively redacted;
- KodeStudio uses typed controls and a worker `QThread` for governed actions so potentially long operations do not execute on the UI thread;
- English, French and pseudo-localized navigation/control text are available;
- accessibility names/descriptions are mandatory for the R15.15 controls;
- manual state: `NONE`.

## Accepted technical-source evidence

Technical source `7ede682ec2c21d89e42886a5774115278b0fbb2c` passed all pre-END gates on the same SHA:

- R15.15 CLI + KodeStudio UX Acceptance #5 / `33335194725`: SUCCESS Ubuntu 24.04 + Windows 2025;
- R0 Repository Guard #2212 / `33335194680`: SUCCESS Ubuntu + Windows;
- Python Core #2187 / `33335194694`: SUCCESS 5/5;
- KodeStudio UI Smoke #2152 / `33335194748`: SUCCESS.

Because this END synchronization changes documentation, these technical-source runs are historical implementation evidence only. The resulting END-sync SHA must receive fresh copies of all four required gates before PR #326 may merge.

The workflow-originated END synchronization produced documentary candidate `f8f96c9b6b0cb64147237013343bbc6f01700d69`. This docs-only closure commit intentionally changes no runtime, CLI, UI or test behavior; it establishes the final PR head on which the mandatory fresh exact-head gates are evaluated.

## Exact-head acceptance required before merge

The final R15.15 PR head must receive all of the following without changing SHA afterwards:

1. R15.15 CLI + KodeStudio UX Acceptance on Ubuntu and Windows;
2. R0 Repository Guard;
3. full Python Core;
4. KodeStudio UI Smoke.

The implementation PR must then merge with exact `expected_head_sha`. Exactly one continuity-only post-merge normalization with fresh exact-head R0/Python/UI remains mandatory before R15.16 START-sync is authorized.
