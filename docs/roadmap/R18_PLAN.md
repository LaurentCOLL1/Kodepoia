# R18 — Trusted Release, Updates & Distribution Channels

Status: **IN_PROGRESS**

Started: **2026-09-04**

Normalized source of truth: `main` `58e488d80e60d04fc675e305bc8f040a3ab2bb9c` — R17 COMPLETE + NORMALIZED.

Roadmap status: planning is **ACCEPTED + NORMALIZED** on `main` `bbffc382d4fb8a7d947345da11b56459d0fec825`. R18.1 is COMPLETE + NORMALIZED on canonical `main` `c611131268041b06f53de66eaadd45120e2b750d`. R18.2 is COMPLETE at END-sync on immutable technical source `f15967530e79bb365246afb92a8db02906acb0c4`; its exact-head implementation/evidence merge and the unique post-merge continuity-only normalization remain required before R18.3 may start. The frozen v1.0/R1–R16 architecture and history are not rewritten.

## Phase objective

Turn the standalone Windows distribution delivered by R17 into a trustworthy release/update system that can be promoted to real users without weakening Kodepoia's local-first and guarded architecture.

R18 must establish one canonical release identity; reproducible release bundles; build provenance/SBOM evidence; Windows Authenticode integration with truthful production-signing claims; immutable release staging/promotion; secure update metadata with rollback/freeze protections; a user-consented updater; release-channel UX; WinGet-ready manifests; rollback/revocation incident procedures; and integrated adversarial release acceptance.

The core phase is designed to be authoritatively testable without production secrets or public publication. Production certificate use, public GitHub Release publication and submission to the public WinGet Community Repository remain separately governed **CONDITIONAL** operations. Their absence must never be silently converted into a production claim.

## Research basis frozen for planning

The plan adopts the following externally verified principles as design inputs, not as mutable runtime dependencies:

- GitHub immutable releases lock the tag and release assets after publication and generate release attestation material linking release identity, commit and assets.
- GitHub artifact attestations provide cryptographically signed build provenance and can carry SBOM-related evidence.
- Microsoft SignTool is the canonical Windows SDK tool for signing/verifying Authenticode signatures; modern usage must specify digest algorithms and SHA-256 is the required project baseline.
- Windows Package Manager uses versioned YAML manifests and validates submissions before a package can enter the public community repository.
- The Update Framework (TUF) defines trusted root/targets/snapshot/timestamp roles and defenses against rollback, freeze and repository-compromise classes of update attack.

These principles must be re-checked against current official documentation when the relevant subdivision is implemented because external platform behavior may change.

## Phase-wide architecture and governance boundaries

All existing v1.0/R16 security and governance boundaries remain in force:

- `WorkspaceBoundary`, `ProcessSandbox`, Guardian/`PermissionSet`, global KillSwitch and SafeChange behavior are not bypassed by release/update code.
- update discovery is network-capable only through an explicit structured release/update adapter; model-supplied arbitrary URLs, commands or executable paths are non-authoritative.
- installer/update execution is never silently delegated to an LLM. The user must receive a concrete version/source summary and explicitly consent before an installer is launched.
- no signing key, certificate private key, token, password, timestamp credential or store credential may enter Git, generated evidence, logs or prompts.
- repository-controlled metadata cannot claim a binary is production-signed; authoritative verification must inspect the built binary/signature and its trust evidence.
- release/update metadata is fail-closed for signature, expiry, rollback, hash, size, channel and target-name mismatches.
- offline/local-first use remains valid. Failure to reach update infrastructure must not block KodeStudio startup or project work.
- release/update operations may not change project workspaces, Project DNA, user assets or local model data without the pre-existing backup/migration boundaries.
- public publication and package-manager submission are distinct effects and require explicit authorization at the point of effect.
- all phase branches use exact-head tests, expected-head protected merges, and post-merge continuity normalization.

## Global prerequisites

Before R18.1 begins:

- R17 must remain COMPLETE + NORMALIZED on exact base `58e488d80e60d04fc675e305bc8f040a3ab2bb9c`.
- `KodepoiaSetup.exe` standalone install/smoke/uninstall evidence from R17 remains the packaging baseline.
- Python 3.12, the accepted PySide6/Nuitka range and Inno Setup 6 remain the implementation baseline unless a subdivision explicitly and safely updates a pinned dependency.
- no production signing certificate, GitHub Release, WinGet publication or external update host is assumed to exist.
- synthetic/local release repositories and test certificates/keys may be used only as non-production fixtures and must be unmistakably marked as such.

## Subdivision index

| ID | Title | Status | Manual intervention | Depends on |
| --- | --- | --- | --- | --- |
| R18.1 | Canonical release identity, versions and channels | COMPLETE | NONE | R17 normalized main |
| R18.2 | Deterministic release bundle and manifest contract | COMPLETE | NONE | R18.1 |
| R18.3 | SBOM, provenance and artifact attestations | PLANNED | NONE | R18.2 |
| R18.4 | Windows Authenticode signing and verification boundary | PLANNED | CONDITIONAL | R18.2–R18.3 |
| R18.5 | Immutable GitHub Release staging and promotion | PLANNED | CONDITIONAL | R18.2–R18.4 |
| R18.6 | TUF-secured update repository and metadata lifecycle | PLANNED | NONE | R18.1–R18.3 |
| R18.7 | KodeStudio update discovery and release-channel UX | PLANNED | NONE | R18.6 |
| R18.8 | Verified download, user-consented install and rollback | PLANNED | NONE | R18.4, R18.6–R18.7 |
| R18.9 | WinGet manifest generation and validation | PLANNED | CONDITIONAL | R18.2, R18.4–R18.5 |
| R18.10 | Revocation, rollback and compromised-release drills | PLANNED | NONE | R18.4–R18.9 |
| R18.11 | Integrated adversarial release/update acceptance | PLANNED | NONE | R18.1–R18.10 |

No subdivision may be silently added, removed, merged, split or renumbered. Any change requires a plan + continuity update in the same governed work cycle.

---

# R18.1 — Canonical release identity, versions and channels

## Objective and rationale

Eliminate version ambiguity before any trusted release mechanism is built. At the R17-normalized base, Python package metadata and installer metadata are not yet a single canonical identity. R18.1 creates one machine-readable source of truth and explicit release channels.

## In scope

- define a canonical `ReleaseIdentity`/release metadata schema with product name, package name, semantic public version, Python-compatible version, installer version, channel, commit SHA and build type;
- define channels `stable`, `beta` and `nightly/development`, with stable promotion rules and no accidental downgrade from stable to prerelease;
- make `pyproject.toml`, installer manifest, About/version UI, CLI `--version`, release bundle and future update metadata derive from or validate against the canonical identity;
- preserve compatibility where Python packaging requires PEP 440 formatting while Windows/public display uses a normalized public form;
- add version monotonicity and channel-transition tests.

## Out of scope

Signing, publishing, downloading updates, GitHub Releases, WinGet submission and automatic version bumping from untrusted branch names.

## Dependencies and prerequisites

Direct child of the normalized R17 main. No external account or credential required.

## Detailed implementation plan

Introduce a repository-controlled release identity document/schema under `packaging/` and/or `schemas/`, plus a small pure-Python resolver under `src/kodepoia/release/`. The resolver must parse and validate identity, normalize PEP 440/public forms, expose channel policy, reject conflicting versions and bind build output to exact source SHA. Build scripts must fail if `pyproject.toml`, Inno Setup metadata and manifest disagree with the canonical identity. Runtime UI reads packaged generated identity, never mutable network metadata, for "installed version".

## Deliverables

Release identity schema/data, resolver module, installer/build wiring, CLI/UI version accessors, focused tests and design/acceptance evidence.

## Acceptance gates / Definition of Done

Focused unit tests; invalid/mismatch negative cases; installer static tests; R0 Repository Guard; full Python Core Ubuntu + Windows; KodeStudio UI smoke Windows; exact-head PR merge and post-merge continuity normalization.

## Validation and evidence

Preserve exact head SHA, normalized identity JSON, all derived version strings and CI run IDs. Evidence must demonstrate zero version disagreement.

END-sync technical acceptance: immutable source `8fda649829acfd5abae2ea31e9c744f8554b8d06`; R18.1 run `33928967043` SUCCESS on Ubuntu 24.04 and Windows with compile, Ruff, 6/6 focused tests, packaged-wheel identity verification and exact-source evidence emission. Canonical identity is `Kodepoia` / `kodepoia`, channel `beta`, build type `prerelease`, PEP 440 `1.1.0rc1`, public/installer `1.1.0-rc1`, source binding `exact-head`; acceptance SHA-256 `1bf94b74713522149083b608c0664c215ba12304244fb6d6ec04e280291f883d`, identity SHA-256 `d0cd93c16846980ac8e633bd23f2930969f2d249040452c5529095de1cd40ef1`, schema SHA-256 `0c4dfdd550cd14bccbdcf03a6f3b1403e0bff3c2afed6b61803f7e1ee6612b4f`. Manual state is `NONE`; production signing, public GitHub Release and public WinGet submission are not triggered. Because this END-sync changes documentation bytes, fresh R18.1 + R0 Repository Guard + full Python Core + KodeStudio UI Smoke gates on the resulting exact END-head are mandatory before exact-head merge.

## Rollback / recovery

Revert resolver/schema/build wiring together; retain previous R17 installer version contract until R18.1 is re-accepted.

## Risks and regression traps

PEP 440 vs display-version formatting, prerelease ordering, accidental downgrade, stale generated files, tests reading mutable package metadata.

## Manual intervention

**NONE**.

---

# R18.2 — Deterministic release bundle and manifest contract

## Objective and rationale

Promote the R17 installer artifact into a complete, deterministic release candidate bundle with machine-verifiable contents and no ambiguous loose files.

## In scope

- define `ReleaseBundleManifest` containing exact source SHA, release identity, file names, SHA-256, sizes, roles and build provenance references;
- produce a deterministic bundle containing `KodepoiaSetup.exe`, checksums, release manifest, license/notices required by repository policy and generated release notes metadata;
- bind the installer to the manifest and reject duplicate/unexpected executable payloads;
- generate deterministic archive ordering/timestamps where technically practical and record any platform-controlled non-determinism explicitly;
- build twice from the same exact source where practical and compare semantic/binary evidence.

## Out of scope

Production signature, public upload, delta patching, model/Ollama bundling.

## Dependencies and prerequisites

R18.1 canonical release identity.

## Detailed implementation plan

Extend Windows packaging scripts around the existing Nuitka + Inno path. Add manifest schema, bundle builder and verifier. Every generated release artifact must be enumerated, hashed and size-bound. The verifier must reject path traversal, duplicate names, unknown executables and source-SHA mismatches. Any non-reproducible signing/timestamp layer must be separated from the unsigned deterministic payload boundary.

## Deliverables

Schema, bundle builder/verifier, Windows workflow updates, release note template, tests and acceptance report.

## Acceptance gates / Definition of Done

Focused manifest/bundle tests including tamper negatives; two-build semantic equivalence; installer clean install/smoke/uninstall; R0; Python Core; UI smoke; exact-head merge + normalization.

## Validation and evidence

Bundle manifest digest, installer digest/size, semantic bundle digest, two-build comparison, workflow/artifact IDs and exact source SHA.

END-sync technical acceptance: immutable source `f15967530e79bb365246afb92a8db02906acb0c4`; R18.2 #8 / `33944044685` SUCCESS with Ubuntu + Windows focused contract acceptance and actual Windows two-build/install/smoke/uninstall evidence. The two real Windows builds expose Nuitka/Inno binary variance rather than hiding it: installer/archive/manifest/payload hashes differ, while both bundles share semantic SHA-256 `92cbf76bfadf686499ce25bde734e62943e4bbb863dbc296d6ddd8f48eb001eb` and acceptance reports `semantic_equivalent=true`, `installer_binary_reproducibility=platform-variance-observed`, status PASS. Build 1 archive SHA-256 `45233feb800e30480390dcf91947d06de167bbab0a1eec359a88ea9643e67939`; build 2 archive SHA-256 `c4637e537584c78108cdfc27e06842279c47179be13bed0346ddee972c09ecfb`; schema SHA-256 `c7e8f65b0e68cdc48f8cc01f33fab31d1b71ae93d281da53e241fc0033888ca1`; two-build artifact ID `9963221589`, artifact ZIP digest `sha256:ca50e831ace8780f309159dbecd724167614ebe1251e677924ccc316e7327ed0`. Exact technical-head R16.9 #112 / `33944044704`, R0 #2442 / `33944044651`, Python Core #2414 / `33944044622` 5/5 and KodeStudio UI Smoke #2379 / `33944044688` also SUCCESS. Manual intervention NONE; production signing, public GitHub Release and public WinGet submission remain NOT TRIGGERED. Because this END-sync changes documentation bytes, fresh R18.2 + R16.9 + R0 + full Python Core + KodeStudio UI Smoke gates on the resulting exact END-head are mandatory before exact-head merge.

## Rollback / recovery

Keep R17 installer builder callable until new bundle path is accepted; no deletion of last accepted artifact path during implementation.

## Risks and regression traps

Nuitka/Inno timestamp variance, archive metadata, unexpected DLL additions, manifest self-hash cycles, line-ending differences.

## Manual intervention

**NONE**.

---

# R18.3 — SBOM, provenance and artifact attestations

## Objective and rationale

Make each release candidate independently traceable to source, dependencies and the workflow that built it.

## In scope

- generate a release SBOM in a standard machine-readable format accepted by current tooling (prefer SPDX JSON unless implementation research demonstrates a stronger repository-compatible choice);
- capture packaged Python distributions and relevant native/runtime components without claiming completeness for files the tooling cannot identify;
- generate GitHub artifact provenance attestations for release candidate artifacts when supported by the public repository/workflow context;
- verify attestations in CI or a dedicated acceptance step using GitHub-supported verification tooling;
- bind SBOM/provenance digests into the release bundle manifest.

## Out of scope

Treating attestations as malware/security guarantees; signing Windows binaries; third-party store publication.

## Dependencies and prerequisites

R18.2 release bundle contract. GitHub workflow permissions must be least-privilege and explicitly documented.

## Detailed implementation plan

Add an SBOM generator/normalizer and verification tests. Extend release workflow with GitHub-supported artifact attestation action pinned to immutable revision where feasible, with only required `id-token`/attestation permissions. Record source repository, source digest, workflow identity and subject digests. Tests must distinguish build provenance from production Authenticode trust.

## Deliverables

SBOM generator/schema policy, workflow attestation integration, verification script, tests and acceptance evidence.

## Acceptance gates / Definition of Done

SBOM schema/semantic validation; attestation generated for exact subject and successfully verified; negative verification against modified subject; dependency/license governance regressions remain green; R0/Python/UI gates; merge + normalization.

## Validation and evidence

SBOM digest, attestation subject digest, verification output, run/workflow IDs and exact head.

## Rollback / recovery

Attestation/SBOM failures block release promotion but must not break developer builds; revert workflow additions independently of runtime code.

## Risks and regression traps

Confusing provenance with code signing, incomplete native dependency inventories, excessive workflow permissions, mutable action tags.

## Manual intervention

**NONE** for repository/workflow attestations supported by GitHub Actions.

---

# R18.4 — Windows Authenticode signing and verification boundary

## Objective and rationale

Add a real signing boundary without ever fabricating a production-signing claim. The implementation must work in unsigned/test modes and become production-signed only when a real identity is explicitly supplied and successfully verified.

## In scope

- integrate Microsoft SignTool discovery, signing, RFC3161 timestamping configuration and verification;
- require SHA-256 file digest and timestamp digest policy;
- define `SigningEvidence` with mode (`unsigned`, `test`, `production`), certificate identity/fingerprint summary, timestamp verification result and binary digest;
- perform post-sign verification on the exact installer and relevant executable(s);
- keep credentials in approved CI secret/key-provider boundaries only;
- support a non-production test-signing fixture/path sufficient to exercise failure handling without claiming public trust.

## Out of scope

Acquiring/buying a certificate, requesting private keys from the user, bypassing SmartScreen reputation, or publishing because a signature exists.

## Dependencies and prerequisites

R18.2 bundle; R18.3 provenance. Windows SDK/SignTool on acceptance runner.

## Detailed implementation plan

Add a signing adapter/script that accepts only structured configuration. The build produces an unsigned deterministic payload first, then optionally signs a copy/promotion candidate. Verification must inspect the actual PE signature and fail production claims when chain/timestamp/evidence is absent. Logs must redact sensitive provider details. Repository metadata alone cannot set `production_signed=true`.

## Deliverables

Signing adapter/scripts, evidence schema, CI test-sign mode, static/runtime tests and documentation.

## Acceptance gates / Definition of Done

Unsigned path remains green and truthful; test-sign path signs and verifies a fixture/candidate; tampered binary fails verification; missing/expired/incorrect identity cases fail closed; R0/Python/UI; merge + normalization. Production-signing acceptance occurs only if a real production identity is explicitly authorized and exercised.

## Validation and evidence

Exact pre/post-sign digests, SignTool verify output sanitized of secrets, certificate public identity summary, timestamp result and explicit production claim boolean.

## Rollback / recovery

Signing failure leaves accepted unsigned bundle untouched and prevents promotion. Rotate/revoke configuration without changing source history.

## Risks and regression traps

Secret leakage, signing wrong binary, timestamp service outage, certificate expiry/revocation, conflating test certificate with production trust.

## Manual intervention

**CONDITIONAL**.

Condition: only if the user chooses to establish a real production Authenticode identity. At that gate, provide exact provider-specific steps based on current official documentation; never request private-key material in chat. Until triggered, authoritative state remains `production_signed=false`.

---

# R18.5 — Immutable GitHub Release staging and promotion

## Objective and rationale

Create a release process in which the exact accepted bundle can be staged, verified and—only when explicitly authorized—published as an immutable GitHub Release.

## In scope

- define draft/staged/published promotion states;
- tag naming and source-SHA binding from R18.1 identity;
- generate release notes from repository-controlled data;
- attach only manifest-approved assets;
- verify digests/attestations before promotion;
- support GitHub immutable-release capability where repository settings/API permit it;
- post-publication verification of release/tag/assets when publication is authorized.

## Out of scope

Automatic publication on every merge, replacing GitHub with a CDN, or claiming immutability where the repository setting is unavailable/not enabled.

## Dependencies and prerequisites

R18.2 bundle, R18.3 attestations, R18.4 truthful signing state.

## Detailed implementation plan

Implement a release promotion command/workflow with a dry-run/stage mode as default. It must refuse source mismatch, dirty bundle, unexpected asset, mutable tag reuse, missing required attestation or contradictory signing evidence. Public publication requires a separate explicit effect boundary and exact release candidate digest approval.

## Deliverables

Release promotion module/workflow, release metadata schema, tests, dry-run evidence and documentation.

## Acceptance gates / Definition of Done

Offline/dry-run promotion passes; negative mismatch/tamper/tag-reuse cases fail; GitHub API interactions are mocked or use non-public safe test primitives where possible; R0/Python/UI; merge + normalization. Actual public release is conditional, not required for core phase truthfulness.

## Validation and evidence

Staged release manifest, intended tag/source SHA, asset digests, attestation verification and—if triggered—published release ID/tag/immutable verification.

## Rollback / recovery

Before publish, discard staging safely. After an immutable public release, never mutate assets; supersede with a new version and document withdrawal/revocation state.

## Risks and regression traps

Publishing wrong SHA, mutable tag assumptions, release asset drift, accidental public effect from CI.

## Manual intervention

**CONDITIONAL**.

Condition: explicit user authorization to create/publish a public GitHub Release or enable a repository release setting not safely available to automation. No public release may be inferred from successful staging.

---

# R18.6 — TUF-secured update repository and metadata lifecycle

## Objective and rationale

Secure update discovery against tampering, rollback, freeze and repository compromise rather than trusting a mutable JSON file or release API response directly.

## In scope

- implement a TUF-compatible update metadata repository using root, targets, snapshot and timestamp roles;
- pin an initial trusted root in the installed application/package;
- support metadata versioning, expiry, threshold policy where applicable and root rotation tests;
- publish channel-specific installer targets with exact length/hash and release identity metadata;
- implement local/synthetic repository generation for acceptance;
- define metadata cache and clock/error behavior without blocking app startup.

## Out of scope

Silent installation, peer-to-peer updates, delta patches, external CDN deployment or remote key custody service procurement.

## Dependencies and prerequisites

R18.1 channel identity and R18.3 provenance. Implementation research must select a maintained TUF library/version and pin it under existing dependency-governance rules rather than inventing cryptography.

## Detailed implementation plan

Add `src/kodepoia/update/` repository/trust abstractions. The client begins from packaged trusted root, refreshes timestamp/snapshot/targets through a structured transport adapter, validates signatures/version/expiry/hash/length and resolves only targets permitted for the configured channel/platform. Network response content is untrusted until TUF verification completes. Synthetic fixtures exercise compromised mirror, stale metadata, rollback and key rotation.

## Deliverables

Update trust adapter, repository builder for tests/release staging, schemas/config, fixtures, tests and security design record.

## Acceptance gates / Definition of Done

Happy-path refresh; tampered target; rollback metadata; expired timestamp; freeze/stale state; wrong-channel target; root rotation; offline cached behavior; R0/Python/UI; merge + normalization.

## Validation and evidence

Trusted-root digest/version, metadata role versions/expiry, target digest/size/channel and negative-case results.

## Rollback / recovery

Keep last verified metadata/target state; never replace trusted root or installed software from failed refresh. Root-rotation recovery procedure documented and tested with synthetic keys.

## Risks and regression traps

Clock skew, root-key loss, unsafe custom crypto, rollback acceptance, metadata cache corruption, mixing channel targets.

## Manual intervention

**NONE** for synthetic/local acceptance. Production key custody/hosting remains outside core acceptance unless separately triggered.

---

# R18.7 — KodeStudio update discovery and release-channel UX

## Objective and rationale

Expose trustworthy update information without turning update checks into a startup dependency or a model-controlled action.

## In scope

- Settings UI for update channel with conservative default and explicit prerelease warning;
- manual "Check for updates" action plus configurable periodic checks that never exceed defined network/budget policy;
- show installed version, candidate version/channel, source verification state, release notes summary, size and signing/provenance status;
- distinguish `up to date`, `update available`, `offline`, `metadata expired`, `verification failed`, `channel unavailable` and `update withdrawn` states;
- no forced update and no automatic installer launch.

## Out of scope

Downloading/installing the update (R18.8), public release publication, telemetry/analytics.

## Dependencies and prerequisites

R18.6 verified metadata API.

## Detailed implementation plan

Add an update controller/model independent of Qt, then a KodeStudio settings/update panel consuming structured status. Persist only channel/check preference and verified cache metadata in application config. All user-facing French/English strings must be cataloged; legacy fallback remains English rather than fabricated translation.

## Deliverables

Controller, UI panel/dialog, localization entries, persistence, tests and screenshots/smoke evidence where available.

## Acceptance gates / Definition of Done

Pure logic tests; Qt smoke for every major status; offline launch unaffected; verification failure visibly blocks download action; R0/Python/UI; merge + normalization.

## Validation and evidence

State-machine cases, UI smoke results, locale coverage and exact candidate metadata shown.

## Rollback / recovery

Disable update checking via config without affecting startup. Remove cached metadata safely while retaining packaged trusted root.

## Risks and regression traps

Startup latency, background thread leaks, confusing prerelease/stable states, stale translated text, exposing unverified release notes as trusted instructions.

## Manual intervention

**NONE**.

---

# R18.8 — Verified download, user-consented install and rollback

## Objective and rationale

Complete the updater with a safe download/install handoff that verifies the exact target before execution and preserves recoverability.

## In scope

- download only TUF-authorized Windows installer target through bounded streaming transport;
- enforce target length/hash before any execution;
- verify Authenticode evidence according to R18.4 policy and release identity consistency;
- stage to application-owned update cache with atomic finalize;
- require explicit user confirmation before launching installer;
- close/restart handoff that avoids overwriting a running executable unsafely;
- preserve previous installer/version metadata and recovery instructions; test failed/cancelled install and interrupted download.

## Out of scope

Silent forced upgrades, kernel/service updater, binary deltas, modifying project data during update.

## Dependencies and prerequisites

R18.4 signing verifier, R18.6 TUF target resolution, R18.7 UX.

## Detailed implementation plan

Implement downloader with size/time/budget bounds, `.partial` files and atomic rename after verification. Execution adapter accepts only the verified staged path generated by the update controller. User confirmation contains current/candidate versions and trust state. Installer launch uses structured arguments and never model-provided command text. On next launch, application records update outcome and can guide reinstall of the prior accepted installer if needed.

## Deliverables

Downloader/cache/execution modules, UI flow, installer integration, recovery metadata, tests and Windows acceptance workflow.

## Acceptance gates / Definition of Done

Clean update from older packaged fixture to newer fixture; corrupted/truncated/wrong-size/wrong-hash/wrong-signature targets fail before execution; cancellation leaves no executable partial; install failure leaves app/project data intact; uninstall/install regression; R0/Python/UI; merge + normalization.

## Validation and evidence

Old/new version identities, target hashes/sizes, verification report, installer exit result, post-update packaged UI smoke and rollback/reinstall drill.

## Rollback / recovery

Retain reference to prior accepted installer/bundle where available; document manual reinstall fallback. Never auto-delete the last known-good installer until new version passes post-install smoke/first-launch health check.

## Risks and regression traps

TOCTOU between verify/execute, antivirus locks, partial downloads, reboot-required installer states, loss of user preferences, privilege escalation.

## Manual intervention

**NONE** for CI/synthetic acceptance.

---

# R18.9 — WinGet manifest generation and validation

## Objective and rationale

Prepare an OS-native distribution channel without making public submission part of ordinary CI.

## In scope

- generate Windows Package Manager manifests from canonical release identity and published/staged installer metadata;
- include exact installer URL only when a real public immutable release exists; otherwise produce non-publishable preview manifests clearly marked as such;
- include installer SHA-256, architecture, locale, silent switches and upgrade behavior consistent with accepted Inno Setup package;
- run current `winget validate`/equivalent schema validation where available;
- provide Sandbox validation instructions/workflow when practical.

## Out of scope

Automatically opening a public `microsoft/winget-pkgs` PR without explicit authorization; Microsoft Store publication.

## Dependencies and prerequisites

R18.2 bundle identity; R18.4 signing truth; R18.5 release URL if public publication is triggered.

## Detailed implementation plan

Add manifest template/generator under `packaging/winget/`, consuming only canonical release metadata. Prevent placeholder/private CI artifact URLs from being treated as publishable. Tests validate mapping and SHA. Windows workflow attempts local manifest validation with pinned/current supported tool and records unavailable-tool state truthfully.

## Deliverables

Generator/templates, validation script/tests, documentation and optional Sandbox test instructions.

## Acceptance gates / Definition of Done

Schema validation, mapping tests, installer switch consistency, negative placeholder URL/publication checks, R0/Python/UI; merge + normalization. Public repository submission remains conditional.

## Validation and evidence

Generated manifest digest/version/installer SHA; `winget validate` output; if triggered, public PR URL and validation result.

## Rollback / recovery

Withdraw/supersede a bad manifest with a corrected later package version according to WinGet policy; never mutate accepted installer bytes behind a version URL.

## Risks and regression traps

Manifest/version mismatch, unstable asset URL, wrong silent switches, public PR side effect, validation policy changes.

## Manual intervention

**CONDITIONAL**.

Condition: explicit authorization to submit to the public WinGet Community Repository and any account-side interaction GitHub automation cannot perform. Until then only local/CI manifest readiness is claimed.

---

# R18.10 — Revocation, rollback and compromised-release drills

## Objective and rationale

Prove that Kodepoia can respond safely when a release, signing identity, update metadata key or hosted asset must no longer be trusted.

## In scope

- synthetic compromised signing-certificate evidence and blocked trust policy;
- TUF key rotation/root update and rollback/freeze attack drills;
- release withdrawal/supersession metadata and UI state;
- wrong/malicious release asset simulation;
- rollback to last-known-good installer/release channel state;
- incident playbook defining freeze publication, rotate keys, supersede release and user communication evidence boundaries.

## Out of scope

Revoking a real certificate or deleting a real public release unless separately authorized due to an actual incident.

## Dependencies and prerequisites

R18.4–R18.9 complete enough to exercise end-to-end trust paths.

## Detailed implementation plan

Create deterministic fixtures for compromised/stale/tampered states and an acceptance harness that proves the updater fails closed while normal application work remains usable. Document which actions are local simulation versus provider-side production actions.

## Deliverables

Incident/recovery design, fixtures, drill runner, structured report and tests.

## Acceptance gates / Definition of Done

Every attack/drill has expected verdict; no critical bypass; last-known-good recovery verified; R0/Python/UI; merge + normalization.

## Validation and evidence

Structured drill report with scenario IDs, expected/actual verdicts, source SHA, key/metadata versions using non-secret identifiers, and recovery result.

## Rollback / recovery

The drill itself must be non-destructive and synthetic. Reset to clean fixtures after each scenario.

## Risks and regression traps

Tests accidentally contacting production endpoints, real revocation/publication side effects, recovery depending on attacker-controlled metadata.

## Manual intervention

**NONE** for authoritative synthetic drills.

---

# R18.11 — Integrated adversarial release/update acceptance

## Objective and rationale

Close R18 only after the complete release/update chain is exercised on one immutable exact source with positive and negative controls.

## In scope

- build the final Windows release candidate bundle from exact source;
- validate canonical identity, deterministic bundle, SBOM/provenance, signing truth state, release staging, TUF metadata, update discovery, verified download/install, channel policy, WinGet readiness and revocation/rollback drills;
- run clean Windows install and packaged update from an older accepted fixture to the candidate;
- run adversarial tamper/rollback/freeze/wrong-channel/wrong-signature/wrong-digest cases;
- generate a single integrated R18 acceptance report with `critical_veto` semantics;
- perform END-sync on `R18_PLAN.md` + continuity only, then fresh exact-END gates before implementation/evidence merge and one post-merge phase normalization.

## Out of scope

Automatic production publication/signing/WinGet submission. These remain explicit external effects even if readiness is proven.

## Dependencies and prerequisites

R18.1–R18.10 accepted and normalized.

## Detailed implementation plan

Create an integrated acceptance harness that consumes exact-source release artifacts and earlier structured evidence rather than trusting prose. It must verify provenance freshness, source SHA equality, manifest subject digests, signing mode, TUF target binding and updater result. Every critical trust-boundary negative must fail closed and set `critical_veto=true` when unexpectedly accepted.

## Deliverables

Integrated acceptance harness, schema/report, final Windows artifacts/evidence, END-sync documentation and final exact-head workflows.

## Acceptance gates / Definition of Done

- all R18 subdivisions accounted for;
- integrated report PASS with blockers empty and `critical_veto=false`;
- final release candidate build/install/update/uninstall health path succeeds on Windows;
- required negative controls fail as expected;
- R0 Repository Guard Ubuntu + Windows SUCCESS on final exact END-head;
- full Python Core Ubuntu + Windows SUCCESS;
- KodeStudio UI Smoke Windows SUCCESS;
- R18-specific integrated acceptance SUCCESS;
- implementation/evidence PR merges with exact expected head;
- exactly one post-merge continuity-only R18 phase normalization re-gated and merged.

## Validation and evidence

Final exact END-head SHA, workflow/run IDs, release bundle/installer digests, SBOM/provenance identifiers, signing mode, TUF root/metadata versions, update result, WinGet manifest digest and integrated report digest.

## Rollback / recovery

If any critical gate fails, R18 remains incomplete. Preserve the last accepted R17 distribution and last accepted R18 subdivision state; fix on the same dedicated R18.11 lineage and re-run fresh exact-source acceptance.

## Risks and regression traps

Circular evidence, reusing stale workflow successes after source changes, accepting unsigned artifacts as production-signed, update test accidentally using public production endpoints, cross-platform evidence mismatch.

## Manual intervention

**NONE** for core final acceptance. Production signing/public GitHub Release/WinGet submission evidence is included only if its earlier CONDITIONAL gate was explicitly triggered; otherwise the final report must state those effects were NOT TRIGGERED.

---

## Phase completion rule

R18 may be marked COMPLETE only when R18.1–R18.11 are each COMPLETE with fresh required evidence, or a subdivision is formally removed by an explicit roadmap/architecture decision. A successful dry-run does not imply a public release; a successful test signature does not imply production signing; a valid WinGet manifest does not imply public WinGet publication.

## Ongoing maintenance rule

Update `R18_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md` in the same work cycle whenever subdivision scope/status, manual conditions, acceptance requirements, recovered security defects or phase ordering changes. Architecture changes require an ADR.

## R18 planning merge rule

This planning document and its matching planning-continuity record must be the only intentional planning-scope changes relative to normalized R17 `main`. The exact planning head must pass fresh R0 Repository Guard, full Python Core and KodeStudio UI Smoke before the planning PR merges with exact expected-head protection. After that merge, exactly one planning continuity-only normalization must be performed and re-gated. Only the resulting normalized `main` authorizes R18.1 START-sync.
