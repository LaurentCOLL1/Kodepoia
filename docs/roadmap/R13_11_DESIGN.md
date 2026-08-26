# R13.11 — iOS Simulator/XCTest, device/TestFlight evidence adapter — Design

## Status

R13.11 is **IN_PROGRESS** on dedicated branch `r13/11-ios-simulator-xctest-testflight`, created exactly from normalized R13.10 `main` `5c92b43cb407fb359bd692ba60a9862cb19b4201`.

Manual intervention is **CONDITIONAL / NOT TRIGGERED** for the frozen core claim.

## Objective

R13.11 adds a governed Apple runtime-test seam on top of the accepted R13.8 Xcode boundary, R13.9 deterministic SwiftUI/Xcode scaffold, and R13.10 signing/archive state model. It does not introduce a new project architecture, a second state model, arbitrary Xcode controls, production signing, automatic App Store Connect access, or automatic TestFlight distribution.

The frozen core claim is deliberately narrow and auditable:

1. render the canonical R13.9 SwiftUI project and bind its accepted shared app-model digest;
2. add a repository-owned XCTest target through a deterministic, fail-closed overlay;
3. discover/select one available iOS Simulator from structured `simctl` output;
4. run real XCTest on hosted `macos-26` with signing disabled;
5. retain the native `.xcresult` bundle and derive a bounded structured test summary;
6. persist simulator-only evidence that cannot be reinterpreted as physical-device or TestFlight proof;
7. model TestFlight/App Store Connect as a separate optional remote capability that is `UNAVAILABLE` without an explicit authorized credential reference.

## Authority reuse

R13.11 reuses, rather than replaces:

- R13.1 `MobileToolchainBoundary` for allowlisted executable identity, project roots, staging roots and structured argv;
- R13.8 `xcodebuild` / `xcrun` / `simctl` capability and hosted-macOS authority;
- R13.9 `AppleScaffoldEngine`, canonical SwiftUI project, shared Xcode scheme and shared app-model contract;
- R13.10 rule that simulator execution is independent of production signing/provisioning credentials;
- R1/R6/R8/R12 security, budget, evidence, provenance and package/release boundaries.

No model/project text may inject a raw destination, simulator command, Xcode build setting, result path, TestFlight endpoint, token, signing identity or arbitrary command.

## Simulator identity and selection

`parse_simctl_devices` consumes bounded JSON only. Every accepted iOS simulator candidate has:

- valid CoreSimulator runtime identity;
- valid CoreSimulator device-type identity;
- valid UUID-form UDID;
- explicit availability and bounded state;
- normalized iOS version.

Selection is deterministic: usable `Booted`/`Shutdown` devices are ranked by highest iOS runtime, then phone preference, then stable name/UDID ordering. The raw UDID is an ephemeral execution locator only. Durable evidence records `SHA-256(lowercase(UDID))`; it never persists the raw UDID.

The adapter also provides a bounded simulator-create argv using a repository-owned constant device name. The hosted canonical acceptance normally selects an already provisioned GitHub runner simulator rather than mutating the host unnecessarily.

## XCTest overlay

R13.9 remains the source of the app Xcode project. R13.11 overlays only the ephemeral acceptance workspace with:

- `KodepoiaIOSTests` application-hosted unit-test target;
- deterministic PBX object identities;
- explicit dependency on `KodepoiaIOS`;
- `TEST_HOST=$(BUILT_PRODUCTS_DIR)/KodepoiaIOS.app/KodepoiaIOS`;
- app Debug `ENABLE_TESTABILITY=YES` while Release is explicitly left non-testable;
- shared scheme testable entry;
- repository-owned `XCTestCase` source and test bundle Info.plist.

The overlay verifies exact canonical R13.9 markers and cardinality. Renderer drift or a previously applied overlay fails closed rather than selecting an arbitrary occurrence.

The canonical test target binds the existing R13.9 shared model by asserting the generated `KodepoiaAppModelContract.logicalModelSHA256`. A second test asserts that the runtime evidence scope is simulator-only.

## Governed execution

The acceptance collector uses only typed argv and `subprocess.run(..., shell=False)`:

- `xcrun simctl list devices --json`;
- `xcrun simctl boot <validated-UDID>` when needed;
- `xcrun simctl bootstatus <validated-UDID> -b`;
- fixed `xcodebuild ... -destination id=<validated-UDID> -derivedDataPath <staging> -resultBundlePath <staging/*.xcresult> CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO test`;
- `xcrun xcresulttool get test-results summary --format json --path <bounded-result-bundle>`.

No raw user destination and no arbitrary `xcodebuild` setting is accepted.

## `.xcresult` evidence

Apple's current Xcode result-bundle interface is used rather than log scraping. The native `.xcresult` bundle remains an uploaded CI artifact. R13.11 derives a strict summary containing:

- overall result;
- total test count;
- passed/failed/skipped counts;
- expected failures.

The native result-bundle tree is content-hashed using stable relative paths and file bytes, under a bounded 512 MiB evidence budget. The structured evidence binds that digest, the exact source SHA, XCTest plan digest, R13.9 workspace-manifest digest and shared app-model digest.

Core acceptance requires a passing result with at least the two canonical tests.

## Evidence partitioning

The durable scope enum is explicit:

- `SIMULATOR` — virtual CoreSimulator evidence;
- `PHYSICAL_DEVICE` — reserved for actual device evidence;
- `TESTFLIGHT` — reserved for actual App Store Connect/TestFlight remote evidence.

The R13.11 core evidence schema fixes `scope=SIMULATOR`, `physical_device_capability_proven=false`, and `signing_credential_used=false`.

A simulator PASS therefore cannot certify camera/sensor/radio/hardware-performance/device-only semantics. Apple documentation itself distinguishes simulated from physical-device behavior; those claims remain separate conditional evidence.

## TestFlight / App Store Connect capability

TestFlight is not inferred from XCTest. A build becomes remote TestFlight evidence only through an authorized App Store Connect flow after upload and processing.

The local capability state machine is fail-closed:

- `UNAVAILABLE` — no credential reference; no network query attempted; blocker recorded;
- `READY_TO_QUERY` — an explicit authorized credential reference exists, but no remote state is yet claimed;
- `QUERY_FAILED` — an authorized live query was attempted but did not produce proof;
- `REMOTE_STATE_PROVEN` — only an actual credentialed remote adapter may produce this state.

Core R13.11 acceptance intentionally uses `UNAVAILABLE`. No Apple Developer membership, App Store Connect token, production signing material, live upload, beta group or tester enrollment is required.

## Secret and privacy boundary

Durable simulator evidence excludes raw UDID and rejects account/signing secret vocabulary. Production credentials belong exclusively to KodeSecrets references. Tokens, private keys, passwords, certificate private material and provisioning secrets must never enter source, argv, logs or acceptance JSON.

## Current official-source basis — 2026-08-26

External facts are evidence inputs, not frozen architecture constants:

- Apple documents running apps on simulated and physical devices and notes that simulator behavior does not cover all hardware/device characteristics.
- Xcode's current `xcresulttool` exposes `get test-results summary` for structured XCTest result extraction from `.xcresult` bundles.
- App Store Connect/TestFlight documentation treats uploaded/processed builds as the remote distribution authority; local XCTest does not create TestFlight state.

Planning/research references:

- https://developer.apple.com/documentation/xcode/running-your-app-in-simulator-or-on-a-device
- https://developer.apple.com/documentation/xcode-release-notes/xcode-16_3-release-notes
- https://developer.apple.com/help/app-store-connect/test-a-beta-version/testflight-overview/
- https://developer.apple.com/help/app-store-connect/manage-builds/upload-builds/

## Manual gate

**CONDITIONAL / NOT TRIGGERED.** Hosted macOS Simulator/XCTest is sufficient for the frozen core claim. If a later frozen R13.11 requirement is proven to depend on a physical Apple device or live TestFlight/App Store Connect state, execution must stop before R13.12 and request only bounded user-controlled evidence. Passwords, private keys and tokens are never requested in chat.
