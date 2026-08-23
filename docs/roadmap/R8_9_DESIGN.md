# R8.9 — Godot 4.7 source/import bridge + rebuild verification — Design

## Frozen objective

Bridge R8 Vault source/derived semantics to the already accepted R5 Godot 4.7 execution boundary. Original source bytes and Vault/VCS identity remain authoritative; Godot generated import cache remains disposable derived state.

## Architecture

`GodotAssetBridge` is a typed R8 service over `WorkspaceBoundary` and a `GodotImportExecutor` protocol. Production execution is supplied by the accepted `KodeGodotExecutor`; the bridge never launches a process directly and exposes no Godot argv, executable, cwd, environment or host surface.

Only two structured R5 operations are required for rebuild:

- `kodegodot_engine_version`;
- `kodegodot_import_project` with a bounded timeout.

The existing R5 executor remains responsible for Guardian, `PermissionSet`, `ProcessSandbox`, KillSwitch and audit behavior.

## Classification contract

- original importable files such as SVG/PNG/audio/3D files: `source`;
- Godot native `.tscn/.scn/.tres/.res/.gd`: `godot_native`;
- `project.godot`: `project_config`;
- `<asset>.import`: `import_metadata` and reproducibility evidence, never source bytes;
- `.godot/**` and legacy `.import/**`: `generated_cache`, never Vault source.

A Vault project reference that targets generated cache is a portability error. Missing materialized sources remain explicit.

## Rebuild sequence

1. Resolve `project.godot` and source paths through `WorkspaceBoundary`.
2. Capture source SHA-256/length and any existing `<asset>.import` evidence.
3. Validate supplied `ProjectAssetReference` targets.
4. Query Godot capability through the structured R5 tool **before any purge**.
5. If Godot is missing or not 4.7.x, return `UNAVAILABLE` and preserve all source/cache state.
6. Purge only managed `.godot/` and legacy `.import/` directories. Cache-root symlinks fail closed.
7. Invoke the accepted headless Godot import tool.
8. Re-hash `project.godot` and all preserved source bytes; mutation is `FAILED`.
9. Capture regenerated `<asset>.import` sidecars and verify generated-cache presence for importable sources.
10. Emit a deterministic manifest digest over Godot version, project identity, source identities, import sidecars and Vault references. Generated cache bytes are excluded from canonical identity.

## Versioned evidence

`schemas/godot-import-manifest-v1.schema.json` defines the canonical manifest payload. It contains no absolute local path and no generated cache bytes.

## Hardware-local acceptance

`scripts/r8_9_local_acceptance.py` creates a disposable SVG Godot fixture under `.kodepoia/acceptance/r8-9/`, verifies the exact Git head through the accepted R8.7 VCS service, builds the normal R5 Guardian/Permissions/KodeGodotExecutor stack, purges a disposable legacy cache, performs a real Godot 4.7 import and writes only `.kodepoia/acceptance/r8-9-local-acceptance.json`.

No credentials, remote URL, private project data, export template or unrelated asset is required.

## Rollback and safety

Source/Vault identities are never deleted by rebuild. If import fails after purge, only disposable cache has been removed and can be rebuilt later. Missing capability never causes purge. No `.godot/` content is promoted into Vault by this service.
