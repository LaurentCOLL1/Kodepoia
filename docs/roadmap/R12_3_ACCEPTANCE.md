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

## Accepted implementation candidate

Implementation branch: `r12/3-desktop-scaffold-engine`.
Base normalized `main`: `6a58719522b46b0f89b9514dbeff6cb5ca0bdb6c`.
Accepted implementation head: `bf4c5b095bc7b91ecf7c27100c3da81c0a13ce31`.

- R0 Repository Guard #1478 / `32778299021` — **SUCCESS**.
- Python Core #1452 / `32778298974` — **SUCCESS**, including Ubuntu/Windows pytest, package builds and internal KodeStudio smoke.
- KodeStudio UI Smoke #1419 / `32778299000` — **SUCCESS**.
- Manual state: **NONE**.

This evidence update changes bytes after the independently accepted implementation candidate. The resulting final documentation head must therefore pass a fresh exact-head R0 + full Python Core + KodeStudio UI Smoke triplet before merge. No synthetic PASS report is created.

## Merge / normalization rule

After the final documentation head is accepted, merge PR #191 with `expected_head_sha`, then create exactly one continuity-only post-merge normalization from that merge. R12.4 remains forbidden until the normalization exact-head R0/full Python/UI triplet succeeds and the normalization merges.
