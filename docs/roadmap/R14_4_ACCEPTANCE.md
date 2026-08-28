# R14.4 — Acceptance evidence ledger

## Current state

**Status: IMPLEMENTATION_CANDIDATE_PENDING**

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

## Manual intervention

**CONDITIONAL / NOT TRIGGERED.** Core acceptance uses deterministic local providers. A real domain/TLS/IdP/passkey RP configuration would require provider-side work, but no such claim is needed for R14.4 core.
