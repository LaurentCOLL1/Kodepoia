# KODEPOIA CONTINUITY — R19

**Status:** **R19 COMPLETE + NORMALIZED**

This file is the terminal continuation authority for **R19 — Installed Experience & Trusted Self-Update Hardening**. All five authorized subdivisions R19.1 through R19.5 are implemented, accepted and merged. This unique R19.5 continuity-only normalization is the terminal R19 change. **No R19.6 is authorized.**

## Frozen inherited authority

- Repository: `LaurentCOLL1/Kodepoia`.
- R18 remains **COMPLETE + NORMALIZED** and frozen at R18.11. No `R18.12` is authorized.
- Historical public prerelease `v1.1.0-rc1` remains immutable at source `c64bac012ef3afa332526a539901b11428fd966f`, installer SHA-256 `3d11af229392a6756a2bbc161af0150aca92168d843a42a3944ab5c01660b8e0`, `production_signed=false`.
- Corrective public prerelease `v1.1.0-rc2` is the current R19 release authority. Its accepted release source is `18ee16173d12f34a3508ccc0ad1a9ce38e9ecd3e`, installer SHA-256 `a753ecef07757c3a8d6f97db4db7c77bece9d8129bdd0887eb7dea71d805ff8c`, length `37613254`, `production_signed=false`.
- Published release assets must never be replaced in place as a normal update mechanism.

## R19 planning authority

Formal phase: **R19 — Installed Experience & Trusted Self-Update Hardening**.

Roadmap authority: `docs/roadmap/R19_PLAN.md`.

Planning PR #408 merged as `main` `c1e8dd2848c0a57a6a4f6c59082cdc111f155df1` after exact-head R0, Python Core and KodeStudio UI acceptance.

Unique planning-normalization PR #409 merged as normalized planning `main` `c586e7f6cfd175c5c6fd81574b3a1b3dd43cee6d` after fresh exact-head R0 Repository Guard, Python Core and KodeStudio UI Smoke. That normalization authorized R19.1.

## Authorized subdivision sequence — CLOSED

1. R19.1 — Language Switching Hardening
2. R19.2 — Production/Beta Update Repository Bootstrap
3. R19.3 — Network UpdateTransport & Packaged Startup Wiring
4. R19.4 — Seamless Windows In-App Update
5. R19.5 — Corrective RC Release Automation & Integrated Acceptance

All five subdivisions are complete. No subdivision may be silently inserted, removed, merged, split or renumbered, and **no R19.6 may be started**.

## R19.1 accepted authority

- Implementation branch: `r19/01-language-switching-hardening`.
- Accepted exact implementation HEAD: `f8bb810f459d0af35673e3bb80789e1109dfbb80`.
- PR #410 merged with `expected_head_sha=f8bb810f459d0af35673e3bb80789e1109dfbb80` as `main` `717b2cc0efd4c59100c5145dd8916c21787137c7`.
- R0 Repository Guard #2576: **SUCCESS** Ubuntu + Windows.
- Python Core #2548: **SUCCESS** Ubuntu + Windows; package-build and KodeStudio evidence passed.
- KodeStudio UI Smoke #2513: **SUCCESS**.
- R18.7 Update Discovery Channel UX #77: **SUCCESS** Ubuntu + Windows.
- R15.15 CLI KodeStudio UX #250: **SUCCESS**.

Accepted behavior includes merge-safe preferences, persisted locale precedence, controlled language apply/restart, strict English/French v1.1 catalogs, completed French runtime coverage and regression coverage for preference/locale/UI behavior.

Manual intervention for R19.1: **NONE**.

### R19.1 post-merge continuity normalization

- Branch: `r19/01-continuity-normalization`.
- Accepted exact normalization HEAD: `eb2cb73e468819850289a3174afcb99bb5c0438d`.
- PR #411 merged with exact-head protection as normalized `main` `fd7736adc565c3c3cb169d8223c5841e86bbbe9d`.
- No second R19.1 continuity normalization is authorized.

## R19.2 accepted authority

- Implementation branch: `r19/02-update-repository-bootstrap`.
- Accepted exact implementation HEAD: `356d0b29521155ef06c03e3342336532ac1dd0f1`.
- PR #412 merged with exact-head protection as `main` `59bb064127b16c1374493ad8f3e0e7b48d23aab5`.
- R19.2 Production/Beta Update Repository Bootstrap Acceptance #29: **SUCCESS** Ubuntu + Windows.
- R0 Repository Guard #2587: **SUCCESS** Ubuntu + Windows.
- Python Core #2559: **SUCCESS** Ubuntu + Windows; package-build and KodeStudio evidence passed.
- KodeStudio UI Smoke #2524: **SUCCESS**.
- R16.9 Supply Chain Provenance Acceptance #208: **SUCCESS** Ubuntu + Windows.

R19.2 established the production/beta TUF repository contract, separate role keys, Root threshold policy, canonical HTTPS metadata layout, synthetic-root separation, exact packaged/public Root equality and the private-key exclusion boundary. The original public bootstrap Root was later superseded before first R19 public distribution by the retained user-custodied Root adopted in R19.5.

Manual intervention for R19.2: **NONE required to finalize the repository subdivision**.

### R19.2 post-merge continuity normalization

- Branch: `r19/02-continuity-normalization`.
- Accepted exact normalization HEAD: `07a867afe06604f1795cde7cafc7a08206321ef9`.
- PR #413 merged as normalized `main` `5790004ed4fd5ec9679adbf8a3c8e4d599744683`.
- No second R19.2 continuity normalization is authorized.

## R19.3 accepted authority

- Implementation branch: `r19/03-network-update-transport`.
- Accepted exact implementation HEAD: `d3c1364b5d7f4015a7205f16f0158e301c5c2e81`.
- PR #414 merged with exact-head protection as `main` `e74426844d661c7a6c1debc8823a137a03a0ce69`.
- R19.3 Network UpdateTransport Acceptance #7: **SUCCESS** Ubuntu + Windows.
- R0 Repository Guard #2597: **SUCCESS** Ubuntu + Windows.
- Python Core #2569: **SUCCESS** Ubuntu + Windows; package-build and integrated KodeStudio evidence passed.
- KodeStudio UI Smoke #2534: **SUCCESS**.
- R16.9 Supply Chain Provenance Acceptance #215: **SUCCESS** Ubuntu + Windows.

Accepted behavior includes bounded HTTPS-only TUF/target transport, explicit timeouts and byte ceilings, redirect confinement, deterministic offline errors, canonical GitHub Release target URLs, packaged startup with local production Root loading and no startup network dependency, injected discovery/install services and truthful Windows verification behavior.

Manual intervention for R19.3: **NONE**.

### R19.3 post-merge continuity normalization

- Branch: `r19/03-continuity-normalization`.
- Accepted exact normalization HEAD: `e8c2c69f084d52590c4e0926b8c338e777abc09d`.
- PR #415 merged as normalized `main` `3f25b51f0c9f619b859cd588908d0ecb04a4875c`.
- No second R19.3 continuity normalization is authorized.

## R19.4 accepted authority

- Implementation branch: `r19/04-seamless-windows-in-app-update`.
- Accepted exact implementation HEAD: `86384155aed8dd1e536669c94b2e5958b7096d22`.
- PR #416 merged with exact-head protection as `main` `d8f365cc1abd585cd5a603d7f50e53cbaeb8416f`.
- R19.4 Seamless Windows In-App Update Acceptance #3: **SUCCESS** Ubuntu + Windows.
- R0 Repository Guard #2603: **SUCCESS** Ubuntu + Windows.
- Python Core #2575: **SUCCESS** Ubuntu + Windows; package-build and integrated KodeStudio evidence passed.
- KodeStudio UI Smoke #2540: **SUCCESS**.
- R16.9 Supply Chain Provenance Acceptance #217: **SUCCESS** Ubuntu + Windows.

Accepted behavior includes pre-handoff installer revalidation, fixed Inno Setup self-update arguments, explicit consent preservation, safe application exit only after successful handoff, governed original-user relaunch, local post-relaunch reconciliation and fail-closed handling of altered payloads or launch failure.

Historical note: frozen R16.17/R16.18 v1.0 assertions may fail on v1.1 identity; they are historical compatibility evidence, not R19.4/R19.5 promotion authority.

Manual intervention for R19.4: **NONE**.

### R19.4 post-merge continuity normalization — ACCEPTED

- Base `main`: `d8f365cc1abd585cd5a603d7f50e53cbaeb8416f`.
- Branch: `r19/04-continuity-normalization`.
- Accepted exact normalization HEAD: `0c358cf033446ad1aefd5ec9bdf065523b4c1ead`.
- PR #417 merged with exact-head protection as normalized `main` `54c79340a07f2d237bfef061b1df93d2a66072be`.
- Fresh R0 Repository Guard #2605: **SUCCESS** Ubuntu + Windows.
- Fresh Python Core #2577: **SUCCESS** Ubuntu + Windows with package-build/UI evidence.
- Fresh KodeStudio UI Smoke #2542: **SUCCESS**.
- No second R19.4 continuity normalization is authorized.

That normalized `main` authorized R19.5.

## R19.5 accepted authority — FINAL SUBDIVISION

- Implementation branch: `r19/05-corrective-rc-release-automation`.
- Final accepted exact implementation/finalization HEAD: `4ed914d5454bc7434fd61e0eeefe8f27ec8745c6`.
- PR #418 merged with `expected_head_sha=4ed914d5454bc7434fd61e0eeefe8f27ec8745c6` as `main` `ee0c9227b2276cb72ceb89ee0a5e6f98a6bdf2b6`.
- Release source that produced the accepted installer: `18ee16173d12f34a3508ccc0ad1a9ce38e9ecd3e`.
- Immutable Actions artifact source: workflow run `34249968626`, artifact `10066516267`, artifact ZIP SHA-256 `ec326d6549b7d63cbe874d9d8c656162fec8ce49c914c320fa08b295567f1172`.

### Final accepted-head evidence

On exact HEAD `4ed914d5454bc7434fd61e0eeefe8f27ec8745c6`:

- R19.5 Corrective RC Release Integrated Acceptance #28: **SUCCESS** — Ubuntu contract, Windows contract and final immutable release-artifact replay all passed. The acceptance verifies the live public GitHub prerelease/tag/assets in read-only mode in addition to TUF and artifact evidence.
- R16.9 Supply Chain Provenance Acceptance #245: **SUCCESS** Ubuntu + Windows.
- R0 Repository Guard #2634: **SUCCESS** Ubuntu + Windows.
- Python Core #2606: **SUCCESS** Ubuntu + Windows; package-build Ubuntu/Windows and integrated KodeStudio UI evidence passed.
- KodeStudio UI Smoke #2571: **SUCCESS**.
- R19.2 Production/Beta Update Repository Bootstrap Acceptance #61: **SUCCESS** Ubuntu + Windows.
- R19.3 Network UpdateTransport Acceptance #38: **SUCCESS** Ubuntu + Windows.
- R19.4 Seamless Windows In-App Update Acceptance #31: **SUCCESS** Ubuntu + Windows.

Historical R16.17/R16.18 and R18.9 failures tied to older frozen v1.0/rc1 assumptions remain non-authoritative noise and do not replace the explicit R19.5 promotion contract above.

### User-custodied production TUF authority

R19.5 completed a real local custody ceremony outside Git. **Private TUF keys and their passphrase remain exclusively under user custody and must never enter Git, CI, release assets, logs, continuity or chat.** Only public signed material is committed.

Adopted production Root v1:

- SHA-256 `892442754966aa643bbe15a2910aa3fef59032c8f5eade34fed62efd96aefee5`;
- Root threshold 2-of-3;
- three independent Root Ed25519 keys;
- distinct Targets, Snapshot and Timestamp role keys.

Final production role metadata:

- Targets v2 SHA-256 `0b65bf34e50d43ed1f82f0f4a17875fb0a4bb597ed5b6066749dc9352e504e3f`;
- Snapshot v2 SHA-256 `176d8b75f0f7b1b53a706640581a2b34cea4dac2fda36cf729c0616066906b4b`;
- Timestamp v2 SHA-256 `2586981d4a50af8140457edcc5e0fb70a089ccf200b0acecc8113c3e40283093`;
- all Root/role signatures, thresholds, versions, expirations and Snapshot→Targets / Timestamp→Snapshot length/hash bindings passed R19.5 acceptance.

The release target is exactly:

`channels/beta/windows-x86_64/1.1.0-rc2/18ee16173d12f34a3508ccc0ad1a9ce38e9ecd3e/KodepoiaSetup.exe`

### Public corrective prerelease authority

Public GitHub prerelease:

- tag: `v1.1.0-rc2`;
- annotated tag object: `4e61faa78e16c89d3f87ce4c7860560017841394`;
- tag target commit: `18ee16173d12f34a3508ccc0ad1a9ce38e9ecd3e`;
- GitHub Release ID: `384982066`;
- prerelease: `true`; draft: `false`;
- published at `2026-09-08T18:49:01Z`.

Published assets:

- `KodepoiaSetup.exe` — asset `551092693`, length `37613254`, SHA-256 `a753ecef07757c3a8d6f97db4db7c77bece9d8129bdd0887eb7dea71d805ff8c`;
- `installer-manifest.json` — asset `551092694`, length `508`, SHA-256 `83d5c1bebdacba8cb9cf2f59e3cabd3af6cb72ddb842e16313e6cbc51f7ee8d8`;
- `R19_5_RELEASE_HANDOFF.json` — asset `551092695`, length `1589`, SHA-256 `3d8b32af73233f19e9ed3c8f7ad1389e882aefc062038348e566eb1b4e5d01a5`.

`production_signed=false` is intentional and truthful: R19.5 does not claim production Authenticode. TUF remains the update authorization authority.

### Manual interventions completed for R19.5

The genuine manual boundaries were completed successfully:

1. local generation/custody of encrypted production TUF private keys outside Git;
2. local signing/re-signing of Targets v2 → Snapshot v2 → Timestamp v2 using retained custody keys;
3. push of annotated tag `v1.1.0-rc2` to the accepted release-source commit;
4. explicit publication of GitHub prerelease `v1.1.0-rc2` with the three exact accepted assets.

No private key, passphrase or GitHub token was committed or uploaded as release evidence.

## R19.5 post-merge continuity normalization — TERMINAL

- Base `main`: `ee0c9227b2276cb72ceb89ee0a5e6f98a6bdf2b6`.
- Branch: `r19/05-continuity-normalization`.
- This is the **single authorized continuity-only normalization after R19.5**.
- It changes only `docs/continuity/KODEPOIA_CONTINUITY_R19.md`.
- It must pass fresh exact-head R0 Repository Guard Ubuntu + Windows, full Python Core and KodeStudio UI Smoke before merge.
- It must merge with exact expected-head protection.
- Once this exact normalization merges into `main`, R19 is **COMPLETE + NORMALIZED** and frozen. No second R19.5 normalization and no R19.6 are authorized.

## R19 closure

R19 closes the authorized defects/work items in its formal scope:

- R19.1 closes language switching/persistence and complete FR/EN runtime hardening;
- R19.2 closes update repository/bootstrap trust structure;
- R19.3 closes bounded network UpdateTransport and packaged startup wiring;
- R19.4 closes verified Windows in-app handoff/shutdown/relaunch coordination;
- R19.5 closes corrective rc2 identity, retained production TUF custody, exact signed metadata, real rc1→rc2 installed upgrade proof and governed public prerelease publication.

There is **no remaining authorized R19 subdivision**.

## Security and operational invariants after R19

- Never embed private TUF/AuthentiCode keys, tokens, passwords, passphrases or certificate private material in source, packages, logs, artifacts, release assets or continuity.
- Preserve and back up the user-custodied encrypted TUF keys offline; future Targets/Snapshot/Timestamp renewal requires those retained keys.
- Never silently promote `trusted_root.synthetic.json` into production trust.
- TUF metadata remains the update authorization source; GitHub Release hosting alone never authorizes installation.
- Network update checks never gate normal application startup.
- No update installation occurs without explicit user confirmation after verification.
- RC/beta discovery must not rely only on GitHub `/releases/latest` because prereleases require channel-aware/TUF authority.
- Root rotation remains sequential and threshold-protected; rollback/freeze protections remain mandatory.
- Snapshot/Timestamp are deliberately short-lived and must be renewed before expiry using monotonically newer signed metadata; do not place their private keys in the repository merely to automate renewal.
- Public `v1.1.0-rc1` and `v1.1.0-rc2` assets are historical immutable release coordinates for Kodepoia policy purposes and must not be replaced in place.

## Resume rule after R19

On a new conversation, first verify current `main`, the public releases, open PRs, and this terminal continuity authority. Treat R19 as **COMPLETE + NORMALIZED** after the terminal normalization merge. Do not invent or start R19.6. Any future work must be authorized by a later roadmap phase/continuity authority, with its own dedicated planning/implementation/acceptance sequence.