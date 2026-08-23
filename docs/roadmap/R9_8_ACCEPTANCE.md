# R9.8 Acceptance — VRAM telemetry, admission scheduler + Ollama coexistence

Status: **REQUIRED LOCAL GPU EVIDENCE SATISFIED; FINAL DOCUMENTATION GATES PENDING**.

Authority: `docs/roadmap/R9_PLAN.md` R9.8. This document does not authorize R9.9 until the final documentation/continuity head passes all three hosted gates, R9.8 is merged, and its post-merge continuity normalization is merged.

## Accepted implementation head

Exact R9.8 implementation candidate:

- `86777ddc7a87ad6041ddc599e20e93af38512a19`

Hosted gates on that exact head:

- R0 Repository Guard #1179 / `32642291824`: **SUCCESS**;
- Python Core #1153 / `32642291811`: **SUCCESS 5/5**;
- Python Ubuntu: **719 passed / 6 skipped / 46 warnings**;
- package builds Ubuntu + Windows: **SUCCESS**;
- KodeStudio UI Smoke #1120 / `32642291850`: **SUCCESS**;
- R7 integrated acceptance: **PASS**;
- R8 integrated acceptance: **PASS**.

The accepted implementation includes deterministic tests for telemetry, admission, total/reserve/headroom policy, cleanup/re-measure, explicit Ollama coexistence, OOM estimate monotonicity, Health/Budget bridge, audit/evidence tamper rejection, targeted workflow capability/model inventory, current ComfyUI UUID wire prompt IDs while preserving frozen R9.5 logical `kp_<32hex>` identities, and bounded history reconciliation that accepts metadata-only or value-preserving INT/FLOAT normalization while still rejecting semantic prompt mutation.

## REQUIRED local acceptance — SATISFIED

Reason for the frozen REQUIRED gate: hosted runners cannot authoritatively prove real local GPU VRAM allocation/release or the installed ComfyUI backend behavior.

The operator executed the accepted local runner from a clean worktree on exact candidate head `86777ddc7a87ad6041ddc599e20e93af38512a19` against loopback ComfyUI and returned the canonical evidence file `.kodepoia/evidence/r9-8-local-vram.json` for review.

Reviewed canonical local evidence:

- envelope: `schema=kodepoia.comfy-vram-evidence`, `version=1`;
- evidence file byte length: **5744 bytes**;
- candidate head: `86777ddc7a87ad6041ddc599e20e93af38512a19`;
- evidence digest SHA-256: `a8412a92ea2d1f456fdc3fdf47aa1a3ac63257a69df8854d36162128e6f0a967`;
- independently recomputed canonical digest: **MATCH**;
- status: **pass**;
- failure reason: `null`;
- ComfyUI version: `0.33.0`;
- endpoint: `http://127.0.0.1:8188`;
- capability identity SHA-256: `8bcdaa1ab206d9fde8762b3e551d5fbef088856d0e156dbe6c97ae5db52734e7`;
- device index: `0`;
- device: `cuda:0 AMD Radeon RX 6750 XT : native`;
- backend type: `cuda`;
- measured total VRAM: `12868124672` bytes;
- measured free VRAM at admission: `12461146112` bytes;
- configured estimate: `8589934592` bytes (8192 MiB);
- reserve: `536870912` bytes (512 MiB);
- headroom: `536870912` bytes (512 MiB);
- required free VRAM: `9663676416` bytes;
- scheduler initial/final decision: **admit**;
- scheduler reason: measured free VRAM satisfies estimate plus reserve/headroom;
- workflow definition: `wf_3aa2ac5225d8a3d88bcf8b3b7aee7205`;
- workflow instance digest SHA-256: `7a42edf3db886f8902e78fafe7330fcda1a190de0d2de2ad2aa0cf72c6b6e5bd`;
- run ID: `run_dccd6ff31d2f45f5add31415f694abf5`;
- run manifest digest SHA-256: `b97ebbb54bf96a23726dc98ec41abfac58c8936e9acd2179bbd452d55425095b`;
- generated output SHA-256: `a18b2eae0fd90f36382e92638bef7984cd591cfd8d9d2466941f66e65f488e92`;
- generated output length: `1029726` bytes;
- memory observation start: `12461146112` free bytes;
- memory observation minimum: `4410702336` free bytes;
- observed peak delta: `8050443776` bytes;
- memory observation end: `12461146112` free bytes;
- OOM observed: `false`;
- terminal `/free` request: acknowledged;
- terminal cleanup unload-models request: `true`;
- terminal cleanup free-memory request: `true`;
- `reclaimed_bytes`: deliberately `null` per accepted R9.7 semantics; cleanup acknowledgement is not fabricated as byte reclamation;
- resource audit chain: **valid**;
- lifecycle audit chain: **valid**;
- Ollama state: **n/a**;
- Ollama reason: no Ollama model was already loaded; no model was loaded or downloaded for this gate;
- Ollama restored models: none.

The observed peak delta (`8050443776` bytes) is below the configured workflow estimate (`8589934592` bytes), while the scheduler retained the separate 512 MiB reserve and 512 MiB headroom. The evidence therefore establishes a real admitted generation on the installed GPU/backend without weakening the configured resource policy.

The authoritative runner also performed a terminal cleanup request followed by a fresh `/system_stats` measurement. The evidence does not claim a fabricated reclaimed-byte quantity; that field remains `null` as required by R9.7/R9.8 semantics.

## Compatibility discoveries resolved during REQUIRED acceptance

The real local gate surfaced several upstream/custom-installation compatibility conditions that deterministic hosted fixtures could not authoritatively reveal. They were corrected without weakening frozen R9.1–R9.7 contracts:

1. an unrelated malformed custom-node `output_is_list` no longer blocks a workflow that does not reference that node; R9.8 scopes discovery to node classes actually present in the governed R9.4 workflow, while any required malformed node remains fail-closed;
2. unrelated Windows-native model tokens no longer poison global discovery; R9.8 scopes model inventory to model types and exact governed target tokens required by the selected workflow, while accepted model identity remains the unchanged R9.3 forward-slash token contract;
3. current ComfyUI requires client-supplied `prompt_id` values to be canonical UUIDs; the R9.8 wire compatibility facade deterministically maps frozen R9.5 logical `kp_<32hex>` identity to/from the same 128-bit UUID only at the transport boundary;
4. current ComfyUI may persist validation-normalized scalar inputs, such as a FLOAT input represented as `1.0` after submission of JSON integer `1`; R9.8 reconciliation accepts only complete structural equality plus metadata-only changes and value-preserving finite INT/FLOAT normalization. Numeric value changes, bool/number substitution, input/class/node mutations and other semantic changes remain rejected.

These are R9.8 compatibility adaptations around unchanged accepted foundations, not an ADR-level reinterpretation of R9.3/R9.5 identity or governance.

## Failure-handling policy retained

The accepted gate did not require installing/updating GPU drivers, ComfyUI, custom nodes, models, runtimes or Ollama models. No reserve/headroom weakening, arbitrary model selection, remote ComfyUI exposure, process kill, GPU reset or model download was used.

Any future re-run that produces a non-zero exit, REJECT/DEFER/UNKNOWN final decision, failed generation, missing output, audit failure, head mismatch, dirty worktree, unavailable required model/workflow or malformed evidence remains a failed gate and must not be converted into PASS by weakening policy.

## Gate state

Manual R9.8: **REQUIRED SATISFIED** on implementation head `86777ddc7a87ad6041ddc599e20e93af38512a19` with reviewed local evidence digest `a8412a92ea2d1f456fdc3fdf47aa1a3ac63257a69df8854d36162128e6f0a967`.

R9.8 is **not yet COMPLETE** at this commit. The final documentation/continuity head must now pass R0 Repository Guard, full Python Core and KodeStudio UI Smoke on that exact head; then PR #119 may merge. A continuity-only post-merge normalization must itself pass all three gates and merge before R9.9 may start.
