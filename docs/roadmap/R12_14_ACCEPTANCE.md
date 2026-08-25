# R12.14 — Acceptance

## Scope

Packaging/install/update/signing-state + rollback contracts only. R12.14 proves semantic package identity/integrity, framework package capability truthfulness, explicit signing states, local-fixture update validation/promotion and rollback. It does **not** manufacture a real MSIX/MSI installation, certificate trust, production signing, Store publication or production update-server claim.

Manual intervention: **CONDITIONAL**.

Manual evidence is triggered only if the final accepted claim requires a real installer/install/update/signing semantic that hosted CI cannot prove. No production certificate is required for phase acceptance; truthful `UNSIGNED`/`TEST_SIGNED` states are sufficient where applicable.

## Required acceptance

- versioned `PackageDefinition`, `ArtifactManifest`, `UpdatePolicy` and `UpdateManifest` contracts are deterministic and digest-stable;
- semantic artifact identity is based on normalized file set/size/SHA-256/role, not nondeterministic package-container metadata;
- framework/package capability states distinguish `SUPPORTED_DEFINITION`, `TOOLCHAIN_REQUIRED` and `UNSUPPORTED` without manufacturing toolchain availability;
- signing states `UNSIGNED`, `TEST_SIGNED`, `SIGNED`, `SIGNING_UNAVAILABLE` are mutually validated and never carry private-key/secret material;
- exact artifact file-set/size/digest verification fails closed on tamper;
- traversal, duplicate-path and workspace-escape inputs fail closed;
- update source/target digest, package identity, version, channel, framework, platform, architecture, package kind and signing identity/state are bound together;
- same-version updates and downgrades are rejected by default; downgrade works only under explicit policy;
- wrong architecture/package/signing-state/signer substitution is rejected;
- local promotion verifies candidate before backup/promotion;
- injected post-promotion failure restores and re-verifies the prior accepted tree;
- stale staging/backup state is not silently overwritten;
- focused R12.14 tests plus exact-head R0 Repository Guard, full Python Core, KodeStudio UI Smoke and existing desktop adapter regressions succeed.

## Official implementation basis

Microsoft requires deployable MSIX packages to be signed with a valid code-signing certificate and trusted on the target device. Microsoft App Installer is forward-only by default and only allows downgrade when `ForceUpdateFromAnyVersion` is explicit. Qt's `windeployqt` creates a deployable dependency folder rather than proving installer trust/signing by itself. These boundaries are intentionally reflected as capability/update-policy states rather than synthetic PASS.

References:

- https://learn.microsoft.com/windows/msix/package/signing-package-overview
- https://learn.microsoft.com/windows/msix/app-installer/update-settings
- https://learn.microsoft.com/windows/msix/app-package-updates
- https://doc.qt.io/qt-6/windows-deployment.html
- https://v2.tauri.app/plugin/updater/

## Evidence state

Base normalized `main`: `63d6548d024fb511ca6172b121c05c9c7f02cf9c`.
Branch: `r12/14-packaging-update`.
Manual state: **CONDITIONAL / PENDING CANDIDATE GATES**.
Implementation candidate: **PENDING**.
Exact-head workflow evidence: **PENDING**.

The R12 phase plan and continuity were synchronized at subdivision start before implementation: R12.1–R12.13 `COMPLETE`, R12.14 `IN_PROGRESS`, R12.15–R12.16 `PLANNED`.

## Merge / normalization rule

Freeze one immutable implementation candidate and require exact-head standard gates plus desktop adapter regressions. If hosted evidence is sufficient for the bounded semantic/local-fixture claim, record manual state **CONDITIONAL / NOT TRIGGERED**. Before final documentation re-gates, update `R12_PLAN.md` and continuity again so R12.14 is `COMPLETE` and R12.15 remains `PLANNED`. If those documentation bytes change the head, re-run all required gates on that exact final head. Merge with `expected_head_sha`, then perform exactly one continuity-only post-merge normalization and its exact-head gates. R12.15 remains forbidden until that normalization merges.
