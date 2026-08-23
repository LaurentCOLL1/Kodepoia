# Kodepoia — R10 detailed phase plan

**Phase:** R10  
**Roadmap title:** Blender / 3D  
**Status:** PLANNING  
**Phase planning started:** 2026-08-23  
**Architecture:** v1.0 frozen  
**Source of truth at planning branch point:** normalized `main` `ec857163915923e7aae9ce316b20d4ab9ae1ce1f`

## Purpose and authority

R10 implements Kodepoia's governed Blender/3D authoring, validation and export layer without changing the frozen foundations. The frozen roadmap requires `bpy/headless`, geometry, UV/PBR, rigs, animation, retarget, humans/animals, LOD, GLTF and validation of topology/normals/weights/budgets.

This file is the exhaustive execution/recovery plan for R10. The R10.1–R10.12 subdivision structure becomes frozen when this plan is merged. No subdivision may be silently added, removed, merged, split or renumbered. Any scope change must update this plan and `docs/continuity/KODEPOIA_CONTINUITY.md` in the same work cycle; any foundation change requires an ADR.

R10.1 MUST NOT begin before this plan is merged to `main` with R0 Repository Guard, full Python Core and KodeStudio UI Smoke successful on the exact final planning head, followed by the normal continuity-only planning normalization if required by the phase-start rule.

## Phase objective

Deliver a deterministic, auditable, local-first 3D pipeline that lets Kodepoia inspect a supported Blender installation, execute only structured Blender jobs through the existing protected external-process boundary, author and transform governed meshes, materials, rigs and animations, validate production budgets, generate controlled LOD variants, export GLB/glTF 2.0, and verify that exported assets preserve the expected geometry/material/skin/animation semantics before promotion through R8 Vault/AssetPipeline lineage.

R10 must enable later phases and existing engine integrations without making Blender a generic code-execution surface:

- R5 KodeGodot can consume validated GLB/glTF assets and continue to own Godot-specific scene/import semantics;
- R8 remains authoritative for source/derived asset identity, provenance, transforms, cache/rebuild and governed export;
- R9 texture/concept outputs may be used only as governed R8 inputs and never become production-ready PBR merely because Blender consumes them;
- R11 can later reuse validated rigs, animation clips, shape keys and facial-ready mesh metadata for voice/lip-sync/cinematics;
- R15 can benchmark 3D quality, topology, rigging and performance from versioned R10 evidence.

Out of scope for R10: Blender installation/update/package management, arbitrary add-on installation, arbitrary Python supplied by a model, arbitrary command lines, online asset libraries, proprietary human generators, cloud rendering, sculpting as an unconstrained interactive agent activity, photogrammetry, CAD, USD production pipeline replacement, audio/lip-sync/cinematics (R11), Godot gameplay logic (R5), model fine-tuning (R15), GPU/driver tuning, and bypassing R6/R7/R8 governance.

## Current external compatibility baseline

Planning research on 2026-08-23 uses official upstream documentation only as compatibility input, never as architecture authority.

### Blender baseline

- Blender **5.2 LTS** is the current stable LTS, released 2026-07-14 and supported until 2028-07.
- R10's authoritative runtime profile is `5.2.x` LTS. Patch updates may be accepted when capability probing and R10 regression gates pass; no silent major/minor upgrade is accepted.
- Blender 4.5 LTS may be detected and reported, but initial R10 acceptance targets 5.2.x unless this plan is explicitly amended.
- Headless automation uses Blender's supported command-line background mode and Python script execution.
- Runner invocations must use a generated, fixed argument template equivalent in intent to `--background`, `--factory-startup`, `--disable-autoexec`, `--offline-mode` where supported, and a non-zero `--python-exit-code`; user startup files and system Python environment inheritance are not trusted inputs.
- Blender 5.2 changed parts of the Python API, including Geometry Nodes modifier properties, therefore capabilities and version are probed and persisted rather than assumed.

### GLB/glTF 2.0 baseline

- GLB is the primary R10 exchange artifact because it is a single binary package containing scene data and referenced images when appropriate.
- glTF 2.0 is the semantic contract. The supported Blender exporter covers meshes, PBR materials, cameras/lights when requested, custom properties/extras, animations, skinning and shape-key animation.
- Export may triangulate quads/ngons and may split vertices at UV/normal discontinuities; R10 budgets therefore distinguish Blender source mesh counts from exported primitive/accessor counts.
- Production material policy targets glTF metal/rough PBR semantics: base color, metallic, roughness, normal, emissive and optional AO, plus explicitly accepted extensions when downstream support is known.

### Godot 4.7 interoperability baseline

- R5 remains authoritative for Godot 4.7 integration.
- Godot 4.x should consume supported 3D scene formats such as GLB/glTF; the old Godot Blender ESCN exporter is not maintained for Godot 4.x and is not an R10 dependency.
- Godot's 3D import pipeline can import UVs, normals, tangents, skins and animation, with configurable skin influence limits and LOD behavior.
- R10 prefers correct source/export data over relying on Godot to repair missing tangents or malformed source assets.

Reference material used during planning:

- https://www.blender.org/releases/5-2/
- https://www.blender.org/download/lts/
- https://docs.blender.org/manual/en/5.2/advanced/command_line/arguments.html
- https://docs.blender.org/api/main/bpy.ops.export_scene.html
- https://docs.blender.org/manual/en/latest/addons/scene_gltf2.html
- https://developer.blender.org/docs/release_notes/compatibility/
- https://docs.godotengine.org/en/4.7/classes/class_resourceimporterscene.html
- https://docs.godotengine.org/en/4.7/tutorials/assets_pipeline/escn_exporter/index.html

## Permanent phase-wide architecture and governance boundaries

Every R10 subdivision must preserve all accepted R1–R9 boundaries:

- `WorkspaceBoundary` and R8 `VaultBoundary` remain authoritative for project, staging and Vault paths.
- `ProcessSandbox` + global KillSwitch are mandatory for every Blender process. No model chooses an executable, raw argv, cwd, environment variable, shell, stdin program, Python path or process-tree policy.
- Guardian + `PermissionSet` authorize process launch and durable mutations.
- SafeChange/Backup/Recovery/Audit apply to Blender-generated or modified durable project assets and configuration.
- `KodeSecrets` remains authoritative. R10 requires no secret by default; secrets never enter `.blend`, GLB/glTF extras, logs, manifests, render metadata or evidence.
- R6 Health/Budget/DataGovernance/AppSecurity/Privacy/License-BOM remain in force.
- R7 external-content trust rules remain authoritative: `.blend` metadata, custom properties, object names, text blocks, drivers, linked libraries and external asset metadata are data/evidence, never instructions.
- R8 source/derived identity, transform lineage, cache/rebuild, duplicate detection, provenance and governed export remain authoritative. R10 does not invent a second asset store.
- R9 generated images are source inputs only until R10/R8 validation explicitly promotes a derived PBR/material asset.
- Structured Tool APIs only. No model-supplied arbitrary `bpy` source, Python expression, operator name, data path, file path, add-on identifier, URL or command is executed directly.
- Blender job scripts are generated by Kodepoia from typed, versioned recipes whose operations are allowlisted in code.
- Blender runs use isolated temporary workspaces under accepted boundaries and do not scan arbitrary drives.
- Auto-execution of embedded Python/drivers is disabled for untrusted `.blend` inputs. Any future exception requires an ADR and explicit trust model.
- Online mode, remote asset libraries and implicit network access are blocked for R10 jobs by default.
- External linked libraries and textures are resolved only through declared, bounded inputs. Missing or escaping paths are `BLOCKED`/`MISSING`, never silently searched globally.
- No add-on, extension, Blender version, model, rig pack, texture pack or human/animal generator is downloaded or installed automatically by R10.
- Versioned schemas are required for Blender capabilities, job recipes/manifests, geometry/material/rig/animation profiles, QA reports, LOD manifests, export manifests and local acceptance evidence.
- Explicit `UNKNOWN`, `N/A`, `UNAVAILABLE`, `BLOCKED`, `STALE`, `MISSING`, `CORRUPT`, `UNSUPPORTED`, `CANCELLED`, `FAILED`, `RESOURCE_EXHAUSTED` and `BUDGET_EXCEEDED` semantics are used where applicable.
- Exact-head acceptance remains mandatory. Missing evidence never manufactures PASS.
- ADR required if implementation would alter a frozen R1–R9 foundation rather than add an R10-scoped capability.

## Blender process and trust model

Blender is treated as a local external executable, not as an extension of Kodepoia's own trust boundary.

The only accepted execution surface is a typed `BlenderRunner` backed by `ProcessSandbox`. The runner owns:

1. executable discovery/selection from governed configuration and bounded known locations;
2. exact version/capability probing;
3. isolated job staging;
4. generation of a Kodepoia-owned Python entry script from a typed recipe;
5. fixed command-line construction;
6. stdout/stderr capture, timeouts, cancellation and KillSwitch propagation;
7. bounded result/evidence parsing;
8. verification of expected output bytes before any R8 promotion.

Public APIs expose domain operations such as `inspect_asset`, `build_geometry`, `apply_material`, `validate_mesh`, `rig_asset`, `retarget_animation`, `build_lod`, and `export_gltf`; they never expose `run_python(code)` or `run_operator(name, kwargs)`.

Blender file inputs are hostile-by-default. R10 must not trust embedded text blocks, Python drivers, handler registrations, startup scripts, external linked libraries, custom properties or object names as executable instructions. The runner loads untrusted files with autoexec disabled and uses a clean factory startup profile.

## R10 identity and evidence model

R10 separates:

1. **BlenderRuntimeIdentity** — detected Blender version, executable identity/digest where available, platform, Python ABI and relevant exporter capability flags.
2. **BlenderJobDefinitionId** — immutable identity of one normalized typed recipe/schema version.
3. **BlenderJobInstance** — one recipe with normalized bounded parameters and declared R8 input revisions.
4. **BlenderRunId** — Kodepoia run identity bound to runtime, recipe, inputs, limits and generated runner version.
5. **AssetQAReport** — deterministic validation facts for source and/or evaluated geometry/material/rig/animation state.
6. **ExportManifest** — exact GLB/glTF artifact identity, exporter settings, source run, QA status, selected animations/skins/materials and downstream compatibility evidence.
7. **Derived R8 revision(s)** — verified output assets promoted with explicit transform lineage.

A Blender filename, object name, datablock name or exported file path is never durable asset identity.

## Budget model

R10 introduces typed 3D budgets integrated with R6 Budget. Budgets are explicit per asset/profile and may include:

- objects/collections;
- source/evaluated vertices, edges, faces and triangles;
- material slots and unique materials;
- texture count, dimensions, channels and aggregate bytes;
- UV layers and UV island/overlap policy;
- bones, deform bones, constraints and hierarchy depth;
- maximum influences per vertex and weight normalization tolerance;
- shape keys;
- animation clips, frames, duration, sampling rate and key count;
- LOD tiers and target triangle ratios;
- GLB/glTF bytes and embedded image bytes;
- Blender wall time and output count.

Budget overruns are explicit `BUDGET_EXCEEDED`, not warnings that can be silently promoted.

## Global prerequisites

Before R10.1 implementation begins:

- R1–R9 are COMPLETE on normalized `main`;
- final R9 normalization PR #128 is merged and `main` is `ec857163915923e7aae9ce316b20d4ab9ae1ce1f` at the planning branch point;
- R7, R8 and R9 integrated acceptance reports remain PASS with unchanged canonical digests;
- Python baseline remains 3.12.x unless a separately accepted compatibility change is made;
- R1 `ProcessSandbox`, KillSwitch, Guardian, SafeChange, Backup/Recovery and Audit remain available;
- R5 Godot 4.7 runner/import validation contracts remain available for downstream interoperability checks;
- R6 Health/Budget/CI/Privacy/AppSecurity/License-BOM remain accepted;
- R8 Vault/AssetService/transform lineage/governed export remain accepted;
- R9 texture/concept outputs remain governed R8 assets;
- no mandatory cloud service, account or API key is introduced;
- hosted CI may use deterministic pure-Python fixtures and fake Blender process fixtures until the subdivision explicitly requiring real Blender evidence;
- no Blender/add-on/asset download is performed merely to make CI pass.

## Complete subdivision index

| ID | Title | Status | Manual intervention | Depends on |
| --- | --- | --- | --- | --- |
| R10.1 | Blender contracts, runtime discovery + secure process boundary | PLANNED | NONE | R9 COMPLETE + planning PR merged |
| R10.2 | Headless `bpy` runner, capability probe + real-runtime acceptance | PLANNED | REQUIRED | R10.1 |
| R10.3 | Structured scene/geometry authoring + deterministic transform recipes | PLANNED | NONE | R10.1–R10.2 |
| R10.4 | UV + PBR material pipeline + governed texture lineage | PLANNED | CONDITIONAL | R10.2–R10.3 + R8/R9 |
| R10.5 | Mesh QA: topology, normals, tangents, UV and production budgets | PLANNED | NONE | R10.3–R10.4 |
| R10.6 | Armatures, skinning + weight validation | PLANNED | CONDITIONAL | R10.3–R10.5 |
| R10.7 | Animation actions/NLA + governed retargeting | PLANNED | CONDITIONAL | R10.6 |
| R10.8 | Human + animal profile pipelines | PLANNED | CONDITIONAL | R10.3–R10.7 + R8 governance |
| R10.9 | LOD generation, preservation checks + variant lineage | PLANNED | NONE | R10.5–R10.8 |
| R10.10 | GLB/glTF export + Blender round-trip + Godot 4.7 acceptance | PLANNED | REQUIRED | R10.4–R10.9 + R5/R8 |
| R10.11 | CLI + KodeStudio Blender/3D UX | PLANNED | NONE | R10.1–R10.10 |
| R10.12 | Adversarial hardening + R10 integrated acceptance | PLANNED | CONDITIONAL | R10.1–R10.11 |

---

# R10.1 — Blender contracts, runtime discovery + secure process boundary

## Objective and rationale

Create the typed Blender domain and executable boundary before any real Blender Python is run. Freeze runtime identity, supported-version policy, job/result states, path rules, recipe identity and process invocation constraints so later work cannot turn Blender into a generic local shell/Python escape surface.

## In scope

- `BlenderRuntimeIdentity`, capability/state enums, typed executable selection and path validation;
- bounded discovery from explicit configuration plus documented platform-specific candidate locations only;
- no recursive disk search;
- supported runtime policy targeting Blender 5.2.x LTS;
- job/result/run-manifest contracts and canonical digest helpers;
- typed recipe root schema and operation allowlist identifiers;
- fixed process policy contract: background, factory startup, autoexec disabled, offline mode where supported, Python exit code, bounded cwd/environment;
- stdout/stderr/result size limits, wall-time limits and KillSwitch/cancellation semantics;
- R10 package namespace, expected `src/kodepoia/blender3d/`;
- schema roots for capabilities, jobs, QA, export and local evidence.

## Out of scope

No real Blender launch, no `bpy`, geometry mutation, material creation, rigging, animation, LOD or export.

## Dependencies and prerequisites

R9 COMPLETE + normalized main, merged R10 plan, existing R1 process/governance foundations.

## Detailed implementation plan

Implement immutable dataclasses/enums and canonical serialization. Executable candidates must resolve to regular files, remain within configured/known candidate roots, and be selected by explicit policy rather than user/model free text. Record enough runtime file identity for diagnostics without making filesystem metadata alone a trust guarantee.

Define job states such as `PLANNED`, `STAGED`, `RUNNING`, `SUCCEEDED`, `FAILED`, `CANCELLED`, `BLOCKED`, `UNSUPPORTED`, `TIMED_OUT`. Define transitions and fail closed on impossible transitions or malformed persisted state.

Build a fixed argv constructor whose flags are owned by Kodepoia. The model may choose only high-level typed operations and bounded parameters. Environment starts from the ProcessSandbox policy and never inherits `PYTHONPATH`/user site injection merely because Blender supports it.

## Deliverables

- `src/kodepoia/blender3d/contracts.py`, `boundary.py`, `serialization.py`, package exports;
- R10 schema roots under `schemas/`;
- discovery/path/state/argv/schema/tamper tests;
- deterministic fake-executable fixtures;
- `docs/roadmap/R10_1_DESIGN.md` and `R10_1_ACCEPTANCE.md`.

## Acceptance gates / Definition of Done

R0 + full Python Core + UI Smoke SUCCESS on exact head; schema round-trip; canonical digests; malicious executable/path/argv/environment cases blocked; no shell invocation; no external process launched by production R10.1 code; prior integrated acceptance remains PASS.

## Validation and evidence

Accepted head SHA, CI run IDs, test counts, schema IDs, representative runtime/job digest, negative-case matrix.

## Rollback / recovery

Remove R10 package contracts/schemas/exports. No durable Blender-produced state exists yet.

## Risks and regression traps

Executable path confusion, PATH hijacking, symlink escape, shell quoting differences, env inheritance, mutable fields entering identity, accepting unsupported Blender versions, collapsing `UNAVAILABLE` into success.

## Manual intervention

**NONE**.

---

# R10.2 — Headless `bpy` runner, capability probe + real-runtime acceptance

## Objective and rationale

Implement the real Blender 5.2 LTS headless execution boundary and prove it against an actual local Blender runtime before higher-level 3D authoring depends on unverified API assumptions.

## In scope

- `BlenderRunner` backed only by `ProcessSandbox`;
- Kodepoia-generated bootstrap Python entrypoint;
- capability probe returning Blender/Python versions, background state, glTF exporter availability, relevant `bpy`/`bmesh` capabilities and supported feature flags;
- isolated staging/output directories under accepted boundaries;
- machine-readable result envelope written atomically by the generated script;
- stdout/stderr/log capture with redaction and size limits;
- timeout, cancellation and global KillSwitch propagation;
- deterministic fake-runner coverage in hosted CI;
- local real-Blender acceptance command and evidence schema.

## Out of scope

Production mesh/material/rig/animation editing beyond a tiny canonical probe scene.

## Dependencies and prerequisites

R10.1 COMPLETE. Authoritative manual acceptance requires Blender 5.2.x LTS accessible locally; R10 does not install it.

## Detailed implementation plan

Generate one static bootstrap script from Kodepoia code plus a JSON job document. The bootstrap imports only Kodepoia-defined operation modules bundled/staged by the runner; it does not `exec` recipe strings.

Launch with a fixed clean profile. The probe verifies actual `bpy.app.version`, background mode, exporter registration and essential modules. It creates a tiny deterministic scene, saves a temporary `.blend`, exports a tiny GLB, reports hashes/sizes/counts and exits through the configured Python exit code path. Output bytes are treated as evidence only after path confinement and hash verification.

Persist local evidence with runtime identity, OS, executable digest if obtainable, command policy version, probe facts, output SHA-256 and OOM/crash/timeout flags. No username, home path or unrelated environment values belong in canonical evidence.

## Deliverables

- runner/process adapter and generated bootstrap module;
- capability-probe operation;
- `blender-capability-v1` and `r10-local-blender-evidence-v1` schemas;
- fake process fixtures and hostile output tests;
- local acceptance CLI entrypoint;
- `R10_2_DESIGN.md` and `R10_2_ACCEPTANCE.md`.

## Acceptance gates / Definition of Done

Hosted exact-head R0 + Python Core + UI Smoke SUCCESS; fake-runner tests cover success/crash/timeout/cancel/malformed-result/path escape; real local Blender 5.2.x probe evidence is REQUIRED and must be reviewed against the exact implementation head before merge/normalization.

## Validation and evidence

CI IDs + exact head; reviewed local JSON; Blender version and background=true; exporter available; canonical tiny `.blend` and GLB SHA-256/size facts; no out-of-bound writes; no unexpected network; exit code success.

## Rollback / recovery

Delete staged temporary runs and R10 runner state; no accepted Vault promotion occurs in R10.2. Revert runner package if validation fails.

## Risks and regression traps

Blender binary mismatch, startup-file contamination, Python autoexec, driver execution, unexpected online asset access, result-file spoofing, Windows process-tree termination, hanging shutdown.

## Manual intervention

**REQUIRED**.

1. **Reason:** authoritative `bpy`/exporter/background-process behavior must be proven against a real Blender 5.2.x runtime; hosted deterministic stubs cannot certify the user's actual executable.
2. **Prerequisites:** exact accepted R10.2 candidate SHA checked out locally, Python environment prepared, Blender 5.2.x LTS installed or available as a legitimate local portable build, no unrelated Blender job running from the same acceptance workspace.
3. **Exact actions/commands:** the subdivision must provide one copy-paste local acceptance command through `python -m kodepoia.cli` that accepts an explicit Blender executable/configured runtime ID and writes one canonical JSON evidence file; the command must not install Blender.
4. **Expected output:** exit code 0; evidence schema valid; Blender version 5.2.x; background mode true; glTF exporter available; tiny deterministic GLB produced; `status=pass`; `blockers=[]`.
5. **Failure recovery:** stop on non-zero exit, preserve logs/evidence, do not retry with relaxed sandbox flags, clean only the documented R10 temporary workspace, and report the failure.
6. **Evidence to send back:** canonical JSON evidence plus console summary containing no secrets; SHA-256 and byte size must be preserved.
7. **Do not do yet:** do not download add-ons/assets, enable autoexec, enable online mode, edit Blender preferences for acceptance, or continue to R10.3 before evidence review.
8. **Privacy/security note:** redact usernames/home paths if diagnostic logs expose them; never provide passwords, tokens, private keys or unrelated files.

---

# R10.3 — Structured scene/geometry authoring + deterministic transform recipes

## Objective and rationale

Provide bounded geometry authoring and scene-editing capabilities through typed recipes instead of arbitrary `bpy` source.

## In scope

- scene reset/collection/object creation using allowlisted primitive and mesh-data operations;
- import of declared R8 source meshes where supported;
- transforms with explicit units/orientation and apply-policy;
- deterministic edit operations such as join/separate, triangulate, limited modifiers, normal recalculation request, origin/pivot and naming policy;
- explicit modifier allowlist with bounded parameters;
- deterministic object/datablock IDs independent of display names;
- source/evaluated mesh statistics;
- transaction-like staging: source inputs immutable, outputs new derived candidates.

## Out of scope

UV/PBR authoring, rigs, animation, human/animal semantics, LOD and final export.

## Dependencies and prerequisites

R10.2 COMPLETE + reviewed real-runtime evidence.

## Detailed implementation plan

Define a versioned geometry recipe composed of explicit operation records. Each record resolves only declared object IDs. Unsupported operator/parameter combinations are rejected before Blender launch.

Favor direct Blender data API/BMesh operations where deterministic and context-safe; context-sensitive operators must be wrapped in Kodepoia-owned code with explicit selection/mode setup and cleanup.

Record pre/post topology statistics and modifier stack identity. Never overwrite the user's original `.blend` or source asset; write a new staged `.blend` and promote only through R8 after acceptance.

## Deliverables

Geometry recipe schemas, operation catalog, geometry executor, deterministic fixture scenes, tests for context/mode cleanup and object identity, docs.

## Acceptance gates / Definition of Done

Exact-head R0/Python/UI; real-runner integration tests may reuse R10.2 accepted runtime when available but hosted CI remains deterministic; geometry stats match expected fixtures; unsupported operations and object references BLOCK; repeated canonical recipe produces semantically identical stats and stable manifest identity.

## Validation and evidence

Head/CI IDs, recipe digest, input/output hashes, object/triangle counts and operation manifest.

## Rollback / recovery

Discard staged derived outputs and revert recipe/executor code. Original R8 revisions remain immutable.

## Risks and regression traps

Context leakage between operations, unapplied scale changing export semantics, modifier nondeterminism, hidden objects leaking into outputs, name collisions, source mutation.

## Manual intervention

**NONE**.

---

# R10.4 — UV + PBR material pipeline + governed texture lineage

## Objective and rationale

Create a controlled UV/material pipeline that turns declared source textures and mesh inputs into validated Blender/glTF-compatible metal/rough PBR candidates while retaining R8/R9 provenance.

## In scope

- UV layer inspection, creation and bounded unwrap/pack recipes;
- texel-density and UV-area statistics where feasible;
- Principled-BSDF-based material templates compatible with the accepted glTF exporter subset;
- governed texture roles: base color, metallic, roughness, normal, emissive and optional AO;
- color-space declarations and normal-map handling;
- bounded image dimensions/count/bytes;
- optional deterministic bake operations for explicitly supported channels;
- R8 lineage binding from source texture revisions, including R9 `material_source` outputs;
- explicit `source_only` semantics preserved until R10 validates a production material.

## Out of scope

Arbitrary shader graphs, arbitrary Geometry Nodes, custom OSL, online texture acquisition, automatic material-model downloads.

## Dependencies and prerequisites

R10.2–R10.3 COMPLETE; R8 lineage available; R9 material-source semantics retained.

## Detailed implementation plan

Expose material recipes, not raw node graphs. Each template creates a known Principled BSDF graph and maps declared texture roles through fixed node patterns. Reject undeclared file paths and unsupported image types.

UV operations use bounded parameters and report overlap/coverage indicators. Baking is conditional on runtime capability and resource budgets; CI uses small deterministic fixtures. Hardware/GPU acceleration is not required for correctness and must not silently change result authority.

## Deliverables

UV/material schemas, template executor, texture-role validator, lineage bridge, small fixtures and docs.

## Acceptance gates / Definition of Done

Exact-head R0/Python/UI; schema and lineage tests; material graph inspection tests; glTF-exportable template smoke; texture path escape and unsupported graph injection blocked; source-only R9 texture cannot be mislabeled production-ready without R10 validation.

## Validation and evidence

UV stats, material/texture role manifest, source revision digests, bake settings/output digests if used.

## Rollback / recovery

Discard staged material/UV derivatives; preserve original mesh/textures and lineage.

## Risks and regression traps

Wrong color spaces, inverted normal convention, packed-channel confusion, generated UV nondeterminism, texture escape paths, silently unsupported Blender procedural nodes.

## Manual intervention

**CONDITIONAL** — only if a planned bake path cannot be authoritatively validated on hosted/accepted CPU fixtures or exposes backend-specific behavior. If triggered, stop before R10.5 and provide exact local command/evidence requirements; do not ask the user to change GPU drivers or Blender global preferences.

---

# R10.5 — Mesh QA: topology, normals, tangents, UV and production budgets

## Objective and rationale

Make 3D correctness measurable before rigging/export. A mesh must not become production-ready based on visual appearance alone.

## In scope

- source and evaluated mesh inspection;
- degenerate/zero-area geometry, loose vertices/edges, non-finite coordinates, duplicate/coincident indicators, non-manifold/boundary policy by asset profile;
- face winding and normal consistency checks;
- tangent availability/validity when normal-mapped materials require it;
- UV layer count, missing UVs, zero-area UVs, overlap policy/coverage statistics where supported;
- transform/scale sanity;
- triangle/material/texture/shape-key/object budgets;
- deterministic severity taxonomy `PASS/WARN/BLOCK` with explicit reasons;
- machine-readable QA report and digest.

## Out of scope

Subjective artistic beauty scoring, automatic destructive repair of every defect, rig weights, animation and LOD.

## Dependencies and prerequisites

R10.3–R10.4 COMPLETE.

## Detailed implementation plan

Implement profile-aware validators with explicit tolerances. Character meshes may legitimately have seams/boundaries that a closed static prop would not. Every rule records applicability and measurement method.

Repairs, where offered, are separate explicit recipes and produce new derived outputs followed by re-validation. A validator never silently edits source geometry.

## Deliverables

QA schema/engine, budget profiles, repair recipe subset, fixtures for each failure class, docs.

## Acceptance gates / Definition of Done

Exact-head R0/Python/UI; adversarial malformed mesh fixtures; deterministic reports; budget overflow blocks promotion; required-normal-map tangents validated; no destructive implicit fix.

## Validation and evidence

QA report digest, counts, tolerances, rule applicability and final blockers.

## Rollback / recovery

QA itself is read-only; discard repair derivatives if they fail re-validation.

## Risks and regression traps

Treating all boundaries as errors, expensive O(n²) checks on large meshes, float tolerance drift, source/evaluated count confusion, warnings accidentally treated as pass for mandatory rules.

## Manual intervention

**NONE**.

---

# R10.6 — Armatures, skinning + weight validation

## Objective and rationale

Add governed rigging/skinning contracts with objective hierarchy and weight validation suitable for real-time export.

## In scope

- armature/rig profile schema;
- bone hierarchy, rest pose, deform/control distinction and stable semantic bone IDs;
- bind/parent operations through typed recipes;
- automatic/explicit weight assignment only through allowlisted strategies;
- weight normalization, zero-weight vertex detection, invalid bone references, influence-count budgets and tiny-weight pruning;
- configurable target influence profile, with a default Godot-compatible four-influence acceptance profile and explicit opt-in profile for higher supported counts;
- pose/deformation smoke fixtures;
- R8 lineage for rigged derivatives.

## Out of scope

Proprietary auto-rig services, arbitrary Rigify/add-on dependency, facial lip-sync (R11), animation retargeting (R10.7).

## Dependencies and prerequisites

R10.3–R10.5 COMPLETE.

## Detailed implementation plan

Represent rig semantics independently of Blender display bone names. Recipes create/attach an armature from validated profile data or validate an imported governed rig. Control-only bones can exist but exporter-facing deform bones are explicit.

Weight validator computes per-vertex sum, influence count, missing groups, non-finite/negative weights and orphan bone groups. Repairs are explicit and revalidated.

## Deliverables

Rig/skin schemas, executor, validators, humanoid/quadruped minimal test rigs, deformation tests, docs.

## Acceptance gates / Definition of Done

Exact-head R0/Python/UI; malformed hierarchy and weight cases BLOCK; deterministic rig profile identity; exported-deform-bone set explicit; influence/tolerance budgets tested.

## Validation and evidence

Rig profile digest, bone counts, deform set, weight statistics, blocker list and deformation fixture facts.

## Rollback / recovery

Rigging produces new derivatives; source mesh remains immutable. Revert rigged outputs and code if validation fails.

## Risks and regression traps

Bone-name coupling, non-uniform scale, unapplied transforms, weight normalization changing silhouettes, hidden control bones exported, exceeding downstream influence support.

## Manual intervention

**CONDITIONAL** — triggered only if a runtime-specific Blender 5.2 skinning behavior differs from deterministic fixtures or cannot be reproduced in accepted CI/runtime evidence. If triggered, stop before R10.7 and request a bounded local acceptance run, never manual weight painting as acceptance evidence.

---

# R10.7 — Animation actions/NLA + governed retargeting

## Objective and rationale

Provide deterministic animation clip management and retargeting between explicitly mapped compatible rigs without guessing semantic correspondences.

## In scope

- animation clip/action manifest schema;
- frame rate, frame range, duration, loop and root-motion policy;
- action/NLA organization for export;
- baking/sampling policy for constraints and interpolation compatibility;
- source/target rig semantic maps, rest-pose compatibility checks and explicit bone correspondence;
- translation/rotation/scale transfer rules with axis/unit normalization;
- retarget quality facts such as mapped/unmapped deform bones and root drift;
- clip budget/key-count validation;
- independent animation-library export readiness.

## Out of scope

Motion capture acquisition, AI motion generation, facial visemes/lip-sync, subjective animation polish.

## Dependencies and prerequisites

R10.6 COMPLETE.

## Detailed implementation plan

Retargeting requires a versioned `RigSemanticProfile` on both sides. Unknown or ambiguous bones remain unmapped and can block when required. No fuzzy model-generated bone-name matching is executed as authority; suggestions may be presented as data but require deterministic resolution before execution.

Bake exporter-facing animation onto deform bones/shape keys as required. Preserve clip identity independent of Blender action display names.

## Deliverables

Animation/retarget schemas, executor, profile mapper, canonical humanoid and quadruped retarget fixtures, docs.

## Acceptance gates / Definition of Done

Exact-head R0/Python/UI; loop/frame boundaries deterministic; ambiguous mapping blocked; fixture retarget preserves required bones within numeric tolerances; no arbitrary driver/script execution.

## Validation and evidence

Clip manifest digests, mapping coverage, sample/key counts, root-motion stats and blocker list.

## Rollback / recovery

Retarget creates new animation derivatives; source clips/rigs remain unchanged.

## Risks and regression traps

Rest-pose mismatch, axis conversion, root motion duplication, action/NLA exporter rules, constraint baking drift, quaternion discontinuities.

## Manual intervention

**CONDITIONAL** — only if real Blender 5.2 animation/export semantics diverge from accepted fixtures in a way that cannot be certified automatically. If triggered, stop before R10.8 and provide a bounded local command plus machine-readable evidence; video-only subjective evidence is insufficient.

---

# R10.8 — Human + animal profile pipelines

## Objective and rationale

Satisfy the frozen human/animal scope through governed reusable profile pipelines rather than proprietary generators or unbounded procedural code.

## In scope

- profile families for at least `humanoid_biped` and `quadruped`;
- expected orientation, scale/unit, semantic rig zones, mesh parts, material slots and required QA rules;
- governed assembly/validation of user/project/Vault source assets;
- optional deterministic low-complexity canonical fixtures created entirely by R10 code for CI;
- morph/shape-key inventory validation and safe rename/identity mapping;
- compatibility with R10 rig/animation/LOD/export contracts;
- provenance/license status retained from R8.

## Out of scope

Photorealistic body generation from nothing, age/identity inference, proprietary add-ons, automatic online character downloads, anatomical correctness claims, R11 facial/audio systems.

## Dependencies and prerequisites

R10.3–R10.7 COMPLETE + R8 provenance.

## Detailed implementation plan

A profile describes what a governed asset must expose, not how an LLM can execute arbitrary Blender edits. Production source meshes come from declared R8 revisions. R10 may normalize orientation, materials, rig binding and metadata only through existing typed recipes.

Canonical CI fixtures are intentionally synthetic and simple; they prove contract behavior, not artistic quality.

## Deliverables

Human/animal profile schemas, validators, canonical fixtures, assembly recipes, docs.

## Acceptance gates / Definition of Done

Exact-head R0/Python/UI; at least one humanoid and one quadruped fixture pass end-to-end profile/rig/animation validation; missing required semantic bones/materials/weights block; provenance survives transformations.

## Validation and evidence

Profile digest, source lineage, required/optional feature matrix, rig/material/shape-key stats.

## Rollback / recovery

Discard derivatives; source human/animal assets remain immutable.

## Risks and regression traps

Overfitting to one rig naming convention, claiming photorealism from contract tests, license/provenance loss, morph explosion, hidden geometry and material slot bloat.

## Manual intervention

**CONDITIONAL** — not required for canonical contract acceptance. Trigger only if a specific production human/animal asset is made mandatory for acceptance by an explicit later plan amendment; no external asset download is implied by the current plan.

---

# R10.9 — LOD generation, preservation checks + variant lineage

## Objective and rationale

Generate controlled lower-detail variants while proving that material, UV, skinning and silhouette-critical semantics remain valid within explicit budgets.

## In scope

- LOD profile schema with tier names/ratios/triangle budgets;
- deterministic decimation recipes for supported mesh classes;
- preservation checks for materials, UV layers, normals, shape-key policy and skin groups;
- separate policy for static versus skinned meshes;
- screen/perceptual proxy metrics where deterministic and bounded;
- R8 variant lineage linking each LOD to the exact source revision and recipe;
- downstream hint metadata without inventing a non-standard glTF LOD extension as universal truth.

## Out of scope

Godot's runtime LOD algorithm itself, HLOD scene orchestration, proprietary simplifiers, destructive overwrite of source mesh.

## Dependencies and prerequisites

R10.5–R10.8 COMPLETE.

## Detailed implementation plan

Each tier is a new derived asset. Validate after decimation with R10.5/R10.6 rules. Skinned meshes use stricter preservation rules; if decimation breaks weights/topology beyond tolerance the tier is `BLOCKED` rather than accepted.

The export layer may package explicit LODs as separate governed outputs or downstream-specific bundles via R5; R10 does not assert a universal standard extension where none is accepted.

## Deliverables

LOD schema/executor, static/skinned fixtures, QA bridge, lineage manifests, docs.

## Acceptance gates / Definition of Done

Exact-head R0/Python/UI; target triangle ranges enforced; every accepted LOD re-passes mandatory QA; lineage deterministic; failed preservation blocks promotion.

## Validation and evidence

Source/tier counts, ratios, QA digests, output hashes and lineage edges.

## Rollback / recovery

Discard LOD derivatives; source asset remains unchanged.

## Risks and regression traps

Decimation harming deformation, UV seams, normals or silhouettes; ratio rounding; treating engine auto-LOD as equivalent to authored tiers.

## Manual intervention

**NONE**.

---

# R10.10 — GLB/glTF export + Blender round-trip + Godot 4.7 acceptance

## Objective and rationale

Produce the canonical real-time exchange artifact and prove its semantics across Blender export/re-import and the accepted Godot 4.7 toolchain.

## In scope

- typed GLB/glTF export profile;
- primary GLB output plus optional separate glTF mode when explicitly requested;
- axis/unit/orientation policy;
- selection/collection scope;
- normals/tangents/UV/materials/skins/morphs/animation export settings;
- influence-count policy and deform-bone policy;
- bounded use of supported glTF extensions only when downstream support is declared;
- GLB container and glTF JSON structural validation;
- Blender re-import round-trip facts;
- Godot 4.7 headless import/parse validation through existing R5 boundaries;
- export manifest + R8 promotion/lineage.

## Out of scope

FBX as the canonical interchange path, ESCN exporter, arbitrary third-party glTF extensions, Godot gameplay scene generation.

## Dependencies and prerequisites

R10.4–R10.9 COMPLETE; R5 Godot acceptance tooling; R8 promotion; Blender 5.2 runtime from R10.2.

## Detailed implementation plan

Export only already-passing source/QA profiles. Record exact exporter arguments and capability/version. Validate GLB header/chunk bounds and parse glTF JSON with strict size limits. Re-import exported artifact in a clean Blender job and compare semantic facts: object/mesh/material counts, required UV sets, skin/bone coverage, animation names/durations and shape-key inventory where applicable. Count differences caused by legitimate glTF triangulation/vertex splitting are interpreted through profile-aware rules rather than naive exact vertex equality.

Then pass the GLB through R5's Godot 4.7 headless scene/import validation using a small canonical static asset and a rigged animated asset. Validate import success, absence of fatal errors, expected mesh/skeleton/animation presence and declared material/skin semantics. R10 does not modify Godot import settings globally.

## Deliverables

Exporter profile/schema, GLB/glTF validator, round-trip comparator, R5 bridge, canonical static + rigged fixtures, export manifest schema, local acceptance runner, docs.

## Acceptance gates / Definition of Done

Exact-head R0/Python/UI; deterministic fixture exports; malformed GLB/json blocked; Blender round-trip PASS; Godot 4.7 canonical import PASS; real local Blender+Godot acceptance evidence REQUIRED on the exact implementation head; R8 promotion only after all mandatory blockers clear.

## Validation and evidence

Runtime/export profile, input QA digests, GLB SHA-256/size, glTF asset/generator/version fields, semantic compare report, Godot version/import summary, blockers=[], output Vault revision.

## Rollback / recovery

Do not promote failing exports. Revert derived export revisions/lineage references through R8 SafeChange rules if a post-promotion defect is discovered; source revisions remain intact.

## Risks and regression traps

glTF exporter option drift, Blender vertex splitting, coordinate confusion, missing stashed actions, unsupported shader nodes, skin influence mismatch, Godot importer option drift, assuming `.blend` direct import equals GLB behavior.

## Manual intervention

**REQUIRED**.

1. **Reason:** final R10 interoperability must be certified against real Blender 5.2.x and real Godot 4.7, including process/export/import behavior that deterministic stubs cannot authoritatively prove.
2. **Prerequisites:** exact R10.10 candidate SHA, accepted R10.2 Blender runtime, accepted local Godot 4.7 executable/configuration from R5 or equivalent governed setup, enough free disk for tiny fixtures.
3. **Exact actions/commands:** R10.10 must provide one copy-paste `python -m kodepoia.cli` local acceptance command that runs only bundled canonical static + rigged fixtures and writes canonical JSON evidence. It must not download software/assets or mutate global Blender/Godot preferences.
4. **Expected output:** exit 0; Blender round-trip PASS; Godot import PASS; `status=pass`; `blockers=[]`; canonical GLB/output digests recorded.
5. **Failure recovery:** preserve JSON/logs, stop, do not loosen export/sandbox/import rules, clean only documented temp workspace, report exact failing stage.
6. **Evidence to send back:** canonical JSON evidence and concise console summary with Blender/Godot versions and SHA-256/byte sizes.
7. **Do not do yet:** do not continue to R10.11 until evidence is reviewed; do not install plugins, convert through FBX, or edit source fixtures manually to force success.
8. **Privacy/security note:** redact personal paths/usernames if logs expose them; no secrets are required.

---

# R10.11 — CLI + KodeStudio Blender/3D UX

## Objective and rationale

Expose accepted R10 capabilities through one governed service shared by CLI and KodeStudio without leaking raw Blender/Python/process surfaces.

## In scope

- `BlenderService` as the single façade over accepted R10 contracts;
- bounded CLI commands for status/capabilities, inspect, geometry recipe validation, QA, rig/skin report, animation/retarget report, LOD, export and evidence;
- KodeStudio Blender/3D page using non-blocking worker patterns;
- runtime/capability visibility;
- recipe/job status and cancellation;
- mesh/material/rig/animation/LOD/GLB QA summaries;
- R8 lineage/export references;
- accessibility/localization/pseudo-locale coverage.

## Out of scope

Embedded full Blender UI, arbitrary Python console, arbitrary operator browser, addon installer, file browser outside governed boundaries.

## Dependencies and prerequisites

R10.1–R10.10 COMPLETE.

## Detailed implementation plan

CLI/UI call `BlenderService` only. Commands accept IDs/typed options; no raw `--python`, `--expr`, executable, arbitrary path or argv pass-through exists. Long jobs run through cancellable workers and surface explicit progress/state where available.

## Deliverables

Service façade, CLI parser/handlers, KodeStudio view/view-model, localization/accessibility keys, dedicated smoke tests, docs.

## Acceptance gates / Definition of Done

Exact-head R0/Python/UI; dedicated R10.11 UI smoke; pseudo-locale and accessibility registration; forbidden raw process/Python surface tests; cancellation/state rendering verified.

## Validation and evidence

CI IDs, CLI output fixtures, UI smoke summary, service API inventory.

## Rollback / recovery

Remove UI/CLI surface while preserving lower-level accepted R10 modules and data.

## Risks and regression traps

UI thread blocking, accidental arbitrary path/executable passthrough, stale job status, localization regression, duplicating domain logic in UI.

## Manual intervention

**NONE**.

---

# R10.12 — Adversarial hardening + R10 integrated acceptance

## Objective and rationale

Attack R10's cross-subsystem seams and produce the canonical integrated R10 acceptance report without circular self-attestation.

## In scope

- adversarial tests for executable/path/env/argv injection;
- malicious `.blend` metadata/text/driver/custom-property cases with autoexec disabled;
- recipe/operator/parameter injection attempts;
- output/result manifest spoofing, symlink/path escape and oversized files;
- malformed mesh/UV/material/weight/animation/GLB cases;
- cross-run identity substitution and stale runtime/capability evidence;
- R8 lineage/provenance substitution attempts;
- cancellation/crash/timeout/partial-output recovery;
- budget exhaustion and many-run bounded-state tests;
- R10 integrated acceptance contracts/schema and deterministic verifier;
- final documentation/evidence sequence that binds accepted R10.1–R10.12 evidence plus reviewed required local R10.2/R10.10 evidence.

## Out of scope

New product features, architecture changes, weakening earlier phases, modifying frozen R7/R8/R9 integrated reports.

## Dependencies and prerequisites

R10.1–R10.11 COMPLETE, required local evidence accepted, all prior integrated reports still PASS.

## Detailed implementation plan

Freeze the implementation head before generating canonical integrated documentation. Integrated report creation reads immutable Git blobs/evidence and recomputes digests; it must not claim its own yet-uncommitted digest. Follow the anti-circular sequence established by R9.11: implementation head acceptance first, then generated/bound final report/docs, then exact final gates, merge, and one continuity-only final normalization if the frozen phase-completion rule requires it.

The integrated report must include `status`, `blockers`, `source_sha`, runtime policy, accepted Blender baseline, subdivision evidence bindings, required local evidence digests/byte lengths, and prior-phase integrated report verification status.

## Deliverables

R10 integrated acceptance model/schema/verifier, adversarial seam tests, `R10_12_DESIGN.md`, `R10_12_ACCEPTANCE.md`, canonical `R10_INTEGRATED_ACCEPTANCE.json`, continuity synchronization.

## Acceptance gates / Definition of Done

Exact implementation head: R0 + full Python Core + UI Smoke SUCCESS; adversarial suite PASS; prior integrated reports PASS. Canonical R10 report then generated/bound without circularity. Exact final documentation/evidence head must again pass R0 + full Python Core + UI Smoke. `status=pass`, `blockers=[]`, required local evidence digests bound. Merge + final continuity normalization per frozen rule before R10 becomes COMPLETE + NORMALIZED and R11 planning is authorized.

## Validation and evidence

Immutable implementation SHA, all authoritative run IDs, adversarial test summary, integrated report SHA-256, local evidence digests/byte lengths, final docs head, merge SHA and normalization record.

## Rollback / recovery

If any integrated gate fails, R10 remains IN PROGRESS. Do not alter prior phase reports to make R10 pass. Revert only R10 candidate changes or fix forward on the same subdivision branch with a new exact head.

## Risks and regression traps

Circular report generation, stale evidence, accepting a different Blender runtime than tested, autoexec regression, output spoofing, missing required local evidence, weakening earlier integrated acceptance.

## Manual intervention

**CONDITIONAL** — normally NOT TRIGGERED if R10.2 and R10.10 required local evidence already bind all hardware/runtime-facing semantics unchanged by R10.12. Trigger only if R10.12 changes or newly exercises an authoritative real Blender/Godot behavior not covered by those accepted local gates. If triggered, stop and issue a new bounded local evidence command before final acceptance.

---

## Phase completion rule

R10 can be marked COMPLETE only when all R10.1–R10.12 subdivisions are COMPLETE with required evidence, the canonical R10 integrated acceptance report is `status=pass` with `blockers=[]`, all REQUIRED manual gates are SATISFIED, all triggered CONDITIONAL gates are satisfied, the final exact-head R0/Python/UI gates succeed, and the final continuity normalization required by the frozen phase-completion rule is merged to `main`.

R11 planning is forbidden before that condition is satisfied.

## Ongoing maintenance rule

Update `R10_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md` in the same work cycle whenever subdivision scope/status, manual prerequisites, acceptance requirements, important recovered defects, supported Blender runtime policy, Godot interoperability assumptions or phase ordering changes. Any frozen-foundation change requires an ADR.
