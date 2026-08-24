# R12.3 — Acceptance

## Scope

Deterministic desktop scaffold/template/workspace manifest engine only.

Manual intervention: **NONE**.

## Required acceptance

- repository-owned versioned template manifest validates against its strict schema;
- identical template + typed values + DNA/Product lineage render identical ordered files and workspace manifest digest;
- generated text uses deterministic LF endings;
- traversal, symlink escape, reserved path, rendered collision and malformed directive attacks fail closed;
- identifier/namespace/type/directive substitution attacks fail closed;
- preview produces no source file side effects;
- user-owned files are preserved;
- unowned or modified generated files are conflicts, not overwrite candidates;
- regeneration replacement requires verified previous SHA ownership plus SafeChange snapshot and verified Backup archive;
- AuditLog remains tamper-verifiable after governed apply;
- workspace manifest binds Project DNA, KodeProduct, template and generated file SHA-256 lineage;
- full repository R0 Repository Guard + Python Core + KodeStudio UI Smoke succeed on one exact head.

## Evidence state

Implementation branch: `r12/3-desktop-scaffold-engine`.
Base normalized `main`: `6a58719522b46b0f89b9514dbeff6cb5ca0bdb6c`.

Exact implementation/final-documentation SHA and GitHub Actions run IDs are intentionally **PENDING** until an immutable candidate is created and independently gated. No PASS report is manufactured before those gates.

## Merge / normalization rule

After the final documentation head is accepted, merge its PR with `expected_head_sha`, then create exactly one continuity-only post-merge normalization from that merge. R12.4 remains forbidden until the normalization exact-head R0/full Python/UI triplet succeeds and the normalization merges.
