# R8.2 — Inter-project Vault store, revisions, reuse + preservation — Design

R8.2 adds durable local storage on top of R8.1 contracts.

- Immutable bytes are stored once under `objects/sha256/<prefix>/<digest>` and always verified by SHA-256 + length.
- Logical revisions and provenance remain separate even when bytes deduplicate.
- Canonical JSON manifests are the recovery authority; SQLite is a rebuildable transactional index.
- Ingest copies an authorized project file into Vault staging, hashes/verifies staged bytes, atomically promotes the immutable object, then commits manifests/index state.
- Project references are explicit canonical records; materialization resolves only through the target `WorkspaceBoundary`, verifies source and temporary-copy bytes, and uses atomic replacement.
- Deletion is two-phase. Project references and pinned-source preservation block removal. Orphan object removal occurs only after the last revision reference is removed.
- No symlink-based materialization, remote service, transform execution, semantic search or Git history operation is introduced.
