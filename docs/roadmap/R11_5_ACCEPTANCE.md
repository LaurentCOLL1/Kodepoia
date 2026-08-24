# R11.5 — Acceptance

Status: **LOCAL REQUIRED ACCEPTED; FINAL EXACT-HEAD GATES PENDING**  
Frozen manual intervention: **REQUIRED — SATISFIED**

## Definition of Done

R11.5 requires backend-neutral local TTS capabilities/registry, Piper-compatible execution only through `MediaRuntimeBoundary` + `ProcessSandbox`, privacy-safe ephemeral `--input-file` text transport, model/config/runtime SHA binding, deterministic request/cache identity, Godot/system-TTS restricted to non-canonical accessibility/runtime speech, repository-local model catalog governance, bounded WAV/PCM QA, full hosted R0/Python/UI acceptance, and one real local Piper synthesis bound to the exact implementation candidate.

## Candidate 1 — hosted accepted, local rejected

Implementation candidate: `441ea87436c6851cd106654454f955a91460f7af`.

Hosted exact-head gates were all SUCCESS:
- R0 Repository Guard #1359 / `32734530111`;
- Python Core #1333 / `32734530102` — Ubuntu 961 passed / 8 skipped / 46 warnings, R7/R8/R9 PASS, Windows/builds/internal smoke SUCCESS;
- KodeStudio UI Smoke #1300 / `32734530119`.

The first REQUIRED local run is preserved as rejected historical evidence. Piper itself succeeded with return code 0 and all privacy controls satisfied, but generic R11.2 audio QA blocked one full-scale endpoint sample because its global profile intentionally allows zero clipped samples. That result is not reclassified.

## Candidate 2 — hosted accepted

Accepted implementation candidate: `a9862b3bf475b259fe154d1e2486116ad04602f3`.

Candidate 2 keeps R11.2 generic QA unchanged and adds only the dedicated `tts.local.v2` speech profile, which allows an isolated full-scale endpoint rate of at most 10 ppm with an absolute cap of 16 samples; repeated saturation remains blocked.

Candidate 2 also establishes `<repo>/models/` as Kodepoia's canonical physical local model catalog. Large payloads remain local and ignored by Git; tracked manifests carry stable model id, relative payload paths, SHA-256, license/provenance/use metadata and byte budgets. Existing `kodepoia.models.router.ModelRegistry` remains the logical LLM router, while `KodeModelRegistry` governs physical model payload identity and path confinement.

Hosted exact-head evidence on candidate 2:
- R0 Repository Guard #1394 / `32740559995`: **SUCCESS**;
- Python Core #1368 / `32740559969`: **SUCCESS**;
  - Ubuntu Python: **970 passed / 8 skipped / 46 warnings**;
  - Ubuntu integrated R7/R8/R9: **PASS**;
  - Windows Python: **SUCCESS**;
  - Ubuntu + Windows package builds: **SUCCESS**;
  - internal KodeStudio UI smoke: **SUCCESS**;
- KodeStudio UI Smoke #1335 / `32740559942`: **SUCCESS**.

## REQUIRED local acceptance — ACCEPTED

The second REQUIRED local run was executed from exact candidate `a9862b3bf475b259fe154d1e2486116ad04602f3` with the governed catalog model `tts.piper.fr-FR.siwis-medium` and returned exit code 0 with `status=pass` and `blockers=[]`.

Canonical evidence: `R11_5_LOCAL_ACCEPTANCE.json`.
- evidence file: **2865 bytes**, SHA-256 `6406884deb38ab5be22fe99d5f3c50187953b4aa9cb8f59f5f21b4a396309e2e`;
- canonical evidence digest: `12223e911a76087a4eea23ce9e371fdc401990d127cb9f306237d67550725ffe`;
- model id: `tts.piper.fr-FR.siwis-medium`;
- model SHA-256: `641d1ab097da2b81128c076810edb052b385decc8be3381814802a64a73baf99`;
- config SHA-256: `39479916c2db192b5ac9764daddd0c744d83e023ad890c6976c0633ae4df8959`;
- runtime executable SHA-256: `4695e1b383903cd2b6ff3c3ea0126406000d10e87a3d49bf1c38d36b924024d1`;
- Piper capability status: PASS, network required: false;
- synthesis: return code 0, no timeout/cancel, stdout/stderr 0 bytes;
- output WAV: **215084 bytes**, SHA-256 `4943de190a4087bb7253b22f5a32e051ddbabc99d47686837f50476a6ac39b86`;
- PCM facts: mono, 22,050 Hz, 107,520 frames, 4.876190476190477 s, peak 0.999969482421875, 1 full-scale endpoint sample;
- QA profile `tts.local.v2`: **PASS**, no blockers or warnings;
- text was not passed through argv and the ephemeral input file was deleted;
- no private recording, voice cloning, collector download or retained audio;
- operator-approved license id `cc-by-4.0`, provenance `piper.fr-fr.siwis.medium`.

The evidence digest was independently recomputed from canonical JSON with `evidence_digest` omitted and matched exactly. The raw evidence SHA-256 and byte size were also independently recomputed before binding. A repository test now validates the schema, raw SHA, canonical digest, candidate binding, model/config identities, QA PASS and privacy invariants on every final Python Core run.

## Accepted R11.5 implementation surface

- backend-neutral TTS capability/registry contracts and explicit `UNAVAILABLE` semantics;
- Piper-compatible fixed-argv adapter under the existing sandbox boundary;
- privacy-safe staging text file through `--input-file` only;
- deterministic synthesis request/cache identity bound to runtime/model/config SHA-256;
- R8-revision cache references without duplicate physical audio ownership;
- Godot/system TTS capability adapter restricted to accessibility/runtime use;
- `models/` physical catalog with tracked manifests and ignored heavy payloads;
- `KodeModelRegistry` path/SHA/license/provenance verification;
- bounded `tts.local.v2` speech QA while preserving generic R11.2 zero-clipping policy;
- JSON schemas, hosted tests and real local acceptance collector.

## Final acceptance ordering

1. Keep the rejected first-run result historical and preserve the accepted candidate-2 local evidence permanently.
2. Freeze the evidence-bound branch head containing this record, `R11_5_LOCAL_ACCEPTANCE.json`, and its verifier test.
3. Run fresh R0 Repository Guard + full Python Core + KodeStudio UI Smoke on that exact head.
4. Merge PR #165 only if all three are SUCCESS and the PR head has not moved.
5. Create a continuity-only post-merge normalization branch from the resulting `main` merge commit.
6. Run fresh R0 + Python + UI on the normalization head and merge only if all three are SUCCESS.
7. Only after that normalization merge is R11.5 **COMPLETE + NORMALIZED** and R11.6 authorized.

## Manual safety rule

The REQUIRED manual gate is satisfied. No additional Piper/model download, voice change, cloning/reference recording, QA relaxation, or local rerun is authorized unless a later runtime-affecting exact-head change invalidates the evidence binding.
