# R8.1 — Asset/Vault contracts, identity, schemas + boundary — Acceptance

**Status:** COMPLETE / ACCEPTED  
**Manual intervention:** NONE

## Accepted implementation

- Exact implementation head: `0e382bcdc82c5d289a9007c40d4a4b6c72120e5c`.
- PR: #85.
- Merge SHA: `7001d9042dda5611f4dbcf7dacb7cd29110e6735`.

## Authoritative CI on the exact head

- R0 Repository Guard #1043 / `32602291539`: SUCCESS.
- Python Core #1017 / `32602291581`: SUCCESS 5/5.
- Ubuntu authoritative suite: `521 passed / 5 skipped / 46 warnings`.
- KodeStudio UI Smoke #984 / `32602291524`: SUCCESS.

## Accepted scope

Typed Asset/Vault contracts, deterministic logical/revision identity, source/derived role, v1 schemas, canonical/tamper-checked serialization, SHA-256 + exact-length byte verification and `VaultBoundary` confinement composed from the accepted `WorkspaceBoundary` semantics. Traversal, absolute-path and resolved symlink escapes fail closed. No R8.2 storage or later-phase behavior was implemented on this head.
