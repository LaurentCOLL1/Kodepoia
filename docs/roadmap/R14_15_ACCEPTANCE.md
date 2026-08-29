# R14.15 — Service operations / resilience acceptance

**Status:** ACCEPTED TECHNICAL SOURCE / END-SYNC PENDING FRESH GATES
**Immutable technical source:** `232bae747e91fd97f4cf3110a019639217d7914b`
**Normalized branch point:** `0078a75d473524688e6ab76ccf41b509e2146dea`
**Clean START-head:** `c3dd8aa5f3a7ec7d5f866ead207cf3a023fedbf0`
**Branch:** `r14/15-service-operations-resilience`
**Manual intervention:** CONDITIONAL / NOT TRIGGERED
**Provider-live claim:** false

## Accepted scope

The accepted technical source adds provider-neutral service-operations resilience without duplicating the existing R6 quality authority, R14 backend health contract, PostgreSQL transaction policy or R14 event-retention authority. It provides dependency-health aggregation and OTel-compatible observations; idempotency-gated bounded retry with deterministic exponential backoff/jitter; circuit breaker, token-bucket rate limiting, bulkhead and graceful drain; deterministic bounded failure injection; governed backup artifacts with provenance/hash/encryption metadata; isolated LOCAL/TEST restore verification with bounded RPO/RTO evidence; and explicit load profiles with latency/error/concurrency/CPU/memory budgets.

The acceptance does **not** claim Internet-scale capacity, multi-region resilience, production provider quota/cost behavior, production load certification or PostgreSQL PITR. Those require separate external/manual evidence when explicitly claimed.

## Technical exact-source gates

All decision gates below ran on exactly `232bae747e91fd97f4cf3110a019639217d7914b`:

- R0 Repository Guard #1959 / `33255887218`: **SUCCESS** on Ubuntu and Windows.
- Python Core #1934 / `33255887265`: **SUCCESS**, 5/5 jobs. Ubuntu full suite: **1731 passed / 13 skipped / 46 warnings**; R7/R8/R9 integrated acceptance PASS.
- KodeStudio UI Smoke #1899 / `33255887175`: **SUCCESS**.
- R14 Service Operations Resilience Acceptance #1 / `33255887252`: **SUCCESS** on Ubuntu 24.04 and Windows 2025.
- Dedicated R14.15 focused/export tests: **18 passed on Ubuntu + 18 passed on Windows**.

## Deterministic acceptance checks

The Ubuntu and Windows evidence objects are semantically identical and all **24/24** checks are true:

1. `backup_integrity_verified`
2. `bulkhead_blocks`
3. `circuit_opens`
4. `circuit_recovers`
5. `evidence_redacted`
6. `failure_timeline_bounded`
7. `graceful_drain`
8. `load_budget_failure_detected`
9. `load_budget_pass`
10. `no_external_load_claim`
11. `non_idempotent_retry_rejected`
12. `optional_dependency_degrades`
13. `otel_service_budget_ready`
14. `production_restore_forbidden`
15. `rate_limit_blocks`
16. `required_dependency_outage_unavailable`
17. `restore_isolated`
18. `restore_payload_matches`
19. `retry_delays_bounded`
20. `retry_jitter_deterministic`
21. `retry_transient_recovers`
22. `rpo_bounded`
23. `rto_bounded`
24. `untrusted_backup_rejected`

## Frozen evidence

Health evidence covers two dependencies. The optional-dependency degraded snapshot digest is `6013bc39f146bc5e564f62cfa9367c9cbde619214dd391879204e43f13df838d`; the required-dependency unavailable snapshot digest is `16e45082480ef5b9a65d09671be1c7075aab119400f71ca5a4f8c139627042e7`; the OTel-derived dependency digest is `b775b5ab61cac6c3f2df3eb6cb25840cf19980264257e6fde80e92fb4ca4a066`.

Retry evidence: 3 attempts; bounded delays `[6, 30]` ms; total timeout 400 ms; worst-case policy budget 375 ms; digest `7f44cdb44fbb2dc37d0e8b443e97ece9c81b951d286d4cd1c4b00f3187380e3b`.

Failure-injection evidence: 3 retained timeline records, 0 dropped; primary timeline digest `7d50d5506fff18d3e6d005debac723b961a54da9a9491a1a0c52095ecec640c4`; bounded fixture timeline digest `1b6992d3bfbfbfda0cca5ecd011ff07da8d2988c0eea7a38385659d24686b798`.

Restore evidence: backup digest `53141385e61fcd1054ab58bb3339777034f058573e9da6f03fbda1eb26445747`; payload SHA-256 `90d37617c95d63cf7296db0d735aa23d53d7791cb285e3a6afb68c747b7b212e`; restore digest `464b5105d0113d69ecf6ad47618e7e47e4930cd690e606a5f7e6701212a3a6cf`; provenance `kodepoia_fixture`; encrypted=true; isolated=true; measured fixture RPO 100 ms and RTO 40 ms.

Load-profile evidence: 200 requests; p95 latency 92.0 ms; error rate 0.005; peak concurrency 6; CPU 620 ms; memory 180 MB; profile digest `2bce6ca28c86da6c15c7fd82a50a46e74e60cedc7cabd43ce0cde8cf30e6e9e2`; result digest `73814856c829f3e8cccf3731f3da81cb63613be6ebed12f98742f95e3c949616`; `profile_scoped_only=true`.

Overall service-operations evidence digest: `81f49a0c335a0f6dacd94017dcd82a74bc2eb9825e26c98bb1ca7d1c58532718`.

## Cross-platform artifacts

- Ubuntu 24.04: artifact `9715782929`, `sha256:4f5c11edd50677bacdfcd73c88acc77f3e8c2574b9c2b32af9b4a16010c4bb5e`.
- Windows 2025: artifact `9715786195`, `sha256:02b4a0c471c832c06ec2ae7cd80c14fd22e6e169015eae1cf142608a4997bb68`.

The ZIP and raw JSON byte digests differ because platform/archive and line-ending metadata differ; the decoded JSON evidence objects are exactly equal.

## Evidence, privacy and provider state

Evidence schema: `schemas/r14/backend-resilience-evidence.schema.json` (JSON Schema Draft 2020-12 validation in the dedicated workflow).

Frozen flags: `manual_state=conditional_not_triggered`; `provider_live_claim=false`; `external_load_required=false`; `secrets_exposed=false`; `pii_exposed=false`; `raw_payloads_exposed=false`; `internet_scale_claim=false`; `multi_region_claim=false`; `postgresql_pitr_claim=false`.

No production provider account, quota, billing cost, destructive production load, production credential, secret, token, PII sample, raw provider payload, multi-region deployment or production PostgreSQL restore is required or claimed by this acceptance.

## Compatibility and DR baseline

Retry behavior is deliberately restricted to operations declared idempotent and uses finite backoff/jitter budgets to avoid retry amplification. PostgreSQL 18 backup/restore documentation is informative compatibility evidence only: continuous-archive PITR requires a physical/base backup plus WAL history, while the R14.15 CI restore exercise is an isolated governed fixture restore. Therefore `postgresql_backup_scope=fixture_restore_only` and `postgresql_pitr_claim=false` are intentional acceptance boundaries, not missing PASSes.

OpenTelemetry compatibility is limited to provider-neutral `service.name`-compatible service observations; no Collector, backend vendor or complete OTel conformance is claimed.

## END-sync rule

The immutable technical source remains `232bae747e91fd97f4cf3110a019639217d7914b`. The final R14.15 END-head is acceptable only if its cumulative diff from that source contains exactly:

- `docs/roadmap/R14_PLAN.md`
- `docs/roadmap/R14_15_ACCEPTANCE.md`
- `docs/continuity/KODEPOIA_CONTINUITY.md`

That END-head must then pass fresh exact-head R0 Repository Guard, full Python Core, KodeStudio UI Smoke and R14 Service Operations Resilience Acceptance (Ubuntu + Windows) on the same SHA. Merge is permitted only with `expected_head_sha`. R14.16 remains unauthorized until exactly one post-merge continuity-only normalization passes fresh R0/Python/UI and merges.
