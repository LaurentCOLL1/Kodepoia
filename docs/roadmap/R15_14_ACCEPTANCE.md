# R15.14 — Specialized-model registry acceptance

Status: IMPLEMENTED / exact-head acceptance pending.

This acceptance surface verifies immutable version identity, complete lineage binding, role-scoped eligibility, fail-closed rejected/inconclusive activation, mutable runtime-tag digest verification, atomic persisted promotion, restart-safe rollback pointers, SafeChange snapshotting, audit events and compatibility with the existing R3 `KodeModelRouter`/`ModelRegistry` abstractions.

The registry never treats an Ollama tag as an immutable identity. A runtime reference must resolve to the artifact digest bound by the accepted registry record before promotion. Promotion is authorized only for `PROMOTE_TO_EXPORT`; a post-promotion health failure restores the exact prior persisted mapping.

Manual intervention: NONE.
