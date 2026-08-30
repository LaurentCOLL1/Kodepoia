# R15.15 — CLI + KodeStudio Experience/Bench/Tune UX acceptance

Status: IMPLEMENTED / exact-head acceptance pending.

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

## Exact-head acceptance required before merge

The final R15.15 PR head must receive all of the following without changing SHA afterwards:

1. R15.15 CLI + KodeStudio UX Acceptance on Ubuntu and Windows;
2. R0 Repository Guard;
3. full Python Core;
4. KodeStudio UI Smoke.

The implementation PR must then merge with exact `expected_head_sha`. Exactly one continuity-only post-merge normalization with fresh exact-head R0/Python/UI remains mandatory before R15.16 START-sync is authorized.
