# R15.14 — Specialized-model registry acceptance

Status: TECHNICAL ACCEPTED / fresh exact-END acceptance pending.

This acceptance surface verifies immutable version identity, complete lineage binding, role-scoped eligibility, fail-closed rejected/inconclusive activation, mutable runtime-tag digest verification, atomic persisted promotion, restart-safe rollback pointers, SafeChange snapshotting, audit events and compatibility with the existing R3 `KodeModelRouter`/`ModelRegistry` abstractions.

The registry never treats an Ollama tag as an immutable identity. A runtime reference must resolve to the artifact digest bound by the accepted registry record before promotion. Promotion is authorized only for `PROMOTE_TO_EXPORT`; a post-promotion health failure restores the exact prior persisted mapping.

Manual intervention: NONE.

## Technical-source evidence

- normalized START: `d0225f4086c8ad1328fe6450a85e92fcc62644a6`
- immutable technical source: `d6e3aef8224cb45a329b76077d1dd39a9adda0c3`
- R15.14 acceptance: `33332947813` — SUCCESS on Ubuntu and Windows
- focused tests: immutable identity, fail-closed disposition/role eligibility, atomic promotion, restart persistence, health rollback, exact rollback, mutable-tag digest binding, tamper rejection and R3 `KodeModelRouter` compatibility
- static/schema gates: Ruff, compileall and Draft 2020-12 schema validation PASS
- manual state: `NONE`

The technical run is evidence for the immutable source only. The final documentary END-head created by this synchronization must receive fresh R15.14 + R0 + Python Core + KodeStudio UI Smoke evidence before PR #324 may merge.
