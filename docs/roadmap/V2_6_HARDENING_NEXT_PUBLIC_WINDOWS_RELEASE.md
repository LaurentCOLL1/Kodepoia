# V2.6 — V2 hardening and next public Windows release

Status: **PLANNING CURRENT — IMPLEMENTATION NOT YET AUTHORIZED**  
Planning base: `65ef3ac66494b4b801274b81141d136a4830d7be`  
Public distribution baseline at planning start: `v1.1.0-rc8`

## 1. Authority and purpose

The user explicitly authorized progression after V2.5 terminal normalization by instructing Kodepoia to continue. This authority permits **V2.6 planning only** until this planning contract is exact-head qualified, merged with `expected_head_sha`, and post-merge normalized.

V2.5 planning and V2.5.1 through V2.5.6 are COMPLETE + NORMALIZED. V2.6 is the terminal V2 phase for:

- full V2 hardening and regression closure;
- exact-source Windows release preparation;
- release/update security transition over the already accepted R17-R20 machinery;
- final installed Windows update validation;
- governed publication of the next public Windows release;
- terminal V2 continuity closure.

V2.6 is not a feature-expansion phase. No V2.7 is planned or authorized.

## 2. Release sequencing rule

The user has explicitly required that the next public release be made only when V2 is completely finished.

Therefore:

- no public release/tag/asset/TUF/updater/WinGet mutation is authorized during V2.6 planning;
- no such public mutation is authorized in V2.6.1 through V2.6.5;
- V2.6.1 through V2.6.5 must complete and normalize sequentially before the public-release subdivision may execute;
- **V2.6.6 is the only subdivision allowed to perform the governed public-release transition**, and only from a frozen exact source that has passed all preceding V2.6 gates;
- publication, TUF activation and installed updater validation remain distinct effect boundaries even when executed inside V2.6.6;
- a failed public transition is never reclassified as success and must be superseded/corrected through explicit evidence rather than overwritten.

The current public reference remains `v1.1.0-rc8` until V2.6.6 successfully publishes and validates a successor.

## 3. Version and channel boundary

Planning does **not** assume that the next release is `v2.0.0`, `v1.1.0`, or another version.

V2.6.1 must explicitly freeze:

- canonical public version;
- release channel (`stable`, `beta`, or other already-supported channel);
- release/build type;
- canonical tag;
- exact source SHA;
- installer version;
- update target path;
- release-note identity;
- Authenticode posture;
- whether WinGet publication is part of the release.

The selected identity must satisfy the existing `ReleaseIdentity` transition rules from the current `1.1.0-rc8` beta baseline. Any version/channel change after the release identity is frozen invalidates downstream V2.6 evidence.

## 4. Existing authority to reuse

V2.6 must reuse, not replace, the already accepted machinery:

- R17 Windows installer construction and installed packaged smoke;
- R18.1 canonical release identity;
- R18.2 deterministic release bundle;
- R18.3 SBOM/provenance/attestation;
- R18.4 truthful Windows Authenticode evidence;
- R18.5 immutable GitHub Release staging/promotion boundary;
- R18.6 TUF-secured update repository;
- R18.7 update discovery;
- R18.8 verified install/explicit consent;
- R18.9 WinGet packaging where explicitly in scope;
- R18.10 incident drills;
- R18.11 integrated adversarial release/update acceptance;
- R19.2 production update-repository bootstrap;
- R19.3 network update transport;
- R19.4 seamless Windows updater behavior;
- R19.5 corrective release mechanics;
- R20.1-R20.6 metadata refresh/signing/monitoring/continuous-operations machinery;
- the real installed rc7 -> rc8 updater E2E as the current terminal baseline.

R20 remains terminal. V2.6 must not create or imply R20.7.

## 5. Trust and publication invariants

All V2.6 work preserves the existing fail-closed boundaries:

- exact source SHA must be bound to every release artifact and evidence record;
- no fixture, synthetic key, synthetic TUF repository or CI-only attestation may be represented as live production release evidence;
- production TUF trust and synthetic acceptance trust remain distinct;
- no private signing key or credential is serialized into repository content, artifacts, logs or prompts;
- existing TUF root continuity, thresholds, rollback, freeze/expiry, target length/hash and source binding remain mandatory;
- release assets are immutable after publication when the provider supports/declares immutability; a bad release is superseded rather than silently replaced;
- installer identity, length, SHA-256 and signing posture must agree across staging, release, TUF metadata and installed-updater evidence;
- explicit user consent remains required before the updater launches an installer;
- updater failure must not prevent Kodepoia local startup;
- update discovery and metadata refresh never silently weaken signature/hash/expiry/rollback policy;
- release publication cannot be authorized by branch merge, CI success, presence of credentials, draft creation or model text alone.

## 6. Authenticode truth

V2.6 must report signing truth exactly.

If a trusted production Authenticode signing path is available and authorized, the exact signed installer and certificate evidence must be bound into release/TUF evidence.

If no trusted production signing path is available, V2.6 must not fabricate or imply one. Any decision to publish an unsigned Windows installer must be explicit, target-scoped, compatible with existing accepted updater policy and visible in release notes and TUF target metadata. Broken/invalid/untrusted/malformed signature states remain rejected.

The planning contract itself does not decide signed versus unsigned; V2.6.1 must freeze that release posture from observed capability and policy truth.

## 7. Installed-upgrade baseline

The current real installed baseline is `v1.1.0-rc8`, whose rc7 -> rc8 updater path passed on Windows.

The next release must preserve an auditable upgrade path from that installed baseline.

Pre-publication CI may use deterministic installed fixtures and staged TUF/update material. The terminal real public updater proof, when required by V2.6.6, must use the actual published release/TUF material and must not substitute a manually downloaded installer for the updater-managed target.

## 8. Critical-veto classes

Any of the following blocks V2 completion and public release:

- source SHA drift;
- version/tag/release identity mismatch;
- missing or contradictory SBOM/provenance/attestation evidence;
- installer hash/length/identity mismatch;
- invalid or falsely claimed Authenticode state;
- TUF rollback, freeze, threshold, root continuity or expiry failure;
- TUF target not bound to the exact release source/artifact;
- updater accepting an unauthorized target/channel/platform/source;
- updater bypass of explicit consent;
- failed clean install, packaged launch, upgrade, restart or post-upgrade update check;
- corruption/loss of user project data caused by the release/update path;
- public asset differing from the qualified staged asset;
- public tag not resolving to the qualified exact source;
- production secret leakage;
- unresolved critical regression from V2.0-V2.5;
- any attempt to substitute fixtures for production publication evidence.

No score averaging may override a critical veto.

## 9. Deterministic CI and live effects

Mandatory planning and pre-publication acceptance remains deterministic and provider-independent wherever possible.

CI may:

- build exact-source Windows candidates;
- generate deterministic release bundles;
- generate/verify SBOM/provenance evidence;
- exercise synthetic/local TUF repositories;
- test update discovery/verification/install flows against isolated fixtures;
- exercise clean install/update/uninstall on hosted Windows;
- verify GitHub release request descriptions and read-only snapshots.

CI must not during normal PR acceptance:

- publish a public GitHub Release;
- create/repoint a public tag as release authority;
- mutate production TUF metadata;
- rotate live production keys;
- submit public WinGet changes;
- claim real installed public-updater success.

Live release effects belong only to V2.6.6 after all prior subdivisions are complete.

## 10. Frozen subdivisions

### V2.6.1 — Terminal V2 scope, release identity and compatibility freeze

Freeze the exact terminal release contract before building public-release evidence.

Includes:

- exact source baseline and terminal V2 change inventory;
- canonical version/channel/build type/tag decision;
- transition validation from `1.1.0-rc8`;
- Windows installer/update target identity;
- Authenticode posture;
- stable/beta channel behavior;
- release-note and known-limitation contract;
- supported installed-upgrade baseline;
- explicit WinGet in/out decision;
- no-new-feature freeze after identity acceptance.

Does not publish or mutate production TUF/update state.

### V2.6.2 — Full V2 integrated regression and adversarial hardening

Prove the terminal codebase before release packaging.

Includes:

- integrated V2.0-V2.5 regression suite;
- security/privacy/secret/tool/workspace/memory/research/model-lab/orchestration regressions;
- Windows packaged UI and project durability;
- cancellation/recovery/resource-soak checks;
- updater local-availability invariants;
- critical-veto aggregation;
- deterministic exact-head Ubuntu/Windows evidence.

Does not create public release effects.

### V2.6.3 — Exact-source Windows release candidate, SBOM, provenance and signing truth

Create the frozen release candidate from the exact qualified source.

Includes:

- R17 installer build;
- release bundle/manifest;
- installer SHA-256 and byte length;
- SBOM/provenance;
- artifact-attestation verification where available;
- truthful Authenticode evidence;
- clean install, packaged smoke and uninstall;
- deterministic/two-build comparison where the existing R18 contract requires it;
- immutable staged GitHub-release description bound to exact evidence.

Does not publish a release or production TUF metadata.

### V2.6.4 — Production TUF transition and updater compatibility staging

Prepare and adversarially verify the exact update transition without publishing it.

Includes:

- production-root continuity and packaged-root pin validation;
- exact target path/version/source/hash/length binding;
- rollback/freeze/expiry/threshold tests;
- preservation/revocation rules for historical targets;
- rc8 -> candidate discovery/verification in isolated staged transport;
- explicit Authenticode policy consistency;
- updater cache/offline behavior;
- metadata-transition request/evidence suitable for later live signing.

Does not mutate the live update repository.

### V2.6.5 — Installed Windows release rehearsal and pre-publication go/no-go

Perform the final pre-publication release rehearsal.

Includes:

- clean install of the exact release candidate;
- installed `v1.1.0-rc8` -> candidate upgrade rehearsal using staged verified update material;
- packaged restart and version confirmation;
- post-upgrade update check against staged metadata;
- custom install-directory preservation;
- project/settings/user-data preservation checks;
- uninstall behavior;
- incident rollback/recovery rehearsal;
- final critical-veto report;
- freeze of the exact release candidate digest and publication inputs.

Definition of done: V2 product/hardening work is complete and the exact release candidate is ready for the governed live publication subdivision.

### V2.6.6 — Governed public Windows release, updater activation and terminal V2 closure

This subdivision is the only V2.6 phase allowed to perform live release effects.

It may begin only after V2.6.1-V2.6.5 are individually COMPLETE + NORMALIZED on the exact frozen candidate.

Includes, in governed sequence:

1. re-fetch exact candidate/source/release state and confirm no anti-race drift;
2. create/finalize the public GitHub tag/release from the frozen exact source;
3. upload only the qualified installer/assets;
4. verify public asset digest/length and tag/source binding;
5. perform the authorized production TUF metadata transition using existing R20 signing/operations boundaries;
6. verify live TUF target/source/hash/length/signing-policy truth;
7. perform the real installed Windows updater path from the accepted rc8 baseline when operationally required;
8. confirm restart into the new version and a healthy subsequent update check;
9. verify no old target was silently rewritten;
10. perform WinGet publication only if V2.6.1 explicitly placed it in scope and all dedicated gates pass;
11. write terminal V2 release evidence and continuity normalization.

A manual operator step may be required for real-machine installed updater verification or protected production signing/publication actions. If so, execution must stop at that exact boundary with step-by-step instructions and no later step may be claimed complete.

## 11. Acceptance discipline

Every V2.6 subdivision must:

1. re-fetch live `main` and current authorities;
2. branch from the exact live SHA;
3. modify only the authorized subdivision;
4. reuse accepted R17-R20 release/update machinery;
5. add deterministic tests and exact-head acceptance evidence;
6. invalidate all prior-SHA results after any implementation commit;
7. read exact failing logs before correction or rerun;
8. distinguish deterministic failure from provider/runner failure;
9. merge only after all required workflows succeed on the unchanged exact head;
10. use `expected_head_sha` protection;
11. post-merge normalize before authorizing the next subdivision;
12. keep public release effects impossible until V2.6.6.

## 12. Planning definition of done

V2.6 planning is complete only when:

- this contract is exact-head qualified;
- the six subdivisions and their effect boundaries are frozen;
- version selection is explicitly deferred to V2.6.1 rather than guessed in planning;
- the rc8 installed baseline is explicit;
- R17-R20 reuse points are explicit;
- Authenticode truth and unsigned/signed handling are explicit;
- GitHub Release and TUF publication boundaries are explicit;
- pre-publication rehearsals are distinct from live publication;
- exact-source and anti-race requirements are explicit;
- real installed Windows updater validation is explicit;
- no synthetic evidence can become production proof;
- no V2.7 or R20.7 is authorized;
- planning PR is merged with `expected_head_sha`;
- post-merge normalization authorizes **V2.6.1 only**.

Until that normalization is complete, no V2.6 implementation subdivision and no public-release mutation is authorized.

## 13. Planning qualification and current implementation authority

Planning PR `#551` completed **25/25** exact-head pull-request workflows with conclusion `success` on `f6f6cb80092af2ee790bc3e81e1f7c620fe2d751` and merged with `expected_head_sha` protection as `b7af0d3024ac3bcdbf75835941873aabcb0be345`.

V2.6 planning is therefore **COMPLETE + NORMALIZED**.

The six subdivisions and their effect boundaries are frozen. In particular, live public release/tag/asset/TUF/updater/WinGet effects remain reserved to V2.6.6 after V2.6.1 through V2.6.5 have each completed and normalized.

**V2.6.1 — Terminal V2 scope, release identity and compatibility freeze is the only authorized implementation subdivision.** V2.6.2 through V2.6.6 remain unauthorized until sequential qualification and normalization.

V2.6.1 must establish release identity and compatibility truth only. It must not publish or mutate production release/update state. The public baseline remains `v1.1.0-rc8`.

## 14. V2.6.1 qualification and current implementation authority

V2.6.1 implementation PR `#553` completed **33/33** exact-head pull-request workflows with conclusion `success` on `272f72d3dabf3ee6219dc847d1afaf78e23c6ca6` and merged with `expected_head_sha` protection as `75fa3f38ec4039cfa6972e1adf930423d16320b3`.

V2.6.1 is therefore **COMPLETE + NORMALIZED**.

Its accepted freeze establishes the terminal target as Kodepoia `1.1.0` / stable / release / `v1.1.0`, preserves `v1.1.0-rc8` as the current public/runtime baseline, keeps `candidate_source_sha = null` until V2.6.3, records production Authenticode signing as unverified, places WinGet publication OUT for `v1.1.0`, and preserves fail-closed rejection of the observed expired production TUF snapshot/timestamp metadata until the governed V2.6.4 transition stage.

The no-new-feature freeze is effective from this normalization. Remaining V2 changes are restricted to bug fixes, security hardening, regression fixes, release packaging, release evidence and release documentation.

**V2.6.2 — Full V2 integrated regression and adversarial hardening is the only authorized implementation subdivision.** V2.6.3 through V2.6.6 remain unauthorized until sequential qualification and normalization.

V2.6.2 must prove the terminal codebase with integrated V2.0-V2.5 regression, adversarial security/privacy/secrets/tools/workspaces/memory/research/Model Lab/orchestration coverage, packaged Windows/project durability, cancellation/recovery/resource-soak and updater local-availability invariants, critical-veto aggregation, and deterministic exact-head Ubuntu/Windows evidence.

V2.6.2 must not create public release effects and must not repair or mutate production TUF metadata. Public release/tag/asset/TUF/updater/WinGet effects remain reserved to V2.6.6.

## 15. V2.6.2 qualification and current implementation authority

V2.6.2 implementation PR `#555` completed **33/33** exact-head pull-request workflows with conclusion `success` on `5badcfb68b5593432f24ef4cf53eafd596d109cd` and merged with `expected_head_sha` protection as `2453c5122c096d807e5b49840d33a61e1bcc5e92`.

V2.6.2 is therefore **COMPLETE + NORMALIZED**.

Its deterministic terminal hardening evidence passed **12/12 on Ubuntu** and **12/12 on Windows**, with `critical_veto=false` and common evidence SHA-256 `91031f1462e46d9c24d17cc10fde5811d948c75a91597432861d0a211a16bfe0`. The complete Python regression suite passed before the evidence step on both operating systems.

The accepted result preserves the V2.6.1 terminal release freeze exactly and introduces no new product capability or public release effect.

**V2.6.3 — Exact-source Windows release candidate, SBOM, provenance and signing truth is the only authorized implementation subdivision.** V2.6.4 through V2.6.6 remain unauthorized until sequential qualification and normalization.

V2.6.3 must create the frozen candidate from its exact qualified source and prove the existing R17/R18 release-artifact contracts: Windows installer, release bundle/manifest, exact SHA-256 and byte length, SBOM/provenance, artifact attestation where available, truthful Authenticode evidence, clean install/packaged smoke/uninstall, required deterministic two-build comparison, and immutable staged GitHub-release description bound to exact evidence.

V2.6.3 must not publish the GitHub Release, create/repoint the public `v1.1.0` tag, publish public assets or mutate production TUF/update metadata. Live publication remains reserved to V2.6.6 after V2.6.1 through V2.6.5 are each COMPLETE + NORMALIZED.
