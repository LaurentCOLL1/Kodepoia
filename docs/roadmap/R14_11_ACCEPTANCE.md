# R14.11 — Remote config, feature flags, targeting and safe rollout acceptance

**Subdivision:** R14.11 — Remote config, feature flags, targeting + safe rollout/rollback  
**Technical status:** ACCEPTED — END-head candidate ready for fresh gates  
**Immutable technical source:** `a58a0cf48a5e2311b5f6e671655f107e92c4645e`  
**Exact branch:** `r14/11-remote-config-feature-flags`  
**Exact normalized base:** `a9db57de1c1cc550604edbe6fec095e0a8e13c40`  
**Pull request:** #277  
**Manual intervention:** NONE  
**Provider-live claim:** false

## Accepted scope

R14.11 implements a provider-neutral, backend-owned remote configuration and feature-flag boundary with immutable/versioned snapshots, typed values, canonical bounded evaluation contexts, deterministic targeting, stable fractional rollout, prerequisite evaluation, prerequisite-cycle rejection, server-clock expiry, kill-switch override, activation preview, explicit production approval, SafeChange evidence binding, audit records, environment isolation and rollback to prior immutable snapshots.

Remote configuration contains data and declarative rules only. It cannot carry or execute arbitrary remote code or scripts. Unknown/unsupported value types, malformed contexts, missing required targeting keys for fractional evaluation, prerequisite cycles, authorization failures and capacity violations fail closed. Production activation is never silently promoted.

The provider-neutral core does not depend on a third-party flag provider and does not claim provider-live conformance. `provider_live_claim=false` is explicit acceptance state.

## Rejected candidate

`b43acf2a0f870587a85141cbdb91a3cf352bf2c7` is **REJECTED** and none of its evidence is reusable. Dedicated `R14 Remote Config Acceptance` run `33234680565` failed before evidence generation because the R14.11 test/acceptance fixtures attempted to use `"*"` as an `authorized_object_id`.

Existing R14 authority semantics permit wildcard function permissions but require every object authorization identifier to be a stable identifier. The correction did not weaken `AuthorityActorContext`; R14.11 fixtures were changed to enumerate explicit snapshot, flag and environment object IDs. A fresh exact-head run was required after the correction.

Intermediate technically green source `2a97caac8e2ac19615f7ce2c64585ae8080bd2fe` proved the corrected remote-config behavior on Ubuntu and Windows, but it was not frozen because the public `kodepoia.backend` export surface had not yet been completed. After exporting the R14.11 API and adding a dedicated public-export regression, the final immutable technical source became `a58a0cf48a5e2311b5f6e671655f107e92c4645e`.

## Canonical technical gate

Dedicated `R14 Remote Config Acceptance` run `33234881304` completed successfully on exact source `a58a0cf48a5e2311b5f6e671655f107e92c4645e`:

- Ubuntu job `99053992967` — SUCCESS;
- Windows job `99053993105` — SUCCESS.

Both jobs checked out the exact evidence source, used Python 3.12, installed development dependencies, compiled the R14.11 surface, ran focused R14.5 PostgreSQL + R14.6 authoritative-server + R14.11 remote-config/public-export regression, generated deterministic evidence, validated it with JSON Schema Draft 2020-12, asserted exact source provenance and privacy/manual/code-execution invariants, and uploaded evidence artifacts.

Focused files:

- `tests/test_r14_5_postgresql_persistence.py`;
- `tests/test_r14_6_authoritative_server.py`;
- `tests/test_r14_11_remote_config.py`;
- `tests/test_r14_11_backend_exports.py`.

## Frozen semantic/adversarial checks

All nineteen schema-required checks are `true` on both operating systems:

1. typed schema enforcement;
2. immutable snapshots;
3. targeting precedence over fractional rollout;
4. stable fractional assignment;
5. bounded 2,000-subject rollout distribution;
6. missing targeting key fails closed;
7. prerequisite cycles rejected;
8. prerequisites enforced deterministically;
9. server-clock expiry;
10. kill-switch override;
11. activation preview/dry-run;
12. production approval + SafeChange evidence;
13. rollback to prior immutable snapshot;
14. environment isolation;
15. object/function authorization;
16. OpenFeature-style typed fallback behavior;
17. redacted evidence/context identity;
18. bounded capacity;
19. arbitrary remote-code value type rejected.

## Cross-platform semantic evidence

Ubuntu and Windows evidence decode to exactly the same JSON object. Platform line endings/ZIP packaging differ, but all semantic fields and digests are identical:

- snapshot digest: `70397539d8e0fd41102387f32a29f947f29b629cbbfddbd9b20b660b40ca27c4`;
- state digest: `5343df1b58f0f595133261cdff705d720dc2e2c561e6d01cd69263060680a0c9`;
- trace digest: `4f45743cdc5af05bbdb795026d2e15a76c502c37d46c649a5ba08347efd00509`;
- audit digest: `4ec2eb54f751b49c6f43388fc7fcc76f16b7cc9e76eeffe703a638c941b46aa7`;
- rollout assignment digest: `24df98a3b2058d746bbbec24af41299acc9d84ea2b3d102cee4efbb56de69a98`;
- rollback preview digest: `d34ad885b9bb733120616e14c96c3e82418d1e3bdbc05099538c9c00022a176a`.

Deterministic evaluation digests:

- targeted: `0108b18f0cf2c1d5820204d79473c003fa43bbb86ac26655c7e1f3f27495a5ca`;
- stable fractional: `0884d32b42a8a9b9d597419a9b10978fe61d53c822227c47c22250e0a20cc387`;
- prerequisite: `c7df99df66d5131c8b3479ec83fd0b692c171067e921c763074e64ea9b28b5df`;
- expired: `70db1632311fd461604b273f6c51c85a917c5ba3ef1d2d3a8cbb36e93bf979b7`;
- kill switch: `90dfb468e71f6bed10d4621e9a3aa2de4c02c5f90d08b5167a28c62ffa30ae46`;
- test environment: `3660d8d68ee426cb5b0841da5a2532b203efbd78094fea8cce2900d2c07652af`;
- production environment: `136bef9b6a6f828e328806dc54020e1b7d595fa0daaa00f0985297184e567e11`.

Fractional fixture: population `2000`, `off=980`, `on=1020`. The assignment is based on stable hashing of the flag, rollout identity and targeting key; changing non-targeting attributes does not reshuffle the same targeting key.

Rollback fixture: `test-v2 → test-v1`, with final active snapshot `test-v1` while both immutable snapshots remain registered.

Governed acceptance budgets:

- `max_snapshots=32`;
- `max_flags_per_snapshot=32`;
- `max_evaluations=5000`;
- `max_audit_records=128`.

Evidence state is `manual_state=none`, `provider_live_claim=false`, `secrets_exposed=false`, `pii_exposed=false`, `arbitrary_code_execution=false`.

## Evidence artifacts

Canonical run `33234881304` artifacts:

- Ubuntu artifact `9709604569`, ZIP digest `sha256:25026a76c041d780cb75aeb0cc6cf06143c4a6a5430dc1c1c3a3c82725c6ef63`, recorded archive size 1372 bytes;
- Windows artifact `9709607701`, ZIP digest `sha256:1db48d5162f36132568ec8d223c036c7267831f471f068d4140e6ef9360eee24`, recorded archive size 1379 bytes.

The decoded evidence payloads are semantically identical. Evidence schema: `schemas/r14/backend-remote-config-evidence.schema.json`.

## External compatibility evidence

OpenFeature is used as a conceptual/provider-boundary reference, not as a claim of full SDK conformance:

- the stable Evaluation Context specification defines an optional string targeting key identifying the evaluation subject and notes that providers may require it for fractional evaluation;
- custom evaluation-context fields are typed data, while context privacy must be considered by integrators;
- the stable evaluation API expects typed flag methods to return the supplied default when an underlying resolved value has the wrong type;
- stable error vocabulary includes `TYPE_MISMATCH`, `TARGETING_KEY_MISSING` and `INVALID_CONTEXT`;
- fractional evaluation is defined as pseudorandom flag resolution using a context property such as targeting key and a configured proportion.

Official references:

- https://openfeature.dev/specification/sections/evaluation-context/
- https://openfeature.dev/docs/reference/concepts/evaluation-context/
- https://openfeature.dev/specification/sections/flag-evaluation/
- https://openfeature.dev/specification/types/
- https://openfeature.dev/specification/glossary/

R14.11 intentionally uses a stricter privacy boundary than the generic OpenFeature data model: explicit high-risk PII/context keys are rejected from this provider-neutral core acceptance path and raw targeting keys never appear in trace/state evidence.

## Rollback / recovery

Snapshots are immutable and versioned. Activation preview binds from/to snapshot digests before mutation. Production activation requires function/object authorization plus an explicit registered approval bound to the preview, target snapshot and SafeChange digest. Rollback reactivates a previously registered immutable snapshot instead of editing history. Kill switches are server-owned and override targeting/rollout immediately. All state-changing administrative operations produce bounded audit/trace records.

## END synchronization rule

No technical implementation byte may change after immutable source `a58a0cf48a5e2311b5f6e671655f107e92c4645e`. The R14.11 END-head may differ from that source only by:

- `docs/roadmap/R14_PLAN.md`;
- `docs/roadmap/R14_11_ACCEPTANCE.md`;
- `docs/continuity/KODEPOIA_CONTINUITY.md`.

That exact END-head must pass fresh R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R14 Remote Config Acceptance before merge with `expected_head_sha`. After merge, exactly one continuity-only normalization with fresh R0/Python/UI is required before R14.12 is authorized.

The assertion-guarded END synchronization completed without any implementation-byte change. PR #277 carries the final R14.11 END-head candidate; its exact diff from the immutable source must remain restricted to the three documentation files above.
