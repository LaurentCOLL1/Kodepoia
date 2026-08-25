# R13.6 Acceptance — Android emulator/device testing + ADB instrumentation adapter

## Required candidate conditions

A candidate is eligible for R13.6 acceptance only when all of the following are true on one exact head:

1. `docs/roadmap/R13_6_DESIGN.md` and this acceptance record exist.
2. Focused R13.6 Python tests pass.
3. `schemas/r13/android-device-evidence.schema.json` is valid Draft 2020-12 and rejects additional fields such as a raw serial.
4. R0 Repository Guard passes.
5. full Python Core passes.
6. KodeStudio UI Smoke passes.
7. R13 Android Build Acceptance remains green because R13.6 consumes its staging/build seam.
8. R13 Android Signing Acceptance remains green because the accepted package/signing authority is still affected by Android package construction.
9. R13 Android Device Acceptance passes on the exact candidate SHA with a real hosted API 36 emulator.
10. manual state remains truthful.

Any byte change after evidence invalidates the decision and requires fresh exact-head gates.

## Focused adversarial acceptance

The test suite must prove at minimum:

- `adb devices -l` parsing distinguishes online/offline and rejects malformed/unbounded data;
- durable observation output contains a hash, not a raw serial;
- exactly one online virtual device is selected for hosted acceptance;
- offline/stale device state cannot satisfy a lease;
- wrong-device substitution is rejected;
- APK digest substitution is rejected;
- arbitrary `getprop` names are rejected;
- arbitrary instrumentation/shell text cannot become typed argv;
- logcat collection is line-bounded;
- instrumentation output without a positive `OK (N tests)` result cannot PASS;
- hosted emulator evidence cannot set `physical_device_claim=true`;
- evidence schema rejects unknown fields/raw serial injection.

## Real hosted emulator acceptance

Workflow: `.github/workflows/r13-android-device-acceptance.yml`.

Canonical hosted flow:

1. checkout exact PR/push SHA;
2. Python 3.12 + JDK 17 + Gradle 9.5.0;
3. Android platform/build-tools/platform-tools/emulator plus `system-images;android-36;google_apis;x86_64`;
4. create R13.4 exact-head canonical staging;
5. apply deterministic R13.6 instrumentation overlay;
6. build `:app:assembleDebug` and `:app:assembleDebugAndroidTest`;
7. create and launch one headless API 36 AVD;
8. require one online emulator and completed boot;
9. bind lease to emulator hash + main APK SHA-256;
10. install application and test APKs;
11. run only the fixed AndroidJUnitRunner component through `am instrument`;
12. require at least one passing instrumentation test;
13. collect bounded logcat digest only;
14. uninstall owned packages and require cleanup completion;
15. write strict `R13_6_ANDROID_DEVICE_ACCEPTANCE.json` tied to exact source SHA;
16. kill the owned emulator in an `always()` cleanup step.

The uploaded evidence must not include raw ADB serial, raw private device identifiers, unrestricted logs or a physical-device claim.

## Manual state

**CONDITIONAL / NOT TRIGGERED** unless the hosted emulator cannot prove the frozen core claim or a hardware-only claim is explicitly required. No physical device is required merely to mark this subdivision complete.

## Decision rule

R13.6 becomes `COMPLETE` only after the implementation candidate and the final end-synchronized head each pass their required exact-head gates. Merge must use `expected_head_sha`. Exactly one continuity-only post-merge normalization then passes R0/Python/UI and merges before R13.7 can start.
