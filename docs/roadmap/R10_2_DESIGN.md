# R10.2 — Headless bpy runner, capability probe + real-runtime acceptance

## Status

Hosted implementation candidate. Manual intervention: **REQUIRED** before merge.

## Execution boundary

`BlenderRunner` is backed by the accepted R1 `ProcessSandbox`. It stages one Kodepoia-owned static probe bootstrap and a machine-readable job document inside an empty project-confined workspace. The executable is validated by the accepted R10.1 boundary and the argv remains fixed: background, factory startup, autoexec disabled, offline mode, non-zero Python exit code, one staging-root Python bootstrap.

The probe bootstrap contains no `exec`, `eval`, subprocess, socket, URL/client or add-on installation surface. It imports Blender `bpy`/`bmesh`, creates one tiny cube mesh through the data API, saves one temporary `.blend`, exports one GLB, hashes both, atomically writes a result envelope, and exits 0 only for probe success.

The production runner drains stdout/stderr while retaining only bounded prefixes, propagates timeout/global KillSwitch cancellation, requires a bounded UTF-8 JSON result, verifies exact artifact filenames and SHA-256/byte sizes, and never promotes R10.2 probe artifacts to R8 Vault.

## Acceptance evidence

Canonical local evidence intentionally excludes username, hostname, home path, executable path, arbitrary environment values and Blender preferences. It binds:

- exact R10.2 source SHA;
- Blender version + Python version + OS/machine class;
- executable SHA-256;
- fixed command-policy/bootstrap digest;
- background/offline/glTF/bmesh facts;
- tiny scene counts;
- `.blend` and GLB SHA-256/byte sizes;
- return code, timeout/cancel/crash/OOM and bounded-output facts;
- explicit `status` and `blockers`.

## Upstream compatibility evidence

Official Blender 5.2 LTS documentation checked on 2026-08-23 confirms the command-line background/factory/autoexec/offline/Python-exit-code controls and documents glTF 2.0 as enabled by default. These sources are compatibility evidence only; the REQUIRED local probe remains authoritative for the user's actual runtime.

## Manual boundary

Hosted fake-runner tests certify Kodepoia's orchestration and hostile-result behavior but cannot certify an actual Blender executable. After hosted exact-head gates succeed and the candidate is frozen, the user must run the one `python -m kodepoia.cli r10-blender-accept ...` command documented in `R10_2_ACCEPTANCE.md`. R10.3 remains forbidden until reviewed local evidence is accepted and R10.2 is merged + normalized.
