# R12.8 — Acceptance

## Scope

Qt 6 / CMake desktop adapter with explicit Qt/CMake/compiler kit identity and license/BOM state.

Manual intervention: **CONDITIONAL**. Trigger only if accepted hosted CI cannot prove the required Qt/compiler build/runtime semantic for an immutable candidate SHA.

## Required acceptance

- deterministic mapping from the shared R12.4 logical model;
- generated project requires CMake 3.22, C++17 and only Qt `Core` + `Widgets`;
- generated resource manifest embeds and runtime-verifies the shared logical-model SHA-256;
- CMake and Qt identities are probed separately and missing/incompatible tools never become PASS;
- Qt root comes only from the discovered `qtpaths` installation;
- fixed CMake generator/architecture/cache argv; raw generator, toolchain, compiler, path and environment injection remains closed;
- CMake-selected compiler ID/version/path is captured after configure and the compiler executable is SHA-256 identified;
- Qt dependency/BOM declarations are exact-version and explicitly `REVIEW_REQUIRED`; no redistribution right is inferred;
- canonical repository-owned fixture configures and builds with a real supported Qt/CMake/MSVC toolchain on accepted hosted Windows;
- runtime probe links Qt Widgets, validates the embedded resource/model digest and reports the actual Qt runtime version without claiming interactive rendering;
- staged build artifacts are SHA-256 inventoried;
- exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke + `R12 Qt6 Acceptance` all succeed;
- prior WPF/WinUI/Avalonia acceptance workflows remain green as regression evidence on the candidate when they are triggered by the PR.

## Evidence state

Base normalized `main`: `306d0b6fafb6d8c9c069936799e0c82bf94be1c7`.
Branch: `r12/8-qt6-cmake-adapter`.

Exact implementation SHA and workflow run IDs are **PENDING** until the branch is frozen and independently gated. A Python mock/unit test cannot replace the real Qt compiler/build gate.

## Merge / normalization rule

After accepted evidence is recorded, re-gate the resulting final documentation head with R0 + Python + UI + Qt. Merge with `expected_head_sha`, then perform exactly one continuity-only post-merge normalization and gate that exact head with the same required acceptance set. R12.9 remains forbidden until normalization merges.
