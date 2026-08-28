from __future__ import annotations

import base64
import hashlib
import hmac
import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Iterable
from urllib.parse import urlsplit

from .contracts import BackendEnvironmentKind, canonical_sha256

_STABLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_B64URL_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_PKCE_VERIFIER_RE = re.compile(r"^[A-Za-z0-9._~-]{43,128}$")
_SAFE_OIDC_ALGS = frozenset({"RS256", "ES256", "EdDSA"})


def _stable_id(value: str, *, field_name: str) -> str:
    if not isinstance(value, str) or _STABLE_ID_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a stable identifier")
    return value


def _nonempty(value: str, *, field_name: str, maximum: int = 512) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value) > maximum
        or any(ord(ch) < 32 or ord(ch) == 127 for ch in value)
    ):
        raise ValueError(f"{field_name} must be bounded non-empty text")
    return value


def _b64url_no_pad(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _pkce_s256(verifier: str) -> str:
    if _PKCE_VERIFIER_RE.fullmatch(verifier) is None:
        raise ValueError("PKCE verifier must be 43..128 unreserved characters")
    return _b64url_no_pad(hashlib.sha256(verifier.encode("ascii")).digest())


def _https_url(value: str, *, field_name: str, allow_loopback_http: bool = False) -> str:
    _nonempty(value, field_name=field_name, maximum=2048)
    parts = urlsplit(value)
    if parts.username is not None or parts.password is not None:
        raise ValueError(f"{field_name} must not contain userinfo")
    if parts.query or parts.fragment:
        raise ValueError(f"{field_name} must not contain query or fragment")
    if not parts.hostname:
        raise ValueError(f"{field_name} must contain a host")
    scheme = parts.scheme.lower()
    host = parts.hostname.lower()
    if scheme == "https":
        return value
    if allow_loopback_http and scheme == "http" and host in {"127.0.0.1", "::1", "localhost"}:
        return value
    raise ValueError(f"{field_name} must use https")


def _exact_redirect(value: str, allowed: Iterable[str]) -> str:
    value = _nonempty(value, field_name="redirect_uri", maximum=2048)
    if value not in tuple(allowed):
        raise AuthPolicyError("redirect URI is not exactly registered")
    return value


class AuthPolicyError(ValueError):
    """Security-policy rejection at the R14.4 auth boundary."""


class AuthStateError(RuntimeError):
    """Invalid, expired, replayed or revoked auth state."""


class AuthClientKind(StrEnum):
    BROWSER_PUBLIC = "browser_public"
    NATIVE_PUBLIC = "native_public"
    SERVER_CONFIDENTIAL = "server_confidential"


class AuthTokenKind(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class SessionState(StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class AuthRealmIdentity:
    realm_id: str
    issuer: str
    environment: BackendEnvironmentKind = BackendEnvironmentKind.LOCAL

    def __post_init__(self) -> None:
        _stable_id(self.realm_id, field_name="realm_id")
        if self.environment not in {BackendEnvironmentKind.LOCAL, BackendEnvironmentKind.TEST}:
            raise AuthPolicyError("R14.4 local provider is restricted to local/test environments")
        _https_url(self.issuer, field_name="issuer", allow_loopback_http=True)

    def canonical(self) -> dict[str, Any]:
        return {
            "realm_id": self.realm_id,
            "issuer": self.issuer,
            "environment": self.environment.value,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class AccountIdentity:
    account_id: str
    realm_id: str
    subject: str

    def __post_init__(self) -> None:
        _stable_id(self.account_id, field_name="account_id")
        _stable_id(self.realm_id, field_name="realm_id")
        _nonempty(self.subject, field_name="subject", maximum=256)

    def canonical(self) -> dict[str, str]:
        return {
            "account_id": self.account_id,
            "realm_id": self.realm_id,
            "subject": self.subject,
        }


@dataclass(frozen=True, slots=True)
class AuthClientPolicy:
    client_id: str
    client_kind: AuthClientKind
    redirect_uris: tuple[str, ...]
    allowed_audiences: tuple[str, ...]
    require_pkce: bool = True
    pkce_method: str = "S256"

    def __post_init__(self) -> None:
        _stable_id(self.client_id, field_name="client_id")
        if not self.redirect_uris:
            raise AuthPolicyError("at least one redirect URI is required")
        redirects = tuple(
            dict.fromkeys(
                _nonempty(uri, field_name="redirect_uri", maximum=2048)
                for uri in self.redirect_uris
            )
        )
        for uri in redirects:
            parts = urlsplit(uri)
            if parts.fragment or parts.username is not None or parts.password is not None:
                raise AuthPolicyError("registered redirect URI must not contain fragment or userinfo")
            if parts.scheme not in {"https", "http"}:
                raise AuthPolicyError("registered redirect URI must use http/https")
            if parts.scheme == "http" and (parts.hostname or "").lower() not in {
                "127.0.0.1",
                "::1",
                "localhost",
            }:
                raise AuthPolicyError("http redirect URI is permitted only on loopback")
        audiences = tuple(
            sorted(
                {
                    _nonempty(item, field_name="audience", maximum=256)
                    for item in self.allowed_audiences
                }
            )
        )
        if not audiences:
            raise AuthPolicyError("at least one token audience is required")
        if self.pkce_method != "S256":
            raise AuthPolicyError("R14.4 permits only PKCE S256")
        if self.client_kind in {AuthClientKind.BROWSER_PUBLIC, AuthClientKind.NATIVE_PUBLIC} and not self.require_pkce:
            raise AuthPolicyError("public clients must use PKCE")
        object.__setattr__(self, "redirect_uris", redirects)
        object.__setattr__(self, "allowed_audiences", audiences)

    def canonical(self) -> dict[str, Any]:
        return {
            "client_id": self.client_id,
            "client_kind": self.client_kind.value,
            "redirect_uris": list(self.redirect_uris),
            "allowed_audiences": list(self.allowed_audiences),
            "require_pkce": self.require_pkce,
            "pkce_method": self.pkce_method,
        }


@dataclass(frozen=True, slots=True)
class TokenValidationPolicy:
    issuer: str
    audience: str
    allowed_algorithms: tuple[str, ...] = ("opaque-local-v1",)
    clock_skew_seconds: int = 30

    def __post_init__(self) -> None:
        _https_url(self.issuer, field_name="issuer", allow_loopback_http=True)
        _nonempty(self.audience, field_name="audience", maximum=256)
        algorithms = tuple(
            sorted(
                {
                    _nonempty(a, field_name="algorithm", maximum=32)
                    for a in self.allowed_algorithms
                }
            )
        )
        if not algorithms or "none" in {a.lower() for a in algorithms}:
            raise AuthPolicyError("token validation must use an explicit non-none algorithm allowlist")
        if (
            isinstance(self.clock_skew_seconds, bool)
            or not isinstance(self.clock_skew_seconds, int)
            or not 0 <= self.clock_skew_seconds <= 300
        ):
            raise ValueError("clock_skew_seconds must be an integer in [0, 300]")
        object.__setattr__(self, "allowed_algorithms", algorithms)


@dataclass(frozen=True, slots=True)
class IssuedToken:
    token_id: str
    token_kind: AuthTokenKind
    subject_id: str
    issuer: str
    audience: str
    issued_at: int
    expires_at: int
    family_id: str
    generation: int
    algorithm: str
    _raw_value: str = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        _stable_id(self.token_id, field_name="token_id")
        _stable_id(self.subject_id, field_name="subject_id")
        _stable_id(self.family_id, field_name="family_id")
        if self.expires_at <= self.issued_at:
            raise ValueError("token expiry must be after issuance")
        if self.generation < 0:
            raise ValueError("token generation cannot be negative")
        _nonempty(self._raw_value, field_name="raw token", maximum=1024)

    @property
    def value(self) -> str:
        """Return the bearer value only to the immediate caller; never log it."""
        return self._raw_value

    def safe_canonical(self) -> dict[str, Any]:
        return {
            "token_id": self.token_id,
            "token_kind": self.token_kind.value,
            "subject_id": self.subject_id,
            "issuer": self.issuer,
            "audience": self.audience,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "family_id": self.family_id,
            "generation": self.generation,
            "algorithm": self.algorithm,
            "token_sha256": _sha256_text(self._raw_value),
        }


@dataclass(slots=True)
class SessionRecord:
    session_id: str
    account_id: str
    client_id: str
    created_at: int
    expires_at: int
    state: SessionState = SessionState.ACTIVE
    rotation: int = 0
    refresh_family_id: str = ""

    def __post_init__(self) -> None:
        _stable_id(self.session_id, field_name="session_id")
        _stable_id(self.account_id, field_name="account_id")
        _stable_id(self.client_id, field_name="client_id")
        if self.expires_at <= self.created_at:
            raise ValueError("session expiry must follow creation")

    def safe_canonical(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "account_id": self.account_id,
            "client_id": self.client_id,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "state": self.state.value,
            "rotation": self.rotation,
        }


@dataclass(slots=True)
class AuthorizationTransaction:
    transaction_id: str
    client_id: str
    redirect_uri: str
    issuer: str
    state_sha256: str
    nonce_sha256: str
    pkce_challenge: str
    created_at: int
    expires_at: int
    consumed: bool = False

    def safe_canonical(self) -> dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "issuer": self.issuer,
            "state_sha256": self.state_sha256,
            "nonce_sha256": self.nonce_sha256,
            "pkce_challenge": self.pkce_challenge,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "consumed": self.consumed,
        }


@dataclass(frozen=True, slots=True)
class AuthorizationResult:
    transaction_id: str
    client_id: str
    redirect_uri: str
    issuer: str
    nonce_sha256: str


@dataclass(frozen=True, slots=True)
class OIDCProviderPolicy:
    provider_id: str
    issuer: str
    redirect_uris: tuple[str, ...]
    allowed_signing_algorithms: tuple[str, ...] = ("RS256", "ES256", "EdDSA")

    def __post_init__(self) -> None:
        _stable_id(self.provider_id, field_name="provider_id")
        _https_url(self.issuer, field_name="issuer")
        redirects = tuple(dict.fromkeys(self.redirect_uris))
        if not redirects:
            raise AuthPolicyError("OIDC provider requires explicit redirect URI allowlist")
        for uri in redirects:
            _https_url(uri, field_name="redirect_uri", allow_loopback_http=True)
        algorithms = tuple(sorted(set(self.allowed_signing_algorithms)))
        if not algorithms or not set(algorithms) <= _SAFE_OIDC_ALGS:
            raise AuthPolicyError("OIDC signing algorithms must be explicitly allowlisted strong algorithms")
        object.__setattr__(self, "redirect_uris", redirects)
        object.__setattr__(self, "allowed_signing_algorithms", algorithms)


@dataclass(frozen=True, slots=True)
class OIDCProviderMetadata:
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str
    signing_algorithms: tuple[str, ...]

    def __post_init__(self) -> None:
        _https_url(self.issuer, field_name="issuer")
        _https_url(self.authorization_endpoint, field_name="authorization_endpoint")
        _https_url(self.token_endpoint, field_name="token_endpoint")
        _https_url(self.jwks_uri, field_name="jwks_uri")
        algorithms = tuple(sorted(set(self.signing_algorithms)))
        if not algorithms:
            raise AuthPolicyError("OIDC metadata must declare signing algorithms")
        object.__setattr__(self, "signing_algorithms", algorithms)


@dataclass(frozen=True, slots=True)
class PasskeyPolicy:
    rp_id: str
    allowed_origins: tuple[str, ...]
    user_verification: str = "required"

    def __post_init__(self) -> None:
        _nonempty(self.rp_id, field_name="rp_id", maximum=253)
        if not self.allowed_origins:
            raise AuthPolicyError("passkey policy requires at least one origin")
        origins: list[str] = []
        for origin in self.allowed_origins:
            value = _https_url(origin, field_name="origin", allow_loopback_http=True)
            parts = urlsplit(value)
            if parts.path not in {"", "/"}:
                raise AuthPolicyError("passkey origin must not contain a path")
            origins.append(value.rstrip("/"))
        if self.user_verification != "required":
            raise AuthPolicyError("R14.4 requires passkey user verification")
        object.__setattr__(self, "allowed_origins", tuple(dict.fromkeys(origins)))


@dataclass(frozen=True, slots=True)
class PasskeyCredentialRecord:
    credential_id: str
    account_id: str
    rp_id: str
    public_key_cose_b64url: str
    sign_count: int = 0
    transports: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _stable_id(self.credential_id, field_name="credential_id")
        _stable_id(self.account_id, field_name="account_id")
        _nonempty(self.rp_id, field_name="rp_id", maximum=253)
        if _B64URL_RE.fullmatch(self.public_key_cose_b64url or "") is None:
            raise ValueError("public_key_cose_b64url must be base64url without padding")
        if isinstance(self.sign_count, bool) or not isinstance(self.sign_count, int) or self.sign_count < 0:
            raise ValueError("sign_count must be a non-negative integer")
        safe_transports = tuple(
            sorted({_stable_id(t, field_name="transport") for t in self.transports})
        )
        object.__setattr__(self, "transports", safe_transports)

    def canonical(self) -> dict[str, Any]:
        return {
            "credential_id": self.credential_id,
            "account_id": self.account_id,
            "rp_id": self.rp_id,
            "public_key_cose_b64url": self.public_key_cose_b64url,
            "sign_count": self.sign_count,
            "transports": list(self.transports),
        }


@dataclass(frozen=True, slots=True)
class AuthRateLimitPolicy:
    max_attempts: int = 5
    window_seconds: int = 60
    lockout_seconds: int = 300

    def __post_init__(self) -> None:
        for name, value, low, high in (
            ("max_attempts", self.max_attempts, 1, 100),
            ("window_seconds", self.window_seconds, 1, 3600),
            ("lockout_seconds", self.lockout_seconds, 1, 86400),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
                raise ValueError(f"{name} must be in [{low}, {high}]")


class AuthAttemptLimiter:
    def __init__(self, policy: AuthRateLimitPolicy | None = None) -> None:
        self.policy = policy or AuthRateLimitPolicy()
        self._attempts: dict[str, list[int]] = {}
        self._locked_until: dict[str, int] = {}

    def assert_allowed(self, subject_key: str, *, now: int) -> None:
        _nonempty(subject_key, field_name="subject_key", maximum=256)
        if self._locked_until.get(subject_key, 0) > now:
            raise AuthStateError("authentication temporarily locked")
        attempts = [
            t
            for t in self._attempts.get(subject_key, [])
            if t > now - self.policy.window_seconds
        ]
        self._attempts[subject_key] = attempts
        if len(attempts) >= self.policy.max_attempts:
            self._locked_until[subject_key] = now + self.policy.lockout_seconds
            raise AuthStateError("authentication temporarily locked")

    def record_failure(self, subject_key: str, *, now: int) -> None:
        self.assert_allowed(subject_key, now=now)
        attempts = self._attempts.setdefault(subject_key, [])
        attempts.append(now)
        if len(attempts) >= self.policy.max_attempts:
            self._locked_until[subject_key] = now + self.policy.lockout_seconds

    def record_success(self, subject_key: str) -> None:
        self._attempts.pop(subject_key, None)
        self._locked_until.pop(subject_key, None)


@dataclass(frozen=True, slots=True)
class AuthSecurityEvidence:
    realm_digest: str
    client_digest: str
    active_sessions: int
    revoked_sessions: int
    consumed_transactions: int
    rejected_replays: int
    rejected_policy: int
    standards: tuple[str, ...] = (
        "RFC9700",
        "OIDC-Core-1.0",
        "WebAuthn-Level-3-2026-05-26",
    )

    def canonical(self) -> dict[str, Any]:
        return {
            "realm_digest": self.realm_digest,
            "client_digest": self.client_digest,
            "active_sessions": self.active_sessions,
            "revoked_sessions": self.revoked_sessions,
            "consumed_transactions": self.consumed_transactions,
            "rejected_replays": self.rejected_replays,
            "rejected_policy": self.rejected_policy,
            "standards": list(self.standards),
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


class LocalAuthProvider:
    """Deterministic local/test auth fixture with bounded in-memory state."""

    algorithm = "opaque-local-v1"

    def __init__(
        self,
        realm: AuthRealmIdentity,
        client: AuthClientPolicy,
        *,
        fixture_secret: bytes,
        token_ttl_seconds: int = 900,
        refresh_ttl_seconds: int = 86_400,
        session_ttl_seconds: int = 86_400,
        transaction_ttl_seconds: int = 300,
    ) -> None:
        if realm.environment not in {BackendEnvironmentKind.LOCAL, BackendEnvironmentKind.TEST}:
            raise AuthPolicyError("local auth fixture cannot serve staging/production")
        if not isinstance(fixture_secret, bytes) or len(fixture_secret) < 32:
            raise ValueError("fixture_secret must contain at least 32 bytes")
        self.realm = realm
        self.client = client
        self._secret = bytes(fixture_secret)
        self._ttls = (
            token_ttl_seconds,
            refresh_ttl_seconds,
            session_ttl_seconds,
            transaction_ttl_seconds,
        )
        if any(
            isinstance(v, bool) or not isinstance(v, int) or not 1 <= v <= 7 * 86_400
            for v in self._ttls
        ):
            raise ValueError("auth TTLs must be positive and bounded")
        self._counter = 0
        self._accounts: dict[str, AccountIdentity] = {}
        self._sessions: dict[str, SessionRecord] = {}
        self._transactions: dict[str, AuthorizationTransaction] = {}
        self._refresh_used: set[str] = set()
        self._revoked_token_ids: set[str] = set()
        self._rejected_replays = 0
        self._rejected_policy = 0

    def __repr__(self) -> str:
        return (
            f"LocalAuthProvider(realm_id={self.realm.realm_id!r}, "
            f"client_id={self.client.client_id!r})"
        )

    def _derive(self, label: str, *parts: object) -> str:
        payload = "|".join([label, *(str(p) for p in parts)]).encode("utf-8")
        return _b64url_no_pad(hmac.new(self._secret, payload, hashlib.sha256).digest())

    def _next_id(self, prefix: str, *parts: object) -> str:
        self._counter += 1
        raw = self._derive(prefix, self._counter, *parts)
        return f"{prefix}.{raw[:32]}"

    def account_for_subject(self, subject: str) -> AccountIdentity:
        subject = _nonempty(subject, field_name="subject", maximum=256)
        key = _sha256_text(subject)
        existing = self._accounts.get(key)
        if existing is not None:
            return existing
        account_id = f"acct.{self._derive('account', self.realm.realm_id, subject)[:32]}"
        account = AccountIdentity(
            account_id=account_id,
            realm_id=self.realm.realm_id,
            subject=subject,
        )
        self._accounts[key] = account
        return account

    def begin_authorization(
        self,
        *,
        redirect_uri: str,
        state: str,
        nonce: str,
        pkce_challenge: str,
        now: int,
    ) -> AuthorizationTransaction:
        try:
            redirect = _exact_redirect(redirect_uri, self.client.redirect_uris)
            _nonempty(state, field_name="state", maximum=512)
            _nonempty(nonce, field_name="nonce", maximum=512)
            if len(pkce_challenge) != 43 or _B64URL_RE.fullmatch(pkce_challenge) is None:
                raise AuthPolicyError("PKCE S256 challenge must be 43 base64url characters")
        except ValueError:
            self._rejected_policy += 1
            raise
        transaction_id = self._next_id("txn", self.client.client_id, now)
        tx = AuthorizationTransaction(
            transaction_id=transaction_id,
            client_id=self.client.client_id,
            redirect_uri=redirect,
            issuer=self.realm.issuer,
            state_sha256=_sha256_text(state),
            nonce_sha256=_sha256_text(nonce),
            pkce_challenge=pkce_challenge,
            created_at=now,
            expires_at=now + self._ttls[3],
        )
        self._transactions[transaction_id] = tx
        return tx

    def complete_authorization(
        self,
        transaction_id: str,
        *,
        state: str,
        nonce: str,
        code_verifier: str,
        issuer: str,
        now: int,
    ) -> AuthorizationResult:
        tx = self._transactions.get(transaction_id)
        if tx is None:
            raise AuthStateError("unknown authorization transaction")
        if tx.consumed:
            self._rejected_replays += 1
            raise AuthStateError("authorization transaction replayed")
        if now > tx.expires_at:
            raise AuthStateError("authorization transaction expired")
        try:
            if not hmac.compare_digest(tx.state_sha256, _sha256_text(state)):
                raise AuthPolicyError("state mismatch")
            if not hmac.compare_digest(tx.nonce_sha256, _sha256_text(nonce)):
                raise AuthPolicyError("nonce mismatch")
            if issuer != tx.issuer:
                raise AuthPolicyError("issuer mismatch")
            if not hmac.compare_digest(tx.pkce_challenge, _pkce_s256(code_verifier)):
                raise AuthPolicyError("PKCE verifier mismatch")
        except ValueError:
            self._rejected_policy += 1
            raise
        tx.consumed = True
        return AuthorizationResult(
            transaction_id=tx.transaction_id,
            client_id=tx.client_id,
            redirect_uri=tx.redirect_uri,
            issuer=tx.issuer,
            nonce_sha256=tx.nonce_sha256,
        )

    def create_session(self, account: AccountIdentity, *, now: int) -> SessionRecord:
        if account.realm_id != self.realm.realm_id:
            raise AuthPolicyError("account belongs to a different realm")
        session_id = self._next_id("sess", account.account_id, now)
        family_id = self._next_id("family", session_id)
        session = SessionRecord(
            session_id=session_id,
            account_id=account.account_id,
            client_id=self.client.client_id,
            created_at=now,
            expires_at=now + self._ttls[2],
            refresh_family_id=family_id,
        )
        self._sessions[session_id] = session
        return session

    def _issue(
        self,
        session: SessionRecord,
        *,
        kind: AuthTokenKind,
        audience: str,
        now: int,
        generation: int,
    ) -> IssuedToken:
        if session.state is not SessionState.ACTIVE or now > session.expires_at:
            raise AuthStateError("session is not active")
        if audience not in self.client.allowed_audiences:
            self._rejected_policy += 1
            raise AuthPolicyError("audience is not allowed for this client")
        ttl = self._ttls[0] if kind is AuthTokenKind.ACCESS else self._ttls[1]
        token_id = self._next_id("tok", session.session_id, kind.value, generation)
        raw = self._derive(
            "token",
            token_id,
            kind.value,
            session.account_id,
            self.realm.issuer,
            audience,
            now,
            now + ttl,
            session.refresh_family_id,
            generation,
        )
        return IssuedToken(
            token_id=token_id,
            token_kind=kind,
            subject_id=session.account_id,
            issuer=self.realm.issuer,
            audience=audience,
            issued_at=now,
            expires_at=now + ttl,
            family_id=session.refresh_family_id,
            generation=generation,
            algorithm=self.algorithm,
            _raw_value=raw,
        )

    def issue_pair(
        self,
        session_id: str,
        *,
        audience: str,
        now: int,
    ) -> tuple[IssuedToken, IssuedToken]:
        session = self._sessions.get(session_id)
        if session is None:
            raise AuthStateError("unknown session")
        return (
            self._issue(
                session,
                kind=AuthTokenKind.ACCESS,
                audience=audience,
                now=now,
                generation=session.rotation,
            ),
            self._issue(
                session,
                kind=AuthTokenKind.REFRESH,
                audience=audience,
                now=now,
                generation=session.rotation,
            ),
        )

    def validate_token(
        self,
        token: IssuedToken,
        *,
        policy: TokenValidationPolicy,
        now: int,
    ) -> None:
        if token.token_id in self._revoked_token_ids:
            raise AuthStateError("token is revoked")
        if token.issuer != policy.issuer:
            raise AuthPolicyError("token issuer mismatch")
        if token.audience != policy.audience:
            raise AuthPolicyError("token audience mismatch")
        if token.algorithm not in policy.allowed_algorithms:
            raise AuthPolicyError("token algorithm is not allowed")
        if now > token.expires_at + policy.clock_skew_seconds:
            raise AuthStateError("token expired")
        if now + policy.clock_skew_seconds < token.issued_at:
            raise AuthStateError("token issued in the future")

    def rotate_refresh(
        self,
        refresh: IssuedToken,
        *,
        audience: str,
        now: int,
    ) -> tuple[IssuedToken, IssuedToken]:
        if refresh.token_kind is not AuthTokenKind.REFRESH:
            raise AuthPolicyError("refresh rotation requires a refresh token")
        if refresh.token_id in self._refresh_used or refresh.token_id in self._revoked_token_ids:
            self._rejected_replays += 1
            raise AuthStateError("refresh token replayed or revoked")
        session = next(
            (
                s
                for s in self._sessions.values()
                if s.refresh_family_id == refresh.family_id
                and s.account_id == refresh.subject_id
            ),
            None,
        )
        if session is None or session.state is not SessionState.ACTIVE:
            raise AuthStateError("refresh family is not attached to an active session")
        if now > refresh.expires_at:
            raise AuthStateError("refresh token expired")
        self._refresh_used.add(refresh.token_id)
        self._revoked_token_ids.add(refresh.token_id)
        session.rotation += 1
        return (
            self._issue(
                session,
                kind=AuthTokenKind.ACCESS,
                audience=audience,
                now=now,
                generation=session.rotation,
            ),
            self._issue(
                session,
                kind=AuthTokenKind.REFRESH,
                audience=audience,
                now=now,
                generation=session.rotation,
            ),
        )

    def revoke_session(self, session_id: str) -> None:
        session = self._sessions.get(session_id)
        if session is not None:
            session.state = SessionState.REVOKED

    def evidence(self) -> AuthSecurityEvidence:
        active = sum(1 for s in self._sessions.values() if s.state is SessionState.ACTIVE)
        revoked = sum(1 for s in self._sessions.values() if s.state is SessionState.REVOKED)
        consumed = sum(1 for tx in self._transactions.values() if tx.consumed)
        return AuthSecurityEvidence(
            realm_digest=self.realm.digest(),
            client_digest=canonical_sha256(self.client.canonical()),
            active_sessions=active,
            revoked_sessions=revoked,
            consumed_transactions=consumed,
            rejected_replays=self._rejected_replays,
            rejected_policy=self._rejected_policy,
        )


def validate_oidc_metadata(
    policy: OIDCProviderPolicy,
    metadata: OIDCProviderMetadata,
) -> None:
    if metadata.issuer != policy.issuer:
        raise AuthPolicyError("OIDC metadata issuer does not match configured issuer exactly")
    if not set(metadata.signing_algorithms) <= set(policy.allowed_signing_algorithms):
        raise AuthPolicyError("OIDC metadata advertises a signing algorithm outside the allowlist")


def passkey_registration_record(
    *,
    policy: PasskeyPolicy,
    credential_id: str,
    account_id: str,
    origin: str,
    rp_id: str,
    public_key_cose: bytes,
    sign_count: int = 0,
    transports: tuple[str, ...] = (),
) -> PasskeyCredentialRecord:
    normalized_origin = _https_url(
        origin,
        field_name="origin",
        allow_loopback_http=True,
    ).rstrip("/")
    if normalized_origin not in policy.allowed_origins:
        raise AuthPolicyError("passkey origin is not allowed")
    if rp_id != policy.rp_id:
        raise AuthPolicyError("passkey RP ID mismatch")
    if not isinstance(public_key_cose, bytes) or len(public_key_cose) < 16:
        raise ValueError("passkey public key material is missing or implausibly short")
    return PasskeyCredentialRecord(
        credential_id=credential_id,
        account_id=account_id,
        rp_id=rp_id,
        public_key_cose_b64url=_b64url_no_pad(public_key_cose),
        sign_count=sign_count,
        transports=transports,
    )


__all__ = [
    "AccountIdentity",
    "AuthAttemptLimiter",
    "AuthClientKind",
    "AuthClientPolicy",
    "AuthPolicyError",
    "AuthRateLimitPolicy",
    "AuthRealmIdentity",
    "AuthSecurityEvidence",
    "AuthStateError",
    "AuthTokenKind",
    "AuthorizationResult",
    "AuthorizationTransaction",
    "IssuedToken",
    "LocalAuthProvider",
    "OIDCProviderMetadata",
    "OIDCProviderPolicy",
    "PasskeyCredentialRecord",
    "PasskeyPolicy",
    "SessionRecord",
    "SessionState",
    "TokenValidationPolicy",
    "passkey_registration_record",
    "validate_oidc_metadata",
]
