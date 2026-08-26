# R13.8 — Apple platform/Xcode capability bridge + macOS execution boundary

## Status

Implementation design for the dedicated `r13/08-apple-xcode-bridge` subdivision. The authorized base is normalized `main` `3a88f944a1424648fd4d1477c7c88b5da38e86dd`.

## Objective

R13.8 establishes a truthful, provider-neutral Apple host/toolchain capability boundary before R13.9 generates an iOS/iPadOS project. It does **not** sign, provision, archive, upload, publish, enroll devices, or contact App Store Connect.

The implementation extends the R13.1 mobile authority instead of adding a parallel process-launch surface.

## External baseline as versioned evidence

The snapshot dated 2026-08-26 records only mutable compatibility evidence:

- Apple production uploads require Xcode 26+ with the iOS/iPadOS 26 SDK+ since 2026-04-28.
- Apple App Store Connect release notes dated 2026-08-25 accept Xcode 27 beta 6 / iOS 27 beta 6 SDK builds for internal and external TestFlight testing.
- A beta/TestFlight-capable toolchain must never manufacture a stable production-upload claim.
- GitHub-hosted macOS runner-image documentation is advisory discovery evidence only. Exact capability is derived from runtime probes on the exact source head.

The snapshot expires. Stale policy evidence blocks current production/TestFlight capability claims rather than silently remaining valid forever.

## Architecture

### Existing authority reused

`MobileToolchainBoundary` remains the sole R13 tool/path/argv construction boundary. R13.8 extends it with fixed Apple operations only:

- `xcodebuild -version`;
- `xcrun --sdk iphoneos --show-sdk-version`;
- `xcrun --sdk iphonesimulator --show-sdk-version`;
- `xcrun simctl list runtimes --json`;
- `xcrun simctl list devices --json`;
- bounded `xcodebuild -project|-workspace ... -list -json`;
- bounded `xcodebuild -project|-workspace ... -scheme <stable-id> -showdestinations`.

There is no raw command string, arbitrary `xcodebuild` action, arbitrary build setting, arbitrary destination, shell fragment, or model-selected executable path.

### `apple_xcode.py`

The Apple capability model contains:

- `AppleXcodePolicySnapshot`: dated official-source policy evidence and expiry;
- `AppleXcodeChannel`: `STABLE`, `BETA`, `UNVERIFIED`;
- `AppleSDKIdentity`: public `iphoneos` / `iphonesimulator` versions;
- `AppleSimulatorRuntime`: public runtime identity/availability only;
- `AppleExecutorDescriptor`: provider-neutral non-interactive executor contract with bounded timeout, cancellation support and logical staging/output scopes;
- `AppleXcodeCapabilityEvidence`: exact-head durable evidence binding Xcode/XCRUN public identities, SDKs, simulator capabilities, executor, policy digest and readiness.

Existing `MobileToolchainIdentity`, `MobileArchitecture`, `MobileHostOS`, `MobileToolKind` and `MobileCapabilityState` are reused.

### Readiness semantics

`PRODUCTION_UPLOAD_TOOLCHAIN_READY` means only that the **probed stable Xcode/SDK toolchain** satisfies the dated production upload minimum. It does not mean the application is signed, provisioned, archived, accepted by Apple, or publishable. Those concerns remain R13.10/R13.11.

`TESTFLIGHT_BETA_TOOLCHAIN_READY` means the dated policy snapshot recognizes the probed beta major for TestFlight. It is explicitly incompatible with `production_upload_toolchain_capable=true`.

`DEVELOPMENT_READY` means the tools are usable but do not satisfy a stronger dated release-toolchain claim.

`BLOCKED` is used for stale policy, unverified Xcode channel, absent iOS simulator runtime/device, or other evidence that prevents a truthful capability claim.

## Hosted execution boundary

The canonical acceptance provider is GitHub-hosted macOS 26. The workflow checks out the exact evidence SHA and probes the tools installed on that runner. The Python collector:

1. resolves `xcodebuild` and `xcrun` from the host;
2. validates them against bounded system runtime roots and exact tool names;
3. constructs every argv through `MobileToolchainBoundary`;
4. runs with `subprocess.run(..., shell=False, timeout=...)` only in the acceptance collector;
5. parses bounded public output;
6. emits no executable paths, credentials, certificate material, provisioning material, Apple team ID, device UDID or secret;
7. schema-validates the durable JSON before upload.

Kodepoia runtime still does not silently install Xcode or execute arbitrary project-supplied commands.

## Stable versus beta fail-closed rule

The 2026-08-26 policy snapshot recognizes stable major 26 and TestFlight beta major 27. A future/unrecognized Xcode major is `UNVERIFIED` and blocks release-readiness until the policy evidence is explicitly refreshed. This deliberately favors false-negative capability over a fabricated production claim.

## Simulator and physical-device partitioning

R13.8 proves only host Xcode/SDK/simulator capability. `physical_device_capability_proven` is hard false in this evidence model. Physical device execution and TestFlight state are later scoped to R13.11/R13.12.

## Security and privacy boundaries

- no Apple account requirement;
- no Developer Team ID requirement;
- no signing certificate/private key;
- no provisioning profile;
- no App Store Connect API key/token;
- no physical device identifier;
- no network-enabled store operation;
- no arbitrary remote executor endpoint;
- no raw environment override beyond the already accepted R13.1 allowlist.

The executor contract defaults to `interactive=false` and `network_allowed=false` and has a bounded timeout with cancellation capability.

## Durable schema

`schemas/r13/apple-xcode-capability.schema.json` is Draft 2020-12, `additionalProperties=false` throughout relevant durable objects, and explicitly contains only public capability evidence.

## Manual gate

`CONDITIONAL / NOT TRIGGERED` at implementation start. Hosted CI is the first authority. Only if the frozen Xcode/macOS capability cannot be demonstrated on accepted hosted CI may manual evidence be requested. User credentials must never be requested in chat.
