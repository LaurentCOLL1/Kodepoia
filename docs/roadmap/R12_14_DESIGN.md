# R12.14 — Packaging/install/update/signing-state + rollback model

## Frozen scope

R12.14 adds framework-neutral package/update contracts without creating a second build system or silently installing packages. It consumes accepted R12.5–R12.13 adapter/build/accessibility foundations and preserves R1 SafeChange/Backup/Recovery/Audit, R6 package/build evidence, R8 provenance, WorkspaceBoundary, ProcessSandbox, KillSwitch, Guardian and KodeSecrets boundaries.

Manual intervention is **CONDITIONAL**. It triggers only if the accepted claim requires a real installer execution, real OS package trust/install/update, or real signing operation that hosted CI cannot prove. Phase acceptance does **not** require a production certificate. The ordinary R12.14 claim is deliberately bounded to deterministic semantic package manifests, truthful capability state, local-fixture update promotion/rollback, and explicit signing-state identity.

## Contracts

### Package definition and capability

`PackageDefinition` binds a stable definition/package identity to version, framework, OS, architecture, package kind and signing state. Framework/format support is explicit:

- `SUPPORTED_DEFINITION`: Kodepoia can represent and semantically verify that package form without claiming that an OS installer was executed;
- `TOOLCHAIN_REQUIRED`: the form is modeled but an external framework/OS packaging tool is required before a real artifact can be claimed;
- `UNSUPPORTED`: the frozen framework/platform combination is rejected.

The matrix is intentionally conservative. WinUI/WPF MSIX, Avalonia/Qt Windows MSIX and Tauri Windows MSI are `TOOLCHAIN_REQUIRED`, not synthetic `AVAILABLE`.

### Semantic ArtifactManifest

`ArtifactManifest` records sorted normalized relative paths, byte sizes, SHA-256 digests and roles. Its digest is computed from semantic content rather than raw installer/container bytes so that upstream ZIP/MSIX/MSI metadata such as timestamps cannot silently alter the accepted logical package identity.

Artifact trees reject traversal, duplicate paths, symlinks and unbounded file/package sizes. `verify_artifact_tree` checks the exact file set, size and SHA-256 for every file before update promotion.

### Signing state

Signing state is explicit and non-interchangeable:

- `UNSIGNED` — no signing identity is asserted;
- `TEST_SIGNED` — a public non-production signer subject/fingerprint is recorded;
- `SIGNED` — a public production signer subject/fingerprint is recorded;
- `SIGNING_UNAVAILABLE` — a requested signing capability is unavailable and cannot be treated as signed.

No PFX/P12/private-key/password/secret material may appear in the signing identity. KodeSecrets remains authoritative for actual secrets if a later governed packaging operation uses them.

### Update policy and manifest

`UpdateManifest` binds source and target manifest digests, package identity, source/target versions, channel, framework, OS, architecture, package kind and signing state/fingerprint.

`UpdatePolicy` controls channel, downgrade permission, accepted signing states and signer rotation. Validation rejects:

- source/target digest substitution;
- wrong package identity/version;
- same-version update;
- downgrade unless explicitly allowed;
- framework/platform/architecture/package-kind substitution;
- signing-state substitution;
- unexpected signer identity/rotation.

R12 deliberately chooses stricter same-architecture update semantics even though Windows MSIX can support some architecture transitions. The frozen acceptance requirement says wrong-architecture substitution must fail closed.

### Local update engine

`LocalUpdateEngine` is a bounded local-fixture state machine, not an OS installer:

1. verify current accepted tree;
2. verify candidate tree;
3. validate update manifest/policy;
4. copy candidate to bounded staging;
5. verify staged target;
6. rename current state to backup;
7. promote staged state;
8. verify promoted target;
9. retire backup only after success.

Any post-promotion failure restores and verifies the prior manifest before returning `ROLLED_BACK`. Stale staging/backup paths block operation rather than being silently overwritten. Paths must remain under one explicit workspace root.

## Framework packaging basis

- Microsoft documents MSIX as the modern Windows package format. Deployable MSIX packages require signing with a valid code-signing certificate, and installation also requires certificate trust on the device. Therefore R12.14 does not claim a deployable MSIX merely from semantic manifest generation.
- Microsoft App Installer update settings default to forward-only updates; `ForceUpdateFromAnyVersion` must be explicit to allow downgrade. Kodepoia mirrors this by defaulting `allow_downgrade=false`.
- Qt documents `windeployqt` as the Windows deployment tool that gathers Qt runtime dependencies into a deployable folder; that supports an archive/deployment-tree capability but does not by itself prove an installer/signing result.
- Tauri v2 updater/package signing requirements remain external toolchain semantics; R12.14 models signing/update identity without embedding a private key or manufacturing a signed claim.

Official references:

- https://learn.microsoft.com/windows/msix/package/signing-package-overview
- https://learn.microsoft.com/windows/msix/app-installer/update-settings
- https://learn.microsoft.com/windows/msix/app-package-updates
- https://doc.qt.io/qt-6/windows-deployment.html
- https://v2.tauri.app/plugin/updater/

## Security and rollback boundaries

- no shell strings, arbitrary argv, signing command, certificate path, private key or package-manager script is accepted by these contracts;
- no network update server is introduced; update source is a local verified fixture only;
- candidate bytes are never promoted before manifest and update-policy verification;
- failure never advances accepted version/state and must restore the verified prior tree;
- update audit events are ordered and bounded to non-secret digest/status information;
- signing state cannot be edited into PASS by changing display metadata;
- real install/signing claims remain subject to ProcessSandbox/Guardian/KodeSecrets and conditional exact-head runtime evidence.

## Acceptance boundary

R12.14 is acceptable without manual intervention if hosted CI proves the deterministic contracts and local update/rollback state machine on the exact candidate and no real installer/trust/signing claim is made. If a later acceptance step requires such a real OS semantic and hosted CI does not prove it, the conditional manual gate triggers and execution must stop before R12.15.
