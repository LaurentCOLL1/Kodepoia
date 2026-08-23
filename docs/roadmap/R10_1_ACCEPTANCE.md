# R10.1 — Acceptance record

Status: **IMPLEMENTATION ACCEPTED; FINAL DOCUMENTED HEAD PENDING GATES**  
Manual intervention: **NONE**

## Frozen acceptance requirements

R10.1 requires R0 Repository Guard, full Python Core, and KodeStudio UI Smoke on one exact head; prior R7/R8/R9 integrated acceptance must remain PASS. Missing evidence never becomes PASS.

## Accepted implementation head

Accepted immutable implementation head: `f8d629ca0109037863bd7dd5d109f11cd72a196e`.

Exact-head implementation gates:

- R0 Repository Guard #1220 / `32662214432`: **SUCCESS**.
- Python Core #1194 / `32662214437`: **SUCCESS**.
- KodeStudio UI Smoke #1161 / `32662214438`: **SUCCESS**.

The implementation head contains the complete R10.1 code/test/schema/design scope and no real Blender launch. The temporary marker commits on the branch have zero net tree effect and were removed before the accepted head.

## Accepted behavior

- `BlenderRuntimePolicy` targets Blender 5.2.x LTS and rejects adjacent 4.5/5.1/5.3 profiles.
- Blender job states and transitions fail closed.
- Canonical JSON/SHA-256 recipe/runtime identities are deterministic.
- Executable discovery is finite and constrained to configured/known roots; no recursive disk scan exists.
- Executable/path escapes and wrong executable names are rejected.
- The fixed future runner argv uses `--background`, `--factory-startup`, `--disable-autoexec`, `--offline-mode`, non-zero `--python-exit-code`, and exactly one staging-root `--python` script.
- `--python-expr`, `--python-text`, `--python-use-system-env`, arbitrary addon/operator/argv/cwd/URL/code surfaces are not exposed.
- `PYTHONPATH`, `PYTHONHOME`, Blender user/system script injection and arbitrary environment overrides are rejected.
- Five R10 v1 schema roots validate representative capability/job/QA/export/local-acceptance documents.
- R10.1 executes no Blender process, `bpy`, geometry mutation, material work, rigging, animation, LOD or export.

## Final documentation gate

This acceptance update intentionally changes only documentation after the immutable implementation head was accepted. The resulting exact documented head must itself pass R0 Repository Guard + full Python Core + KodeStudio UI Smoke before PR merge. Those final run IDs belong in the PR/merge evidence; no implementation claim is rewritten from a later commit.
