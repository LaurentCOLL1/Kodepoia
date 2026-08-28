# R14.4 — Auth, identity, sessions, tokens, passkeys/OIDC boundary

## Status

Implementation design for the R14.4 local/provider-neutral core. External IdP proof is intentionally not required and the conditional manual gate is **NOT TRIGGERED**.

## Standards baseline

- OAuth 2.0 Security Best Current Practice — RFC 9700 (January 2025): exact redirect URI matching, PKCE for public clients, S256, issuer/mix-up defenses and no open redirects.
- OpenID Connect Core 1.0: issuer, audience and nonce remain explicit validation inputs; external discovery metadata is data to validate, never an instruction to trust arbitrary endpoints or algorithms.
- Web Authentication Level 3 — W3C Candidate Recommendation Snapshot, 26 May 2026: passkeys are represented by RP-scoped public-key credentials. Kodepoia persists only public credential material/metadata; authenticator private keys are out of scope and must never enter Kodepoia evidence.
- OWASP Session Management guidance: session identifiers are opaque/unpredictable, server-side session state is authoritative, credentials/tokens are excluded from client-readable durable evidence, and session rotation/revocation is explicit.

## Trust boundaries

R14.4 extends the existing `kodepoia.backend` contracts; it does not create a parallel networking or secrets stack. `BackendEnvironmentKind` prevents the deterministic fixture from serving staging/production. The local provider uses opaque HMAC-derived fixture values solely to make tests repeatable; it does **not** claim production OAuth/OIDC server interoperability.

External OIDC metadata is accepted only after a provider policy already fixes the issuer, redirect allowlist and strong signing-algorithm allowlist. R14.4 performs no uncontrolled discovery fetch. Later adapters must pass any network request through the R14.1 governed network boundary.

## Identity and session model

`AuthRealmIdentity` binds realm, issuer and environment. `AccountIdentity` is stable inside a realm. `AuthClientPolicy` explicitly distinguishes browser public, native public and server confidential clients. Public clients cannot disable PKCE and the only accepted method is `S256`.

Authorization transactions store hashes of `state` and `nonce`, the PKCE challenge, exact redirect URI and issuer. They expire and are single-use. Successful authorization does not itself manufacture a provider credential; it unlocks creation of a local session.

`SessionRecord` is server-side and has explicit ACTIVE/REVOKED state plus a refresh-family rotation counter. Access and refresh tokens are typed separately. Refresh use rotates the family generation and revokes the consumed refresh token; replay is a hard failure.

## Token validation

`TokenValidationPolicy` fixes issuer, audience, algorithm allowlist and bounded clock skew. Validation rejects issuer confusion, audience confusion, algorithm substitution/`none`, expiry and future issuance. R14.4 does not infer algorithm, issuer or audience from untrusted token text.

The bearer value is held in an `IssuedToken` field excluded from `repr` and all canonical evidence. Safe serialization contains only a SHA-256 fingerprint for correlation.

## OIDC boundary

`OIDCProviderPolicy` requires an explicit HTTPS issuer, explicit redirect allowlist and one or more algorithms from the R14.4 strong set (`RS256`, `ES256`, `EdDSA`). `OIDCProviderMetadata` requires HTTPS endpoints and declared signing algorithms. Validation requires exact issuer equality and refuses algorithms outside policy.

No real tenant, client secret or hosted identity provider is required for core acceptance.

## Passkey boundary

`PasskeyPolicy` binds RP ID, exact allowed origins and `user_verification=required`. `PasskeyCredentialRecord` contains credential ID, account ID, RP ID, COSE public-key bytes encoded base64url, signature counter and transports. There is deliberately no field for private key, seed, recovery secret or authenticator PIN.

The helper refuses origin or RP-ID mismatch before creating a record.

## Abuse controls

`AuthAttemptLimiter` provides deterministic bounded attempt windows and lockout duration for local evidence. It does not claim to replace provider/WAF/global distributed rate limiting in production.

## Redaction and evidence

`AuthSecurityEvidence` contains only realm/client digests, aggregate session/transaction/rejection counters and standards identifiers. Raw bearer values, fixture secrets, state, nonce, PKCE verifier, passwords and provider client secrets are excluded.

## Rollback

R14.4 state is in-memory/local-test only. Rollback removes the new auth module, schemas/tests/docs and exports. No provider-side resource exists to revoke because the conditional external-provider path is not activated.
