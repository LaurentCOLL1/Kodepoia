# R10.2 — Acceptance record

Status: **LOCAL EVIDENCE ACCEPTED; FINAL DOCUMENTED HEAD PENDING GATES**  
Manual intervention: **REQUIRED — SATISFIED**

## Accepted hosted implementation

Immutable hosted implementation head: `b107c565e0df628eb3308543acd998f94b0b6942`.

Exact-head hosted gates:

- R0 Repository Guard #1225 / `32662882198`: **SUCCESS**.
- Python Core #1199 / `32662882146`: **SUCCESS**.
- KodeStudio UI Smoke #1166 / `32662882152`: **SUCCESS**.

The hosted implementation includes deterministic fake-runner coverage for success, crash, timeout, cancellation, bounded output, malformed result and artifact-path spoofing; schema validation; CLI registration; and a static bootstrap with no dynamic-code/network/subprocess surface.

## Final manual candidate and hosted gates

Final manual candidate head: `0a2da2334cc6ebe116819110ba80ad1729e22057`.

Exact-head gates on that candidate:

- R0 Repository Guard #1226 / `32663068270`: **SUCCESS**.
- Python Core #1200 / `32663068251`: **SUCCESS**.
- KodeStudio UI Smoke #1167 / `32663068243`: **SUCCESS**.

The REQUIRED local acceptance was executed on that exact SHA against Blender **5.2.0 LTS** on Windows and returned CLI exit code `0`.

## Reviewed canonical local evidence

Canonical repository copy: `docs/roadmap/R10_2_LOCAL_ACCEPTANCE.json`.

Evidence file identity as received and independently rechecked:

- SHA-256: `3b65790c4f553640f6d3c14bc141940bca73695a911a343a4ad78449445f243a`.
- Bytes: `1141`.
- `schema=kodepoia.r10.local_blender_evidence`, version `1`.
- `source_sha=0a2da2334cc6ebe116819110ba80ad1729e22057`.
- `status=pass`, `blockers=[]`.
- Runtime: Blender `5.2.0`, embedded Python `3.13.13`, Windows AMD64.
- Executable SHA-256: `0060916d6921eb4d46c57254609d805a2ea711917399051391a52ba14beb6327`.
- Command policy `r10.2-v1`: factory startup, background mode, autoexec disabled, offline mode, Python exit code `17`.
- Probe: `background=true`, `online_access=false`, `gltf_exporter_available=true`, `bmesh_available=true`.
- Canonical probe scene facts: 1 object, 8 vertices, 6 faces; bmesh vertex count 8.
- `.blend`: 94,460 bytes, SHA-256 `dbda97a9f3f7dddeb2df92af277502aa21ac119a3ee9f49509dbdf4735389e43`.
- GLB: 1,436 bytes, SHA-256 `47fa0c82eb14f211e33a9f6b5c36d48a60d1619c33632c4cbbd9099c5d70bc1f`.
- Process: return code `0`; timeout/cancel/crash/OOM all false; stdout/stderr limits not exceeded.

The evidence contains no username, home path, executable path, token, password, private key, network endpoint or unrelated user data.

## Upstream compatibility cross-check

Official Blender 5.2 LTS release material identifies Blender 5.2.0 as the July 14, 2026 LTS release supported until July 2028. The Blender 5.2 manual documents the glTF 2.0 importer/exporter and GLB single-file export. These upstream sources are compatibility evidence only; the reviewed real-runtime evidence above remains authoritative for R10.2 acceptance.

## Final gate ordering

This documentation/evidence commit changes no runner implementation. Its exact head must now pass R0 Repository Guard + full Python Core + KodeStudio UI Smoke. If those gates succeed, PR #133 may be merged with `expected_head_sha` and then a single continuity-only post-merge normalization must pass the same three gates and merge.

Only after that normalization merge is R10.2 **COMPLETE + NORMALIZED** and R10.3 authorized.
