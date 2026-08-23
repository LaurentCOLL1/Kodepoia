# R9.9 Acceptance — Production 2D/UI/texture/concept workflow packs

Status: **IMPLEMENTATION ACCEPTED / FINAL DOCUMENTATION GATES PENDING**.

Authority: `docs/roadmap/R9_PLAN.md` R9.9.

## Accepted implementation

Exact implementation head: `85f8aacf8baf0f8dba6d28ba07fcfc0dbc37a324`.

Hosted gates on that exact head:

- R0 Repository Guard #1188 / run `32644669495`: SUCCESS Ubuntu + Windows;
- Python Core #1162 / run `32644669572`: SUCCESS 5/5; Ubuntu `724 passed / 6 skipped / 46 warnings`; Windows tests SUCCESS; Ubuntu/Windows package builds SUCCESS; integrated KodeStudio Windows smoke SUCCESS; R7/R8 integrated acceptance PASS;
- KodeStudio UI Smoke #1129 / run `32644669558`: SUCCESS.

## Accepted scope

The accepted candidate implements the four frozen mandatory families through `ProductionWorkflowPackCatalog`:

- concept/key art;
- UI/icon/illustration;
- texture/material source;
- 2D sprite/asset.

Every v1 family is a deterministic R9.4 workflow definition using only the core node allowlist `CheckpointLoaderSimple`, `CLIPTextEncode`, `EmptyLatentImage`, `KSampler`, `VAEDecode`, `SaveImage`. No custom node, model download, arbitrary graph execution, process, remote endpoint or R8 bypass is introduced.

The single model requirement is `checkpoints`, resolved only from the unchanged R9.4 discovered inventory. Ambiguous inventory requires an explicit selection; missing/non-discovered selections remain BLOCKED. Every pack carries explicit required output node `7`, resource bounds, deterministic identity and compatibility evidence. Generated output remains subject to R9.5/R9.6 and R8 lineage/governance rather than becoming a second asset authority.

## Frozen workflow identities

| Family | Variant | Definition ID | Definition SHA-256 | Pack identity SHA-256 |
| --- | --- | --- | --- | --- |
| concept | `core-checkpoint-concept-v1` | `wf_8669df755636dec13e925fadab1f8ef6` | `8669df755636dec13e925fadab1f8ef63500ea5e1ea6abf4e2102162a44f3798` | `b43bf09981500288ba8a7ba929c01925b514abee0e3551a1b0c9bec96239c8f1` |
| UI/illustration | `core-checkpoint-ui-v1` | `wf_16d0d88a0894862c1397122b4d172c6a` | `16d0d88a0894862c1397122b4d172c6a7c72b82bd187144b2f4573248cc2ee16` | `255ca2a636d35849657aa0414dc178152f732ac9e6f335daa9f18442e1f5ca4a` |
| material source | `core-checkpoint-material-source-v1` | `wf_a1d319af779ee8be79af3dcb58d0d755` | `a1d319af779ee8be79af3dcb58d0d755ee588d3f10497d1fe3b78a43b92d35db` | `fed1a4dcee2d2206cbaa70f3946598cbd59d69ad93676b86368c1c12dbecd6fe` |
| 2D sprite | `core-checkpoint-sprite-v1` | `wf_97ca4c167ee6a407de61346f1c6175c3` | `97ca4c167ee6a407de61346f1c6175c39799aebfde077d02e4ae901dd9fdd71e` | `ead65661be6fe01792c7d870ca0d2129bbe9f7f268507a14253fbb4cbf86e280` |

These identities are derived by the accepted R9 canonical JSON/SHA-256 rules from the committed typed definitions; tests verify deterministic identity and marker-free instantiated prompts.

## Resource/output policy

- concept/material: dimensions 256..1536, output count 1..4, aggregate cap 8,388,608 pixels, pack estimate 8192 MiB;
- UI/sprite: dimensions 64..1024, output count 1..4, aggregate cap 3,145,728 pixels, pack estimate 6144 MiB;
- `prompt` and `negative_prompt` are bounded non-empty strings matching the frozen R9.4 string contract;
- seed is explicit; steps 1..80; cfg 1.0..20.0; sampler/scheduler/denoise are fixed by v1;
- material output is explicitly `material_source_only=true`; R9.9 does not label generated color imagery as validated PBR maps.

R9.8 remains the execution-time VRAM admission authority; pack estimates do not fabricate free-memory proof.

## Rejected precursor

Candidate `a8913dd1c46730babec7ac123e65de4bb6c8ca52` was **not accepted**. R0 #1185 / `32644395498` and UI #1126 / `32644395464` succeeded, but Python Core #1159 / `32644395484` correctly failed on two newly introduced R9.9 tests (`2 failed, 722 passed, 6 skipped, 46 warnings` on Ubuntu).

The failures identified:

1. an aggregate-pixel test used a value exactly equal to the then-declared cap, so it could not prove composed-resource rejection;
2. pack-level validation allowed an empty negative prompt while the already-frozen R9.4 string contract rejects empty strings.

The accepted correction strengthened production rather than weakening gates: aggregate pixel caps are now strictly below the product of independent scalar maxima, and negative prompts are rejected as empty before R9.4 instantiation.

## Manual state

Frozen state: **CONDITIONAL**.

Final resolution: **CONDITIONAL NOT TRIGGERED**.

Reason: the accepted mandatory v1 packs introduce no mandatory new custom-node family and no mandatory new model family/token. They are Kodepoia-owned core-node definitions whose model requirement is resolved through the unchanged R9.4 `checkpoints` inventory with explicit selection when ambiguous. All R9.9-specific graph/parameter/resource/compatibility properties are deterministic and passed hosted Ubuntu/Windows. No new hardware/model-specific truth beyond the already accepted R9.8 local ComfyUI/GPU evidence is required.

If a future versioned pack introduces an authoritative new node/model family, that is new scope and must re-evaluate the frozen conditional; no model/custom-node/driver/runtime download is authorized merely to manufacture acceptance.

## Finalization rule

This accepted implementation head is not itself the final documentation head. Synchronize `docs/continuity/KODEPOIA_CONTINUITY.md` with the evidence above on the same branch, then run R0 Repository Guard, full Python Core and KodeStudio UI Smoke on that exact resulting head. Only after all three succeed may PR #121 merge. A post-merge continuity-only normalization must then pass the same three gates and merge before R9.10 starts.
