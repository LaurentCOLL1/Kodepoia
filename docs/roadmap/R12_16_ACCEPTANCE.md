# R12.16 — Acceptance

## Scope

Adversarial hardening + anti-circular Wizard-to-Windows integrated acceptance only.

Base normalized `main`: `30095003ab5fa61328319be320122ff647ce351a`.
Branch: `r12/16-adversarial-integrated-acceptance`.
Manual intervention: **CONDITIONAL / NOT TRIGGERED at subdivision start**.

Trigger manual evidence only if the final frozen R12 Definition of Done requires an interactive/runtime/install Windows semantic that accepted hosted Windows CI cannot establish. A trigger changes R12.16 to `BLOCKED / MANUAL_REQUIRED`; no canonical PASS report or R13 planning may proceed until one bounded exact-head collector is executed and reviewed.

## Required implementation acceptance

The immutable pre-report implementation candidate must contain:

- `src/kodepoia/desktop/integrated_acceptance.py` with strict evidence bindings and anti-circular verifier;
- strict schemas `schemas/r12/r12-windows-ci-acceptance.schema.json` and `schemas/r12/r12-integrated-acceptance.schema.json`;
- `scripts/r12_16_windows_ci_acceptance.py` producing candidate-bound Windows CI evidence;
- `scripts/r12_16_build_integrated_report.py` capable of generating the later canonical report but unable to succeed without already accepted Windows CI evidence;
- `.github/workflows/r12-integrated-windows.yml` on `windows-latest` + Python 3.12 + .NET 10;
- `tests/test_desktop_r12_16.py` covering evidence substitution plus path/env/SQL/IPC/cancellation/package attacks;
- this acceptance and `R12_16_DESIGN.md`;
- **no checked-in `docs/roadmap/R12_16_WINDOWS_CI_ACCEPTANCE.json` and no checked-in `docs/roadmap/R12_INTEGRATED_ACCEPTANCE.json` on the first immutable implementation candidate**.

Required exact-head implementation gates:

- R0 Repository Guard;
- full Python Core, including Linux/Windows test matrix and package build evidence defined by the workflow;
- KodeStudio UI Smoke;
- WPF, WinUI, Avalonia, Qt and Tauri regression workflows;
- dedicated `R12 Integrated Windows Acceptance` on the same exact candidate SHA.

The dedicated Windows workflow must create one Project Wizard desktop intent, persist DNA/Product, scaffold deterministically, reload via DesktopWorkspaceService, compile/test the WPF shared model through ProcessSandbox, verify semantic package artifacts, emit a schema-valid JSON artifact and exit successfully.

## Anti-circular evidence ordering

1. Freeze one immutable implementation head while both canonical checked-in R12 evidence JSON files are absent.
2. Require all implementation gates above on exactly that head.
3. Decide the CONDITIONAL manual trigger truthfully from the actual frozen claim and CI results.
4. If manual is required, stop and collect/review exact-head manual evidence before proceeding; otherwise record `conditional_not_triggered`.
5. Freeze implementation SHA + run IDs in this acceptance/PR metadata without changing the accepted implementation bytes where possible.
6. Download the exact `R12 Integrated Windows Acceptance` artifact from that candidate; verify its source SHA, schema and semantic digest; import it unchanged as `docs/roadmap/R12_16_WINDOWS_CI_ACCEPTANCE.json`.
7. Generate `docs/roadmap/R12_INTEGRATED_ACCEPTANCE.json` with `scripts/r12_16_build_integrated_report.py --source-sha <accepted-implementation-sha>`.
8. Validate the report schema and call `validate_repository_evidence`; it must bind all R12.1–R12.16 acceptances, continuity, exact Windows CI evidence and canonical R11 digest `ed956be1aa19592b654382a209e5ca99d44d3cbcd67dd3981bdae3d865563170`.
9. Perform the required **end-of-subdivision** synchronization: `R12_PLAN.md` + continuity mark R12.16 `COMPLETE`; R12 as a phase is not yet `COMPLETE + NORMALIZED` until post-merge normalization.
10. Freeze the final evidence/documentation head and run fresh exact-head R0/full Python/UI plus desktop adapter regressions and integrated Windows acceptance.
11. Merge the implementation/evidence PR only with `expected_head_sha` equal to that accepted final head.
12. Create exactly one continuity-only R12.16 post-merge normalization; gate its exact head with the same standard family and merge with expected SHA.
13. Only after that normalization merge is R12 `COMPLETE + NORMALIZED`; only then may R13 planning start.

## Evidence state

Start-of-subdivision plan/continuity synchronization: **DONE** — R12.1–R12.15 `COMPLETE`, R12.15 `COMPLETE + NORMALIZED`, R12.16 `IN_PROGRESS`.

Normalized base: `30095003ab5fa61328319be320122ff647ce351a`.

Implementation candidate: **PENDING FREEZE**.
Implementation exact-head gates: **PENDING**.
Dedicated Windows CI artifact: **PENDING**.
Manual state after implementation gates: **PENDING DECISION; currently not triggered**.
Checked-in Windows CI evidence: **ABSENT by anti-circular design**.
Canonical `R12_INTEGRATED_ACCEPTANCE.json`: **ABSENT by anti-circular design**.
End-of-subdivision plan/continuity synchronization: **PENDING**.
Final evidence/documentation gates: **PENDING**.
Implementation/evidence merge: **PENDING**.
Single post-merge continuity normalization: **PENDING**.

## Failure policy

Any failed gate rejects that exact candidate. Correct only R12.16, freeze a new SHA, and restart every required implementation gate. Missing evidence, stale workflow runs, editable `status=pass`, mismatched source SHA, recomputed attacker digests, or prior-phase substitution never manufacture PASS.
