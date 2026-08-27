# R13.14 — Mobile diagnostics design

**Subdivision:** R13.14  
**Title:** Mobile diagnostics: logs, crash/ANR/test/performance bundles + redaction  
**Status:** IN_PROGRESS  
**Authorized normalized base:** `69efa1f5cf92ae3c3ce4040fe5abe54faae2ed8b`  
**Dedicated branch:** `r13/14-mobile-diagnostics`  
**Manual state:** CONDITIONAL / NOT TRIGGERED

## Objective

R13.14 adds a deterministic, local-first diagnostic evidence model for accepted Android and Apple mobile artifacts. It must make support evidence useful without turning Kodepoia into a surveillance or background-telemetry product.

The core claim is deliberately narrower than remote crash analytics. R13.14 accepts already-collected or explicitly collected diagnostic material, verifies its identity, redacts it before persistence/export, binds it to immutable release/artifact/device/toolchain evidence, and produces bounded diagnostic bundles. It does not silently subscribe to, upload, scrape, or continuously collect user/device telemetry.

## Frozen deliverables

The subdivision implements:

- Android diagnostic source identities for logcat, crash, ANR, test and performance material;
- Apple diagnostic source identities for crash, Jetsam, device console, XCTest and performance material;
- provider identity separate from source kind;
- explicit collection modes only: `ON_DEMAND`, `TEST_RUN`, `EXPLICIT_USER_EXPORT`;
- common diagnostic entries with immutable SHA-256 bindings to release candidate, artifact, device snapshot, toolchain and optional test run;
- independent source-digest verification before text parsing;
- deterministic redaction before bundle serialization;
- bounded fingerprinting/deduplication for crash, ANR, memory termination, test failure and performance observations;
- bounded performance snapshots expressed as observations, not hard-coded provider/OEM pass/fail thresholds;
- bounded retention, bundle byte count, entry count and export permission;
- anti-substitution checks for release and artifact correlation;
- a durable JSON Schema at `schemas/mobile-diagnostics-v1.schema.json`.

## Source taxonomy

Android and Apple diagnostics are not collapsed into one ambiguous failure type.

### Android

- `ANDROID_LOGCAT` — bounded logcat text supplied by a governed collector or local evidence file.
- `ANDROID_CRASH` — crash evidence.
- `ANDROID_ANR` — ANR evidence kept distinct from crash evidence.
- `ANDROID_TEST` — instrumentation/test failure output.
- `ANDROID_PERFORMANCE` — bounded observations such as startup duration, FPS, memory, CPU or throughput when a trusted collector provides them.

Android's official ANR guidance notes that default timeout ranges documented for AOSP/Pixel can vary by OEM and recommends distinguishing system causes from app causes. R13.14 therefore does not encode one universal ANR timeout as architecture truth and does not convert a timing observation into ANR proof by threshold alone.

Official references:

- https://developer.android.com/topic/performance/anrs/diagnose-and-fix-anrs
- https://developer.android.com/studio/debug/logcat

### Apple

- `APPLE_CRASH` — crash report material.
- `APPLE_JETSAM` — memory-pressure termination evidence, intentionally separate from crash reports.
- `APPLE_CONSOLE` — device console material.
- `APPLE_XCTEST` — XCTest/result-derived diagnostic material.
- `APPLE_PERFORMANCE` — bounded performance observations, including data derived from explicitly supplied MetricKit or other accepted evidence where applicable.

Apple's Xcode diagnostic guidance explicitly distinguishes crash reports, Jetsam reports and device console logs. Distribution crash diagnosis also depends on retaining suitable archive/symbol information. R13.14 keeps those source identities separate and only binds supplied evidence; it does not claim automatic symbolication or remote App Store retrieval when that evidence is absent.

MetricKit can deliver device performance and diagnostic reports, but its existence is not treated as permission to add hidden continuous telemetry. Any future live MetricKit adapter remains an explicit, separately governed collection seam.

Official references:

- https://developer.apple.com/documentation/xcode/diagnosing-issues-using-crash-reports-and-device-logs
- https://developer.apple.com/documentation/xcode/acquiring-crash-reports-and-diagnostic-logs
- https://developer.apple.com/documentation/metrickit

## Identity and binding model

`DiagnosticBinding` contains only immutable digests:

- `release_candidate_sha256`;
- `artifact_sha256`;
- `device_snapshot_sha256`;
- `toolchain_sha256`;
- optional `test_run_sha256`.

Every `DiagnosticEntry` must carry the binding. `MobileDiagnosticBundle` also declares the authoritative release candidate and artifact digests. Bundle construction fails when an entry or performance snapshot carries another release/artifact identity. `verify_bundle_binding()` provides a second explicit replay/substitution check for consumers.

This prevents a crash from release A from being presented as evidence for release B merely because its text or fingerprint looks similar.

## Source integrity

Text ingestion is two-stage:

1. `verify_source_digest()` validates a caller-supplied expected SHA-256 against the exact source bytes and rejects oversized input.
2. Only after that check succeeds does `ingest_text_diagnostic()` decode strict UTF-8 and run redaction.

Malformed UTF-8, embedded NUL in text and over-budget sources fail closed. The raw source bytes are not a field in `DiagnosticEntry` and therefore are not serialized into the durable bundle.

## Redaction model

`redact_diagnostic_text()` is deterministic and bounded. It currently redacts:

- explicit bounded sensitive values supplied by the trusted caller;
- Authorization header credentials;
- common key/token/password/secret assignments;
- email addresses;
- IPv4 addresses;
- Unix user-home prefixes;
- Windows user-home prefixes.

The redaction result records category counts and a digest of the redacted text. The durable entry contains only redacted text plus the original source digest and byte count. The source digest proves which input was processed without preserving the sensitive source payload in the exported bundle.

The implementation intentionally does not claim that regex redaction can identify every category of personal data. Callers handling domain-specific identifiers must provide explicit sensitive values or add a separately reviewed redaction rule before persistence. Missing redaction capability must never be represented as guaranteed anonymity.

## Fingerprinting and deduplication

Fingerprints are deterministic hashes of bounded, whitespace-normalized, redacted signature components plus platform/source/fingerprint kind. Compatibility is explicit:

- crash fingerprint: Android crash or Apple crash only;
- ANR fingerprint: Android ANR only;
- memory termination: Apple Jetsam only;
- test failure: Android test or Apple XCTest;
- performance: Android or Apple performance source.

This prevents Apple Jetsam from being silently converted into a crash fingerprint and prevents Android ANR from becoming an Apple crash analogue.

`deduplicate_fingerprints()` deduplicates only identical kind/platform/source/signature identities. It does not merge different platform failure semantics.

## Performance model

`PerformanceMetric` permits only bounded finite non-negative numeric observations and explicit units. Percent values are bounded to 0..100. `PerformanceSnapshot` binds metrics to an existing diagnostic entry digest and the same release/artifact binding as the containing bundle.

R13.14 intentionally does not encode one global startup/FPS/CPU/ANR threshold as a platform-independent truth. Threshold policies, if later needed, belong to versioned platform/device evidence or R6 budget policy, not the diagnostic envelope.

## Retention and export

`DiagnosticRetentionPolicy` bounds:

- retention intent to 1..90 days;
- bundle bytes to a maximum of 16 MiB globally;
- entries to a maximum of 256 globally;
- whether export is allowed.

`MobileDiagnosticBundle` additionally checks the configured byte/entry budgets during construction. `export_bytes()` fails when export is disabled.

The model records bounded retention intent; it does not start a scheduler or background deletion service in R13.14. Any future persistence service must enforce the same policy through SafeChange/Recovery/Audit and remain explicit.

## No hidden telemetry invariant

The durable schema requires `continuous_hidden_telemetry=false` and the Python model emits it as a constant. The only collection modes are explicit/on-demand/test-run/user-export modes. There is no background collection mode, remote upload endpoint, credential field, account polling loop, analytics SDK integration or network adapter in the R13.14 core.

## Security and privacy boundaries

Existing frozen boundaries remain authoritative:

- Workspace/Vault path controls apply to any future diagnostic file adapter.
- KodeSecrets owns credentials; R13.14 durable data contains no credential value.
- R8 provenance/lineage continues to bind exported evidence.
- R6 privacy/security/budget controls remain mandatory.
- R11 media/runtime privacy evidence remains independent.
- R13.6/R13.11/R13.12 runtime/device evidence can be referenced by digest but is not rewritten by R13.14.
- Network stays off by default.

## Manual gate

Manual is **CONDITIONAL / NOT TRIGGERED**.

No frozen R13.14 core claim requires a physical phone/tablet, App Store Connect account, Google Play account, Firebase project, Crashlytics account, MetricKit live delivery, production signing key, or user credential. Core acceptance is deterministic ingestion/redaction/binding/budget behavior exercised from repository-owned test fixtures.

If a later exact acceptance claim is changed to require device-only evidence that hosted CI cannot establish, stop before R13.15, freeze the candidate SHA and request a bounded collector/evidence action. Secrets must never be requested in chat.

## Acceptance strategy

Focused tests must prove at least:

- common secret/personal patterns are removed from serialized diagnostic text;
- line-ending normalization/redaction is deterministic;
- source digest mismatch fails before ingestion;
- corrupt UTF-8, NUL and oversized sources fail closed;
- platform/source/provider substitution fails;
- Apple crash/Jetsam/console/XCTest identities remain distinct;
- release and artifact replay/substitution fails;
- fingerprint compatibility and deterministic deduplication;
- Jetsam is memory termination, not crash;
- metrics are finite/bounded and performance snapshots bind an entry in the same bundle;
- duplicate metric identities fail;
- only explicit collection modes exist and `continuous_hidden_telemetry` is always false;
- export can be disabled;
- retention and byte/entry counts are bounded;
- the JSON schema is versioned and requires the privacy invariants.

After focused implementation stabilizes, the exact candidate SHA must pass R0 Repository Guard, full Python Core and KodeStudio UI Smoke. No new real external tool seam is introduced by R13.14, so a dedicated device/account workflow is not a core acceptance prerequisite. Any existing platform workflows automatically triggered by repository policy remain supplementary regression evidence rather than a substitute for the three required exact-head gates.
