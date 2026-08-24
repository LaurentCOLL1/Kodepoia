# Kodepoia — R11 detailed phase plan

**Phase:** R11  
**Roadmap title:** Audio / Voice / Cinematics / Franchise  
**Status:** PLANNING  
**Phase planning started:** 2026-08-24  
**Architecture:** v1.0 frozen  
**Source of truth at planning branch point:** normalized `main` `d627f26a086c46273ce378a2d4d9919db0e9dd3a`

## Purpose and authority

R11 implements Kodepoia's governed audio, voice, cinematic and long-lived franchise continuity layer without changing the frozen foundations. The frozen roadmap requires Music/SFX/Foley/QA, Voice Profiles, multilingual TTS, lip-sync, visemes, facial LOD, shots/timelines, Continuity Bridge, Franchise DNA, Canon and Persistence/SaveBridge.

This file is the exhaustive execution/recovery plan for R11. The R11.1–R11.14 subdivision structure becomes frozen when this plan is merged. No subdivision may be silently added, removed, merged, split or renumbered. Any scope change must update this plan and `docs/continuity/KODEPOIA_CONTINUITY.md` in the same work cycle; any foundation change requires an ADR.

R11.1 MUST NOT begin before this plan is merged to `main` with R0 Repository Guard, full Python Core and KodeStudio UI Smoke successful on the exact final planning head, followed by the single continuity-only planning normalization required by the phase-start rule.

## Phase objective

Deliver a deterministic, auditable, local-first media and narrative continuity pipeline that lets Kodepoia:

- ingest, inspect, normalize, transform and QA governed audio assets;
- model music, SFX and Foley cues with loop, variation, spatialization and budget semantics;
- define durable Voice Profiles with locale, pronunciation, prosody, runtime/model identity and rights/provenance metadata;
- synthesize multilingual speech through structured local TTS adapters without exposing arbitrary shell/model execution;
- derive word/phoneme/viseme timelines and map them to validated R10 facial targets and R5 Godot animation/import semantics;
- model facial performance and facial LOD without silently changing R10 geometry/rig authority;
- define cinematic shots, sequences and deterministic timelines combining cameras, dialogue, audio, animation and events;
- assemble/preview/capture Godot 4.7 cinematics with bounded runtime invocation and machine-verifiable A/V evidence;
- preserve cross-scene/project character/world/story continuity through a Continuity Bridge;
- define Franchise DNA and a versioned Canon model with explicit authority/conflict/deprecation semantics;
- bridge runtime persistence/save state across schema and content versions without inventing cloud-save/backend semantics reserved for R14;
- expose the full governed workflow through CLI and KodeStudio;
- close the phase with adversarial hardening and an anti-circular R11 integrated acceptance report.

R11 extends existing systems instead of replacing them:

- R2 Project DNA/Product remains authoritative for product/project intent; Franchise DNA is a higher-level multi-project continuity contract, not a second project wizard.
- R5 KodeGodot remains authoritative for Godot 4.7 project/runtime semantics, audio nodes, animation resources, scene import and movie capture.
- R6 remains authoritative for Health, Budget, Tests, Regression, VisualQA, Accessibility, Localization, Privacy, AppSecurity and License/BOM.
- R7 remains authoritative for external-content trust and research provenance.
- R8 remains authoritative for Vault/source-vs-derived identity, transform lineage, cache/rebuild and governed export.
- R9 remains authoritative for VRAM scheduling and ComfyUI-generated source media where used.
- R10 remains authoritative for Blender/3D geometry, rigs, shape keys/blend shapes, animation and GLB/glTF semantics.

Out of scope for R11: replacing a DAW/NLE; unrestricted music or voice model training; arbitrary voice cloning or impersonation from recordings; biometric identity inference; cloud TTS/audio APIs by default; automatic download/install of codecs, TTS engines or voice weights; backend/cloud saves/auth/matchmaking (R14); mobile/store release (R13); desktop app framework work (R12); model fine-tuning (R15); unconstrained film editing; DRM; bypassing R1–R10 governance; or changing the frozen architecture without ADR.

## Current external compatibility baseline

Planning research on 2026-08-24 uses official upstream documentation as compatibility evidence only; upstream behavior never overrides Kodepoia governance.

### Godot 4.7 baseline

- Godot 4.7 remains the engine baseline inherited from R5.
- Godot supports WAV, Ogg Vorbis and MP3 audio streams, including non-positional and 2D/3D playback.
- Audio buses provide routable processing/effects; R11 may author/validate bus-aware manifests but R5 remains authoritative for actual Godot resource/project mutation.
- `AnimationPlayer` supports audio and animation playback tracks; `AnimationTree` supports advanced blending and remains suitable for facial/body animation composition.
- Godot exposes platform-provided text-to-speech through `DisplayServer`, but this is treated as accessibility/runtime speech and is not assumed to provide deterministic production voice assets or phoneme timing.
- Godot's command line supports `--write-movie` and `--fixed-fps`; R11 may use this only through the already-governed Godot execution boundary to produce deterministic cinematic evidence.

Official references:

- https://docs.godotengine.org/en/4.7/tutorials/audio/text_to_speech.html
- https://docs.godotengine.org/en/4.7/classes/class_audiostream.html
- https://docs.godotengine.org/en/4.7/tutorials/audio/recording_with_microphone.html
- https://docs.godotengine.org/en/4.7/tutorials/animation/animation_tree.html
- https://docs.godotengine.org/en/4.7/tutorials/animation/animation_track_types.html
- https://docs.godotengine.org/en/4.7/tutorials/editor/command_line_tutorial.html

### FFmpeg/ffprobe baseline

- FFmpeg **9.0.1** is the current stable release as of 2026-08-24 and is the reference compatibility baseline for R11 planning.
- R11 uses capability probing and explicit executable identity; no silent major/minor downgrade or automatic install occurs.
- `ffprobe` JSON output is the preferred structured inspection surface where an FFmpeg runtime is used.
- FFmpeg's `loudnorm` filter implements EBU R128 loudness normalization and exposes integrated loudness, loudness range and true-peak targets; R11 uses those facts as measurable QA inputs, not as a universal mastering prescription.
- External ffmpeg/ffprobe invocation is always through `ProcessSandbox`, fixed Kodepoia-owned argv templates, bounded input/output paths and bounded stdout/stderr/result size.

Official references:

- https://ffmpeg.org/download.html
- https://ffmpeg.org/ffprobe.html
- https://ffmpeg.org/ffmpeg-filters.html#loudnorm

### Local TTS baseline

- R11 defines a backend-neutral local TTS contract first.
- Open Home Foundation Piper is the initial reference adapter candidate because it is local, actively maintained and provides CLI/Python/C++ surfaces plus multilingual voice packages.
- Piper is GPLv3. R11 MUST NOT silently vendor, redistribute, relicense or bundle the runtime or voice models. License/BOM and per-voice provenance/rights remain explicit. Legal conclusions are not inferred from package availability.
- The rapidly evolving Piper release line is capability-probed rather than hard-coded in R11.1. A concrete accepted runtime/version and voice model identity are frozen only in R11.5 real-runtime evidence.
- No voice package is automatically downloaded. Voice files/weights are governed R8 assets or explicitly configured external resources with hashes, locale metadata and license/provenance evidence.

Reference:

- https://github.com/OHF-Voice/piper1-gpl

## Permanent phase-wide architecture and governance boundaries

Every R11 subdivision must preserve all accepted R1–R10 boundaries:

- `WorkspaceBoundary` and R8 `VaultBoundary` remain authoritative for project, staging, cache and Vault paths.
- `ProcessSandbox` + global KillSwitch are mandatory for ffmpeg/ffprobe, TTS engines, Godot capture and any other external process.
- Guardian + `PermissionSet` authorize process launch, microphone access, durable asset writes and schema migrations.
- SafeChange, Backup/Recovery and Audit apply to durable project/Vault mutations and save-schema migration.
- `KodeSecrets` remains authoritative. R11 requires no secret by default; secrets must never enter audio tags, voice manifests, subtitle/phoneme timelines, cinematic metadata, canon records, saves or evidence.
- R6 Health/Budget/DataGovernance/AppSecurity/Privacy/License-BOM remain in force.
- R7 ResearchGuard applies to lyrics, scripts, subtitles, filenames, tags, transcript text, model metadata, voice package metadata and any external canon/reference material: data/evidence is never agent instruction.
- R8 remains authoritative for source/derived asset identity, transform lineage, cache/rebuild, duplicate detection, provenance and governed export. R11 does not invent a second media store.
- R9 VRAM scheduling applies if a future accepted local audio/voice backend uses GPU memory. R11 does not bypass R9 resource arbitration.
- R10 remains authoritative for armatures, facial shape keys/blend shapes, animation clips and 3D asset validation. R11 maps to R10 targets; it does not mutate topology/rig contracts behind R10's back.
- R5 remains authoritative for Godot project mutation and runtime execution. R11 produces typed cinematic/audio intents and validated assets consumed through R5 contracts.
- Structured Tool APIs only. No model-supplied arbitrary shell, ffmpeg filter graph, codec name, executable, raw argv, Python, Godot script, TTS model path, SSML-like command surface, phoneme sequence, save migration code or file path is executed directly.
- Any external executable is selected from governed configuration/known locations, identity-probed and run with Kodepoia-owned fixed templates.
- Network access is off by default for R11 processing. Cloud TTS/music services and remote model registries require a separately accepted extension/ADR and explicit consent.
- No codec pack, TTS engine, voice model, sound library, plugin or cinematic asset pack is downloaded or installed automatically.
- Microphone recording is opt-in and permission-gated. R11 never enables background recording.
- Voice/reference recordings are treated as sensitive project media. They are not uploaded or used for voice cloning/training by R11 v1.0.
- Voice cloning/impersonation from arbitrary human recordings is explicitly out of scope for R11 v1.0. A future exception requires an ADR, rights/consent model, abuse controls and new acceptance.
- Existing licensed synthetic voices may be referenced only with explicit voice/runtime/model identity and license/provenance metadata.
- Versioned schemas are required for audio identity/QA, cue definitions, voice profiles, synthesis manifests, pronunciation lexicons, alignment/viseme timelines, facial profiles/LOD, shot/sequence timelines, continuity snapshots, Franchise DNA, Canon, SaveBridge and local acceptance evidence.
- Canonical JSON/SHA-256 identities are used for durable evidence and recipe identities. Filenames/display names are never durable identity.
- Explicit `UNKNOWN`, `N/A`, `UNAVAILABLE`, `BLOCKED`, `STALE`, `MISSING`, `CORRUPT`, `UNSUPPORTED`, `CANCELLED`, `FAILED`, `RESOURCE_EXHAUSTED`, `BUDGET_EXCEEDED`, `RIGHTS_BLOCKED`, `CONFLICTED` and `MIGRATION_REQUIRED` semantics are used where applicable.
- Exact-head acceptance remains mandatory. Missing evidence never manufactures PASS.
- ADR required if implementation would alter a frozen R1–R10 foundation rather than add an R11-scoped capability.

## R11 identity and evidence model

R11 separates durable identities instead of conflating filenames or mutable tool state:

1. **AudioSourceIdentity** — R8 source revision plus media digest, codec/container facts, sample rate, channels and duration.
2. **AudioTransformDefinitionId** — canonical identity of one bounded normalize/transcode/trim/fade/resample recipe.
3. **AudioQAReport** — deterministic inspection facts and profile-specific PASS/WARN/FAIL/BUDGET states.
4. **AudioCueDefinition** — semantic music/SFX/Foley cue, categories, variants, loop/spatialization policy and R8 asset refs.
5. **VoiceProfileId** — durable character/role voice intent independent of a particular TTS engine/model file.
6. **VoiceRuntimeIdentity** — backend/runtime/version/platform/capabilities identity.
7. **VoiceModelIdentity** — exact voice model/config digest, locale, speaker metadata, provenance/license declaration and compatibility.
8. **SynthesisDefinitionId / VoiceRunId** — normalized text/locale/pronunciation/prosody request bound to runtime/model/limits and resulting audio/timing artifacts.
9. **PronunciationLexiconId** — versioned locale-aware pronunciation overrides with bounded text/phoneme entries.
10. **SpeechAlignmentTimeline** — timed words/phonemes with confidence/source semantics.
11. **VisemeTimeline** — deterministic mapping from normalized phoneme/alignment events to profile-specific viseme targets.
12. **FacialPerformanceProfileId** — mapping from viseme/expression semantics to R10-validated blend-shape/bone targets plus LOD tiers.
13. **ShotDefinitionId** — immutable cinematic shot intent: camera, duration, actors, dialogue/audio/animation/event tracks and transition policy.
14. **SequenceTimelineId** — ordered/branch-aware set of shots and timing constraints.
15. **ContinuitySnapshotId** — scoped state exported from a scene/project point for later continuity checks.
16. **FranchiseDNAId** — higher-level multi-project invariants, naming/style/world/character continuity and compatibility policy.
17. **CanonRecordId / CanonSnapshotId** — versioned canonical facts with authority, scope, temporal validity, source and conflict/deprecation semantics.
18. **SaveBridgeSchemaId / SaveManifestId** — runtime persistence contract, schema/content version, migration chain, canonical state digest and compatibility result.
19. **R11IntegratedEvidenceDigest** — semantic digest tying accepted subdivision evidence, required local evidence and prior integrated reports without circular self-attestation.

## Audio and cinematic budget model

R11 budgets extend R6 Budget and are profile-specific. They may include:

- audio file bytes, duration, channels, sample rate, bit depth/bitrate and stream count;
- integrated loudness, loudness range, true peak, DC offset/silence thresholds and clipping counts where measurable;
- loop boundary discontinuity tolerance and cue variant count;
- simultaneous voices/polyphony and Godot bus/effect count;
- TTS wall time, real-time factor, output duration, chunk count and model memory footprint;
- text/phoneme/viseme event count, alignment confidence floor and timeline drift tolerances;
- facial target count, simultaneous blend-shape weights, curve key count and facial LOD target count;
- cinematic shot/track/event count, duration, frame count, fixed FPS, resolution and generated movie bytes;
- A/V duration and sync drift thresholds;
- continuity/canon node-edge counts and conflict counts;
- save bytes, entity/object counts, migration wall time, migration step count and rollback storage.

Budget overruns are explicit `BUDGET_EXCEEDED`, not silently demoted to warnings.

## Global prerequisites

Before R11.1 implementation begins:

- R1–R10 are COMPLETE + NORMALIZED on `main`;
- final R10 normalization PR #154 is merged and planning branch point is `d627f26a086c46273ce378a2d4d9919db0e9dd3a`;
- canonical R7/R8/R9/R10 integrated reports remain present and PASS; R10 digest `48c18aacc916fb064810b36ada5a179f1d3b149912bea8a19a3295da1826a3c8` remains the accepted semantic closure evidence;
- Python baseline remains 3.12.x unless separately changed and accepted;
- R1 protected process/governance foundations remain available;
- R5 Godot 4.7 contracts remain accepted;
- R6 QA/budget/privacy/license/build foundations remain accepted;
- R8 Vault/AssetPipeline provenance and transform lineage remain accepted;
- R10 validated rigs/shape-key/blend-shape metadata remain accepted for facial work;
- no mandatory cloud service/account/API key is introduced;
- hosted CI may use deterministic pure-Python WAV/PCM fixtures, fake process fixtures and synthetic voice/viseme/cinematic fixtures until a subdivision explicitly requires a real runtime;
- no ffmpeg, TTS runtime, voice model, codec pack or third-party media library is downloaded merely to make CI pass.

## Complete subdivision index

| ID | Title | Status | Manual intervention | Depends on |
| --- | --- | --- | --- | --- |
| R11.1 | Media/voice/cinematic contracts, identities + secure runtime boundaries | PLANNED | NONE | R10 COMPLETE + planning PR merged |
| R11.2 | Audio ingest/transcode/analysis + deterministic QA | PLANNED | CONDITIONAL | R11.1 + R6/R8 |
| R11.3 | Music/SFX/Foley cue system + loops/variants/spatialization packaging | PLANNED | NONE | R11.1–R11.2 + R5/R8 |
| R11.4 | Voice Profiles, pronunciation/prosody + rights/provenance governance | PLANNED | NONE | R11.1 + R7/R8 |
| R11.5 | Multilingual local TTS adapters, synthesis cache + real-runtime acceptance | PLANNED | REQUIRED | R11.1–R11.4 + R8/R9 |
| R11.6 | Speech alignment, phoneme/viseme timeline + lip-sync QA | PLANNED | CONDITIONAL | R11.4–R11.5 |
| R11.7 | Facial performance mapping + facial LOD + R10/R5 integration | PLANNED | CONDITIONAL | R11.6 + R10 + R5 |
| R11.8 | Cinematic shots, sequences + deterministic timeline model | PLANNED | NONE | R11.1–R11.7 |
| R11.9 | Godot 4.7 cinematic assembly, movie capture + A/V sync acceptance | PLANNED | REQUIRED | R11.3 + R11.7–R11.8 + R5 |
| R11.10 | Continuity Bridge across scenes/projects | PLANNED | NONE | R11.8–R11.9 + R2/R8 |
| R11.11 | Franchise DNA + versioned Canon graph/conflict policy | PLANNED | NONE | R11.10 + R2/R7/R8 |
| R11.12 | Persistence/SaveBridge schemas, migrations + compatibility/rollback | PLANNED | CONDITIONAL | R11.10–R11.11 + R1/R5/R6 |
| R11.13 | CLI + KodeStudio Audio/Voice/Cinematics/Franchise UX | PLANNED | NONE | R11.1–R11.12 |
| R11.14 | Adversarial hardening + R11 integrated acceptance | PLANNED | CONDITIONAL | R11.1–R11.13 |

---

# R11.1 — Media/voice/cinematic contracts, identities + secure runtime boundaries

## Objective and rationale

Freeze typed domain contracts before any production audio/TTS/cinematic runtime is executed. Establish identities, states, path rules, capability probes, bounded process policies and evidence semantics so later subdivisions cannot turn ffmpeg, TTS engines or Godot into arbitrary execution surfaces.

## In scope

- AudioSourceIdentity and AudioQA state models.
- VoiceRuntimeIdentity, VoiceModelIdentity, VoiceProfile root references, synthesis/alignment/viseme/facial identity roots.
- ShotDefinition/SequenceTimeline/Continuity/Franchise/Canon/SaveBridge root contracts.
- canonical JSON and SHA-256 serialization helpers.
- versioned schema roots under schemas/r11.
- bounded external-media runtime policy layered on existing ProcessSandbox.
- explicit executable discovery from configured/known roots only.
- fixed Kodepoia-owned argv/environment/cwd/output policies.
- timeouts, cancellation, KillSwitch propagation, stdout/stderr/result limits.
- R11 status vocabulary including RIGHTS_BLOCKED, CONFLICTED and MIGRATION_REQUIRED.

## Out of scope

- No real TTS synthesis.
- No production ffmpeg transform requirement.
- No music/SFX/Foley packaging.
- No lip-sync/facial generation.
- No cinematic capture.
- No canon promotion or save migration.

## Dependencies and prerequisites

R10 COMPLETE + normalized; merged R11 planning PR; R1/R5/R6/R8/R10 foundations. The branch point must be the exact normalized `main` produced by the preceding accepted work cycle. Required external runtimes, if any, must be discovered/configured through accepted boundaries; no download is implied by this dependency.

## Detailed implementation plan

- Create `src/kodepoia/media/` with small focused modules (`contracts.py`, `serialization.py`, `boundary.py`) rather than a monolith.
- Use immutable dataclasses/enums and strict validators; reject non-finite numeric values, unknown enum values and non-canonical state transitions.
- Bind every runtime/model/media object to explicit identity and declared capabilities; filenames/display names are never durable identity.
- Reuse ProcessSandbox and Guardian rather than implementing a new subprocess layer. The caller chooses high-level operation/backend intent only; executable, argv template, cwd, environment and output paths remain policy-owned.
- Reject URLs, raw shell fragments, arbitrary ffmpeg filters, arbitrary TTS parameters, arbitrary Godot scripts and path escapes before process launch.
- Create JSON schemas for the root contracts and tests proving canonical round-trip/digest stability across Windows and Ubuntu path representations.

## Deliverables

- `src/kodepoia/media/__init__.py`.
- `src/kodepoia/media/contracts.py`.
- `src/kodepoia/media/serialization.py`.
- `src/kodepoia/media/boundary.py`.
- R11 root JSON schemas under `schemas/r11/`.
- `tests/test_r11_1_media_contracts.py`.
- `docs/roadmap/R11_1_DESIGN.md` and `R11_1_ACCEPTANCE.md`.

## Acceptance gates / Definition of Done

- Focused contract/path/process-policy tests pass.
- Canonical serialization/digest tests are deterministic on Ubuntu/Windows.
- No API equivalent to `run_shell`, `run_ffmpeg(args)`, `run_tts(code)` or arbitrary Godot script execution exists.
- R0 Repository Guard, full Python Core and KodeStudio UI Smoke are SUCCESS on one exact head.
- R7/R8/R9/R10 canonical integrated evidence remains present and unchanged; missing prior evidence blocks acceptance.

A subdivision is never COMPLETE from partial CI, a green subset of jobs, an unverified local claim, or a later commit that was not re-gated. Merge uses the exact accepted head SHA.

## Validation and evidence

- Exact candidate SHA and all workflow run IDs.
- schema validation logs.
- focused pytest names/counts.
- proof that no real external media runtime was required.

## Rollback / recovery

Revert the R11.1 implementation commit/PR. No durable project data migration exists yet. Delete only R11-scoped schemas/code introduced by this subdivision; do not alter R1–R10 foundations or evidence.

## Risks and regression traps

- Accidentally creating a generic process escape.
- Conflating runtime/model display names with identity.
- Path canonicalization differences on Windows.
- Schema drift before later subdivisions depend on the roots.
- Retrospective modification of prior acceptance evidence.

## Manual intervention

**NONE.** No user-side runtime execution is required; pure Python/fake-process fixtures are authoritative for this boundary subdivision.

For REQUIRED/triggered CONDITIONAL gates, the exact candidate SHA, prerequisites, copy-paste command/UI actions, expected output, failure recovery, evidence-to-return and privacy/redaction instructions MUST be frozen in the subdivision acceptance work before the manual run. Manual PASS is never inferred from silence.

## Completion record

When accepted, append the immutable implementation head, authoritative CI run IDs/conclusions, required/triggered local evidence identity, PR/merge SHA, post-merge normalization PR/merge when used, and final subdivision status `COMPLETE`. Do not rewrite earlier immutable evidence to make later history look cleaner.

---

# R11.2 — Audio ingest/transcode/analysis + deterministic QA

## Objective and rationale

Create the governed audio inspection, transform and QA layer before semantic cues or voice production depend on it.

## In scope

- deterministic WAV/PCM parser fixtures.
- optional ffprobe JSON inspection adapter.
- bounded resample/channel/trim/fade/normalize/transcode recipes.
- R8 source→derived transform lineage.
- duration/sample-rate/channel/bit-depth/codec/container facts.
- clipping/silence/loudness/true-peak facts where runtime capability exists.
- loop-boundary measurements and audio budget enforcement.
- corrupt/truncated/oversized media rejection.
- AudioQAReport schema and profile policies.

## Out of scope

- No creative music generation.
- No TTS.
- No background microphone capture.
- No arbitrary ffmpeg filter graph.
- No mastering quality claim beyond measured profile facts.

## Dependencies and prerequisites

R11.1 COMPLETE; R6 Budget/QA; R8 asset lineage. The branch point must be the exact normalized `main` produced by the preceding accepted work cycle. Required external runtimes, if any, must be discovered/configured through accepted boundaries; no download is implied by this dependency.

## Detailed implementation plan

- Implement a pure-Python WAV fixture parser sufficient to make hosted acceptance independent of ffmpeg availability.
- Add `FFprobeAdapter` only through R11.1 boundary with fixed `-of json`/allowlisted inspection options and bounded JSON size/depth.
- Represent transformations as typed recipes with allowlisted operation enums and bounded parameters; compile recipes to fixed process templates only inside trusted code.
- Persist source/output SHA-256, byte size, runtime identity, recipe identity and R8 lineage.
- Implement QA thresholds as explicit profiles; loudness normalization uses measured EBU R128-compatible facts when supported but targets remain project policy, not universal constants.
- Fail closed on malformed streams, multiple unexpected streams, path escapes, unbounded duration/output or unavailable codec capability.

## Deliverables

- audio parser/inspection/transform/QA modules under `src/kodepoia/media/audio/`.
- AudioQA and transform schemas.
- synthetic WAV fixtures.
- fake ffprobe/ffmpeg fixtures.
- `tests/test_r11_2_audio_pipeline.py`.
- design/acceptance docs.
- conditional local collector/schema only if real-runtime claim is triggered.

## Acceptance gates / Definition of Done

- Pure-Python fixtures cover valid/corrupt/truncated/oversized WAV cases.
- ffprobe JSON parser rejects malformed/oversized/unexpected output.
- Transform recipe identity is deterministic and path-safe.
- QA states and R6 budget overruns fail closed.
- Full R0/Python/UI gates are green on exact head.
- If an accepted claim depends on concrete ffmpeg behavior unavailable in CI, CONDITIONAL local evidence is satisfied before merge.

A subdivision is never COMPLETE from partial CI, a green subset of jobs, an unverified local claim, or a later commit that was not re-gated. Merge uses the exact accepted head SHA.

## Validation and evidence

- Exact head/workflow IDs.
- fixture input/output hashes.
- AudioQA report examples.
- ffmpeg/ffprobe version/capability JSON if conditional gate triggers.

## Rollback / recovery

Revert R11.2 code and derived test fixtures. Any generated project asset remains an R8 derived revision and can be invalidated/rebuilt from its source recipe; no source asset is overwritten in place.

## Risks and regression traps

- Codec/version behavior differences.
- Decompression bombs or huge duration metadata.
- Loudness metric misuse.
- Output path spoofing.
- Non-deterministic metadata fields entering identity.

## Manual intervention

**CONDITIONAL.** Trigger only when final acceptance claims ffmpeg/ffprobe behavior not authoritatively covered by hosted capability-compatible runtime. Then run the exact repository collector on the candidate SHA with repository synthetic fixtures. No private audio, automatic installation, network access or unrelated path disclosure is required.

For REQUIRED/triggered CONDITIONAL gates, the exact candidate SHA, prerequisites, copy-paste command/UI actions, expected output, failure recovery, evidence-to-return and privacy/redaction instructions MUST be frozen in the subdivision acceptance work before the manual run. Manual PASS is never inferred from silence.

## Completion record

When accepted, append the immutable implementation head, authoritative CI run IDs/conclusions, required/triggered local evidence identity, PR/merge SHA, post-merge normalization PR/merge when used, and final subdivision status `COMPLETE`. Do not rewrite earlier immutable evidence to make later history look cleaner.

---

# R11.3 — Music/SFX/Foley cue system + loops/variants/spatialization packaging

## Objective and rationale

Represent production audio semantically rather than as loose filenames, while preserving R8 identity and R5 playback authority.

## In scope

- AudioCueDefinition categories for music/ambience/SFX/Foley/UI/dialogue-support.
- one-shot/loop/playlist/randomized/weighted variants.
- loop regions, pre-roll/tail/crossfade policy.
- deterministic variant selection seed.
- 2D/3D spatialization intent.
- attenuation/profile metadata.
- bus target/priority/polyphony/cooldown/ducking intent.
- R8 refs and QA/rights promotion gates.
- R5 Godot packaging intent.

## Out of scope

- No DAW replacement.
- No AI music model.
- No runtime mixer replacement.
- No raw `.tres` text injection.

## Dependencies and prerequisites

R11.1–R11.2 COMPLETE; R5/R8 accepted. The branch point must be the exact normalized `main` produced by the preceding accepted work cycle. Required external runtimes, if any, must be discovered/configured through accepted boundaries; no download is implied by this dependency.

## Detailed implementation plan

- Create cue/cue-set contracts referencing R8 asset revisions, never raw paths.
- Validate every referenced asset has accepted R11.2 QA state and non-blocked rights/provenance.
- Implement deterministic variant selection for seeded preview/testing and explicit nondeterministic runtime policy flag when desired by product design.
- Map spatial/bus/polyphony intent to an R5 adapter contract; keep engine resource materialization inside R5 boundaries.
- Measure loop edge discontinuity/crossfade configuration from R11.2 facts and block invalid loop definitions under strict profiles.

## Deliverables

- cue contracts/schemas.
- Godot audio packaging intent adapter interface.
- loop/variation fixtures.
- `tests/test_r11_3_audio_cues.py`.
- design/acceptance docs.

## Acceptance gates / Definition of Done

- Cue round-trip/digest deterministic.
- Invalid/stale/missing R8 refs fail closed.
- Variant selection/weights/seed behavior is tested.
- Loop/spatialization/bus budgets are validated.
- R0/Python/UI exact-head gates pass.

A subdivision is never COMPLETE from partial CI, a green subset of jobs, an unverified local claim, or a later commit that was not re-gated. Merge uses the exact accepted head SHA.

## Validation and evidence

- Exact SHA/run IDs.
- representative cue manifests.
- deterministic variant test vectors.
- R8 lineage references.

## Rollback / recovery

Remove R11.3 semantic cue definitions/adapters. Existing audio assets remain intact in R8. Any generated Godot packaging artifacts are derived and rebuildable.

## Risks and regression traps

- Hidden filename identity.
- Randomness breaking reproducibility.
- Invalid loop seams.
- Over-polyphony/performance regression.
- Bus rename semantics drifting from Godot project config.

## Manual intervention

**NONE.** Hosted deterministic fixtures and accepted R5 contracts are authoritative; no user-side playback judgment is required for acceptance.

For REQUIRED/triggered CONDITIONAL gates, the exact candidate SHA, prerequisites, copy-paste command/UI actions, expected output, failure recovery, evidence-to-return and privacy/redaction instructions MUST be frozen in the subdivision acceptance work before the manual run. Manual PASS is never inferred from silence.

## Completion record

When accepted, append the immutable implementation head, authoritative CI run IDs/conclusions, required/triggered local evidence identity, PR/merge SHA, post-merge normalization PR/merge when used, and final subdivision status `COMPLETE`. Do not rewrite earlier immutable evidence to make later history look cleaner.

---

# R11.4 — Voice Profiles, pronunciation/prosody + rights/provenance governance

## Objective and rationale

Separate durable character voice intent from any one engine/model and make rights/provenance first-class before TTS synthesis begins.

## In scope

- VoiceProfile IDs and character/role scopes.
- locales/fallback locales.
- bounded pace/pitch/energy/style intents.
- PronunciationLexicon with locale-aware overrides.
- VoiceModelBinding separate from profile identity.
- license/provenance/allowed-use declarations.
- RIGHTS_BLOCKED state.
- consent/authorization reference fields for applicable synthetic voice packages.
- Unicode/text normalization policy.
- small typed markup allowlist only.

## Out of scope

- No voice cloning/training.
- No biometric speaker verification.
- No age/gender/identity inference from voice.
- No real synthesis.

## Dependencies and prerequisites

R11.1 COMPLETE; R7/R8 governance. The branch point must be the exact normalized `main` produced by the preceding accepted work cycle. Required external runtimes, if any, must be discovered/configured through accepted boundaries; no download is implied by this dependency.

## Detailed implementation plan

- Define VoiceProfile as engine-neutral intent and separate it from runtime/model identity.
- Normalize locale tags, text and pronunciation keys canonically; preserve original display text separately from identity text where needed.
- Require explicit provenance/license metadata for every voice model binding; unknown or prohibited use blocks synthesis promotion.
- Treat any reference recording metadata as sensitive governed data; do not store unrelated personal paths or hidden EXIF-like metadata.
- Reject arbitrary SSML/XML/script payloads; expose only typed supported controls.

## Deliverables

- voice profile/pronunciation/provenance modules.
- schemas.
- Unicode/adversarial fixtures.
- `tests/test_r11_4_voice_profiles.py`.
- design/acceptance docs.

## Acceptance gates / Definition of Done

- Schema/round-trip and locale fallback tests pass.
- Unicode/bidi/control-character tests cannot inject instructions or paths.
- Rights/provenance missing/blocked cases cannot produce accepted model bindings.
- No voice cloning/training surface exists.
- Full exact-head gates pass.

A subdivision is never COMPLETE from partial CI, a green subset of jobs, an unverified local claim, or a later commit that was not re-gated. Merge uses the exact accepted head SHA.

## Validation and evidence

- Exact SHA/run IDs.
- schema examples with synthetic voices only.
- rights/provenance state test matrix.

## Rollback / recovery

Revert profile/lexicon contracts. No voice model bytes are altered; R8 assets remain source of truth.

## Risks and regression traps

- Conflating character identity with biometric identity.
- License metadata ambiguity.
- Locale fallback silently changing pronunciation.
- Markup injection.
- Storing sensitive reference data in evidence.

## Manual intervention

**NONE.** All behavior is contract/governance logic testable with synthetic metadata; no real voice or personal recording is needed.

For REQUIRED/triggered CONDITIONAL gates, the exact candidate SHA, prerequisites, copy-paste command/UI actions, expected output, failure recovery, evidence-to-return and privacy/redaction instructions MUST be frozen in the subdivision acceptance work before the manual run. Manual PASS is never inferred from silence.

## Completion record

When accepted, append the immutable implementation head, authoritative CI run IDs/conclusions, required/triggered local evidence identity, PR/merge SHA, post-merge normalization PR/merge when used, and final subdivision status `COMPLETE`. Do not rewrite earlier immutable evidence to make later history look cleaner.

---

# R11.5 — Multilingual local TTS adapters, synthesis cache + real-runtime acceptance

## Objective and rationale

Produce governed multilingual speech assets through local structured adapters while preserving runtime/model/voice identity, reproducibility and user control.

## In scope

- backend-neutral TTSBackend contract/capability probe.
- initial Piper-compatible external adapter when prerequisites are satisfied.
- optional Godot system-TTS adapter for accessibility/runtime speech only.
- bounded text/locale/speaker/rate/pitch/prosody parameters.
- deterministic synthesis request/cache identity.
- ProcessSandbox fixed execution contract.
- offline/no-network policy.
- output duration/bytes/time/chunk limits.
- WAV/PCM validation through R11.2.
- synthesis manifest and local evidence schema.
- cancellation/KillSwitch/resource exhaustion.

## Out of scope

- No model training.
- No voice cloning.
- No automatic voice/model download.
- No cloud TTS.
- No arbitrary engine flags.

## Dependencies and prerequisites

R11.1–R11.4 COMPLETE; R8 asset governance; R9 resource arbitration if GPU used. The branch point must be the exact normalized `main` produced by the preceding accepted work cycle. Required external runtimes, if any, must be discovered/configured through accepted boundaries; no download is implied by this dependency.

## Detailed implementation plan

- Implement adapter registry based on typed capabilities; absence of a backend is `UNAVAILABLE`, not failure of the whole phase.
- For Piper, treat executable/package and voice files as separately identified external resources; do not vendor or redistribute them.
- Generate a canonical SynthesisDefinitionId from normalized text, VoiceProfile, lexicon, model/runtime IDs and bounded config.
- Stage outputs under WorkspaceBoundary, validate bytes with R11.2, then promote via R8 only if QA and rights pass.
- Cache only by canonical request+runtime+model identity; stale runtime/model changes invalidate cache.
- Collector emits a privacy-minimized JSON evidence file with runtime/model digests, locale, neutral test-text digest, output digest, duration/sample facts, limits and blockers.

## Deliverables

- TTS backend contracts/registry.
- Piper-compatible adapter.
- system-TTS capability adapter (non-canonical production role).
- synthesis/cache modules/schemas.
- fake backend fixtures.
- real-runtime local collector/schema.
- `tests/test_r11_5_tts.py`.
- design/acceptance docs.

## Acceptance gates / Definition of Done

- Hosted fake backends cover success/failure/timeout/cancel/malformed output/cache behavior.
- No network/model download is attempted.
- Real local synthesis succeeds on exact candidate SHA using an explicitly configured accepted runtime and at least one licensed/configured voice model.
- Output passes R11.2 QA and evidence verifies exact runtime/model/input/output identities.
- R0/Python/UI exact-head gates pass before and after accepted local evidence documentation as required.

A subdivision is never COMPLETE from partial CI, a green subset of jobs, an unverified local claim, or a later commit that was not re-gated. Merge uses the exact accepted head SHA.

## Validation and evidence

- Exact candidate SHA and workflow IDs.
- local TTS evidence JSON.
- runtime and model version/digest.
- locale and neutral input digest.
- output WAV digest and QA facts.
- explicit manual status REQUIRED SATISFIED.

## Rollback / recovery

Revert adapter code; delete only staged/cache outputs for the candidate. Do not delete user-installed runtimes/models. R8 promoted derived outputs can be invalidated without touching source models.

## Risks and regression traps

- GPL/runtime redistribution confusion.
- Voice model license ambiguity.
- Backend version drift.
- Unbounded synthesis time/output.
- Text injection into CLI.
- Cache poisoning.
- GPU memory contention.

## Manual intervention

**REQUIRED.** Required because hosted CI cannot authoritatively provide the user-approved local TTS runtime and voice model without violating no-auto-download/provenance constraints. Before the gate the implementation must emit one exact copy-paste collector command tied to the candidate SHA. Use neutral repository text only; return the generated JSON. If runtime/model is missing, license is unclear, network access is requested, or output escapes staging, stop and report instead of improvising. Redact secrets and unrelated personal paths.

For REQUIRED/triggered CONDITIONAL gates, the exact candidate SHA, prerequisites, copy-paste command/UI actions, expected output, failure recovery, evidence-to-return and privacy/redaction instructions MUST be frozen in the subdivision acceptance work before the manual run. Manual PASS is never inferred from silence.

## Completion record

When accepted, append the immutable implementation head, authoritative CI run IDs/conclusions, required/triggered local evidence identity, PR/merge SHA, post-merge normalization PR/merge when used, and final subdivision status `COMPLETE`. Do not rewrite earlier immutable evidence to make later history look cleaner.

---

# R11.6 — Speech alignment, phoneme/viseme timeline + lip-sync QA

## Objective and rationale

Turn synthesized/approved speech into deterministic facial timing data without trusting backend-specific token streams as durable semantics.

## In scope

- word/phoneme alignment timeline.
- backend-provided timing adapter.
- deterministic synthetic fallback fixtures.
- versioned phoneme→viseme mapping sets.
- silence/rest/coarticulation windows.
- smoothing constraints.
- VisemeTimeline identity.
- lip-sync QA for monotonicity/overlap/duration/density/drift.
- caption/subtitle timing bridge under R6 accessibility/localization.

## Out of scope

- No arbitrary forced-alignment model download.
- No facial target mutation.
- No cinematic assembly.

## Dependencies and prerequisites

R11.4–R11.5 COMPLETE. The branch point must be the exact normalized `main` produced by the preceding accepted work cycle. Required external runtimes, if any, must be discovered/configured through accepted boundaries; no download is implied by this dependency.

## Detailed implementation plan

- Normalize backend timing into an engine-neutral timeline with source and confidence.
- Reject negative/non-finite/non-monotonic or out-of-duration timings.
- Map normalized phonemes to a versioned viseme set; unknown phonemes use explicit fallback semantics, never silent arbitrary mapping.
- Generate deterministic smoothing/coarticulation windows with bounded overlap.
- Compare final timeline duration to accepted audio duration and emit drift metrics.
- Keep subtitles/captions as separate accessibility text artifacts linked by timing, not as the authority for phoneme identity.

## Deliverables

- alignment/viseme modules/schemas.
- phoneme→viseme mapping fixtures.
- timing adversarial fixtures.
- conditional local timing collector if triggered.
- `tests/test_r11_6_lipsync.py`.
- design/acceptance docs.

## Acceptance gates / Definition of Done

- Synthetic timelines deterministic.
- Malformed/non-finite timing fails closed.
- Unknown phoneme and silence handling tested.
- Drift/event-density budgets enforced.
- If production acceptance depends on backend-native timing unavailable in CI, local evidence is collected on exact head.
- Full exact-head gates pass.

A subdivision is never COMPLETE from partial CI, a green subset of jobs, an unverified local claim, or a later commit that was not re-gated. Merge uses the exact accepted head SHA.

## Validation and evidence

- Exact head/run IDs.
- timeline digests.
- audio duration/drift metrics.
- conditional timing evidence if used.

## Rollback / recovery

Revert derived alignment/viseme artifacts; source audio and TTS evidence remain intact and can regenerate timelines.

## Risks and regression traps

- Backend timing units mismatch.
- Locale phoneme inventory differences.
- Coarticulation causing overlap explosion.
- Confidence misuse.
- Subtitles silently becoming canonical pronunciation.

## Manual intervention

**CONDITIONAL.** Trigger only when accepted production behavior relies on backend/native phoneme timing or an external aligner not reproducible in hosted CI. Use the already accepted R11.5 runtime/model and repository neutral audio/text; no new private recording or download.

For REQUIRED/triggered CONDITIONAL gates, the exact candidate SHA, prerequisites, copy-paste command/UI actions, expected output, failure recovery, evidence-to-return and privacy/redaction instructions MUST be frozen in the subdivision acceptance work before the manual run. Manual PASS is never inferred from silence.

## Completion record

When accepted, append the immutable implementation head, authoritative CI run IDs/conclusions, required/triggered local evidence identity, PR/merge SHA, post-merge normalization PR/merge when used, and final subdivision status `COMPLETE`. Do not rewrite earlier immutable evidence to make later history look cleaner.

---

# R11.7 — Facial performance mapping + facial LOD + R10/R5 integration

## Objective and rationale

Map viseme/expression semantics onto validated character facial controls while keeping R10 geometry/rig authority and R5 runtime animation authority intact.

## In scope

- FacialPerformanceProfile.
- viseme/expression→R10 blend-shape/bone semantic mapping.
- target existence/range validation.
- additive/blended weighting and smoothing.
- facial LOD tiers.
- curve sampling/key-density budgets.
- R5 Godot animation intent adapter.
- neutral synthetic face fixture.
- QA for missing targets/invalid weights/drift/LOD preservation.

## Out of scope

- No topology changes.
- No rig generation.
- No free-form Blender editing.
- No photoreal facial solver.

## Dependencies and prerequisites

R11.6 COMPLETE; R10 facial-ready targets; R5 Godot contracts. The branch point must be the exact normalized `main` produced by the preceding accepted work cycle. Required external runtimes, if any, must be discovered/configured through accepted boundaries; no download is implied by this dependency.

## Detailed implementation plan

- Reference R10 target identities/metadata rather than mesh-local names whenever possible.
- Validate all mapped targets exist and permitted ranges are respected before curve generation.
- Generate curves deterministically from VisemeTimeline + expression layers; clamp only according to explicit profile policy and report clipping.
- Define facial LOD as semantic target-reduction/sampling policy with preservation assertions for mouth closure/opening and critical expressions.
- Produce R5 animation intent, not raw Godot scene/resource text.

## Deliverables

- facial profile/curve/LOD modules/schemas.
- R10 target adapter.
- R5 facial animation intent adapter.
- synthetic target fixtures.
- conditional real-target collector if triggered.
- `tests/test_r11_7_facial.py`.
- design/acceptance docs.

## Acceptance gates / Definition of Done

- Missing/spoofed R10 targets fail closed.
- Weights/key density/LOD budgets tested.
- Generated curves deterministic.
- R5 intent validates without raw script/resource injection.
- Conditional runtime evidence satisfied only if claimed behavior cannot be proved from accepted metadata/CI.
- Full gates pass.

A subdivision is never COMPLETE from partial CI, a green subset of jobs, an unverified local claim, or a later commit that was not re-gated. Merge uses the exact accepted head SHA.

## Validation and evidence

- Exact SHA/run IDs.
- profile/curve digests.
- LOD preservation report.
- conditional runtime evidence if triggered.

## Rollback / recovery

Discard derived facial curves/profiles from candidate; R10 source rigs/meshes remain untouched.

## Risks and regression traps

- Target-name drift.
- Overdriven blend shapes.
- Curve explosion.
- LOD losing intelligibility.
- Accidental R10 topology mutation.

## Manual intervention

**CONDITIONAL.** Trigger only for a real R10/Godot facial behavior claim not provable from existing accepted metadata. Use repository test assets, not personal likenesses; return machine-readable hashes/target/curve/import facts.

For REQUIRED/triggered CONDITIONAL gates, the exact candidate SHA, prerequisites, copy-paste command/UI actions, expected output, failure recovery, evidence-to-return and privacy/redaction instructions MUST be frozen in the subdivision acceptance work before the manual run. Manual PASS is never inferred from silence.

## Completion record

When accepted, append the immutable implementation head, authoritative CI run IDs/conclusions, required/triggered local evidence identity, PR/merge SHA, post-merge normalization PR/merge when used, and final subdivision status `COMPLETE`. Do not rewrite earlier immutable evidence to make later history look cleaner.

---

# R11.8 — Cinematic shots, sequences + deterministic timeline model

## Objective and rationale

Create a portable cinematic representation before binding it to Godot capture/runtime specifics.

## In scope

- ShotDefinition.
- SequenceTimeline.
- camera/body/facial/dialogue/music/SFX/Foley/subtitle/event tracks.
- markers and nested sequences.
- deterministic branches/conditions.
- rational/fixed FPS timebase conversion.
- gap/overlap/ref/budget validation.
- canonical serialization/diff summaries.
- R8 refs only.

## Out of scope

- No live Godot capture.
- No NLE replacement.
- No arbitrary scripted event execution.

## Dependencies and prerequisites

R11.1–R11.7 COMPLETE. The branch point must be the exact normalized `main` produced by the preceding accepted work cycle. Required external runtimes, if any, must be discovered/configured through accepted boundaries; no download is implied by this dependency.

## Detailed implementation plan

- Represent timeline times in a canonical rational/frame-aware form to avoid float drift.
- Separate declarative events from executable runtime code; event kinds and payload schemas are allowlisted.
- Validate shot/sequence refs against accepted asset/profile identities.
- Support deterministic branch evaluation inputs for tests; runtime gameplay conditions remain R5/product concerns.
- Produce compact canonical timeline and human-readable diagnostics separately.

## Deliverables

- cinematic timeline modules/schemas.
- timebase utilities.
- synthetic sequence fixtures.
- `tests/test_r11_8_cinematics.py`.
- design/acceptance docs.

## Acceptance gates / Definition of Done

- Time/frame conversion deterministic at supported FPS values.
- Gaps/overlaps/missing refs/non-monotonic events fail according to policy.
- Arbitrary event code rejected.
- Branch fixtures deterministic.
- Full exact-head gates pass.

A subdivision is never COMPLETE from partial CI, a green subset of jobs, an unverified local claim, or a later commit that was not re-gated. Merge uses the exact accepted head SHA.

## Validation and evidence

- Exact SHA/run IDs.
- timeline digests.
- frame/time test vectors.
- validation report fixtures.

## Rollback / recovery

Revert timeline definitions and derived fixtures; referenced media/facial assets remain unchanged.

## Risks and regression traps

- Floating-point drift.
- Executable event smuggling.
- Branch nondeterminism.
- Huge nested timelines.
- Cross-reference cycles.

## Manual intervention

**NONE.** Timeline semantics are fully testable with synthetic fixtures; no user-side engine run is required.

For REQUIRED/triggered CONDITIONAL gates, the exact candidate SHA, prerequisites, copy-paste command/UI actions, expected output, failure recovery, evidence-to-return and privacy/redaction instructions MUST be frozen in the subdivision acceptance work before the manual run. Manual PASS is never inferred from silence.

## Completion record

When accepted, append the immutable implementation head, authoritative CI run IDs/conclusions, required/triggered local evidence identity, PR/merge SHA, post-merge normalization PR/merge when used, and final subdivision status `COMPLETE`. Do not rewrite earlier immutable evidence to make later history look cleaner.

---

# R11.9 — Godot 4.7 cinematic assembly, movie capture + A/V sync acceptance

## Objective and rationale

Prove governed R11 timelines can be assembled through accepted R5 Godot contracts and captured deterministically with synchronized audio/video evidence.

## In scope

- R5-owned cinematic materialization adapter.
- allowlisted AnimationPlayer/audio/facial/body/camera track generation.
- fixed timebase mapping.
- governed Godot `--write-movie`/`--fixed-fps` invocation.
- bounded output staging.
- frame/duration/resolution limits.
- KillSwitch/cancellation.
- post-capture media/ffprobe validation.
- A/V duration/sync metrics.
- local collector with synthetic cinematic fixture.

## Out of scope

- No unrestricted Godot script execution.
- No gameplay logic generation.
- No NLE/editing suite.
- No encoder/plugin auto-install.

## Dependencies and prerequisites

R11.3 + R11.7–R11.8 COMPLETE; R5 Godot 4.7 accepted. The branch point must be the exact normalized `main` produced by the preceding accepted work cycle. Required external runtimes, if any, must be discovered/configured through accepted boundaries; no download is implied by this dependency.

## Detailed implementation plan

- Translate R11 timeline intents through R5 typed adapters only; never generate raw arbitrary GDScript from model input.
- Use the previously accepted Godot executable selection/policy and a fixed movie-capture command template.
- Stage a deterministic synthetic scene with synthetic audio/facial/body data and fixed FPS/resolution.
- Record expected frame/audio duration facts before launch; validate captured output container/streams/duration afterward.
- Emit sync metrics and output SHA-256; reject partial/truncated capture or unexpected external file writes.
- Collector must be copy-paste runnable against exact candidate SHA and require no private project assets.

## Deliverables

- Godot cinematic adapter.
- capture runner/manifest schema.
- synthetic capture fixture/project.
- A/V sync verifier.
- required local collector/schema.
- `tests/test_r11_9_godot_cinematic.py`.
- design/acceptance docs.

## Acceptance gates / Definition of Done

- Hosted fake runner covers command policy/failure/timeout/cancel/output spoofing.
- Real Godot 4.7 capture succeeds on exact candidate SHA.
- Captured evidence has expected FPS/frame count/resolution/audio facts within frozen tolerances and correct digest.
- No output escapes staging and no unapproved script/process surface is exposed.
- R0/Python/UI gates pass before/after local evidence documentation as required.

A subdivision is never COMPLETE from partial CI, a green subset of jobs, an unverified local claim, or a later commit that was not re-gated. Merge uses the exact accepted head SHA.

## Validation and evidence

- Exact SHA/run IDs.
- Godot version/runtime identity.
- capture command policy ID.
- fixture/input hashes.
- movie/output digest.
- frame/FPS/resolution/audio duration/sync metrics.
- manual REQUIRED SATISFIED record.

## Rollback / recovery

Delete only staged synthetic capture output and revert adapter code. Do not modify the user's real project. R5/R11 source assets remain unchanged.

## Risks and regression traps

- Headless/movie writer platform differences.
- A/V drift.
- Renderer/audio driver variance.
- Output file path escape.
- Partial capture accepted as success.
- Godot version mismatch.

## Manual intervention

**REQUIRED.** Required because unit tests cannot establish actual Godot 4.7 movie-writer/import/animation behavior. Run only the exact repository collector on the candidate SHA with the synthetic fixture. If Godot is missing/wrong version or capture fails, return failure evidence; do not edit generated files manually or use a private project to force PASS.

For REQUIRED/triggered CONDITIONAL gates, the exact candidate SHA, prerequisites, copy-paste command/UI actions, expected output, failure recovery, evidence-to-return and privacy/redaction instructions MUST be frozen in the subdivision acceptance work before the manual run. Manual PASS is never inferred from silence.

## Completion record

When accepted, append the immutable implementation head, authoritative CI run IDs/conclusions, required/triggered local evidence identity, PR/merge SHA, post-merge normalization PR/merge when used, and final subdivision status `COMPLETE`. Do not rewrite earlier immutable evidence to make later history look cleaner.

---

# R11.10 — Continuity Bridge across scenes/projects

## Objective and rationale

Preserve narrative/character/world continuity when moving between shots, scenes and projects without turning free-form prose into ungoverned persistent truth.

## In scope

- ContinuitySnapshot scopes: shot/sequence/scene/project/franchise.
- character/world/time/location and profile/ref state.
- before/after structured comparison.
- severity/policy findings.
- source authority and content-version refs.
- R8 governed bridge import/export.
- explicit conflict/stale/missing states.
- deterministic diff/report schemas.

## Out of scope

- No free-form dialogue auto-promotes to canon.
- No cloud sync.
- No automatic conflict resolution without policy.

## Dependencies and prerequisites

R11.8–R11.9 COMPLETE; R2/R8 accepted. The branch point must be the exact normalized `main` produced by the preceding accepted work cycle. Required external runtimes, if any, must be discovered/configured through accepted boundaries; no download is implied by this dependency.

## Detailed implementation plan

- Define a typed extensible snapshot envelope with core fields and namespaced extension points.
- Require each durable fact/ref to carry source authority and version/scope metadata.
- Compare snapshots structurally and emit stable finding IDs for regressions/waivers.
- Keep stale/deleted/missing refs explicit; never silently drop them during import.
- Use R8 artifact transport/lineage for cross-project bridge packages.

## Deliverables

- continuity bridge modules/schemas.
- diff/report model.
- cross-scene/project fixtures.
- `tests/test_r11_10_continuity.py`.
- design/acceptance docs.

## Acceptance gates / Definition of Done

- Deterministic snapshot identity/diff.
- Conflict/stale/missing ref fixtures behave fail-closed.
- Cross-project import cannot escape allowed scopes or mutate canon automatically.
- Full exact-head gates pass.

A subdivision is never COMPLETE from partial CI, a green subset of jobs, an unverified local claim, or a later commit that was not re-gated. Merge uses the exact accepted head SHA.

## Validation and evidence

- Exact SHA/run IDs.
- snapshot/diff digests.
- cross-project fixture reports.

## Rollback / recovery

Remove R11.10 bridge artifacts and regenerate from source scene/project state. No source project data is overwritten by a compare operation.

## Risks and regression traps

- Snapshot becoming a second save system.
- Implicit canon promotion.
- Cross-project ID collisions.
- Stale refs silently discarded.
- Unbounded snapshot growth.

## Manual intervention

**NONE.** Synthetic multi-project fixtures are authoritative; no user-side project is required.

For REQUIRED/triggered CONDITIONAL gates, the exact candidate SHA, prerequisites, copy-paste command/UI actions, expected output, failure recovery, evidence-to-return and privacy/redaction instructions MUST be frozen in the subdivision acceptance work before the manual run. Manual PASS is never inferred from silence.

## Completion record

When accepted, append the immutable implementation head, authoritative CI run IDs/conclusions, required/triggered local evidence identity, PR/merge SHA, post-merge normalization PR/merge when used, and final subdivision status `COMPLETE`. Do not rewrite earlier immutable evidence to make later history look cleaner.

---

# R11.11 — Franchise DNA + versioned Canon graph/conflict policy

## Objective and rationale

Represent long-lived multi-project invariants and canonical facts explicitly so future projects can reuse a franchise without silently rewriting history.

## In scope

- FranchiseDNA identity/invariants.
- compatible Project DNA refs.
- shared style/world/technology/rating/locale/naming policies.
- CanonRecord and CanonSnapshot.
- authority tiers.
- temporal/content-version validity.
- supersedes/deprecates links.
- deterministic conflict detection.
- canon query with evidence/source refs.
- proposed→reviewed→canonical/deprecated workflow.
- R7 research suggestions remain proposed only.

## Out of scope

- No graph database server.
- No cloud collaboration backend.
- No automatic legal/IP determination.
- No automatic conflict winner when policy ambiguous.

## Dependencies and prerequisites

R11.10 COMPLETE; R2/R7/R8 accepted. The branch point must be the exact normalized `main` produced by the preceding accepted work cycle. Required external runtimes, if any, must be discovered/configured through accepted boundaries; no download is implied by this dependency.

## Detailed implementation plan

- Model Franchise DNA separately from R2 Project DNA and link compatible projects explicitly.
- Represent canon as immutable versioned records/snapshots; updates create new records/snapshots rather than mutating historical evidence invisibly.
- Define authority tiers and conflict rules; ambiguous conflicts remain `CONFLICTED` and block dependent promotion under strict policy.
- Require Guardian/Audit/SafeChange for durable canonical promotion/deprecation.
- Ensure R7 external sources can propose evidence but cannot directly set canonical authority.

## Deliverables

- franchise/canon modules/schemas.
- query/conflict engine.
- promotion/audit hooks.
- fixtures.
- `tests/test_r11_11_franchise_canon.py`.
- design/acceptance docs.

## Acceptance gates / Definition of Done

- Graph/reference integrity and deterministic queries.
- Authority/conflict/deprecation/supersession tests.
- External research cannot auto-promote to canon.
- Historical canon snapshots remain verifiable.
- Full gates pass.

A subdivision is never COMPLETE from partial CI, a green subset of jobs, an unverified local claim, or a later commit that was not re-gated. Merge uses the exact accepted head SHA.

## Validation and evidence

- Exact SHA/run IDs.
- canon snapshot digests.
- conflict test matrix.
- Audit/SafeChange evidence for fixture promotions.

## Rollback / recovery

Rollback a proposed durable promotion via SafeChange and restore prior CanonSnapshot pointer; historical immutable records remain preserved for audit.

## Risks and regression traps

- Canon mutation without history.
- Circular supersession.
- Authority escalation.
- Research prompt injection into canon.
- Franchise DNA duplicating Project DNA.

## Manual intervention

**NONE.** All acceptance uses synthetic canon/franchise fixtures; no user-side content judgment is required.

For REQUIRED/triggered CONDITIONAL gates, the exact candidate SHA, prerequisites, copy-paste command/UI actions, expected output, failure recovery, evidence-to-return and privacy/redaction instructions MUST be frozen in the subdivision acceptance work before the manual run. Manual PASS is never inferred from silence.

## Completion record

When accepted, append the immutable implementation head, authoritative CI run IDs/conclusions, required/triggered local evidence identity, PR/merge SHA, post-merge normalization PR/merge when used, and final subdivision status `COMPLETE`. Do not rewrite earlier immutable evidence to make later history look cleaner.

---

# R11.12 — Persistence/SaveBridge schemas, migrations + compatibility/rollback

## Objective and rationale

Provide a safe bridge between runtime save state, continuity/canon versions and evolving project schemas while preserving rollback and explicit compatibility semantics.

## In scope

- SaveBridgeSchema/manifest.
- project/franchise/content/schema versions.
- canonical state envelope/checksum.
- runtime save vs canon separation.
- migration registry source→target.
- ordered deterministic/idempotent steps.
- dry-run + SafeChange snapshot + backup + verify + commit/rollback.
- unknown-field/extension policy.
- corruption/truncation/tamper detection.
- compatibility report states.
- bounded R5 save-location hooks.
- local-only baseline.

## Out of scope

- No backend/cloud saves.
- No account sync.
- No anti-cheat authority.
- No DRM/encryption-key infrastructure.

## Dependencies and prerequisites

R11.10–R11.11 COMPLETE; R1/R5/R6 foundations. The branch point must be the exact normalized `main` produced by the preceding accepted work cycle. Required external runtimes, if any, must be discovered/configured through accepted boundaries; no download is implied by this dependency.

## Detailed implementation plan

- Use typed data migrations, not arbitrary model-generated code strings. Migration functions are code-reviewed/allowlisted and version-addressed.
- Require a migration path graph with cycle detection and bounded step count.
- Always support dry-run and produce before/after canonical digests plus a deterministic diff summary.
- Before durable mutation, create SafeChange/Backup evidence; verify target schema/checksum and rollback on any failure.
- Treat newer unsupported schemas as explicit `UNSUPPORTED_NEWER`; never downgrade destructively by default.
- Keep Canon/Franchise refs versioned and report conflicts rather than rewriting canon from save data.

## Deliverables

- savebridge contracts/migration engine/schemas.
- compatibility verifier.
- rollback/snapshot integration.
- multi-version/corruption fixtures.
- conditional real-project collector if triggered.
- `tests/test_r11_12_savebridge.py`.
- design/acceptance docs.

## Acceptance gates / Definition of Done

- Multi-version synthetic migrations deterministic/idempotent.
- Injected failure proves rollback restores exact prior bytes/state.
- Corrupt/tampered/truncated/newer-version inputs fail closed.
- Migration graph cycles/path explosion blocked.
- Full gates pass.
- If concrete existing Godot-project save compatibility is claimed beyond accepted fixtures, conditional disposable-project evidence is satisfied.

A subdivision is never COMPLETE from partial CI, a green subset of jobs, an unverified local claim, or a later commit that was not re-gated. Merge uses the exact accepted head SHA.

## Validation and evidence

- Exact SHA/run IDs.
- before/after/rollback digests.
- migration path IDs.
- compatibility reports.
- conditional disposable-project evidence if triggered.

## Rollback / recovery

SafeChange snapshot/Backup is mandatory before durable migration; failure or rejected verification restores the exact pre-migration state. Migration code can be reverted without deleting historical schema definitions required to read older saves.

## Risks and regression traps

- Irreversible migration.
- Version downgrade confusion.
- Save data mutating canon.
- Unbounded migration path.
- Partial write/corruption.
- Scanning unrelated user save directories.

## Manual intervention

**CONDITIONAL.** Trigger only if final claims cover a concrete real project/save format beyond synthetic/accepted R5 fixtures. Use a disposable copy, default dry-run, exact candidate SHA, explicit backup, and return only structured evidence. Never operate on the sole copy of a real save.

For REQUIRED/triggered CONDITIONAL gates, the exact candidate SHA, prerequisites, copy-paste command/UI actions, expected output, failure recovery, evidence-to-return and privacy/redaction instructions MUST be frozen in the subdivision acceptance work before the manual run. Manual PASS is never inferred from silence.

## Completion record

When accepted, append the immutable implementation head, authoritative CI run IDs/conclusions, required/triggered local evidence identity, PR/merge SHA, post-merge normalization PR/merge when used, and final subdivision status `COMPLETE`. Do not rewrite earlier immutable evidence to make later history look cleaner.

---

# R11.13 — CLI + KodeStudio Audio/Voice/Cinematics/Franchise UX

## Objective and rationale

Expose R11 capabilities through stable structured workflows without surfacing raw process/model/script controls.

## In scope

- CLI groups for audio/cues/voice/synthesis/alignment/facial/cinematics/continuity/franchise/canon/savebridge.
- stable JSON output and exit semantics.
- KodeStudio Audio/Voice/Cinematics workspace.
- Franchise/Canon/Persistence views.
- runtime capability/status panels.
- rights/provenance blockers.
- budget/evidence summaries.
- progress/cancel/KillSwitch.
- accessibility/pseudo-localization/truncation coverage.

## Out of scope

- No DAW/NLE UI.
- No raw ffmpeg/Piper/Godot command editor.
- No free-form migration code editor.

## Dependencies and prerequisites

R11.1–R11.12 COMPLETE. The branch point must be the exact normalized `main` produced by the preceding accepted work cycle. Required external runtimes, if any, must be discovered/configured through accepted boundaries; no download is implied by this dependency.

## Detailed implementation plan

- Expose only high-level typed commands that call accepted domain services.
- Ensure every long-running runtime operation supports progress, cancellation and final evidence link.
- Add navigation without regressing existing R6 pseudo-localization expectation; update historical fixed counts only when intentional and preserve semantic assertions.
- Present blocked/missing rights/runtime/model/evidence states explicitly rather than hiding unavailable actions.
- Persist only non-sensitive UI preferences; never store secrets or personal voice paths in plain settings.

## Deliverables

- CLI registration/handlers.
- KodeStudio pages/widgets/models.
- localization strings.
- UI/CLI tests.
- `docs/roadmap/R11_13_DESIGN.md` and acceptance doc.

## Acceptance gates / Definition of Done

- CLI JSON/exit-code tests.
- KodeStudio smoke and navigation tests.
- Pseudo-localization/truncation/accessibility regressions pass.
- Cancellation/KillSwitch and blocked-state UX tested.
- No raw command/script surface exists.
- Full exact-head gates pass.

A subdivision is never COMPLETE from partial CI, a green subset of jobs, an unverified local claim, or a later commit that was not re-gated. Merge uses the exact accepted head SHA.

## Validation and evidence

- Exact SHA/run IDs.
- CLI golden JSON fixtures.
- UI smoke identifiers.
- localization regression results.

## Rollback / recovery

Revert R11.13 UI/CLI bindings; domain data and accepted runtime evidence remain intact and accessible to future re-exposure.

## Risks and regression traps

- Navigation count regression.
- UI exposing unsafe raw parameters.
- Long-running operations without cancel.
- Sensitive path leakage.
- Localization truncation.

## Manual intervention

**NONE.** No new runtime behavior is introduced; existing R11.5/R11.9 accepted evidence remains authoritative.

For REQUIRED/triggered CONDITIONAL gates, the exact candidate SHA, prerequisites, copy-paste command/UI actions, expected output, failure recovery, evidence-to-return and privacy/redaction instructions MUST be frozen in the subdivision acceptance work before the manual run. Manual PASS is never inferred from silence.

## Completion record

When accepted, append the immutable implementation head, authoritative CI run IDs/conclusions, required/triggered local evidence identity, PR/merge SHA, post-merge normalization PR/merge when used, and final subdivision status `COMPLETE`. Do not rewrite earlier immutable evidence to make later history look cleaner.

---

# R11.14 — Adversarial hardening + R11 integrated acceptance

## Objective and rationale

Red-team R11 across hostile media/text/timing/save/canon inputs and produce anti-circular phase evidence before R11 can be marked complete.

## In scope

- corrupt/truncated/oversized audio and forged metadata.
- path/URL/environment/argv/filter/model injection.
- malformed TTS output/result JSON and evidence substitution.
- Unicode/bidi/control-character attacks.
- NaN/inf/negative/non-monotonic timing.
- viseme/facial target spoofing.
- cinematic path/frame/duration/event injection.
- continuity/canon substitution/conflict masking/unauthorized promotion.
- save corruption/schema confusion/migration cycle/rollback failure injection.
- resource exhaustion/timeout/cancel/KillSwitch.
- R11 integrated acceptance schema/model/verifier.
- anti-circular evidence generation and final normalization.

## Out of scope

- No R12 implementation.
- No retrospective rewriting of R1–R10 evidence.

## Dependencies and prerequisites

R11.1–R11.13 COMPLETE. The branch point must be the exact normalized `main` produced by the preceding accepted work cycle. Required external runtimes, if any, must be discovered/configured through accepted boundaries; no download is implied by this dependency.

## Detailed implementation plan

- Build a dedicated adversarial suite that calls accepted R11 public contracts and verifies fail-closed behavior.
- Implement `R11_INTEGRATED_ACCEPTANCE.json` verifier binding R11.1–R11.14 acceptance docs, normalized continuity, required/triggered local evidence and prior R7/R8/R9/R10 integrated reports by repository identity/semantic digest.
- Use an anti-circular sequence: immutable implementation head → gates → freeze source SHA → generate report from immutable evidence → final evidence head → gates → merge → one continuity-only normalization → gates → merge.
- Reject stale/missing/substituted evidence, non-PASS required manual state, runtime/model identity drift, changed acceptance bytes, prior integrated report failure or explicit/derived blockers.
- Keep generated-at timestamps out of semantic digest where necessary to preserve deterministic evidence identity.

## Deliverables

- adversarial test suite.
- integrated acceptance model/verifier/script.
- R11 integrated JSON schema.
- `R11_14_DESIGN.md` and acceptance doc.
- canonical `R11_INTEGRATED_ACCEPTANCE.json` after immutable head acceptance.
- final continuity-only normalization.

## Acceptance gates / Definition of Done

- Dedicated adversarial suite passes.
- Full Ubuntu/Windows Python Core, package builds, R0 and UI Smoke green on exact heads.
- R7/R8/R9/R10 integrated reports still PASS.
- R11.5 and R11.9 REQUIRED evidence verifies against exact accepted heads/bytes; every triggered conditional gate is satisfied.
- Canonical R11 report verifies `status=pass`, `blockers=[]` with deterministic semantic digest.
- Implementation/evidence PR merges, then exactly one final continuity-only normalization passes same gates and merges.

A subdivision is never COMPLETE from partial CI, a green subset of jobs, an unverified local claim, or a later commit that was not re-gated. Merge uses the exact accepted head SHA.

## Validation and evidence

- Rejected candidate history if any.
- accepted implementation/final-evidence SHA.
- all workflow run IDs.
- manual evidence SHA-256/bytes.
- prior integrated evidence digests.
- canonical R11 semantic digest.
- normalization PR/head/merge.

## Rollback / recovery

If any integrated verification fails, do not regenerate history to fit the report. Fix the current R11.14 branch or reject the candidate. If post-merge normalization fails, keep R11 merged-but-not-normalized and do not authorize R12 until a corrected continuity-only normalization passes.

## Risks and regression traps

- Circular self-attestation.
- Evidence substitution.
- Accepting stale local runtime/model evidence.
- Hardening tests weakening earlier guarantees.
- Accidentally starting R12 before normalization.
- Resource-exhaustion tests escaping budgets.

## Manual intervention

**CONDITIONAL.** Normally no additional manual run beyond already accepted R11.5/R11.9 evidence. Trigger only if final hardening exposes a runtime-specific approved seam not covered by hosted CI/preserved evidence. If triggered, stop finalization, freeze one exact collector and review its structured evidence before proceeding.

For REQUIRED/triggered CONDITIONAL gates, the exact candidate SHA, prerequisites, copy-paste command/UI actions, expected output, failure recovery, evidence-to-return and privacy/redaction instructions MUST be frozen in the subdivision acceptance work before the manual run. Manual PASS is never inferred from silence.

## Completion record

When accepted, append the immutable implementation head, authoritative CI run IDs/conclusions, required/triggered local evidence identity, PR/merge SHA, post-merge normalization PR/merge when used, and final subdivision status `COMPLETE`. Do not rewrite earlier immutable evidence to make later history look cleaner.


---

## Phase-wide acceptance discipline

Every R11 subdivision uses the following invariant sequence unless its frozen manual state explicitly adds a gate:

1. branch from the exact normalized `main` produced by the preceding accepted normalization;
2. implement only that subdivision's frozen scope;
3. run focused tests + full Python Core + R0 Repository Guard + KodeStudio UI Smoke on one exact candidate head;
4. ensure prior integrated acceptance reports remain PASS and no evidence bytes were silently rewritten;
5. satisfy REQUIRED/triggered CONDITIONAL local evidence before final docs claim acceptance;
6. update subdivision acceptance/design evidence without rewriting earlier immutable evidence;
7. run exact-head gates again after final documentation/evidence changes when required;
8. merge the implementation PR with `expected_head_sha`;
9. perform exactly one continuity-only post-merge normalization when required, validate it with the same three gates, merge it, then authorize the next subdivision;
10. never create recursive continuity commits solely to record a normalization's own run IDs; those IDs belong in PR/merge metadata.

## Phase completion rule

R11 becomes **COMPLETE + NORMALIZED** only when R11.1–R11.14 are all COMPLETE with REQUIRED/triggered CONDITIONAL manual evidence satisfied, the canonical R11 integrated report verifies `status=pass` with no blockers, the implementation/final-evidence PR is merged, and the single final continuity-only normalization passes exact-head R0 + Python Core + KodeStudio UI Smoke and merges.

Only that final normalization merge authorizes R12 planning. R12 implementation MUST NOT begin directly from an unnormalized R11 merge.

## Ongoing maintenance rule

Update `R11_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md` in the same work cycle whenever subdivision scope/status, manual prerequisites, compatibility baseline, acceptance requirements, important recovered defects or phase ordering changes. Architecture changes require an ADR.
