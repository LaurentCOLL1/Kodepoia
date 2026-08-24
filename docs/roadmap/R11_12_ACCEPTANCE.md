# R11.12 — Acceptance

Status: **IMPLEMENTED — FINAL DOCUMENTATION HEAD GATES PENDING**  
Manual intervention: **CONDITIONAL — NOT TRIGGERED**

## Base and scope

- Base normalized `main`: `7fa6d1294d10a9b0e602b412db644cf68fb66ede`.
- Branch: `r11/12-savebridge-migrations`.
- Scope: SaveBridge document/checksum, compatibility states, trusted migration registry, deterministic bounded paths, dry-run, durable SafeChange+Backup+Recovery+Audit migration, corruption/tamper/newer-version handling and exact rollback.

## Acceptance criteria

- Canonical save checksum detects tamper/truncation/unknown fields.
- Namespaced extensions are bounded and preserved.
- Synthetic v1→v2→v3 migrations are deterministic and idempotent.
- Migration graph cycles and missing/unbounded paths fail closed.
- `UNSUPPORTED_NEWER` never performs destructive downgrade by default.
- Save migration cannot rewrite project/franchise/Canon snapshot identity.
- Dry-run does not modify bytes.
- Durable migration creates a verified backup and SafeChange snapshot, updates atomically, verifies output and audits success.
- Injected post-write failure restores the exact prior bytes and leaves explicit recovery/audit evidence.
- JSON Schema Draft 2020-12 validates canonical fixtures offline.

## Accepted implementation head

Exact candidate: `66ccd03bf486ac325ee2fba7133a6fc2a9c244b0`.

- R0 Repository Guard #1442 / `32762000034`: **SUCCESS**.
- Python Core #1416 / `32762000036`: **SUCCESS**.
- KodeStudio UI Smoke #1383 / `32762000071`: **SUCCESS**.
- Ubuntu and Windows Python Core: **SUCCESS**.
- Ubuntu and Windows package builds: **SUCCESS**.
- Internal KodeStudio UI job: **SUCCESS**.
- Prior R7/R8/R9 integrated acceptance checks: **PASS** where executed.

## Conditional manual gate

**NOT TRIGGERED.** This work claims compatibility only with synthetic SaveBridge/accepted R5 contract fixtures. It does **not** claim compatibility with a concrete existing user Godot project/save format. Therefore the frozen R11.12 conditional disposable-project collector is not required.

If a later change adds such a real-format claim, the conditional gate must be frozen and satisfied before merge; the sole copy of a real save must never be used.

## Finalization

This update changes acceptance documentation only. Its resulting exact head must pass R0 Repository Guard + full Python Core + KodeStudio UI Smoke before PR #179 can merge with `expected_head_sha`.

After merge, exactly one continuity-only post-merge normalization must pass the same gates and merge. Only that normalization authorizes R11.13.
