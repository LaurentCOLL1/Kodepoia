# R13.12 — DeviceLab provider-neutral matrices, physical/virtual routing + evidence — Acceptance

## Status

Subdivision status: **COMPLETE for end synchronization**. The technical candidate has satisfied the frozen core acceptance claim; implementation merge and the single continuity-only post-merge normalization remain pending.

Manual state: **CONDITIONAL / NOT TRIGGERED**.

## Frozen core acceptance claim

R13.12 is accepted only when one exact source head proves all of the following:

1. DeviceLab matrix identity deterministically binds platform, artifact digest, test-execution identity, model, OS version, locale, orientation and explicit physical/virtual target class;
2. semantically identical matrices have the same digest regardless of input ordering, while duplicate/malformed/unbounded configurations fail closed;
3. provider capability is explicit and cannot become AVAILABLE from configuration text alone;
4. deterministic routing prefers accepted local/hosted zero-cost capability and does not silently choose a paid/cloud provider;
5. iOS virtual matrices route to the Xcode Simulator seam and cannot be satisfied by Firebase iOS physical capability;
6. Android physical routing requires an explicitly available physical-capable provider and an accepted budget;
7. missing Firebase account state remains `ACCOUNT_REQUIRED`; exhausted quota/budget is non-routable and never PASS;
8. hosted CI/simulator evidence cannot manufacture physical-device proof;
9. leases bind exact route, matrix and artifact digests with bounded timeout/retries;
10. normalized provider results cannot be replayed against another matrix or artifact digest;
11. durable DeviceLab evidence validates against `schemas/r13/devicelab-evidence.schema.json`, requires cleanup and binds only passing provider results for a PASS bundle;
12. accepted R13.6 Android emulator/device and R13.11 iOS Simulator/XCTest workflows remain green on the exact technical candidate, proving the provider-neutral layer did not regress the underlying real tool seams;
13. no live Firebase account, credential, billing mutation, cloud test submission or physical provider allocation is required for core acceptance.

## Accepted technical candidate

Exact source SHA: **`250c179590bc2b63b625b806cb5b1f1d618bd640`**.

Required exact-head gates on that SHA:

- R0 Repository Guard #1692 / `33016321788` — SUCCESS;
- Python Core #1666 / `33016321879` — SUCCESS;
- KodeStudio UI Smoke #1633 / `33016321824` — SUCCESS;
- R13 Android Device Acceptance #130 / `33016321843` — SUCCESS;
- R13 Apple XCTest Acceptance #22 / `33016321680` — SUCCESS.

The underlying real runtime seams also completed their exact-head evidence and cleanup paths. Android Device #130 provisioned the accepted API 36 toolchain/image, verified hosted KVM, built app + instrumentation APKs, launched the bounded emulator, ran governed ADB instrumentation, verified exact-head evidence, uploaded it and cleaned up. Apple XCTest #22 ran the accepted hosted `macos-26` simulator XCTest path, verified simulator-only exact-head evidence and uploaded it. No live Firebase/provider account or physical cloud execution was required.

Because this acceptance document now changes bytes after the technical candidate, this record is historical evidence only for `250c179...`; all five required gates must be rerun on the final end-synchronized head before merge.

## Explicit non-claims

R13.12 core acceptance does **not** claim:

- a Firebase/Google Cloud project is configured;
- live Test Lab quota or billing state has been queried;
- a Test Lab matrix has been submitted;
- a physical Android/iOS Test Lab device executed the canonical app;
- simulator/virtual evidence proves sensors, radios, thermal/performance or other hardware-only behavior;
- account/billing availability or future provider inventory is permanent.

Those states remain conditional provider evidence.

## Focused deterministic/adversarial tests

`tests/test_r13_12_devicelab.py` and `tests/test_r13_12_devicelab_evidence.py` pass as part of the accepted full Python gate and cover at minimum:

- deterministic matrix canonicalization;
- duplicate configuration rejection;
- invalid locale/model/version bounds;
- local-first zero-cost routing;
- Xcode Simulator vs Firebase iOS physical partitioning;
- explicit physical Android routing and cost ceiling;
- Firebase account-required state;
- exhausted-quota fail closed;
- hosted-CI physical-claim rejection;
- virtual result physical-proof rejection;
- matrix/artifact result anti-replay;
- lease route/matrix/artifact anti-substitution;
- failure blocker semantics;
- durable evidence determinism and JSON Schema validation;
- cleanup requirement.

## External-provider facts used as versioned evidence

Current official Firebase Test Lab documentation is used only to constrain the optional provider capability model:

- Test Matrix = devices × test executions;
- device configurations include model, OS version, orientation and locale;
- Android supports physical and virtual Test Lab device targets;
- current iOS Test Lab device targets are physical;
- testing/API quotas are project-scoped and pricing/quota availability may vary by project/plan.

Official sources:

- https://firebase.google.com/docs/test-lab
- https://firebase.google.com/docs/test-lab/android/get-started
- https://firebase.google.com/docs/test-lab/ios/get-started
- https://firebase.google.com/docs/test-lab/usage-quotas-pricing

## Exact-head required gates

The accepted final end-synchronized candidate must have, on the **same exact SHA**:

- R0 Repository Guard — SUCCESS;
- Python Core — SUCCESS;
- KodeStudio UI Smoke — SUCCESS;
- R13 Android Device Acceptance — SUCCESS;
- R13 Apple XCTest Acceptance — SUCCESS.

No new live-provider workflow is required for core R13.12 because this subdivision deliberately does not introduce a credentialed external Test Lab execution seam. If a live Firebase adapter is later added to this subdivision before acceptance, a dedicated exact-head provider workflow becomes mandatory and the acceptance contract must be updated before it runs.

Any byte change after decision-making results creates a new candidate and invalidates those results for merge.

## End synchronization and merge

1. update `R13_PLAN.md` and continuity in the same work cycle so R13.12 is `COMPLETE` and R13.13 remains `PLANNED`;
2. record the accepted technical candidate and the exact-head run identities above;
3. rerun all five required gates on the new end-synchronized exact head;
4. merge PR #243 using `expected_head_sha` only if every required gate is SUCCESS;
5. create exactly one continuity-only post-merge normalization branch/PR;
6. require fresh exact-head R0 + Python Core + KodeStudio UI Smoke on the normalization head;
7. merge normalization with `expected_head_sha`;
8. only then may R13.13 start.

## Manual gate

**CONDITIONAL / NOT TRIGGERED.** The frozen R13.12 core claim was established using deterministic provider-neutral validation plus the accepted hosted Android emulator and iOS Simulator seams. No physical provider/account-only behavior became required. If a later change before merge introduces such a frozen requirement, stop before R13.13 and provide bounded prerequisites, commands/actions, expected evidence path and recovery/privacy instructions. Never request passwords, private keys, service-account JSON or tokens in chat.
