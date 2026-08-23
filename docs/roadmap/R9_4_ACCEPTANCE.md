# R9.4 — Acceptance evidence

**Subdivision:** R9.4 — Validated workflow catalog + governed model resolver  
**Manual intervention:** NONE  
**Base normalized `main`:** `e9152cbe15ba9da2b383e2e6577251ca7c424e41`  
**Accepted implementation head:** `e158fd643ecf55a1ed9022193a48d2d1ee1716ed`

## Exact-head CI

All required implementation gates completed successfully on the exact implementation head `e158fd643ecf55a1ed9022193a48d2d1ee1716ed`:

- R0 Repository Guard #1132 / run `32627342083`: **SUCCESS**.
- Python Core #1106 / run `32627342056`: **SUCCESS**.
  - Ubuntu pytest: `643 passed / 6 skipped / 46 warnings`.
  - R7 integrated acceptance: PASS.
  - R8 integrated acceptance: PASS.
  - Ubuntu package build: SUCCESS.
  - Windows Python Core/package/UI jobs: SUCCESS as required by the workflow.
- KodeStudio UI Smoke #1073 / run `32627342058`: **SUCCESS**.

## Accepted R9.4 properties

The accepted implementation establishes all frozen R9.4 requirements without executing a ComfyUI workflow:

1. `WorkflowDefinition` is immutable by canonical SHA-256 identity and stable `wf_<32 hex>` ID. Node IDs, node classes, links, declared scalar/input/model targets, allowlist and model requirements all participate in identity.
2. Templates accept only Kodepoia-owned internal `$param`, `$input` and `$model` markers. Marker targets must exactly match declarations; undeclared or duplicate-target mutation fails closed.
3. Validation requires a `CURRENT` R9.3 capability snapshot. Node presence, allowlist membership, required/unknown inputs, scalar constraints, connection output/input types and typed output slots are checked against the snapshot.
4. Workflow parameter constraints may narrow but never widen discovered capability constraints. Seed values are explicit non-negative integers; R9.4 does not generate hidden randomness.
5. Parameter values are JSON scalars only. Arbitrary mappings, arrays or graph fragments cannot be injected through a parameter slot.
6. `GovernedModelResolver` resolves only from the supplied R9.3 model inventory and exposes explicit `RESOLVED`, `MISSING`, `AMBIGUOUS` and `BLOCKED` states. It performs no scan, download or install.
7. Multiple valid model candidates remain `AMBIGUOUS` until an explicit valid selection is provided. Invalid explicit selections are `BLOCKED`; no filename is guessed.
8. Optional `VaultModelEvidence` reuses accepted R8 `AssetRevisionId`, content digest, `ReuseScope` and `AssetGovernanceOutcome`. Without R8 evidence a local model is `EXTERNAL_LOCAL_UNKNOWN`, license `NOASSERTION`, and not exportable.
9. Concrete `WorkflowInstance` identity binds definition, exact capability snapshot, exact model-resolution set, explicit parameters/input bindings and the final marker-free API prompt. Parameter map ordering does not alter identity.
10. `WorkflowCatalog` loads only explicitly enumerated safe JSON basenames inside one root, rejects symlinks/path escapes/oversize/invalid JSON, reconstructs canonical identity and rejects tampering. It does not recursively discover arbitrary workflows.
11. The frozen R9.1 root envelope schema was not tightened. R9.4 adds the separate strict `comfy-workflow-definition-payload-v1.schema.json` payload authority.
12. No workflow submission, arbitrary ComfyUI route/method, model/custom-node install/update, model download, recursive model scan or quality-scoring surface was introduced.

## Adversarial/negative evidence

The deterministic suite covers:

- unknown node injection;
- incompatible link type;
- undeclared marker/target mutation;
- graph-fragment injection through a parameter;
- ambiguous, missing and invalid model selection;
- stale capability snapshot rejection;
- catalog tampering and path traversal;
- parameter-range widening beyond capability constraints;
- missing R8 provenance/license evidence remaining non-exportable `NOASSERTION`.

## External compatibility evidence

Current official ComfyUI API material confirms that prompt execution consumes a node-ID-keyed prompt object and returns a `prompt_id` plus node-error information, while history entries retain prompt/extra-data/output/status evidence. R9.4 uses that external shape only as compatibility evidence; Kodepoia's allowlist, capability validation and governed model resolution remain authoritative.

## Manual state

**NONE.** R9.4 acceptance requires no real GPU, model download, custom-node installation or user-specific ComfyUI deployment. All frozen R9.4 properties are deterministic pre-execution contracts and are established by exact-head CI fixtures and current upstream compatibility evidence.

## Final documentation gate

This file pins the accepted implementation head. After this acceptance document and continuity synchronization are committed, the new exact documentation head must independently pass R0 Repository Guard, full Python Core and KodeStudio UI Smoke before PR #111 may merge. After merge, a continuity-only normalization must pass and merge before R9.5 starts.
