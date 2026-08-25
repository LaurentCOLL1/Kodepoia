# R12.9 — Acceptance

## Scope

Tauri v2 / Rust MSVC / Windows WebView2 desktop adapter with exact dependency lock, default-deny IPC policy and real runtime evidence.

Manual intervention: **CONDITIONAL / NOT TRIGGERED**. Hosted Windows CI proved the required Rust/MSVC/Tauri/WebView2 build/runtime semantic on an immutable candidate SHA, so no local/manual gate is required.

## Required acceptance

- deterministic projection from the shared R12.4 logical model;
- exact `tauri = 2.11.5` and `tauri-build = 2.6.3` declarations;
- plain static frontend only; no Node package manager, development server or remote frontend URL;
- empty Tauri capability set, `withGlobalTauri=false`, no plugins/custom IPC commands and restrictive CSP;
- no MSI/NSIS/MSIX/bundle target in R12.9;
- Cargo and rustc discovered separately and SHA-256 identified;
- Rust host must be x86_64 Windows MSVC for hosted acceptance;
- Cargo.lock generated/fetched only as CI infrastructure, then exact Tauri versions validated;
- authoritative build executes through Kodepoia as `cargo build --locked --offline` with target output bounded under staging;
- runtime executable must initialize configured `main` WebView, report Tauri runtime version and a non-empty system WebView2 version through public Tauri APIs, emit the source-bound sentinel and exit successfully;
- staged artifacts are SHA-256 inventoried;
- dependencies remain `REVIEW_REQUIRED` and no redistribution right is inferred;
- exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke + `R12 Tauri2 Acceptance` all succeed;
- WPF, WinUI, Avalonia and Qt acceptance workflows remain green as regression evidence when triggered by the PR.

## Accepted implementation evidence

Base normalized `main`: `1cd32eb0cf78dbf468a9921955bbc8695cedab89`.
Branch: `r12/9-tauri2-rust-webview2-adapter`.
PR: `#203`.
Accepted implementation SHA: `2664b65903e3f9dc1399bbbfad10cac772ce5b75`.

Exact-head workflow matrix on `2664b65903e3f9dc1399bbbfad10cac772ce5b75`:

- R0 Repository Guard `#1537`: **SUCCESS**;
- Python Core `#1511`: **SUCCESS** on Linux and Windows;
- KodeStudio UI Smoke `#1478`: **SUCCESS**;
- R12 Tauri2 Acceptance `#12`, run `32814261183`: **SUCCESS**;
- R12 Qt6 Acceptance `#21`: **SUCCESS**;
- R12 WPF Acceptance `#40`: **SUCCESS**;
- R12 WinUI3 Acceptance `#30`: **SUCCESS**;
- R12 Avalonia Acceptance `#26`: **SUCCESS**.

The hosted Windows Tauri artifact is `r12-9-tauri2-windows-2664b65903e3f9dc1399bbbfad10cac772ce5b75`, artifact id `9551033181`, artifact ZIP digest `sha256:67e49aba4a1bb99d9f93e0ad2a13beb3d636a63bf2f6a29287e345974169d407`.

Authoritative runtime/build evidence extracted from `R12_9_TAURI_WINDOWS.json`:

- source SHA: `2664b65903e3f9dc1399bbbfad10cac772ce5b75`;
- adapter state: `AVAILABLE`, blockers `[]`;
- platform / architecture: `windows` / `x64`;
- host triple: `x86_64-pc-windows-msvc`;
- Cargo: `cargo 1.97.1 (c980f4866 2026-06-30)`;
- rustc: `rustc 1.97.1 (8bab26f4f 2026-07-14)`;
- Tauri: `2.11.5`;
- WebView2: `131.0.2903.86`;
- Cargo.lock SHA-256: `1025ee09c818d223e81c58cc1bba32db857b15ce149bcee0f933bb9974bd53b1`;
- capability-policy SHA-256: `de488b31c09f30a7c7b710569b5c7a959d715f27ccd0abf17fea994f35a4f99c`;
- kit SHA-256: `7465b5e24d8eaa7e11a12c330a969523272e4dd163cfe9bdfee3887d5ef35c28`;
- logical model SHA-256: `3feb7493c8fa969e638bb9c4454161edea8d1f36f49f2f93a72a99c3b4ca0da0`;
- project manifest SHA-256: `37692d5887a7b4df6d49b8e93d606a1f2116eb5b9a727ea0ef3fbebf4802e3b7`;
- deterministic `icons/icon.ico` SHA-256: `6462dd1dac9c5e4da7beeee3803393e019557123583d736a67ef3c3b508ff47f`;
- built fixture executable SHA-256: `a2e0c8cff11a182a49fd52990a68abcd29f4810bb137a171edc15a0dadf70e7f`;
- build return code: `0`;
- runtime return code: `0`;
- runtime sentinel: `KODEPOIA_TAURI2_RUNTIME_PASS:3feb7493c8fa969e638bb9c4454161edea8d1f36f49f2f93a72a99c3b4ca0da0:2.11.5:131.0.2903.86`.

Dependency evidence remains fail-closed: `tauri 2.11.5` and `tauri-build 2.6.3` are both `REVIEW_REQUIRED`, with `redistribution_rights_inferred=false`.

## Final documentation gate / merge rule

This evidence recording changes repository bytes. The resulting final documentation head MUST therefore pass the complete exact-head gate matrix again before PR #203 is merged with `expected_head_sha`.

After that merge, perform exactly one continuity-only post-merge normalization, gate its exact head, and merge it. R12.10 remains forbidden until that normalization is merged.
