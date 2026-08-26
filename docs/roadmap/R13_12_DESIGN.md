# R13.12 — DeviceLab provider-neutral matrices, physical/virtual routing + evidence — Design

## Status

Subdivision status: **IN_PROGRESS**.

Authorized normalized base: `fb05135c4a5e1b7177dd4c68e6f05f61a489594e`.

Dedicated branch: `r13/12-devicelab-matrices`.

Manual state: **CONDITIONAL / NOT TRIGGERED**.

## Objective

Unify the accepted R13.6 Android runtime-testing seam and R13.11 Apple Simulator/XCTest seam behind a provider-neutral DeviceLab contract without conflating execution context, device class, provider account state, or evidence scope.

DeviceLab is a routing/evidence authority, not an arbitrary remote-command runner. It does not add shell-string execution, direct cloud credentials, implicit billing, or synthetic physical-device certification.

## Current external provider baseline — 2026-08-26

Firebase Test Lab is optional capability evidence, not a mandatory architecture dependency. Current official documentation states that a Test Lab matrix is devices × test executions and that device configurations are identified by model, OS version, screen orientation and locale. Android Test Lab targets may be physical or virtual; the current iOS Test Lab offering uses physical devices. Test Lab testing/API quotas are project-scoped, and billed usage depends on project plan/usage.

Official references:

- https://firebase.google.com/docs/test-lab
- https://firebase.google.com/docs/test-lab/android/get-started
- https://firebase.google.com/docs/test-lab/ios/get-started
- https://firebase.google.com/docs/test-lab/usage-quotas-pricing

These mutable provider facts are versioned capability evidence and must not silently become permanent architecture constants.

## Provider-neutral model

`DeviceLabMatrixDefinition` binds:

- stable matrix identity;
- target platform (`ANDROID` or `IOS`);
- immutable artifact SHA-256;
- stable test-execution identity;
- one to 64 bounded device configurations;
- device model;
- OS version;
- locale;
- orientation;
- explicit target class (`VIRTUAL` or `PHYSICAL`).

Input order is normalized before hashing, so semantically identical matrices have identical canonical digests. Duplicate configurations are rejected.

`DeviceLabProviderCapability` describes only observed/authorized provider capability. It cannot manufacture availability from configuration text. Supported providers in R13.12 are:

- `LOCAL_ANDROID` — Android ADB/emulator/device capability, with physical support only when explicitly observed/authorized;
- `XCODE_SIMULATOR` — iOS virtual-only, reusing the accepted R13.11 simulator seam;
- `HOSTED_CI` — execution context capable of virtual/simulator evidence only; it may not claim physical-device support merely because a hosted runner exists;
- `FIREBASE_TEST_LAB` — optional external provider. Android capability may expose physical and/or virtual classes; iOS capability is physical-only under the current documented provider offering.

Capability states are explicit: `AVAILABLE`, `UNAVAILABLE`, `ACCOUNT_REQUIRED`, `QUOTA_EXCEEDED`, `BUDGET_EXCEEDED`, `UNSUPPORTED`.

## Deterministic routing

`select_provider()` accepts a matrix, a bounded capability set and an explicit maximum cost. It:

1. filters by exact platform;
2. requires the provider to support every target class present in the matrix;
3. requires `AVAILABLE` capability;
4. enforces the caller's cost ceiling;
5. applies deterministic local-first ranking: platform-local provider first, hosted virtual context second, optional Firebase last;
6. binds the route to matrix digest, artifact digest and capability digest.

A paid/cloud route is never selected by default because the default cost budget is zero.

## Account, quota and cost boundary

Firebase credentials are represented only by the presence of an authorized account reference; secret values never enter DeviceLab data. An available Firebase capability additionally requires a hashed project scope. Missing account state is `ACCOUNT_REQUIRED`, not PASS. Exhausted quota or budget is explicit and non-routable.

Provider quota and cost values are bounded. Budget alerts or provider account plans are not treated as hard cost caps unless Kodepoia's own explicit DeviceLab budget rejects the route.

## Lease and retry model

`DeviceLabLease` binds:

- stable lease id;
- exact route digest;
- exact matrix digest;
- exact artifact digest;
- bounded timeout (1..7200 seconds);
- bounded retry count (0..3).

Matrix, artifact or route substitution is rejected before execution/result acceptance.

## Normalized provider result

`DeviceLabNormalizedResult` binds:

- exact source Git SHA;
- provider identity;
- matrix SHA-256;
- artifact SHA-256;
- underlying provider-result/evidence SHA-256;
- pass/fail state;
- target class;
- physical-device proof boolean;
- bounded cost;
- explicit blockers.

Virtual/simulator evidence cannot set `physical_device_proven=true`. `XCODE_SIMULATOR` and `HOSTED_CI` can never manufacture physical-device proof. Provider results cannot be replayed against another matrix or artifact digest.

The underlying R13.6 and R13.11 exact-head evidence remains authoritative for actual Android emulator and iOS Simulator execution. R13.12 normalizes their verified digests; it does not weaken their platform-specific validators.

## Durable evidence

`DeviceLabEvidenceBundle` and `schemas/r13/devicelab-evidence.schema.json` bind matrix, route, lease and normalized results. A PASS bundle requires:

- schema version 1;
- one to 64 normalized results;
- lease/route/matrix/artifact consistency;
- provider identity consistency;
- every normalized result PASS;
- cleanup complete;
- no synthetic blocker-free failure state.

## Security and governance invariants

- no shell command strings;
- no model-supplied executable path, device id, provider endpoint, credential or billing action;
- network remains off by default;
- cloud execution requires explicit future provider adapter authorization, KodeSecrets reference, bounded endpoint, permission and budget;
- missing account/quota/device is never PASS;
- provider/account metadata cannot certify a device class it did not actually execute;
- simulator/virtual evidence is partitioned from physical evidence;
- result provenance is digest-bound and anti-replay;
- physical-only/manual claims remain separate from core acceptance.

## Manual gate

**CONDITIONAL / NOT TRIGGERED.** Core R13.12 is accepted through deterministic contracts/tests plus the already accepted hosted Android emulator and iOS Simulator seams. A live Firebase account, billing plan, service-account credential, physical device allocation or live cloud matrix is not required.

Trigger the manual gate only if a frozen R13.12 claim is later found to specifically require real physical-provider execution that accepted CI cannot prove. If triggered, stop before R13.13 and provide bounded user-controlled collection instructions without requesting secrets in chat.
