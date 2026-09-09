# KODEPOIA CONTINUITY — R20

**Status:** R20.2 COMPLETE + NORMALIZED; R20.3 MANUAL BOUNDARY NEXT

This file is the active continuation authority for **R20 — Continuous Trusted Update Operations**. R20 planning, R20.1 and R20.2 are complete. R20.2 implementation PR #424 merged from exact accepted HEAD `9ab039519e434b24fff1c45dfeed2aa2fef4920f` as `main` `2d94afc22be01871caad9d99fdca090e3743a786`. This branch, `r20/02-continuity-normalization`, is the unique continuity-only post-merge normalization for R20.2; once this branch merges, that merge is the sole normalized R20.2 base and R20.3 becomes the next authorized subdivision.

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
- Private-key custody remains outside Git/repository/CI. No R20 private key or passphrase has entered Git, CI, public evidence or continuity.
- Targets v2 remains byte-identical at SHA-256 `0b65bf34e50d43ed1f82f0f4a17875fb0a4bb597ed5b6066749dc9352e504e3f`, authorizes only the accepted beta rc2 installer and expires `2027-09-08T17:32:00Z`.
- Production Snapshot v3 SHA-256: `dbbb5966f9146b00e5697fda302107bab850c6dcb254e70e0a6e10d25b5c7796`.
- Production Timestamp v3 SHA-256: `3d16a4d3bfccec33102b73a3a4cddb8af83f0c558bc4cc3e42b7c7536fdbdc7d`.
- Snapshot v3 and Timestamp v3 both expire `2026-10-08T21:44:18Z`.
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
- AWS KMS and Google Cloud KMS are R20.3 candidate providers; provider choice remains a privileged manual decision.

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

Manual intervention for R20.1: **COMPLETE**. The user performed the one authorized local Snapshot/Timestamp signing ceremony using existing custody keys and returned public signed metadata only.

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
- production Root v1 remains byte-identical and R20.2 performs no live KMS/OIDC provisioning or offline Root signing;
- the R20.2 acceptance workflow is registered as an immutable R16.9 authority while external action SHA pins and least-privilege `contents: read` remain intact;
- CI contains no `id-token: write` provider credential flow in R20.2 and emits public-only acceptance evidence.

Manual intervention for R20.2: **NONE**.

### R20.2 post-merge continuity normalization — COMPLETE

Implementation merge base: `main` `2d94afc22be01871caad9d99fdca090e3743a786`.

Unique normalization branch: `r20/02-continuity-normalization`.

This branch modifies only `docs/continuity/KODEPOIA_CONTINUITY_R20.md`. Its protected merge is the sole R20.2 post-merge normalization. The resulting normalized `main` SHA is intentionally established by that merge itself and becomes the only authorized R20.3 base; no second normalization is permitted merely to embed the resulting merge SHA recursively.

R20.3 is therefore the next authorized subdivision after this normalization merge, but it immediately reaches the explicit external provisioning/custody boundary described below.

## R20.3 — OIDC/KMS Online-Key Provisioning & Root Rotation — MANUAL BOUNDARY

No live provider resource has been created by repository automation yet. Before any R20.3 implementation may proceed past this boundary, the user must select and provision an approved cloud/KMS path, configure narrowly scoped GitHub Actions OIDC trust, retrieve only the public keys/resource identifiers, and later perform the offline Root v2 threshold-signing ceremony. Private Root files/passphrases must never be sent to ChatGPT, GitHub, CI or repository artifacts.

R20.4 and all later subdivisions remain blocked until R20.3 is completed, exact-head accepted, merged and normalized.

## Immediate operational priority

Production Snapshot/Timestamp are v3 and expire at `2026-10-08T21:44:18Z`. R20.3 must therefore establish dedicated online Snapshot/Timestamp signers and rotate Root before the bridge expires, while retaining enough operational margin for R20.4 scheduled refresh implementation.

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

R20.1: **COMPLETE** — one local Snapshot/Timestamp bridge signing ceremony was performed; public metadata only was returned.

R20.2: **NONE / COMPLETE + NORMALIZED** — provider-neutral implementation and synthetic acceptance only.

R20.3: **REQUIRED NOW** — choose/provision the live cloud/KMS keys, configure GitHub OIDC trust and later perform offline Root v2 threshold signing. Stop before later subdivisions and provide exact user actions; never request private Root key files/passphrases.

R20.4: repository environment/protection settings may require a manual boundary if unavailable through connected tooling.

R20.5: none after automation exists.

R20.6: live incident/key-rotation drill may require explicit provider-side approval.

## Resume rule

On a new conversation, verify current normalized `main`, R20 roadmap, open PRs, current production metadata expiry and public release state. If the R20.2 normalization PR has not merged, resume only that normalization. Once it has merged, do not create another R20.2 normalization: R20.3 is the next authorized subdivision and begins at its external KMS/OIDC/offline-custody manual boundary. Continue only after the user returns the non-secret provider choice, KMS public key/resource identifiers and other explicitly requested public evidence. Never request or accept Root private-key files, TUF passphrases, cloud long-lived secrets or exported KMS private material. R20.4 remains blocked until R20.3 is **COMPLETE + NORMALIZED**.
