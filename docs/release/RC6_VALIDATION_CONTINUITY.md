# Kodepoia 1.1.0-rc6 validation continuity

Status: **PLANNED — NOT YET BUILT OR PUBLISHED**  
Continuity baseline: `main` at `2946f3b6c4bcff4297c20d355144729854225990`  
Purpose: preserve the exact post-rc5 state and the acceptance contract for a validation-only `1.1.0-rc6` before the current ChatGPT session is replaced.

## 1. Non-negotiable scope

`1.1.0-rc6` is a **validation-only prerelease**. It must introduce **no new functionality and no behavior change** beyond the minimum release/version identity changes required to produce a distinct newer candidate.

Its sole product goal is to validate the complete installed Windows updater path from the already-installed public `1.1.0-rc5`:

`rc5 -> search -> detect rc6 -> download -> verify with TUF -> install verified update -> restart -> confirm rc6 -> search again`.

R20 remains **COMPLETE + NORMALIZED** and terminal. This work must **not** create `R20.7`, reopen R20, or reinterpret the rc6 validation as another R20 subdivision.

## 2. Canonical public rc5 baseline

Public release: `v1.1.0-rc5`  
Source SHA: `3f25eefa1a65cbbe9eb5822d6f68741675cf179b`  
Release ID: `387546105`  
Asset: `KodepoiaSetup.exe`  
Asset ID: `559134222`  
Asset size: `37712707` bytes  
Asset SHA-256: `30636a6ef5db4b3d171acc3817282595eff8ba724ff6c175329a10e8c5e8d42b`  
Public asset URL: `https://github.com/LaurentCOLL1/Kodepoia/releases/download/v1.1.0-rc5/KodepoiaSetup.exe`

The release is a published prerelease and the Git tag resolves to the exact source SHA above.

## 3. Real installed rc5 validation already completed

A clean copy of the public rc5 installer was downloaded and independently checked against the release asset identity:

- exact size: `37712707` bytes;
- exact SHA-256: `30636a6ef5db4b3d171acc3817282595eff8ba724ff6c175329a10e8c5e8d42b`;
- rc5 installed successfully into a custom Windows installation directory;
- packaged relative resource `kodepoia/update/trusted_root.production.manifest.json` is present in the installed application (278 bytes);
- KodeStudio starts as `1.1.0-rc5`;
- Settings -> Updates, Beta channel, `Rechercher des mises à jour` completes without the rc4 bootstrap error;
- updater reports candidate `1.1.0-rc5 (beta)` and source verification `tuf-verified-metadata`;
- updater reports declared size `37712707` bytes;
- because installed version equals candidate version, download/install buttons are correctly disabled.

Therefore the rc4 packaging defect where the packaged updater could not read `trusted_root.production.manifest.json` is considered corrected by rc5.

What remains **untested** is the complete newer-version path: download, TUF verification of the downloaded installer, launching the verified installer, upgrade/restart, and post-upgrade version confirmation. That is exactly why rc6 exists.

## 4. TUF authority at this continuity checkpoint

The exact repository state at this checkpoint is:

- Root: v2, SHA-256 `c92b2165bcbf39f74599fbdf8cc30e203f8c93cc2f24c5c74012821646850ee7`, expiry `2027-09-08T14:59:19Z`;
- Targets: v5, SHA-256 `d5c30941d6ae9ad21555db0e16ef6a1aa8f38a6d0049fdcebd29fc71d97a2757`, length `2392`, expiry `2027-09-12T20:49:31Z`;
- Targets authorized key ID: `70e86d478a769ffbefbf6febc37435a2a4563197df03d6dcda6627282fa5cf00`;
- Snapshot: v7, SHA-256 `66d7095dbe98ca5cd5d8de098d3537466aa92ec782db6b64c3282fce18a69df2`, length `469`, expiry `2026-09-15T21:47:58Z`;
- Timestamp: v7, SHA-256 `e91412f70ed161e9f26b3dd61721377af543d3ab837e6ee8d72d4c5ba64f8586`, length `470`, expiry `2026-09-14T21:47:58Z`.

Targets v5 preserves rc3 and rc4 and authorizes rc5. Root v2 must remain unchanged for rc6 unless a separate, explicitly governed Root ceremony becomes necessary; none is expected for this validation release.

**Important:** Snapshot/Timestamp are short-lived and may be automatically refreshed before the rc6 ceremony. Do not hard-code `v8` or any particular next online generation. At signing time, re-read the current trusted metadata from `main` and generate the next monotonic versions from that exact state.

## 5. rc6 implementation contract

The rc6 source commit must contain only the minimum release identity/version changes required to make the installed program report `1.1.0-rc6` and to build a distinct rc6 installer. No feature, refactor, dependency upgrade, UI redesign, updater logic change, TUF trust change, or unrelated cleanup is allowed in the rc6 product delta.

Before building, capture and pin the exact rc6 source SHA. Build the Windows installer from that exact SHA. Record its exact byte length and SHA-256 before any TUF metadata is produced.

Create `v1.1.0-rc6` first as a **draft prerelease** targeted to the exact rc6 source SHA. Upload the exact installer to the draft and record the GitHub asset identity. Do not manually create a conflicting tag before publication.

## 6. rc6 TUF transition contract

At the actual signing ceremony:

1. Re-read and verify the current Root, Targets, Snapshot and Timestamp from the canonical branch.
2. Keep Root v2 unchanged.
3. Produce the next monotonic Targets generation from the then-current Targets metadata, preserving every still-authorized prior beta target and adding exactly the rc6 installer path, length, SHA-256, source SHA and final release URL.
4. Sign Targets only with the already-authorized offline Targets authority. Never generate a replacement Targets key merely for rc6.
5. Produce the next monotonic Snapshot generation binding the exact new Targets metadata.
6. Produce the next monotonic Timestamp generation binding the exact new Snapshot metadata.
7. Validate every signature, threshold, version, hash, length and expiry before repository integration.
8. Keep private keys, seeds, passphrases and custody paths out of Git, GitHub Actions, release assets and public evidence.

The atomic transition must follow the established rc5 fail-closed discipline. `main` must never be intentionally left in a state that advertises a target whose final public payload cannot be retrieved and verified.

## 7. Required rc6 exact-head acceptance before publication

Before publishing the draft rc6 release, require all release-relevant acceptance checks on the exact transition/source heads, including the repository guard, Python core/update tests, TUF/signing acceptance, corrective RC integrated acceptance, and the Windows installer workflow used for rc5.

Do not treat a green run from a different SHA as evidence for rc6.

## 8. Mandatory real-machine end-to-end acceptance from installed rc5

After rc6 is public and its final tag/asset identities have been independently re-verified, use the already-installed public rc5 application and perform this exact user path:

1. Open KodeStudio `1.1.0-rc5`.
2. Settings -> Updates -> Beta.
3. Click `Rechercher des mises à jour`.
4. Confirm the candidate is `1.1.0-rc6` and the source is TUF-verified metadata.
5. Click `Télécharger et vérifier l'installateur`.
6. Confirm download completes and verification succeeds; any hash/length/TUF failure is a release blocker.
7. Click `Installer la mise à jour vérifiée...`.
8. Complete the installer-driven upgrade without manually substituting another installer.
9. Restart KodeStudio from the installed application.
10. Confirm the installed version is `1.1.0-rc6`.
11. Search for updates again and confirm rc6 is current on the Beta channel.
12. Confirm `trusted_root.production.manifest.json` remains packaged after the upgrade.

Only after this sequence passes should the Windows updater be considered end-to-end validated. If it fails, stop feature work and diagnose the failure from the exact rc5 -> rc6 transition.

## 9. Publication and normalization rules

GitHub release workflow should remain draft-first: build and attach the exact asset, validate the transition, then publish the draft prerelease. After publication, verify the actual Git tag resolves to the pinned rc6 source SHA and re-check the public asset size/digest.

After successful real-machine acceptance, record a concise public acceptance evidence file and normalize continuity. Do not promote rc6 to stable merely because the updater test passes; stable promotion remains a separate decision.

## 10. Security/custody invariants

- No private TUF material in the repository.
- No private TUF material in GitHub issues, PRs, Actions logs, release notes or ChatGPT-visible public evidence.
- Never paste private key contents, seeds or passphrases into a chat.
- Reuse the existing authorized Targets authority and authorized online Snapshot/Timestamp authorities.
- Fail closed on unexpected SHA, version, threshold, key ID, metadata binding, expiry, asset size or asset digest.

## 11. Next-session resume instruction

A new ChatGPT conversation must begin by reading this file from the current GitHub branch/main state and re-fetching the live GitHub/TUF state before making any mutation.

Recommended prompt:

`@Recherche sur le Web Reprends la création de Kodepoia 1.1.0-rc6 de validation depuis docs/release/RC6_VALIDATION_CONTINUITY.md. Vérifie d'abord le main, les métadonnées TUF et la release rc5 actuels. rc6 ne doit contenir aucune nouvelle fonctionnalité et doit servir uniquement au test E2E rc5 -> rc6.`

Do not infer a future rc6 source SHA, installer hash/size, Targets version, Snapshot version or Timestamp version from this document. Those identities must be generated and verified from the live state when rc6 is actually built and signed.
