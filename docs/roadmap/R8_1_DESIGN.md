# R8.1 — Asset/Vault contracts, identity, schemas + boundary — Design

R8.1 introduces the typed asset domain only. It does not implement durable Vault storage, transforms, search, Git/LFS mutation or UI.

## Identity

- `AssetId` is a logical identity and can be deterministically derived from an explicit stable namespace/key; mutable display names and paths are not identity.
- `AssetRevisionId` is derived from canonical revision identity: asset ID, role/kind, verified byte SHA-256 and length, reuse/preservation semantics, provenance and lineage.
- Runtime status is intentionally excluded from immutable revision identity.
- A serialized revision is accepted only when its revision ID recomputes exactly.

## Boundary

`VaultBoundary` composes the already accepted `WorkspaceBoundary` semantics around an explicitly configured local Vault root. Callers still pass only relative managed paths; traversal, absolute paths and resolved symlink escapes fail closed.

## Schemas

R8.1 freezes v1 JSON documents for asset records, immutable revisions and project references. Canonical JSON uses UTF-8, sorted keys and compact separators. Byte verification uses SHA-256 and exact content length.

No process, network, secret or arbitrary-root tool surface is introduced.
