# R10.2 — Acceptance record

Status: **HOSTED GATES PENDING; MANUAL REQUIRED**  
Manual intervention: **REQUIRED**

## Hosted acceptance requirements

One exact implementation head must pass:

- R0 Repository Guard;
- full Python Core on Ubuntu/Windows with R7/R8/R9 integrated acceptance still PASS;
- KodeStudio UI Smoke;
- deterministic fake-runner tests for success, crash, timeout, cancellation, bounded output, malformed result and artifact-path spoofing;
- schema validation for probe-result and canonical local evidence;
- static bootstrap inspection proving no dynamic-code/network/subprocess surface.

## REQUIRED local gate

After the hosted candidate head is accepted and frozen, run the repository command documented here on a legitimate local Blender 5.2.x LTS executable. Acceptance requires exit code 0 and canonical evidence with `status=pass`, `blockers=[]`, Blender 5.2.x, `background=true`, `online_access=false`, glTF exporter + bmesh available, verified `.blend` and GLB SHA-256/byte sizes, no timeout/cancel/crash/OOM, and the exact candidate `source_sha`.

The final exact command and accepted hosted run IDs will be written only after hosted CI succeeds. **Do not run a provisional SHA and do not start R10.3.**
