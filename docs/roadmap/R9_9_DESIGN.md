# R9.9 Design — Production 2D/UI/texture/concept workflow packs

Status: IMPLEMENTED CANDIDATE / ACCEPTANCE PENDING.

Authority: `docs/roadmap/R9_PLAN.md` R9.9. Architecture v1.0 remains frozen.

## Goal

R9.9 provides the four frozen production-media workflow families through deterministic Kodepoia-owned R9.4 definitions rather than arbitrary ComfyUI graphs:

- concept/key art;
- UI/icon/illustration;
- texture/material source;
- 2D sprite/asset.

The implementation lives in `src/kodepoia/comfyui/packs.py` and composes the already accepted R9.3 capability snapshot, R9.4 `WorkflowDefinition` / `WorkflowValidator` / `GovernedModelResolver`, R9.5 required-output-node semantics, R9.6 generated-output capture/lineage and R9.8 VRAM estimates. It creates no second workflow executor, asset store, model resolver or GPU scheduler.

## Core-only v1 graph variant

Each mandatory family has one explicit `core-checkpoint-*-v1` variant using only these ComfyUI core node classes:

1. `CheckpointLoaderSimple`;
2. `CLIPTextEncode` positive;
3. `CLIPTextEncode` negative;
4. `EmptyLatentImage`;
5. `KSampler`;
6. `VAEDecode`;
7. `SaveImage`.

The graph follows the upstream core text-to-image pattern: checkpoint -> text conditioning + latent -> sampling -> VAE decode -> save. R9.9 does not import an upstream UI workflow JSON verbatim and does not trust embedded metadata as instructions.

No custom-node class is in the allowlist. No model token is embedded as an accepted default. The single `checkpoints` requirement is resolved exclusively through the accepted R9.4 inventory resolver; an ambiguous inventory requires an explicit user/service selection. A missing or non-discovered selection remains BLOCKED.

## Typed parameters and resource bounds

Every family exposes exactly these typed R9.4 parameters:

- `prompt`: bounded non-empty string at the pack-policy layer;
- `negative_prompt`: bounded string;
- `width`, `height`: integer and family-bounded;
- `output_count`: integer 1..4;
- `seed`: explicit non-negative R9 seed;
- `steps`: integer 1..80;
- `cfg`: number 1.0..20.0.

Sampler and scheduler are frozen to `euler` / `normal` in v1 rather than widening the user surface to arbitrary sampler metadata. Denoise is fixed to `1.0` for this text-to-image variant.

Pack-level policy also enforces `width * height * output_count` so independently legal scalar dimensions cannot compose into an unbounded batch. Concept/material-source packs cap the aggregate at 9,437,184 pixels and carry an 8192 MiB estimate; UI/sprite packs cap at 4,194,304 pixels and carry a 6144 MiB estimate. R9.8 remains the actual admission authority at execution time; these estimates do not manufacture free-VRAM proof.

## Output and R8 lineage contract

`SaveImage` node `7` is the explicit required production output node for every pack. R9.10 orchestration must pass that node set into the accepted R9.5 execution preparation path. Retrieved output references remain subject to R9.6 byte/type/path validation and R8-derived-asset lineage; a ComfyUI filename is never asset identity.

The material family is explicitly `material_source_only=true`. Its output is a visual source suitable for later Godot/Blender processing; R9.9 does not claim generated color imagery is a validated normal/roughness/metallic/AO/PBR map set.

## Compatibility reports

`ProductionWorkflowPackCatalog.compatibility()` accepts only an R9.3 capability snapshot. It preserves `STALE` and non-current states, runs the unchanged R9.4 workflow validator, then runs the unchanged R9.4 model resolver with only explicit selections. The report binds:

- family + variant;
- pack identity digest;
- workflow definition ID;
- capability identity;
- validation digest;
- model-resolution digest;
- exact selected model tokens;
- explicit `compatible`, `blocked`, `stale` or `unavailable` state;
- deterministic report digest.

No compatibility failure downloads a model, installs a custom node, rewrites a graph, guesses a filename or widens a node constraint.

## Conditional local acceptance decision

The frozen R9.9 manual state is CONDITIONAL. It triggers only if a mandatory workflow pack depends on a real node/model family not already covered by accepted R9.8 local evidence.

The v1 mandatory pack definitions deliberately introduce no mandatory custom-node family and no mandatory new model token/family. They are resolver-driven over installed `checkpoints` and are validated deterministically against typed capability fixtures in hosted CI. Therefore the current candidate resolves the conditional as **CONDITIONAL NOT TRIGGERED**, unless implementation/CI review discovers an actual dependency on a new authoritative local model/node family.

If that condition changes, acceptance must stop on the exact candidate head and use only an already-installed user-selected compatible model; no model/custom-node/driver/runtime download or installation is authorized to satisfy R9.9.

## Security and governance invariants

- no arbitrary graph fragment parameter;
- no arbitrary URL/host/path/process/custom Python;
- no model download or recursive filesystem model scan;
- explicit discovered model selection when inventory is ambiguous;
- current capability snapshot required for compatible state;
- deterministic seed and settings retained in the R9.5 manifest;
- R9.6/R8 lineage required for promoted generated assets;
- external-local model rights remain unknown/`NOASSERTION` unless R8 evidence proves otherwise;
- generated material imagery is not mislabeled as validated PBR data.
