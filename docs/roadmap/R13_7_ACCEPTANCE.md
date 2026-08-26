# R13.7 — Google Play readiness acceptance

## Frozen acceptance claim

R13.7 is accepted only if Kodepoia can evaluate Google Play release readiness deterministically on the exact candidate head without a Play Console account, without live upload, and without production credentials. Passing this phase does **not** claim that Google reviewed, accepted or published an application.

## Required exact-head evidence

The final R13.7 candidate must pass:

1. R0 Repository Guard;
2. full Python Core suite;
3. KodeStudio UI Smoke;
4. R13 Android Build Acceptance;
5. R13 Android Signing Acceptance;
6. R13 Google Play Readiness Acceptance.

The R13.7 workflow runs the focused suite and canonical dry-run evidence generation on Ubuntu and Windows. Every uploaded report must contain the exact workflow head SHA, `dry_run=true`, `publish_attempted=false`, `policy_freshness=CURRENT`, and a valid schema payload.

Android Device Acceptance may run automatically on `r13/**` branches but is not a frozen R13.7 decision gate because this subdivision changes store/policy preparation rather than runtime-device semantics.

## Focused adversarial acceptance

`tests/test_r13_7_google_play_readiness.py` proves at minimum:

- internal-only testing can use the current Data safety exemption and remains a test-ready dry run;
- closed/open/production contexts cannot silently omit required Data safety evidence;
- non-internal readiness cannot silently omit IARC content-rating evidence;
- API 35 is evaluated before the 2026-08-31 deadline and API 36 is enforced from that date;
- a stale official-policy snapshot becomes `STALE` and blocks readiness;
- listing character limits are evaluated from the policy snapshot;
- release/metadata/AAB application-id mismatch blocks readiness;
- AAB/signing digest substitution raises an error;
- a first release cannot carry a staged rollout percentage;
- the internal-test 100-tester limit is enforced from the snapshot;
- sensitive/high-risk permission declarations marked as required but incomplete block readiness;
- unreviewed SDK/Data safety accounting blocks readiness where applicable;
- the 12-testers/14-days rule applies only to its scoped new-personal-account context, not organization accounts;
- open testing for the scoped new-personal-account case cannot manufacture production access;
- test-signed evidence cannot manufacture upload/Play App Signing readiness;
- metadata ordering produces the same canonical evidence digest;
- `KodeSecrets` API capability serialization contains only a reference and never the resolved secret;
- the evidence schema rejects unexpected fields such as a live publish token.

## Canonical hosted fixture

`scripts/r13_7_google_play_acceptance.py` creates a non-live closed-track fixture from public/digested identities only. It evaluates the API 36 rule on 2026-08-31, completed declaration fixtures, and `PLAY_APP_SIGNING_READY` state metadata; then it separately proves that the same policy snapshot becomes stale after the Kodepoia freshness horizon. No Google endpoint is called.

The hosted fixture's `STORE_READY` status means **the modeled local evidence has no blockers for its declared closed-track fixture**. It is not proof of Play Console acceptance or publication.

## Manual gate

Manual state begins and should remain **CONDITIONAL / NOT TRIGGERED** for core acceptance.

Manual intervention becomes REQUIRED only if the frozen claim is changed to require a live account-owned action, such as real Play API authentication, upload to an actual application, tester enrollment, production-access application, staged rollout, or publication. In that event, stop before R13.8 and request only bounded user-controlled evidence/actions; never request a password, private key, service-account JSON, token or secret in chat.

## Completion discipline

After a technical candidate passes all required exact-head gates, update only `R13_PLAN.md` and continuity for the R13.7 end-sync, rerun every frozen gate on the new exact head, merge with `expected_head_sha`, then create exactly one continuity-only normalization branch/PR. R13.8 may start only after that normalization is merged.
