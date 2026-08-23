# R9.3 — Node/model inventory + capability snapshots

## Status

Implementation candidate. R9.3 manual intervention is **NONE** per the frozen R9 plan.

## Purpose

R9.3 captures what the connected loopback ComfyUI instance actually exposes so later workflow validation never assumes node classes, parameter contracts, model categories or model tokens.

## Fixed discovery surface

The inventory uses the accepted R9.2 loopback transport and only these ComfyUI routes:

- `GET /system_stats`
- `GET /features`
- `GET /object_info`
- `GET /models`
- `GET /models/{validated-model-type}`

There is no arbitrary-route public API, filesystem scan, model download, custom-node install/update or node execution.

## Node normalization

`ComfyNodeDefinition` retains only fields required for later validation:

- immutable node `class_type`;
- optional category;
- normalized required/optional inputs;
- input type token or scalar choice set;
- numeric min/max/step constraints when present;
- output types and list flags;
- deprecated/experimental/API-node flags.

The full upstream metadata object contributes only a SHA-256 digest. Unknown extension metadata therefore changes snapshot identity and can make prior evidence stale, but it is never surfaced as executable instruction.

## Model normalization

`/models` provides reported model categories and `/models/{folder}` provides the corresponding model tokens. Tokens are treated as opaque relative identifiers, not content identities or filesystem authorities. Absolute paths, Windows drive prefixes, backslashes and traversal segments are rejected. R8 remains the only authority for Vault content identity/provenance when a later resolver has Vault evidence.

## Snapshot identity

`ComfyCapabilitySnapshot.identity_sha256` binds:

- loopback endpoint identity;
- ComfyUI/Python/system evidence;
- feature digest;
- normalized node definitions including raw-metadata digests;
- normalized model inventories;
- explicit unavailable components.

`captured_at` is evidence only and is excluded from identity, so recapturing unchanged capabilities at the same endpoint yields the same digest.

## State and stale detection

A fully captured snapshot is `CURRENT`. Missing/unavailable discovery components must never be represented as an authoritative empty inventory. `diff_capability_snapshots` compares identities and reports `STALE` plus added/removed/changed node classes, changed model categories and system changes.

## Rebuildable cache

`CapabilitySnapshotStore` is a rebuildable cache only. It writes the accepted version-1 envelope atomically beneath a caller-selected root, rejects unsafe cache names/path escapes/symlink entries, recomputes the snapshot identity on load, and fails closed on tampering.

## Schema compatibility

R9.1 froze `schemas/comfy-capability-snapshot-v1.schema.json` as the generic version-1 envelope contract. R9.3 deliberately leaves that frozen envelope unchanged and adds `schemas/comfy-capability-snapshot-payload-v1.schema.json` for the concrete strict payload. The payload schema uses `additionalProperties: false` and bounds collection sizes, scalar fields and SHA-256 values. This preserves the accepted R9.1 contract while giving R9.3 a strict validation authority for its newly defined payload.

## Security invariants

- loopback origin remains enforced by R9.1;
- no arbitrary route/method is exposed publicly;
- no arbitrary filesystem scan occurs in Kodepoia;
- no model/custom-node download or installation;
- metadata text is evidence, never instruction;
- model filenames do not imply provenance/license/exportability;
- timestamp does not poison deterministic identity;
- missing evidence does not become empty-success.

## Acceptance target

R9.3 is accepted only after R0 Repository Guard, full Python Core and KodeStudio UI Smoke succeed on the same exact implementation head, followed by an acceptance/continuity documentation head that passes those same gates before merge. Post-merge continuity normalization is required before R9.4.
