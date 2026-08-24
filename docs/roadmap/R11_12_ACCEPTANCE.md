# R11.12 — Acceptance

Status: **IMPLEMENTED — HOSTED EXACT-HEAD GATES PENDING**  
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
- Full R0 Repository Guard, Python Core and KodeStudio UI Smoke must pass on one exact candidate head, followed by final-doc re-gate before merge.

## Conditional manual gate

**NOT TRIGGERED.** This work claims compatibility only with synthetic SaveBridge/accepted R5 contract fixtures. It does **not** claim compatibility with a concrete existing user Godot project/save format. Therefore the frozen R11.12 conditional disposable-project collector is not required.

If a later change adds such a real-format claim, the conditional gate must be frozen and satisfied before merge; the sole copy of a real save must never be used.

## Completion ordering

Accepted candidate -> acceptance run IDs -> re-gate final docs -> expected-SHA merge -> exactly one continuity-only normalization -> exact-head gates -> merge normalization -> only then R11.13.
