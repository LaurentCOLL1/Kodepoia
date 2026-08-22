# R6.4 — KodeVisualQA foundation — Design

**Phase:** R6.4  
**Status:** IN PROGRESS  
**Parent plan:** `docs/roadmap/R6_PLAN.md`  
**Architecture:** Kodepoia v1.0 frozen

## Objective

R6.4 provides a deterministic, engine-neutral visual-regression contract. It compares a current image with an explicitly approved baseline, preserves evidence hashes and a diff artifact, and exposes the result to the already accepted R6.3 test/regression layer through a stable test ID.

It deliberately does **not** make aesthetic judgements, auto-approve a failed image, or add a second arbitrary process-execution path.

## External implementation baseline

- Pillow is pinned to `>=12.3,<12.4` so image decoding/comparison behavior is controlled to one released minor series during R6.4 acceptance.
- Godot Movie Maker supports PNG image-sequence output through `--write-movie <file.png>`. This provides lossless rendered frames without extracting frames from the already accepted R5 AVI path.
- Real-render VisualQA capture intentionally omits `--headless`; R5 already established that Movie Maker evidence must not be produced through the dummy RenderingServer.
- Hardware-local acceptance additionally records Godot rendering method, rendering driver and video-adapter name. Empty or headless/dummy renderer evidence is rejected.

These external references inform implementation only. The frozen Kodepoia architecture and R6 plan remain authoritative.

## Architecture

### `VisualPolicy`

A policy contains only deterministic comparison inputs:

- `pixel_delta_threshold` — per-channel delta below/equal to this value does not mark a pixel changed;
- `warn_changed_ratio` / `fail_changed_ratio`;
- `warn_perceptual_ratio` / `fail_perceptual_ratio`;
- zero or more rectangular masks declared before evaluation.

Policies are canonically serialized and SHA-256 hashed. Masks therefore become part of the evidence identity rather than an unrecorded exception.

### Image identity

`VisualImage` preserves:

- workspace-relative path;
- SHA-256;
- byte size;
- image format;
- mode/channel model;
- width/height.

Format, mode or resolution mismatches are explicit failures instead of being silently normalized away.

### Immutable baseline approval

`VisualBaselineApproval` records:

- stable visual case ID;
- approval timestamp;
- approver/provenance label;
- approval reason;
- image metadata/hash;
- canonical manifest hash.

Approved baseline images use content-addressed storage under:

`.kodepoia/visual_tests/baselines/<case-id>/<sha256>.<ext>`

The approval path never overwrites an existing content identity. Loading a baseline re-hashes the stored artifact and rejects mutation after approval.

### Deterministic comparison

KodeVisualQA computes:

- exact-file equality;
- changed pixels after policy masks and channel threshold;
- changed/compared/masked pixel counts;
- changed ratio;
- normalized mean absolute channel error;
- maximum channel delta;
- a 64-bit difference hash (dHash) using deterministic grayscale + 9x8 nearest-neighbor sampling;
- normalized Hamming distance of the dHashes.

The dHash is a coarse, deterministic perceptual signal. It is not an AI/aesthetic judgement and is always reported alongside pixel evidence.

### PASS / WARN / FAIL / UNKNOWN

- missing baseline or current artifact => `UNKNOWN`, never PASS;
- format/mode/resolution incompatibility => `FAIL`;
- ratio at/above configured FAIL threshold => `FAIL`;
- ratio at/above configured WARN threshold => `WARN`;
- otherwise => `PASS`.

Threshold boundaries are inclusive and covered by fixtures.

### Diff evidence

A PNG difference artifact is generated under `.kodepoia/visual_tests/diffs/`. Masked regions are zeroed in the diff so the artifact reflects the same policy used by the metrics.

### Report integrity

`VisualReport` schema v1 binds:

- baseline/current metadata;
- baseline approval hash;
- full policy + policy hash;
- derived metrics;
- diff metadata;
- reasons/status;
- canonical report evidence SHA-256.

Deserialization recomputes policy/status/derived consistency and rejects evidence-hash tampering.

### R6.3 integration

`KodeVisualQA.to_test_case()` exposes each report as stable R6.3 evidence:

`visual:<case-id>`

Mapping:

- Visual PASS -> test PASS;
- Visual WARN -> PASS by default or FAIL if the caller explicitly configures warn-as-failure;
- Visual FAIL -> test FAIL;
- Visual UNKNOWN -> test ERROR.

The visual status and evidence/policy hashes remain in `details` so generic regression comparison never erases VisualQA semantics.

## KodeGodot integration

R6.4 adds one structured tool only:

`kodegodot_capture_png_sequence`

Contract:

- inputs: known scene, simple output filename, bounded frame count, bounded FPS, bounded timeout;
- output root fixed to `.kodepoia/visual_tests/runs/`;
- no arbitrary executable, argv, command, cwd, host or output path;
- `KodeGodotExecutor` has an explicit Guardian policy requiring FILE_READ + FILE_WRITE + PROCESS_EXECUTE;
- process execution remains through `GodotRuntime` -> `ProcessSandbox`;
- no `--headless` flag for real rendered capture.

The accepted R5 `kodegodot_capture_movie` AVI contract is unchanged.

## Hardware-local acceptance fixture

`kodepoia.quality.visual_acceptance` creates a disposable 320x180 Godot project under `.kodepoia/r6-4-acceptance/project` and draws deterministic vector primitives. The fixture:

1. checks Godot 4.7.x;
2. captures three rendered PNG baseline frames;
3. approves frame 1 as baseline;
4. captures three current frames;
5. requires non-empty rendering method, rendering driver and video adapter and rejects dummy/headless evidence;
6. compares frame 1 using KodeVisualQA;
7. converts the PASS to R6.3 stable test evidence;
8. verifies the KodeGodot AuditLog hash chain;
9. saves a machine-readable acceptance report.

The script does not mutate a user project and does not auto-update a failed baseline.

## Persistence

All project evidence remains under initialized `.kodepoia/` and all caller-provided paths go through `WorkspaceBoundary`:

- baselines: `.kodepoia/visual_tests/baselines/`;
- current/report snapshots: `.kodepoia/visual_tests/runs/`;
- diffs: `.kodepoia/visual_tests/diffs/`.

Fixtures explicitly cover `../` and symlink escape rejection.

## Security / governance boundaries

R6.4 preserves:

- WorkspaceBoundary confinement;
- ProcessSandbox + KillSwitch execution path;
- Guardian/PermissionSet authorization;
- structured KodeGodot APIs only;
- AuditLog evidence;
- no arbitrary shell command fields;
- no automatic baseline acceptance after regression;
- no architecture change requiring an ADR.

## Known risks and mitigations

- **Renderer/driver noise:** controlled through threshold policy and perceptual metric; policy is hash-bound.
- **Masks hiding regressions:** masks are explicit, bounded, stored and hashed; they cannot be invented during comparison.
- **Baseline laundering:** failed comparisons never replace baselines; baseline approval is a separate explicit operation.
- **Encoding-only changes:** exact file hash and pixel identity are reported separately.
- **Huge artifacts:** R6.4 foundation stores one diff per run; retention policy belongs to later lifecycle/CI work.
- **Cross-device variance:** CI proves deterministic fixtures; authoritative real-render acceptance is explicitly hardware-local on the accepted Windows workstation.

## Rollback

R6.4 is additive. Reverting the R6.4 implementation PR removes:

- the visual module/schema/tests/dependency;
- the separate PNG-capture tool;
- the local acceptance runner/docs.

It does not alter the semantics of accepted R6.1–R6.3 evidence or the existing R5 AVI Movie Maker contract. Approved baseline artifacts in managed projects are evidence data and are never destructively rewritten by rollback code.
