# R20.6 Continuous Operations Integrated Acceptance

R20.6 is the terminal integrated acceptance for **R20 — Continuous Trusted Update Operations**. It verifies the long-offline user promise and the steady-state operational security contract without performing a production key rotation, publishing metadata, creating a release, or requiring a paid provider.

## Authority

- Authorized base: normalized R20.5 `main` `ca1f1415dbad47f46f1a4714b2da225cfd4e9e51`.
- Implementation branch: `r20/06-long-offline-continuous-operations`.
- Exact-head evidence is emitted by `scripts/r20_6_continuous_operations_acceptance.py` and validated on Ubuntu and Windows by `.github/workflows/r20-6-continuous-operations-acceptance.yml`.
- The acceptance is synthetic and repository-safe. It has **no privileged live drill**, no production signing key use and no production metadata effect.

## 17-case integrated matrix

The acceptance proves all of the following as one exact-source contract:

1. persisted trusted client state remains usable after a simulated multi-month offline period;
2. a returning client accepts fresh Timestamp/Snapshot/Targets and obtains the current authorized candidate;
3. trust decisions do not depend on installation age;
4. expired server metadata is rejected;
5. an old correctly signed Timestamp replay is rejected after newer trusted state;
6. Snapshot/Targets mix-and-match is rejected;
7. a GitHub Actions or signing outage maps to retryable update-service unavailability without blocking startup/local work;
8. a scheduled refresh that initially lacks online signers fails closed and then recovers when the authorized online signers return;
9. serialized publication plus trusted-state rollback checks prevent concurrent refreshes from regressing versions;
10. compromise of the Timestamp role alone cannot authorize new Targets;
11. compromise of the Snapshot role alone cannot authorize arbitrary target bytes;
12. Root/Targets private authority remains absent from routine Actions/runtime contracts;
13. one online role can rotate while Targets authorization and target bytes remain unchanged;
14. the emergency manual refresh runbook is exercised against the deterministic outage/recovery path;
15. English/French update-service UX remains localized, retryable and non-destructive;
16. user settings and project data survive the normal verified update handoff, with the historical R19.5 live installer replay retained as inherited real-Windows evidence;
17. the complete mandatory path remains **zero-cost** and requires no paid KMS/HSM infrastructure.

## Security interpretation

R20.6 does not weaken TUF freshness. Expired metadata, rollback, inconsistent Snapshot/Targets views and unauthorized target bytes all remain fail-closed. Snapshot and Timestamp online authority remains strictly below Root/Targets authority, and the terminal acceptance deliberately demonstrates that compromising either online role alone is insufficient to authorize arbitrary release bytes.

The R20.4 production workflow remains serialized and performs exact-main revalidation before protected publication. The R20.5 monitor remains read-only and has no signing secret or publication permission.

## User-data preservation

The deterministic R20.6 handoff drill creates sentinel user settings and project data, launches a verified local update handoff, reconciles the authorized version, and asserts both sentinels remain byte-for-byte unchanged. This supplements rather than replaces the accepted R19.5 Windows replay that installed rc1, updated to the pinned rc2 installer and verified that user settings and project data survived.

## Manual intervention

**NONE for R20.6 acceptance.** The roadmap allowed a privileged live incident/key-rotation drill only conditionally. The 17-case matrix proves the required rotation and incident boundaries synthetically with production effect explicitly disabled, so no new secret provisioning, Root/Targets ceremony or live production mutation is required.

If an actual production incident occurs later, operators must use `R20_5_UPDATE_OPERATIONS_RUNBOOK.md`; that operational procedure must never accept expired or unverifiable metadata for availability.

## Completion rule

R20.6 is not terminally complete until its unchanged exact accepted implementation HEAD merges with expected-head protection and exactly one documentation-only post-merge normalization jointly finalizes `docs/roadmap/R20_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY_R20.md`.

After that unique normalization, R20 is **COMPLETE + NORMALIZED**. No `R20.7` is authorized.
