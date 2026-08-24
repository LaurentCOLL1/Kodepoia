# Kodepoia — R12.1 Desktop contracts and secure toolchain boundaries

**Phase:** R12.1  
**Status:** IMPLEMENTED CANDIDATE  
**Manual intervention:** NONE  
**Base normalized main:** `f82444fa4c7018409bb0bdf83456b2cebd683e7e`

## Scope

R12.1 establishes the framework-neutral desktop contract layer required by R12.2–R12.16. It does not scaffold, restore, compile, test, package or launch a desktop application. Concrete WPF, WinUI 3, Avalonia, Qt 6 and Tauri v2 adapters remain reserved for R12.5–R12.9.

## Delivered contracts

- `DesktopFramework`: `wpf`, `winui3`, `avalonia`, `qt6`, `tauri2`.
- `DesktopOS`: Windows, Linux, macOS.
- `DesktopArchitecture`: x64, arm64, x86.
- `DesktopPackageKind`: unpackaged, MSIX, MSI, archive.
- `DesktopToolKind`: dotnet, MSBuild, CMake, Qt paths, Cargo and rustc.
- `DesktopCapabilityState`: `NOT_PROBED`, `AVAILABLE`, `UNAVAILABLE`, `UNSUPPORTED`, `BLOCKED`, `FAILED`.
- `DesktopTargetProfile` with deterministic validation and canonical SHA-256 identity.
- `DesktopToolchainIdentity` bound to executable digest, version, platform, architecture and normalized capabilities.
- `DesktopCapabilityReport` with fail-closed state/evidence rules: `AVAILABLE` requires a toolchain identity and may not contain blockers; unavailable/unsupported/blocked/failed states require blockers.

## Secure boundary

`DesktopToolchainBoundary` is a validation/argv-construction layer in front of the existing R1 `ProcessSandbox`; it never launches a process itself.

It provides:

- configured runtime-root containment;
- strict executable basename allowlists per tool kind;
- real-file resolution before accepting an executable;
- project-file containment and suffix allowlists;
- staging-root containment for outputs;
- bounded environment overrides restricted to `KODEPOIA_RUN_ID`, `TEMP`, `TMP`;
- fixed probe argv for every accepted tool kind;
- fixed, typed dotnet build/test argv;
- fixed CMake build argv;
- fixed Cargo check/build/test argv with `--locked --offline` and an explicit target directory.

No API accepts a shell command string, raw argv list, arbitrary MSBuild property, arbitrary CMake flag, Cargo flag, executable basename or unrestricted environment map.

Actual execution in later subdivisions MUST pass the already-validated argv to the existing `ProcessSandbox`, which remains authoritative for `shell=False`, working-directory containment and KillSwitch registration.

## Determinism and evidence

Durable identities use canonical JSON (`sort_keys=True`, compact separators, UTF-8, `allow_nan=False`) and SHA-256. Stable identifiers and report list sizes are bounded. Duplicate targets/capabilities/blockers normalize deterministically.

Strict Draft 2020-12 schemas are provided for target profiles and capability reports. Both reject unknown properties.

## Security invariants

R12.1 fails closed for:

- traversal and project/staging root escape;
- executable substitution or executable outside configured runtime roots;
- forbidden environment overrides such as `PATH`, `DOTNET_ROOT`, `RUSTFLAGS`, proxy/secret variables or arbitrary keys;
- raw operation/configuration substitution;
- false `AVAILABLE` reports without toolchain evidence;
- invalid Windows-only WPF/WinUI target combinations;
- invalid package/OS combinations;
- non-finite canonical data.

## Upstream compatibility baseline

Official upstream documentation is compatibility context only and never overrides Kodepoia governance. R12.1 intentionally does not hard-code mutable SDK/package releases: later adapters must capability-probe exact installed identities.

- Microsoft documents WinUI 3 / Windows App SDK as the recommended native platform for new Windows desktop applications; WPF remains a supported .NET desktop framework.
- Avalonia, Qt and Tauri adapter-specific requirements are frozen only in their respective subdivisions.

## Out of scope

Project DNA evolution (R12.2), scaffolding (R12.3), MVVM (R12.4), concrete framework adapters (R12.5–R12.9), SQLite (R12.10), async (R12.11), IPC (R12.12), accessibility/localization/DPI (R12.13), packaging/update (R12.14), CLI/KodeStudio desktop UX (R12.15) and integrated acceptance (R12.16).
