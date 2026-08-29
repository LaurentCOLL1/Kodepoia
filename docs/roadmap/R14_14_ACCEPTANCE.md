# R14.14 — LiveOps campaigns / seasons / schedules / rotations acceptance

**Status:** ACCEPTED TECHNICAL SOURCE / END-SYNC PENDING FRESH GATES
**Immutable technical source:** `bd7d0130b5241047e5583bd31e0a183be1a1e6f1`
**Normalized branch point:** `b56162e0903bf2dc29505dfb6385030ed5d4b9d4`
**Clean START-head:** `c17356c7d24fb07544d3f58e65d7f4ef2a2f7624`
**Branch:** `r14/14-liveops-campaigns-schedules`
**Manual intervention:** NONE
**Provider-live claim:** false

## Accepted scope

The accepted technical source provides a provider-neutral LiveOps authority for immutable/versioned seasons and campaigns; exact immutable references to R14.10 catalog/entitlement, R14.11 config/flags, R14.12 content manifests and R14.13 event contracts; canonical UTC schedule windows with explicit display TZID/tzdb metadata; non-mutating preview; SafeChange-bound approval; idempotent activation and scheduler replay; deterministic rotations; Remote Config audience targeting; explicit pause/resume/expiry/rollback/kill; bounded audit/trace/state; environment separation; authorization and fail-closed capacity behavior.

No arbitrary scheduled scripts, production LiveOps provider, external network dependency, raw entitlement grant bypass or hidden pause-side scheduler transition is accepted.

## Technical exact-source gates

All decision gates below ran on exactly `bd7d0130b5241047e5583bd31e0a183be1a1e6f1`:

- R0 Repository Guard #1930 / `33251838461`: **SUCCESS**.
- Python Core #1905 / `33251838469`: **SUCCESS**, 5/5 jobs. Ubuntu full suite: **1713 passed / 13 skipped / 46 warnings**; R7/R8/R9 integrated acceptance PASS.
- KodeStudio UI Smoke #1870 / `33251838453`: **SUCCESS**.
- R14 LiveOps Acceptance #4 / `33251838460`: **SUCCESS** on Ubuntu 24.04 and Windows 2025.
- Dedicated R14.14 focused/export regression: **21 passed on Ubuntu + 21 passed on Windows**.

## Deterministic acceptance checks

The Ubuntu and Windows evidence objects are semantically identical and all **23/23** checks are true:

1. `activation_idempotent`
2. `approval_safechange_idempotent`
3. `audience_snapshot_mismatch_rejected`
4. `authorization_fail_closed`
5. `billing_environment_guard`
6. `capacity_fail_closed`
7. `exact_dependency_binding`
8. `expiry_idempotent`
9. `immutable_season_identity`
10. `kill_terminal_idempotent`
11. `missing_dependencies_fail_closed`
12. `pause_has_no_hidden_advance`
13. `pause_resume_explicit`
14. `preview_digest_clock_stable`
15. `preview_non_mutating`
16. `redacted_evidence`
17. `remote_config_audience_targeting`
18. `rollback_auditable`
19. `rotation_resolution`
20. `schedule_utc_timezone_metadata`
21. `scheduler_replay_idempotent`
22. `stale_preview_rejected`
23. `unsafe_schedule_rejected`

## Frozen evidence

Counts: 1 season, 1 campaign, 1 activation, 1 runtime record, 2 rotations, 7 audit records, 8 trace records, 23 checks.

Budgets: `max_seasons=1024`; `max_campaigns=4096`; `max_dependencies=16384`; `max_activations=16384`; `max_audit_records=100000`; `max_trace_records=200000`.

Digests:

- season: `b248ec4595a757731318705d498d7275aa25cb80416308025b7bf5d318d67e34`
- campaign: `f8a37a0dcd545f3fae4d13092c4e443d753dba96e6cdd6d6f0e6452ca6295183`
- preview: `0cc8fa8f6dac0cb882b94149516f98c6d502a041b8bc2e98c7c64b3d79710742`
- approval: `9e32edb5397b1b3e68cb8d765c5530ddee340667565f7fd4b8f94f73d17721bb`
- activation: `62aa304aadf785e204a5c3bbb6fa09cdce365e5f8b0ccc82bf02b3fa7b81e723`
- audience: `c892c99331c1e8904894506ee20724105efa40d2915d5ffdf8bd5eca95953ef5`
- state: `d24bfdaec041971f4270c46d8ffe60740432bf6805ea63d69857abe6d65f7aa5`
- dependencies: `3a959c3c83aaca047e0f1c81018e6d506cad10d07a88ff6b14590ddbde9e0336`
- audit: `bb18bd011fb7a0a6ac128f0426ce8643b416e10250445026e98e810c8653c7f9`
- trace: `1c0d7d7fd2cb50397c5783faf29ed518a7dea15a39b9463889f5db91129f43e5`
- SafeChange: `e6fbd826cda283c4d17cdcfce9b753ec503f5880295e701edc35078dfddf4de0`

Time authority: canonical `utc`; season display TZID `Europe/Paris`; campaign display TZID `America/Edmonton`; evidence tzdb version `2026c`.

## Cross-platform artifacts

- Ubuntu 24.04: artifact `9714598172`, `sha256:8ca1e46462e31f5a41dd97f517f5e98d06081b0d392d77bfe7977bec0b9f99a8`.
- Windows 2025: artifact `9714604219`, `sha256:fc9202c60fb080c95f0106f3c3d62580fff32311fc24d08ae04a3e26f82662f1`.

The ZIP digests differ because platform/archive metadata differs. The decoded JSON evidence is semantically identical.

## Evidence, privacy and provider state

Evidence schema: `schemas/r14/backend-liveops-evidence.schema.json` (JSON Schema Draft 2020-12 validation in the dedicated workflow).

Frozen flags: `manual_state=none`; `provider_live_claim=false`; `external_provider_required=false`; `secrets_exposed=false`; `pii_exposed=false`; `raw_payloads_exposed=false`.

No production billing account, LiveOps SaaS, CDN, external event broker, OpenTelemetry collector, provider credential, secret, token, PII sample or raw provider payload is required or claimed by this acceptance.

## Compatibility baseline

IANA Time Zone Database `2026c` and RFC 5545 TZID/recurrence semantics are informative time-compatibility evidence. Stable OpenFeature evaluation-context and targeting-key concepts are informative for the R14.11 Remote Config audience boundary. They are versioned interoperability references, not claims of full standards/provider conformance, and the canonical scheduler authority remains explicit UTC instants plus versioned timezone metadata.

## END-sync rule

The immutable technical source remains `bd7d0130b5241047e5583bd31e0a183be1a1e6f1`. The final R14.14 END-head is acceptable only if its cumulative diff from that source contains exactly:

- `docs/roadmap/R14_PLAN.md`
- `docs/roadmap/R14_14_ACCEPTANCE.md`
- `docs/continuity/KODEPOIA_CONTINUITY.md`

That END-head must then pass fresh exact-head R0 Repository Guard, full Python Core, KodeStudio UI Smoke and R14 LiveOps Acceptance (Ubuntu + Windows) on the same SHA. Merge is permitted only with `expected_head_sha`. R14.15 remains unauthorized until exactly one post-merge continuity-only normalization passes fresh R0/Python/UI and merges.
