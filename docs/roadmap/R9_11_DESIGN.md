# R9.11 — Adversarial hardening + R9 integrated acceptance — Design

## Status and authority

**IMPLEMENTATION CANDIDATE — exact-head acceptance pending.**

Authority: `docs/roadmap/R9_PLAN.md` R9.11. Base normalized R9.10 `main`: `8cd01c5f5d1ae667602d2e13c1d86219d86748cf`.

Manual mode is frozen as **CONDITIONAL**. This implementation does not change hardware-facing ComfyUI/GPU semantics, does not introduce a new node/model/runtime path, and does not invalidate the accepted R9.8 local GPU evidence. Therefore no new manual run is triggered by this candidate unless later implementation work changes those facts.

## Objective

Close R9 by proving the R9.1–R9.10 system fails closed across hostile protocol, workflow, identity, output and resource conditions, then bind every R9 subdivision to canonical Git-blob acceptance evidence in one deterministic integrated report.

R9.11 does not add a new generation feature. It adds adversarial cross-subsystem evidence and a phase-level evidence model.

## Adversarial coverage strategy

R9.11 deliberately reuses the accepted full regression suite instead of cloning lower-level fixtures. The R9.2–R9.9 tests already provide authoritative deterministic coverage for the detailed attacks below; R9.11 adds seam tests proving the safe surfaces still compose correctly.

### Endpoint, HTTP and WebSocket attacks

Existing R9.1/R9.2 coverage re-executed by full Python Core proves:

- non-loopback endpoints and `localhost` are rejected;
- redirect origin changes are rejected;
- malformed/oversized HTTP JSON is bounded;
- timeout/unavailable states do not manufacture readiness;
- oversized WebSocket frames are rejected before payload read;
- malformed event JSON and invalid progress ranges fail closed;
- event prompt-ID mismatch and terminal-state regression are rejected;
- reconnect count is bounded;
- `ComfyUIClient` has no public arbitrary request/get/post/urlopen surface.

R9.11 adds a cross-layer assertion that `ComfyService` also has no arbitrary transport/process/install/graph execution surface and that the CLI parser exposes no arbitrary endpoint option.

### Workflow, parameter and model attacks

Existing R9.4/R9.9 coverage re-executed by full Python Core proves:

- unknown-node graph injection is rejected;
- connection type mismatch is rejected;
- undeclared `$param` markers and graph-fragment parameter values are rejected;
- workflow catalog path escape/tampering is rejected;
- parameter constraints cannot widen node capability;
- stale capability snapshots cannot validate or resolve;
- ambiguous/missing/invalid model selections remain blocked;
- the production catalog contains only the four frozen families and core-node graphs;
- production prompt/dimension/output/pixel budgets remain bounded.

R9.11 additionally attempts `graph`, `url`, `command`, `model_download` and `custom_node_install` fields through the R9.9 request seam. The exact-field contract rejects all of them before execution. The R9.10 model-selection seam remains a single governed `checkpoint` token mapping.

### Prompt/history/run identity and duplicate-submit races

Existing R9.5 coverage re-executed by full Python Core exercises:

- persisted prompt/history correlation validation;
- forged prompt content and correlation mismatch rejection;
- ambiguous/lost submit responses without blind duplicate submission;
- reconciliation from queue/history rather than UI-local state;
- terminal state monotonicity.

R9.10 reconstruction additionally binds persisted capability identity and reconstructed workflow-instance digest to the run manifest. A mismatch fails closed before reconcile/cancel operations can trust the run.

### Output attacks and R8 lineage

Existing R9.6 coverage re-executed by full Python Core proves:

- cross-prompt output references are rejected;
- output filename/subfolder traversal and drive syntax are rejected before retrieval/promotion;
- corrupt image signatures, hash mismatch and byte-length mismatch fail before Vault promotion;
- multi-output retrieval failure cannot silently promote an unvalidated set;
- non-SUCCEEDED runs cannot promote outputs;
- capture-store tampering is rejected;
- successful generated outputs are promoted through the accepted R8 Asset/Transform pipeline as DERIVED revisions with reconstructable lineage.

R9.11 adds an explicit cross-run output-reference seam assertion using the same R9.6 guard.

### Cancellation, reconnect and free-memory attacks

Existing R9.7 coverage re-executed by full Python Core proves:

- cancellation is targeted to the persisted job;
- legacy running cancellation is blocked rather than using global `/interrupt`;
- cancel/complete races reconcile to the already-terminal result without a cancel side effect;
- disappeared jobs do not fabricate `CANCELLED`;
- restart recovery repairs/reconciles persisted state;
- `/free` is blocked while known runs are active;
- `/free` acknowledgement never fabricates reclaimed bytes;
- failed/OOM terminal cleanup is ordered and bounded;
- lifecycle audit tampering is rejected.

R9.11 adds a façade-level test proving `ComfyService.free_memory()` passes only its bounded persisted known-run set and preserves `reclaimed_bytes = null` semantics.

### VRAM/OOM/coexistence attacks

Existing R9.8 coverage re-executed by full Python Core proves:

- impossible telemetry such as free VRAM greater than total is rejected;
- ADMIT/DEFER/REJECT/UNKNOWN decisions remain explicit;
- cleanup/re-measure order is deterministic;
- Ollama models are never unloaded without an explicit allowlist;
- OOM feedback can raise but never silently lower the learned estimate;
- evidence/audit tampering is rejected.

R9.11 adds façade-level reserve/headroom bound assertions and retains the accepted R9.8 hardware evidence rather than performing a destructive or redundant real-GPU red-team run.

### Bounded many-job state

R9.10 bounds lifecycle evidence enumeration to 10,000 accepted persisted run files. R9.11 tests this fail-closed behavior with a deliberately reduced test-only bound, proving deterministic sorted enumeration at the bound and rejection at bound + 1 without creating thousands of real files.

## R9 integrated acceptance model

R9.11 adds `kodepoia.comfyui.acceptance` and `schemas/r9-integration-report-v1.schema.json`. It is independent of the frozen R7/R8 integrated models and does not rewrite their reports.

The R9 report requires exactly R9.1 through R9.11 in order. Each subdivision binds:

- canonical `docs/roadmap/R9_<n>_ACCEPTANCE.md` source;
- SHA-256 of the canonical Git blob;
- exact byte length;
- accepted implementation head;
- manual state and explicit reason;
- derived manual satisfaction;
- optional reviewed manual-evidence digest/byte length.

R9.8 is special only because its frozen manual state is REQUIRED. A passing R9.8 record with `REQUIRED_SATISFIED` must carry the reviewed local evidence digest and byte length. Repository validation also requires that the canonical R9.8 acceptance document explicitly references those values. The integrated report does not need or attempt to read the operator-local evidence file from hosted CI.

A passing report cannot contain explicit or derived blockers. R9.11's accepted implementation head must equal the report `source_sha`.

## Anti-circularity sequence

R9.11 follows the accepted R8.11 sequence:

1. implement adversarial tests, R9 integration contracts/schema and this design document;
2. pass R0 Repository Guard, full Python Core and KodeStudio UI Smoke on one immutable **implementation head**;
3. create `R9_11_ACCEPTANCE.md` that records that immutable implementation head and gate IDs;
4. add `scripts/r9_integrated_acceptance.py` with the accepted R9.1–R9.11 heads/manual states and Git-blob loader;
5. while `R9_INTEGRATED_ACCEPTANCE.json` is absent, let the script print the exact canonical candidate;
6. check in that exact report, synchronize continuity and add the Python Core Linux verification hook;
7. pass the three final gates on one exact documentation/evidence head;
8. merge R9.11;
9. perform final continuity-only normalization and exact-head gates before marking R9 COMPLETE.

This avoids a report that attempts to certify the commit containing its own SHA.

## Manual intervention determination

The R9.11 conditional is **not triggered by the current implementation candidate** because:

- R9.8 REQUIRED local hardware evidence is already reviewed and valid for the unchanged hardware-facing contracts;
- R9.11 does not modify ComfyUI wire compatibility, VRAM telemetry/admission, lifecycle cleanup, workflow node/model requirements or output capture semantics;
- all new adversarial operations use deterministic hosted fixtures or pure contract checks;
- no real user project, ComfyUI process, GPU allocation, Ollama model or local model installation is mutated by R9.11 tests.

If a later R9.11 fix changes a hardware-facing authoritative path or invalidates R9.8 evidence, this determination must be revisited and work must stop before phase completion until new exact-head local evidence is reviewed.

## Rollback

If R9.11 hardening or integrated evidence fails, R9 remains IN PROGRESS. Remove/fix only the R9.11 candidate; do not weaken R9.1–R9.10 gates and do not edit frozen R7/R8 integrated evidence to make R9 pass.
