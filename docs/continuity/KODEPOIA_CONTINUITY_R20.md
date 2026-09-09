# KODEPOIA CONTINUITY — R20

**Status:** R20.2 COMPLETE + NORMALIZED; R20.3 ZERO-COST IMPLEMENTATION IN PROGRESS / MANUAL KEY BOUNDARY NEXT

This file is the active continuation authority for **R20 — Continuous Trusted Update Operations**. R20 planning, R20.1 and R20.2 are complete and normalized. R20.2 normalization PR #425 merged as normalized `main` `02ae599f951f353d9647e5cb6ca39f28eb655cbf`, which is the sole authorized R20.3 base. R20.3 is active on `r20/03-zero-cost-architecture` and has been explicitly revised to preserve the product invariant that Kodepoia must remain free to create and free to use.

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
- Private-key custody remains outside Git/repository/CI. No R20 Root/Targets private key or passphrase has entered Git, CI, public evidence or continuity.
- Targets v2 remains byte-identical at SHA-256 `0b65bf34e50d43ed1f82f0f4a17875fb0a4bb597ed5b6066749dc9352e504e3f`, authorizes only the accepted beta rc2 installer and expires `2027-09-08T17:32:00Z`.
- Production Snapshot v3 SHA-256: `dbbb5966f9146b00e5697fda302107bab850c6dcb254e70e0a6e10d25b5c7796`.
- Production Timestamp v3 SHA-256: `3d16a4d3bfccec33102b73a3a4cddb8af83f0c558bc4cc3e42b7c7536fdbdc7d`.
- Snapshot v3 and Timestamp v3 both expire `2026-10-08T21:44:18Z`.
- Kodepoia rejects expired trusted metadata and maps that case to a non-destructive `metadata-expired` update-discovery state.

## R20 objective

Users must be able to return to Kodepoia after a long period and update directly inside the application without being exposed to metadata-expiry maintenance. TUF freshness protections remain enforced; operational automation, not client-side bypass, keeps metadata fresh.

A new explicit product invariant governs the rest of R20: **the mandatory Kodepoia creation, maintenance, distribution and user path must cost 0 €.** Paid cloud/KMS/HSM services may be optional hardening backends only and may never become a prerequisite.

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

## External authority re-verified for R20.3

- TUF permits Snapshot and Timestamp online keys for continuous delivery and recommends keeping other top-level role keys offline.
- Timestamp is intentionally short-lived/frequently re-signed to detect freeze attacks.
- Snapshot and Timestamp must not share a key.
- GitHub documents that standard GitHub-hosted runners are free and unlimited for public repositories.
- GitHub Actions secrets are encrypted before reaching GitHub and are available only to workflows that explicitly reference them.
- GitHub Free exposes environment secrets for public repositories and environments can restrict deployment branches.
- Consequently, GitHub environment secrets plus ephemeral hosted runners are accepted as the **zero-cost reference backend for the two low-authority online roles only**. This intentionally trades non-exportable-HSM hardening for zero mandatory cost while retaining TUF role separation and offline Root/Targets custody.

## Authorized subdivision sequence

1. R20.1 — Bridge Metadata Refresh & Custody-Safe Tooling
2. R20.2 — Online Signer Abstraction & Rotation Package
3. R20.3 — Zero-Cost Online-Key Provisioning & Root Rotation
4. R20.4 — Scheduled Metadata Refresh & Atomic Publication
5. R20.5 — Expiry Monitoring, Alerting & Client UX Hardening
6. R20.6 — Long-Offline Client & Continuous-Operations Integrated Acceptance

No subdivision may be silently inserted, removed, merged, split or renumbered. The R20.3 title/scope adjustment is an explicit governed roadmap change preserving subdivision number/dependencies while enforcing the zero-cost product constraint. No `R20.7` is authorized.

## R20 planning accepted authority

Planning branch: `r20/planning`.

Accepted exact planning HEAD: `45c442533211c6efba1ea5fddcf49f7814a12c9f`.

Planning PR #420 merged with `expected_head_sha=45c442533211c6efba1ea5fddcf49f7814a12c9f` as `main` `274831790f7ebbcce8d470569a651cb6b9a10211`.

Accepted exact-head evidence:

- R0 Repository Guard #2638: **SUCCESS** on Ubuntu and Windows.
- Python Core #2610: **SUCCESS** on Ubuntu and Windows; package-build Ubuntu/Windows and integrated KodeStudio UI evidence also passed.
- KodeStudio UI Smoke #2575: **SUCCESS**.

Planning accepted behavior/authority originally included an OIDC/remote-KMS steady-state candidate. That historical planning decision is preserved as provenance, but R20.3 explicitly supersedes **mandatory** paid-provider use with the governed zero-cost reference backend. The provider-neutral R20.2 interface remains available for optional hardening.

Manual intervention for planning: **NONE**.

## R20 planning post-merge continuity normalization — COMPLETE

Base `main`: `274831790f7ebbcce8d470569a651cb6b9a10211`.

Normalization branch: `r20/planning-continuity-normalization`.

Normalization branch head merged as the second parent `e2d2250c8cd57084d32be4a2af6dbbb32d192076` of normalized `main` `725a44756ab27ed29f84e7fcf238477fd2997d8a`.

R20 planning is therefore **COMPLETE + NORMALIZED**, and `725a44756ab27ed29f84e7fcf238477fd2997d8a` was the authorized R20.1 base.

## R20.1 — Bridge Metadata Refresh & Custody-Safe Tooling — COMPLETE + NORMALIZED

Implementation branch: `r20/01-bridge-metadata-refresh`.

Authorized base: normalized planning `main` `725a44756ab27ed29f84e7fcf238477fd2997d8a`.

Accepted exact R20.1 HEAD: `878b2f81d1893b63bef4d7980a6bcb19101530eb`.

R20.1 PR #422 merged with `expected_head_sha=878b2f81d1893b63bef4d7980a6bcb19101530eb` as `main` `324ad91f47eff8a69166b78e16c11b49251ceb0d`.

Accepted exact-head evidence on `878b2f81d1893b63bef4d7980a6bcb19101530eb`:

- R20.1 Bridge Metadata Refresh Acceptance #25: **SUCCESS** on Ubuntu and Windows.
- R0 Repository Guard #2652: **SUCCESS** on Ubuntu and Windows.
- Python Core #2624: **SUCCESS** on Ubuntu and Windows; package-build Ubuntu/Windows and integrated KodeStudio UI evidence also passed.
- KodeStudio UI Smoke #2589: **SUCCESS**.

R20.1 accepted behavior/evidence:

- Root stays v1 and byte-identical at SHA-256 `892442754966aa643bbe15a2910aa3fef59032c8f5eade34fed62efd96aefee5`.
- Targets stays v2 and byte-identical at SHA-256 `0b65bf34e50d43ed1f82f0f4a17875fb0a4bb597ed5b6066749dc9352e504e3f`.
- Snapshot advances monotonically v2 -> v3 and is signed by the Root-authorized Snapshot role key.
- Timestamp advances monotonically v2 -> v3 and is signed by the distinct Root-authorized Timestamp role key.
- Snapshot v3 binds exact Targets v2 bytes/version/hash/length.
- Timestamp v3 binds exact signed Snapshot v3 bytes/version/hash/length.
- Snapshot v3 SHA-256 is `dbbb5966f9146b00e5697fda302107bab850c6dcb254e70e0a6e10d25b5c7796`.
- Timestamp v3 SHA-256 is `3d16a4d3bfccec33102b73a3a4cddb8af83f0c558bc4cc3e42b7c7536fdbdc7d`.
- Snapshot/Timestamp bridge signing time is `2026-09-08T21:44:18Z` and bridge expiry is `2026-10-08T21:44:18Z`.
- Accepted returned public ZIP SHA-256 is `bc60924c250bb602fb9add13657a7f18c1ea27a20bef075811879254121aa31d`.
- `docs/roadmap/R20_1_BRIDGE_PUBLIC_MANIFEST.json` records the returned public manifest semantically; its JSON serialization is not a cryptographic authority.
- `docs/roadmap/R20_1_BRIDGE_FINAL_ACCEPTANCE.json` records local public-bundle validation evidence without private material.
- CI verifies signatures, exact signed metadata hashes, versions 1/2/3/3, bindings, freshness and custody invariants with `contents: read` only.
- No private key or passphrase entered Git, CI or public evidence.

Manual intervention for R20.1: **COMPLETE**. The user performed the one authorized local Snapshot/Timestamp bridge signing ceremony using existing custody keys and returned public signed metadata only.

The 30-day bridge remains a migration exception, not the steady-state freshness policy. R20.4 must restore short-lived automatically renewed metadata.

### R20.1 post-merge continuity normalization — COMPLETE

R20.1 normalization merged to produce normalized `main` `53f431f50361d7fa0e3b31ac0c2a2596326c9f85`. That exact normalized head was the sole authorized base for R20.2.

## R20.2 — Online Signer Abstraction & Rotation Package — COMPLETE + NORMALIZED

Implementation branch: `r20/02-online-signer-rotation`.

Authorized base: normalized R20.1 `main` `53f431f50361d7fa0e3b31ac0c2a2596326c9f85`.

Accepted exact R20.2 HEAD: `9ab039519e434b24fff1c45dfeed2aa2fef4920f`.

R20.2 PR #424 merged with `expected_head_sha=9ab039519e434b24fff1c45dfeed2aa2fef4920f` as `main` `2d94afc22be01871caad9d99fdca090e3743a786`.

Accepted exact-head evidence on `9ab039519e434b24fff1c45dfeed2aa2fef4920f`:

- R20.2 Online Signer Rotation Acceptance #21: **SUCCESS** on Ubuntu and Windows.
- R0 Repository Guard #2665: **SUCCESS** on Ubuntu and Windows.
- Python Core #2637: **SUCCESS** on Ubuntu and Windows; package-build Ubuntu/Windows and integrated KodeStudio UI evidence all passed.
- KodeStudio UI Smoke #2602: **SUCCESS**.
- R16.9 Supply Chain Provenance Acceptance #261: **SUCCESS**.

A prior technical R20.2 HEAD `f22b404630a427bd6ca6fc8e58e1e575f0a8bdab` had also passed focused acceptance #17 on Ubuntu and Windows before final END-sync. The final documentation-synchronized HEAD above is the accepted authority.

R20.2 accepted behavior/evidence:

- online signer configuration contains only role, provider/resource identifiers and public key material;
- runtime signer resolution is behind the generic `securesystemslib.signer.Signer` boundary and validates resolved public identity before signing;
- SubjectPublicKeyInfo PEM public keys can be imported with matching TUF/securesystemslib keyid derivation;
- deterministic synthetic in-memory CI signers require no provider credential;
- Root N+1 rotation packages are immutable/public-only and replace only Snapshot/Timestamp public keys;
- Root and Targets role policies, Root threshold and TUF policy fields remain preserved;
- sequential Root transition verification requires candidate Root N+1 to satisfy both the currently trusted Root threshold and its own Root threshold;
- Snapshot and Timestamp remain separate threshold-1 roles with distinct keys;
- production Root v1 remains byte-identical and R20.2 performs no live provider provisioning or offline Root signing;
- the R20.2 acceptance workflow is registered as an immutable R16.9 authority while external action SHA pins and least-privilege `contents: read` remain intact.

Manual intervention for R20.2: **NONE**.

### R20.2 post-merge continuity normalization — COMPLETE

Implementation merge base: `main` `2d94afc22be01871caad9d99fdca090e3743a786`.

Unique normalization branch: `r20/02-continuity-normalization`.

Normalization PR #425 merged with exact head `8ba7fbcf49836094dab9e7a78fdb9cba8db16332` as normalized `main` `02ae599f951f353d9647e5cb6ca39f28eb655cbf` after fresh R0, R20.2, Python Core, package-build and UI evidence passed. No second R20.2 normalization is permitted.

## R20.3 — Zero-Cost Online-Key Provisioning & Root Rotation — IN PROGRESS

Implementation branch: `r20/03-zero-cost-architecture`.

Authorized base: normalized R20.2 `main` `02ae599f951f353d9647e5cb6ca39f28eb655cbf`.

R20.3 zero-cost scope:

- use two distinct Ed25519 keys for Snapshot and Timestamp;
- generate the two 32-byte online private seeds locally, never in CI and never in Git;
- store the seeds as separate GitHub environment secrets named `TUF_SNAPSHOT_ED25519_SEED_B64` and `TUF_TIMESTAMP_ED25519_SEED_B64` in environment `tuf-production-signing`;
- use GitHub-hosted standard runners on this public repository so the mandatory automation path remains free;
- decode the two low-authority secrets directly in process memory and never persist them into repository files or artifacts;
- preserve Root/Targets private custody entirely offline;
- generate a public-only R20.3 package with the new public keys/keyids and unsigned Root v2 rotation package;
- later require the offline Root 2-of-3 ceremony before Root v2 may enter production;
- optional external KMS/HSM signers remain compatible through R20.2 but are never mandatory.

Repository-side pre-boundary implementation includes:

- `src/kodepoia/update/zero_cost_signing.py` — zero-cost GitHub environment-secret signer resolver and local Ed25519 material generator;
- `scripts/r20_3_prepare_zero_cost_keys.py` — local-only key-generation/public-package tool that refuses to place private output inside the repository;
- `tests/test_r20_3_zero_cost_signing.py` — separation, in-memory resolution, fail-closed and no-private-public-package acceptance;
- `.github/workflows/r20-3-zero-cost-signing-acceptance.yml` — synthetic exact-head acceptance consuming no live secrets;
- R16.9 authority updated to include the new focused acceptance while retaining immutable external action pins and `contents: read`.

### R20.3 manual boundary — REQUIRED NEXT

After the repository-side pre-boundary head passes focused acceptance, the user must perform the following locally/external to CI:

1. generate the real Snapshot/Timestamp online key pair with the repository-provided local tool;
2. return only the public `R20_3_ZERO_COST_PUBLIC_PACKAGE.zip`;
3. create GitHub environment `tuf-production-signing` and configure the two secret values from the local private output without exposing them in chat/issues/logs;
4. later sign the exact Root v2 with at least 2-of-3 existing Root private keys locally and return only the public signed Root metadata.

No AWS/GCP/Azure/paid account, billing setup, cloud region or OIDC trust is required by the reference path.

R20.4 and all later subdivisions remain blocked until R20.3 is completed, exact-head accepted, merged and normalized.

## Immediate operational priority

Production Snapshot/Timestamp are v3 and expire at `2026-10-08T21:44:18Z`. R20.3 must establish the two zero-cost online role keys and rotate Root before the bridge expires, while retaining enough margin for R20.4 scheduled refresh implementation.

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

R20.1: **COMPLETE** — one local Snapshot/Timestamp bridge signing ceremony was performed; public metadata only was returned.

R20.2: **NONE / COMPLETE + NORMALIZED** — provider-neutral implementation and synthetic acceptance only.

R20.3: **REQUIRED NEXT** — generate the two online seeds locally, configure the two GitHub environment secrets, and later perform offline Root v2 threshold signing. Stop before later subdivisions and give exact actions; never request or accept the private seed values, Root private-key files or passphrases.

R20.4: GitHub environment/protection settings may require a manual boundary if unavailable through connected tooling.

R20.5: none after automation exists.

R20.6: live incident/key-rotation drill may require explicit privileged approval.

## Resume rule

On a new conversation, verify current normalized `main`, R20 roadmap, open R20.3 PR/branch, current production metadata expiry and public release state. If `r20/03-zero-cost-architecture` exists, resume R20.3 only. Confirm the zero-cost architecture remains authoritative. Complete repository-side focused acceptance first; then stop at the local online-key generation / GitHub environment-secret boundary and provide exact user actions. Accept back only public key/Root metadata evidence, never private seed values or Root private-key files/passphrases. R20.4 remains blocked until R20.3 is **COMPLETE + NORMALIZED**.
