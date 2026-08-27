# R13.14 — Mobile diagnostics acceptance

**Subdivision:** R13.14  
**Branch:** `r13/14-mobile-diagnostics`  
**Authorized normalized base:** `69efa1f5cf92ae3c3ce4040fe5abe54faae2ed8b`  
**Status:** COMPLETE / END-SYNC IN PROGRESS  
**Manual:** CONDITIONAL / NOT TRIGGERED

## Frozen acceptance claim

R13.14 is accepted only if the repository proves, on one exact implementation head, that mobile diagnostic evidence can be ingested and exported with bounded source handling, deterministic redaction, immutable release/artifact correlation, platform/source separation and no hidden continuous telemetry.

The acceptance claim does **not** require or imply:

- live Google Play or App Store diagnostic retrieval;
- Firebase/Crashlytics credentials or project access;
- production signing credentials;
- a physical Android/iOS device;
- automatic MetricKit subscription/delivery;
- remote telemetry upload;
- legal/privacy certification;
- universal OEM/device ANR or performance thresholds.

## Required implementation artifacts

The candidate contains:

- `src/kodepoia/mobile/diagnostics.py`;
- `schemas/mobile-diagnostics-v1.schema.json`;
- `tests/test_mobile_r13_14_diagnostics.py`;
- `docs/roadmap/R13_14_DESIGN.md`;
- this acceptance document;
- synchronized `docs/roadmap/R13_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md`.

No dedicated external-tool workflow is required unless implementation introduces a new real device/account/tool seam. The accepted core implementation does not.

## Focused acceptance matrix

| Area | Required result |
| --- | --- |
| Source integrity | SHA-256 verified before parsing; mismatch rejected |
| Input bounds | >2 MiB source rejected; invalid UTF-8/NUL rejected |
| Platform separation | Android source cannot certify Apple and vice versa |
| Provider separation | ADB/Android runtime/Play cannot certify Apple; Xcode/App Store/TestFlight cannot certify Android |
| Apple taxonomy | Crash, Jetsam, console and XCTest remain distinct source kinds |
| Redaction | Authorization credentials, common secret assignments, email/IP/home paths and explicit sensitive values removed before durable serialization |
| Raw payload privacy | Durable entry contains redacted text, not raw source bytes |
| Release correlation | Cross-release and cross-artifact substitution rejected |
| Fingerprints | Crash/ANR/Jetsam/test/performance fingerprint kinds are source-compatible and deterministic |
| Jetsam semantics | Memory termination remains distinct from crash |
| Performance | Metrics finite/non-negative/bounded; percentages 0..100; snapshot binds an entry from same bundle |
| Retention | 1..90 day policy intent; global bundle <=16 MiB; <=256 entries |
| Export | Explicitly disable-able; canonical deterministic JSON bytes |
| Telemetry | Only on-demand/test-run/user-export modes; `continuous_hidden_telemetry=false` |
| Schema | Draft 2020-12 versioned schema preserves the same bounds/invariants |

## Official platform evidence used to constrain semantics

Android documents ANR categories and notes that its default timeout ranges are for AOSP/Pixel and can vary by OEM. It also recommends distinguishing system issues from app issues. Therefore R13.14 does not infer ANR truth from one global timer threshold.

- https://developer.android.com/topic/performance/anrs/diagnose-and-fix-anrs

Apple documents crash reports, Jetsam event reports and device console logs as different diagnostic sources. R13.14 therefore preserves those identities rather than treating every abnormal termination/log as one crash type.

- https://developer.apple.com/documentation/xcode/diagnosing-issues-using-crash-reports-and-device-logs
- https://developer.apple.com/documentation/xcode/acquiring-crash-reports-and-diagnostic-logs

Apple MetricKit provides performance/diagnostic reports, but R13.14 does not add a live hidden MetricKit collector. Metric-derived evidence can only enter the frozen core through explicit bounded evidence ingestion.

- https://developer.apple.com/documentation/metrickit

## Exact-head gates

A technical candidate is accepted only when all of the following refer to the **same exact SHA**:

1. R0 Repository Guard — SUCCESS;
2. Python Core — SUCCESS, including the full Ubuntu/Windows matrix and focused R13.14 tests;
3. KodeStudio UI Smoke — SUCCESS.

If repository policy also runs Android/Apple/R12 workflows, their failures must be investigated when they indicate a regression caused by this branch, but their success cannot replace the three required standard gates.

Any byte change after these runs creates a new candidate and invalidates the previous exact-head qualification for merge.

## End synchronization and merge rule

The technical implementation candidate is accepted. End synchronization now marks R13.14 COMPLETE and keeps R13.15 PLANNED. Because these documentary bytes differ from the technical candidate, the final end-synchronized head must freshly pass R0 + full Python Core + UI Smoke before implementation PR #247 may merge with `expected_head_sha`.

After that merge:

1. create exactly one continuity-only normalization branch from the implementation merge;
2. change no plan/code/schema/test bytes during normalization;
3. record final exact-head gate and implementation-merge authority in continuity;
4. run fresh R0 + Python Core + UI Smoke on the normalization head;
5. merge normalization with `expected_head_sha`;
6. only then may R13.15 start from the resulting normalized main.

## Manual gate

Current state: **CONDITIONAL / NOT TRIGGERED**.

The frozen core acceptance is fully testable with repository-owned synthetic diagnostic material and exact digests. No physical-device-only diagnostic claim has been frozen. No Play/App Store/Firebase account, production credential, physical device or live telemetry source was required. If a later claim is changed to require device-only evidence unavailable to accepted CI, stop before R13.15 and document exact bounded user actions/evidence without requesting credentials or private keys in chat.

## Candidate record

Accepted technical candidate: **`ebb446daf6a6c38cff71b0834151ace74ff46099`**.

Exact-head required gates:

- R0 Repository Guard **#1707** / workflow run **`33094260088`** — SUCCESS on Ubuntu and Windows repository-bootstrap jobs;
- Python Core **#1681** / workflow run **`33094260123`** — SUCCESS, including Ubuntu and Windows full tests, package builds and KodeStudio job; focused `tests/test_mobile_r13_14_diagnostics.py` passed inside the full test suite;
- KodeStudio UI Smoke **#1648** / workflow run **`33094260179`** — SUCCESS.

Supplementary automatically triggered regressions observed successful on the same candidate include R13 Apple Xcode #146, Apple SwiftUI Scaffold #117, Apple Signing Archive #92 and Google Play Readiness #163, plus multiple R12 acceptance workflows. These supplementary runs do not replace the required standard gates.

The technical candidate is accepted for R13.14 semantics. It is **not** the implementation merge head because end-sync documentation now changes bytes; PR #247 must merge only after fresh required gates succeed on the final end-synchronized head.
