# R14.13 — Events / telemetry pipeline acceptance

**Status:** ACCEPTED TECHNICAL SOURCE / END-SYNC PENDING FRESH GATES
**Immutable technical source:** `b1729cabaffb19ac5491dee8a2c18e1bb5877746`
**Normalized branch point:** `2e51e8143949dbca48860ff1ff634ee1acf27cf6`
**Clean START-head:** `3372b20709eeccefa1b65ea256918206436d8b48`
**Branch:** `r14/13-events-telemetry-pipeline`
**Manual intervention:** NONE

## Accepted scope

R14.13 implements the frozen provider-neutral event/telemetry pipeline: typed versioned schemas and immutable envelopes, append-only local authority, duplicate-safe at-least-once consumption, durable checkpoints, bounded permissioned replay with dry-run/audit, explicit dead-letter state, safe retention, privacy classification/redaction, CloudEvents-compatible envelope mapping, and an OpenTelemetry observability bridge.

CloudEvents compatibility is an event-envelope interoperability surface only. It is not the privacy-sanitized telemetry export boundary. The OpenTelemetry bridge is the observability export boundary and redacts fields classified `SENSITIVE`, hashes subject identity, and preserves governed trace/span correlation. `SECRET` and credential-like high-risk payload schema fields fail closed before persistence/export.

## Exact-source gates

All technical gates ran against exact `b1729cabaffb19ac5491dee8a2c18e1bb5877746` and succeeded:

- R0 Repository Guard #1894 / `33247079759` — Ubuntu + Windows SUCCESS.
- Python Core #1869 / `33247079754` — 5/5 jobs SUCCESS: Ubuntu Core, Windows Core, Ubuntu package build, Windows package build and UI-in-core.
- KodeStudio UI Smoke #1834 / `33247079785` — SUCCESS.
- R14 Event Pipeline Acceptance #1 / `33247079799` — Ubuntu + Windows SUCCESS.

Ubuntu full Python Core: **1692 passed / 13 skipped / 46 warnings**, with R7, R8 and R9 integrated acceptance validation PASS. The focused R14.5 PostgreSQL + R14.6 authoritative server + R14.13 event pipeline + public-export regression is **51 passed on Ubuntu and 51 passed on Windows**.

## Frozen deterministic checks

All 25 checks are `true` on both operating systems:

1. immutable schema identity;
2. secret field rejection;
3. credential/high-risk field rejection;
4. unknown payload field rejection;
5. immutable event identity;
6. duplicate deduplication;
7. event-ID rebinding rejection;
8. source out-of-order rejection;
9. function authorization;
10. object authorization;
11. environment isolation;
12. at-least-once redelivery;
13. ordered/idempotent checkpoint acknowledgement;
14. restart checkpoint restore;
15. dead-letter after bounded failure threshold;
16. replay dry-run is non-mutating;
17. executed replay preserves consumer checkpoint;
18. replay-ID rebinding rejection;
19. retention guard against uncheckpointed loss;
20. retention prune after safe checkpoint;
21. pruned event identity cannot be reused;
22. OpenTelemetry sensitive-data redaction;
23. CloudEvents v1 interoperability shape;
24. bounded capacity;
25. redacted evidence.

## Cross-platform semantic evidence

Decoded evidence objects are identical on Ubuntu and Windows.

- schema: `648affd6dedf50063100b3b8cf7d26b95a5c56156d541e03a6867b35fe594259`
- event: `41475424fc7aff50871beeca5335e30e520e0855e7769daea7e42990eb4b77ec`
- checkpoint: `f08c139275b3256f368253f7f7937e3da8d77e356e9cd066b01e0dca5a48df21`
- dead-letter: `615b19f9fd8cda3aa7c4b0e5acef04ad1b659c7e3d77f4b2373100e180accf81`
- replay preview: `54846df765e20b893ee55d8ee0a5cf96c0e886406959e7af1ff4b145038cbf40`
- replay execute: `1ddf5f711184343bec76eca58ccdaeee5f900ca150fc1dabc55940f3c17eaee2`
- OTel: `28a93312419d3e390009254d4cfc7872d3ae61d243dd8b1a4939c699842d3bf7`
- state: `8efdb02adaa57c732d492b0d54eebe8b4a581877864bff3a352fa651c85439c7`
- trace: `9437f5415724c4f299bcea79da5201a46b59c17b250d2c4a40d4bf18410c4d9a`

Counts: 3 acceptance events appended; 2 checkpoints; consumer lag 1; 1 dead-letter; 2 replay records; 1 retained event / 27 retained payload bytes after safe pruning; 1 schema.

Budgets: `max_consumers=16`, `max_dead_letters=16`, `max_events=64`, `max_replay_events=8`, `max_replay_records=16`, `max_retained_payload_bytes=65536`, `max_schemas=16`, `max_trace_records=256`.

Artifacts:

- Ubuntu: `9713178222`, ZIP `sha256:20ac5fdd68f5295d96a198c896e885c470c7cc5a778f9dabcce112f2169770ac`.
- Windows: `9713185126`, ZIP `sha256:9c62de0d3ebe042c0d0555a4934d90486dc2b3738d819e638ca9fd64a02c293b`.

The ZIP digests differ because artifact packaging metadata is platform-dependent; the decoded semantic JSON evidence is identical.

## Evidence / privacy state

Evidence schema: `schemas/r14/backend-event-pipeline-evidence.schema.json` (JSON Schema Draft 2020-12).

- `manual_state=none`
- `provider_live_claim=false`
- `external_broker_required=false`
- `otel_collector_required=false`
- `secrets_exposed=false`
- `pii_exposed=false`
- `raw_payloads_exposed=false`

No external broker, Kafka cluster, OpenTelemetry Collector, telemetry SaaS, public endpoint, account or credential is required for core acceptance.

## External interoperability baseline

These references are informative interoperability/security evidence, not provider dependencies or architecture authority:

- CloudEvents specification / stable 1.0.x baseline: https://github.com/cloudevents/spec
- OpenTelemetry Specification 1.60.0 baseline: https://opentelemetry.io/docs/specs/otel/
- OpenTelemetry sensitive-data guidance: https://opentelemetry.io/docs/security/handling-sensitive-data/

## END-sync rule

The final R14.13 END-head is valid only if its diff from immutable technical source `b1729cabaffb19ac5491dee8a2c18e1bb5877746` contains exactly:

- `docs/roadmap/R14_PLAN.md`;
- `docs/roadmap/R14_13_ACCEPTANCE.md`;
- `docs/continuity/KODEPOIA_CONTINUITY.md`.

Because END-sync changes documentation/evidence bytes, fresh exact-head R0 Repository Guard, full Python Core, KodeStudio UI Smoke and R14 Event Pipeline Acceptance are mandatory. The implementation/evidence PR may merge only with `expected_head_sha` equal to that exact END-head. R14.14 remains unauthorized until that merge is followed by exactly one continuity-only normalization which itself passes fresh exact-head R0 + Python Core + UI and merges.
