# R12.15 — CLI + KodeStudio Desktop workspace design

## Status

Implementation subdivision. Manual intervention: **NONE**.

Base normalized `main`: `089e54cdbd1ac344ce71fc92eef213ad2e9589d3`.
Dedicated branch: `r12/15-cli-kodestudio-desktop`.

## Objective

Expose the accepted R12 desktop contracts through bounded user-facing intents without adding an arbitrary command surface. The Project Wizard remains authoritative for desktop intent; the Desktop workspace consumes its persisted Project DNA rather than creating a second project model.

## CLI contract

`kodepoia r12` contains exactly these operation subcommands:

- `status`
- `scaffold`
- `validate`
- `build`
- `test`
- `package`

Each accepts only `--project <root>`. No executable path, raw argv, shell command, compiler property, CMake/Cargo flag, package-manager script, SQL, certificate, signing key or update credential is accepted.

Every invocation emits one versioned JSON object matching `schemas/r12/desktop-workspace-result.schema.json`. Exit code `0` means `ready`/`pass`; blocked, failed or cancelled execution returns `2`.

## Passive refresh boundary

`DesktopWorkspaceService.status()` is intentionally incapable of launching a process. It reads only:

- `.kodepoia/project.yaml` produced by the existing Project Wizard/initializer;
- fixed, bounded evidence paths under `.kodepoia/desktop/evidence/{build,test,package}.json`.

Evidence files are read-only observations. A textual `"status": "pass"` inside such a file is surfaced only as `reported_status`; it cannot convert the workspace result into `PASS`. Symlinked, escaping, oversized or malformed evidence fails closed as unavailable evidence.

`validate()` validates Project DNA only and also launches no process.

## Explicit execution boundary

`scaffold`, `build`, `test` and `package` are explicit operations. They require a trusted injected `DesktopWorkspaceExecutor`. Without one they return `BLOCKED` with `EXECUTION_BACKEND_UNAVAILABLE`; Kodepoia does not improvise a command or silently restore/install a dependency.

The executor receives only a typed operation enum and a typed context derived from accepted Project DNA. The global R1 KillSwitch is checked before the executor is called. If active, execution returns `CANCELLED` and the backend is never invoked.

R12.16 may inject the accepted end-to-end Windows executor/evidence path into this interface; R12.15 itself does not manufacture toolchain availability.

## KodeStudio workspace

KodeStudio receives a dedicated **Desktop** navigation page. It displays:

- Project Wizard-derived project name/framework/architecture/package intent;
- workspace state and blockers;
- read-only structured build/test/package evidence;
- explicit Refresh, Validate, Scaffold, Build, Test, Package and Cancel actions.

Initial page population and Refresh call only `status()`. The evidence widget is read-only. Explicit execution buttons use the same typed service as the CLI. Cancel triggers the global KillSwitch.

## Accessibility and localization

All new controls have stable object names and accessible names/descriptions through the existing `mark_accessible` helper. R12 has its own source catalog and `qps-ploc` pseudo-localized catalog using the accepted R6 localization infrastructure. Keyboard focus remains on standard Qt push buttons and read-only text controls.

## Security invariants

- no shell-string execution;
- no raw process/property/flag surface;
- no passive external probes;
- no mutable PASS checkbox or editable evidence field;
- no model/project text promoted into executable data;
- no signing secret surface;
- no hidden restore/install/network activity;
- Project DNA must resolve to a regular file inside the chosen project root;
- evidence is bounded and non-authoritative until an accepted executor/integrated verifier binds it.

## Rollback

R12.15 adds typed user-facing surfaces only. Removing `workspace.py`, `r12_cli.py`, the R12 KodeStudio page/localization/schema/tests, and the two integration registrations restores the prior accepted user surface without changing R1–R14 durable project data.
