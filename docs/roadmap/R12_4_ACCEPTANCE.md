# R12.4 — Acceptance

## Scope

Framework-neutral desktop MVVM/state/navigation/command/service contracts only.

Manual intervention: **NONE**.

## Required acceptance

- canonical sample logical model serializes/digests deterministically;
- strict schema validates canonical model;
- construction ordering does not change logical serialization;
- duplicate route paths, dangling refs and route-parent cycles fail closed;
- invalid/raw command operations and non-boolean can-execute state fail closed;
- service dependency cycles and lifetime-capture conflicts fail closed;
- deterministic disposal order releases dependents before dependencies;
- validation rules are type-compatible;
- all five frozen R12 adapter projections preserve one equivalent logical signature;
- no framework objects/toolchains/processes are introduced;
- exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke all succeed.

## Evidence state

Branch: `r12/4-desktop-app-contracts`.
Base normalized `main`: `1f52adffedb69384904a4b35bb32e45e06b05e33`.
Manual: **NONE**.

Exact implementation and final-documentation SHA/run IDs remain **PENDING** until an immutable candidate is independently gated.

## Merge / normalization rule

After final documentation head acceptance, merge the R12.4 PR with `expected_head_sha`, then create exactly one continuity-only post-merge normalization. R12.5 remains forbidden until that normalization passes the exact-head triplet and merges.
