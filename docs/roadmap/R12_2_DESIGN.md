# Kodepoia — R12.2 Desktop Project DNA and Project Wizard

**Subdivision:** R12.2  
**Manual intervention:** NONE  
**Base normalized main:** `d0c97b89a49a0bb3a49761a0ccf46ac755c3a1e8`

## Purpose

Extend the existing R2 Project DNA, KodeProduct and KodeStudio Project Wizard with explicit desktop application intent. R12.2 does not create a second wizard and does not generate source code or invoke a desktop toolchain.

## Project DNA compatibility

`ProjectDNA.schema_version` remains `1`. A new optional `desktop` profile carries framework, architecture, package intent and persistence/IPC/update decisions. When `desktop` is absent, `to_dict()` omits the field entirely so pre-R12 schema-v1 projects load and serialize without silently gaining desktop intent.

New Wizard-created `desktop_app` projects always include an explicit profile. A desktop profile is rejected on non-desktop project types. With a profile present, targets are limited to Windows/Linux/macOS and the frozen R12.1 framework/package constraints are reused, including Windows-only WPF/WinUI and Windows-required MSI/MSIX.

## Existing Wizard extension

`kodepoia.kodestudio.r12_project_wizard.create_project_dialog()` decorates the existing `ProjectDialog` returned by the R2 wizard. It adds one accessible Desktop tab and reconnects the existing acceptance action so desktop projects flow through the same initializer.

Desktop controls:

- framework: WPF, WinUI 3, Avalonia, Qt 6, Tauri v2;
- architecture: x64, arm64, x86;
- package intent: unpackaged, MSIX, MSI, archive;
- persistence, local IPC and updates: yes/no/undecided.

The UI disables game-only fields through the existing adaptive logic and constrains desktop platform choices. WPF/WinUI select Windows only. Cross-platform frameworks may select Windows/Linux/macOS. Mobile/Web/XR/Steam Deck targets are disabled for desktop intent.

## KodeProduct mapping

Desktop Project DNA maps deterministically into six machine-readable product constraints and one reserved P0 requirement `DESKTOP-TARGET` with two acceptance criteria covering targets/framework/architecture and package/persistence/IPC/update intent. A conflicting user-created `DESKTOP-TARGET` fails closed.

## Out of scope

Source generation and template rendering are R12.3; MVVM is R12.4; concrete framework builds/runtimes are R12.5–R12.9. R12.2 performs no restore, install, build or process launch.
