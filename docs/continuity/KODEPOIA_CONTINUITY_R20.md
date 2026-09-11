# KODEPOIA CONTINUITY — R20

**Status:** R20 COMPLETE + NORMALIZED; R20.1 THROUGH R20.6 COMPLETE + NORMALIZED; R20.7 NOT AUTHORIZED

This file is the terminal continuation authority for **R20 — Continuous Trusted Update Operations**. R20 planning and R20.1 through R20.6 are complete and normalized. R20.6 was the terminal authorized subdivision, implemented on dedicated branch `r20/06-long-offline-continuous-operations` from exact normalized `main` `ca1f1415dbad47f46f1a4714b2da225cfd4e9e51`, accepted at exact HEAD `861e5d9aae67df96bff2f382c84f94ebffa172c1`, and merged through PR #434 as `main` `be4f9227331ba7a21dd591ec528ec8d9b3369029`.

The detailed pre-R20.6 narrative remains frozen in Git history at the normalized R20.5 parent. This compacted terminal authority preserves every execution-critical head, PR, trust identifier, security invariant and manual boundary needed to understand the completed R20 phase without recursively rewriting prior normalized history.

The unique documentation-only branch `r20/06-continuity-normalization` jointly finalizes this file and `docs/roadmap/R20_PLAN.md`. Its merge closes R20 terminally. No second normalization may be created merely to record that normalization's own resulting head or merge SHA recursively.

R19 remains **COMPLETE + NORMALIZED** and frozen. No `R19.6` is authorized.

## Frozen inherited authority

- Repository: `LaurentCOLL1/Kodepoia`.
- Normalized R19 base: `main` `a5cb56fdf5993be3222b486fa80748f5aa339b71`.
- R19 terminal continuity: `docs/continuity/KODEPOIA_CONTINUITY_R19.md`.
- Public prerelease authority: `v1.1.0-rc2`.
- Accepted release source: `18ee16173d12f34a3508ccc0ad1a9ce38e9ecd3e`.
- Accepted installer SHA-256: `a753ecef07757c3a8d6f97db4db7c77bece9d8129bdd0887eb7dea71d805ff8c`.
- Accepted installer length: `37613254` bytes.
- Historical predecessor Root v1 SHA-256: `892442754966aa643bbe15a2910aa3fef59032c8f5eade34fed62efd96aefee5`.
- Current production Root is **v2**, SHA-256 `c92b2165bcbf39f74599fbdf8cc30e203f8c93cc2f24c5c74012821646850ee7`, threshold 2-of-3, expiry `2027-09-08T14:59:19Z`.
- Targets remains exact **v2**, SHA-256 `0b65bf34e50d43ed1f82f0f4a17875fb0a4bb597ed5b6066749dc9352e504e3f`, length `1001`, expiry `2027-09-08T17:32:00Z`.
- Current production Snapshot is **v4**, SHA-256 `1fccbcc5721acf59188761a79b70d829fa1ae23e77e505d1c1e9867c110eced9`, replacement keyid `fac1c790b4d6dbeb04ca4a803bd80e6fde19127fc7ada34003cef5d6b50506d8`.
- Current production Timestamp is **v4**, SHA-256 `74c815dc414ae946aba1f7c427ae044dbaa3a5e1fb15bbdb436e33881fc6e501`, distinct replacement keyid `8d81006fd9de63660d74c43b6926ed664b2e9f1bdf81a9556367232533d5a2ad`.
- Snapshot v4 and Timestamp v4 retain transition expiry `2026-10-08T21:44:18Z`; R20.4 did not manufacture an unnecessary production refresh while sufficient lifetime remained.
- Snapshot v4 binds exact Targets v2 bytes/version/hash/length; Timestamp v4 binds exact signed Snapshot v4 bytes/version/hash/length.
- Root/Targets private custody remains outside Git/repository/CI.
- The two low-authority online Ed25519 seeds exist only as distinct GitHub environment secrets in `tuf-production-signing` and in retained local custody; their values are never repository authority.
- Kodepoia rejects expired trusted metadata and maps update-service failure to a non-destructive, retryable state while application startup/local work remain available.

## R20 objective and steady-state trust model

Users must be able to return to Kodepoia after a long period and update directly inside the application without being exposed to TUF metadata-expiry maintenance. TUF freshness remains enforced; automation, not client-side bypass, keeps online metadata fresh.

Mandatory Kodepoia creation, maintenance, distribution and user operation remains **0 €**. Paid cloud/KMS/HSM services are optional hardening backends only.

Steady-state authority:

- Root: offline, threshold-protected;
- Targets: offline, release authorization only;
- Snapshot: dedicated low-authority online Ed25519 key;
- Timestamp: separate low-authority online Ed25519 key;
- online keys: distinct GitHub Actions environment secrets consumed only by ephemeral GitHub-hosted runners;
- scheduled online metadata renewal before expiry;
- no Root/Targets private material in routine Actions;
- no paid infrastructure requirement in the mandatory path.

## Authorized subdivision sequence

1. R20.1 — Bridge Metadata Refresh & Custody-Safe Tooling
2. R20.2 — Online Signer Abstraction & Rotation Package
3. R20.3 — Zero-Cost Online-Key Provisioning & Root Rotation
4. R20.4 — Scheduled Metadata Refresh & Atomic Publication
5. R20.5 — Expiry Monitoring, Alerting & Client UX Hardening
6. R20.6 — Long-Offline Client & Continuous-Operations Integrated Acceptance

No subdivision may be silently inserted, removed, merged, split or renumbered. **No `R20.7` is authorized.**

## R20 planning — COMPLETE + NORMALIZED

- Planning branch: `r20/planning`.
- Accepted exact planning HEAD: `45c442533211c6efba1ea5fddcf49f7814a12c9f`.
- Planning PR #420 merged as `main` `274831790f7ebbcce8d470569a651cb6b9a10211`.
- Unique planning normalization produced `main` `725a44756ab27ed29f84e7fcf238477fd2997d8a`, sole authorized R20.1 base.
- Manual intervention: **NONE**.

## R20.1 — Bridge Metadata Refresh & Custody-Safe Tooling — COMPLETE + NORMALIZED

- Implementation branch: `r20/01-bridge-metadata-refresh`.
- Authorized base: `725a44756ab27ed29f84e7fcf238477fd2997d8a`.
- Accepted exact HEAD: `878b2f81d1893b63bef4d7980a6bcb19101530eb`.
- PR #422 merged as `main` `324ad91f47eff8a69166b78e16c11b49251ceb0d`.
- Unique normalization produced `main` `53f431f50361d7fa0e3b31ac0c2a2596326c9f85`, sole authorized R20.2 base.
- Root v1 and Targets v2 were preserved byte-for-byte; bridge Snapshot/Timestamp advanced to v3/v3 and were hash/version/length bound.
- Manual intervention: **COMPLETE** — local Snapshot/Timestamp bridge signing was performed and only public signed metadata returned.

## R20.2 — Online Signer Abstraction & Rotation Package — COMPLETE + NORMALIZED

- Implementation branch: `r20/02-online-signer-rotation`.
- Authorized base: `53f431f50361d7fa0e3b31ac0c2a2596326c9f85`.
- Accepted exact HEAD: `9ab039519e434b24fff1c45dfeed2aa2fef4920f`.
- PR #424 merged as `main` `2d94afc22be01871caad9d99fdca090e3743a786`.
- Normalization PR #425 merged exact head `8ba7fbcf49836094dab9e7a78fdb9cba8db16332` as `main` `02ae599f951f353d9647e5cb6ca39f28eb655cbf`, sole authorized R20.3 base.
- Provider-neutral online signer configuration, public identity validation, synthetic CI signers and public-only Root N+1 rotation packages are accepted.
- Manual intervention: **NONE**.

## R20.3 — Zero-Cost Online-Key Provisioning & Root Rotation — COMPLETE + NORMALIZED

- Implementation branch: `r20/03-zero-cost-architecture`.
- Authorized base: `02ae599f951f353d9647e5cb6ca39f28eb655cbf`.
- Accepted implementation HEAD: `747405e133fb2934e377a0312b59a9d468e4af19`.
- Implementation PR #426 merged as `main` `a0650cba7ad0faf95e16f3059baa2e422f79648a`.
- Corrective PR #427 merged exact head `6ff80d9d4560b31c7ef9f4e094c029f66b63917e` as `main` `f4e537b62e5aef7f84131ee3fddf17ca04e603e4`.
- Final corrective PR #428 merged exact head `8ebb87e0357c3fd1e9b2f1709780112847938ee8` as `main` `35f3cad975877f0a7e2416afb180a0160511add2`.
- Public online-key package SHA-256: `4b26dbf702f93e1c2e6f813eae7c22771a06e97fd9d77bd6d57bff1b6c22b1db`.
- Full public transition ZIP SHA-256: `7ee54d08d0dc11ce275705c877a0615b69bedd15a18747393ef7e1dbee58651e`.
- Transition manifest SHA-256: `bfd8ca6c1386911f6504410e42a4ef0b9e8243b13d5670a84738f572237e7d50`.
- Root v2 old-threshold and new-self-threshold verification: **PASS**.
- Snapshot v4 / Timestamp v4 signature verification: **PASS**.
- Targets bytes unchanged: **TRUE**; private material detected: **FALSE**; paid provider required: **FALSE**.
- R20.3 Live Zero-Cost Signer Challenge run `34507387616` on `main` `35f3cad975877f0a7e2416afb180a0160511add2`: **SUCCESS**, no publication and no secret emission.
- Unique R20.3 normalization produced `main` `18593924711c135740bcdf6ca2ca757e18f1194c`, sole authorized R20.4 base.
- Manual intervention: **COMPLETE** — online secret provisioning, offline Root v2 threshold ceremony and no-publication live signer challenge completed.

## R20.4 — Scheduled Metadata Refresh & Atomic Publication — COMPLETE + NORMALIZED

- Implementation branch: `r20/04-scheduled-metadata-refresh`.
- Authorized base: `18593924711c135740bcdf6ca2ca757e18f1194c`.
- Accepted exact HEAD: `391ffc27c7a360a8ebb2f4f4483128ca67b52f99`.
- PR #430 merged as `main` `3099561a38a7df6abf7e90fc8cd29ac035147cc2`.
- Unique normalization branch `r20/04-continuity-normalization`, exact head `b65eeec42d30b72a46022652caff8d1343bc07d4`, PR #431 → normalized `main` `fa8460a7681554e2e9cd47adc591e2fed5af0956`.
- Scheduled check: every 6 hours; refresh threshold: 24 hours; Snapshot target lifetime: 72 hours; Timestamp target lifetime: 48 hours.
- Protected publication uses isolated PR, exact-main revalidation, R0 required checks and expected-head merge; Root/Targets and release assets are unchanged.
- Existing R20.3 low-authority online secrets are reused; no Root/Targets private material is needed.
- Manual intervention: **NONE / COMPLETE + NORMALIZED**.

## R20.5 — Expiry Monitoring, Alerting & Client UX Hardening — COMPLETE + NORMALIZED

- Implementation branch: `r20/05-expiry-monitoring-ux-hardening`.
- Authorized base: `fa8460a7681554e2e9cd47adc591e2fed5af0956`.
- Accepted exact implementation HEAD: `bbf30a86eb9a2f332c3805ed19f36327b355e32a`.
- Implementation PR #432 merged with expected-head protection as `main` `94b787b11e1010c9ad6cfa77bd96360e49e0fb8e`.
- Accepted push evidence: R20.5 Acceptance #10, R0 #2740, Python Core #2711 and UI Smoke #2675 all successful on required platforms.
- Accepted PR evidence: R20.5 Acceptance #11, R0 #2741, UI Smoke #2676, R16.9 #297 and dedicated R16.12 #268 successful. Generic PR-level Python Core #2712 had one inherited Windows `dotnet_probe_failed` toolchain variance while 2359 tests passed; unchanged SHA had already passed Python Core Windows and dedicated R16.12 with explicit accepted .NET SDK.
- Unique normalization branch `r20/05-continuity-normalization` exact head `9ec92ac1a667e2e06da757e5cb45f0d79a571a08`, PR #433, merged as normalized `main` `ca1f1415dbad47f46f1a4714b2da225cfd4e9e51`.
- R20.5 monitor is read-only, secret-free and scheduled every six hours at minute 47; Root/Targets warnings/critical are 90/30 days and Snapshot/Timestamp 36/24 hours; R20.4 run health warns after 9h and is critical after 18h or two completed failures.
- Expired/inconsistent/unverifiable metadata remains fail-closed; localized EN/FR service-unavailable UX never blocks startup or local work.
- R20.5 workflows are registered under immutable R16.9 authority.
- Manual intervention: **NONE / COMPLETE + NORMALIZED**.

## R20.6 — Long-Offline Client & Continuous-Operations Integrated Acceptance — COMPLETE + NORMALIZED

Implementation branch: `r20/06-long-offline-continuous-operations`.

Authorized base: normalized R20.5 `main` `ca1f1415dbad47f46f1a4714b2da225cfd4e9e51`.

Accepted exact implementation HEAD: `861e5d9aae67df96bff2f382c84f94ebffa172c1`.

Implementation PR #434 merged that exact head with expected-head protection as `main` `be4f9227331ba7a21dd591ec528ec8d9b3369029`.

Objective: prove that a client returning after a long offline period can safely obtain current authorized metadata and update without weakening freshness, while exercising continuous-operations recovery and preserving user data/local work.

### Accepted 17-case terminal matrix

The deterministic exact-source acceptance verifies:

1. persisted trusted client state after a simulated multi-month offline period;
2. fresh Timestamp/Snapshot/Targets acceptance and current candidate discovery on return;
3. installation age is not a trust input;
4. expired server metadata rejection;
5. old correctly signed Timestamp replay rejection after newer trusted state;
6. Snapshot/Targets mix-and-match rejection;
7. GitHub Actions/signing outage maps to retryable update-service failure without blocking startup/local work;
8. scheduled refresh fails closed without signers and recovers when authorized online signers return;
9. serialized publication plus trusted-state rollback checks prevent version regression;
10. compromised Timestamp authority alone cannot authorize new Targets;
11. compromised Snapshot authority alone cannot authorize arbitrary target bytes;
12. Root/Targets offline private authority remains absent from routine Actions/runtime contracts;
13. one online role can rotate while Targets authorization and target bytes remain unchanged;
14. emergency manual refresh runbook is exercised against the deterministic outage/recovery path;
15. EN/FR update UX remains localized and non-destructive;
16. user settings and project data survive the verified update handoff, while accepted R19.5 real-Windows rc1→rc2 replay remains inherited live evidence;
17. the complete mandatory path remains zero-cost and requires no paid infrastructure.

### R20.6 repository artifacts

- `src/kodepoia/update/continuous_operations.py` — integrated deterministic acceptance model;
- `scripts/r20_6_continuous_operations_acceptance.py` — exact-source JSON evidence emitter;
- `tests/test_r20_6_continuous_operations.py` — terminal matrix/non-production regressions;
- `.github/workflows/r20-6-continuous-operations-acceptance.yml` — Ubuntu/Windows exact-head gate;
- `docs/release/R20_6_CONTINUOUS_OPERATIONS_ACCEPTANCE.md` — terminal acceptance and security interpretation;
- `configs/r16_supply_chain_policy.json` + `tests/test_supply_chain_r16_9.py` — R20.6 workflow registered as immutable authority, raising authority count from 45 to 46.

The R20.6 acceptance is synthetic and repository-safe: `production_effect=false`, no production private key consumption, no production metadata publication, no public release creation and no live role rotation. The roadmap's live incident/key-rotation drill was conditional only; the deterministic 17-case matrix covers the required boundaries without privileged production mutation.

### Accepted exact-head evidence

Push evidence on accepted HEAD `861e5d9aae67df96bff2f382c84f94ebffa172c1`:

- R20.6 Long-Offline Continuous Operations Acceptance #9: **SUCCESS** on Ubuntu and Windows, including the full 17/17 matrix;
- R0 Repository Guard #2760: **SUCCESS** on Ubuntu and Windows;
- Python Core #2731: **SUCCESS** for Python Core Ubuntu/Windows, package-build Ubuntu/Windows and integrated KodeStudio UI Windows;
- KodeStudio UI Smoke #2695: **SUCCESS**.

PR #434 evidence on the same unchanged HEAD:

- R20.6 Long-Offline Continuous Operations Acceptance #10: **SUCCESS** on Ubuntu and Windows;
- R0 Repository Guard #2761: **SUCCESS** on Ubuntu and Windows;
- R16.9 Supply Chain Provenance Acceptance #298: **SUCCESS** on Ubuntu and Windows, validating authority count 46;
- Python Core #2732: **SUCCESS** across Python Core Ubuntu/Windows, package-build Ubuntu/Windows and integrated KodeStudio UI Windows;
- KodeStudio UI Smoke #2696: **SUCCESS**.

The exact accepted implementation was therefore merged with expected-head protection as `main` `be4f9227331ba7a21dd591ec528ec8d9b3369029`.

The unique documentation-only branch `r20/06-continuity-normalization` jointly finalizes `docs/roadmap/R20_PLAN.md` and this continuity authority. Its merge is the terminal R20 normalization. No second normalization may be created merely to embed its own final head or merge SHA recursively.

Manual intervention for R20.6: **NONE / COMPLETE + NORMALIZED**. No new secret provisioning, Root/Targets ceremony or live production mutation is required by the accepted design.

## R20 security invariants

- Never disable metadata expiry checks.
- Never accept expired metadata as an availability fallback.
- Never require a paid service in the mandatory Kodepoia path.
- Never store Root/Targets private keys in CI or routine online signers.
- Never reuse one online private key for Snapshot and Timestamp.
- Never expose TUF passphrases, local vault material or online secret values in Git, Actions logs/artifacts, issues or continuity.
- Online signer compromise must not authorize new Targets or Root metadata.
- Metadata versions are monotonic.
- Snapshot references exact Targets bytes/version/hash/length.
- Timestamp references exact signed Snapshot bytes/version/hash/length.
- Publication must not expose a mixed metadata generation.
- GitHub Actions/signing-backend failure never gates Kodepoia startup or local work.
- All R20 implementation merges require exact-head evidence and expected-head protection.
- Every completed subdivision gets exactly one post-merge continuity normalization.

## Manual boundaries

R20 planning: **NONE / COMPLETE + NORMALIZED**.

R20.1: **COMPLETE + NORMALIZED** — local bridge signing was performed; public metadata only was returned.

R20.2: **NONE / COMPLETE + NORMALIZED**.

R20.3: **COMPLETE + NORMALIZED** — public online-key generation, GitHub environment-secret provisioning, offline Root v2 threshold ceremony, atomic v4/v4 transition and live no-publication signer challenge passed.

R20.4: **NONE / COMPLETE + NORMALIZED** — steady-state automation and protected publication accepted.

R20.5: **NONE / COMPLETE + NORMALIZED** — monitoring, alerting, localized UX hardening and emergency runbook accepted.

R20.6: **NONE / COMPLETE + NORMALIZED** — deterministic terminal acceptance uses synthetic signing/trust state plus inherited public evidence; no privileged live drill is required.

## Terminal rule

R20 is **COMPLETE + NORMALIZED** after the unique joint R20.6 documentation normalization merges. **No `R20.7` is authorized.** Do not create a second R20 normalization merely to record the terminal normalization's own resulting head or merge SHA.