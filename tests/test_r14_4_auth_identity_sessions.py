from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.backend.auth import (
    AuthAttemptLimiter,
    AuthClientKind,
    AuthClientPolicy,
    AuthPolicyError,
    AuthRateLimitPolicy,
    AuthRealmIdentity,
    AuthStateError,
    AuthTokenKind,
    LocalAuthProvider,
    OIDCProviderMetadata,
    OIDCProviderPolicy,
    PasskeyPolicy,
    SessionState,
    TokenValidationPolicy,
    passkey_registration_record,
    validate_oidc_metadata,
)
from kodepoia.backend.contracts import BackendEnvironmentKind

ROOT = Path(__file__).resolve().parents[1]
SECRET = b"r14-4-local-fixture-secret-material-000001"
ISSUER = "https://local-auth.kodepoia.invalid"
AUDIENCE = "kodepoia.game"
REDIRECT = "http://127.0.0.1:8787/callback"
VERIFIER = "A" * 64


def _challenge(verifier: str = VERIFIER) -> str:
    return base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ascii")).digest()
    ).decode("ascii").rstrip("=")


def _realm() -> AuthRealmIdentity:
    return AuthRealmIdentity(
        realm_id="realm.local",
        issuer=ISSUER,
        environment=BackendEnvironmentKind.LOCAL,
    )


def _client() -> AuthClientPolicy:
    return AuthClientPolicy(
        client_id="client.local",
        client_kind=AuthClientKind.NATIVE_PUBLIC,
        redirect_uris=(REDIRECT,),
        allowed_audiences=(AUDIENCE,),
    )


def _provider() -> LocalAuthProvider:
    return LocalAuthProvider(_realm(), _client(), fixture_secret=SECRET)


def _authorized_provider(now: int = 1_000) -> tuple[LocalAuthProvider, str]:
    provider = _provider()
    tx = provider.begin_authorization(
        redirect_uri=REDIRECT,
        state="state-123",
        nonce="nonce-123",
        pkce_challenge=_challenge(),
        now=now,
    )
    provider.complete_authorization(
        tx.transaction_id,
        state="state-123",
        nonce="nonce-123",
        code_verifier=VERIFIER,
        issuer=ISSUER,
        now=now + 1,
    )
    account = provider.account_for_subject("subject@example.invalid")
    session = provider.create_session(account, now=now + 2)
    return provider, session.session_id


def test_local_realm_rejects_staging_and_production() -> None:
    for environment in (BackendEnvironmentKind.STAGING, BackendEnvironmentKind.PRODUCTION):
        with pytest.raises(AuthPolicyError):
            AuthRealmIdentity(
                realm_id="realm.prod",
                issuer="https://auth.example.test",
                environment=environment,
            )


def test_public_clients_require_pkce_s256() -> None:
    with pytest.raises(AuthPolicyError):
        AuthClientPolicy(
            client_id="client.bad",
            client_kind=AuthClientKind.NATIVE_PUBLIC,
            redirect_uris=(REDIRECT,),
            allowed_audiences=(AUDIENCE,),
            require_pkce=False,
        )
    with pytest.raises(AuthPolicyError):
        AuthClientPolicy(
            client_id="client.bad2",
            client_kind=AuthClientKind.BROWSER_PUBLIC,
            redirect_uris=(REDIRECT,),
            allowed_audiences=(AUDIENCE,),
            pkce_method="plain",
        )


def test_redirect_matching_is_exact_and_non_loopback_http_is_rejected() -> None:
    with pytest.raises(AuthPolicyError):
        AuthClientPolicy(
            client_id="client.bad",
            client_kind=AuthClientKind.NATIVE_PUBLIC,
            redirect_uris=("http://example.test/callback",),
            allowed_audiences=(AUDIENCE,),
        )
    provider = _provider()
    with pytest.raises(AuthPolicyError):
        provider.begin_authorization(
            redirect_uri=REDIRECT + "/extra",
            state="state",
            nonce="nonce",
            pkce_challenge=_challenge(),
            now=100,
        )


def test_authorization_state_nonce_issuer_and_pkce_are_transaction_bound() -> None:
    provider = _provider()
    tx = provider.begin_authorization(
        redirect_uri=REDIRECT,
        state="state-good",
        nonce="nonce-good",
        pkce_challenge=_challenge(),
        now=100,
    )
    for kwargs in (
        {"state": "state-bad", "nonce": "nonce-good", "code_verifier": VERIFIER, "issuer": ISSUER},
        {"state": "state-good", "nonce": "nonce-bad", "code_verifier": VERIFIER, "issuer": ISSUER},
        {"state": "state-good", "nonce": "nonce-good", "code_verifier": "B" * 64, "issuer": ISSUER},
        {"state": "state-good", "nonce": "nonce-good", "code_verifier": VERIFIER, "issuer": "https://evil.example"},
    ):
        with pytest.raises((AuthPolicyError, ValueError)):
            provider.complete_authorization(tx.transaction_id, now=101, **kwargs)
    result = provider.complete_authorization(
        tx.transaction_id,
        state="state-good",
        nonce="nonce-good",
        code_verifier=VERIFIER,
        issuer=ISSUER,
        now=102,
    )
    assert result.redirect_uri == REDIRECT
    assert result.issuer == ISSUER


def test_authorization_transaction_is_one_time_and_expires() -> None:
    provider = _provider()
    tx = provider.begin_authorization(
        redirect_uri=REDIRECT,
        state="state",
        nonce="nonce",
        pkce_challenge=_challenge(),
        now=100,
    )
    provider.complete_authorization(
        tx.transaction_id,
        state="state",
        nonce="nonce",
        code_verifier=VERIFIER,
        issuer=ISSUER,
        now=101,
    )
    with pytest.raises(AuthStateError):
        provider.complete_authorization(
            tx.transaction_id,
            state="state",
            nonce="nonce",
            code_verifier=VERIFIER,
            issuer=ISSUER,
            now=102,
        )
    expired = provider.begin_authorization(
        redirect_uri=REDIRECT,
        state="state2",
        nonce="nonce2",
        pkce_challenge=_challenge(),
        now=200,
    )
    with pytest.raises(AuthStateError):
        provider.complete_authorization(
            expired.transaction_id,
            state="state2",
            nonce="nonce2",
            code_verifier=VERIFIER,
            issuer=ISSUER,
            now=501,
        )


def test_local_identity_and_issue_sequence_are_reproducible() -> None:
    p1 = _provider()
    p2 = _provider()
    a1 = p1.account_for_subject("same-subject")
    a2 = p2.account_for_subject("same-subject")
    assert a1 == a2
    s1 = p1.create_session(a1, now=100)
    s2 = p2.create_session(a2, now=100)
    pair1 = p1.issue_pair(s1.session_id, audience=AUDIENCE, now=101)
    pair2 = p2.issue_pair(s2.session_id, audience=AUDIENCE, now=101)
    assert [token.value for token in pair1] == [token.value for token in pair2]
    assert [token.safe_canonical() for token in pair1] == [
        token.safe_canonical() for token in pair2
    ]


def test_token_validation_checks_issuer_audience_algorithm_expiry_and_future_time() -> None:
    provider, session_id = _authorized_provider()
    access, _ = provider.issue_pair(session_id, audience=AUDIENCE, now=1_010)
    good = TokenValidationPolicy(issuer=ISSUER, audience=AUDIENCE)
    provider.validate_token(access, policy=good, now=1_020)
    with pytest.raises(AuthPolicyError):
        provider.validate_token(
            access,
            policy=TokenValidationPolicy(issuer="https://other.example", audience=AUDIENCE),
            now=1_020,
        )
    with pytest.raises(AuthPolicyError):
        provider.validate_token(
            access,
            policy=TokenValidationPolicy(issuer=ISSUER, audience="other"),
            now=1_020,
        )
    with pytest.raises(AuthPolicyError):
        provider.validate_token(
            replace(access, algorithm="none"),
            policy=good,
            now=1_020,
        )
    with pytest.raises(AuthStateError):
        provider.validate_token(access, policy=good, now=access.expires_at + 31)
    with pytest.raises(AuthStateError):
        provider.validate_token(access, policy=good, now=access.issued_at - 31)


def test_refresh_rotation_revokes_old_token_and_detects_replay() -> None:
    provider, session_id = _authorized_provider()
    _, refresh = provider.issue_pair(session_id, audience=AUDIENCE, now=1_010)
    access2, refresh2 = provider.rotate_refresh(refresh, audience=AUDIENCE, now=1_020)
    assert access2.generation == 1
    assert refresh2.generation == 1
    with pytest.raises(AuthStateError):
        provider.rotate_refresh(refresh, audience=AUDIENCE, now=1_021)
    evidence = provider.evidence()
    assert evidence.rejected_replays == 1


def test_session_revocation_blocks_new_tokens() -> None:
    provider, session_id = _authorized_provider()
    provider.revoke_session(session_id)
    with pytest.raises(AuthStateError):
        provider.issue_pair(session_id, audience=AUDIENCE, now=1_010)
    assert provider.evidence().revoked_sessions == 1


def test_bearer_and_fixture_secret_are_absent_from_repr_and_evidence() -> None:
    provider, session_id = _authorized_provider()
    access, refresh = provider.issue_pair(session_id, audience=AUDIENCE, now=1_010)
    serialized = json.dumps(
        {
            "provider": repr(provider),
            "access_repr": repr(access),
            "refresh_repr": repr(refresh),
            "access_safe": access.safe_canonical(),
            "refresh_safe": refresh.safe_canonical(),
            "evidence": provider.evidence().canonical(),
        },
        sort_keys=True,
    )
    assert SECRET.decode("ascii") not in serialized
    assert access.value not in serialized
    assert refresh.value not in serialized
    assert "token_sha256" in serialized


def test_oidc_boundary_requires_exact_issuer_https_and_algorithm_allowlist() -> None:
    policy = OIDCProviderPolicy(
        provider_id="oidc.example",
        issuer="https://id.example.test",
        redirect_uris=(REDIRECT,),
        allowed_signing_algorithms=("RS256", "ES256"),
    )
    metadata = OIDCProviderMetadata(
        issuer="https://id.example.test",
        authorization_endpoint="https://id.example.test/authorize",
        token_endpoint="https://id.example.test/token",
        jwks_uri="https://id.example.test/jwks",
        signing_algorithms=("RS256",),
    )
    validate_oidc_metadata(policy, metadata)
    with pytest.raises(AuthPolicyError):
        validate_oidc_metadata(policy, replace(metadata, issuer="https://mixup.example"))
    with pytest.raises(AuthPolicyError):
        validate_oidc_metadata(policy, replace(metadata, signing_algorithms=("HS256",)))
    with pytest.raises((AuthPolicyError, ValueError)):
        OIDCProviderPolicy(
            provider_id="oidc.bad",
            issuer="http://id.example.test",
            redirect_uris=(REDIRECT,),
        )


def test_passkey_record_contains_public_material_only_and_binds_origin_rp() -> None:
    policy = PasskeyPolicy(
        rp_id="example.test",
        allowed_origins=("https://example.test",),
    )
    record = passkey_registration_record(
        policy=policy,
        credential_id="cred.1",
        account_id="acct.1",
        origin="https://example.test",
        rp_id="example.test",
        public_key_cose=b"public-cose-key-material-1234567890",
        transports=("internal",),
    )
    payload = record.canonical()
    assert payload["rp_id"] == "example.test"
    assert "public_key_cose_b64url" in payload
    assert not any("private" in key.lower() for key in payload)
    with pytest.raises(AuthPolicyError):
        passkey_registration_record(
            policy=policy,
            credential_id="cred.2",
            account_id="acct.1",
            origin="https://evil.example",
            rp_id="example.test",
            public_key_cose=b"public-cose-key-material-1234567890",
        )
    with pytest.raises(AuthPolicyError):
        passkey_registration_record(
            policy=policy,
            credential_id="cred.3",
            account_id="acct.1",
            origin="https://example.test",
            rp_id="evil.example",
            public_key_cose=b"public-cose-key-material-1234567890",
        )


def test_passkey_policy_requires_user_verification() -> None:
    with pytest.raises(AuthPolicyError):
        PasskeyPolicy(
            rp_id="example.test",
            allowed_origins=("https://example.test",),
            user_verification="preferred",
        )


def test_rate_limiter_locks_and_recovers_after_bound() -> None:
    limiter = AuthAttemptLimiter(
        AuthRateLimitPolicy(max_attempts=3, window_seconds=60, lockout_seconds=120)
    )
    limiter.record_failure("subject", now=100)
    limiter.record_failure("subject", now=101)
    limiter.record_failure("subject", now=102)
    with pytest.raises(AuthStateError):
        limiter.assert_allowed("subject", now=103)
    limiter.assert_allowed("subject", now=223)
    limiter.record_success("subject")
    limiter.assert_allowed("subject", now=224)


def test_evidence_is_canonical_and_contains_standards_without_raw_state() -> None:
    provider, session_id = _authorized_provider()
    provider.issue_pair(session_id, audience=AUDIENCE, now=1_010)
    evidence = provider.evidence()
    assert evidence.digest() == provider.evidence().digest()
    payload = evidence.canonical()
    assert payload["active_sessions"] == 1
    assert "RFC9700" in payload["standards"]
    assert not any("secret" in key.lower() or "token" in key.lower() for key in payload)


def test_auth_schemas_are_draft_2020_12_and_validate_canonical_documents() -> None:
    policy_schema = json.loads(
        (ROOT / "schemas/r14/backend-auth-policy.schema.json").read_text(encoding="utf-8")
    )
    evidence_schema = json.loads(
        (ROOT / "schemas/r14/backend-auth-evidence.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(policy_schema)
    Draft202012Validator.check_schema(evidence_schema)
    client_payload = _client().canonical()
    Draft202012Validator(policy_schema).validate(client_payload)
    Draft202012Validator(evidence_schema).validate(_provider().evidence().canonical())
    with pytest.raises(Exception):
        Draft202012Validator(policy_schema).validate({**client_payload, "client_secret": "nope"})


def test_token_kind_and_session_state_are_explicit() -> None:
    provider, session_id = _authorized_provider()
    access, refresh = provider.issue_pair(session_id, audience=AUDIENCE, now=1_010)
    assert access.token_kind is AuthTokenKind.ACCESS
    assert refresh.token_kind is AuthTokenKind.REFRESH
    provider.revoke_session(session_id)
    assert provider.evidence().active_sessions == 0
    assert provider.evidence().revoked_sessions == 1
    assert SessionState.REVOKED.value == "revoked"
