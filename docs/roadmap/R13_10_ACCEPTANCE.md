# R13.10 Acceptance — Apple signing/provisioning/archive/export

## Required exact-head gates

A candidate is acceptable only when the same exact head passes:

- R0 Repository Guard;
- full Python Core;
- KodeStudio UI Smoke;
- R13 Apple Xcode Acceptance;
- R13 Apple SwiftUI Scaffold Acceptance;
- R13 Apple Signing Archive Acceptance.

Any byte change after a decision-making run requires fresh gates.

## Focused acceptance criteria

- Apple Team ID, provisioning-profile UUID, bundle ID/pattern and certificate SHA-256 identities are bounded and malformed substitutions fail closed.
- Capability intent maps only to repository-owned entitlement keys; unknown entitlement injection is rejected.
- Claimed entitlements must be authorized by the modeled provisioning-profile allowlist. Team/application identifier mismatch, bundle mismatch, wrong profile UUID and wrong certificate substitution block readiness.
- Wildcards are authorization rules only; wildcard claims are not accepted as application entitlements.
- `KodeSecrets` durable state contains only `SecretRef` namespace/key pairs. Known secret values cannot occur in the archive definition, evidence or process argv.
- `UNSIGNED_SIMULATOR` carries no team/profile/certificate/private refs and remains independent of distribution signing.
- Missing production credentials on otherwise valid distribution metadata returns `DISTRIBUTION_CREDENTIALS_REQUIRED`, never `DISTRIBUTION_READY` and never synthetic App Store PASS.
- Providing a complete set of test `SecretRef` values may make the local model `DISTRIBUTION_READY`; this proves state semantics only and does not prove that referenced credentials exist or that Apple accepted an artifact.
- Privacy-manifest presence is checked explicitly; a required missing `PrivacyInfo.xcprivacy` is a blocker.
- Archive and export builders reject scheme injection, path escape and unsupported suffixes.
- Export options are deterministic and contain public Team/profile mapping only.

## Hosted macOS evidence contract

The dedicated workflow must produce `R13_10_APPLE_SIGNING_ARCHIVE.json` bound to the exact source SHA. Required claims:

- simulator build succeeds with signing disabled;
- unsigned generic-iOS archive succeeds mechanically;
- `.xcarchive/Info.plist` and the application product exist;
- `code_signing_allowed=false` and `code_signing_required=false`;
- public signing metadata assessment is `DISTRIBUTION_CREDENTIALS_REQUIRED`;
- `distribution_signing_capable=false` and `distribution_credentials_required=true`;
- export method is `APP_STORE_CONNECT`, export options are prepared, but `export_attempted=false`;
- no Apple account/signing credential is used;
- no physical-device capability is claimed;
- no live App Store acceptance is claimed;
- `blockers=[]` for the frozen non-production R13.10 core claim.

The evidence schema is `schemas/r13/apple-signing-archive-evidence.schema.json`.

## Rejection conditions

Reject a candidate if any required exact-head gate fails, if the hosted archive cannot be produced without signing, if a secret-shaped value enters durable evidence/argv, if entitlement/profile substitution is accepted, if a missing credential is converted to PASS, or if documentation/status is stale relative to the candidate head.

## Manual state

**CONDITIONAL / NOT TRIGGERED** for core acceptance. Production distribution signing, live export/upload or physical-device evidence is not required. If one of those claims becomes required, stop before R13.11 and request bounded user-controlled evidence without requesting private keys/passwords/tokens in chat.
