# R12.15 — Acceptance

## Scope

Structured desktop CLI + KodeStudio Desktop workspace + governed Project Wizard workflow only.

Manual intervention: **NONE**.

Base normalized `main`: `089e54cdbd1ac344ce71fc92eef213ad2e9589d3`.
Branch: `r12/15-cli-kodestudio-desktop`.

## Required acceptance

- `kodepoia r12` exposes exactly `status`, `scaffold`, `validate`, `build`, `test`, `package` operation intents with stable JSON state and exit semantics;
- no R12 CLI command accepts raw executable, argv, shell/script, MSBuild/CMake/Cargo flags, SQL, certificate, signing-key or updater credential input;
- passive `status` and `validate` perform no external process invocation;
- a user-edited evidence JSON containing `status=pass` remains merely `reported_status` and cannot mutate the workspace state to PASS;
- absent governed execution backend makes `scaffold/build/test/package` explicitly BLOCKED/non-zero rather than synthetic PASS;
- an active global KillSwitch cancels execution before the backend receives the typed operation;
- KodeStudio has a Desktop workspace consuming Project Wizard-persisted desktop intent;
- KodeStudio evidence is read-only and Refresh is passive;
- explicit KodeStudio execution buttons are distinct from Refresh and share the typed service boundary;
- new UI strings are available through source and pseudo-localized R12 catalogs;
- focused R12.15 tests, full Python Core, KodeStudio UI Smoke, R0 Repository Guard and existing WPF/WinUI/Avalonia/Qt/Tauri regressions succeed on one exact candidate SHA.

## Evidence state

Start-of-subdivision plan/continuity synchronization: **DONE** — R12.1–R12.14 `COMPLETE`, R12.15 `IN_PROGRESS`, R12.16 `PLANNED`.

Implementation candidate: **ACCEPTED** — `79cda1733bc470f897a5153dcd0c4d059b948900`.
Candidate exact-head gates: **SUCCESS** — R0 #1577 / `32834583380`; Python #1551 / `32834583390`; KodeStudio UI #1518 / `32834583399`; WPF #68 / `32834583424`; WinUI #58 / `32834583419`; Avalonia #54 / `32834583411`; Qt #49 / `32834583377`; Tauri #40 / `32834583375`.
Candidate correction note: the earlier candidate `696ab04eda402fd77b826ef80c9cc8a98706ad75` was rejected after KodeStudio UI Smoke #1516 exposed the unregistered `r12Evidence` accessibility control and stale pseudo-locale navigation cardinality. Both defects were corrected before freezing `79cda1733bc470f897a5153dcd0c4d059b948900`; no failed evidence is reused.
End-of-subdivision plan/continuity synchronization: **DONE** — R12.15 is `COMPLETE`; R12.16 remains `PLANNED`.
Synchronized documentation head: **ACCEPTED FOR RECORDING** — `881ac7e6baee67f594f62377f3a7d1b9aee2ce72`.
Synchronized-documentation exact-head gates: **SUCCESS** — R0 #1580 / `32836806493`; Python #1554 / `32836806644`; KodeStudio UI #1521 / `32836806507`; WPF #71 / `32836806242`; WinUI #61 / `32836806760`; Avalonia #57 / `32836806320`; Qt #52 / `32836806429`; Tauri #43 / `32836806371`.
Final recorded-evidence documentation head: **PENDING** — this record changes bytes and therefore requires one fresh exact-head gate cycle before merge.
Implementation merge: **PENDING**.
Post-merge continuity normalization: **PENDING**.

## Acceptance ordering

1. freeze one implementation candidate;
2. require exact-head R0 + full Python Core + KodeStudio UI Smoke + five desktop adapter regressions;
3. because manual state is NONE, no user-local evidence is required;
4. update `R12_PLAN.md` and continuity so R12.15 is `COMPLETE` while R12.16 remains `PLANNED`;
5. record candidate and synchronized-documentation evidence; re-gate the resulting recorded-evidence documentation head because bytes changed;
6. merge with `expected_head_sha` only after that final exact-head cycle is green;
7. perform exactly one continuity-only post-merge normalization, gate it on its exact SHA, merge it;
8. only then authorize the R12.16 branch.
