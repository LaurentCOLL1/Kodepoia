# R12.9 — Acceptance

## Scope

Tauri v2 / Rust MSVC / Windows WebView2 desktop adapter with exact dependency lock, default-deny IPC policy and real runtime evidence.

Manual intervention: **CONDITIONAL**. Trigger only if accepted hosted Windows CI cannot prove the required Rust/MSVC/Tauri/WebView2 build/runtime semantic for an immutable candidate SHA.

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

## Evidence state

Base normalized `main`: `1cd32eb0cf78dbf468a9921955bbc8695cedab89`.
Branch: `r12/9-tauri2-rust-webview2-adapter`.

Exact implementation SHA and workflow run IDs are **PENDING** until the branch is frozen and independently gated. Unit tests cannot replace the real hosted Windows Tauri/WebView2 runtime gate.

## Merge / normalization rule

After accepted evidence is recorded, re-gate the resulting final documentation head with R0 + Python + UI + Tauri. Merge with `expected_head_sha`, then perform exactly one continuity-only post-merge normalization and gate that exact head with the same required acceptance set. R12.10 remains forbidden until normalization merges.
