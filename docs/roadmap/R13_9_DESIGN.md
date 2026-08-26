# R13.9 — iOS/iPadOS SwiftUI/Xcode deterministic scaffold — Design

## Scope

R13.9 generates a repository-owned Xcode/SwiftUI scaffold from the already accepted Project Wizard / Project DNA mobile intent and the shared logical app model. It does not introduce a second application architecture, does not own Apple signing/provisioning, and does not publish to App Store Connect.

The authorized base is normalized `main` `cd1e34321c57a7f6e25d1d1c17d084469761c8a3`; implementation branch is `r13/09-ios-swiftui-scaffold`.

## Apple platform baseline

Mutable Apple requirements remain dated evidence, not architecture constants. R13.9 depends on the R13.8 hosted Xcode capability seam. Core acceptance is a build for `generic/platform=iOS Simulator`; it is deliberately separate from physical-device and App Store signing claims.

Apple documents SwiftUI Observation support beginning with iOS/iPadOS 17. Therefore the scaffold selects one deterministic state strategy from the explicit deployment target:

- minimum iOS/iPadOS >= 17: `@Observable` / Observation;
- minimum below 17: `ObservableObject` / `@Published` compatibility mapping.

No project text can select an arbitrary Swift compiler flag, destination, executable or signing setting.

## Domain model

`AppleScaffoldDefinition` binds:

- accepted Apple bundle identifier from Project DNA;
- application display name;
- minimum and target iOS/iPadOS version intent;
- phone/tablet form factors;
- shared app-model SHA-256;
- deterministic localization catalogs;
- native-vs-Godot source identity;
- selected state strategy;
- optional `GodotIOSExportBridgeDefinition` metadata.

The Godot bridge is metadata only. It fixes the export preset to `iOS`, expects an `.xcodeproj` container, and records that execution remains owned by R5. R13.9 refuses to render a SwiftUI native project from a Godot-export definition.

## Deterministic generated workspace

`AppleScaffoldEngine` emits a fixed logical Xcode project named `KodepoiaIOS` containing:

- `KodepoiaIOS.xcodeproj/project.pbxproj`;
- a shared `KodepoiaIOS` scheme;
- SwiftUI `App`, `ContentView`, state model and shared contract projection;
- explicit `Info.plist`;
- `Assets.xcassets` catalog metadata;
- deterministic `.lproj/Localizable.strings` catalogs;
- a user-owned README;
- `.kodepoia/mobile/apple/workspace-manifest.json` after apply.

Generated paths are normalized relative POSIX paths. Traversal, reserved names, control characters, Windows separator injection and symlink escapes fail closed. File ownership mirrors the accepted R13.3 policy: Kodepoia-owned generated files may be replaced only when the previous manifest proves they are unmodified; user-owned files are preserved. Replacements require SafeChange + Backup and may emit Audit evidence.

## Shared app-model mapping

R13.9 consumes `DesktopAppModel` as the already accepted framework-neutral logical contract. The generated `AppModelContract.swift` binds the logical model digest plus state IDs, command IDs, service IDs and route paths. State fields are emitted as typed Swift properties. This is a platform projection, not a new source of truth.

## Xcode execution boundary

Rendering is pure and launches no process. Hosted compilation is a separate governed seam. `build_ios_simulator_build_argv` reuses `MobileToolchainBoundary` to validate the exact `xcodebuild` executable, project container and derived-data staging path. The invocation is fixed to:

- generated project container;
- stable scheme `KodepoiaIOS`;
- configuration `Debug`;
- destination `generic/platform=iOS Simulator`;
- bounded derived-data path;
- `CODE_SIGNING_ALLOWED=NO`;
- `CODE_SIGNING_REQUIRED=NO`;
- action `build`.

There is no raw destination/build-setting argument and no shell string.

## Durable schemas and evidence

R13.9 adds strict Draft 2020-12 schemas for:

- Apple scaffold definition;
- Apple workspace manifest;
- hosted SwiftUI Simulator build evidence.

Hosted build evidence binds the exact Git head, definition digest, manifest digest, shared app-model digest, observed Xcode/Simulator SDK versions, fixed destination/scheme/configuration, no-signing state and SHA-256 of the produced app executable. It explicitly states that no account/signing credential and no physical-device capability were used/proven.

## Manual boundary

Manual state is `CONDITIONAL / NOT TRIGGERED` while hosted `macos-26` can prove the frozen Simulator compile claim. Apple Developer membership, certificates/private keys, provisioning profiles, App Store Connect credentials and physical devices belong to later/conditional claims and are never requested for core R13.9 acceptance.
