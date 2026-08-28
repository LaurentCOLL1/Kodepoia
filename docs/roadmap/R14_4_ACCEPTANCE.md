# R14.4 — Acceptance evidence ledger

## Current state

**Status: TECHNICAL_ACCEPTED_FINAL_REGATES_PENDING**

R14.4 starts exactly from normalized R14.3 `main` `f28e6762830ec9a2b22ddedc24bdc9a446e5f4b2` on `r14/04-auth-identity-sessions`. Mandatory START-sync completed before implementation and changed only `docs/roadmap/R14_PLAN.md` plus continuity.

## Frozen claims

R14.4 may claim only:

- typed account/auth realm/client/session/token identities and policies;
- deterministic local/test identity-provider fixture;
- exact redirect URI, PKCE S256, state, nonce and issuer transaction validation;
- explicit access/refresh token abstraction, validation, rotation, revocation and replay rejection;
- explicit OIDC provider metadata/policy boundary without uncontrolled discovery;
- passkey/WebAuthn public-credential storage contract with RP/origin binding;
- deterministic local rate/lockout evidence;
- redacted auth evidence that excludes bearer values and secrets.

R14.4 does not claim a production authorization server, production IdP tenant, social login integration, external discovery networking, production TLS, generalized federation, authenticator private-key custody or product-specific authorization rules.

## Standards provenance

- RFC 9700, OAuth 2.0 Security Best Current Practice, January 2025.
- OpenID Connect Core 1.0 issuer/audience/nonce semantics.
- W3C Web Authentication Level 3 Candidate Recommendation Snapshot, 26 May 2026.
- Current OWASP session-management guidance for opaque identifiers, lifecycle and credential handling.

## Required focused assertions

- local fixture refuses staging/production;
- public clients cannot disable PKCE and cannot select `plain`;
- redirects are exact-match and non-loopback HTTP redirects are rejected;
- authorization state/nonce/issuer/PKCE are transaction-bound;
- transactions expire and cannot replay;
- fixture identities and issue sequence are reproducible for fixed seed/time;
- token validation rejects issuer/audience/algorithm/expiry/future-time mismatch;
- refresh rotation revokes the old refresh and detects replay;
- revoked sessions cannot mint new tokens;
- bearer values and fixture secret never appear in repr/canonical evidence;
- OIDC metadata requires exact issuer, HTTPS endpoints and algorithm allowlist;
- passkey records contain public credential material only and enforce origin/RP binding;
- passkey user verification is required;
- local attempt limiter locks and recovers at bounded times;
- strict Draft 2020-12 policy/evidence schemas accept canonical documents and reject extra secret fields.

## Required technical candidate gates

After focused prevalidation, the accepted immutable implementation candidate must bind one unchanged SHA to fresh:

1. R0 Repository Guard — COMPLETED / SUCCESS.
2. full Python Core — COMPLETED / SUCCESS, including Ubuntu/Windows core, both package builds and internal KodeStudio smoke.
3. KodeStudio UI Smoke — COMPLETED / SUCCESS.

Then END-sync may change only `R14_PLAN.md`, this ledger and continuity before fresh exact-head re-gates, merge with expected-head protection and exactly one continuity-only post-merge normalization.

## Accepted technical source

- SHA: `3660f351649e85450324df25888d577afb02b19a`.
- R0 Repository Guard #1779 / `33187747722`: SUCCESS.
- Python Core #1753 / `33187747723`: SUCCESS.
- KodeStudio UI Smoke #1720 / `33187747872`: SUCCESS.
- Ubuntu full suite: 1494 passed, 13 skipped, 46 warnings. Windows Core, both package builds and Python internal UI smoke also SUCCESS.
- Focused cross-platform prevalidation `33187554520`: 29 tests passed on Ubuntu and Windows.
- The technical tree is immutable. This END-sync changes documentation/evidence only.

## Manual intervention

**CONDITIONAL / NOT TRIGGERED.** Core acceptance uses deterministic local providers. A real domain/TLS/IdP/passkey RP configuration would require provider-side work, but no such claim is needed for R14.4 core.
