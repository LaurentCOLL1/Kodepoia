# R13.2 — Project DNA / KodeProduct mobile profiles + Project Wizard target selection

## Scope

R13.2 extends the accepted R2 Project DNA, KodeProduct and KodeStudio Project Wizard. It does not create a second mobile project authority and does not execute a mobile toolchain.

The subdivision carries **intent only**. Selecting Android or iOS in the Wizard cannot install an SDK, invoke Gradle/Xcode, access a device, sign an artifact, contact a store, or publish a release. Those capabilities remain capability-gated in later R13 subdivisions.

## Compatibility rule

Project DNA remains schema version 1. `mobile` is an optional field exactly like the R12 `desktop` extension. A pre-R13 DNA document with no mobile intent loads and serializes without gaining a `mobile` key or any other semantic data.

`ProjectType.MOBILE_APP` is added for native mobile applications. Existing project types retain their prior values. A `GAME` may target Android/iOS through the existing Godot game path; it does not become a `MOBILE_APP`.

## Mobile Project DNA profile

`MobileProjectProfile` records bounded declarative intent:

- source kind: `native` or `godot_export`;
- phone/tablet form factors;
- Android application ID plus minimum/target API intent;
- Apple bundle ID plus minimum/target OS intent;
- requested package kinds;
- permission and capability names as structured identifiers, never raw manifest/entitlement text;
- network intent;
- release channel intent;
- signing intent without credential/key material;
- bounded package/build/device-matrix budgets.

Platform-specific fields are rejected when their platform is absent. Android package kinds cannot certify Apple output and Apple package kinds cannot certify Android output.

## Source and project-type partition

The following combinations are authoritative:

| Project type | Mobile source | Allowed mobile targets | Meaning |
| --- | --- | --- | --- |
| `mobile_app` | `native` | Android and/or iOS only | Native application intent |
| `game` | `godot_export` | Android/iOS may coexist with other game targets | Existing Godot game exported to mobile |

`native` on a game, `godot_export` on a native mobile app, a non-Godot game using the Godot export route, or a `mobile_app` with desktop/web/XR platforms fail closed.

## Platform identity boundary

Android documents `applicationId` as the app identity used by both the device and Google Play and warns that changing it after publication causes Play to treat the upload as a different application. R13.2 therefore models it as explicit durable intent and never derives it from mutable toolchain output.

Official reference: https://developer.android.com/build/configure-app-module

Apple documents the bundle ID as the unique app identifier, with alphanumeric, hyphen and period characters and reverse-DNS format. Apple also requires the built bundle identifier to match App Store Connect for an uploaded app. R13.2 keeps the bundle identity distinct from display name, team/signing state and store state.

Official references:

- https://developer.apple.com/help/glossary/bundle-id/
- https://developer.apple.com/documentation/bundleresources/information-property-list/cfbundleidentifier

R13.2 defaults new unclaimed project identities to `org.kodepoia.<normalized-project-name>`. This is only deterministic local project intent; it does **not** claim that an identifier is available in Google Play, Apple Developer or App Store Connect. Account/provider availability is a later capability/compliance concern.

## Mutable platform values

The Wizard currently seeds Android target API intent at 36 because the accepted R13 planning baseline uses the Google Play API 36 transition effective 2026-08-31. This is a default intent, not a permanent architecture constant and not store-readiness evidence. R13.15 owns effective-date compliance evaluation.

Likewise Apple minimum/target OS intent is declarative. R13.2 does not claim that a selected version is supported by a particular installed Xcode; R13.8 capability-probes the real Apple toolchain.

## KodeProduct mapping

R13.2 uses the accepted R12 pattern rather than changing the ProductSpec schema:

- deterministic `mobile.*` constraints are derived from the accepted mobile DNA profile;
- the reserved P0 requirement `MOBILE-TARGET` binds target platforms, durable identifiers and release/signing/network intent;
- repeated mapping is idempotent;
- a user/model-authored conflicting `MOBILE-TARGET` is rejected rather than overriding Project DNA authority.

No raw Gradle property, Xcode build setting, signing password, provisioning profile, store token or executable argument is representable through this mapping.

## Existing Wizard integration

`kodepoia.kodestudio.r13_project_wizard` wraps the accepted R12 Project Wizard. KodeStudio's Projects page now opens that wrapper, so there remains one visible project creation flow.

Adaptive behavior:

- `mobile_app` enables only Android/iOS and locks source to `native`;
- a game with Android/iOS locks mobile source to `godot_export` and preserves its normal game targets;
- unrelated project types disable Android/iOS through this mobile-app path;
- Android-only fields are disabled unless Android is selected;
- Apple-only fields are disabled unless iOS is selected;
- the mobile tab states explicitly that it is intent-only.

Controls have accessible names/descriptions. R13-specific strings are registered in a source catalog and exercised through pseudo-localization (`qps-ploc`).

## Security / governance

R13.1 remains authoritative for identifier grammar and platform contracts. R13.2 adds no process runner, filesystem executable discovery, network client, signing adapter or store API.

Adversarial requirements include rejection of:

- shell/Gradle/Xcode fragments smuggled into identifiers, permission names or profile schemas;
- invalid min/target version relationships;
- platform/package mismatches;
- hidden platform fields for an unselected platform;
- reserved Product requirement substitution;
- unknown durable profile properties such as `raw_gradle_args` or `xcode_build_setting`.

## Manual state

**NONE.** R13.2 acceptance needs only deterministic model/schema/UI behavior and the normal exact-head repository gates. No Android SDK, Xcode installation, device, signing identity, Play Console or Apple account is required.
