# R12.14 — Acceptance

## Scope

Packaging/install/update/signing-state + rollback contracts only. R12.14 proves semantic package identity/integrity, framework package capability truthfulness, explicit signing states, local-fixture update validation/promotion and rollback. It does **not** manufacture a real MSIX/MSI installation, certificate trust, production signing, Store publication or production update-server claim.

Manual intervention: **CONDITIONAL / NOT TRIGGERED**.

The conditional gate did not trigger because the accepted R12.14 claim is fully covered by hosted deterministic semantic/local-fixture evidence and does not require an unproven real installer, OS trust, production signing or production update-server semantic. No production certificate is required for this accepted scope.

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
PR: #213.
Manual state: **CONDITIONAL / NOT TRIGGERED**.
Accepted implementation candidate: `4d1377d74d9a6b5f7d47256288511908957d0adb`.

Candidate exact-head workflow evidence:

- R0 Repository Guard #1568 / run `32831015949` — SUCCESS;
- Python Core #1542 / run `32831015974` — SUCCESS; hosted `python-core-ubuntu-latest` and `python-core-windows-latest` both completed `Test` successfully, and package build jobs succeeded on both OSes;
- KodeStudio UI Smoke #1509 / run `32831016023` — SUCCESS;
- R12 WPF Acceptance #61 / run `32831016002` — SUCCESS;
- R12 WinUI3 Acceptance #51 / run `32831016057` — SUCCESS;
- R12 Avalonia Acceptance #47 / run `32831016116` — SUCCESS;
- R12 Qt6 Acceptance #42 / run `32831016129` — SUCCESS;
- R12 Tauri2 Acceptance #33 / run `32831015985` — SUCCESS.

The R12 phase plan and continuity were synchronized at subdivision start before implementation: R12.1–R12.13 `COMPLETE`, R12.14 `IN_PROGRESS`, R12.15–R12.16 `PLANNED`. They must now receive the mandatory end-of-subdivision update before final documentation re-gates: R12.14 `COMPLETE`, R12.15–R12.16 still `PLANNED`.

## Merge / normalization rule

The candidate above is accepted. Perform the mandatory end-of-subdivision `R12_PLAN.md` + continuity status update, record this evidence, and freeze the resulting final documentation HEAD. Because documentation bytes change after the accepted candidate, re-run the full exact-head gate set plus desktop adapter regressions on that exact final head. Merge PR #213 only with `expected_head_sha` equal to that accepted final documentation SHA, then perform exactly one continuity-only post-merge normalization and its exact-head gates. R12.15 remains forbidden until that normalization merges.
