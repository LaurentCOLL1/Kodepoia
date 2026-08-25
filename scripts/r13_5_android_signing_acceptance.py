from __future__ import annotations

import argparse
import json
import os
import platform
import re
import secrets as runtime_secrets
import shutil
import subprocess
from pathlib import Path

from jsonschema import Draft202012Validator

from kodepoia.core.secrets import KodeSecrets, MemorySecretBackend
from kodepoia.mobile.android_build import AndroidArtifactKind
from kodepoia.mobile.android_signing import (
    AndroidSigningAcceptanceEvidence,
    AndroidSigningIdentity,
    AndroidSigningSecretRefs,
    AndroidSigningState,
    bounded_signing_environment,
    certificate_fingerprints_from_pem,
    inspect_android_signing,
    validate_signing_payload_no_leaks,
)

ROOT = Path(__file__).resolve().parents[1]
_SCHEMA = ROOT / "schemas/r13/android-signing-evidence.schema.json"
_STORE_ENV = "KODEPOIA_R13_TEST_STORE_PASSWORD"
_KEY_ENV = "KODEPOIA_R13_TEST_KEY_PASSWORD"


def _tool(name: str) -> str:
    direct = shutil.which(name)
    if direct:
        return direct
    if name == "apksigner":
        sdk = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
        if sdk:
            suffix = "apksigner.bat" if os.name == "nt" else "apksigner"
            candidate = Path(sdk) / "build-tools" / "36.0.0" / suffix
            if candidate.is_file():
                return str(candidate)
    raise SystemExit(f"required R13.5 signing tool is unavailable: {name}")


def _run(argv: list[str], *, env: dict[str, str]) -> bytes:
    completed = subprocess.run(
        argv,
        capture_output=True,
        check=False,
        timeout=120,
        env=env,
    )
    if completed.returncode != 0:
        raise SystemExit("ephemeral R13.5 signing command failed")
    return completed.stdout


def _generate_test_keystore(
    private_root: Path,
    keytool: str,
    kode_secrets: KodeSecrets,
    refs: AndroidSigningSecretRefs,
) -> tuple[Path, str]:
    private_root.mkdir(parents=True, exist_ok=True)
    keystore = private_root / "r13-5-ephemeral.jks"
    store_password = runtime_secrets.token_urlsafe(32)
    key_password = runtime_secrets.token_urlsafe(32)
    alias = "r13-5-test"
    kode_secrets.store(refs.keystore.namespace, refs.keystore.key, str(keystore))
    kode_secrets.store(refs.store_password.namespace, refs.store_password.key, store_password)
    kode_secrets.store(refs.key_password.namespace, refs.key_password.key, key_password)
    kode_secrets.store(refs.key_alias.namespace, refs.key_alias.key, alias)

    env = bounded_signing_environment({_STORE_ENV: store_password, _KEY_ENV: key_password})
    _run(
        [
            keytool,
            "-genkeypair",
            "-alias",
            alias,
            "-keyalg",
            "RSA",
            "-keysize",
            "3072",
            "-validity",
            "30",
            "-dname",
            "CN=Kodepoia R13.5 CI,O=Kodepoia,C=FR",
            "-keystore",
            str(keystore),
            "-storetype",
            "JKS",
            "-storepass:env",
            _STORE_ENV,
            "-keypass:env",
            _KEY_ENV,
        ],
        env=env,
    )
    cert_pem = _run(
        [
            keytool,
            "-exportcert",
            "-rfc",
            "-alias",
            alias,
            "-keystore",
            str(keystore),
            "-storepass:env",
            _STORE_ENV,
        ],
        env=env,
    )
    fingerprints = certificate_fingerprints_from_pem(cert_pem)
    if len(fingerprints) != 1:
        raise SystemExit("ephemeral R13.5 keystore did not expose exactly one certificate")
    return keystore, fingerprints[0]


def _sign_apk(
    source: Path,
    destination: Path,
    *,
    apksigner: str,
    keystore: Path,
    alias: str,
    store_password: str,
    key_password: str,
) -> None:
    env = bounded_signing_environment({_STORE_ENV: store_password, _KEY_ENV: key_password})
    _run(
        [
            apksigner,
            "sign",
            "--ks",
            str(keystore),
            "--ks-key-alias",
            alias,
            "--ks-pass",
            f"env:{_STORE_ENV}",
            "--key-pass",
            f"env:{_KEY_ENV}",
            "--out",
            str(destination),
            str(source),
        ],
        env=env,
    )


def _sign_aab(
    source: Path,
    destination: Path,
    *,
    jarsigner: str,
    keystore: Path,
    alias: str,
    store_password: str,
    key_password: str,
) -> None:
    env = bounded_signing_environment({_STORE_ENV: store_password, _KEY_ENV: key_password})
    _run(
        [
            jarsigner,
            "-keystore",
            str(keystore),
            "-storepass:env",
            _STORE_ENV,
            "-keypass:env",
            _KEY_ENV,
            "-signedjar",
            str(destination),
            str(source),
            alias,
        ],
        env=env,
    )


def collect(source_sha: str, staging_root: Path, private_root: Path, output: Path) -> None:
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise SystemExit("source SHA must be exact lowercase 40-hex Git SHA")

    apk_source = staging_root / "app/build/outputs/apk/debug/app-debug.apk"
    aab_source = staging_root / "app/build/outputs/bundle/release/app-release.aab"
    if not apk_source.is_file() or not aab_source.is_file():
        raise SystemExit("R13.5 requires the exact-head R13.4 APK and AAB build outputs")

    apksigner = _tool("apksigner")
    jarsigner = _tool("jarsigner")
    keytool = _tool("keytool")

    namespace = "kodepoia.r13.5.android-signing"
    secrets_store = KodeSecrets(MemorySecretBackend())
    refs = AndroidSigningSecretRefs(
        keystore=secrets_store.ref(namespace, "keystore"),
        store_password=secrets_store.ref(namespace, "store_password"),
        key_alias=secrets_store.ref(namespace, "key_alias"),
        key_password=secrets_store.ref(namespace, "key_password"),
    )

    if private_root.exists():
        shutil.rmtree(private_root)
    private_root.mkdir(parents=True)
    try:
        unsigned = inspect_android_signing(
            aab_source,
            AndroidArtifactKind.AAB,
            AndroidSigningIdentity(),
            jarsigner=jarsigner,
            keytool=keytool,
        )
        if unsigned.state != AndroidSigningState.UNSIGNED:
            raise SystemExit("release AAB expected to be unsigned before R13.5 test signing")

        keystore, test_fingerprint = _generate_test_keystore(
            private_root,
            keytool,
            secrets_store,
            refs,
        )
        resolved = refs.resolve(secrets_store)
        signed_apk = private_root / "fixture-test-signed.apk"
        signed_aab = private_root / "fixture-test-signed.aab"
        _sign_apk(
            apk_source,
            signed_apk,
            apksigner=apksigner,
            keystore=keystore,
            alias=resolved["key_alias"],
            store_password=resolved["store_password"],
            key_password=resolved["key_password"],
        )
        _sign_aab(
            aab_source,
            signed_aab,
            jarsigner=jarsigner,
            keystore=keystore,
            alias=resolved["key_alias"],
            store_password=resolved["store_password"],
            key_password=resolved["key_password"],
        )

        identity = AndroidSigningIdentity(test_sha256=test_fingerprint)
        apk_evidence = inspect_android_signing(
            signed_apk,
            AndroidArtifactKind.APK,
            identity,
            apksigner=apksigner,
        )
        aab_evidence = inspect_android_signing(
            signed_aab,
            AndroidArtifactKind.AAB,
            identity,
            jarsigner=jarsigner,
            keytool=keytool,
        )
        evidence = AndroidSigningAcceptanceEvidence(
            schema_version=1,
            source_sha=source_sha,
            runner_os=platform.system(),
            inspections=(unsigned, apk_evidence, aab_evidence),
            secret_refs=refs,
        )
        payload = evidence.to_dict()
        validate_signing_payload_no_leaks(
            payload,
            refs,
            known_secret_values=secrets_store.known_values(),
            known_private_paths=(str(private_root), str(keystore)),
        )
        schema = json.loads(_SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(payload)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(evidence.canonical_bytes(known_secret_values=secrets_store.known_values()) + b"\n")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    finally:
        shutil.rmtree(private_root, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="R13.5 hosted Android signing acceptance")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--staging-root", type=Path, required=True)
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    collect(args.source_sha, args.staging_root, args.private_root, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
