# R12.6 — Acceptance

## Scope

WinUI 3 / Windows App SDK adapter + Windows identity/deployment bridge.

Manual intervention: **CONDITIONAL**. Trigger only if accepted hosted Windows CI cannot prove the required WinUI build/runtime/deployment semantic for an immutable candidate SHA.

## Required acceptance

- shared R12.4 canonical model maps deterministically to WinUI 3 source;
- Windows-only target and .NET 10 minimum are explicit;
- WinUI template capability is probed separately from generic `dotnet` presence;
- Windows App SDK dependency is exact-version pinned;
- package name, publisher, four-part version, minimum OS and deployment mode are schema-backed and deterministic;
- packaged/unpackaged/self-contained intent remains structural data rather than raw MSBuild arguments;
- ordinary development acceptance requires no production certificate/private key;
- acceptance does not enable Developer Mode or install workloads at Kodepoia runtime;
- repository-owned canonical fixture restores and builds on accepted hosted Windows;
- runtime probe loads the WinUI runtime and proves `Microsoft.UI.Xaml.Application` and `Microsoft.UI.Xaml.Window` availability;
- manifest/package identity metadata validates deterministically;
- missing template/SDK/package capability reports `UNAVAILABLE`/`UNSUPPORTED`/`FAILED`, never PASS;
- project/property/argv/environment injection paths fail closed;
- staged artifacts receive SHA-256 manifest evidence;
- exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke + `R12 WinUI3 Acceptance` all succeed.

## Evidence state

Base normalized `main`: `f84762085282eccc2e2c26ee1c0ccf62fbdfcf49`.
Branch: `r12/6-winui3-windows-app-sdk`.

Exact implementation SHA and workflow run IDs are **PENDING** until the candidate is frozen and independently gated. A missing WinUI gate cannot be replaced by Python unit tests.

## Merge / normalization rule

After accepted implementation evidence is recorded, any resulting documentation head is re-gated with R0 + Python + UI + WinUI. Merge with `expected_head_sha`, then perform exactly one continuity-only post-merge normalization and gate that exact normalization head with the same quartet. R12.7 remains forbidden until the normalization merges.
