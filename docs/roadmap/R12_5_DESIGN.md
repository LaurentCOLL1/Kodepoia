# R12.5 — WPF/.NET desktop adapter design

## Scope

R12.5 maps the framework-neutral R12.4 logical application contract to a deterministic WPF/.NET fixture and proves its Windows build/test bridge without extending scope into WinUI, packaging or installers.

Manual intervention: **CONDITIONAL** only if authoritative Windows runtime behavior required by acceptance cannot be demonstrated by the accepted GitHub Windows runner/toolchain evidence.

## Boundaries

- WPF is Windows-only and targets `net10.0-windows` with `UseWPF=true`.
- The adapter consumes `DesktopAppModel.conformance_projection(DesktopFramework.WPF)`; Project DNA/KodeProduct remain framework-neutral authorities.
- Toolchain discovery is explicit. Missing `dotnet` is `UNAVAILABLE`; pre-.NET-10 SDK is `UNSUPPORTED`; a failed probe/build/runtime harness is `FAILED`.
- `dotnet` is validated by `DesktopToolchainBoundary` and executed only through `ProcessSandbox`/KillSwitch with fixed repository-owned argv.
- No project/model text supplies executable paths, MSBuild properties, configuration names, environment overrides or shell strings.
- CI setup may provision the accepted .NET SDK. Kodepoia runtime itself does not install SDKs.
- Fixture source contains no third-party NuGet package. Restore only materializes SDK/framework assets required by .NET/WPF.
- Build products are redirected to `.kodepoia` staging and represented by path/size/SHA-256 artifact evidence.

## Real acceptance fixture

The repository-owned fixture contains:

1. a WPF `WinExe` using XAML, `Application` and `Window`;
2. a WPF STA harness that loads `PresentationFramework`, creates an `Application`, dispatcher and `Window`, binds the exact R12.4 logical-model digest as `DataContext`, then emits a deterministic sentinel;
3. deterministic Release builds and a parsed runtime sentinel;
4. toolchain identity including the `dotnet` executable SHA-256 and SDK version.

The adapter cannot report `AVAILABLE` with `build_ready`, `test_ready` and `runtime_smoke_ready` until all of those operations succeed.

## External compatibility note

Microsoft documents that `UseWPF=true` imports the .NET Desktop SDK and that WPF projects target Windows. Microsoft also documents WPF compilation through MSBuild. These upstream facts are compatibility evidence only; exact-head repository acceptance remains authoritative.
