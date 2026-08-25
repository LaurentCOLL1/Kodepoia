# R13.6 Design — Android emulator/device testing + ADB instrumentation adapter

## Status

Implementation design for R13.6. Architecture v1.0 remains frozen. R13.6 extends the accepted R13.1 tool boundary, R13.4 Android build staging, and R13.5 signing model; it does not create a parallel Android execution architecture.

## Objective

Provide deterministic, auditable Android runtime-test evidence while preventing an arbitrary `adb shell` surface, stale/offline/wrong-device substitution, artifact replay, raw device-serial persistence, unbounded logs, or a synthetic physical-device claim.

## Official compatibility baseline used for this subdivision

Observed 2026-08-25 from Android Developers:

- `adb devices -l` exposes serial, state and descriptive device fields and distinguishes operational `device` from `offline` connections: https://developer.android.com/tools/adb
- command-line tests can be driven through `adb shell am instrument`, including remote CI environments: https://developer.android.com/studio/test/command-line
- Android Emulator supports `-no-window` specifically for display-less servers: https://developer.android.com/studio/run/emulator-commandline
- stable AndroidX Test dependencies used by the acceptance overlay are `androidx.test:runner:1.7.0` and `androidx.test.ext:junit:1.3.0`: https://developer.android.com/jetpack/androidx/releases/test

These values are dated acceptance evidence, not permanent architecture constants.

## Runtime model

`src/kodepoia/mobile/android_device.py` provides pure models/parsers/typed argv builders. It does not provide a generic command executor.

### Device observation and redaction

`AndroidDeviceObservation` keeps the raw ADB serial only as ephemeral process-memory selection state. Durable output uses `device_sha256 = SHA256("adb-device-v1:" + serial)` and excludes the serial and transport ID. Public evidence may retain bounded product/model/device descriptors.

ADB states are explicit: `device`, `offline`, `unauthorized`, `no_permissions`, or `unknown`. Only `device` can enter a lease or PASS capability snapshot. `device` is still not treated as boot-complete until `sys.boot_completed=1` is observed.

### Device capability snapshot

A PASS snapshot records only bounded public runtime properties: hashed device identity, virtual/physical partition, boot completion, Android release, model, ABI, locale and density. Hosted R13.6 evidence requires `virtual=true` and may not assert a physical-device claim.

### Lease and anti-substitution

`AndroidDeviceLease` binds stable lease id, hashed device identity, exact application APK SHA-256 and bounded timeout. Every critical operation can re-check the lease. Offline/stale state, changed device hash or changed APK digest fails closed.

### Matrix contract

`AndroidDeviceMatrixEntry` models locale, portrait/landscape orientation, density and bounded network profile (`default`, `offline`, `wifi`). R13.6 establishes the durable matrix contract and proves the canonical default entry on a real hosted emulator. R13.12 later owns provider-neutral multi-device matrix routing; R13.6 does not overclaim full DeviceLab coverage.

## Typed ADB surface

The accepted adapter exposes only repository-owned builders for:

- `adb devices -l`;
- one selected serial via `-s`;
- `wait-for-device`;
- allowlisted `getprop` reads;
- fixed `wm density` read;
- APK install with `install -r`;
- package uninstall;
- fixed `shell am instrument -w -r <validated component>`;
- bounded `logcat -d -t <line-count>`;
- `emu kill` only for a serial beginning with `emulator-`.

There is no builder accepting arbitrary shell text, arbitrary shell tokens, model-selected subcommands, or raw environment command strings.

## Hosted acceptance staging

The R13.4 canonical source project remains unchanged. `scripts/r13_4_android_ci_acceptance.py prepare` creates the already-governed compatibility staging tree. R13.6 then applies a deterministic test-only overlay inside that staging tree:

- `testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"`;
- AndroidX Test Runner 1.7.0;
- AndroidX Test ext.junit 1.3.0;
- one canonical `R13DeviceSmokeTest` asserting the target package identity.

The overlay is hashed into `test_overlay_sha256` and bound into R13.6 evidence. This keeps the R13.3 source manifest immutable while proving a real instrumented runtime seam.

## Emulator lifecycle

CI infrastructure provisions public SDK packages, emulator and the API 36 Google APIs x86_64 system image. Kodepoia runtime does not silently install SDKs. The acceptance collector creates a named ephemeral AVD with typed argv, launches Android Emulator with bounded arguments including `-no-window`, waits for one online emulator and then waits for `sys.boot_completed=1`.

Cleanup is mandatory: uninstall instrumentation package if installed; uninstall application package if installed; persist PASS only if uninstall cleanup completed; workflow `always()` cleanup sends `adb -s <emulator> emu kill` only to virtual targets. Raw emulator logs are not uploaded as acceptance evidence.

## Evidence

`schemas/r13/android-device-evidence.schema.json` is strict and contains no raw serial field. PASS binds exact Git source SHA, public capability snapshot, device/APK lease, instrumentation APK SHA-256, R13.6 test overlay SHA-256, canonical matrix, instrumentation result digest/test count, bounded logcat digest/line count, cleanup completion and `physical_device_claim=false`.

## Manual gate

Manual status is **CONDITIONAL / NOT TRIGGERED** for core R13.6. Hosted emulator evidence is sufficient for the frozen acceptance claim. A future hardware-only claim that cannot be established in hosted CI must trigger a separate bounded manual collector and stop progression before the next subdivision; no private device identifier or credential may be pasted into chat.
