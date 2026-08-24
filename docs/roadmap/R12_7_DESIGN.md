# R12.7 — Avalonia cross-platform desktop adapter design

## Frozen scope

R12.7 maps the shared R12 desktop/MVVM contracts to an Avalonia desktop adapter while keeping evidence partitioned by operating system. It does not expand R12 into Android/iOS/browser targets.

Base normalized `main`: `47ca9463015d652ead0b21a2e9a7030377a0c695`.
Branch: `r12/7-avalonia-cross-platform`.
Manual intervention: **CONDITIONAL** only if a platform runtime claim required by acceptance cannot be established by hosted CI.

## Upstream compatibility baseline

- Avalonia is a cross-platform .NET UI framework supporting Windows, Linux and macOS desktop environments.
- R12.7 pins `Avalonia`, `Avalonia.Desktop` and `Avalonia.Themes.Fluent` to `12.1.1`.
- The upstream package supports .NET 8 and newer, including `net10.0`; R12.7 chooses `net10.0` as the accepted R12 build target rather than claiming .NET 10 is Avalonia's universal minimum.
- Broader Avalonia mobile/browser capabilities remain outside this R12 subdivision.

## Durable target matrix

`AvaloniaTargetMatrix` is canonical, digestible and backed by `schemas/r12/avalonia-target-matrix.schema.json`. Only `windows`, `linux` and `macos` values are accepted. Target order is normalized deterministically.

A platform PASS is never copied to another platform. Each acceptance JSON records current OS, architecture, toolchain identity, shared-model digest, matrix digest, exact Avalonia version and artifact hashes.

## Adapter and fixture

`AvaloniaAdapter`:

- discovers only a bounded `dotnet` executable;
- uses .NET 10 for the R12 accepted target;
- hashes the executable identity and records current OS/architecture;
- renders deterministic Avalonia app source from `canonical_sample_app()`;
- pins all Avalonia package references exactly;
- invokes restore/build through `ProcessSandbox` and KillSwitch;
- writes all outputs below `.kodepoia` staging.

The generated app contains Avalonia XAML application/window source and embeds the common logical-model SHA in the canonical window.

A separate console runtime probe references the same locked Avalonia packages and proves that `Avalonia.Application`, `Avalonia.Controls.Window` and `Avalonia.AppBuilder` assemblies/types load on the current OS. This is an **assembly/runtime availability** claim, not an interactive native-window-rendering claim.

## Cross-platform acceptance policy

The dedicated workflow runs the exact candidate on:

- `windows-latest`;
- `ubuntu-latest`;
- `macos-latest`.

Each job installs the accepted .NET 10 SDK as CI infrastructure, restores the exact packages, compiles the canonical Avalonia application and probe, executes the runtime probe and uploads a platform-specific evidence artifact.

If one OS fails while another succeeds, only the successful OS evidence remains successful; the matrix as a whole is not accepted until all selected targets pass.

## Security / failure boundaries

- no user/model raw executable path, `dotnet` argv, MSBuild property or package version surface;
- no mobile target injection;
- missing SDK/package/runtime remains `UNAVAILABLE`/`UNSUPPORTED`/`FAILED`, never PASS;
- CI dependency provisioning is distinct from Kodepoia runtime auto-installation;
- no interactive UI/runtime claim is manufactured from the assembly probe;
- any future interactive accessibility/window-manager claim belongs to its specific later acceptance seam.
