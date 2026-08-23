# R10.1 — Blender contracts, runtime discovery + secure process boundary

## Status

Implementation candidate for the frozen R10.1 scope. Manual intervention: **NONE**.

## Boundary

R10.1 creates `kodepoia.blender3d` without launching Blender. The public contract contains only typed Blender operations and immutable evidence models. There is no `run_python`, arbitrary operator, arbitrary executable, arbitrary argv, arbitrary cwd/environment or URL surface.

`BlenderExecutableBoundary` accepts regular files named `blender`/`blender.exe` only when they remain under explicitly configured roots. Discovery is finite: explicit candidates plus platform-specific known Blender 5.2 locations. It never performs recursive disk search.

The generated future runner argv is owned by Kodepoia and fixes `--background`, `--factory-startup`, `--disable-autoexec`, `--offline-mode`, a non-zero `--python-exit-code`, and exactly one Kodepoia-owned `--python` script under the staging root. R10.1 only constructs/validates this argv; execution starts in R10.2 through `ProcessSandbox`.

Environment overrides are allowlisted and reject Python/Blender script-path injection. Embedded `.blend` Python is therefore not granted a path around the frozen R1/R7 trust boundaries.

## Version policy

The initial authoritative profile accepts Blender **5.2.x LTS** only. Other versions may be detected later but are `UNSUPPORTED` for authoritative R10 acceptance unless the frozen plan is amended.

Official compatibility inputs checked on 2026-08-23:

- Blender 5.2 LTS release/support window: https://www.blender.org/releases/5-2/
- command-line arguments: https://docs.blender.org/manual/en/5.2/advanced/command_line/arguments.html
- production/offline deployment guidance: https://docs.blender.org/manual/en/5.2/advanced/deploying_blender.html

External documentation is compatibility evidence only; it does not override Kodepoia governance.

## Identity and schemas

Canonical JSON is UTF-8, sorted-key, compact and rejects NaN/Infinity. SHA-256 digests bind recipe/runtime evidence. R10.1 introduces strict v1 schema roots for Blender capability evidence, job recipes, QA reports, export manifests and local acceptance evidence. Later subdivisions refine the currently empty QA/export/local payload roots without changing their v1 envelope identity silently.

## Security regression traps

- never add model-supplied `--python-expr`, `--python-text`, `--python-use-system-env` or `--addons`;
- never recursively search disks for Blender;
- never treat a filename/path as durable asset identity;
- never allow `PYTHONPATH`, `PYTHONHOME` or Blender user/system script-path injection;
- no real Blender process is permitted in R10.1.
