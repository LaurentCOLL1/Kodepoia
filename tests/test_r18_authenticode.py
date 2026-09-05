from __future__ import annotations

import pytest

from kodepoia.release.signing import (
    SigningMode,
    SigningPolicy,
    SigningPolicyError,
    SubjectEvidence,
    build_signing_evidence,
    signtool_sign_args,
    signtool_verify_args,
)

SOURCE = "a" * 40
THUMB = "AB" * 20
TSA = "http://timestamp.digicert.com"
# R18.4 exact-source CI exercises these same contracts with a non-production certificate.


def test_unsigned_policy_is_exact_source_and_secret_free() -> None:
    policy = SigningPolicy(SigningMode.UNSIGNED, SOURCE.upper()).validated()
    assert policy.source_sha == SOURCE
    assert policy.timestamp_url is None
    assert policy.certificate_thumbprint is None


def test_unsigned_policy_rejects_signing_material() -> None:
    with pytest.raises(SigningPolicyError):
        SigningPolicy(SigningMode.UNSIGNED, SOURCE, timestamp_url=TSA).validated()


def test_test_signing_requires_timestamp_and_certificate() -> None:
    with pytest.raises(SigningPolicyError):
        SigningPolicy(SigningMode.TEST, SOURCE).validated()


def test_production_is_fail_closed_without_explicit_enable() -> None:
    with pytest.raises(SigningPolicyError, match="explicitly enabled"):
        SigningPolicy(
            SigningMode.PRODUCTION,
            SOURCE,
            timestamp_url=TSA,
            certificate_thumbprint=THUMB,
        ).validated()


def test_production_can_be_constructed_only_when_explicitly_enabled() -> None:
    policy = SigningPolicy(
        SigningMode.PRODUCTION,
        SOURCE,
        timestamp_url=TSA,
        certificate_thumbprint=THUMB.lower(),
        production_enabled=True,
    ).validated()
    assert policy.certificate_thumbprint == THUMB
    assert policy.production_enabled is True


def test_timestamp_url_rejects_embedded_credentials() -> None:
    with pytest.raises(SigningPolicyError):
        SigningPolicy(
            SigningMode.TEST,
            SOURCE,
            timestamp_url="https://user:secret@example.invalid/tsa",
            certificate_thumbprint=THUMB,
        ).validated()


def test_signtool_sign_contract_is_sha256_rfc3161() -> None:
    policy = SigningPolicy(
        SigningMode.TEST,
        SOURCE,
        timestamp_url=TSA,
        certificate_thumbprint=THUMB,
    )
    args = signtool_sign_args("signtool.exe", "KodepoiaSetup.exe", policy)
    assert args == [
        "signtool.exe",
        "sign",
        "/sha1",
        THUMB,
        "/s",
        "My",
        "/fd",
        "SHA256",
        "/tr",
        TSA,
        "/td",
        "SHA256",
        "KodepoiaSetup.exe",
    ]


def test_signtool_verify_contract_requires_authenticode_and_timestamp() -> None:
    assert signtool_verify_args("signtool.exe", "KodepoiaSetup.exe") == [
        "signtool.exe",
        "verify",
        "/pa",
        "/all",
        "/tw",
        "/v",
        "KodepoiaSetup.exe",
    ]


def test_test_evidence_never_becomes_production_claim() -> None:
    policy = SigningPolicy(
        SigningMode.TEST,
        SOURCE,
        timestamp_url=TSA,
        certificate_thumbprint=THUMB,
    )
    evidence = build_signing_evidence(
        policy,
        signtool_version="10.0",
        subjects=[
            SubjectEvidence(
                filename="KodepoiaSetup.exe",
                sha256="1" * 64,
                authenticode_status="Valid",
                signer_subject="CN=Kodepoia Test",
                signer_thumbprint=THUMB,
                timestamp_subject="CN=RFC3161 TSA",
                timestamp_verified=True,
                signtool_verified=True,
            )
        ],
    )
    assert evidence.production_signed is False
    assert evidence.public_trust_claim is False


def test_signed_evidence_rejects_missing_timestamp() -> None:
    policy = SigningPolicy(
        SigningMode.TEST,
        SOURCE,
        timestamp_url=TSA,
        certificate_thumbprint=THUMB,
    )
    with pytest.raises(SigningPolicyError, match="timestamp"):
        build_signing_evidence(
            policy,
            signtool_version="10.0",
            subjects=[
                SubjectEvidence(
                    filename="KodepoiaSetup.exe",
                    sha256="1" * 64,
                    authenticode_status="Valid",
                    signer_subject="CN=Kodepoia Test",
                    signer_thumbprint=THUMB,
                    timestamp_subject=None,
                    timestamp_verified=False,
                    signtool_verified=True,
                )
            ],
        )


def test_signed_evidence_rejects_invalid_or_expired_status() -> None:
    policy = SigningPolicy(
        SigningMode.TEST,
        SOURCE,
        timestamp_url=TSA,
        certificate_thumbprint=THUMB,
    )
    with pytest.raises(SigningPolicyError, match="not Valid"):
        build_signing_evidence(
            policy,
            signtool_version="10.0",
            subjects=[
                SubjectEvidence(
                    filename="KodepoiaSetup.exe",
                    sha256="1" * 64,
                    authenticode_status="NotTimeValid",
                    signer_subject="CN=Kodepoia Test",
                    signer_thumbprint=THUMB,
                    timestamp_subject="CN=RFC3161 TSA",
                    timestamp_verified=True,
                    signtool_verified=True,
                )
            ],
        )


def test_signed_evidence_rejects_wrong_certificate() -> None:
    policy = SigningPolicy(
        SigningMode.TEST,
        SOURCE,
        timestamp_url=TSA,
        certificate_thumbprint=THUMB,
    )
    with pytest.raises(SigningPolicyError, match="thumbprint"):
        build_signing_evidence(
            policy,
            signtool_version="10.0",
            subjects=[
                SubjectEvidence(
                    filename="KodepoiaSetup.exe",
                    sha256="1" * 64,
                    authenticode_status="Valid",
                    signer_subject="CN=Wrong",
                    signer_thumbprint="CD" * 20,
                    timestamp_subject="CN=RFC3161 TSA",
                    timestamp_verified=True,
                    signtool_verified=True,
                )
            ],
        )
