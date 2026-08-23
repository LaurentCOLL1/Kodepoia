# R9.4 — Validated workflow catalog + governed model resolver

## Status

Implementation candidate. Manual intervention is **NONE** per the frozen R9 plan.

## Purpose

R9.4 turns the R9.3 capability snapshot into a strict pre-execution authority. Kodepoia owns immutable workflow templates, validates every node/input/link against one exact `CURRENT` capability snapshot, resolves declared model requirements from that snapshot only, and produces a deterministic concrete `WorkflowInstance`. R9.4 does **not** submit anything to ComfyUI.

## Upstream compatibility basis

Current ComfyUI API material describes `/prompt` as accepting a node-ID-keyed prompt graph and returning prompt/node-error information, while object-info metadata describes node classes and typed inputs/outputs. R9.4 follows that external shape but adds a stricter Kodepoia-owned governance layer. The upstream format does not authorize arbitrary model- or user-generated graph execution.

## Immutable workflow definition

`WorkflowDefinition` identity binds:

- human-readable workflow name and positive revision;
- the normalized API-graph template;
- scalar parameter declarations and their target node/input;
- typed external input/output slot declarations;
- logical model requirements and exact accepted inventory-token aliases;
- the explicit node-class allowlist.

The full identity is SHA-256 and yields `wf_<32 hex>` as the stable definition ID. The graph is stored internally as canonical JSON rather than a mutable dictionary.

Every graph node contains exactly `class_type` and `inputs`. Node IDs, node classes and connections are immutable for a definition revision. Changing any of them creates a different workflow digest/ID.

## Internal slot markers

Templates may contain only three internal one-key markers:

- `{"$param": "name"}` for a declared typed scalar parameter;
- `{"$input": "name"}` for a declared typed external input slot;
- `{"$model": "requirement"}` for a declared model requirement.

Markers must match declarations exactly by node and input. Undeclared markers, duplicate target declarations and arbitrary objects/graph fragments are rejected. Before a `WorkflowInstance` is created, every marker must be replaced; an unresolved marker is a hard governance error.

R9.4 scalar values cannot themselves be arrays, mappings or node fragments. The only arrays retained in the template are immutable two-element ComfyUI node links `[source_node_id, output_index]`.

## Capability validation

Validation requires an exact R9.3 `CURRENT` snapshot. For every node:

- its class must be in the workflow allowlist and present in the snapshot;
- all capability-required inputs must exist;
- unknown inputs are rejected;
- fixed literals must satisfy choice/type/min/max metadata;
- declared parameter ranges/choices may narrow but never widen capability constraints;
- links must target an existing output index and its output type must match the destination input type;
- typed output slots must match the recorded node output metadata.

Validation evidence binds the workflow definition digest, capability snapshot identity and raw node-definition digests. A stale/unavailable snapshot cannot validate or resolve models.

## Deterministic parameter and seed policy

R9.4 does not generate a random seed. A workflow that declares a `seed` parameter requires an explicit non-negative integer within both workflow and capability bounds. All declared parameters must be supplied exactly once and no undeclared parameter is accepted. Parameter ordering does not affect instance identity.

## Governed model resolution

`ModelRequirement` declares:

- logical requirement ID;
- ComfyUI model category/type;
- fixed target node/input;
- zero or more exact accepted ComfyUI inventory tokens.

The resolver reads only the supplied R9.3 snapshot; it does not perform filesystem scans or network/download operations.

Resolution states are explicit:

- `RESOLVED`: exactly one deterministic candidate, or an explicit user selection that is one of the declared candidates;
- `MISSING`: no discovered candidate matches;
- `AMBIGUOUS`: multiple valid candidates exist and no explicit selection was supplied;
- `BLOCKED`: an explicit selection is not a valid candidate.

An ambiguous/missing/blocked resolution set cannot instantiate a workflow.

## R8 governance bridge

A ComfyUI inventory token remains a local service token, not content identity. Optional `VaultModelEvidence` may bind an already accepted R8 `AssetRevisionId`, exact content SHA-256, `ReuseScope`, R8 `AssetGovernanceOutcome` and concluded license token.

If no R8 evidence is supplied, the model is `EXTERNAL_LOCAL_UNKNOWN`, its license is `NOASSERTION`, and `exportable=false`. R9.4 never infers provenance or exportability from a filename. With Vault evidence, exportability is inherited only when the R8 reuse scope is `EXPORTABLE` and the accepted governance outcome is not `BLOCK`.

## Workflow catalog

`WorkflowCatalog` loads only caller-enumerated JSON basenames beneath one explicit root. It does not recursively discover workflows. Catalog files are size-bounded, cannot be symlinks or path escapes, use the frozen R9.1 `kodepoia.comfy-workflow-definition` version-1 envelope, and are reconstructed to recompute the canonical definition ID/digest. Tampering fails closed.

The R9.1 root envelope schema remains unchanged. R9.4 adds `schemas/comfy-workflow-definition-payload-v1.schema.json` as the strict payload authority so a previously frozen root compatibility contract is not retroactively tightened.

## Security invariants

- no arbitrary ComfyUI HTTP method/path;
- no workflow execution in R9.4;
- no raw model/user-generated graph execution;
- no model/custom-node download or install;
- no recursive filesystem/model scan;
- no graph fragment through parameters;
- no filename-derived provenance or license;
- no stale capability validation;
- no unresolved model substitution;
- no mutation of frozen R1–R8 governance semantics.

## Acceptance target

R9.4 is accepted only when R0 Repository Guard, full Python Core and KodeStudio UI Smoke succeed on the same exact implementation head. The implementation evidence is then frozen in `R9_4_ACCEPTANCE.md` and continuity, and that final documentation head must pass the same three gates before merge. A continuity-only post-merge normalization must then pass and merge before R9.5.
