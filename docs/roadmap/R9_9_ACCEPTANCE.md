# R9.9 Acceptance — Production 2D/UI/texture/concept workflow packs

Status: **IMPLEMENTATION CANDIDATE / HOSTED GATES PENDING**.

Authority: `docs/roadmap/R9_PLAN.md` R9.9.

## Candidate scope

The candidate implements the four frozen mandatory families through `ProductionWorkflowPackCatalog`:

- concept/key art;
- UI/icon/illustration;
- texture/material source;
- 2D sprite/asset.

Every v1 family is a deterministic R9.4 workflow definition using only the core node allowlist `CheckpointLoaderSimple`, `CLIPTextEncode`, `EmptyLatentImage`, `KSampler`, `VAEDecode`, `SaveImage`. No custom node, model download, arbitrary graph execution, process, remote endpoint or R8 bypass is introduced.

## Acceptance requirements

The exact accepted implementation head must pass, on the same commit:

- R0 Repository Guard — Ubuntu + Windows;
- full Python Core — all jobs, including Ubuntu/Windows tests and package builds;
- KodeStudio UI Smoke;
- deterministic R9.9 tests proving exact mandatory-family coverage, core-only node allowlists, explicit discovered model selection, deterministic compatibility evidence, stale/missing/ambiguous model rejection, seed/settings capture, dimension/output/pixel bounds, material-source-only semantics and absence of unresolved graph markers after instantiation.

The final documentation/continuity head must then pass the same three hosted gates before merge.

## Manual state

Frozen state: **CONDITIONAL**.

Current resolution: **CONDITIONAL NOT TRIGGERED**, subject to hosted-gate review.

Reason: the mandatory v1 workflow families do not require a new authoritative local custom-node family or a mandatory new model family/token. They are Kodepoia-owned core-node definitions whose model requirement is resolved through the unchanged R9.4 discovered `checkpoints` inventory with explicit selection when ambiguous. R9.9 therefore adds no hardware/model-specific truth beyond the already accepted R9.8 local ComfyUI/GPU evidence.

If review reveals that any mandatory pack actually depends on a real node/model family not already covered by accepted R9.8 evidence, STOP acceptance on the exact candidate head and run the bounded local workflow acceptance only with an already-installed user-selected compatible model. Do not install/download models, custom nodes, drivers, runtimes or expose ComfyUI remotely merely to satisfy this gate.

## Evidence to freeze after hosted CI

After the implementation candidate is green, record here:

- exact implementation SHA;
- R0 run number / run ID;
- Python Core run number / run ID and Ubuntu pytest totals;
- UI Smoke run number / run ID;
- exact mandatory family/definition identities;
- manual final state and reason;
- rejected precursor(s), if any, without weakening gates.

R9.10 MUST NOT START until this document and continuity are synchronized on the accepted evidence, the final exact documentation head is green, R9.9 is merged, and its post-merge continuity normalization is itself green and merged.
