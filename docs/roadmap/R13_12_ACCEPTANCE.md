# R13.12 — DeviceLab provider-neutral matrices, physical/virtual routing + evidence — Acceptance

## Status

Subdivision status: **IN_PROGRESS**. This document defines the acceptance contract and does not predeclare PASS.

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

`tests/test_r13_12_devicelab.py` and `tests/test_r13_12_devicelab_evidence.py` must pass and cover at minimum:

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

The accepted technical candidate must have, on the **same exact SHA**:

- R0 Repository Guard — SUCCESS;
- Python Core — SUCCESS;
- KodeStudio UI Smoke — SUCCESS;
- R13 Android Device Acceptance — SUCCESS;
- R13 Apple XCTest Acceptance — SUCCESS.

No new live-provider workflow is required for core R13.12 because this subdivision deliberately does not introduce a credentialed external Test Lab execution seam. If a live Firebase adapter is later added to this subdivision before acceptance, a dedicated exact-head provider workflow becomes mandatory and the acceptance contract must be updated before it runs.

Any byte change after decision-making results creates a new candidate and invalidates those results for merge.

## End synchronization and merge

After a technical candidate passes the required gates:

1. update `R13_PLAN.md` and continuity in the same work cycle so R13.12 becomes `COMPLETE` and R13.13 remains `PLANNED`;
2. record the exact-head run identities and any durable provider-neutral evidence digest;
3. rerun all required gates on the new end-synchronized exact head;
4. merge the implementation PR using `expected_head_sha` only if every required gate is SUCCESS;
5. create exactly one continuity-only post-merge normalization branch/PR;
6. require fresh exact-head R0 + Python Core + KodeStudio UI Smoke on the normalization head;
7. merge normalization with `expected_head_sha`;
8. only then may R13.13 start.

## Manual gate

**CONDITIONAL / NOT TRIGGERED** unless the frozen R13.12 acceptance claim is found to require physical-provider behavior that cannot be proven using accepted local/hosted seams. If triggered, stop before R13.13 and provide bounded prerequisites, commands/actions, expected evidence path and recovery/privacy instructions. Never request passwords, private keys, service-account JSON or tokens in chat.
