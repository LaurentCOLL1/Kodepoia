from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import zipfile
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Mapping, Sequence

from kodepoia.core.secrets import KodeSecrets, SecretRef, assert_secret_refs_only
from kodepoia.mobile.android_build import AndroidArtifactKind

_PEM_RE = re.compile(
    rb"-----BEGIN CERTIFICATE-----\s*(.*?)\s*-----END CERTIFICATE-----",
    re.DOTALL,
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_APK_SIG_BLOCK_MAGIC = b"APK Sig Block 42"


class AndroidSigningState(StrEnum):
    UNSIGNED = "UNSIGNED"
    DEBUG_SIGNED = "DEBUG_SIGNED"
    TEST_SIGNED = "TEST_SIGNED"
    UPLOAD_SIGNED = "UPLOAD_SIGNED"
    PLAY_APP_SIGNING_READY = "PLAY_APP_SIGNING_READY"
    SIGNING_UNAVAILABLE = "SIGNING_UNAVAILABLE"


class AndroidSigningRole(StrEnum):
    NONE = "none"
    DEBUG = "debug"
    TEST = "test"
    UPLOAD = "upload"
    APP_SIGNING = "app_signing"


def normalize_sha256_fingerprint(value: str) -> str:
    compact = re.sub(r"[^0-9A-Fa-f]", "", value).lower()
    if not _SHA256_RE.fullmatch(compact):
        raise ValueError("certificate fingerprint must contain exactly 64 hexadecimal digits")
    return compact


@dataclass(frozen=True)
class AndroidSigningSecretRefs:
    keystore: SecretRef
    store_password: SecretRef
    key_alias: SecretRef
    key_password: SecretRef

    def refs(self) -> tuple[SecretRef, ...]:
        return (self.keystore, self.store_password, self.key_alias, self.key_password)

    def to_dict(self) -> dict[str, object]:
        return {
            "keystore": self.keystore.to_dict(),
            "store_password": self.store_password.to_dict(),
            "key_alias": self.key_alias.to_dict(),
            "key_password": self.key_password.to_dict(),
        }

    def resolve(self, secrets: KodeSecrets) -> dict[str, str]:
        resolved: dict[str, str] = {}
        for field_name, ref in (
            ("keystore", self.keystore),
            ("store_password", self.store_password),
            ("key_alias", self.key_alias),
            ("key_password", self.key_password),
        ):
            value = secrets.resolve(ref)
            if value is None:
                raise ValueError(f"required Android signing secret is unavailable: {field_name}")
            resolved[field_name] = value
        return resolved


@dataclass(frozen=True)
class AndroidSigningIdentity:
    debug_sha256: str | None = None
    test_sha256: str | None = None
    upload_sha256: str | None = None
    app_signing_sha256: str | None = None

    def __post_init__(self) -> None:
        for name in ("debug_sha256", "test_sha256", "upload_sha256", "app_signing_sha256"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, normalize_sha256_fingerprint(value))
        if (
            self.upload_sha256 is not None
            and self.app_signing_sha256 is not None
            and self.upload_sha256 == self.app_signing_sha256
        ):
            raise ValueError("upload key and Play app-signing key fingerprints must be distinct")

    def classify(self, fingerprints: Sequence[str]) -> tuple[AndroidSigningState, AndroidSigningRole]:
        normalized = tuple(dict.fromkeys(normalize_sha256_fingerprint(item) for item in fingerprints))
        if not normalized:
            return AndroidSigningState.UNSIGNED, AndroidSigningRole.NONE
        if len(normalized) != 1:
            raise ValueError("multiple signing certificates are outside the R13.5 single-signer contract")
        observed = normalized[0]
        if self.debug_sha256 == observed:
            return AndroidSigningState.DEBUG_SIGNED, AndroidSigningRole.DEBUG
        if self.test_sha256 == observed:
            return AndroidSigningState.TEST_SIGNED, AndroidSigningRole.TEST
        if self.upload_sha256 == observed:
            if self.app_signing_sha256 is not None:
                return AndroidSigningState.PLAY_APP_SIGNING_READY, AndroidSigningRole.UPLOAD
            return AndroidSigningState.UPLOAD_SIGNED, AndroidSigningRole.UPLOAD
        if self.app_signing_sha256 == observed:
            if self.upload_sha256 is None:
                raise ValueError("Play app-signing evidence requires a distinct upload-key fingerprint")
            return AndroidSigningState.PLAY_APP_SIGNING_READY, AndroidSigningRole.APP_SIGNING
        raise ValueError("unexpected signing certificate fingerprint")


@dataclass(frozen=True)
class AndroidSigningInspection:
    kind: AndroidArtifactKind
    artifact_sha256: str
    state: AndroidSigningState
    role: AndroidSigningRole
    certificate_sha256: tuple[str, ...] = ()
    verifier: str | None = None
    blockers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _SHA256_RE.fullmatch(self.artifact_sha256):
            raise ValueError("artifact digest must be lowercase SHA-256")
        fingerprints = tuple(normalize_sha256_fingerprint(v) for v in self.certificate_sha256)
        object.__setattr__(self, "certificate_sha256", fingerprints)
        if self.state == AndroidSigningState.UNSIGNED and fingerprints:
            raise ValueError("unsigned evidence cannot contain certificate fingerprints")
        if self.state == AndroidSigningState.SIGNING_UNAVAILABLE and not self.blockers:
            raise ValueError("unavailable signing evidence requires a blocker")
        if self.state not in {
            AndroidSigningState.UNSIGNED,
            AndroidSigningState.SIGNING_UNAVAILABLE,
        } and not fingerprints:
            raise ValueError("signed evidence requires a public certificate fingerprint")

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "artifact_sha256": self.artifact_sha256,
            "state": self.state.value,
            "role": self.role.value,
            "certificate_sha256": list(self.certificate_sha256),
            "verifier": self.verifier,
            "blockers": list(self.blockers),
        }


@dataclass(frozen=True)
class AndroidUploadKeyRotation:
    previous_upload_sha256: str
    replacement_upload_sha256: str
    app_signing_sha256: str
    reason: str
    recovery_sequence: int

    def __post_init__(self) -> None:
        previous = normalize_sha256_fingerprint(self.previous_upload_sha256)
        replacement = normalize_sha256_fingerprint(self.replacement_upload_sha256)
        app = normalize_sha256_fingerprint(self.app_signing_sha256)
        object.__setattr__(self, "previous_upload_sha256", previous)
        object.__setattr__(self, "replacement_upload_sha256", replacement)
        object.__setattr__(self, "app_signing_sha256", app)
        if previous == replacement:
            raise ValueError("upload-key recovery must change the upload certificate")
        if app in {previous, replacement}:
            raise ValueError("Play app-signing key must remain distinct from upload keys")
        if not self.reason.strip():
            raise ValueError("rotation/recovery reason is required")
        if self.recovery_sequence < 1:
            raise ValueError("recovery sequence must be positive")

    def to_dict(self) -> dict[str, object]:
        return {
            "previous_upload_sha256": self.previous_upload_sha256,
            "replacement_upload_sha256": self.replacement_upload_sha256,
            "app_signing_sha256": self.app_signing_sha256,
            "reason": self.reason,
            "recovery_sequence": self.recovery_sequence,
        }


@dataclass(frozen=True)
class AndroidSigningAcceptanceEvidence:
    schema_version: int
    source_sha: str
    runner_os: str
    inspections: tuple[AndroidSigningInspection, ...]
    secret_refs: AndroidSigningSecretRefs
    status: str = "pass"

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("R13.5 signing evidence schema version must be 1")
        if not re.fullmatch(r"[0-9a-f]{40}", self.source_sha):
            raise ValueError("source SHA must be exact lowercase 40-hex Git SHA")
        if self.runner_os not in {"Linux", "Windows"}:
            raise ValueError("R13.5 hosted acceptance runner must be Linux or Windows")
        if self.status != "pass":
            raise ValueError("this evidence type represents accepted signing evidence only")
        states = {item.state for item in self.inspections}
        kinds = {item.kind for item in self.inspections if item.state == AndroidSigningState.TEST_SIGNED}
        if AndroidSigningState.UNSIGNED not in states:
            raise ValueError("R13.5 pass requires truthful unsigned evidence")
        if kinds != {AndroidArtifactKind.APK, AndroidArtifactKind.AAB}:
            raise ValueError("R13.5 pass requires test-signed APK and AAB evidence")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "source_sha": self.source_sha,
            "runner_os": self.runner_os,
            "status": self.status,
            "inspections": [item.to_dict() for item in self.inspections],
            "secret_refs": self.secret_refs.to_dict(),
        }

    def canonical_bytes(self, *, known_secret_values: Sequence[str] = ()) -> bytes:
        payload = self.to_dict()
        assert_secret_refs_only(payload, self.secret_refs.refs(), known_secret_values)
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _zip_has_jar_signature(path: Path) -> bool:
    with zipfile.ZipFile(path) as archive:
        names = {name.upper() for name in archive.namelist()}
    sf = any(name.startswith("META-INF/") and name.endswith(".SF") for name in names)
    block = any(
        name.startswith("META-INF/") and name.endswith((".RSA", ".DSA", ".EC"))
        for name in names
    )
    return sf and block


def _apk_has_signature_material(path: Path) -> bool:
    if _zip_has_jar_signature(path):
        return True
    size = path.stat().st_size
    with path.open("rb") as stream:
        stream.seek(max(0, size - 1024 * 1024))
        tail = stream.read()
    return _APK_SIG_BLOCK_MAGIC in tail


def certificate_fingerprints_from_pem(raw: bytes) -> tuple[str, ...]:
    fingerprints: list[str] = []
    for match in _PEM_RE.finditer(raw):
        compact = re.sub(rb"\s+", b"", match.group(1))
        try:
            der = base64.b64decode(compact, validate=True)
        except ValueError as exc:
            raise ValueError("verifier returned malformed PEM certificate") from exc
        fingerprints.append(hashlib.sha256(der).hexdigest())
    return tuple(dict.fromkeys(fingerprints))


def bounded_signing_environment(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    allowed = {
        key: value
        for key, value in os.environ.items()
        if key in {"PATH", "JAVA_HOME", "ANDROID_HOME", "ANDROID_SDK_ROOT", "SYSTEMROOT", "WINDIR"}
    }
    if extra:
        allowed.update(extra)
    return allowed


def inspect_android_signing(
    path: Path,
    kind: AndroidArtifactKind,
    identity: AndroidSigningIdentity,
    *,
    apksigner: str = "apksigner",
    jarsigner: str = "jarsigner",
    keytool: str = "keytool",
    timeout_seconds: int = 60,
) -> AndroidSigningInspection:
    artifact_sha256 = _sha256_path(path)
    has_material = (
        _apk_has_signature_material(path)
        if kind == AndroidArtifactKind.APK
        else _zip_has_jar_signature(path)
    )
    if not has_material:
        return AndroidSigningInspection(
            kind=kind,
            artifact_sha256=artifact_sha256,
            state=AndroidSigningState.UNSIGNED,
            role=AndroidSigningRole.NONE,
        )

    required = (apksigner,) if kind == AndroidArtifactKind.APK else (jarsigner, keytool)
    missing = tuple(
        tool
        for tool in required
        if not Path(tool).is_file() and shutil.which(tool) is None
    )
    if missing:
        return AndroidSigningInspection(
            kind=kind,
            artifact_sha256=artifact_sha256,
            state=AndroidSigningState.SIGNING_UNAVAILABLE,
            role=AndroidSigningRole.NONE,
            blockers=tuple(f"required verifier unavailable: {Path(tool).name}" for tool in missing),
        )

    env = bounded_signing_environment()
    if kind == AndroidArtifactKind.APK:
        completed = subprocess.run(
            [apksigner, "verify", "--print-certs-pem", str(path)],
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
            env=env,
        )
        if completed.returncode != 0:
            raise ValueError("APK signature verification failed")
        fingerprints = certificate_fingerprints_from_pem(completed.stdout)
        verifier = "apksigner"
    else:
        verified = subprocess.run(
            [jarsigner, "-verify", str(path)],
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
            env=env,
        )
        combined = (verified.stdout + b"\n" + verified.stderr).lower()
        if verified.returncode != 0 or b"jar is unsigned" in combined:
            raise ValueError("AAB JAR signature verification failed")
        certs = subprocess.run(
            [keytool, "-printcert", "-rfc", "-jarfile", str(path)],
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
            env=env,
        )
        if certs.returncode != 0:
            raise ValueError("AAB signer certificate extraction failed")
        fingerprints = certificate_fingerprints_from_pem(certs.stdout)
        verifier = "jarsigner+keytool"

    if not fingerprints:
        raise ValueError("verified signed artifact did not expose a signing certificate")
    state, role = identity.classify(fingerprints)
    return AndroidSigningInspection(
        kind=kind,
        artifact_sha256=artifact_sha256,
        state=state,
        role=role,
        certificate_sha256=fingerprints,
        verifier=verifier,
    )


def validate_signing_payload_no_leaks(
    payload: Mapping[str, object],
    refs: AndroidSigningSecretRefs,
    *,
    known_secret_values: Sequence[str],
    known_private_paths: Sequence[str] = (),
) -> None:
    assert_secret_refs_only(payload, refs.refs(), known_secret_values)
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    for private_path in known_private_paths:
        if private_path and private_path in serialized:
            raise ValueError("private signing path leaked into durable evidence")
