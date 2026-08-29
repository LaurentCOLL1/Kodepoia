from __future__ import annotations

from dataclasses import replace

import pytest

from kodepoia.backend.authority import AuthorityActorContext
from kodepoia.backend.content_delivery import (
    CacheDisposition,
    ContentBundleDefinition,
    ContentDeliveryAuthorizationError,
    ContentDeliveryCapacityError,
    ContentDeliveryIntegrityError,
    ContentDeliveryPolicyError,
    ContentDeliveryStateError,
    ContentManifest,
    ContentSignatureState,
    InMemoryContentDeliveryService,
    LocalContentProvider,
    VerifiedContentCache,
)
from kodepoia.backend.contracts import BackendEnvironmentKind


class Clock:
    def __init__(self, value: int = 1_000_000) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value


OBJECTS = (
    "base",
    "bundle.base",
    "bundle.extra",
    "bundle.other",
    "bundle.patch",
    "channel.stable",
    "manifest.prod",
    "manifest.test.v1",
    "manifest.test.v2",
    "manifest.test.v3",
    "production",
    "test",
)


def actor(*, permissions: tuple[str, ...] = ("*",), objects: tuple[str, ...] = OBJECTS) -> AuthorityActorContext:
    return AuthorityActorContext(
        account_id="operator",
        session_id="session-1",
        permissions=permissions,
        authorized_object_ids=objects,
    )


def bundle(
    bundle_id: str,
    payload: bytes,
    *,
    version: int = 1,
    object_id: str | None = None,
    payload_name: str | None = None,
    media_type: str = "application/octet-stream",
    dependencies: tuple[str, ...] = (),
) -> ContentBundleDefinition:
    import hashlib

    return ContentBundleDefinition(
        bundle_id=bundle_id,
        version=version,
        object_id=object_id or bundle_id,
        payload_name=payload_name or f"{bundle_id}.asset",
        media_type=media_type,
        size_bytes=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
        dependencies=dependencies,
        signature_state=ContentSignatureState.NOT_APPLICABLE,
    )


def manifest(
    manifest_id: str,
    bundles: tuple[ContentBundleDefinition, ...],
    *,
    revision: int = 1,
    environment: BackendEnvironmentKind = BackendEnvironmentKind.TEST,
    min_client_version: int = 1,
    max_client_version: int = 3,
    schema_version: int = 1,
) -> ContentManifest:
    return ContentManifest(
        manifest_id=manifest_id,
        revision=revision,
        environment=environment,
        bundles=bundles,
        min_client_version=min_client_version,
        max_client_version=max_client_version,
        schema_version=schema_version,
        created_at_ms=900_000 + revision,
    )


def service(*, max_manifests: int = 32, max_bundles_per_manifest: int = 32, max_channels: int = 8) -> tuple[InMemoryContentDeliveryService, LocalContentProvider, VerifiedContentCache, Clock]:
    clock = Clock()
    provider = LocalContentProvider(max_object_bytes=1024 * 1024, max_objects=64)
    cache = VerifiedContentCache(max_entries=64, max_bytes=4 * 1024 * 1024)
    return (
        InMemoryContentDeliveryService(
            clock_ms=clock,
            provider=provider,
            cache=cache,
            max_manifests=max_manifests,
            max_bundles_per_manifest=max_bundles_per_manifest,
            max_channels=max_channels,
            max_trace_records=256,
        ),
        provider,
        cache,
        clock,
    )


def register_payload(provider: LocalContentProvider, item: ContentBundleDefinition, payload: bytes) -> None:
    assert provider.put(item.object_id, payload) == item.sha256


def test_bundle_identity_is_immutable_and_canonical() -> None:
    payload = b"hello-content"
    item = bundle("bundle.base", payload)
    assert item.etag == f'"sha256-{item.sha256}"'
    assert item.digest() == replace(item).digest()
    assert item.canonical()["sha256"] == item.sha256


def test_executable_payload_names_and_media_types_are_rejected() -> None:
    payload = b"unsafe"
    with pytest.raises(ContentDeliveryPolicyError, match="executable_payload_forbidden"):
        bundle("bundle.base", payload, payload_name="unsafe.exe")
    with pytest.raises(ContentDeliveryPolicyError, match="executable_payload_forbidden"):
        bundle("bundle.base", payload, media_type="application/javascript")
    with pytest.raises(ContentDeliveryPolicyError, match="executable_payload_forbidden"):
        bundle("bundle.base", payload, payload_name="module.wasm")


def test_manifest_identity_conflict_is_rejected() -> None:
    svc, provider, _cache, _clock = service()
    a = bundle("bundle.base", b"a")
    b = bundle("bundle.extra", b"b")
    register_payload(provider, a, b"a")
    register_payload(provider, b, b"b")
    first = manifest("manifest.test.v1", (a,), revision=1)
    conflicting = manifest("manifest.test.v1", (b,), revision=2)
    svc.register_manifest(actor(), first)
    with pytest.raises(ContentDeliveryStateError, match="manifest_id_conflict"):
        svc.register_manifest(actor(), conflicting)


def test_manifest_revision_conflict_is_rejected() -> None:
    svc, _provider, _cache, _clock = service()
    a = bundle("bundle.base", b"a")
    b = bundle("bundle.extra", b"b")
    svc.register_manifest(actor(), manifest("manifest.test.v1", (a,), revision=1))
    with pytest.raises(ContentDeliveryStateError, match="manifest_revision_conflict"):
        svc.register_manifest(actor(), manifest("manifest.test.v2", (b,), revision=1))


def test_missing_dependency_and_cycle_fail_closed() -> None:
    svc, _provider, _cache, _clock = service()
    missing = bundle("bundle.base", b"a", dependencies=("bundle.extra",))
    with pytest.raises(ContentDeliveryPolicyError, match="dependency_not_found"):
        svc.register_manifest(actor(), manifest("manifest.test.v1", (missing,), revision=1))

    a = bundle("bundle.base", b"a", dependencies=("bundle.extra",))
    b = bundle("bundle.extra", b"b", dependencies=("bundle.base",))
    with pytest.raises(ContentDeliveryPolicyError, match="dependency_cycle"):
        svc.register_manifest(actor(), manifest("manifest.test.v2", (a, b), revision=2))


def test_tampered_provider_object_blocks_promotion() -> None:
    svc, provider, _cache, _clock = service()
    payload = b"trusted"
    item = bundle("bundle.base", payload)
    register_payload(provider, item, payload)
    m = manifest("manifest.test.v1", (item,), revision=1)
    svc.register_manifest(actor(), m)
    provider.tamper_for_test(item.object_id, b"tampered")
    with pytest.raises(ContentDeliveryIntegrityError, match="bundle_size_mismatch|bundle_hash_mismatch"):
        svc.promote_channel(actor(), environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", manifest_id=m.manifest_id)


def test_truncated_provider_object_blocks_promotion() -> None:
    svc, provider, _cache, _clock = service()
    payload = b"abcdefghij"
    item = bundle("bundle.base", payload)
    register_payload(provider, item, payload)
    m = manifest("manifest.test.v1", (item,), revision=1)
    svc.register_manifest(actor(), m)
    provider.tamper_for_test(item.object_id, payload[:4])
    with pytest.raises(ContentDeliveryIntegrityError, match="bundle_size_mismatch"):
        svc.promote_channel(actor(), environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", manifest_id=m.manifest_id)


def test_wrong_client_or_schema_version_is_rejected() -> None:
    svc, provider, _cache, _clock = service()
    payload = b"data"
    item = bundle("bundle.base", payload)
    register_payload(provider, item, payload)
    m = manifest("manifest.test.v1", (item,), revision=1, min_client_version=2, max_client_version=4, schema_version=3)
    svc.register_manifest(actor(), m)
    svc.promote_channel(actor(), environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", manifest_id=m.manifest_id)
    with pytest.raises(ContentDeliveryPolicyError, match="client_manifest_incompatible"):
        svc.resolve_channel(environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", client_version=1, schema_version=3)
    with pytest.raises(ContentDeliveryPolicyError, match="client_manifest_incompatible"):
        svc.resolve_channel(environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", client_version=2, schema_version=2)


def test_channel_promotion_requires_object_authorization() -> None:
    svc, provider, _cache, _clock = service()
    payload = b"data"
    item = bundle("bundle.base", payload)
    register_payload(provider, item, payload)
    m = manifest("manifest.test.v1", (item,), revision=1)
    svc.register_manifest(actor(), m)
    unauthorized = actor(objects=("manifest.test.v1", "test"))
    with pytest.raises(ContentDeliveryAuthorizationError, match="forbidden"):
        svc.promote_channel(unauthorized, environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", manifest_id=m.manifest_id)


def test_function_authorization_is_enforced() -> None:
    svc, _provider, _cache, _clock = service()
    item = bundle("bundle.base", b"data")
    restricted = actor(permissions=("content.channel.promote",))
    with pytest.raises(ContentDeliveryAuthorizationError, match="forbidden"):
        svc.register_manifest(restricted, manifest("manifest.test.v1", (item,), revision=1))


def test_environment_isolation() -> None:
    svc, provider, _cache, _clock = service()
    test_payload = b"test"
    prod_payload = b"prod"
    test_bundle = bundle("bundle.base", test_payload, object_id="bundle.base")
    prod_bundle = bundle("bundle.other", prod_payload, object_id="bundle.other")
    register_payload(provider, test_bundle, test_payload)
    register_payload(provider, prod_bundle, prod_payload)
    test_manifest = manifest("manifest.test.v1", (test_bundle,), revision=1)
    prod_manifest = manifest("manifest.prod", (prod_bundle,), revision=1, environment=BackendEnvironmentKind.PRODUCTION)
    svc.register_manifest(actor(), test_manifest)
    svc.register_manifest(actor(), prod_manifest)
    svc.promote_channel(actor(), environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", manifest_id=test_manifest.manifest_id)
    with pytest.raises(ContentDeliveryStateError, match="manifest_not_found"):
        svc.promote_channel(actor(), environment=BackendEnvironmentKind.PRODUCTION, channel_id="channel.stable", manifest_id=test_manifest.manifest_id)


def test_cache_hit_uses_etag_and_corruption_is_rebuilt_atomically() -> None:
    svc, provider, cache, _clock = service()
    payload = b"stable-cache-payload"
    item = bundle("bundle.base", payload)
    register_payload(provider, item, payload)
    m = manifest("manifest.test.v1", (item,), revision=1)
    svc.register_manifest(actor(), m)
    svc.promote_channel(actor(), environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", manifest_id=m.manifest_id)

    first = svc.fetch_bundle(environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", bundle_id=item.bundle_id, client_version=1, schema_version=1)
    second = svc.fetch_bundle(environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", bundle_id=item.bundle_id, client_version=1, schema_version=1)
    assert first.disposition is CacheDisposition.MISS
    assert second.disposition is CacheDisposition.HIT

    cache.corrupt_for_test(m.digest(), item.bundle_id, b"corrupt")
    rebuilt = svc.fetch_bundle(environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", bundle_id=item.bundle_id, client_version=1, schema_version=1)
    assert rebuilt.disposition is CacheDisposition.REBUILT
    cached = cache.entry(m.digest(), item.bundle_id)
    assert cached is not None and cached.payload == payload and cached.digest() == item.sha256


def test_range_fetch_and_if_range_follow_representation_etag() -> None:
    svc, provider, _cache, _clock = service()
    payload = b"0123456789"
    item = bundle("bundle.base", payload)
    register_payload(provider, item, payload)
    m = manifest("manifest.test.v1", (item,), revision=1)
    svc.register_manifest(actor(), m)
    svc.promote_channel(actor(), environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", manifest_id=m.manifest_id)

    partial = svc.fetch_bundle_range(
        environment=BackendEnvironmentKind.TEST,
        channel_id="channel.stable",
        bundle_id=item.bundle_id,
        client_version=1,
        schema_version=1,
        start=2,
        end_exclusive=6,
        if_range=item.etag,
    )
    assert partial.payload == b"2345"
    assert partial.is_partial

    full = svc.fetch_bundle_range(
        environment=BackendEnvironmentKind.TEST,
        channel_id="channel.stable",
        bundle_id=item.bundle_id,
        client_version=1,
        schema_version=1,
        start=2,
        end_exclusive=6,
        if_range='"stale"',
    )
    assert full.payload == payload
    assert not full.is_partial


def test_stale_channel_promotion_is_rejected() -> None:
    svc, provider, _cache, _clock = service()
    a = bundle("bundle.base", b"a")
    b = bundle("bundle.extra", b"b")
    c = bundle("bundle.patch", b"c")
    for item, payload in ((a, b"a"), (b, b"b"), (c, b"c")):
        register_payload(provider, item, payload)
    m1 = manifest("manifest.test.v1", (a,), revision=1)
    m2 = manifest("manifest.test.v2", (b,), revision=2)
    m3 = manifest("manifest.test.v3", (c,), revision=3)
    for item in (m1, m2, m3):
        svc.register_manifest(actor(), item)
    svc.promote_channel(actor(), environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", manifest_id=m1.manifest_id)
    svc.promote_channel(actor(), environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", manifest_id=m2.manifest_id, expected_current_manifest_id=m1.manifest_id)
    with pytest.raises(ContentDeliveryStateError, match="stale_channel_pointer"):
        svc.promote_channel(actor(), environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", manifest_id=m3.manifest_id, expected_current_manifest_id=m1.manifest_id)


def test_rollback_restores_prior_immutable_manifest() -> None:
    svc, provider, _cache, clock = service()
    a = bundle("bundle.base", b"a")
    b = bundle("bundle.extra", b"b")
    register_payload(provider, a, b"a")
    register_payload(provider, b, b"b")
    m1 = manifest("manifest.test.v1", (a,), revision=1)
    m2 = manifest("manifest.test.v2", (b,), revision=2)
    svc.register_manifest(actor(), m1)
    svc.register_manifest(actor(), m2)
    first = svc.promote_channel(actor(), environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", manifest_id=m1.manifest_id)
    clock.value += 1
    second = svc.promote_channel(actor(), environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", manifest_id=m2.manifest_id, expected_current_manifest_id=m1.manifest_id)
    clock.value += 1
    rolled = svc.rollback_channel(actor(), environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", to_manifest_id=m1.manifest_id)
    assert first.manifest_digest == m1.digest()
    assert second.manifest_digest == m2.digest()
    assert rolled.manifest_digest == m1.digest()
    assert rolled.revision == 3
    assert svc.manifest(BackendEnvironmentKind.TEST, m1.manifest_id).digest() == m1.digest()
    assert svc.manifest(BackendEnvironmentKind.TEST, m2.manifest_id).digest() == m2.digest()


def test_revoke_inactive_manifest_and_block_future_promotion() -> None:
    svc, provider, _cache, _clock = service()
    a = bundle("bundle.base", b"a")
    b = bundle("bundle.extra", b"b")
    register_payload(provider, a, b"a")
    register_payload(provider, b, b"b")
    m1 = manifest("manifest.test.v1", (a,), revision=1)
    m2 = manifest("manifest.test.v2", (b,), revision=2)
    svc.register_manifest(actor(), m1)
    svc.register_manifest(actor(), m2)
    svc.promote_channel(actor(), environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", manifest_id=m1.manifest_id)
    with pytest.raises(ContentDeliveryStateError, match="cannot_revoke_active_manifest"):
        svc.revoke_manifest(actor(), environment=BackendEnvironmentKind.TEST, manifest_id=m1.manifest_id)
    svc.revoke_manifest(actor(), environment=BackendEnvironmentKind.TEST, manifest_id=m2.manifest_id)
    with pytest.raises(ContentDeliveryStateError, match="manifest_revoked"):
        svc.promote_channel(actor(), environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", manifest_id=m2.manifest_id)


def test_capacity_budgets_fail_closed() -> None:
    svc, _provider, _cache, _clock = service(max_manifests=1, max_bundles_per_manifest=1, max_channels=1)
    a = bundle("bundle.base", b"a")
    b = bundle("bundle.extra", b"b")
    svc.register_manifest(actor(), manifest("manifest.test.v1", (a,), revision=1))
    with pytest.raises(ContentDeliveryCapacityError, match="manifest_capacity"):
        svc.register_manifest(actor(), manifest("manifest.test.v2", (b,), revision=2))

    svc2, _provider2, _cache2, _clock2 = service(max_bundles_per_manifest=1)
    with pytest.raises(ContentDeliveryCapacityError, match="bundles_per_manifest_capacity"):
        svc2.register_manifest(actor(), manifest("manifest.test.v1", (a, b), revision=1))


def test_redacted_evidence_contains_no_provider_live_or_raw_url_claim() -> None:
    svc, provider, _cache, _clock = service()
    payload = b"safe"
    item = bundle("bundle.base", payload)
    register_payload(provider, item, payload)
    m = manifest("manifest.test.v1", (item,), revision=1)
    svc.register_manifest(actor(), m)
    svc.promote_channel(actor(), environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", manifest_id=m.manifest_id)
    svc.fetch_bundle(environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", bundle_id=item.bundle_id, client_version=1, schema_version=1)
    evidence = svc.redacted_evidence()
    assert evidence["provider_kind"] == "local_deterministic"
    assert evidence["provider_live_claim"] is False
    assert evidence["secrets_exposed"] is False
    assert evidence["raw_urls_exposed"] is False
    assert evidence["executable_content_allowed"] is False
    rendered = repr(evidence).lower()
    assert "http://" not in rendered and "https://" not in rendered and "token" not in rendered and "secret=" not in rendered


def test_state_digest_is_deterministic_for_equivalent_runs() -> None:
    def run() -> str:
        svc, provider, _cache, _clock = service()
        a = bundle("bundle.base", b"a")
        b = bundle("bundle.extra", b"b", dependencies=("bundle.base",))
        register_payload(provider, a, b"a")
        register_payload(provider, b, b"b")
        m = manifest("manifest.test.v1", (b, a), revision=1)
        svc.register_manifest(actor(), m)
        svc.promote_channel(actor(), environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", manifest_id=m.manifest_id)
        svc.fetch_bundle(environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", bundle_id=a.bundle_id, client_version=1, schema_version=1)
        return svc.state_snapshot().digest()

    assert run() == run()
