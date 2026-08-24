# R12.6 — WinUI 3 / Windows App SDK adapter design

## Frozen scope

R12.6 maps the shared R12 desktop/MVVM model to a governed WinUI 3 / Windows App SDK Windows adapter. It does not change R1–R11 architecture and does not replace R12.5 WPF.

Base normalized `main`: `f84762085282eccc2e2c26ee1c0ccf62fbdfcf49`.
Branch: `r12/6-winui3-windows-app-sdk`.
Manual intervention: **CONDITIONAL** only if hosted Windows CI cannot prove the required WinUI/Windows App SDK build/runtime/deployment semantic.

## Upstream compatibility baseline

- Microsoft documents WinUI 3 as part of the Windows App SDK and distinct from UWP.
- Current command-line guidance uses .NET 10 and `dotnet new winui` templates.
- Windows 10 build 17763 is the minimum documented OS baseline.
- Packaged, packaged-with-external-location and unpackaged modes have distinct identity/runtime/deployment semantics.
- The repository-owned acceptance uses Windows App SDK `1.8.260804001` and the documented C# WinUI dotnet-new template package pinned in CI setup. Kodepoia runtime itself does not install either dependency.

## Contracts

`WinUiDeploymentContract` is durable, canonical and schema-backed. It records:

- stable package name;
- bounded `CN=` publisher identity;
- four-part package version;
- deployment mode: packaged MSIX, unpackaged framework-dependent or unpackaged self-contained;
- minimum Windows build.

The canonical runtime fixture selects **unpackaged self-contained** mode so hosted acceptance does not require Developer Mode, MSIX deployment, signing keys or a production certificate. Packaged identity metadata is still rendered and validated deterministically as `Package.appxmanifest` evidence; R12.14 remains authoritative for installer/signing semantics.

## Capability model

`WinUi3Adapter.discover_toolchain()` separates:

1. Windows OS availability;
2. bounded `dotnet` identity and SHA-256;
3. .NET 10 minimum compatibility;
4. `dotnet new winui` template availability;
5. Windows App SDK restore/build/runtime capability.

Generic `dotnet` presence alone can never produce `AVAILABLE`. Missing templates report `UNAVAILABLE`; old SDK reports `UNSUPPORTED`; failed restore/build/runtime remains `FAILED`.

## Build/runtime evidence

The repository-owned fixture contains:

- deterministic WinUI app project with `UseWinUI=true`;
- exact Windows App SDK package pin;
- explicit `WindowsPackageType=None` and `WindowsAppSDKSelfContained=true`;
- canonical shared logical-model digest in the generated window;
- deterministic package identity manifest;
- separate runtime probe loading `Microsoft.WinUI` and proving `Microsoft.UI.Xaml.Application` and `Microsoft.UI.Xaml.Window` are present at runtime.

All `dotnet` execution goes through `ProcessSandbox` and the global KillSwitch. Restore/build argv is Kodepoia-owned. Only fixed non-secret Windows machine path variables required by .NET/NuGet are inherited; project/model/user text cannot inject executable paths, MSBuild properties, raw argv or environment variables.

## CI provisioning boundary

The GitHub workflow may provision the documented WinUI template package and .NET SDK as CI infrastructure. This does not make runtime auto-installation a Kodepoia capability. Passive capability probing never installs templates, Windows App SDK runtimes, Visual Studio workloads, Developer Mode or certificates.

## Rollback / failure semantics

- generated fixture and build products remain under `.kodepoia` staging;
- failures do not promote artifacts;
- `UNAVAILABLE`, `UNSUPPORTED` and `FAILED` remain distinct from PASS;
- diagnostics are bounded and uploaded on failure;
- no manual step is requested unless hosted CI cannot establish the frozen acceptance claim.
