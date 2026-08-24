# R12.7 — Acceptance

## Scope

Avalonia cross-platform desktop adapter with platform-partitioned Windows/Linux/macOS evidence.

Manual intervention: **CONDITIONAL / NOT TRIGGERED**. Hosted CI established every selected platform claim.

## Required acceptance

- deterministic mapping from the shared R12.4 logical model;
- exact Avalonia `12.1.1` dependency identity and `net10.0` accepted target;
- durable target matrix contains only Windows/Linux/macOS and is deterministic;
- Windows/Linux/macOS evidence remains separately identified by OS and architecture;
- generic success on one OS never certifies another OS;
- canonical Avalonia application restores and builds on all three selected hosted CI targets;
- separate runtime probe loads `Avalonia.Application`, `Avalonia.Controls.Window` and `Avalonia.AppBuilder` on each selected target;
- no interactive native-window rendering claim is inferred from the runtime probe;
- mobile/browser targets cannot be silently injected;
- raw package/MSBuild/argv/executable/env injection surfaces remain closed;
- staged artifacts are SHA-256 inventoried per platform;
- missing/incompatible capability is explicit and cannot become PASS;
- exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke + the complete three-OS `R12 Avalonia Acceptance` matrix all succeed.

## Accepted implementation evidence

Base normalized `main`: `47ca9463015d652ead0b21a2e9a7030377a0c695`.
Branch: `r12/7-avalonia-cross-platform`.
PR: #199.
Accepted implementation head: `57432a90c439abbbbcc6a8b2de76dcd7d917b8a2`.

- R0 Repository Guard #1509 / `32787159628` — **SUCCESS**.
- Python Core #1483 / `32787159636` — **SUCCESS**.
- KodeStudio UI Smoke #1450 / `32787159647` — **SUCCESS**.
- R12 Avalonia Acceptance #2 / `32787159696` — **SUCCESS** on Windows, Ubuntu and macOS independently.
- WPF regression #16 / `32787159633` — **SUCCESS**.
- WinUI regression #6 / `32787159622` — **SUCCESS**.

The rejected predecessor `abbfa7677014b26fb60ecee335dec4a3a2f34488` exposed an overly strict internal assembly-name check on macOS. The accepted head validates public Avalonia type identities instead. macOS ARM64, Ubuntu and Windows all restored exact Avalonia `12.1.1`, built the canonical application and executed their platform-specific runtime probe. No manual platform evidence was required.

Recording this evidence changes repository bytes. Re-gate the resulting final documentation head with R0 + Python + UI + the complete Avalonia matrix before merge.

## Merge / normalization rule

Merge PR #199 only after the final documentation head passes the fresh acceptance set, using `expected_head_sha`. Then perform exactly one continuity-only post-merge normalization and gate that exact head with R0 + Python + UI + complete Avalonia matrix before merge. R12.8 remains forbidden until normalization merges.
