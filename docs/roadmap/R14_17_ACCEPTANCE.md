# R14.17 — Adversarial integrated backend/platform-services/LiveOps acceptance

**Status:** ACCEPTED / END RE-GATES PENDING
**Immutable technical source:** `11fb0e1a28fd5cbb607e2b302a36314f151ee170`
**Exact normalized base:** `f6960db290a570e3a0c3c4ff97600014978d45df`
**Manual state:** `CONDITIONAL / NOT TRIGGERED`

## Accepted technical authority

R14.17 closes the frozen R14 service surface with one anti-circular integrated acceptance model. The final report does not consume its own bytes or its own PASS state. Instead, independent exact-source workflow identities and artifact digests are bound first; repository files are then byte-hashed and re-read by the offline verifier. Mixed source SHAs, tampering, prior-phase semantic drift, provider-live fabrication, sensitive-data exposure and synthetic production-publication claims fail closed.

Rejected candidates `f25cb89f1b54d325ecab6d12c08ec1e9129c1025` and `152f34d217f159d65b10d811d8770ea840b8e05b` are permanently non-authoritative. Temporary END-sync/helper commits `4e7f5d17e5e8356b7e6b1d3bc9331b73aefe496f`, `f509b7c683776e180f56129e5cb43eb0c65b8916`, and `6b3dcd15ca27979f55688b0b535eed1417b95dc2` are staging-only and cannot be reused as decision evidence. The accepted source `11fb0e1a28fd5cbb607e2b302a36314f151ee170` fixes the nested R14.16 workspace-bound output contract without weakening that boundary.

## Exact-source gates

- R0 Repository Guard #2028 / run `33265386264`: SUCCESS.
- Python Core #2003 / run `33265386254`: SUCCESS 5/5; Ubuntu **1760 passed / 14 skipped / 46 warnings**; Windows Core SUCCESS; Ubuntu/Windows package builds SUCCESS; UI-in-core SUCCESS.
- KodeStudio UI Smoke #1968 / run `33265386267`: SUCCESS.
- R14 Integrated Acceptance #5 / run `33265386261`: SUCCESS on Ubuntu 24.04 + PostgreSQL 18 and Windows 2025.

## Integrated scenario evidence

All 14 top-level integrated checks PASS. The twelve reused service acceptances contribute 222 deterministic checks, all PASS on the exact accepted source. The scenario covers governed local/test auth, PostgreSQL transactional authority, authoritative command/state/event boundaries, lobby/reservation/reconnect, cloud-save conflict/rollback, progression, duplicate/out-of-order entitlement processing, feature rollout/rollback, immutable content/cache/rollback, event dedupe/checkpoint/replay/redaction, LiveOps lifecycle, resilience/backup/restore/bounded-load evidence and governed CLI/KodeStudio UX.

Exact-source scenario artifact: ID `9718490610`; archive digest `sha256:8ef3c8fd15ab88919918ff9819784e5ed8558d08951bf2e9dc464d7bac9c8bac`. Checked scenario evidence is 6313 bytes with SHA-256 `8080d974bec375e822fb04d271671d922460e4d71e5996ce5a2d61377d4b8d47`.

## Anti-circular CI and canonical report

`R14_17_CI_ACCEPTANCE.json` binds only independent successful gate/run identities plus the integrated scenario artifact. Its semantic digest is `f8e1ea8d274aafc44009bb76c2c2e21e5306673510cc61c47d96de34b9f20a08`.

`R14_INTEGRATED_ACCEPTANCE.json` binds exact bytes for the accepted R13 integrated report, R14.1–R14.16 acceptance documents, the R14.17 design, scenario evidence and CI authority. It excludes itself from its input set. Its canonical semantic evidence digest is `06dbdc830b20fd4b2966b11cbacfd4b010f93101b071d827766c8b9cbfd45189`, with `status=pass` and `blockers=[]`.

## Provider/security boundary

Core closure is local/hosted/sandbox evidence only. `provider_live_claim=false`, `secrets_exposed=false`, `pii_exposed=false`, `production_publish_claim=false`, `internet_scale_claim=false`, and `multi_region_claim=false`. Missing real provider/account/domain/TLS/quota state is not promoted to PASS. No password, token, private key, production DSN or destructive/high-cost production action was required.

## END acceptance rule

The clean END tree contains no temporary report-emission or END-sync helper workflow/script. This acceptance document, the R14 phase plan and continuity change evidence bytes, so the resulting exact END-head must receive fresh R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R14 Integrated Acceptance. Only after all are SUCCESS may the implementation/evidence PR merge with exact `expected_head_sha`. Exactly one post-merge continuity-only normalization must then receive fresh R0/Python/UI before R14 becomes `COMPLETE + NORMALIZED` and R15 planning is authorized.
