from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from kodepoia.release.signing import (
    HASH_ALGORITHM,
    SigningMode,
    SigningPolicy,
    SigningPolicyError,
    SubjectEvidence,
    build_signing_evidence,
    signtool_sign_args,
    signtool_verify_args,
)

TEST_THUMBPRINT = "A1" * 20
TEST_TSA = "http://timestamp.digicert.com"


def _expect_rejected(name: str, fn: Any) -> dict[str, str]:
    try:
        fn()
    except SigningPolicyError as exc:
        return {"case": name, "status": "PASS", "detail": str(exc)}
    raise AssertionError(f"{name} unexpectedly passed")


def _synthetic(source_sha: str) -> dict[str, object]:
    unsigned_policy = SigningPolicy(SigningMode.UNSIGNED, source_sha).validated()
    test_policy = SigningPolicy(
        SigningMode.TEST,
        source_sha,
        timestamp_url=TEST_TSA,
        certificate_thumbprint=TEST_THUMBPRINT,
    ).validated()

    sign_args = signtool_sign_args("signtool.exe", "KodepoiaSetup.exe", test_policy)
    verify_args = signtool_verify_args("signtool.exe", "KodepoiaSetup.exe")
    for fragment in ("/fd", HASH_ALGORITHM, "/tr", TEST_TSA, "/td", HASH_ALGORITHM):
        if fragment not in sign_args:
            raise AssertionError(f"missing SignTool sign contract fragment: {fragment}")
    for fragment in ("/pa", "/all", "/tw", "/v"):
        if fragment not in verify_args:
            raise AssertionError(f"missing SignTool verify contract fragment: {fragment}")

    unsigned = build_signing_evidence(
        unsigned_policy,
        signtool_version="synthetic",
        subjects=[
            SubjectEvidence(
                filename="KodepoiaSetup.exe",
                sha256="0" * 64,
                authenticode_status="NotSigned",
                signer_subject=None,
                signer_thumbprint=None,
                timestamp_subject=None,
                timestamp_verified=False,
                signtool_verified=False,
            )
        ],
    )
    test = build_signing_evidence(
        test_policy,
        signtool_version="synthetic",
        subjects=[
            SubjectEvidence(
                filename="KodepoiaSetup.exe",
                sha256="1" * 64,
                authenticode_status="Valid",
                signer_subject="CN=Kodepoia R18.4 Test Signing",
                signer_thumbprint=TEST_THUMBPRINT,
                timestamp_subject="CN=Synthetic RFC3161 TSA",
                timestamp_verified=True,
                signtool_verified=True,
            )
        ],
    )
    if unsigned.production_signed or unsigned.public_trust_claim:
        raise AssertionError("unsigned mode fabricated a production/public-trust claim")
    if test.production_signed or test.public_trust_claim:
        raise AssertionError("test mode fabricated a production/public-trust claim")

    negative_controls = [
        _expect_rejected(
            "production-without-explicit-enable",
            lambda: SigningPolicy(
                SigningMode.PRODUCTION,
                source_sha,
                timestamp_url=TEST_TSA,
                certificate_thumbprint=TEST_THUMBPRINT,
            ).validated(),
        ),
        _expect_rejected(
            "signed-mode-without-timestamp",
            lambda: SigningPolicy(
                SigningMode.TEST,
                source_sha,
                certificate_thumbprint=TEST_THUMBPRINT,
            ).validated(),
        ),
        _expect_rejected(
            "timestamp-url-with-credentials",
            lambda: SigningPolicy(
                SigningMode.TEST,
                source_sha,
                timestamp_url="https://user:secret@example.invalid/tsa",
                certificate_thumbprint=TEST_THUMBPRINT,
            ).validated(),
        ),
        _expect_rejected(
            "wrong-certificate-evidence",
            lambda: build_signing_evidence(
                test_policy,
                signtool_version="synthetic",
                subjects=[
                    SubjectEvidence(
                        filename="KodepoiaSetup.exe",
                        sha256="2" * 64,
                        authenticode_status="Valid",
                        signer_subject="CN=Wrong",
                        signer_thumbprint="B2" * 20,
                        timestamp_subject="CN=Synthetic RFC3161 TSA",
                        timestamp_verified=True,
                        signtool_verified=True,
                    )
                ],
            ),
        ),
        _expect_rejected(
            "missing-timestamp-evidence",
            lambda: build_signing_evidence(
                test_policy,
                signtool_version="synthetic",
                subjects=[
                    SubjectEvidence(
                        filename="KodepoiaSetup.exe",
                        sha256="3" * 64,
                        authenticode_status="Valid",
                        signer_subject="CN=Kodepoia R18.4 Test Signing",
                        signer_thumbprint=TEST_THUMBPRINT,
                        timestamp_subject=None,
                        timestamp_verified=False,
                        signtool_verified=True,
                    )
                ],
            ),
        ),
    ]

    return {
        "status": "PASS",
        "mode": "synthetic-contract",
        "source_sha": source_sha,
        "hash_algorithm": HASH_ALGORITHM.lower(),
        "timestamp_protocol": "RFC3161",
        "sign_command": sign_args,
        "verify_command": verify_args,
        "unsigned_claim": unsigned.to_dict(),
        "test_claim": test.to_dict(),
        "negative_controls": negative_controls,
        "manual_intervention": "NONE",
        "production_signing": "CONDITIONAL_NOT_TRIGGERED",
        "public_github_release": "NOT_TRIGGERED",
        "public_winget_submission": "NOT_TRIGGERED",
    }


def _actual(source_sha: str, evidence_path: Path) -> dict[str, object]:
    payload = json.loads(evidence_path.read_text(encoding="utf-8-sig"))
    if payload.get("source_sha") != source_sha:
        raise AssertionError("actual R18.4 evidence source SHA mismatch")
    if payload.get("mode") != "test":
        raise AssertionError("actual R18.4 CI path must use non-production test mode")
    if payload.get("production_signed") is not False or payload.get("public_trust_claim") is not False:
        raise AssertionError("test-signing evidence fabricated a production/public trust claim")
    if payload.get("hash_algorithm") != "sha256":
        raise AssertionError("actual R18.4 evidence is not SHA-256 bound")
    if payload.get("timestamp_protocol") != "RFC3161":
        raise AssertionError("actual R18.4 evidence does not claim RFC3161 timestamp verification")

    subjects = payload.get("subjects")
    if not isinstance(subjects, list):
        raise AssertionError("actual R18.4 evidence subjects missing")
    names = {str(item.get("filename")) for item in subjects if isinstance(item, dict)}
    required = {"KodepoiaStudio.exe", "KodepoiaSetup.exe"}
    if not required.issubset(names):
        raise AssertionError(f"actual R18.4 evidence missing subjects: {sorted(required - names)}")
    for item in subjects:
        if not isinstance(item, dict):
            raise AssertionError("invalid actual subject evidence")
        if item.get("authenticode_status") != "Valid":
            raise AssertionError(f"invalid Authenticode status for {item.get('filename')}")
        if item.get("signtool_verified") is not True or item.get("timestamp_verified") is not True:
            raise AssertionError(f"verification/timestamp failure for {item.get('filename')}")

    return {
        "status": "PASS",
        "mode": "actual-windows-test-signing",
        "source_sha": source_sha,
        "evidence": payload,
        "manual_intervention": "NONE",
        "production_signing": "CONDITIONAL_NOT_TRIGGERED",
        "public_github_release": "NOT_TRIGGERED",
        "public_winget_submission": "NOT_TRIGGERED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit exact-source R18.4 Authenticode acceptance.")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--actual-evidence")
    args = parser.parse_args()

    report = (
        _actual(args.source_sha, Path(args.actual_evidence))
        if args.actual_evidence
        else _synthetic(args.source_sha)
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
