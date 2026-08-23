# R9.6 — Generated-output capture + R8 Vault/AssetPipeline lineage bridge

## Status

Implementation candidate. R9.6 remains unaccepted until R0 Repository Guard, full Python Core, and KodeStudio UI Smoke succeed on the same exact head, acceptance/continuity evidence is committed, and the final documentation head is re-gated.

## Frozen scope

R9.6 implements only the bridge from a reconciled R9.5 `SUCCEEDED` run to canonical R8 asset revisions. It does not scan ComfyUI output directories, create a second media store, judge output quality, publish remotely, alter R8 identity/governance semantics, or add arbitrary HTTP/filesystem surfaces.

Manual intervention: **NONE**.

## Authority boundaries

- `ComfyRunStore` remains the source of accepted run/output-reference evidence.
- `ComfyUIClient.retrieve_output()` remains the only network retrieval path and is fixed to `/view` on the exact accepted loopback origin.
- R8 `AssetService` remains the public governed Vault façade.
- R8 `TransformService` remains the DERIVED-revision and lineage authority. R9.6 does not duplicate its promotion or cache rules.
- R8 license/governance remains authoritative. Generated assets without explicit legal evidence remain unknown/`NOASSERTION`; R9.6 never invents export rights.

## Capture flow

1. Load the exact R9.5 run manifest and require `SUCCEEDED`.
2. Require the capture client's exact origin to equal the run's persisted capability endpoint.
3. Select outputs only by explicit `(node_id, output_index)` specs that must exist in the reconciled run manifest.
4. Reject cross-prompt references, unsupported storage types, absolute/traversal/nested filenames, Windows drive-qualified tokens, and unsafe subfolders before retrieval.
5. Retrieve only through `ComfyUIClient.retrieve_output()`.
6. Hash every output, validate optional expected SHA-256/length, and validate supported image signatures against their filename extension.
7. Stage and reverify all requested outputs beneath the project-managed `.kodepoia/comfyui/output-staging/<run_id>` boundary. All retrieval/validation completes before the first asset promotion.
8. Persist canonical generation evidence beneath `.kodepoia/comfyui/generation-evidence/<run_id>.json` and ingest it through `AssetService` as a Vault-local DOCUMENT source revision.
9. Promote each validated media output through a registered pure-Python R8 `TransformService` adapter. The transform lineage includes the generation-evidence revision and any explicitly supplied source/input revisions.
10. Persist immutable R9.6 capture evidence containing the resulting R8 asset/revision IDs and exact output digests.
11. Remove managed byte staging in all outcomes.

## Generation evidence

The generation-evidence revision binds:

- R9 run ID and exact run-manifest digest;
- hashed prompt identifier rather than a server path;
- workflow definition ID/digest;
- capability identity and accepted ComfyUI/Python environment versions;
- model-resolution digest and canonical resolution evidence;
- workflow-instance/prompt digests;
- parameter values, input bindings and seeds;
- explicit source revision IDs;
- per-output node/index, output-reference digest, content SHA-256/length and asset kind.

Server filenames/subfolders are not persisted as local filesystem locators. The capture manifest stores only canonical R8 identities and content evidence.

## Multi-output semantics

R9.6 pre-retrieves and validates the full declared output set before any promotion, so cross-prompt/path/type/hash/length/retrieval failures cannot create a READY generated media revision.

If a rare failure occurs after the first R8 promotion (for example, local storage failure during a later promotion), R9.6 must never claim logical completion. It preserves an immutable `PARTIAL` capture record naming only the READY revisions that actually exist and raises `ComfyPartialCaptureError`. It does not perform hidden destructive rollback because R8 deletion/reference policy is governed independently. A caller must treat `PARTIAL` as blocked/incomplete evidence, never as a complete generated set.

## Content validation

Image/UI/texture outputs accept bounded non-empty bytes with recognized PNG, JPEG, GIF, or WebP signatures and require a matching filename extension. Other R8 kinds remain byte/hash/length verified without inventing a media parser in R9.6. Future richer type validation belongs to an explicit later contract change, not silent heuristic expansion here.

## Persistence

`ComfyOutputCaptureStore` is an immutable, root-confined adjunct evidence store keyed by generated R9 run ID. It is separate from canonical R8 Vault manifests. Its strict payload schema is `schemas/comfy-output-capture-payload-v1.schema.json`; the frozen R9.1/R9.5 root envelopes are unchanged.

## Acceptance coverage

The deterministic binary fixture and tests must establish:

- successful output retrieval creates a reconstructable R8 DERIVED lineage through generation evidence plus source revision inputs;
- cross-prompt references fail closed;
- POSIX traversal, nested filename tokens, Windows drive-qualified tokens and unsafe subfolders fail before network retrieval/promotion;
- hash/length mismatch and invalid image signatures fail before any promotion;
- FAILED/CANCELLED/non-terminal runs never retrieve or promote outputs;
- a later retrieval failure in a multi-output set happens before any promotion;
- capture evidence schema-validates and tampering is rejected;
- conservative R8 license/governance state is preserved.

## Rollback and recovery

Unpromoted staging is disposable and removed automatically. Canonical R8 source/derived revisions are never mutated. Any promoted revision remains governed by existing R8 reference/deletion rules; no R9.6 cleanup path bypasses those rules.

## Security invariants

- loopback exact-origin only;
- no output-directory scan;
- no server path interpreted as a local path;
- no arbitrary HTTP route;
- no arbitrary transform executable/argv/environment;
- no fabricated provenance/license/exportability;
- no hidden deletion rollback;
- no terminal success inferred by R9.6: only a pre-existing reconciled R9.5 `SUCCEEDED` run is eligible.
