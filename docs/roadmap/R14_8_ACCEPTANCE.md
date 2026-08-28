# R14.8 — Cloud saves: immutable revisions, sync, conflicts, idempotency + recovery acceptance

**Status:** END-SYNCED — final exact-head re-gates required  
**Immutable technical source:** `8132c4029983f693a32e0d26903d05e347313bf6`  
**Normalized R14.7 base:** `24e40db2781db8e42591c6ffa8fbdb8f0bf84108`  
**Implementation PR:** #271  
**Manual intervention:** NONE

## Scope accepted

R14.8 adds provider-neutral server-authoritative cloud-save slots with immutable append-only revisions, explicit base-revision/CAS conflict detection, duplicate-safe idempotency, content/schema integrity checks, bounded quotas/retention, deterministic conflict resolution, explicit schema migration and append-only rollback/recovery. Client-supplied slot/revision IDs never confer authority. It does not claim a production cloud provider, commercial storage account, Internet-scale durability or silent last-write-wins semantics.

## Non-authoritative predecessors

Candidate `2b458dc7e16ffabd7c94eb7dfdb3d362c9d74927` is diagnostic only: its acceptance integrity check could pass through an authorization rejection on a different slot and therefore did not prove digest-mismatch rejection strongly enough. Candidate `220bc28fb3ba627c042da76013348e5fd1273613` hardened that proof but predates the final public package exports. Neither SHA nor their runs/artifacts are decision evidence for closure. The immutable technical source is only `8132c4029983f693a32e0d26903d05e347313bf6`.

## Exact-source technical gates

- R0 Repository Guard #1822 / run `33206330276`: SUCCESS.
- Python Core #1796 / run `33206330171`: SUCCESS.
- KodeStudio UI Smoke #1763 / run `33206330345`: SUCCESS.
- R14 Cloud Save Acceptance #6 / run `33206330291`: SUCCESS on Ubuntu and Windows.

## Test evidence

Python Core Ubuntu: **1564 passed, 13 skipped, 46 warnings**; Windows Core SUCCESS; package builds Ubuntu/Windows SUCCESS; internal KodeStudio smoke SUCCESS.

The focused R14.8/R14.7/R14.6/R14.5 regression set passed **70 tests on Ubuntu and 70 tests on Windows**. The dedicated acceptance reports all fourteen checks true on both operating systems:

1. immutable revision history;
2. idempotent replay is mutation-free;
3. idempotency-key rebind is rejected;
4. stale base creates an explicit conflict;
5. conflict replay is mutation-free;
6. conflict resolution is deterministic;
7. double resolution is rejected;
8. schema migration is explicit;
9. silent schema change is rejected;
10. rollback is append-only;
11. object authorization is enforced;
12. function authorization is enforced;
13. content-integrity mismatch is rejected;
14. save quotas are bounded.

## Deterministic evidence

Ubuntu and Windows produced identical semantic values:

- state digest: `984bf5fc88d5ca537cd3a4d938c0aa6d890e8f1794f5485467726331331ce345`;
- trace digest: `f071636d1c5c99614b91817d328bab43ec406daaf315621affecd45af42df5e8`;
- slot digest: `24c423bfc661d2f8d207364c9d7058cb45413b7e15347beb78b50ca10c7345d1`;
- current revision digest: `4603e4e2a7d7d708cf689eb6cd4502b9809993b7245fc3ac64bf05eee1f34d7e`;
- resolved conflict digest: `be2d6808b13bd40aa4a04d003d8d47df315a4461a67647746b87b26d1e6c0eca`;
- revision count: `5`;
- retained bytes: `145`.

Evidence budgets: `max_payload_bytes=1024`, `max_revisions_per_slot=12`, `max_retained_bytes_per_slot=8192`, `max_open_conflicts_per_slot=3`.

Artifacts:

- Ubuntu artifact `9699802370`, ZIP digest `sha256:bfd9d7cadb002a822f5c0f399f32dc7410b62318a1dee7a0c3d480bd1c8398d8`.
- Windows artifact `9699818533`, ZIP digest `sha256:748f1b5572d679e619d82aeda314a1fa1f4c688d7edfe6f84e41fe54424c5a0d`.

Both evidence documents are bound to `8132c4029983f693a32e0d26903d05e347313bf6`, validate against `schemas/r14/backend-cloud-save-evidence.schema.json`, and assert `provider_live_claim=false` and `secrets_exposed=false`.

## External reference posture

External references are informative compatibility/security evidence, never provider lock-in. RFC 9110 documents conditional state-changing requests as a way to prevent lost updates. Google Play Games Saved Games exposes explicit conflict results and manual/automatic conflict-resolution policies, demonstrating that multi-device save conflicts are first-class rather than a reason for silent overwrite. OWASP API1:2023 requires object-level authorization whenever client-controlled identifiers select records. Kodepoia keeps its own provider-neutral save/revision/conflict model.

## Rollback / recovery

Rollback never rewrites retained history: it creates a new authoritative revision derived from an earlier retained revision. A full R14.8 rollback returns to normalized R14.7 main `24e40db2781db8e42591c6ffa8fbdb8f0bf84108`; no production provider state is owned and no provider credentials are required.

## Final closure rule

Relative to `8132c4029983f693a32e0d26903d05e347313bf6`, END synchronization may change only `docs/roadmap/R14_PLAN.md`, this acceptance document, and continuity. The final END-head must pass fresh R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R14 Cloud Save Acceptance. PR #271 may then merge only with expected-head protection. Exactly one continuity-only post-merge normalization must subsequently pass fresh R0/Python/UI and merge before R14.8 becomes COMPLETE + NORMALIZED and R14.9 is authorized.
