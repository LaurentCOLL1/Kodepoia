# R7.11 — Adversarial hardening + R7 integrated acceptance — Acceptance

**Status: IN PROGRESS — R7 MUST NOT be marked COMPLETE before post-merge integrated normalization passes.**

## Scope

This acceptance covers the frozen final R7 subdivision only: cross-source adversarial/security regressions, integrated acceptance contracts/schema, repository evidence validator, final quality/security/BOM review and phase-closing evidence preparation.

## Frozen invariants under test

- Hostile local/official/Web/GitHub/Community/YouTube text remains guarded/untrusted data and cannot become tool instructions or permission authority.
- SSRF defenses reject unsafe schemes/credential targets/private, loopback and link-local addresses, mixed safe/unsafe DNS answers and unsafe redirect targets before a dangerous request.
- Existing pinned-IP Web transport remains the DNS-rebinding boundary; R7.11 does not weaken it or add a second transport.
- Research-local path traversal, absolute paths and supported symlink escapes fail closed through `WorkspaceBoundary`.
- Interactive Research fetch exposes typed research selectors, not arbitrary command/argv/cwd/env/executable/method/header/body controls.
- Web remains BLOCKED without explicit NETWORK capability and Guardian authorization.
- Secret/token-shaped values do not survive serialized/exported research evidence after KodeSecrets/research redaction.
- Cancellation occurs before persistence/READY promotion; cancelled work cannot become successful cached evidence.
- Contradictory version claims remain visible even with explicit supersession; ranking preserves all claims and does not use popularity/source count as authority.
- Missing/unconfigured specialized providers remain explicit UNKNOWN rather than silent READY.
- `R7IntegrationReport` contains exactly R7.1–R7.11 with canonical source path, SHA-256, byte length, accepted head and explicit manual state.
- Stored `manual_satisfied` and report evidence digest are derived/recalculated and tampering fails closed.
- Repository validation reloads canonical bytes, recalculates SHA-256/length, verifies accepted head presence/manual PASS state and requires R7.11 head == report source SHA.
- The domain validator receives an injected blob reader and does not obtain a shell/process/network surface.
- `R7_INTEGRATED_ACCEPTANCE.json` is created only in post-merge normalization after the exact accepted R7.11 implementation head exists, mirroring the accepted R6 self-reference solution.
- R7.7 REQUIRED manual evidence remains satisfied and mandatory for final phase PASS.
- R7.11 manual = CONDITIONAL; deterministic evidence is expected to satisfy the frozen contract without a live probe, in which case the final state is CONDITIONAL NOT TRIGGERED.

## Deliverables

- `src/kodepoia/intelligence/research/acceptance.py`
- `schemas/r7-integration-report-v1.schema.json`
- `tests/test_r7_11_adversarial.py`
- `tests/test_r7_11_integration.py`
- `docs/roadmap/R7_11_DESIGN.md`
- `docs/roadmap/R7_11_SECURITY_REVIEW.md`
- this acceptance document
- post-merge normalization deliverable: `docs/roadmap/R7_INTEGRATED_ACCEPTANCE.json`

## Quality / security / BOM review

`docs/roadmap/R7_11_SECURITY_REVIEW.md` records the final review. R7.11 adds no Python dependency and does not modify `pyproject.toml`; accepted R7.7 FFmpeg/whisper.cpp/model hashes remain unchanged. The authoritative Python suite re-runs R6 Health/Regression/TechnicalDebt/AppSecurity/Privacy/License/BOM and R6.12 repository integration.

## Hosted implementation acceptance

Required exact-head workflows:

- R0 Repository Guard — **PENDING**
- Python Core (all required jobs) — **PENDING**
- KodeStudio UI Smoke — **PENDING**

Authoritative run IDs/test counts and the accepted R7.11 head will be written only after the exact final implementation candidate is green.

## Manual intervention

**CONDITIONAL — currently NOT TRIGGERED for the implementation candidate.**

A live provider probe becomes mandatory only if a frozen R7.11 requirement cannot be established by deterministic hosted evidence. Any trigger must be documented before execution; silence never satisfies it.

## Phase completion rule

A green R7.11 implementation PR is necessary but not sufficient to mark R7 COMPLETE. After that merge, a separate normalization must finalize this document with the accepted implementation head, create `R7_INTEGRATED_ACCEPTANCE.json` bound to canonical acceptance-document blobs, pass the checked-in repository validator plus exact-head R0/Python/UI gates, synchronize status/continuity and merge. Only then may R7 become COMPLETE.
