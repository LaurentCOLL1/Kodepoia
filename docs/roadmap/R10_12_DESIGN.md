# R10.12 — Adversarial hardening + R10 integrated acceptance design

## Authority and scope

This design implements the frozen R10.12 section of `R10_PLAN.md`. It adds no product feature and changes no R1–R9 foundation. R10.1–R10.11 remain authoritative for their own contracts and runtime semantics.

R10.12 attacks cross-subsystem seams and then binds the already accepted R10 evidence into one deterministic integrated report. It does not replace the earlier acceptance records and never edits R7/R8/R9 integrated evidence to manufacture a pass.

## Threat model exercised

The dedicated R10.12 suite covers the high-value seams that can cross an accepted subsystem boundary:

- recipe parameter names that would expose Python, operator, argv, executable, path, environment, URL or script injection;
- NaN/Inf recipe parameters;
- Python/Blender environment injection;
- the exact fixed Blender argv, including factory startup, autoexec disabled, offline mode and non-zero Python exit handling;
- governed script-root confinement;
- glTF remote/absolute/parent-traversal URI attempts;
- bounded data-URI acceptance;
- forged GLB declared lengths and unsupported chunk types;
- envelope/schema-version drift;
- accepted-document substitution after an evidence digest is bound;
- required local runtime evidence substitution;
- prior R7/R8/R9 integrated-report substitution or non-PASS state;
- integrated report semantic-digest and runtime-policy tampering.

The full Python Core remains part of every exact-head gate, so all previously accepted malformed mesh/UV/material, rig/weight, animation/retarget, LOD/preservation, process crash/timeout/cancellation/output-limit and lineage/provenance tests continue to execute. R10.12 does not duplicate those lower-level test matrices merely to increase local test count.

## Integrated evidence model

`src/kodepoia/blender3d/acceptance.py` defines a versioned deterministic model with four bound evidence classes:

1. twelve ordered R10 subdivision acceptance documents (`R10.1` through `R10.12`), each bound by repository byte length, SHA-256, accepted implementation head and satisfied manual state;
2. the two frozen REQUIRED local runtime artifacts, `R10_2_LOCAL_ACCEPTANCE.json` and `R10_10_LOCAL_ACCEPTANCE.json`;
3. the canonical R7, R8 and R9 integrated acceptance reports, each bound by file SHA-256/byte length and its own semantic `evidence_sha256`;
4. a frozen runtime policy requiring Blender 5.2.x with autoexec disabled/offline mode and Godot 4.7 for the R10.10 interoperability proof.

The verifier re-reads repository bytes and recomputes file identities. A report is invalid if a declared accepted head is absent from its canonical acceptance document, if any manual state is unsatisfied, if local evidence is not `status=pass` with no blockers, if the local runtime no longer binds Blender 5.2/Godot 4.7, or if any prior integrated report is not PASS.

## Anti-circular sequence

The canonical `R10_INTEGRATED_ACCEPTANCE.json` is intentionally absent from the initial implementation candidate.

1. Freeze implementation head containing verifier/schema/tests/design/acceptance contract.
2. Require exact-head R0 Repository Guard, full Python Core and KodeStudio UI Smoke.
3. If successful, use that immutable implementation SHA as R10.12 `source_sha` and `accepted_head`.
4. Generate/bind `R10_INTEGRATED_ACCEPTANCE.json` from immutable repository evidence and update the R10.12 acceptance document with the implementation run IDs.
5. Require fresh R0/Python/UI on that exact final documentation/evidence head.
6. Merge only if the canonical report is `status=pass`, `blockers=[]` and its verifier succeeds.
7. Perform exactly one final continuity-only normalization. Only its successful merge makes R10 COMPLETE + NORMALIZED and authorizes R11 planning.

The report digest does not include a future commit SHA and no report claims the digest of its own yet-uncommitted Git blob.

## Manual-state evaluation

Frozen state: **CONDITIONAL**.

Current implementation introduces no new real Blender/Godot behavior. It adversarially validates the already accepted boundaries and explicitly re-binds the reviewed R10.2 Blender 5.2 and R10.10 Blender 5.2 + Godot 4.7 local evidence. Therefore the condition is expected to be **NOT TRIGGERED** unless the implementation gates reveal that R10.12 has in fact created or newly exercised an authoritative hardware/runtime semantic not covered by those local gates.

If that condition changes, work stops before final acceptance and a new bounded local evidence command is required; hosted CI must not manufacture the missing proof.

## External compatibility notes

Official Blender 5.2 documentation exposes `--disable-autoexec`, `--offline-mode`, `--factory-startup` and non-zero `--python-exit-code`; these are compatibility facts, while Kodepoia's fixed argv and sandbox remain the security authority. Khronos glTF 2.0 permits relative and data URIs, so Kodepoia intentionally applies a narrower external-URI policy to reject remote, absolute and parent-traversal references. Godot 4.7 remains the downstream import authority already exercised by accepted R10.10 evidence.
