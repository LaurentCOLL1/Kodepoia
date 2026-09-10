# KODEPOIA CONTINUITY — R20

**Status:** R20.3 COMPLETE + NORMALIZED; LIVE ZERO-COST SIGNER CHALLENGE VERIFIED; R20.4 NEXT

This file is the active continuation authority for **R20 — Continuous Trusted Update Operations**. R20 planning, R20.1, R20.2 and R20.3 are complete. R20.3 implementation PR #426 merged from accepted exact HEAD `747405e133fb2934e377a0312b59a9d468e4af19`, and two narrowly scoped post-merge corrections (#427 and #428) repaired only the live-challenge clean-worktree path. Final pre-normalization `main` is `35f3cad975877f0a7e2416afb180a0160511add2`. On that exact commit, **R20.3 Live Zero-Cost Signer Challenge #4** completed successfully and verified the two live GitHub environment-secret signing identities without publishing metadata, exposing secret values, using artifact storage or modifying repository state.

This branch, `r20/03-continuity-normalization`, is the unique continuity-only post-merge normalization for R20.3. Once it merges, the resulting `main` is the sole authorized R20.4 base. No second R20.3 normalization is permitted merely to embed the resulting merge SHA recursively.

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
- Current production Root is **v2**, SHA-256 `c92b2165bcbf39f74599fbdf8cc30e203f8c93cc2f24c5c74012821646850ee7`, Root threshold 2-of-3, expiry `2027-09-08T14:59:19Z`.
- Targets remains exact **v2**, SHA-256 `0b65bf34e50d43ed1f82f0f4a17875fb0a4bb597ed5b6066749dc9352e504e3f`, length `1001`, and expires `2027-09-08T17:32:00Z`.
- Current production Snapshot is **v4**, SHA-256 `1fccbcc5721acf59188761a79b70d829fa1ae23e77e505d1c1e9867c110eced9`, signed by replacement Snapshot keyid `fac1c790b4d6dbeb04ca4a803bd80e6fde19127fc7ada34003cef5d6b50506d8`.
- Current production Timestamp is **v4**, SHA-256 `74c815dc414ae946aba1f7c427ae044dbaa3a5e1fb15bbdb436e33881fc6e501`, signed by distinct replacement Timestamp keyid `8d81006fd9de63660d74c43b6926ed664b2e9f1bdf81a9556367232533d5a2ad`.
- Snapshot v4 and Timestamp v4 both retain the transition expiry `2026-10-08T21:44:18Z`; R20.3 deliberately did not extend the temporary bridge lifetime.
- Snapshot v4 binds exact Targets v2 hash/version/length; Timestamp v4 binds exact signed Snapshot v4 hash/version/length.
- Private Root/Targets custody remains outside Git/repository/CI. No Root/Targets private key or passphrase entered Git, CI, public evidence or continuity.
- The two low-authority online Ed25519 seeds exist only as separate GitHub environment secrets in `tuf-production-signing` and in the user's retained local custody; their values are not repository authority and must never be requested or recorded.
- Kodepoia rejects expired trusted metadata and maps that case to a non-destructive `metadata-expired` update-discovery state.

## R20 objective

Users must be able to return to Kodepoia after a long period and update directly inside the application without being exposed to metadata-expiry maintenance. TUF freshness protections remain enforced; operational automation, not client-side bypass, keeps metadata fresh.

A phase-wide product invariant governs R20: **the mandatory Kodepoia creation, maintenance, distribution and user path must cost 0 €.** Paid cloud/KMS/HSM services may be optional hardening backends only and may never become a prerequisite.

Steady-state trust model:

- Root: offline, threshold-protected;
- Targets: offline, release authorization only;
- Snapshot: dedicated low-authority online Ed25519 key;
- Timestamp: separate dedicated low-authority online Ed25519 key;
- zero-cost reference backend: two separate GitHub Actions environment secrets consumed only by ephemeral GitHub-hosted runners;
- scheduled metadata renewal before expiry;
- no Root/Targets private material in GitHub Actions;
- no paid infrastructure dependency in the mandatory path;
- optional provider-neutral KMS/HSM backends remain possible through the R20.2 signer abstraction;
- no user-visible update deadline created by metadata maintenance.

## Authorized subdivision sequence

1. R20.1 — Bridge Metadata Refresh & Custody-Safe Tooling
2. R20.2 — Online Signer Abstraction & Rotation Package
3. R20.3 — Zero-Cost Online-Key Provisioning & Root Rotation
4. R20.4 — Scheduled Metadata Refresh & Atomic Publication
5. R20.5 — Expiry Monitoring, Alerting & Client UX Hardening
6. R20.6 — Long-Offline Client & Continuous-Operations Integrated Acceptance

No subdivision may be silently inserted, removed, merged, split or renumbered. No `R20.7` is authorized.

## R20 planning — COMPLETE + NORMALIZED

Planning branch: `r20/planning`.

Accepted exact planning HEAD: `45c442533211c6efba1ea5fddcf49f7814a12c9f`.

Planning PR #420 merged as `main` `274831790f7ebbcce8d470569a651cb6b9a10211`. Planning normalization produced `main` `725a44756ab27ed29f84e7fcf238477fd2997d8a`, the sole authorized R20.1 base.

Accepted planning evidence included R0 Repository Guard #2638, Python Core #2610 and KodeStudio UI Smoke #2575, all successful on their required platforms.

Historical planning considered an OIDC/remote-KMS steady-state candidate. R20.3 explicitly superseded **mandatory** paid-provider use with the governed zero-cost GitHub reference backend while preserving the provider-neutral R20.2 interface for optional hardening.

Manual intervention for planning: **NONE**.

## R20.1 — Bridge Metadata Refresh & Custody-Safe Tooling — COMPLETE + NORMALIZED

Implementation branch: `r20/01-bridge-metadata-refresh`.

Authorized base: normalized planning `main` `725a44756ab27ed29f84e7fcf238477fd2997d8a`.

Accepted exact R20.1 HEAD: `878b2f81d1893b63bef4d7980a6bcb19101530eb`.

R20.1 PR #422 merged as `main` `324ad91f47eff8a69166b78e16c11b49251ceb0d`; unique normalization produced `main` `53f431f50361d7fa0e3b31ac0c2a2596326c9f85`, the sole authorized R20.2 base.

Accepted exact-head evidence included:

- R20.1 Bridge Metadata Refresh Acceptance #25: **SUCCESS** on Ubuntu and Windows;
- R0 Repository Guard #2652: **SUCCESS** on Ubuntu and Windows;
- Python Core #2624: **SUCCESS** on Ubuntu and Windows, including package-build and integrated KodeStudio UI evidence;
- KodeStudio UI Smoke #2589: **SUCCESS**.

R20.1 preserved Root v1 and Targets v2 byte-for-byte, advanced Snapshot/Timestamp to v3/v3, bound exact metadata hashes/versions/lengths, and established the temporary bridge expiry `2026-10-08T21:44:18Z` without weakening client freshness verification.

Manual intervention for R20.1: **COMPLETE**. The user performed the authorized local Snapshot/Timestamp bridge-signing ceremony and returned public signed metadata only.

## R20.2 — Online Signer Abstraction & Rotation Package — COMPLETE + NORMALIZED

Implementation branch: `r20/02-online-signer-rotation`.

Authorized base: normalized R20.1 `main` `53f431f50361d7fa0e3b31ac0c2a2596326c9f85`.

Accepted exact R20.2 HEAD: `9ab039519e434b24fff1c45dfeed2aa2fef4920f`.

R20.2 PR #424 merged as `main` `2d94afc22be01871caad9d99fdca090e3743a786`. Normalization PR #425 merged exact head `8ba7fbcf49836094dab9e7a78fdb9cba8db16332` as normalized `main` `02ae599f951f353d9647e5cb6ca39f28eb655cbf`, the sole authorized R20.3 base.

Accepted exact-head evidence included:

- R20.2 Online Signer Rotation Acceptance #21: **SUCCESS** on Ubuntu and Windows;
- R0 Repository Guard #2665: **SUCCESS** on Ubuntu and Windows;
- Python Core #2637: **SUCCESS** on Ubuntu and Windows with package-build and integrated KodeStudio UI evidence;
- KodeStudio UI Smoke #2602: **SUCCESS**;
- R16.9 Supply Chain Provenance Acceptance #261: **SUCCESS**.

R20.2 accepted behavior includes provider-neutral signer configuration with public identity validation, deterministic synthetic CI signers, public-only Root N+1 rotation packages, sequential old/new Root threshold verification, and preserved Root/Targets custody policy.

Manual intervention for R20.2: **NONE**.

## R20.3 — Zero-Cost Online-Key Provisioning & Root Rotation — COMPLETE + NORMALIZED

Implementation branch: `r20/03-zero-cost-architecture`.

Authorized base: normalized R20.2 `main` `02ae599f951f353d9647e5cb6ca39f28eb655cbf`.

Accepted exact implementation HEAD: `747405e133fb2934e377a0312b59a9d468e4af19`.

Implementation PR #426 merged that exact branch lineage as `main` `a0650cba7ad0faf95e16f3059baa2e422f79648a`.

The post-merge live challenge then exposed two repository-cleanliness integration defects, not secret/signature defects:

- PR #427, exact head `6ff80d9d4560b31c7ef9f4e094c029f66b63917e`, restored tracked exact-source bytes after editable dependency installation and merged as `main` `f4e537b62e5aef7f84131ee3fddf17ca04e603e4`;
- PR #428, final exact head `8ebb87e0357c3fd1e9b2f1709780112847938ee8`, made byte-bound `docs/roadmap/R10_7_LOCAL_ACCEPTANCE.json` immune to line-ending conversion and added a cross-platform regression gate; it merged as `main` `35f3cad975877f0a7e2416afb180a0160511add2`.

### R20.3 accepted exact-head evidence

On implementation HEAD `747405e133fb2934e377a0312b59a9d468e4af19`:

- R20.3 Zero-Cost Signing Acceptance #71: **SUCCESS** on Ubuntu and Windows;
- R0 Repository Guard #2702: **SUCCESS** on Ubuntu and Windows;
- Python Core #2674: **SUCCESS**;
- KodeStudio UI Smoke #2639: **SUCCESS**;
- R16.9 Supply Chain Provenance Acceptance #295: **SUCCESS**.

On final corrective HEAD `8ebb87e0357c3fd1e9b2f1709780112847938ee8`, R20.3 Zero-Cost Signing Acceptance #74 passed on Ubuntu and Windows, including the explicit `Assert byte-bound R10.7 evidence checkout is clean` gate. R0 Repository Guard, Python Core/package-build and KodeStudio UI Smoke also passed on that final correction line before merge.

### R20.3 public online-key and Root-transition evidence

The locally generated public key package remains accepted:

- public online-key package SHA-256: `4b26dbf702f93e1c2e6f813eae7c22771a06e97fd9d77bd6d57bff1b6c22b1db`;
- Snapshot replacement keyid: `fac1c790b4d6dbeb04ca4a803bd80e6fde19127fc7ada34003cef5d6b50506d8`;
- Timestamp replacement keyid: `8d81006fd9de63660d74c43b6926ed664b2e9f1bdf81a9556367232533d5a2ad`;
- unsigned Root v2 SHA-256: `7ae909722149fe7f05380f93b7317c99347f8b3c1d102b7b6ddca64bbe1bbe1d`.

The user completed the offline Root threshold ceremony and returned only the public full-transition package. Accepted final transition authority:

- full public transition ZIP SHA-256: `7ee54d08d0dc11ce275705c877a0615b69bedd15a18747393ef7e1dbee58651e`;
- transition manifest SHA-256: `bfd8ca6c1386911f6504410e42a4ef0b9e8243b13d5670a84738f572237e7d50`;
- signed Root v2 SHA-256: `c92b2165bcbf39f74599fbdf8cc30e203f8c93cc2f24c5c74012821646850ee7`;
- Snapshot v4 SHA-256: `1fccbcc5721acf59188761a79b70d829fa1ae23e77e505d1c1e9867c110eced9`;
- Timestamp v4 SHA-256: `74c815dc414ae946aba1f7c427ae044dbaa3a5e1fb15bbdb436e33881fc6e501`;
- old Root threshold verification: **PASS**;
- new Root threshold verification: **PASS**;
- Snapshot signature verification: **PASS**;
- Timestamp signature verification: **PASS**;
- Targets bytes unchanged: **TRUE**;
- private material detected: **FALSE**;
- paid provider required: **FALSE**;
- expiry extended: **FALSE**.

The integrated repository metadata is now Root v2 / Targets v2 / Snapshot v4 / Timestamp v4. Root v2 authorizes only the dedicated replacement Snapshot/Timestamp online public keys for those roles; Root and Targets authority remain offline.

### R20.3 live GitHub signer challenge — COMPLETE

**R20.3 Live Zero-Cost Signer Challenge #4**, workflow run `34507387616`, was manually dispatched on exact `main` `35f3cad975877f0a7e2416afb180a0160511add2` and completed **SUCCESS**.

The job passed every governed step:

- exact-main checkout provenance;
- focused dependency installation;
- exact tracked-source restoration;
- live Snapshot/Timestamp secret-identity verification without publication;
- final repository-state cleanliness assertion.

Public challenge result:

- format: `kodepoia-r20-3-live-signing-challenge`;
- status: `pass`;
- source SHA: `35f3cad975877f0a7e2416afb180a0160511add2`;
- challenge SHA-256: `ef4bc4a23a4ee06b7f03f80bc479fa4523862406a31083a478fc991254dbc4b3`;
- `distinct_online_keys`: `true`;
- `signatures_verified`: `true`;
- `secret_values_emitted`: `false`;
- `artifact_storage_used`: `false`;
- `production_effect`: `false`;
- verified Snapshot keyid: `fac1c790b4d6dbeb04ca4a803bd80e6fde19127fc7ada34003cef5d6b50506d8`;
- verified Timestamp keyid: `8d81006fd9de63660d74c43b6926ed664b2e9f1bdf81a9556367232533d5a2ad`.

The live challenge therefore proves that the two configured GitHub environment secrets correspond to the exact public online-role identities committed in Root v2, while preserving no-publication and no-secret-output boundaries.

### R20.3 post-merge continuity normalization

Pre-normalization base: `main` `35f3cad975877f0a7e2416afb180a0160511add2`.

Unique normalization branch: `r20/03-continuity-normalization`.

This branch modifies only `docs/continuity/KODEPOIA_CONTINUITY_R20.md`. Its protected exact-head merge is the sole R20.3 post-merge normalization. The resulting normalized `main` SHA is established by the merge itself and becomes the only authorized R20.4 base; do not create a second R20.3 normalization merely to embed that merge SHA.

Manual intervention for R20.3: **COMPLETE**. The public online-key package, GitHub environment-secret setup, offline Root v2 threshold ceremony, v4/v4 transition package, repository integration and live no-publication signer challenge are all complete.

## R20.4 — Scheduled Metadata Refresh & Atomic Publication — NEXT AUTHORIZED SUBDIVISION

R20.4 may begin only from the normalized `main` produced by the unique R20.3 continuity merge.

Required scope remains the R20 plan authority:

- scheduled and manual-dispatch refresh using the R20.3 zero-cost online signer backend;
- secret access only in the authorized signing job/environment;
- refresh only below the remaining-lifetime threshold;
- monotonic versioning under concurrency/superseded runs;
- Snapshot generated from exact current Targets bytes;
- Timestamp generated only from exact final signed Snapshot bytes;
- atomic publication ordering preventing mixed metadata generations;
- no release-asset rebuild/mutation during freshness refresh;
- short-lived steady-state metadata with operational margin;
- least-privilege Actions permissions and no mandatory paid/OIDC provider dependency.

Production Snapshot/Timestamp v4 still expire `2026-10-08T21:44:18Z`, so R20.4 is now the operational priority.

### GitHub Actions Node 20 maintenance constraint

The successful live challenge emitted a non-blocking warning because the currently exact-SHA-pinned `actions/checkout` and `actions/setup-python` revisions target Node.js 20 and GitHub is forcing them to run on Node.js 24. This warning did **not** invalidate R20.3. However, GitHub's published deprecation timeline removes Node.js 20 from hosted runners on **2026-09-23**. R20.4 must therefore update the relevant exact action SHA pins to Node-24-compatible releases under the existing R16.9 supply-chain governance before that removal date, while preserving immutable pinning and least privilege.

## R20 security invariants

- Never disable metadata expiry checks.
- Never accept expired metadata as a fallback for availability.
- Never require a paid service in the mandatory Kodepoia path.
- Never store Root/Targets private keys in CI or a routine online signer.
- Never reuse one online private key for both Snapshot and Timestamp.
- Never expose TUF passphrases, local vault material or online secret values in repository content, Actions logs/artifacts, issues or continuity.
- GitHub environment secrets are permitted only for the low-authority Snapshot/Timestamp online keys.
- Online signer compromise must not authorize new Targets or Root metadata.
- All metadata versions are monotonically increasing.
- Snapshot references exact Targets bytes/version/hash/length.
- Timestamp references exact signed Snapshot bytes/version/hash/length.
- Publication must not expose a mixed metadata generation.
- GitHub Actions/signing-backend failure never gates Kodepoia startup or local work.
- All R20 merges require exact-head evidence and expected-head protection.
- Each completed subdivision gets exactly one continuity-only normalization before the next subdivision starts.

## Manual boundaries

R20.1: **COMPLETE** — local bridge signing was performed; public metadata only was returned.

R20.2: **NONE / COMPLETE + NORMALIZED** — provider-neutral implementation and synthetic acceptance only.

R20.3: **COMPLETE** — public online-key generation, GitHub environment-secret provisioning, offline Root v2 2-of-3 signing, atomic v4/v4 transition and live no-publication secret-identity challenge all passed.

R20.4: **CONDITIONAL** — repository/environment/rules configuration or protected atomic publication permissions may require a manual boundary if unavailable through connected tooling. Do not silently weaken environment or branch restrictions.

R20.5: **NONE** after R20.4 automation exists.

R20.6: **CONDITIONAL** — live incident/key-rotation drill may require explicit privileged approval.

## Resume rule

On a new conversation, first verify the current `main`, this continuity authority, R20 roadmap, production Root/Snapshot/Timestamp versions and expiry, and the latest R20.3 normalization PR state. R20.3 is complete: **do not regenerate or replace the accepted online keys and do not repeat the offline Root ceremony unless an explicit governed revocation/rotation is authorized.** If `r20/03-continuity-normalization` has not merged, finish only that normalization. Once it has merged, the resulting `main` is the sole authorized R20.4 base. Begin R20.4 subdivision-by-subdivision from that exact base, preserving the zero-cost reference path, exact-head acceptance, immutable action pinning, least privilege and the Node-24 migration deadline. R20.5 remains blocked until R20.4 is complete and uniquely normalized.
