# R12.8 — Acceptance

## Scope

Qt 6 / CMake desktop adapter with explicit Qt/CMake/compiler kit identity and license/BOM state.

Manual intervention: **CONDITIONAL / NOT TRIGGERED**. Accepted hosted CI proved the required Qt/compiler build/runtime semantic for the immutable implementation candidate.

## Required acceptance

- deterministic mapping from the shared R12.4 logical model;
- generated project requires CMake 3.22, C++17 and only Qt `Core` + `Widgets`;
- generated resource manifest embeds and runtime-verifies the shared logical-model SHA-256;
- CMake and Qt identities are probed separately and missing/incompatible tools never become PASS;
- Qt root comes only from the discovered `qtpaths` installation;
- fixed CMake generator/architecture/cache argv; raw generator, toolchain, compiler, path and environment injection remains closed;
- CMake-selected compiler ID/version/path is captured after configure and the compiler executable is SHA-256 identified;
- Qt dependency/BOM declarations are exact-version and explicitly `REVIEW_REQUIRED`; no redistribution right is inferred;
- canonical repository-owned fixture configures and builds with a real supported Qt/CMake/compiler toolchain on accepted hosted CI;
- runtime probe links Qt Widgets, validates the embedded resource/model digest and reports the actual Qt runtime version without claiming interactive rendering;
- staged build artifacts are SHA-256 inventoried;
- exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke + `R12 Qt6 Acceptance` all succeed;
- prior WPF/WinUI/Avalonia acceptance workflows remain green as regression evidence on the candidate when they are triggered by the PR.

## Accepted implementation evidence

Base normalized `main`: `306d0b6fafb6d8c9c069936799e0c82bf94be1c7`.
Branch: `r12/8-qt6-cmake-adapter`.
PR: #201.

Accepted implementation candidate: `7d59d1e1320f18f0173d4df0374b174075b8d3fa`.

Exact-head workflow evidence:

- R0 Repository Guard #1519 / `32791617782` — **SUCCESS**;
- Python Core #1493 / `32791617851` — **SUCCESS**;
- KodeStudio UI Smoke #1460 / `32791617772` — **SUCCESS**;
- R12 Qt6 Acceptance #5 / `32791617789` — **SUCCESS**;
- R12 Avalonia Acceptance #10 / `32791617798` — **SUCCESS**;
- R12 WPF Acceptance #24 / `32791617714` — **SUCCESS**;
- R12 WinUI3 Acceptance #14 / `32791617839` — **SUCCESS**.

Qt #5 accepted a real hosted macOS ARM64 toolchain provisioned through the account-free package-manager path documented by Qt. Evidence reports:

- Qt `6.11.1`, `qtpaths6` SHA-256 `aadcdd6c51d3ece0f0b2979003e6331c8d42e165581a26c64c8a9ae852ad2a29`;
- CMake `4.4.0`, Ninja generator;
- AppleClang `21.0.0.21000101`, compiler executable SHA-256 `179301dcb41ea78accc3fa0048a7e6f6710d891945a751a34addd622020c1818`;
- kit semantic digest `9b8fafd5af74d5c41381ebe7df9f31627e24882fc809f982532fe4859839b272`;
- configure/build/runtime return codes all `0`;
- runtime sentinel `KODEPOIA_QT6_RUNTIME_PASS:3feb7493c8fa969e638bb9c4454161edea8d1f36f49f2f93a72a99c3b4ca0da0:6.11.1`;
- Core/Widgets declarations remain `REVIEW_REQUIRED` and `redistribution_rights_inferred=false`.

Two earlier CI-provisioning approaches were rejected before Kodepoia execution: unofficial archive metadata/mirror discovery could not establish Qt 6.11.2, and the official Windows Online Installer required Qt Account/license credentials on the hosted runner. They are not accepted evidence and did not trigger manual intervention because the supported account-free macOS package-manager path successfully established the frozen Qt/CMake/compiler semantic.

## Merge / normalization rule

Recording the accepted candidate changes repository bytes. The resulting final documentation head must therefore receive fresh exact-head R0 + Python + UI + Qt acceptance before PR #201 is merged with `expected_head_sha`. Then perform exactly one continuity-only post-merge normalization and gate that exact head with the same required acceptance set. R12.9 remains forbidden until normalization merges.
