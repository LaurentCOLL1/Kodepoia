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

## Evidence state

Branch: `r12/5-wpf-dotnet-adapter`.
Base normalized `main`: `180a507a81c979ec797f3bafe3de29ba38b72c94`.

Exact implementation SHA and workflow run IDs are **PENDING** until the candidate is frozen and independently gated. A missing WPF gate cannot be replaced by unit-test evidence.

## Merge / normalization rule

After accepted evidence is recorded, any documentation-only head change must be re-gated with the same standard gates and WPF gate. Merge with `expected_head_sha`, then perform exactly one continuity-only post-merge normalization and gate that exact normalization head. R12.6 remains forbidden until the normalization merges.
