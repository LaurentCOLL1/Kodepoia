# R14.10 — Authoritative entitlements and billing acceptance

**Subdivision:** R14.10 — Entitlements, purchase boundaries, and billing catalog contract  
**Technical status:** ACCEPTED — END synchronization pending  
**Immutable technical source:** `8a102a19512b076a8edb5c561e86b1d0101bc391`  
**Exact branch:** `r14/10-entitlements-billing-catalog`  
**Exact normalized base:** `1dc3f8206eb454ecb6638fd75a5b65609c4e4ebf`  
**Pull request:** #275  
**Manual intervention:** CONDITIONAL / NOT TRIGGERED  
**Provider-live claim:** false

## Accepted scope

R14.10 implements a provider-neutral, backend-authoritative entitlement and billing boundary. Clients cannot directly grant trusted entitlements from purchase receipts. Catalog definitions are immutable/versioned; provider notifications are verified before mutation; provider purchase state is re-queried through registered adapters; purchase/account and message/account rebinding fail closed; duplicate notifications are mutation-free; out-of-order notifications cannot regress newer state; reconciliation is deterministic and idempotent; expiry is server-clock authoritative; provider environments are isolated; object/function authorization is enforced; state is bounded; and evidence is redacted.

The accepted core exercises Google Play and Apple App Store contracts through deterministic fixture adapters only. No real store account, production credential, purchase token, real-money transaction or provider-side state is required or claimed. `provider_live_claim=false` is therefore an explicit acceptance invariant rather than an omission.

## Rejected candidate

`55fed19c2ccbb63c790aa427a9afd9366cfe9cef` is **REJECTED** and none of its evidence is reusable. Its first `R14 Entitlements Acceptance` run `33233002948` failed on Ubuntu in two R14.10 tests before evidence generation:

- `test_purchase_locator_is_absent_from_state_trace_and_evidence`;
- `test_deterministic_state_and_trace_digests`.

The failure exposed a shared canonicalization contract defect rather than an entitlement-policy failure: `canonical_json_bytes()` forced every payload through `dict(payload)`, while R14.10 legitimately hashes ordered JSON arrays for traces and provider-event evidence. Applying `dict()` to a list of event dictionaries raised `ValueError("backend canonical payload is not serializable")`.

## Canonicalization defect corrected before acceptance

The accepted implementation changes the shared backend canonicalizer from mapping-only coercion to direct canonical JSON serialization of JSON-compatible payloads. Existing mapping semantics remain byte-for-byte stable because `ensure_ascii=False`, `sort_keys=True`, compact separators and `allow_nan=False` are unchanged; arrays now preserve their deterministic order instead of being incorrectly coerced to dictionaries.

The correction was made in `src/kodepoia/backend/contracts.py` and became immutable technical source `8a102a19512b076a8edb5c561e86b1d0101bc391`. No authority boundary was weakened to make the tests pass.

## Technical gate on immutable source

Dedicated `R14 Entitlements Acceptance` run `33233097442` completed successfully on exact source `8a102a19512b076a8edb5c561e86b1d0101bc391`:

- Ubuntu job `99049221513` — SUCCESS;
- Windows job `99049221666` — SUCCESS.

Both jobs checked out the exact evidence source, used Python 3.12, installed the repository development dependencies, compiled the acceptance surface, ran the focused R14 entitlement/authority regression, ran the focused R13 store-compliance regression, generated deterministic entitlement evidence, validated it against `schemas/r14/backend-entitlement-evidence.schema.json`, asserted exact source provenance and redaction/manual/provider-live invariants, and uploaded the evidence artifact.

Focused R14 regression files:

- `tests/test_r14_4_auth_identity_sessions.py`;
- `tests/test_r14_5_postgresql_persistence.py`;
- `tests/test_r14_6_authoritative_server.py`;
- `tests/test_r14_10_entitlements_billing.py`.

Focused R13 store/compliance regression files:

- `tests/test_r13_7_google_play_readiness.py`;
- `tests/test_mobile_r13_15_store_compliance.py`.

## Frozen semantic/adversarial checks

All nineteen schema-required checks are `true` on both operating systems:

1. client receipt grant rejected;
2. invalid notification signature rejected;
3. invalid purchase token rejected;
4. pending purchase grants no access;
5. verified provider state grants access;
6. duplicate message is mutation-free;
7. message/account rebind rejected;
8. purchase/account rebind rejected;
9. out-of-order notification cannot regress state;
10. reconciliation converges;
11. reconciliation replay is idempotent;
12. server-clock expiry is enforced;
13. provider environment isolation;
14. Apple App Store Server Notifications V2 contract;
15. immutable catalog version;
16. object authorization;
17. function authorization;
18. bounded capacity;
19. redacted evidence.

## Cross-platform semantic evidence

Ubuntu and Windows produced byte-for-byte equivalent JSON evidence and therefore the same semantic values:

- catalog digest: `029829e18972971f3551f3a0a99e3e641e55ab7a2fb6cb374f6b4645b482389c`;
- state digest: `3a526baa050763c8b5453c7970f750ce205ef57d864a612986b43488ab9f0154`;
- trace digest: `1333f7f917742d6a0f93028466e0f1c8e771b9442dfe5403c22184764e1edbeb`;
- provider-event digest: `57962e7fddd666146ebb90aa4fed26eb20a287346995bb37f552179780ea447d`;
- Google entitlement digest: `b0348458e900e79b8eed4237040a6cd33ca329f52920e613a6d8007ea0ae9a88`;
- Apple entitlement digest: `69bae02f05593d6c73bc0928cb01b8de72cb6afdacbea47d6592a57f6e20d851`;
- provider events: `5`;
- purchase records: `3`;
- catalog definitions: `2`.

Acceptance budgets are `max_catalog_versions=32`, `max_provider_events=128`, `max_purchases=32`, `max_accounts=32`, `max_reconciliations=64`.

Evidence state is `manual_state=conditional_not_triggered`, `provider_live_claim=false`, `secrets_exposed=false`.

## Evidence artifacts

Canonical `R14 Entitlements Acceptance` run `33233097442` artifacts:

- Ubuntu artifact `9709088552`, ZIP digest `sha256:9f768b4423cd6b735dc5be51ce258596f78d7bd722106f889fbad30b69f188f3`, recorded archive size 1276 bytes;
- Windows artifact `9709093199`, ZIP digest `sha256:6c8475949e29a7720aea89a583d6f45bdfd3335c04598893fe7d7afe0070c57c`, recorded archive size 1284 bytes.

Evidence schema: `schemas/r14/backend-entitlement-evidence.schema.json`, JSON Schema Draft 2020-12. It requires exact 40-character source SHA provenance, all nineteen acceptance checks to be true, SHA-256-shaped semantic digests, governed positive capacities, `manual_state="conditional_not_triggered"`, `provider_live_claim=false` and `secrets_exposed=false`.

## External compatibility evidence

The provider-specific semantics remain compatibility evidence, not core dependencies or live-provider proof:

- Google Play Billing documentation states that purchase lifecycle and entitlement synchronization belong in a secure backend. Real-time developer notifications indicate that purchase state changed; the backend must query the Google Play Developer API for complete purchase status. Google also recommends deduplicating RTDN `messageId` values to avoid redundant processing.
- Apple App Store Server Notifications V2 carries a cryptographically signed `signedPayload` in JWS format. `notificationUUID` is the provider-assigned unique notification identifier used to recognize duplicate notifications, and `signedDate` provides the signed snapshot ordering used when multiple notifications describe the same transaction.

Official references:

- https://developer.android.com/google/play/billing/backend
- https://developer.android.com/google/play/billing/rtdn-reference
- https://developer.android.com/google/play/billing/security
- https://developer.apple.com/documentation/appstoreservernotifications/receiving-app-store-server-notifications
- https://developer.apple.com/documentation/appstoreservernotifications/notificationuuid
- https://developer.apple.com/documentation/appstoreservernotifications/signeddate

## Rollback / recovery

Catalog definitions are immutable and versioned rather than silently mutated. Provider notifications and verified purchase snapshots retain deterministic identities, replay behavior and canonical digests. Reconciliation can recompute the authoritative account entitlement view from provider-backed state within configured bounds. Revocation/expiry converge to access denial; evidence never requires production provider mutation. The accepted correction to the shared canonicalizer remains covered by R14.4–R14.6 regression in the dedicated gate.

## END synchronization rule

No technical implementation byte may change after immutable source `8a102a19512b076a8edb5c561e86b1d0101bc391`. The R14.10 END-head may differ from that source only by:

- `docs/roadmap/R14_PLAN.md`;
- `docs/roadmap/R14_10_ACCEPTANCE.md`;
- `docs/continuity/KODEPOIA_CONTINUITY.md`.

That exact END-head must pass fresh R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R14 Entitlements Acceptance before PR #275 may merge with `expected_head_sha`. After merge, exactly one continuity-only normalization with fresh R0/Python/UI is required before R14.11 is authorized.
