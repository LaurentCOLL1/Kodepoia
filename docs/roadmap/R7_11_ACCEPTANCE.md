# R7.11 — Adversarial hardening + R7 integrated acceptance — Acceptance

**Status: COMPLETE — implementation accepted; R7 phase closure still requires this normalization to pass and merge.**

## Accepted implementation

- Accepted head: `52330ca576fe294956a8fb601bdfda1d72dc3f92`
- PR: #80
- Merge commit: `1cdf5b90cc6c3e829c13e63f753f47fb067ef14e`
- Manual intervention: **CONDITIONAL NOT TRIGGERED**

## Scope

This acceptance covers the frozen final R7 subdivision only: cross-source adversarial/security regressions, integrated acceptance contracts/schema, repository evidence validator, final quality/security/BOM review and phase-closing evidence preparation.

## Accepted invariants

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
- R7.7 REQUIRED manual evidence remains satisfied and mandatory for final phase PASS.
- Deterministic hosted evidence established every frozen R7.11 behavior, so no live-provider probe was required; the CONDITIONAL gate is explicitly NOT TRIGGERED.

## Deliverables

- `src/kodepoia/intelligence/research/acceptance.py`
- `schemas/r7-integration-report-v1.schema.json`
- `tests/test_r7_11_adversarial.py`
- `tests/test_r7_11_integration.py`
- `docs/roadmap/R7_11_DESIGN.md`
- `docs/roadmap/R7_11_SECURITY_REVIEW.md`
- this acceptance document
- normalization deliverable: `docs/roadmap/R7_INTEGRATED_ACCEPTANCE.json`

## Quality / security / BOM review

`docs/roadmap/R7_11_SECURITY_REVIEW.md` records the final review. R7.11 adds no Python dependency and does not modify `pyproject.toml`; accepted R7.7 FFmpeg/whisper.cpp/model hashes remain unchanged. The authoritative Python suite re-ran the existing R6 Health/Regression/TechnicalDebt/AppSecurity/Privacy/License/BOM and R6.12 repository-integration coverage.

## Exact-head hosted implementation acceptance

All required workflows succeeded on accepted head `52330ca576fe294956a8fb601bdfda1d72dc3f92`:

- R0 Repository Guard — **#1030 / `32598775535` — SUCCESS**
- Python Core — **#1004 / `32598775562` — SUCCESS, 5/5 jobs**
- Authoritative Ubuntu suite — **514 passed / 6 skipped / 46 warnings**
- KodeStudio UI Smoke — **#971 / `32598775534` — SUCCESS**
- Embedded `kodestudio-ui-windows` job inside Python Core — **SUCCESS**

## Rejected implementation candidate retained as evidence

- `b35a6dcd330c7cc3cb582d775ce0275d7a9b2f87`: Python Core #1003 and UI Smoke #970 succeeded, but R0 #1029 correctly rejected a literal GitHub-token-shaped **test fixture** as a possible hard-coded secret. The fixture was changed to construct the fake token at runtime; the repository secret scanner was not weakened or bypassed. The new exact head then passed R0 #1030.

No failed candidate/run is reused as accepted evidence.

## Manual intervention

**CONDITIONAL NOT TRIGGERED.**

All frozen R7.11 provider/security behaviors are covered through deterministic typed fixtures and already accepted lower-layer provider contracts. No live account, credential or external-provider probe was needed. Silence is not being used as evidence; this decision is explicit.

## Phase completion rule

R7.11 implementation is accepted, but **R7 is not COMPLETE yet at this point in the document lifecycle**. This normalization must now create `R7_INTEGRATED_ACCEPTANCE.json` bound to the canonical bytes of R7.1–R7.11 acceptance documents, pass the checked-in repository validator plus exact-head R0/Python/UI gates, synchronize status/continuity, and merge to `main`. Only after that merge is R7 COMPLETE.
