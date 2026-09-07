from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from kodepoia.update.trust import UpdateTargetSpec

REPOSITORY_CONTRACT_FORMAT = "kodepoia-update-repository-bootstrap"
REPOSITORY_CONTRACT_SCHEMA_VERSION = 1
CANONICAL_METADATA_BASE_URL = (
    "https://raw.githubusercontent.com/LaurentCOLL1/Kodepoia/main/update-repository/metadata/"
)
GITHUB_RELEASE_BASE_URL = "https://github.com/LaurentCOLL1/Kodepoia/releases/download/"
TOP_LEVEL_TUF_ROLES = ("root", "targets", "snapshot", "timestamp")
PRODUCTION_ROOT_RESOURCE = "trusted_root.production.json"
SYNTHETIC_ROOT_RESOURCE = "trusted_root.synthetic.json"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REQUIRED_CUSTOM_FIELDS = (
    "source_sha",
    "channel",
    "public_version",
    "release_notes_summary",
    "signing_status",
    "provenance_status",
    "withdrawn",
    "payload_url",
)
_PRIVATE_KEY_MARKERS = (
    b"-----BEGIN " + b"PRIVATE KEY-----",
    b"-----BEGIN " + b"ENCRYPTED PRIVATE KEY-----",
    b"-----BEGIN " + b"OPENSSH PRIVATE KEY-----",
    b"-----BEGIN " + b"RSA PRIVATE KEY-----",
    b"-----BEGIN " + b"EC PRIVATE KEY-----",
)


class UpdateRepositoryBootstrapError(ValueError):
    """Raised when the R19.2 public update repository contract is unsafe or invalid."""


def _require_https_base_url(value: str, *, label: str) -> str:
    text = value.strip()
    parsed = urlsplit(text)
    if parsed.scheme != "https" or not parsed.hostname:
        raise UpdateRepositoryBootstrapError(f"{label} must use an absolute HTTPS URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise UpdateRepositoryBootstrapError(f"{label} must not contain credentials, query, or fragment")
    if not parsed.path.endswith("/"):
        raise UpdateRepositoryBootstrapError(f"{label} must end with '/'")
    return text


def _canonical_json_bytes(payload: dict[str, object]) -> bytes:
    rendered = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return (rendered + "\n").encode("utf-8")


@dataclass(frozen=True, slots=True)
class TufRolePolicy:
    role: str
    threshold: int
    key_storage: str
    expires_after_days: int
    rotate_after_days: int

    def __post_init__(self) -> None:
        role = self.role.strip().lower()
        storage = self.key_storage.strip().lower()
        if role not in TOP_LEVEL_TUF_ROLES:
            raise UpdateRepositoryBootstrapError(f"unsupported top-level TUF role: {role}")
        if self.threshold < 1:
            raise UpdateRepositoryBootstrapError("TUF role threshold must be positive")
        if storage not in {"offline", "online"}:
            raise UpdateRepositoryBootstrapError("TUF key storage must be 'offline' or 'online'")
        if self.expires_after_days < 1 or self.rotate_after_days < 1:
            raise UpdateRepositoryBootstrapError("TUF expiry and rotation intervals must be positive")
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "key_storage", storage)

    def to_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "threshold": self.threshold,
            "key_storage": self.key_storage,
            "expires_after_days": self.expires_after_days,
            "rotate_after_days": self.rotate_after_days,
        }


@dataclass(frozen=True, slots=True)
class UpdateRepositoryContract:
    metadata_base_url: str
    release_asset_base_url: str
    role_policies: tuple[TufRolePolicy, ...]
    consistent_snapshot: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "metadata_base_url",
            _require_https_base_url(self.metadata_base_url, label="metadata base URL"),
        )
        object.__setattr__(
            self,
            "release_asset_base_url",
            _require_https_base_url(self.release_asset_base_url, label="release asset base URL"),
        )
        roles = tuple(policy.role for policy in self.role_policies)
        if roles != TOP_LEVEL_TUF_ROLES:
            raise UpdateRepositoryBootstrapError(
                "role policies must define root, targets, snapshot, and timestamp exactly once"
            )

    @property
    def metadata_files(self) -> dict[str, str]:
        return {role: f"{role}.json" for role in TOP_LEVEL_TUF_ROLES}

    def to_dict(self) -> dict[str, object]:
        return {
            "format": REPOSITORY_CONTRACT_FORMAT,
            "schema_version": REPOSITORY_CONTRACT_SCHEMA_VERSION,
            "metadata_base_url": self.metadata_base_url,
            "release_asset_base_url": self.release_asset_base_url,
            "metadata_files": self.metadata_files,
            "consistent_snapshot": self.consistent_snapshot,
            "roles": [policy.to_dict() for policy in self.role_policies],
            "target_path_template": (
                "channels/{channel}/{platform}/{public_version}/{source_sha}/{filename}"
            ),
            "release_tag_template": "v{public_version}",
            "authorization_source": "tuf-targets-metadata",
            "production_root_resource": PRODUCTION_ROOT_RESOURCE,
            "production_root_state": "pending-real-key-bootstrap",
            "synthetic_root_resource": SYNTHETIC_ROOT_RESOURCE,
            "synthetic_root_permitted_for_production": False,
            "private_keys_permitted_in_repository": False,
        }

    def to_bytes(self) -> bytes:
        return _canonical_json_bytes(self.to_dict())


def default_production_repository_contract() -> UpdateRepositoryContract:
    return UpdateRepositoryContract(
        metadata_base_url=CANONICAL_METADATA_BASE_URL,
        release_asset_base_url=GITHUB_RELEASE_BASE_URL,
        role_policies=(
            TufRolePolicy("root", 2, "offline", 365, 180),
            TufRolePolicy("targets", 1, "offline", 365, 180),
            TufRolePolicy("snapshot", 1, "online", 1, 90),
            TufRolePolicy("timestamp", 1, "online", 1, 30),
        ),
        consistent_snapshot=False,
    )


@dataclass(frozen=True, slots=True)
class UpdateTargetBinding:
    target_path: str
    length: int
    sha256: str
    custom: dict[str, object]

    def __post_init__(self) -> None:
        digest = self.sha256.strip().lower()
        if self.length < 1:
            raise UpdateRepositoryBootstrapError("target length must be positive")
        if not _SHA256_RE.fullmatch(digest):
            raise UpdateRepositoryBootstrapError("target SHA-256 must be lowercase hexadecimal")
        object.__setattr__(self, "sha256", digest)
        validate_target_binding(self)

    @property
    def payload_url(self) -> str:
        return str(self.custom["payload_url"])

    def to_tuf_target_dict(self) -> dict[str, object]:
        return {
            "length": self.length,
            "hashes": {"sha256": self.sha256},
            "custom": dict(self.custom),
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "target_path": self.target_path,
            **self.to_tuf_target_dict(),
        }


def _target_from_path(path: str) -> UpdateTargetSpec:
    parts = path.split("/")
    if len(parts) != 6 or parts[0] != "channels":
        raise UpdateRepositoryBootstrapError(f"invalid canonical update target path: {path!r}")
    return UpdateTargetSpec(
        channel=parts[1],
        platform=parts[2],
        public_version=parts[3],
        source_sha=parts[4],
        filename=parts[5],
    )


def validate_target_binding(binding: UpdateTargetBinding) -> None:
    target = _target_from_path(binding.target_path)
    if target.path != binding.target_path:
        raise UpdateRepositoryBootstrapError("target path is not canonical")
    missing = [name for name in _REQUIRED_CUSTOM_FIELDS if name not in binding.custom]
    if missing:
        raise UpdateRepositoryBootstrapError(f"target custom metadata is missing {missing[0]!r}")
    expected = {
        "source_sha": target.source_sha,
        "channel": target.channel,
        "public_version": target.public_version,
    }
    for key, value in expected.items():
        if binding.custom.get(key) != value:
            raise UpdateRepositoryBootstrapError(f"target custom metadata {key!r} does not match its path")
    for name in ("release_notes_summary", "signing_status", "provenance_status"):
        if not str(binding.custom.get(name, "")).strip():
            raise UpdateRepositoryBootstrapError(f"target custom metadata {name!r} must not be empty")
    if not isinstance(binding.custom.get("withdrawn"), bool):
        raise UpdateRepositoryBootstrapError("target custom metadata 'withdrawn' must be boolean")
    payload_url = str(binding.custom["payload_url"]).strip()
    expected_payload_url = (
        f"{GITHUB_RELEASE_BASE_URL}v{target.public_version}/{target.filename}"
    )
    if payload_url != expected_payload_url:
        raise UpdateRepositoryBootstrapError(
            "target payload URL does not match the canonical GitHub Release asset URL"
        )


def build_target_binding(
    target: UpdateTargetSpec,
    payload: bytes,
    *,
    release_notes_summary: str,
    signing_status: str,
    provenance_status: str,
    withdrawn: bool = False,
) -> UpdateTargetBinding:
    notes = release_notes_summary.strip()
    signing = signing_status.strip()
    provenance = provenance_status.strip()
    if not notes or not signing or not provenance:
        raise UpdateRepositoryBootstrapError("release notes and status metadata must not be empty")
    contract = default_production_repository_contract()
    payload_url = (
        f"{contract.release_asset_base_url}v{target.public_version}/{target.filename}"
    )
    custom: dict[str, object] = {
        "source_sha": target.source_sha,
        "channel": target.channel,
        "public_version": target.public_version,
        "release_notes_summary": notes,
        "signing_status": signing,
        "provenance_status": provenance,
        "withdrawn": withdrawn,
        "payload_url": payload_url,
    }
    return UpdateTargetBinding(
        target_path=target.path,
        length=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
        custom=custom,
    )


def assert_repository_safe_payload(payload: bytes | str) -> None:
    data = payload.encode("utf-8") if isinstance(payload, str) else payload
    upper = data.upper()
    for marker in _PRIVATE_KEY_MARKERS:
        if marker in upper:
            raise UpdateRepositoryBootstrapError(
                "private key material is forbidden in repository-safe R19.2 payloads"
            )
