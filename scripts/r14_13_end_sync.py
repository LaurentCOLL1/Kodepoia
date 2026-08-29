from pathlib import Path

SOURCE = "b1729cabaffb19ac5491dee8a2c18e1bb5877746"
BASE = "2e51e8143949dbca48860ff1ff634ee1acf27cf6"
START = "3372b20709eeccefa1b65ea256918206436d8b48"

plan_path = Path("docs/roadmap/R14_PLAN.md")
plan = plan_path.read_text(encoding="utf-8")

old_checkpoint = "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED; R14 planning is ACCEPTED + NORMALIZED. R14.1–R14.12 are COMPLETE + NORMALIZED on normalized `main` `2e51e8143949dbca48860ff1ff634ee1acf27cf6`. R14.12 immutable technical source `9472f9198cdbaeed5c2b4618595480ac65bc4d5e`; final END-head `42db6d1fa84f5bd9b6a2c8e399603b9b9e621417`; implementation/evidence PR #279 merge `a088a081276213e7efa7bfb03b7b8adea2f0a75b`; unique continuity-only normalization head `8ceff867b09c8161e66d57dee936ce493dfc5a77` passed R0 #1888 / `33246000936`, Python Core #1863 / `33246001036`, UI #1828 / `33246000984`, and PR #280 merged with expected-head as normalized `main` `2e51e8143949dbca48860ff1ff634ee1acf27cf6`. R14.13 is IN_PROGRESS on `r14/13-events-telemetry-pipeline`; R14.14–R14.17 remain PLANNED. R14.13 manual state is NONE."
new_checkpoint = "**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED; R14 planning is ACCEPTED + NORMALIZED. R14.1–R14.12 are COMPLETE + NORMALIZED on normalized `main` `2e51e8143949dbca48860ff1ff634ee1acf27cf6`. R14.13 immutable technical source `b1729cabaffb19ac5491dee8a2c18e1bb5877746` passed exact-source R0 #1894 / `33247079759`, Python Core #1869 / `33247079754`, UI #1834 / `33247079785` and R14 Event Pipeline Acceptance #1 / `33247079799`; R14.13 is COMPLETE at technical/END-sync level on `r14/13-events-telemetry-pipeline`, with implementation/evidence merge and single continuity-only normalization still required before `COMPLETE + NORMALIZED`. R14.14–R14.17 remain PLANNED. R14.13 manual state is NONE; `provider_live_claim=false`."
assert plan.count(old_checkpoint) == 1, plan.count(old_checkpoint)
plan = plan.replace(old_checkpoint, new_checkpoint)

old_row = "| R14.13 | Events/telemetry pipeline: typed envelopes, dedupe, replay, retention + OTel bridge | IN_PROGRESS | NONE | R14.5–R14.6 + R6 |"
new_row = "| R14.13 | Events/telemetry pipeline: typed envelopes, dedupe, replay, retention + OTel bridge | COMPLETE | NONE | R14.5–R14.6 + R6 |"
assert plan.count(old_row) == 1, plan.count(old_row)
plan = plan.replace(old_row, new_row)

start = plan.index("# R14.13 — Events/telemetry pipeline: typed envelopes, dedupe, replay, retention + OTel bridge")
end = plan.index("# R14.14 — LiveOps campaigns, seasons, schedules, rotations, activation + rollback")
section = plan[start:end]
old_completion = "## Completion record\n\nTo be appended when accepted.\n\n---\n\n"
completion = """## Completion record

- Dedicated branch: `r14/13-events-telemetry-pipeline`; exact normalized branch point `2e51e8143949dbca48860ff1ff634ee1acf27cf6`; clean START-head `3372b20709eeccefa1b65ea256918206436d8b48` differed from normalized main by plan + continuity only and preceded all implementation bytes.
- Accepted immutable technical source: `b1729cabaffb19ac5491dee8a2c18e1bb5877746`.
- Technical exact-source gates: R0 Repository Guard #1894 / `33247079759` SUCCESS Ubuntu + Windows; Python Core #1869 / `33247079754` SUCCESS for Ubuntu/Windows Core, both package builds and UI-in-core; KodeStudio UI Smoke #1834 / `33247079785` SUCCESS; R14 Event Pipeline Acceptance #1 / `33247079799` SUCCESS Ubuntu + Windows.
- Full Ubuntu Python Core: **1692 passed / 13 skipped / 46 warnings**; R7/R8/R9 integrated acceptance validation also PASS. Focused R14.5/R14.6/R14.13/export regression: **51 passed Ubuntu + 51 passed Windows**.
- Twenty-five frozen evidence checks PASS identically cross-platform: immutable schema/event identity; secret/credential/unknown-field rejection; dedupe; event-ID rebinding rejection; source ordering; function/object authorization; environment isolation; at-least-once redelivery; ordered/idempotent checkpoint ACK; restart restore; dead-letter threshold; dry-run and executed replay checkpoint safety; replay-ID rebinding rejection; retention guard/prune; pruned identity non-reuse; OTel redaction; CloudEvents v1 interoperability shape; bounded capacity; redacted evidence.
- Cross-platform semantic evidence is identical. Digests: schema `648affd6dedf50063100b3b8cf7d26b95a5c56156d541e03a6867b35fe594259`; event `41475424fc7aff50871beeca5335e30e520e0855e7769daea7e42990eb4b77ec`; checkpoint `f08c139275b3256f368253f7f7937e3da8d77e356e9cd066b01e0dca5a48df21`; dead-letter `615b19f9fd8cda3aa7c4b0e5acef04ad1b659c7e3d77f4b2373100e180accf81`; replay preview `54846df765e20b893ee55d8ee0a5cf96c0e886406959e7af1ff4b145038cbf40`; replay execute `1ddf5f711184343bec76eca58ccdaeee5f900ca150fc1dabc55940f3c17eaee2`; OTel `28a93312419d3e390009254d4cfc7872d3ae61d243dd8b1a4939c699842d3bf7`; state `8efdb02adaa57c732d492b0d54eebe8b4a581877864bff3a352fa651c85439c7`; trace `9437f5415724c4f299bcea79da5201a46b59c17b250d2c4a40d4bf18410c4d9a`.
- Evidence counts: 3 acceptance events appended; 2 checkpoints; consumer lag 1 event; 1 dead-letter; 2 replay records; 1 retained event / 27 retained payload bytes after safe pruning; 1 registered schema. Budgets: `max_consumers=16`, `max_dead_letters=16`, `max_events=64`, `max_replay_events=8`, `max_replay_records=16`, `max_retained_payload_bytes=65536`, `max_schemas=16`, `max_trace_records=256`.
- Canonical artifacts: Ubuntu `9713178222` / `sha256:20ac5fdd68f5295d96a198c896e885c470c7cc5a778f9dabcce112f2169770ac`; Windows `9713185126` / `sha256:9c62de0d3ebe042c0d0555a4934d90486dc2b3738d819e638ca9fd64a02c293b`. ZIP metadata differs by platform while decoded evidence objects are identical.
- Evidence schema: `schemas/r14/backend-event-pipeline-evidence.schema.json`; evidence reports `manual_state=none`, `provider_live_claim=false`, `external_broker_required=false`, `otel_collector_required=false`, `secrets_exposed=false`, `pii_exposed=false`, `raw_payloads_exposed=false`.
- Privacy boundary is explicit: `cloudevent_mapping()` is an internal/provider-neutral event-envelope interoperability mapping and is not a privacy-sanitized telemetry export. `OpenTelemetryEventBridge` is the observability export boundary and redacts `SENSITIVE` payload fields plus hashes subject identity before export; `SECRET` and high-risk credential-like schema fields fail closed at registration/model construction.
- CloudEvents v1.0.2 and OpenTelemetry Specification 1.60.0 are informative interoperability baselines only. No external broker, Kafka cluster, OTel Collector, telemetry SaaS account or credential is required or claimed.
- Manual intervention: **NONE**.
- END state: R14.13 COMPLETE; R14.14–R14.17 remain PLANNED. R14.14 is not authorized until the exact R14.13 END-head passes fresh R0/Python/UI/R14 Event Pipeline gates, the implementation/evidence PR merges with expected-head protection, and exactly one continuity-only post-merge normalization passes fresh R0/Python/UI and merges.

---

"""
assert section.count(old_completion) == 1, section.count(old_completion)
section = section.replace(old_completion, completion)
plan = plan[:start] + section + plan[end:]
plan_path.write_text(plan, encoding="utf-8")

cont_path = Path("docs/continuity/KODEPOIA_CONTINUITY.md")
cont = cont_path.read_text(encoding="utf-8")
old_prompt = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.12 COMPLETE + NORMALIZED. R14.13 IN_PROGRESS. R14.14–R14.17 PLANNED.** Normalized `main` d’autorité `2e51e8143949dbca48860ff1ff634ee1acf27cf6`; branche active `r14/13-events-telemetry-pipeline`. R14.13 doit fournir des événements immuables/typés/versionnés, une consommation duplicate-safe avec checkpoints explicites, replay borné/permissionné/audité, dead-letter/retention sans perte silencieuse et redaction avant bridge OpenTelemetry. CloudEvents v1.0.2 et OpenTelemetry Specification 1.60.0 sont des références d’interopérabilité, pas des dépendances provider. Manual state : NONE."
new_prompt = "> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.12 COMPLETE + NORMALIZED. R14.13 COMPLETE at technical/END-sync level. R14.14–R14.17 PLANNED.** R14.13 immutable technical source `b1729cabaffb19ac5491dee8a2c18e1bb5877746` passed exact-source R0 #1894 / `33247079759`, Python Core #1869 / `33247079754`, UI #1834 / `33247079785` and R14 Event Pipeline #1 / `33247079799`, all SUCCESS. The final END-sync head must differ from that source only by `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_13_ACCEPTANCE.md` and this continuity file, then pass fresh exact-head gates before expected-head merge and one continuity-only normalization. Manual state: NONE; `provider_live_claim=false`."
assert cont.count(old_prompt) == 1, cont.count(old_prompt)
cont = cont.replace(old_prompt, new_prompt)

old_global = "- R14.13 : **IN_PROGRESS** sur `r14/13-events-telemetry-pipeline`, exact branch point `2e51e8143949dbca48860ff1ff634ee1acf27cf6`.\n- R14.14–R14.17 : **PLANNED**.\n- Manual state actuel : **CONDITIONAL / NOT TRIGGERED** (`provider_live_claim=false`)."
new_global = "- R14.13 : **COMPLETE at technical/END-sync level** — branche `r14/13-events-telemetry-pipeline`; exact branch point `2e51e8143949dbca48860ff1ff634ee1acf27cf6`; clean START `3372b20709eeccefa1b65ea256918206436d8b48`; immutable technical source `b1729cabaffb19ac5491dee8a2c18e1bb5877746`. Merge + single normalization remain required before `COMPLETE + NORMALIZED`.\n- R14.14–R14.17 : **PLANNED**.\n- Manual state actuel R14.13 : **NONE** (`provider_live_claim=false`; aucun provider externe requis)."
assert cont.count(old_global) == 1, cont.count(old_global)
cont = cont.replace(old_global, new_global)

old_status_row = "| R14.13 | IN_PROGRESS | NONE |"
new_status_row = "| R14.13 | COMPLETE | NONE |"
assert cont.count(old_status_row) == 1, cont.count(old_status_row)
cont = cont.replace(old_status_row, new_status_row)

marker = "\n## Next authorized action\n\n"
assert cont.count(marker) == 1, cont.count(marker)
technical = """
## R14.13 technical closure authority

- Dedicated branch: `r14/13-events-telemetry-pipeline`; exact normalized base `2e51e8143949dbca48860ff1ff634ee1acf27cf6`; clean START-head `3372b20709eeccefa1b65ea256918206436d8b48` was plan + continuity only and preceded implementation.
- Immutable technical source: `b1729cabaffb19ac5491dee8a2c18e1bb5877746`. START→source surface is exactly seven intended files: event pipeline implementation, backend public exports, focused tests, export regression, deterministic acceptance script, evidence schema and dedicated workflow; no helper survives.
- Technical gates on exact source: R0 Repository Guard #1894 / `33247079759` SUCCESS Ubuntu + Windows; Python Core #1869 / `33247079754` SUCCESS 5/5 jobs; KodeStudio UI Smoke #1834 / `33247079785` SUCCESS; R14 Event Pipeline Acceptance #1 / `33247079799` SUCCESS Ubuntu + Windows.
- Full Ubuntu Python Core: **1692 passed / 13 skipped / 46 warnings** with R7/R8/R9 integrated acceptance PASS. Focused R14.5/R14.6/R14.13/export regression: **51 passed Ubuntu + 51 passed Windows**.
- All 25 deterministic evidence checks PASS identically cross-platform. Digests: schema `648affd6dedf50063100b3b8cf7d26b95a5c56156d541e03a6867b35fe594259`; event `41475424fc7aff50871beeca5335e30e520e0855e7769daea7e42990eb4b77ec`; checkpoint `f08c139275b3256f368253f7f7937e3da8d77e356e9cd066b01e0dca5a48df21`; dead-letter `615b19f9fd8cda3aa7c4b0e5acef04ad1b659c7e3d77f4b2373100e180accf81`; replay preview `54846df765e20b893ee55d8ee0a5cf96c0e886406959e7af1ff4b145038cbf40`; replay execute `1ddf5f711184343bec76eca58ccdaeee5f900ca150fc1dabc55940f3c17eaee2`; OTel `28a93312419d3e390009254d4cfc7872d3ae61d243dd8b1a4939c699842d3bf7`; state `8efdb02adaa57c732d492b0d54eebe8b4a581877864bff3a352fa651c85439c7`; trace `9437f5415724c4f299bcea79da5201a46b59c17b250d2c4a40d4bf18410c4d9a`.
- Counts/budgets: 3 fixture events, 2 checkpoints, lag 1, 1 dead-letter, 2 replays, 1 event / 27 payload bytes retained after safe pruning, 1 schema; `max_consumers=16`, `max_dead_letters=16`, `max_events=64`, `max_replay_events=8`, `max_replay_records=16`, `max_retained_payload_bytes=65536`, `max_schemas=16`, `max_trace_records=256`.
- Artifacts: Ubuntu `9713178222` / `sha256:20ac5fdd68f5295d96a198c896e885c470c7cc5a778f9dabcce112f2169770ac`; Windows `9713185126` / `sha256:9c62de0d3ebe042c0d0555a4934d90486dc2b3738d819e638ca9fd64a02c293b`; decoded evidence objects are identical.
- Privacy boundary: CloudEvents mapping is event-envelope interoperability and may contain governed event payload; it is not the telemetry privacy boundary. `OpenTelemetryEventBridge` redacts sensitive fields and hashes subject identity before observability export; SECRET/high-risk credential-like schema fields are rejected fail-closed.
- Evidence flags: `manual_state=none`, `provider_live_claim=false`, `external_broker_required=false`, `otel_collector_required=false`, `secrets_exposed=false`, `pii_exposed=false`, `raw_payloads_exposed=false`.
- Manual intervention: NONE. No Kafka, external broker, OTel Collector, SaaS account or credential is required.
- R14.13 END-sync changes documentation/evidence bytes only; therefore fresh exact END-head R0 + full Python Core + KodeStudio UI Smoke + R14 Event Pipeline Acceptance are mandatory before merge. R14.14 remains unauthorized until expected-head merge and the single post-merge continuity normalization complete.
"""
cont = cont.replace(marker, technical + marker)

old_next = "Verify the final R14.13 START head differs from normalized `main` `2e51e8143949dbca48860ff1ff634ee1acf27cf6` only by `docs/roadmap/R14_PLAN.md` and this continuity file. Only after that clean compare may R14.13 implementation begin. Implement the frozen typed event/envelope/schema/store/consumer/checkpoint/replay/dead-letter/retention/privacy/OTel bridge scope with deterministic local evidence and no mandatory external broker/provider. Manual intervention remains NONE."
new_next = "Verify the final R14.13 END-head differs from immutable technical source `b1729cabaffb19ac5491dee8a2c18e1bb5877746` only by `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_13_ACCEPTANCE.md` and this continuity file. Run fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R14 Event Pipeline Acceptance; only if all succeed may the implementation/evidence PR merge with `expected_head_sha` equal to that END-head. Then perform exactly one continuity-only normalization with fresh R0/Python/UI before authorizing R14.14. Manual intervention remains NONE."
assert cont.count(old_next) == 1, cont.count(old_next)
cont = cont.replace(old_next, new_next)
cont_path.write_text(cont, encoding="utf-8")

acceptance = f"""# R14.13 — Events / telemetry pipeline acceptance

**Status:** ACCEPTED TECHNICAL SOURCE / END-SYNC PENDING FRESH GATES  
**Immutable technical source:** `{SOURCE}`  
**Normalized branch point:** `{BASE}`  
**Clean START-head:** `{START}`  
**Branch:** `r14/13-events-telemetry-pipeline`  
**Manual intervention:** NONE

## Accepted scope

R14.13 implements the frozen provider-neutral event/telemetry pipeline: typed versioned schemas and immutable envelopes, append-only local authority, duplicate-safe at-least-once consumption, durable checkpoints, bounded permissioned replay with dry-run/audit, explicit dead-letter state, safe retention, privacy classification/redaction, CloudEvents-compatible envelope mapping, and an OpenTelemetry observability bridge.

CloudEvents compatibility is an event-envelope interoperability surface only. It is not the privacy-sanitized telemetry export boundary. The OpenTelemetry bridge is the observability export boundary and redacts fields classified `SENSITIVE`, hashes subject identity, and preserves governed trace/span correlation. `SECRET` and credential-like high-risk payload schema fields fail closed before persistence/export.

## Exact-source gates

All technical gates ran against exact `{SOURCE}` and succeeded:

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

The final R14.13 END-head is valid only if its diff from immutable technical source `{SOURCE}` contains exactly:

- `docs/roadmap/R14_PLAN.md`;
- `docs/roadmap/R14_13_ACCEPTANCE.md`;
- `docs/continuity/KODEPOIA_CONTINUITY.md`.

Because END-sync changes documentation/evidence bytes, fresh exact-head R0 Repository Guard, full Python Core, KodeStudio UI Smoke and R14 Event Pipeline Acceptance are mandatory. The implementation/evidence PR may merge only with `expected_head_sha` equal to that exact END-head. R14.14 remains unauthorized until that merge is followed by exactly one continuity-only normalization which itself passes fresh exact-head R0 + Python Core + UI and merges.
"""
acceptance_path = Path("docs/roadmap/R14_13_ACCEPTANCE.md")
assert not acceptance_path.exists(), "R14_13_ACCEPTANCE.md already exists"
acceptance_path.write_text(acceptance, encoding="utf-8")
