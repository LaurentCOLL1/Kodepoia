# R20 — Continuous Trusted Update Operations

Status: **PLANNING CANDIDATE**

Started: **2026-09-08**

Planning base: `main` `a5cb56fdf5993be3222b486fa80748f5aa339b71` — R19 is **COMPLETE + NORMALIZED** and frozen. No `R19.6` is authorized.

## Phase objective

Turn the R19 trusted self-update implementation into a sustainable production operation where an ordinary Kodepoia user can return after weeks or months, choose **Check for updates**, and receive the newest authorized version directly in the application without being exposed to TUF metadata maintenance or expiry ceremonies.

R20 keeps TUF expiry protections. It does **not** remove or bypass freshness checks. Instead it establishes safe automated renewal of the online roles while preserving offline custody of high-authority roles.

The intended steady state is:

- Root remains offline and threshold-protected;
- Targets remains offline and is used only when authorizing/changing release targets;
- Snapshot uses a dedicated online signing key;
- Timestamp uses a separate dedicated online signing key;
- scheduled automation refreshes Snapshot/Timestamp before expiry;
- GitHub Actions uses OIDC/federated short-lived credentials to a remote signer/KMS rather than long-lived cloud secrets;
- metadata publication is monotonic, atomic and rollback/freeze resistant;
- client UX treats an operational metadata outage as a temporary update-service failure, never as an application-startup failure;
- users do not have a practical time limit for when they may come back and update.

## Verified starting facts

- R19 is terminally **COMPLETE + NORMALIZED** on `main` `a5cb56fdf5993be3222b486fa80748f5aa339b71`.
- Public prerelease `v1.1.0-rc2` is authorized by production TUF Targets v2.
- Current release source: `18ee16173d12f34a3508ccc0ad1a9ce38e9ecd3e`.
- `KodepoiaSetup.exe` SHA-256: `a753ecef07757c3a8d6f97db4db7c77bece9d8129bdd0887eb7dea71d805ff8c`.
- Production Root v1 is user-custodied, threshold 2-of-3, and its private keys remain outside Git/repository/CI.
- Targets, Snapshot and Timestamp currently each use their own Ed25519 role key.
- Local custody recovery has been confirmed for all six current private-key files without committing or disclosing any passphrase.
- Targets v2 expires `2027-09-08T17:32:00Z`.
- Snapshot v2 and Timestamp v2 both expire `2026-09-09T17:32:00Z`.
- Kodepoia correctly rejects expired metadata with `status="metadata-expired"`; application startup remains independent of update-network success.

## External architecture constraints re-verified for planning

- TUF recommends distinct keys per role and permits Snapshot and Timestamp to use online keys for continuous delivery; Root and Targets should remain offline.
- Timestamp is intentionally frequently re-signed and short-lived so clients can detect freeze/staleness attacks.
- Snapshot gives clients a consistent view of Targets metadata and must remain version/hash/length bound to the actual Targets bytes.
- GitHub Actions OIDC can obtain short-lived cloud credentials without storing a long-lived cloud credential in GitHub Secrets. The cloud trust policy must restrict which repository/ref/environment may receive signing access.
- Remote KMS/HSM private keys must never be exportable into the repository runner. Only public key material, signatures and non-secret key identifiers may enter Git/CI evidence.

## Phase-wide governance and security boundaries

- R19 is frozen. R20 does not add or mutate any R19 subdivision.
- Never disable TUF expiry checks to improve availability.
- Never extend expiry to effectively infinite dates.
- Never put Root/Targets private keys, TUF passphrases, DPAPI vault material, cloud credentials or KMS private material into Git, Actions artifacts, logs, issues or continuity.
- Current Root/Targets custody remains offline unless a separately governed rotation explicitly changes that policy.
- Snapshot and Timestamp must use **different** online keys.
- Online role compromise must not authorize a new Targets file, a new Root, or arbitrary installer bytes.
- Metadata version numbers are monotonically increasing and publication must not create mixed Snapshot/Timestamp views.
- Scheduled refresh is idempotent: if metadata is fresh enough, it must not publish unnecessary versions.
- A cloud/KMS outage must not break normal Kodepoia startup or local work.
- All R20 branches require exact-head acceptance and expected-head merge protection, followed by one continuity-only normalization before the next subdivision starts.
- At any external provisioning/custody boundary (KMS creation, OIDC trust configuration, offline Root signature, provider billing/account action), stop before later subdivisions and provide exact user actions.

## Subdivision index

| ID | Title | Status | Manual intervention | Depends on |
| --- | --- | --- | --- | --- |
| R20.1 | Bridge Metadata Refresh & Custody-Safe Tooling | PLANNED | REQUIRED once, for local Snapshot/Timestamp signing | normalized R20 planning |
| R20.2 | Online Signer Abstraction & Rotation Package | PLANNED | NONE for provider-neutral implementation | R20.1 |
| R20.3 | OIDC/KMS Online-Key Provisioning & Root Rotation | PLANNED | REQUIRED for cloud/KMS provisioning and offline Root signatures | R20.2 |
| R20.4 | Scheduled Metadata Refresh & Atomic Publication | PLANNED | CONDITIONAL for repository environment/rules configuration | R20.3 |
| R20.5 | Expiry Monitoring, Alerting & Client UX Hardening | PLANNED | NONE after R20.4 | R20.4 |
| R20.6 | Long-Offline Client & Continuous-Operations Integrated Acceptance | PLANNED | CONDITIONAL for live incident/rotation drill | R20.1–R20.5 |

No subdivision may be silently inserted, removed, merged, split or renumbered. Any scope change requires an explicit roadmap + continuity change in a governed work cycle.

---

# R20.1 — Bridge Metadata Refresh & Custody-Safe Tooling

## Objective

Prevent an immediate update-service outage while R20 automation is being built, without weakening client verification or placing private keys into CI.

## In scope

- add repository-safe tooling that prepares and validates a bridge refresh of current Snapshot/Timestamp only;
- preserve Root v1 and Targets v2 byte-for-byte;
- produce Snapshot v3 referencing the exact current Targets v2 bytes;
- produce Timestamp v3 referencing the exact signed Snapshot v3 bytes;
- use a **temporary bridge expiry** long enough to complete R20.2–R20.4 without daily ceremonies, but explicitly shorter than Root/Targets lifetime and documented as transitional rather than steady-state policy;
- verify role keyids against the currently trusted Root before local signing;
- support local encrypted private-key custody without logging passphrases;
- generate a public-only output bundle suitable for repository integration;
- add acceptance that rejects version rollback, wrong role key, wrong Targets hash/length and accidental private material.

## Bridge policy

The bridge is a one-time operational exception, not the final automated policy:

- Targets remains v2 and is not re-signed;
- Snapshot becomes v3;
- Timestamp becomes v3;
- bridge expiry target: **30 days** from signing for Snapshot and Timestamp;
- after R20.4, automated online metadata returns to a short-lifetime policy with frequent renewal.

The 30-day bridge deliberately increases maximum freeze exposure during migration and therefore must not become the permanent policy.

## Manual intervention boundary

Repository implementation and tests require no private material. Once the bridge signing tool is ready, R20.1 stops and the user runs it locally against the existing encrypted Snapshot/Timestamp keys (or an approved local vault) and returns **only** the public signed Snapshot v3/Timestamp v3 bundle.

No Root or Targets private key should be needed for the bridge.

## Acceptance vetoes

- Root or Targets bytes change;
- Snapshot/ Timestamp version does not increase monotonically;
- Snapshot does not bind current Targets v2 exact hash/length/version;
- Timestamp does not bind exact signed Snapshot v3 hash/length/version;
- any private key/passphrase/vault material enters repository-safe output;
- bridge metadata is accepted after expiry.

---

# R20.2 — Online Signer Abstraction & Rotation Package

## Objective

Implement a provider-neutral remote signing contract and generate all **public** material needed to rotate Snapshot/Timestamp to dedicated online keys without yet requiring a live cloud account.

## In scope

- define a signer interface capable of signing TUF canonical payload bytes with non-exportable asymmetric keys;
- define public key discovery/import and TUF keyid derivation;
- provide deterministic in-memory/synthetic signer fixtures for CI only;
- define provider configuration by non-secret resource identifiers rather than private key bytes;
- create a Root-rotation package builder that accepts new Snapshot/Timestamp public keys and prepares unsigned Root v2 payload/evidence for offline signing;
- verify old Root v1 -> new Root v2 sequential rotation requirements;
- ensure new Snapshot/Timestamp roles remain separate and threshold 1 each;
- keep Root and Targets policies offline.

## Manual intervention

**NONE** for provider-neutral code and synthetic acceptance. R20.2 must stop before creating a live cloud/KMS key or changing production Root.

---

# R20.3 — OIDC/KMS Online-Key Provisioning & Root Rotation

## Objective

Provision dedicated non-exportable online Snapshot/Timestamp keys, authorize GitHub Actions through OIDC, and rotate production Root sequentially so clients trust those new role keys.

## Provider requirements

A selected provider must support:

- asymmetric signing suitable for TUF (Ed25519 preferred where supported);
- non-exportable private keys;
- public-key retrieval;
- auditable signing operations;
- narrowly scoped IAM;
- GitHub Actions OIDC/federated authentication without long-lived cloud credentials in GitHub Secrets.

AWS KMS and Google Cloud KMS both currently document Ed25519 asymmetric-signing support and are candidate reference providers. Selection is deferred until R20.3 provisioning so the repository remains provider-neutral through R20.2.

## Required live rotation flow

1. Provision dedicated Snapshot and Timestamp online signing keys in KMS/HSM.
2. Configure GitHub OIDC trust restricted to `LaurentCOLL1/Kodepoia` and the authorized workflow/environment/ref policy.
3. Retrieve and verify public keys/keyids.
4. Build Root v2 replacing only Snapshot/Timestamp role keyids while preserving Root/Targets policy.
5. Sign Root v2 with at least the current Root v1 threshold (2-of-3) using offline user custody.
6. Ensure Root v2 also satisfies its own Root threshold.
7. Publish Root v2 only after exact verification.
8. Sign initial Snapshot/Timestamp with the new online keys and verify client transition from Root v1.

## Manual intervention boundary

**REQUIRED.** Cloud account/provider choice, KMS creation, billing/region selection, OIDC trust policy creation and offline Root signing are external privileged effects. Stop at that boundary with exact commands/console steps. Never request the user's private Root files or passphrases.

---

# R20.4 — Scheduled Metadata Refresh & Atomic Publication

## Objective

Keep online metadata continuously fresh without user intervention while preserving monotonicity and atomic repository views.

## In scope

- scheduled and manual-dispatch workflow using OIDC and the R20.3 online signer;
- refresh only when remaining lifetime falls below policy threshold;
- version monotonicity under concurrent/superseded workflow runs;
- Snapshot generated from the exact current Targets bytes;
- Timestamp generated only after the exact final Snapshot bytes are signed;
- publication ordering and concurrency control preventing mixed metadata views;
- no rebuilding or mutation of release assets during freshness refresh;
- short-lived steady-state metadata with operational margin and alerting;
- Actions permissions remain least privilege; OIDC `id-token: write` is used only for token minting and does not itself grant repository/cloud write access.

## Steady-state policy candidate

Subject to acceptance and outage testing:

- scheduled check every **6 hours**;
- Timestamp expiry target **48 hours**;
- Snapshot expiry target **72 hours**;
- refresh before remaining lifetime reaches **24 hours**;
- no new metadata version when sufficient lifetime remains;
- separate Snapshot and Timestamp KMS keys.

This trades a bounded freeze window for resilience to a missed schedule while keeping metadata short-lived relative to Targets/Root.

## Manual intervention

Conditional only for repository environment/protection configuration not available through connected tooling.

---

# R20.5 — Expiry Monitoring, Alerting & Client UX Hardening

## Objective

Make operational failures visible to maintainers but non-destructive and understandable to users.

## In scope

- CI monitor for remaining Root/Targets/Snapshot/Timestamp lifetime;
- warning and critical thresholds;
- fail/alert before user-facing expiry;
- explicit evidence when scheduled refresh did not run or KMS signing failed;
- update UI maps metadata expiry/refresh outage to a localized temporary-service message;
- application startup and offline/local work remain unaffected;
- no fallback that accepts expired or unverifiable metadata;
- operator runbook for emergency manual refresh and KMS outage.

## Manual intervention

**NONE** after online signer exists.

---

# R20.6 — Long-Offline Client & Continuous-Operations Integrated Acceptance

## Objective

Prove the operational promise that a user can return long after installation and still update safely without understanding or managing TUF expiry.

## Required acceptance matrix

- client state persisted from an older release remains valid after simulated weeks/months offline;
- on return, client fetches a fresh Timestamp/Snapshot and sees the current authorized Targets candidate;
- no dependence on the age of the local installation itself;
- expired server metadata is rejected;
- old-but-correctly-signed Timestamp replay is rejected after newer trusted state;
- Snapshot/Targets mix-and-match is rejected;
- KMS outage yields a temporary update-service failure, not startup failure;
- scheduled refresh recovers after transient outage;
- concurrent refresh workflows cannot regress versions;
- compromised Timestamp key cannot authorize a new Targets file;
- compromised Snapshot key cannot authorize arbitrary target bytes;
- Root/Targets offline keys remain absent from Actions/runtime;
- rotation of one online role can be performed without changing target authorization;
- emergency manual refresh runbook is tested;
- update UX remains localized and non-destructive;
- installed user settings/projects survive normal update flow.

## Manual intervention

Conditional for a live key-rotation/incident drill if provider policy requires explicit privileged approval.

---

## Planning acceptance / Definition of Done

Before R20.1 starts:

- this roadmap and `docs/continuity/KODEPOIA_CONTINUITY_R20.md` exist on a dedicated planning branch from exact normalized R19 `main`;
- R19 remains frozen and no `R19.6` is introduced;
- R0 Repository Guard passes on the exact planning HEAD on Ubuntu + Windows;
- full Python Core acceptance passes on the exact planning HEAD;
- KodeStudio UI Smoke passes on the exact planning HEAD;
- planning PR is merged with exact expected-head protection;
- one continuity-only post-merge planning normalization is gated and merged;
- only then is R20.1 START-sync authorized.

## Rollback / recovery

- Planning changes are documentation-only and may be reverted without touching R19 runtime/release state.
- R20.1 bridge metadata must always remain recoverable by republishing a newer correctly signed version; never roll metadata version numbers backward.
- R20.3 Root rotation must be sequential and dual-authorized according to TUF Root update rules; if its acceptance fails, Root v1 remains authoritative and no online key is trusted.
- R20.4 automation must be disable-able without invalidating installed Kodepoia; emergency local signing remains a documented recovery path.

## Terminal rule

R20 is not complete until R20.6 and its unique continuity normalization merge. No `R20.7` is authorized by this plan.
