# R9.3 — Acceptance

## Status

**IMPLEMENTATION ACCEPTED — final documentation gates pending**

Manual intervention: **NONE**.

## Exact implementation evidence

- Frozen subdivision: **R9.3 — Node/model inventory + capability snapshots**.
- Base normalized R9.2 `main`: `9c18a0dc88f311c6aab469cdd6c9a02ca453805b`.
- Dedicated branch: `r9/3-capability-inventory`.
- Exact accepted implementation head: `915075149fa81b31308c3eedcfa35e74f8a9b7a4`.
- R0 Repository Guard #1125 / run `32626438121`: **SUCCESS**.
- Python Core #1099 / run `32626438098`: **SUCCESS** (5/5 jobs).
- KodeStudio UI Smoke #1066 / run `32626438104`: **SUCCESS**.
- Ubuntu Python Core: `634 passed / 6 skipped / 46 warnings`; R7 integrated acceptance PASS; R8 integrated acceptance PASS.
- Python Core package builds: Ubuntu **SUCCESS**, Windows **SUCCESS**.
- Python Core Windows test job: **SUCCESS**.
- Integrated KodeStudio Windows smoke inside Python Core: **SUCCESS**.

## Accepted implementation

R9.3 introduces a read-only capability inventory over the already accepted R9.2 loopback transport. The fixed discovery surface is limited to `/system_stats`, `/features`, `/object_info`, `/models`, and `/models/{validated-model-type}`. No arbitrary public HTTP route/method, model download, custom-node install/update, node execution, or Kodepoia filesystem scan is exposed.

`ComfyCapabilitySnapshot` binds the loopback endpoint, system/version evidence, feature digest, normalized node definitions, normalized model inventories, and explicit unavailable components. `captured_at` is evidence only and is deliberately excluded from identity. Re-capturing unchanged capabilities at the same endpoint therefore yields the same identity digest.

Node metadata is normalized to the typed fields required by later workflow validation: class type, required/optional inputs, type or scalar-choice declarations, numeric bounds/step, output types/list flags, category, and selected lifecycle flags. Unknown extension metadata remains inert; it contributes only to a SHA-256 digest so drift becomes visible without turning metadata into instructions.

Model values returned by ComfyUI are treated as relative logical tokens only. Absolute paths, drive prefixes, backslashes, and traversal segments are rejected. A filename/token never manufactures provenance, license evidence, Vault identity, or exportability.

`diff_capability_snapshots` makes capability drift explicit as `STALE` evidence and identifies changed node classes/model categories/system evidence. `CapabilitySnapshotStore` is a rebuildable, root-confined atomic cache; unsafe names, path escapes, symlink entries, malformed envelopes, and identity tampering fail closed.

The frozen R9.1 envelope schema `schemas/comfy-capability-snapshot-v1.schema.json` remains unchanged. R9.3 adds the separate strict concrete payload authority `schemas/comfy-capability-snapshot-payload-v1.schema.json`, avoiding any retroactive reinterpretation of the accepted R9.1 contract.

## Rejected precursor

The first implementation candidate `5c714d49d775dd04d04bca95ec341289cc59a515` is **NOT ACCEPTED**.

Its exact-head runs were:

- R0 Repository Guard #1121: SUCCESS.
- KodeStudio UI Smoke #1062: SUCCESS.
- Python Core #1095: FAILURE.
- Ubuntu pytest: `2 failed / 632 passed / 6 skipped / 46 warnings`.

The two failures were useful acceptance findings rather than gate noise:

1. the candidate had incorrectly tightened the already-frozen generic R9.1 capability envelope schema; the accepted correction restores that schema unchanged and introduces a separate strict R9.3 payload schema;
2. the timestamp-determinism fixture compared captures from two different ephemeral endpoints, although endpoint identity is intentionally part of the snapshot digest; the accepted correction performs the two timestamp captures against the same endpoint.

No production safety check, schema compatibility check, warning baseline, or CI gate was weakened to obtain the accepted result.

## Acceptance properties satisfied

- deterministic fake ComfyUI fixtures cover object-info, model categories/tokens, system/features, capability drift, unknown extension metadata, path-shaped hostile model tokens, persistence/tampering, and array-valued `/models` transport behavior;
- missing/invalid protocol evidence never becomes an authoritative empty success;
- timestamp-only changes do not change capability identity;
- endpoint changes do change identity by design;
- snapshot/canonical payloads are bounded and versioned;
- R9.1/R9.2 boundaries remain intact;
- manual state remains **NONE**.

## Final documentation gate

This document and the synchronized continuity file must be committed on the same R9.3 branch. R0 Repository Guard, full Python Core, and KodeStudio UI Smoke must all succeed on that exact final documentation head before PR #109 may merge. After merge, a continuity-only normalization must itself pass the three exact-head gates and merge before R9.4 may start.
