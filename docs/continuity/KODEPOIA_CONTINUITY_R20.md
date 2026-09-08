# KODEPOIA CONTINUITY — R20

**Status:** R20 PLANNING MERGED; UNIQUE PLANNING NORMALIZATION IN PROGRESS

This file is the active continuation authority for **R20 — Continuous Trusted Update Operations**. Planning implementation is accepted and merged. The branch `r20/planning-continuity-normalization` is the single authorized post-planning continuity-only normalization. R20.1 is authorized only after this normalization passes fresh exact-head R0 Repository Guard, full Python Core and KodeStudio UI Smoke and merges with expected-head protection.

R19 remains **COMPLETE + NORMALIZED** and frozen. No `R19.6` is authorized.

## Frozen inherited authority

- Repository: `LaurentCOLL1/Kodepoia`.
- Normalized R19 base: `main` `a5cb56fdf5993be3222b486fa80748f5aa339b71`.
- R19 terminal continuity: `docs/continuity/KODEPOIA_CONTINUITY_R19.md`.
- Public prerelease authority: `v1.1.0-rc2`.
- Accepted release source: `18ee16173d12f34a3508ccc0ad1a9ce38e9ecd3e`.
- Accepted installer SHA-256: `a753ecef07757c3a8d6f97db4db7c77bece9d8129bdd0887eb7dea71d805ff8c`.
- Accepted installer length: `37613254` bytes.
- Production Root v1 SHA-256: `892442754966aa643bbe15a2910aa3fef59032c8f5eade34fed62efd96aefee5`.
- Root threshold: 2-of-3.
- Targets/Snapshot/Timestamp roles each have separate Ed25519 keys under Root v1.
- Private-key custody remains outside Git/repository/CI. Local recovery has been confirmed for all six current private-key files without disclosing or committing passphrases.
- Targets v2 authorizes only the accepted beta rc2 installer and expires `2027-09-08T17:32:00Z`.
- Snapshot v2 and Timestamp v2 both expire `2026-09-09T17:32:00Z`.
- Kodepoia rejects expired trusted metadata and maps that case to a non-destructive `metadata-expired` update-discovery state.

## R20 objective

Users must be able to return to Kodepoia after a long period and update directly inside the application without being exposed to metadata-expiry maintenance. TUF freshness protections remain enforced; operational automation, not client-side bypass, keeps metadata fresh.

Steady-state trust model:

- Root: offline, threshold-protected;
- Targets: offline, release authorization only;
- Snapshot: dedicated online non-exportable signer;
- Timestamp: separate dedicated online non-exportable signer;
- GitHub Actions: short-lived OIDC/federated cloud credentials only;
- scheduled metadata renewal before expiry;
- no long-lived cloud signing credential stored in GitHub Secrets;
- no user-visible update deadline created by metadata maintenance.

## External authority re-verified for planning

- TUF permits Snapshot and Timestamp online keys for continuous delivery and recommends keeping other top-level role keys offline.
- Timestamp is intentionally short-lived/frequently re-signed to detect freeze attacks.
- Snapshot and Timestamp should not share a key.
- GitHub Actions OIDC can exchange an Actions identity token for short-lived cloud credentials; the cloud trust policy must restrict repository/ref/environment claims.
- AWS KMS and Google Cloud KMS currently document Ed25519 asymmetric signing support and are viable R20.3 candidates; no provider is selected during planning.

## Authorized subdivision sequence

1. R20.1 — Bridge Metadata Refresh & Custody-Safe Tooling
2. R20.2 — Online Signer Abstraction & Rotation Package
3. R20.3 — OIDC/KMS Online-Key Provisioning & Root Rotation
4. R20.4 — Scheduled Metadata Refresh & Atomic Publication
5. R20.5 — Expiry Monitoring, Alerting & Client UX Hardening
6. R20.6 — Long-Offline Client & Continuous-Operations Integrated Acceptance

No subdivision may be silently inserted, removed, merged, split or renumbered. No `R20.7` is authorized by the accepted planning authority.

## R20 planning accepted authority

Planning branch: `r20/planning`.

Accepted exact planning HEAD: `45c442533211c6efba1ea5fddcf49f7814a12c9f`.

Planning PR #420 merged with `expected_head_sha=45c442533211c6efba1ea5fddcf49f7814a12c9f` as `main` `274831790f7ebbcce8d470569a651cb6b9a10211`.

Accepted exact-head evidence:

- R0 Repository Guard #2638: **SUCCESS** on Ubuntu and Windows.
- Python Core #2610: **SUCCESS** on Ubuntu and Windows; package-build Ubuntu/Windows and integrated KodeStudio UI evidence also passed.
- KodeStudio UI Smoke #2575: **SUCCESS**.

Planning accepted behavior/authority includes:

- preserve TUF expiry checks rather than bypassing them;
- keep Root and Targets offline;
- move Snapshot/Timestamp to distinct online non-exportable keys only through a future sequential Root rotation;
- use short-lived OIDC/federated credentials for cloud signing rather than long-lived cloud credentials in GitHub Secrets;
- introduce an immediate bridge refresh before online-signer migration;
- keep update-network/KMS failure non-destructive to Kodepoia startup/local work;
- require exact-head merge governance and one continuity normalization per subdivision.

Manual intervention for planning: **NONE**.

## R20 planning post-merge continuity normalization

Base `main`: `274831790f7ebbcce8d470569a651cb6b9a10211`.

Normalization branch: `r20/planning-continuity-normalization`.

This branch changes continuity only. It must pass fresh exact-head:

- R0 Repository Guard Ubuntu + Windows;
- full Python Core Ubuntu + Windows plus package/UI evidence;
- KodeStudio UI Smoke.

It must then merge with exact expected-head protection. No second R20 planning normalization is authorized.

R20.1 START-sync is authorized **only after** that exact normalization merge enters `main`.

## Immediate operational priority

Current Snapshot/Timestamp v2 expire at `2026-09-09T17:32:00Z`. R20.1 therefore precedes online-signer work and creates a **temporary signed bridge**:

- Root stays v1 and byte-identical;
- Targets stays v2 and byte-identical;
- Snapshot advances to v3;
- Timestamp advances to v3;
- transitional Snapshot/Timestamp expiry is 30 days from the local signing ceremony;
- bridge signing uses only existing Snapshot/Timestamp custody keys locally;
- no private key or passphrase enters Git/CI;
- final R20.4 policy restores short-lived automatically renewed online metadata.

The 30-day bridge is a migration exception, not the steady-state freshness policy.

## R20 security invariants

- Never disable metadata expiry checks.
- Never accept expired metadata as a fallback for availability.
- Never store Root/Targets private keys in CI or a routine online signer.
- Never reuse one online private key for both Snapshot and Timestamp.
- Never expose TUF passphrases or the local DPAPI vault in repository content, Actions logs/artifacts or continuity.
- Online signer compromise must not authorize new Targets or Root metadata.
- All metadata versions are monotonically increasing.
- Snapshot references exact Targets bytes/version/hash/length.
- Timestamp references exact signed Snapshot bytes/version/hash/length.
- Publication must not expose a mixed metadata generation.
- Network/KMS failure never gates Kodepoia startup or local work.
- All R20 merges require exact-head evidence and expected-head protection.
- Each completed subdivision gets exactly one continuity-only normalization before the next subdivision starts.

## Manual boundaries

R20.1: one local Snapshot/Timestamp bridge signing ceremony is required after repository-safe tooling/tests are ready. The user returns public signed metadata only.

R20.2: no private/external provisioning required.

R20.3: live cloud/KMS key creation, OIDC trust setup and offline Root v2 signing are privileged manual boundaries. Stop there and provide exact user actions; never request private Root key files/passphrases.

R20.4: repository environment/protection settings may require a manual boundary if unavailable through connected tooling.

R20.5: none after automation exists.

R20.6: live incident/key-rotation drill may require explicit provider-side approval.

## Resume rule

On a new conversation, verify current `main`, R20 roadmap, open PRs, current production metadata expiry, public release state and whether this continuity record has a later normalization. Continue subdivision-by-subdivision with dedicated branches, exact-head acceptance, protected merge and exactly one continuity normalization. Stop later subdivisions at a genuine external provisioning/custody boundary and give exact user actions.
