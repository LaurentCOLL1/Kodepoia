# R20 — Continuous Trusted Update Operations

Status: **ACTIVE**

Started: **2026-09-08**

Planning base: `main` `a5cb56fdf5993be3222b486fa80748f5aa339b71` — R19 is **COMPLETE + NORMALIZED** and frozen. No `R19.6` is authorized.

## Phase objective

Turn the R19 trusted self-update implementation into a sustainable production operation where an ordinary Kodepoia user can return after weeks or months, choose **Check for updates**, and receive the newest authorized version directly in the application without being exposed to TUF metadata maintenance or expiry ceremonies.

R20 keeps TUF expiry protections. It does **not** remove or bypass freshness checks. Instead it establishes safe automated renewal of the online roles while preserving offline custody of high-authority roles.

A phase-wide product constraint is now explicit: **Kodepoia must remain zero-cost to create and zero-cost to use. No paid cloud/KMS/HSM subscription may be a mandatory dependency.** Optional external hardened signers may remain supported, but the reference path must work on GitHub Free with the public repository.

The intended steady state is:

- Root remains offline and threshold-protected;
- Targets remains offline and is used only when authorizing/changing release targets;
- Snapshot uses a dedicated online signing key;
- Timestamp uses a separate dedicated online signing key;
- scheduled automation refreshes Snapshot/Timestamp before expiry;
- the zero-cost reference backend stores the two low-authority online Ed25519 seeds as separate GitHub Actions environment secrets and loads them only into ephemeral GitHub-hosted runners;
- optional remote KMS/HSM backends remain compatible with the provider-neutral R20.2 signer interface but are never required;
- metadata publication is monotonic, atomic and rollback/freeze resistant;
- client UX treats an operational signing/update outage as a temporary update-service failure, never as an application-startup failure;
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
- Production bridge Snapshot v3 and Timestamp v3 both expire `2026-10-08T21:44:18Z`.
- Kodepoia correctly rejects expired metadata with `status="metadata-expired"`; application startup remains independent of update-network success.
- R20.2 is **COMPLETE + NORMALIZED** on `main` `02ae599f951f353d9647e5cb6ca39f28eb655cbf` and provides the provider-neutral signer + Root rotation package contract.
- R20.3 local online-key generation is complete: accepted public ZIP SHA-256 `4b26dbf702f93e1c2e6f813eae7c22771a06e97fd9d77bd6d57bff1b6c22b1db`.
- Accepted Snapshot replacement keyid: `fac1c790b4d6dbeb04ca4a803bd80e6fde19127fc7ada34003cef5d6b50506d8`.
- Accepted Timestamp replacement keyid: `8d81006fd9de63660d74c43b6926ed664b2e9f1bdf81a9556367232533d5a2ad`.
- Accepted unsigned Root v2 SHA-256: `7ae909722149fe7f05380f93b7317c99347f8b3c1d102b7b6ddca64bbe1bbe1d`; it has no production effect until the governed offline ceremony and complete online-role transition are accepted.

## External architecture constraints re-verified for R20.3

- TUF recommends distinct keys per role and permits Snapshot and Timestamp to use online keys for continuous delivery; Root and Targets remain offline.
- Timestamp is intentionally frequently re-signed and short-lived so clients can detect freeze/staleness attacks.
- Snapshot gives clients a consistent view of Targets metadata and must remain version/hash/length bound to the actual Targets bytes.
- GitHub documents that standard GitHub-hosted runners are free and unlimited for public repositories.
- GitHub Actions secrets are encrypted before reaching GitHub and are exposed to a workflow only when explicitly referenced.
- GitHub Free supports environment secrets for public repositories; an environment can also restrict which branches may deploy/use those secrets.
- The zero-cost reference path therefore uses two distinct GitHub environment secrets for Snapshot/Timestamp and ephemeral GitHub-hosted runners. The secrets are low-authority online-role keys only; Root/Targets private material remains prohibited from GitHub Actions.
- Optional external KMS/HSM signers may be added later without changing TUF metadata semantics, but they are not a prerequisite for any Kodepoia user or maintainer.

## Phase-wide governance and security boundaries

- R19 is frozen. R20 does not add or mutate any R19 subdivision.
- Never disable TUF expiry checks to improve availability.
- Never extend expiry to effectively infinite dates.
- Never require a paid cloud/KMS/HSM account to build, maintain, distribute or use Kodepoia.
- Never put Root/Targets private keys, TUF passphrases, DPAPI vault material or private online-key bytes into Git, Actions artifacts, logs, issues or continuity.
- Current Root/Targets custody remains offline unless a separately governed rotation explicitly changes that policy.
- Snapshot and Timestamp must use **different** online keys and different secret names.
- The GitHub-secret reference backend may materialize each low-authority key only in process memory on an ephemeral GitHub-hosted runner; repository files/artifacts must never contain the secret value.
- Online role compromise must not authorize a new Targets file, a new Root, or arbitrary installer bytes.
- Metadata version numbers are monotonically increasing and publication must not create mixed Snapshot/Timestamp views.
- Scheduled refresh is idempotent: if metadata is fresh enough, it must not publish unnecessary versions.
- A GitHub Actions/signing-backend outage must not break normal Kodepoia startup or local work.
- All R20 branches require exact-head acceptance and expected-head merge protection, followed by one continuity-only normalization before the next subdivision starts.
- At any private-key provisioning/custody boundary (generation of online seeds, GitHub environment-secret creation, offline Root signature), stop before later subdivisions and provide exact user actions.

## Subdivision index

| ID | Title | Status | Manual intervention | Depends on |
| --- | --- | --- | --- | --- |
| R20.1 | Bridge Metadata Refresh & Custody-Safe Tooling | **COMPLETE + NORMALIZED** | COMPLETE — local Snapshot/Timestamp bridge signing performed | normalized R20 planning |
| R20.2 | Online Signer Abstraction & Rotation Package | **COMPLETE + NORMALIZED** | NONE — provider-neutral implementation only | R20.1 |
| R20.3 | Zero-Cost Online-Key Provisioning & Root Rotation | **IN PROGRESS** | PARTIAL — online-key generation COMPLETE; GitHub environment secrets + offline Root 2-of-3 + initial v4/v4 transition REQUIRED | R20.2 |
| R20.4 | Scheduled Metadata Refresh & Atomic Publication | PLANNED | CONDITIONAL for repository environment/rules configuration | R20.3 |
| R20.5 | Expiry Monitoring, Alerting & Client UX Hardening | PLANNED | NONE after R20.4 | R20.4 |
| R20.6 | Long-Offline Client & Continuous-Operations Integrated Acceptance | PLANNED | CONDITIONAL for live incident/rotation drill | R20.1–R20.5 |

No subdivision may be silently inserted, removed, merged, split or renumbered. This R20.3 title/scope revision is an explicit governed roadmap change preserving subdivision number and dependency order while enforcing the zero-cost product constraint.

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

Implement a provider-neutral signing contract and generate all **public** material needed to rotate Snapshot/Timestamp to dedicated online keys without requiring a specific paid provider.

## In scope

- define a signer interface capable of signing TUF canonical payload bytes;
- define public key discovery/import and TUF keyid derivation;
- provide deterministic in-memory/synthetic signer fixtures for CI only;
- define provider configuration by non-secret resource identifiers rather than private key bytes;
- create a Root-rotation package builder that accepts new Snapshot/Timestamp public keys and prepares unsigned Root v2 payload/evidence for offline signing;
- verify old Root v1 -> new Root v2 sequential rotation requirements;
- ensure new Snapshot/Timestamp roles remain separate and threshold 1 each;
- keep Root and Targets policies offline.

## Manual intervention

**NONE** for provider-neutral code and synthetic acceptance. R20.2 is complete and normalized.

---

# R20.3 — Zero-Cost Online-Key Provisioning & Root Rotation

## Objective

Provision dedicated Snapshot/Timestamp online Ed25519 keys without a paid service, store only those two low-authority private seeds as separate GitHub Actions environment secrets, and rotate production Root sequentially so clients trust the new public role keys.

## Zero-cost reference backend

The mandatory/reference backend is GitHub-only:

- repository remains public;
- standard GitHub-hosted runners are used;
- environment name: `tuf-production-signing`;
- secret `TUF_SNAPSHOT_ED25519_SEED_B64` contains only the Snapshot 32-byte Ed25519 private seed encoded as base64;
- secret `TUF_TIMESTAMP_ED25519_SEED_B64` contains only the Timestamp 32-byte Ed25519 private seed encoded as base64;
- public keys/keyids are repository-safe evidence;
- secret values are loaded directly into process memory and are never written to repository files or uploaded artifacts;
- Root and Targets private keys/passphrases are never GitHub secrets and never enter a runner;
- optional KMS/HSM implementations remain supported by the R20.2 interface but are out of the mandatory/free path.

## Accepted public online-key material

The local generation boundary is **COMPLETE** and only public evidence was returned:

- public package SHA-256: `4b26dbf702f93e1c2e6f813eae7c22771a06e97fd9d77bd6d57bff1b6c22b1db`;
- Snapshot replacement keyid: `fac1c790b4d6dbeb04ca4a803bd80e6fde19127fc7ada34003cef5d6b50506d8`;
- Timestamp replacement keyid: `8d81006fd9de63660d74c43b6926ed664b2e9f1bdf81a9556367232533d5a2ad`;
- unsigned Root v2 SHA-256: `7ae909722149fe7f05380f93b7317c99347f8b3c1d102b7b6ddca64bbe1bbe1d`;
- Root v1 and Targets role policy are preserved;
- unsigned Root v2 has no production effect.

## Required live rotation flow

1. **COMPLETE** — generate two new and distinct Ed25519 online seeds locally with repository-provided tooling.
2. **COMPLETE** — produce and validate a public-only key package containing Snapshot/Timestamp public keys, keyids and fingerprints.
3. Store the two base64 private seeds as separate secrets in GitHub environment `tuf-production-signing`; restrict the environment to the `main` branch where GitHub settings permit it.
4. Use the exact accepted unsigned Root v2, replacing only Snapshot/Timestamp role keyids while preserving Root/Targets policy.
5. Sign Root v2 with at least the current Root v1 threshold (2-of-3) using offline user custody and verify that Root v2 also satisfies its own Root threshold.
6. In the same controlled local ceremony, sign Snapshot v4 and Timestamp v4 with the new online keys. Snapshot v4 must bind exact Targets v2 bytes; Timestamp v4 must bind exact signed Snapshot v4 bytes.
7. Preserve the existing bridge expiry `2026-10-08T21:44:18Z` for the initial v4/v4 transition; the key rotation must not silently extend the temporary bridge lifetime.
8. Treat Root v2 + Snapshot v4 + Timestamp v4 as one governed transition package. **Never publish Root v2 alone while Snapshot/Timestamp are still signed by the old keys.**
9. Integrate and exact-head verify the complete transition package before merging R20.3.
10. After the accepted R20.3 merge reaches `main`, run the manual no-publication GitHub environment-secret signing challenge. It must verify both live secret identities against the committed public keys without modifying repository metadata.
11. Only after the live challenge and the unique R20.3 continuity normalization may R20.4 begin scheduled refresh implementation.

## Manual intervention boundary

**PARTIAL / REQUIRED.** Online key generation is complete. The remaining privileged actions are:

- create/update GitHub environment `tuf-production-signing` and its two online-role secrets without exposing their values;
- perform the exact offline Root v2 2-of-3 ceremony locally;
- immediately use the locally retained new Snapshot/Timestamp seeds to build the public Root v2 + Snapshot v4 + Timestamp v4 transition package;
- return only that public transition package for repository integration.

The repository tooling must discover Root custody keys by Root-authorized public keyid rather than relying on a private filename convention, and must never record private paths or passphrases in public output.

No paid provider account, billing setup, cloud region or OIDC trust is required by the reference path.

---

# R20.4 — Scheduled Metadata Refresh & Atomic Publication

## Objective

Keep online metadata continuously fresh without user intervention while preserving monotonicity and atomic repository views.

## In scope

- scheduled and manual-dispatch workflow using the R20.3 zero-cost online signer backend;
- environment secrets are referenced only by the signing job and only on the authorized branch/environment;
- refresh only when remaining lifetime falls below policy threshold;
- version monotonicity under concurrent/superseded workflow runs;
- Snapshot generated from the exact current Targets bytes;
- Timestamp generated only after the exact final Snapshot bytes are signed;
- publication ordering and concurrency control preventing mixed metadata views;
- no rebuilding or mutation of release assets during freshness refresh;
- short-lived steady-state metadata with operational margin and alerting;
- Actions permissions remain least privilege; no OIDC `id-token: write` permission is required by the GitHub-secret reference backend;
- optional external signer backends may use OIDC independently, without changing the mandatory free path.

## Steady-state policy candidate

Subject to acceptance and outage testing:

- scheduled check every **6 hours**;
- Timestamp expiry target **48 hours**;
- Snapshot expiry target **72 hours**;
- refresh before remaining lifetime reaches **24 hours**;
- no new metadata version when sufficient lifetime remains;
- separate Snapshot and Timestamp online keys/secrets.

This trades a bounded freeze window for resilience to a missed schedule while keeping metadata short-lived relative to Targets/Root.

## Manual intervention

Conditional only for GitHub environment/protection configuration not available through connected tooling.

---

# R20.5 — Expiry Monitoring, Alerting & Client UX Hardening

## Objective

Make operational failures visible to maintainers but non-destructive and understandable to users.

## In scope

- CI monitor for remaining Root/Targets/Snapshot/Timestamp lifetime;
- warning and critical thresholds;
- fail/alert before user-facing expiry;
- explicit evidence when scheduled refresh did not run or signing failed;
- update UI maps metadata expiry/refresh outage to a localized temporary-service message;
- application startup and offline/local work remain unaffected;
- no fallback that accepts expired or unverifiable metadata;
- operator runbook for emergency manual refresh and GitHub Actions/signing-backend outage.

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
- GitHub Actions/signing-backend outage yields a temporary update-service failure, not startup failure;
- scheduled refresh recovers after transient outage;
- concurrent refresh workflows cannot regress versions;
- compromised Timestamp key cannot authorize a new Targets file;
- compromised Snapshot key cannot authorize arbitrary target bytes;
- Root/Targets offline keys remain absent from Actions/runtime;
- rotation of one online role can be performed without changing target authorization;
- emergency manual refresh runbook is tested;
- update UX remains localized and non-destructive;
- installed user settings/projects survive normal update flow;
- the complete mandatory operational path remains usable without any paid infrastructure service.

## Manual intervention

Conditional for a live key-rotation/incident drill if explicit privileged approval is required.

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
- R20.3 Root rotation must be sequential and dual-authorized according to TUF Root update rules; if its acceptance fails, Root v1 remains authoritative and no new online key is trusted.
- R20.3 must not expose a transient repository state where Root v2 is trusted but Snapshot/Timestamp still require the revoked v1 online-role keys; the first v4/v4 generation is part of the same governed transition.
- R20.4 automation must be disable-able without invalidating installed Kodepoia; emergency local signing remains a documented recovery path.
- If the GitHub-secret backend is unavailable or later deemed insufficient, the provider-neutral R20.2 interface allows migration to an optional external signer without making that provider mandatory for Kodepoia.

## Terminal rule

R20 is not complete until R20.6 and its unique continuity normalization merge. No `R20.7` is authorized by this plan.
