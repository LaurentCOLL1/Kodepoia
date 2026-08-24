# R12.6 — Acceptance

## Scope

WinUI 3 / Windows App SDK adapter + Windows identity/deployment bridge.

Manual intervention: **CONDITIONAL / NOT TRIGGERED**. Accepted hosted Windows CI proved the required build/runtime/deployment semantic; no local action is required.

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

## Accepted implementation evidence

Base normalized `main`: `f84762085282eccc2e2c26ee1c0ccf62fbdfcf49`.
Branch: `r12/6-winui3-windows-app-sdk`.
PR: #197.
Accepted implementation head: `b990a613d6becbc80e637ea0184f87b502573b74`.

- R0 Repository Guard #1502 / `32786054869` — **SUCCESS**.
- Python Core #1476 / `32786054919` — **SUCCESS**, including Ubuntu/Windows pytest, UI subjob and package builds.
- KodeStudio UI Smoke #1443 / `32786054865` — **SUCCESS**.
- R12 WPF Acceptance #11 / `32786054841` — **SUCCESS** inherited regression gate.
- R12 WinUI3 Acceptance #1 / `32786054895` — **SUCCESS**.

Hosted Windows installed the Microsoft-documented WinUI dotnet-new template package as CI infrastructure, detected .NET 10, restored exact `Microsoft.WindowsAppSDK` `1.8.260804001`, built the canonical WinUI fixture, validated deterministic package/deployment metadata, loaded the WinUI runtime and uploaded SHA-256 artifact evidence. Developer Mode, runtime/workload installation by Kodepoia and production signing were not required.

Recording this evidence changes repository bytes. The resulting final documentation head must receive fresh exact-head R0 + Python + UI + WinUI gates before merge.

## Merge / normalization rule

Merge PR #197 only after the final documentation head passes the fresh quartet, using `expected_head_sha`. Then perform exactly one continuity-only post-merge normalization and gate that exact normalization head with R0 + Python + UI + WinUI before merge. R12.7 remains forbidden until the normalization merges.
