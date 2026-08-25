from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from kodepoia.core.secrets import KodeSecrets, MemorySecretBackend, find_secret_leaks
from kodepoia.mobile.android_build import AndroidArtifactKind
from kodepoia.mobile.android_signing import (
    AndroidSigningAcceptanceEvidence,
    AndroidSigningIdentity,
    AndroidSigningInspection,
    AndroidSigningRole,
    AndroidSigningSecretRefs,
    AndroidSigningState,
    AndroidUploadKeyRotation,
    certificate_fingerprints_from_pem,
    inspect_android_signing,
    normalize_sha256_fingerprint,
    validate_signing_payload_no_leaks,
)

ROOT = Path(__file__).resolve().parents[1]
A = "11" * 32
B = "22" * 32
C = "33" * 32
D = "44" * 32


def _refs(secrets: KodeSecrets) -> AndroidSigningSecretRefs:
    ns = "kodepoia.r13.5.test"
    return AndroidSigningSecretRefs(
        keystore=secrets.ref(ns, "keystore"),
        store_password=secrets.ref(ns, "store_password"),
        key_alias=secrets.ref(ns, "key_alias"),
        key_password=secrets.ref(ns, "key_password"),
    )


def _inspection(
    kind: AndroidArtifactKind,
    state: AndroidSigningState,
    role: AndroidSigningRole,
    fingerprint: str | None = None,
) -> AndroidSigningInspection:
    return AndroidSigningInspection(
        kind=kind,
        artifact_sha256="aa" * 32,
        state=state,
        role=role,
        certificate_sha256=() if fingerprint is None else (fingerprint,),
        verifier=None if fingerprint is None else "test-verifier",
    )


def test_r13_5_fingerprint_normalization_is_canonical() -> None:
    coloned = ":".join(A[index : index + 2] for index in range(0, 64, 2)).upper()
    assert normalize_sha256_fingerprint(coloned) == A
    with pytest.raises(ValueError, match="64 hexadecimal"):
        normalize_sha256_fingerprint("AA:BB")


def test_r13_5_signing_states_are_exact_and_identity_is_fail_closed() -> None:
    assert {item.value for item in AndroidSigningState} == {
        "UNSIGNED",
        "DEBUG_SIGNED",
        "TEST_SIGNED",
        "UPLOAD_SIGNED",
        "PLAY_APP_SIGNING_READY",
        "SIGNING_UNAVAILABLE",
    }
    identity = AndroidSigningIdentity(
        debug_sha256=A,
        test_sha256=B,
        upload_sha256=C,
        app_signing_sha256=D,
    )
    assert identity.classify(()) == (AndroidSigningState.UNSIGNED, AndroidSigningRole.NONE)
    assert identity.classify((A,))[0] == AndroidSigningState.DEBUG_SIGNED
    assert identity.classify((B,))[0] == AndroidSigningState.TEST_SIGNED
    assert identity.classify((C,))[0] == AndroidSigningState.PLAY_APP_SIGNING_READY
    assert identity.classify((D,))[0] == AndroidSigningState.PLAY_APP_SIGNING_READY
    with pytest.raises(ValueError, match="unexpected signing certificate"):
        identity.classify(("55" * 32,))
    with pytest.raises(ValueError, match="multiple signing certificates"):
        identity.classify((A, B))


def test_r13_5_upload_and_play_app_signing_keys_must_be_distinct() -> None:
    with pytest.raises(ValueError, match="must be distinct"):
        AndroidSigningIdentity(upload_sha256=A, app_signing_sha256=A)
    upload_only = AndroidSigningIdentity(upload_sha256=A)
    assert upload_only.classify((A,)) == (
        AndroidSigningState.UPLOAD_SIGNED,
        AndroidSigningRole.UPLOAD,
    )


def test_r13_5_upload_rotation_changes_upload_key_not_app_signing_key() -> None:
    rotation = AndroidUploadKeyRotation(
        previous_upload_sha256=A,
        replacement_upload_sha256=B,
        app_signing_sha256=C,
        reason="upload credential recovery",
        recovery_sequence=1,
    )
    assert rotation.to_dict()["app_signing_sha256"] == C
    with pytest.raises(ValueError, match="must change"):
        AndroidUploadKeyRotation(A, A, C, "recovery", 1)
    with pytest.raises(ValueError, match="must remain distinct"):
        AndroidUploadKeyRotation(A, B, A, "recovery", 1)


def test_r13_5_kodesecrets_refs_resolve_without_serializing_values() -> None:
    secrets = KodeSecrets(MemorySecretBackend())
    refs = _refs(secrets)
    values = {
        refs.keystore: "/private/ci/r13-5.jks",
        refs.store_password: "store-secret-9d8f",
        refs.key_alias: "private-alias",
        refs.key_password: "key-secret-2bc1",
    }
    for ref, value in values.items():
        secrets.store(ref.namespace, ref.key, value)
    assert refs.resolve(secrets)["keystore"] == "/private/ci/r13-5.jks"
    payload = {"secret_refs": refs.to_dict()}
    assert find_secret_leaks(payload, secrets.known_values()) == ()
    validate_signing_payload_no_leaks(
        payload,
        refs,
        known_secret_values=secrets.known_values(),
        known_private_paths=("/private/ci/r13-5.jks",),
    )
    leaked = {"secret_refs": refs.to_dict(), "bad": "store-secret-9d8f"}
    with pytest.raises(ValueError, match="raw secret material"):
        validate_signing_payload_no_leaks(
            leaked,
            refs,
            known_secret_values=secrets.known_values(),
        )


def test_r13_5_private_keystore_path_cannot_enter_durable_evidence() -> None:
    secrets = KodeSecrets(MemorySecretBackend())
    refs = _refs(secrets)
    payload = {"secret_refs": refs.to_dict(), "note": "C:/private/r13-5.jks"}
    with pytest.raises(ValueError, match="private signing path"):
        validate_signing_payload_no_leaks(
            payload,
            refs,
            known_secret_values=(),
            known_private_paths=("C:/private/r13-5.jks",),
        )


def test_r13_5_unsigned_artifact_is_detected_without_signing_tool(tmp_path: Path) -> None:
    path = tmp_path / "unsigned.aab"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("base/manifest/AndroidManifest.xml", b"manifest")
        archive.writestr("base/dex/classes.dex", b"dex")
    evidence = inspect_android_signing(
        path,
        AndroidArtifactKind.AAB,
        AndroidSigningIdentity(),
        jarsigner="definitely-not-installed-jarsigner",
        keytool="definitely-not-installed-keytool",
    )
    assert evidence.state == AndroidSigningState.UNSIGNED
    assert evidence.certificate_sha256 == ()


def test_r13_5_signed_material_without_verifier_is_not_claimed_signed(tmp_path: Path) -> None:
    path = tmp_path / "signed-looking.aab"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("META-INF/MANIFEST.MF", b"manifest")
        archive.writestr("META-INF/R13.SF", b"signature-file")
        archive.writestr("META-INF/R13.RSA", b"signature-block")
        archive.writestr("base/manifest/AndroidManifest.xml", b"manifest")
    evidence = inspect_android_signing(
        path,
        AndroidArtifactKind.AAB,
        AndroidSigningIdentity(test_sha256=A),
        jarsigner="definitely-not-installed-jarsigner",
        keytool="definitely-not-installed-keytool",
    )
    assert evidence.state == AndroidSigningState.SIGNING_UNAVAILABLE
    assert evidence.blockers


def test_r13_5_pem_certificate_fingerprint_is_public_sha256() -> None:
    der = b"not-a-real-cert-but-valid-base64-test-bytes"
    import base64

    pem = (
        b"-----BEGIN CERTIFICATE-----\n"
        + base64.b64encode(der)
        + b"\n-----END CERTIFICATE-----\n"
    )
    import hashlib

    assert certificate_fingerprints_from_pem(pem) == (hashlib.sha256(der).hexdigest(),)


def test_r13_5_acceptance_evidence_requires_unsigned_and_test_signed_apk_aab() -> None:
    secrets = KodeSecrets(MemorySecretBackend())
    refs = _refs(secrets)
    evidence = AndroidSigningAcceptanceEvidence(
        schema_version=1,
        source_sha="a" * 40,
        runner_os="Linux",
        inspections=(
            _inspection(
                AndroidArtifactKind.AAB,
                AndroidSigningState.UNSIGNED,
                AndroidSigningRole.NONE,
            ),
            _inspection(
                AndroidArtifactKind.APK,
                AndroidSigningState.TEST_SIGNED,
                AndroidSigningRole.TEST,
                A,
            ),
            _inspection(
                AndroidArtifactKind.AAB,
                AndroidSigningState.TEST_SIGNED,
                AndroidSigningRole.TEST,
                A,
            ),
        ),
        secret_refs=refs,
    )
    payload = evidence.to_dict()
    assert payload["status"] == "pass"
    assert all("path" not in json.dumps(item).casefold() for item in payload["inspections"])

    with pytest.raises(ValueError, match="test-signed APK and AAB"):
        AndroidSigningAcceptanceEvidence(
            schema_version=1,
            source_sha="a" * 40,
            runner_os="Linux",
            inspections=(
                _inspection(
                    AndroidArtifactKind.AAB,
                    AndroidSigningState.UNSIGNED,
                    AndroidSigningRole.NONE,
                ),
                _inspection(
                    AndroidArtifactKind.APK,
                    AndroidSigningState.TEST_SIGNED,
                    AndroidSigningRole.TEST,
                    A,
                ),
            ),
            secret_refs=refs,
        )


def test_r13_5_evidence_schema_is_strict_and_matches_model() -> None:
    schema = json.loads(
        (ROOT / "schemas/r13/android-signing-evidence.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    secrets = KodeSecrets(MemorySecretBackend())
    refs = _refs(secrets)
    payload = AndroidSigningAcceptanceEvidence(
        schema_version=1,
        source_sha="b" * 40,
        runner_os="Windows",
        inspections=(
            _inspection(
                AndroidArtifactKind.AAB,
                AndroidSigningState.UNSIGNED,
                AndroidSigningRole.NONE,
            ),
            _inspection(
                AndroidArtifactKind.APK,
                AndroidSigningState.TEST_SIGNED,
                AndroidSigningRole.TEST,
                B,
            ),
            _inspection(
                AndroidArtifactKind.AAB,
                AndroidSigningState.TEST_SIGNED,
                AndroidSigningRole.TEST,
                B,
            ),
        ),
        secret_refs=refs,
    ).to_dict()
    Draft202012Validator(schema).validate(payload)
    payload["unexpected"] = True
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(payload)
