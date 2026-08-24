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

## Accepted implementation candidate

Branch: `r12/4-desktop-app-contracts`.
Base normalized `main`: `1f52adffedb69384904a4b35bb32e45e06b05e33`.
Accepted implementation head: `d55b55feedcfc638e1e11d194d12f80b8f7b6f9c`.

- R0 Repository Guard #1484 / `32779332770` — **SUCCESS**.
- Python Core #1458 / `32779332780` — **SUCCESS**, including Ubuntu/Windows pytest, package builds and internal KodeStudio smoke.
- KodeStudio UI Smoke #1425 / `32779332799` — **SUCCESS**.
- Manual state: **NONE**.

This evidence update changes bytes after the accepted implementation candidate. The resulting final documentation head requires a fresh exact-head R0 + full Python Core + KodeStudio UI Smoke triplet before expected-SHA merge. No synthetic PASS is permitted.

## Merge / normalization rule

After final documentation head acceptance, merge PR #193 with `expected_head_sha`, then create exactly one continuity-only post-merge normalization. R12.5 remains forbidden until that normalization passes the exact-head triplet and merges.
