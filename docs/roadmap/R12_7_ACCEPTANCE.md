# R12.7 — Acceptance

## Scope

Avalonia cross-platform desktop adapter with platform-partitioned Windows/Linux/macOS evidence.

Manual intervention: **CONDITIONAL**. Trigger only if a platform runtime claim required by the frozen acceptance cannot be proven by the selected hosted CI target.

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

## Evidence state

Base normalized `main`: `47ca9463015d652ead0b21a2e9a7030377a0c695`.
Branch: `r12/7-avalonia-cross-platform`.

Exact implementation SHA and workflow run IDs are **PENDING** until the branch is frozen and independently gated. A partial OS matrix cannot be promoted to accepted cross-platform evidence.

## Merge / normalization rule

After accepted evidence is recorded, re-gate the resulting final documentation head with R0 + Python + UI + complete Avalonia matrix. Merge with `expected_head_sha`, then perform exactly one continuity-only post-merge normalization and gate that exact head with the same acceptance set. R12.8 remains forbidden until normalization merges.
