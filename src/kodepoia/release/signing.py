from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from urllib.parse import urlsplit

HASH_ALGORITHM = "SHA256"
CERT_THUMBPRINT_RE = re.compile(r"^[0-9A-F]{40}$")
SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class SigningPolicyError(ValueError):
    """Raised when a Windows release signing request violates R18.4 policy."""


class SigningMode(StrEnum):
    UNSIGNED = "unsigned"
    TEST = "test"
    PRODUCTION = "production"


@dataclass(frozen=True)
class SigningPolicy:
    mode: SigningMode
    source_sha: str
    timestamp_url: str | None = None
    certificate_thumbprint: str | None = None
    production_enabled: bool = False

    def validated(self) -> "SigningPolicy":
        source_sha = self.source_sha.strip().lower()
        if not SOURCE_SHA_RE.fullmatch(source_sha):
            raise SigningPolicyError("source_sha must be an exact 40-character hexadecimal Git commit")

        thumbprint = (
            self.certificate_thumbprint.replace(" ", "").upper()
            if self.certificate_thumbprint
            else None
        )
        timestamp_url = self.timestamp_url.strip() if self.timestamp_url else None

        if self.mode is SigningMode.UNSIGNED:
            if thumbprint or timestamp_url:
                raise SigningPolicyError("unsigned mode cannot accept a certificate or timestamp service")
            return SigningPolicy(self.mode, source_sha)

        if not thumbprint or not CERT_THUMBPRINT_RE.fullmatch(thumbprint):
            raise SigningPolicyError("signed modes require an exact 40-hex certificate thumbprint")
        if not timestamp_url:
            raise SigningPolicyError("signed modes require an RFC3161 timestamp URL")
        parsed = urlsplit(timestamp_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise SigningPolicyError("timestamp URL must use http or https and name a host")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise SigningPolicyError(
                "timestamp URL cannot contain credentials, query parameters or fragments"
            )
        if self.mode is SigningMode.PRODUCTION and not self.production_enabled:
            raise SigningPolicyError("production signing is disabled unless explicitly enabled")

        return SigningPolicy(
            self.mode,
            source_sha,
            timestamp_url=timestamp_url,
            certificate_thumbprint=thumbprint,
            production_enabled=self.production_enabled,
        )


@dataclass(frozen=True)
class SubjectEvidence:
    filename: str
    sha256: str
    authenticode_status: str
    signer_subject: str | None
    signer_thumbprint: str | None
    timestamp_subject: str | None
    timestamp_verified: bool
    signtool_verified: bool


@dataclass(frozen=True)
class SigningEvidence:
    schema_version: int
    source_sha: str
    mode: str
    hash_algorithm: str
    timestamp_protocol: str
    timestamp_url: str | None
    certificate_thumbprint: str | None
    production_signed: bool
    public_trust_claim: bool
    signtool_version: str
    subjects: tuple[SubjectEvidence, ...]

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["subjects"] = [asdict(subject) for subject in self.subjects]
        return result


def sha256_file(path: str | Path) -> str:
    target = Path(path)
    return hashlib.sha256(target.read_bytes()).hexdigest()


def signtool_sign_args(
    signtool: str,
    subject: str | Path,
    policy: SigningPolicy,
) -> list[str]:
    policy = policy.validated()
    if policy.mode is SigningMode.UNSIGNED:
        raise SigningPolicyError("unsigned mode does not build a SignTool sign command")
    assert policy.certificate_thumbprint is not None
    assert policy.timestamp_url is not None
    return [
        signtool,
        "sign",
        "/sha1",
        policy.certificate_thumbprint,
        "/s",
        "My",
        "/fd",
        HASH_ALGORITHM,
        "/tr",
        policy.timestamp_url,
        "/td",
        HASH_ALGORITHM,
        str(subject),
    ]


def signtool_verify_args(signtool: str, subject: str | Path) -> list[str]:
    return [signtool, "verify", "/pa", "/all", "/tw", "/v", str(subject)]


def build_signing_evidence(
    policy: SigningPolicy,
    *,
    signtool_version: str,
    subjects: list[SubjectEvidence] | tuple[SubjectEvidence, ...],
) -> SigningEvidence:
    policy = policy.validated()
    material = tuple(subjects)
    if not material:
        raise SigningPolicyError("signing evidence requires at least one subject")

    if policy.mode is SigningMode.UNSIGNED:
        if any(item.authenticode_status.lower() != "notsigned" for item in material):
            raise SigningPolicyError("unsigned evidence contains a signed subject")
        production_signed = False
        public_trust_claim = False
    else:
        for item in material:
            if not item.signtool_verified:
                raise SigningPolicyError(f"SignTool verification failed for {item.filename}")
            if not item.timestamp_verified or not item.timestamp_subject:
                raise SigningPolicyError(f"RFC3161 timestamp verification failed for {item.filename}")
            if item.authenticode_status.lower() != "valid":
                raise SigningPolicyError(f"Authenticode status is not Valid for {item.filename}")
            if (item.signer_thumbprint or "").upper() != policy.certificate_thumbprint:
                raise SigningPolicyError(f"signer thumbprint mismatch for {item.filename}")
        production_signed = policy.mode is SigningMode.PRODUCTION
        public_trust_claim = production_signed

    return SigningEvidence(
        schema_version=1,
        source_sha=policy.source_sha,
        mode=policy.mode.value,
        hash_algorithm=HASH_ALGORITHM.lower(),
        timestamp_protocol=(
            "RFC3161" if policy.mode is not SigningMode.UNSIGNED else "not-applicable"
        ),
        timestamp_url=policy.timestamp_url,
        certificate_thumbprint=policy.certificate_thumbprint,
        production_signed=production_signed,
        public_trust_claim=public_trust_claim,
        signtool_version=signtool_version,
        subjects=material,
    )


__all__ = [
    "HASH_ALGORITHM",
    "SigningEvidence",
    "SigningMode",
    "SigningPolicy",
    "SigningPolicyError",
    "SubjectEvidence",
    "build_signing_evidence",
    "sha256_file",
    "signtool_sign_args",
    "signtool_verify_args",
]
