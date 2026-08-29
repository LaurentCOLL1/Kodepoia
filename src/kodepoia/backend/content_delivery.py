from __future__ import annotations

import hashlib
import re
import threading
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Callable, Mapping, Sequence

from .authority import AuthorityActorContext
from .contracts import BackendEnvironmentKind, canonical_sha256

_STABLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,191}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_MEDIA_TYPE_RE = re.compile(r"^[a-z0-9][a-z0-9!#$&^_.+-]{0,63}/[a-z0-9][a-z0-9!#$&^_.+-]{0,127}$")
_FORBIDDEN_EXECUTABLE_MEDIA_TYPES = frozenset(
    {
        "application/javascript",
        "application/x-dosexec",
        "application/x-executable",
        "application/x-mach-binary",
        "application/x-msdownload",
        "application/x-sharedlib",
        "application/x-shellscript",
        "text/javascript",
        "text/x-python",
        "text/x-shellscript",
    }
)
_FORBIDDEN_EXECUTABLE_SUFFIXES = (
    ".app",
    ".bat",
    ".cmd",
    ".com",
    ".dll",
    ".dylib",
    ".exe",
    ".js",
    ".mjs",
    ".msi",
    ".ps1",
    ".py",
    ".sh",
    ".so",
    ".wasm",
)


class ContentDeliveryPolicyError(ValueError):
    pass


class ContentDeliveryStateError(RuntimeError):
    pass


class ContentDeliveryAuthorizationError(PermissionError):
    pass


class ContentDeliveryCapacityError(ContentDeliveryStateError):
    pass


class ContentDeliveryIntegrityError(ContentDeliveryStateError):
    pass


class ContentSignatureState(StrEnum):
    NOT_APPLICABLE = "not_applicable"
    VERIFIED = "verified"
    UNVERIFIED = "unverified"


class ContentObjectState(StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"


class CacheDisposition(StrEnum):
    MISS = "miss"
    HIT = "hit"
    REVALIDATED = "revalidated"
    REBUILT = "rebuilt"


def _stable_id(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _STABLE_ID_RE.fullmatch(value) is None:
        raise ContentDeliveryPolicyError(f"invalid_{field}")
    return value


def _sha256(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ContentDeliveryPolicyError(f"invalid_{field}")
    return value


def _positive_int(value: int, *, field: str, maximum: int = 2**31 - 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
        raise ContentDeliveryPolicyError(f"invalid_{field}")
    return value


def _non_negative_int(value: int, *, field: str, maximum: int = 2**63 - 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
        raise ContentDeliveryPolicyError(f"invalid_{field}")
    return value


def _server_now_ms(clock_ms: Callable[[], int]) -> int:
    return _non_negative_int(clock_ms(), field="server_clock")


def _validate_payload_name(value: str) -> str:
    value = _stable_id(value, field="payload_name")
    lowered = value.lower()
    if lowered.endswith(_FORBIDDEN_EXECUTABLE_SUFFIXES):
        raise ContentDeliveryPolicyError("executable_payload_forbidden")
    return value


def _validate_media_type(value: str) -> str:
    if not isinstance(value, str):
        raise ContentDeliveryPolicyError("invalid_media_type")
    lowered = value.strip().lower()
    if lowered != value or _MEDIA_TYPE_RE.fullmatch(lowered) is None:
        raise ContentDeliveryPolicyError("invalid_media_type")
    if lowered in _FORBIDDEN_EXECUTABLE_MEDIA_TYPES:
        raise ContentDeliveryPolicyError("executable_payload_forbidden")
    return lowered


def _digest_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class ContentBundleDefinition:
    bundle_id: str
    version: int
    object_id: str
    payload_name: str
    media_type: str
    size_bytes: int
    sha256: str
    dependencies: tuple[str, ...] = ()
    signature_state: ContentSignatureState = ContentSignatureState.NOT_APPLICABLE

    def __post_init__(self) -> None:
        object.__setattr__(self, "bundle_id", _stable_id(self.bundle_id, field="bundle_id"))
        object.__setattr__(self, "version", _positive_int(self.version, field="bundle_version"))
        object.__setattr__(self, "object_id", _stable_id(self.object_id, field="object_id"))
        object.__setattr__(self, "payload_name", _validate_payload_name(self.payload_name))
        object.__setattr__(self, "media_type", _validate_media_type(self.media_type))
        object.__setattr__(self, "size_bytes", _positive_int(self.size_bytes, field="size_bytes", maximum=2**40))
        object.__setattr__(self, "sha256", _sha256(self.sha256, field="sha256"))
        if not isinstance(self.signature_state, ContentSignatureState):
            raise ContentDeliveryPolicyError("invalid_signature_state")
        dependencies = tuple(sorted({_stable_id(item, field="dependency_bundle_id") for item in self.dependencies}))
        if self.bundle_id in dependencies:
            raise ContentDeliveryPolicyError("self_dependency")
        object.__setattr__(self, "dependencies", dependencies)

    @property
    def etag(self) -> str:
        return f'"sha256-{self.sha256}"'

    def canonical(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "version": self.version,
            "object_id": self.object_id,
            "payload_name": self.payload_name,
            "media_type": self.media_type,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "dependencies": list(self.dependencies),
            "signature_state": self.signature_state.value,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class ContentManifest:
    manifest_id: str
    revision: int
    environment: BackendEnvironmentKind
    bundles: tuple[ContentBundleDefinition, ...]
    min_client_version: int
    max_client_version: int
    schema_version: int
    created_at_ms: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "manifest_id", _stable_id(self.manifest_id, field="manifest_id"))
        object.__setattr__(self, "revision", _positive_int(self.revision, field="manifest_revision"))
        if not isinstance(self.environment, BackendEnvironmentKind):
            raise ContentDeliveryPolicyError("invalid_environment")
        if not isinstance(self.bundles, tuple) or not self.bundles:
            raise ContentDeliveryPolicyError("manifest_bundles_required")
        if any(not isinstance(item, ContentBundleDefinition) for item in self.bundles):
            raise ContentDeliveryPolicyError("invalid_manifest_bundle")
        bundle_ids = [item.bundle_id for item in self.bundles]
        if len(bundle_ids) != len(set(bundle_ids)):
            raise ContentDeliveryPolicyError("duplicate_bundle_id")
        object.__setattr__(self, "bundles", tuple(sorted(self.bundles, key=lambda item: item.bundle_id)))
        minimum = _positive_int(self.min_client_version, field="min_client_version")
        maximum = _positive_int(self.max_client_version, field="max_client_version")
        if minimum > maximum:
            raise ContentDeliveryPolicyError("invalid_client_version_range")
        object.__setattr__(self, "schema_version", _positive_int(self.schema_version, field="schema_version"))
        object.__setattr__(self, "created_at_ms", _non_negative_int(self.created_at_ms, field="created_at_ms"))

    def canonical(self) -> dict[str, Any]:
        return {
            "manifest_id": self.manifest_id,
            "revision": self.revision,
            "environment": self.environment.value,
            "bundles": [item.canonical() for item in self.bundles],
            "min_client_version": self.min_client_version,
            "max_client_version": self.max_client_version,
            "schema_version": self.schema_version,
            "created_at_ms": self.created_at_ms,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())

    def bundle(self, bundle_id: str) -> ContentBundleDefinition:
        bundle_id = _stable_id(bundle_id, field="bundle_id")
        for item in self.bundles:
            if item.bundle_id == bundle_id:
                return item
        raise ContentDeliveryStateError("bundle_not_found")

    def compatible_with(self, *, client_version: int, schema_version: int) -> bool:
        client_version = _positive_int(client_version, field="client_version")
        schema_version = _positive_int(schema_version, field="schema_version")
        return self.min_client_version <= client_version <= self.max_client_version and schema_version == self.schema_version


@dataclass(frozen=True, slots=True)
class ChannelPointer:
    channel_id: str
    environment: BackendEnvironmentKind
    manifest_id: str
    manifest_digest: str
    revision: int
    promoted_at_ms: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "channel_id", _stable_id(self.channel_id, field="channel_id"))
        if not isinstance(self.environment, BackendEnvironmentKind):
            raise ContentDeliveryPolicyError("invalid_environment")
        object.__setattr__(self, "manifest_id", _stable_id(self.manifest_id, field="manifest_id"))
        object.__setattr__(self, "manifest_digest", _sha256(self.manifest_digest, field="manifest_digest"))
        object.__setattr__(self, "revision", _positive_int(self.revision, field="channel_revision"))
        object.__setattr__(self, "promoted_at_ms", _non_negative_int(self.promoted_at_ms, field="promoted_at_ms"))

    def canonical(self) -> dict[str, Any]:
        return {
            "channel_id": self.channel_id,
            "environment": self.environment.value,
            "manifest_id": self.manifest_id,
            "manifest_digest": self.manifest_digest,
            "revision": self.revision,
            "promoted_at_ms": self.promoted_at_ms,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class ContentFetchResponse:
    object_id: str
    etag: str
    total_size: int
    start: int
    end_exclusive: int
    payload: bytes

    @property
    def is_partial(self) -> bool:
        return self.start != 0 or self.end_exclusive != self.total_size


class LocalContentProvider:
    def __init__(self, *, max_object_bytes: int = 64 * 1024 * 1024, max_objects: int = 4096) -> None:
        self.max_object_bytes = _positive_int(max_object_bytes, field="max_object_bytes", maximum=2**40)
        self.max_objects = _positive_int(max_objects, field="max_objects", maximum=1_000_000)
        self._objects: dict[str, bytes] = {}
        self._lock = threading.RLock()

    def put(self, object_id: str, payload: bytes) -> str:
        object_id = _stable_id(object_id, field="object_id")
        if not isinstance(payload, bytes) or not payload:
            raise ContentDeliveryPolicyError("payload_bytes_required")
        if len(payload) > self.max_object_bytes:
            raise ContentDeliveryCapacityError("object_bytes_capacity")
        with self._lock:
            existing = self._objects.get(object_id)
            if existing is not None:
                if existing != payload:
                    raise ContentDeliveryStateError("object_id_conflict")
                return _digest_bytes(existing)
            if len(self._objects) >= self.max_objects:
                raise ContentDeliveryCapacityError("object_capacity")
            self._objects[object_id] = bytes(payload)
        return _digest_bytes(payload)

    def fetch(
        self,
        object_id: str,
        *,
        if_none_match: str | None = None,
        start: int = 0,
        end_exclusive: int | None = None,
        if_range: str | None = None,
    ) -> ContentFetchResponse | None:
        object_id = _stable_id(object_id, field="object_id")
        try:
            payload = self._objects[object_id]
        except KeyError as exc:
            raise ContentDeliveryStateError("object_not_found") from exc
        digest = _digest_bytes(payload)
        etag = f'"sha256-{digest}"'
        if if_none_match is not None and if_none_match == etag and start == 0 and end_exclusive is None:
            return None
        if isinstance(start, bool) or not isinstance(start, int) or start < 0:
            raise ContentDeliveryPolicyError("invalid_range_start")
        requested_end = len(payload) if end_exclusive is None else end_exclusive
        if isinstance(requested_end, bool) or not isinstance(requested_end, int) or requested_end < start:
            raise ContentDeliveryPolicyError("invalid_range_end")
        if start > len(payload):
            raise ContentDeliveryPolicyError("range_not_satisfiable")
        requested_end = min(requested_end, len(payload))
        if if_range is not None and if_range != etag:
            start = 0
            requested_end = len(payload)
        return ContentFetchResponse(
            object_id=object_id,
            etag=etag,
            total_size=len(payload),
            start=start,
            end_exclusive=requested_end,
            payload=payload[start:requested_end],
        )

    def tamper_for_test(self, object_id: str, payload: bytes) -> None:
        object_id = _stable_id(object_id, field="object_id")
        if not isinstance(payload, bytes):
            raise ContentDeliveryPolicyError("payload_bytes_required")
        if object_id not in self._objects:
            raise ContentDeliveryStateError("object_not_found")
        self._objects[object_id] = bytes(payload)


@dataclass(frozen=True, slots=True)
class CacheEntry:
    bundle_id: str
    manifest_digest: str
    etag: str
    payload: bytes

    def digest(self) -> str:
        return _digest_bytes(self.payload)


class VerifiedContentCache:
    def __init__(self, *, max_entries: int = 1024, max_bytes: int = 256 * 1024 * 1024) -> None:
        self.max_entries = _positive_int(max_entries, field="max_cache_entries", maximum=1_000_000)
        self.max_bytes = _positive_int(max_bytes, field="max_cache_bytes", maximum=2**40)
        self._entries: dict[tuple[str, str], CacheEntry] = {}
        self._lock = threading.RLock()

    @property
    def bytes_used(self) -> int:
        return sum(len(item.payload) for item in self._entries.values())

    def entry(self, manifest_digest: str, bundle_id: str) -> CacheEntry | None:
        return self._entries.get((_sha256(manifest_digest, field="manifest_digest"), _stable_id(bundle_id, field="bundle_id")))

    def purge(self, manifest_digest: str, bundle_id: str) -> None:
        self._entries.pop((_sha256(manifest_digest, field="manifest_digest"), _stable_id(bundle_id, field="bundle_id")), None)

    def promote(self, entry: CacheEntry) -> CacheEntry:
        key = (_sha256(entry.manifest_digest, field="manifest_digest"), _stable_id(entry.bundle_id, field="bundle_id"))
        if not isinstance(entry.payload, bytes) or not entry.payload:
            raise ContentDeliveryPolicyError("cache_payload_required")
        with self._lock:
            existing = self._entries.get(key)
            if existing == entry:
                return existing
            projected_entries = len(self._entries) + (0 if existing is not None else 1)
            projected_bytes = self.bytes_used - (len(existing.payload) if existing is not None else 0) + len(entry.payload)
            if projected_entries > self.max_entries:
                raise ContentDeliveryCapacityError("cache_entry_capacity")
            if projected_bytes > self.max_bytes:
                raise ContentDeliveryCapacityError("cache_byte_capacity")
            self._entries[key] = entry
            return entry

    def corrupt_for_test(self, manifest_digest: str, bundle_id: str, payload: bytes) -> None:
        current = self.entry(manifest_digest, bundle_id)
        if current is None:
            raise ContentDeliveryStateError("cache_entry_not_found")
        self._entries[(manifest_digest, bundle_id)] = CacheEntry(
            bundle_id=current.bundle_id,
            manifest_digest=current.manifest_digest,
            etag=current.etag,
            payload=bytes(payload),
        )


@dataclass(frozen=True, slots=True)
class DownloadResult:
    manifest_id: str
    bundle_id: str
    manifest_digest: str
    bundle_digest: str
    payload_sha256: str
    size_bytes: int
    etag: str
    disposition: CacheDisposition

    def canonical(self) -> dict[str, Any]:
        return {
            "manifest_id": self.manifest_id,
            "bundle_id": self.bundle_id,
            "manifest_digest": self.manifest_digest,
            "bundle_digest": self.bundle_digest,
            "payload_sha256": self.payload_sha256,
            "size_bytes": self.size_bytes,
            "etag": self.etag,
            "disposition": self.disposition.value,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class ContentDeliveryStateSnapshot:
    manifest_digests: tuple[str, ...]
    channel_digests: tuple[str, ...]
    revoked_manifests: tuple[str, ...]
    trace_digest: str
    cache_bytes: int

    def canonical(self) -> dict[str, Any]:
        return {
            "manifest_digests": list(self.manifest_digests),
            "channel_digests": list(self.channel_digests),
            "revoked_manifests": list(self.revoked_manifests),
            "trace_digest": self.trace_digest,
            "cache_bytes": self.cache_bytes,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


class InMemoryContentDeliveryService:
    def __init__(
        self,
        *,
        clock_ms: Callable[[], int],
        provider: LocalContentProvider,
        cache: VerifiedContentCache,
        max_manifests: int = 512,
        max_bundles_per_manifest: int = 512,
        max_channels: int = 64,
        max_trace_records: int = 100_000,
    ) -> None:
        self.clock_ms = clock_ms
        self.provider = provider
        self.cache = cache
        self.max_manifests = _positive_int(max_manifests, field="max_manifests")
        self.max_bundles_per_manifest = _positive_int(max_bundles_per_manifest, field="max_bundles_per_manifest")
        self.max_channels = _positive_int(max_channels, field="max_channels")
        self.max_trace_records = _positive_int(max_trace_records, field="max_trace_records")
        self._manifests: dict[tuple[BackendEnvironmentKind, str], ContentManifest] = {}
        self._channels: dict[tuple[BackendEnvironmentKind, str], ChannelPointer] = {}
        self._channel_history: dict[tuple[BackendEnvironmentKind, str], list[ChannelPointer]] = {}
        self._revoked: set[tuple[BackendEnvironmentKind, str]] = set()
        self._trace: list[dict[str, Any]] = []
        self._lock = threading.RLock()

    @staticmethod
    def _authorize(actor: AuthorityActorContext, permission: str, target_id: str) -> None:
        if not actor.can(permission, target_id):
            raise ContentDeliveryAuthorizationError("forbidden")

    def _append_trace(self, event: Mapping[str, Any]) -> None:
        if len(self._trace) >= self.max_trace_records:
            raise ContentDeliveryCapacityError("trace_capacity")
        self._trace.append(dict(event))

    def _validate_graph(self, manifest: ContentManifest) -> None:
        if len(manifest.bundles) > self.max_bundles_per_manifest:
            raise ContentDeliveryCapacityError("bundles_per_manifest_capacity")
        by_id = {item.bundle_id: item for item in manifest.bundles}
        for bundle in manifest.bundles:
            for dependency in bundle.dependencies:
                if dependency not in by_id:
                    raise ContentDeliveryPolicyError("dependency_not_found")
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(bundle_id: str) -> None:
            if bundle_id in visiting:
                raise ContentDeliveryPolicyError("dependency_cycle")
            if bundle_id in visited:
                return
            visiting.add(bundle_id)
            for dependency in by_id[bundle_id].dependencies:
                visit(dependency)
            visiting.remove(bundle_id)
            visited.add(bundle_id)

        for bundle_id in sorted(by_id):
            visit(bundle_id)

    def register_manifest(self, actor: AuthorityActorContext, manifest: ContentManifest) -> ContentManifest:
        self._authorize(actor, "content.manifest.register", manifest.manifest_id)
        self._validate_graph(manifest)
        key = (manifest.environment, manifest.manifest_id)
        with self._lock:
            existing = self._manifests.get(key)
            if existing is not None:
                if existing != manifest:
                    raise ContentDeliveryStateError("manifest_id_conflict")
                return existing
            if len(self._manifests) >= self.max_manifests:
                raise ContentDeliveryCapacityError("manifest_capacity")
            for (environment, _manifest_id), other in self._manifests.items():
                if environment is manifest.environment and other.revision == manifest.revision and other.digest() != manifest.digest():
                    raise ContentDeliveryStateError("manifest_revision_conflict")
            self._manifests[key] = manifest
            self._append_trace(
                {
                    "event": "manifest_registered",
                    "environment": manifest.environment.value,
                    "manifest_id": manifest.manifest_id,
                    "manifest_digest": manifest.digest(),
                }
            )
            return manifest

    def manifest(self, environment: BackendEnvironmentKind, manifest_id: str) -> ContentManifest:
        if not isinstance(environment, BackendEnvironmentKind):
            raise ContentDeliveryPolicyError("invalid_environment")
        manifest_id = _stable_id(manifest_id, field="manifest_id")
        try:
            return self._manifests[(environment, manifest_id)]
        except KeyError as exc:
            raise ContentDeliveryStateError("manifest_not_found") from exc

    def verify_provider_objects(self, manifest: ContentManifest) -> None:
        self._validate_graph(manifest)
        for bundle in manifest.bundles:
            response = self.provider.fetch(bundle.object_id)
            if response is None:
                raise ContentDeliveryIntegrityError("provider_object_missing")
            if response.total_size != bundle.size_bytes or len(response.payload) != bundle.size_bytes:
                raise ContentDeliveryIntegrityError("bundle_size_mismatch")
            if _digest_bytes(response.payload) != bundle.sha256:
                raise ContentDeliveryIntegrityError("bundle_hash_mismatch")
            if response.etag != bundle.etag:
                raise ContentDeliveryIntegrityError("bundle_etag_mismatch")

    def promote_channel(
        self,
        actor: AuthorityActorContext,
        *,
        environment: BackendEnvironmentKind,
        channel_id: str,
        manifest_id: str,
        expected_current_manifest_id: str | None = None,
    ) -> ChannelPointer:
        if not isinstance(environment, BackendEnvironmentKind):
            raise ContentDeliveryPolicyError("invalid_environment")
        channel_id = _stable_id(channel_id, field="channel_id")
        manifest_id = _stable_id(manifest_id, field="manifest_id")
        self._authorize(actor, "content.channel.promote", channel_id)
        target = self.manifest(environment, manifest_id)
        if (environment, manifest_id) in self._revoked:
            raise ContentDeliveryStateError("manifest_revoked")
        self.verify_provider_objects(target)
        key = (environment, channel_id)
        with self._lock:
            current = self._channels.get(key)
            if expected_current_manifest_id is not None:
                expected_current_manifest_id = _stable_id(expected_current_manifest_id, field="expected_current_manifest_id")
                if current is None or current.manifest_id != expected_current_manifest_id:
                    raise ContentDeliveryStateError("stale_channel_pointer")
            if current is not None and current.manifest_id == manifest_id and current.manifest_digest == target.digest():
                return current
            if current is None and len(self._channels) >= self.max_channels:
                raise ContentDeliveryCapacityError("channel_capacity")
            pointer = ChannelPointer(
                channel_id=channel_id,
                environment=environment,
                manifest_id=target.manifest_id,
                manifest_digest=target.digest(),
                revision=1 if current is None else current.revision + 1,
                promoted_at_ms=_server_now_ms(self.clock_ms),
            )
            self._channels[key] = pointer
            self._channel_history.setdefault(key, []).append(pointer)
            self._append_trace(
                {
                    "event": "channel_promoted",
                    "environment": environment.value,
                    "channel_id": channel_id,
                    "manifest_id": manifest_id,
                    "manifest_digest": target.digest(),
                    "channel_revision": pointer.revision,
                }
            )
            return pointer

    def channel(self, environment: BackendEnvironmentKind, channel_id: str) -> ChannelPointer:
        if not isinstance(environment, BackendEnvironmentKind):
            raise ContentDeliveryPolicyError("invalid_environment")
        channel_id = _stable_id(channel_id, field="channel_id")
        try:
            return self._channels[(environment, channel_id)]
        except KeyError as exc:
            raise ContentDeliveryStateError("channel_not_found") from exc

    def rollback_channel(
        self,
        actor: AuthorityActorContext,
        *,
        environment: BackendEnvironmentKind,
        channel_id: str,
        to_manifest_id: str,
    ) -> ChannelPointer:
        channel_id = _stable_id(channel_id, field="channel_id")
        to_manifest_id = _stable_id(to_manifest_id, field="manifest_id")
        self._authorize(actor, "content.channel.rollback", channel_id)
        key = (environment, channel_id)
        history = self._channel_history.get(key, [])
        if not any(item.manifest_id == to_manifest_id for item in history):
            raise ContentDeliveryStateError("rollback_target_not_in_history")
        current = self.channel(environment, channel_id)
        return self.promote_channel(
            actor,
            environment=environment,
            channel_id=channel_id,
            manifest_id=to_manifest_id,
            expected_current_manifest_id=current.manifest_id,
        )

    def revoke_manifest(
        self,
        actor: AuthorityActorContext,
        *,
        environment: BackendEnvironmentKind,
        manifest_id: str,
    ) -> None:
        manifest_id = _stable_id(manifest_id, field="manifest_id")
        self._authorize(actor, "content.manifest.revoke", manifest_id)
        self.manifest(environment, manifest_id)
        for (env, _channel_id), pointer in self._channels.items():
            if env is environment and pointer.manifest_id == manifest_id:
                raise ContentDeliveryStateError("cannot_revoke_active_manifest")
        self._revoked.add((environment, manifest_id))
        self._append_trace(
            {
                "event": "manifest_revoked",
                "environment": environment.value,
                "manifest_id": manifest_id,
            }
        )

    def resolve_channel(
        self,
        *,
        environment: BackendEnvironmentKind,
        channel_id: str,
        client_version: int,
        schema_version: int,
    ) -> ContentManifest:
        pointer = self.channel(environment, channel_id)
        manifest = self.manifest(environment, pointer.manifest_id)
        if (environment, manifest.manifest_id) in self._revoked:
            raise ContentDeliveryStateError("manifest_revoked")
        if not manifest.compatible_with(client_version=client_version, schema_version=schema_version):
            raise ContentDeliveryPolicyError("client_manifest_incompatible")
        return manifest

    def fetch_bundle(
        self,
        *,
        environment: BackendEnvironmentKind,
        channel_id: str,
        bundle_id: str,
        client_version: int,
        schema_version: int,
    ) -> DownloadResult:
        manifest = self.resolve_channel(
            environment=environment,
            channel_id=channel_id,
            client_version=client_version,
            schema_version=schema_version,
        )
        bundle = manifest.bundle(bundle_id)
        manifest_digest = manifest.digest()
        current = self.cache.entry(manifest_digest, bundle.bundle_id)
        disposition = CacheDisposition.MISS
        if current is not None:
            if len(current.payload) == bundle.size_bytes and current.digest() == bundle.sha256 and current.etag == bundle.etag:
                response = self.provider.fetch(bundle.object_id, if_none_match=current.etag)
                if response is None:
                    disposition = CacheDisposition.HIT
                    payload = current.payload
                else:
                    payload = response.payload
                    disposition = CacheDisposition.REVALIDATED
            else:
                self.cache.purge(manifest_digest, bundle.bundle_id)
                current = None
                disposition = CacheDisposition.REBUILT
        if current is None:
            response = self.provider.fetch(bundle.object_id)
            if response is None:
                raise ContentDeliveryIntegrityError("unexpected_not_modified")
            payload = response.payload
        if len(payload) != bundle.size_bytes:
            raise ContentDeliveryIntegrityError("bundle_size_mismatch")
        payload_digest = _digest_bytes(payload)
        if payload_digest != bundle.sha256:
            raise ContentDeliveryIntegrityError("bundle_hash_mismatch")
        entry = CacheEntry(
            bundle_id=bundle.bundle_id,
            manifest_digest=manifest_digest,
            etag=bundle.etag,
            payload=bytes(payload),
        )
        self.cache.promote(entry)
        self._append_trace(
            {
                "event": "bundle_fetched",
                "environment": environment.value,
                "channel_id": channel_id,
                "manifest_id": manifest.manifest_id,
                "bundle_id": bundle.bundle_id,
                "bundle_sha256": bundle.sha256,
                "disposition": disposition.value,
            }
        )
        return DownloadResult(
            manifest_id=manifest.manifest_id,
            bundle_id=bundle.bundle_id,
            manifest_digest=manifest_digest,
            bundle_digest=bundle.digest(),
            payload_sha256=payload_digest,
            size_bytes=len(payload),
            etag=bundle.etag,
            disposition=disposition,
        )

    def fetch_bundle_range(
        self,
        *,
        environment: BackendEnvironmentKind,
        channel_id: str,
        bundle_id: str,
        client_version: int,
        schema_version: int,
        start: int,
        end_exclusive: int,
        if_range: str | None = None,
    ) -> ContentFetchResponse:
        manifest = self.resolve_channel(
            environment=environment,
            channel_id=channel_id,
            client_version=client_version,
            schema_version=schema_version,
        )
        bundle = manifest.bundle(bundle_id)
        response = self.provider.fetch(
            bundle.object_id,
            start=start,
            end_exclusive=end_exclusive,
            if_range=if_range,
        )
        if response is None:
            raise ContentDeliveryIntegrityError("unexpected_not_modified")
        if response.total_size != bundle.size_bytes or response.etag != bundle.etag:
            raise ContentDeliveryIntegrityError("range_representation_mismatch")
        return response

    def state_snapshot(self) -> ContentDeliveryStateSnapshot:
        manifest_digests = tuple(sorted(item.digest() for item in self._manifests.values()))
        channel_digests = tuple(sorted(item.digest() for item in self._channels.values()))
        revoked = tuple(sorted(f"{env.value}:{manifest_id}" for env, manifest_id in self._revoked))
        return ContentDeliveryStateSnapshot(
            manifest_digests=manifest_digests,
            channel_digests=channel_digests,
            revoked_manifests=revoked,
            trace_digest=canonical_sha256(self._trace),
            cache_bytes=self.cache.bytes_used,
        )

    def redacted_evidence(self) -> dict[str, Any]:
        return {
            "state": self.state_snapshot().canonical(),
            "trace_digest": canonical_sha256(self._trace),
            "provider_kind": "local_deterministic",
            "provider_live_claim": False,
            "secrets_exposed": False,
            "raw_urls_exposed": False,
            "executable_content_allowed": False,
        }
