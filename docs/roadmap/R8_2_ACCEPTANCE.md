# R8.2 — Inter-project Vault store, revisions, reuse + preservation — Acceptance

**Status:** COMPLETE / ACCEPTED  
**Manual intervention:** NONE

## Accepted implementation

- Exact implementation head: `2046b981cb9506999c40e3fee1a22608efecaa80`.
- PR: #86.
- Merge SHA: `2d68f918b1058c1dd75be236ad74048eb598a3e6`.

## Authoritative CI on the exact head

- R0 Repository Guard #1045 / `32602493996`: SUCCESS.
- Python Core #1019 / `32602493966`: SUCCESS 5/5.
- Ubuntu authoritative suite: `526 passed / 5 skipped / 46 warnings`.
- KodeStudio UI Smoke #986 / `32602493972`: SUCCESS.

## Accepted scope

Content-addressed immutable Vault objects, canonical recovery manifests, rebuildable transactional SQLite index, authorized project ingest, exact verification, distinct logical revisions/provenance over deduplicated bytes, explicit project references, verified materialization, preservation/pinning and two-phase deletion. Canonical object bytes are removed only when no remaining revision needs them and policy permits removal.
