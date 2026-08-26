# R13.10 Design — Apple identity, entitlements, signing/provisioning, archive/export

**Subdivision:** R13.10  
**Architecture:** v1.0 frozen  
**Manual state:** CONDITIONAL / NOT TRIGGERED

## Objective

R13.10 adds a deterministic Apple signing/archive model on top of the accepted R13.8 Xcode capability bridge and R13.9 SwiftUI/Xcode scaffold. It does not create or store production credentials and does not claim App Store acceptance.

## Security and architecture rules

- Public identity and private signing material are separate. Durable state may contain Team ID, bundle ID, provisioning-profile UUID, public certificate SHA-256 fingerprint, entitlement allowlist and export intent. Private certificates, private keys, passwords and provisioning payloads are represented only by `SecretRef` values owned by `KodeSecrets`.
- The provisioning profile is modeled as an authorization allowlist. Every entitlement claimed by the archive definition must be authorized by the profile model; wildcard authorization may match a concrete claim, but wildcard values are rejected in application claims.
- Capability intent maps through a repository-owned allowlist. Project/model text cannot inject arbitrary entitlement names.
- Simulator builds stay independent from production signing. The unsigned simulator mode rejects team/profile/certificate identities and secret references.
- Xcode process arguments are fixed typed tuples. No raw build-setting list, shell command, arbitrary destination or model-supplied signing flag is accepted.
- Archive/export paths remain inside the configured staging boundary. Export uses a generated `ExportOptions.plist` containing public metadata only; no secret value appears in argv.
- Absence of private credentials is not converted into a false PASS. A valid distribution metadata model without private signing refs reports `DISTRIBUTION_CREDENTIALS_REQUIRED`, with `distribution_signing_capable=false`.
- Live App Store upload/publication, account mutation, certificate generation and provisioning-profile generation are outside R13.10 core acceptance.

## Durable contracts

`kodepoia.mobile.apple_signing` introduces:

- `AppleSigningMode`: `UNSIGNED_SIMULATOR`, `DEVELOPMENT`, `AD_HOC`, `APP_STORE`.
- `AppleExportMethod`: `NONE`, `DEVELOPMENT`, `AD_HOC`, `APP_STORE_CONNECT`.
- `AppleSigningReadiness`: unsigned-simulator readiness, archive-metadata readiness, credentials-required, distribution-ready and blocked states.
- `AppleCapability`: explicit capability identifiers mapped to repository-owned entitlement keys.
- `AppleCertificateIdentity`: public SHA-256 fingerprint plus optional bounded public common name.
- `AppleProvisioningProfileIdentity`: public UUID, team/App-ID prefix, bundle pattern, certificate fingerprints and entitlement allowlist.
- `AppleSigningSecretRefs`: `SecretRef` references for certificate bundle, password and provisioning payload.
- `AppleArchiveDefinition`: bundle/scheme/signing/export intent, public identities, capabilities, claims, privacy-manifest expectation and secret references.
- `AppleSigningAssessment`: truthful readiness, credential requirement, privacy-manifest presence and blockers.

The canonical JSON schema is `schemas/r13/apple-signing-archive.schema.json`.

## Entitlement authorization

The initial allowlist is intentionally small and frozen for R13.10:

- system identity: `application-identifier`, `com.apple.developer.team-identifier`;
- common profile controls: `get-task-allow`, `keychain-access-groups`;
- capability claims: `aps-environment`, `com.apple.developer.associated-domains`, `com.apple.security.application-groups`.

Additional Apple capabilities must be added explicitly in a later accepted change; they are never accepted from arbitrary project text.

Authorization compares the concrete app claim against the public profile allowlist. Exact values must match. A profile value ending in `*` may authorize a matching concrete value; the app claim itself may not contain `*`.

## Archive and export model

`build_unsigned_archive_argv` creates a fixed Release archive command for `generic/platform=iOS` with `CODE_SIGNING_ALLOWED=NO` and `CODE_SIGNING_REQUIRED=NO`. This establishes archive mechanics without pretending the archive is distributable.

`render_export_options_plist` creates deterministic public metadata for the selected export method, manual signing style, Team ID and bundle-to-profile UUID mapping. `build_export_archive_argv` creates only the fixed `xcodebuild -exportArchive` argument shape. R13.10 core CI prepares but does not execute distribution export because no production private identity is supplied.

## Privacy manifest boundary

R13.10 provides a bounded `PrivacyInfo.xcprivacy` presence check. The hosted fixture adds a deterministic minimal privacy manifest to exercise the check. Broader required-reason API/store-policy validation remains R13.15 authority.

## Hosted acceptance

`.github/workflows/r13-apple-signing-archive-acceptance.yml` runs on hosted `macos-26` and:

1. executes focused R13.10 adversarial tests;
2. renders the accepted canonical SwiftUI fixture;
3. proves a no-signing simulator build;
4. proves a no-signing iOS archive is mechanically produced and contains archive metadata/application product;
5. evaluates a deterministic public profile/certificate fixture as `DISTRIBUTION_CREDENTIALS_REQUIRED` because no private `SecretRef` is supplied;
6. prepares deterministic export options and the fixed export argv but does not execute distribution export;
7. emits exact-head evidence validated by `schemas/r13/apple-signing-archive-evidence.schema.json`.

No Apple Developer membership, private key, password, App Store Connect token, physical device or live upload is used.

## Manual gate

Manual remains **CONDITIONAL / NOT TRIGGERED** for core acceptance. It triggers only if a later frozen claim specifically requires a real distribution signature, user-owned provisioning identity, physical-device behavior or live App Store/TestFlight operation that hosted CI cannot establish. If triggered, execution stops before R13.11 and the user receives bounded local instructions without sharing secrets in chat.
