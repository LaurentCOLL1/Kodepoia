# R12.5 — Acceptance

## Scope

WPF/.NET desktop adapter + real Windows build/test bridge.

Manual intervention: **CONDITIONAL**. Trigger only if the required WPF Windows runtime semantic cannot be proven on accepted hosted Windows evidence.

## Required acceptance

- WPF fixture is deterministically mapped from the shared R12.4 canonical logical model;
- `UseWPF=true` and Windows-only target are explicit;
- missing/incompatible SDK reports `UNAVAILABLE`/`UNSUPPORTED`, never PASS;
- executable/toolchain identity is bounded and hashed;
- project/configuration/property/environment injection paths fail closed;
- restore/build/runtime test commands are fixed argv under ProcessSandbox/KillSwitch;
- actual WPF application compiles on Windows with an accepted stable .NET toolchain;
- actual WPF STA harness runs and proves `PresentationFramework`, `Application`, `Dispatcher`, `Window` and the shared-model binding sentinel;
- build/test output is parsed and staged artifacts receive SHA-256 manifest evidence;
- no Linux/macOS runtime claim is manufactured;
- exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke + `R12 WPF Acceptance` all succeed.

## Accepted implementation evidence

Branch: `r12/5-wpf-dotnet-adapter`.
Base normalized `main`: `180a507a81c979ec797f3bafe3de29ba38b72c94`.
Accepted implementation head: `bd2ac96b4ac2a1b366ab52aae2ea50f7d49fce33`.

- R0 Repository Guard #1496 / run `32782170580` — **SUCCESS**.
- Python Core #1470 / run `32782170531` — **SUCCESS**, including Ubuntu/Windows pytest, both package builds and internal KodeStudio smoke.
- KodeStudio UI Smoke #1437 / run `32782170529` — **SUCCESS**.
- R12 WPF Acceptance #7 / run `32782170577` — **SUCCESS**: .NET SDK `10.0.400`, real restore, WPF compile, STA harness runtime and evidence upload.
- Conditional manual state: **NOT TRIGGERED**. Hosted Windows proved the required WPF runtime semantic.

Earlier rejected diagnostic heads remain non-authoritative failures and do not manufacture PASS. In particular, the initial sandbox omitted Windows machine paths used by NuGet discovery; the accepted head preserves only repository-owned fixed inheritance of `ProgramFiles*`/`ProgramData` for the WPF toolchain while user/project environment injection remains rejected.

## Final documentation state

Recording the evidence above changes repository bytes. Therefore this document does **not** authorize merge by itself: the resulting final documentation head must receive a fresh exact-head R0 + full Python Core + KodeStudio UI Smoke + R12 WPF Acceptance quartet before PR merge with `expected_head_sha`.

## Merge / normalization rule

After final documentation head acceptance, merge with `expected_head_sha`, then perform exactly one continuity-only post-merge normalization and gate that exact normalization head with the same four workflows. R12.6 remains forbidden until the normalization merges.
