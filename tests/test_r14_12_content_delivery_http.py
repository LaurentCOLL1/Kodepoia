from __future__ import annotations

import hashlib

import pytest

from kodepoia.backend.authority import AuthorityActorContext
from kodepoia.backend.content_delivery import (
    CacheDisposition,
    ContentBundleDefinition,
    ContentDeliveryPolicyError,
    ContentManifest,
    InMemoryContentDeliveryService,
    LocalContentProvider,
    VerifiedContentCache,
)
from kodepoia.backend.content_delivery_http import LoopbackHttpContentFixture, LoopbackHttpContentProvider
from kodepoia.backend.contracts import BackendEnvironmentKind


def _bundle(payload: bytes) -> ContentBundleDefinition:
    return ContentBundleDefinition(
        bundle_id="bundle.base",
        version=1,
        object_id="bundle.base",
        payload_name="bundle.base.asset",
        media_type="application/octet-stream",
        size_bytes=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
    )


def _manifest(item: ContentBundleDefinition) -> ContentManifest:
    return ContentManifest(
        manifest_id="manifest.http",
        revision=1,
        environment=BackendEnvironmentKind.TEST,
        bundles=(item,),
        min_client_version=1,
        max_client_version=1,
        schema_version=1,
        created_at_ms=1_000,
    )


def _actor() -> AuthorityActorContext:
    return AuthorityActorContext(
        account_id="operator",
        session_id="session",
        permissions=("*",),
        authorized_object_ids=("bundle.base", "manifest.http", "channel.stable", "test"),
    )


def test_loopback_http_fixture_exercises_etag_range_and_if_range() -> None:
    payload = b"0123456789-loopback-http"
    item = _bundle(payload)
    storage = LocalContentProvider(max_object_bytes=1024, max_objects=4)
    assert storage.put(item.object_id, payload) == item.sha256

    with LoopbackHttpContentFixture(storage) as fixture:
        provider = LoopbackHttpContentProvider(fixture.base_url, max_response_bytes=1024)

        full = provider.fetch(item.object_id)
        assert full is not None
        assert full.payload == payload
        assert full.etag == item.etag
        assert provider.fetch(item.object_id, if_none_match=item.etag) is None

        partial = provider.fetch(item.object_id, start=2, end_exclusive=7, if_range=item.etag)
        assert partial is not None
        assert partial.payload == payload[2:7]
        assert partial.is_partial
        assert partial.total_size == len(payload)

        stale = provider.fetch(item.object_id, start=2, end_exclusive=7, if_range='"stale"')
        assert stale is not None
        assert stale.payload == payload
        assert not stale.is_partial


def test_content_service_promotes_and_fetches_over_actual_loopback_http() -> None:
    payload = b"kodepoia-http-content"
    item = _bundle(payload)
    manifest = _manifest(item)
    storage = LocalContentProvider(max_object_bytes=1024, max_objects=4)
    storage.put(item.object_id, payload)

    with LoopbackHttpContentFixture(storage) as fixture:
        http_provider = LoopbackHttpContentProvider(fixture.base_url, max_response_bytes=1024)
        cache = VerifiedContentCache(max_entries=4, max_bytes=4096)
        service = InMemoryContentDeliveryService(
            clock_ms=lambda: 2_000,
            provider=http_provider,  # type: ignore[arg-type]
            cache=cache,
            max_manifests=4,
            max_bundles_per_manifest=4,
            max_channels=2,
            max_trace_records=32,
        )
        service.register_manifest(_actor(), manifest)
        pointer = service.promote_channel(
            _actor(),
            environment=BackendEnvironmentKind.TEST,
            channel_id="channel.stable",
            manifest_id=manifest.manifest_id,
        )
        assert pointer.manifest_digest == manifest.digest()

        first = service.fetch_bundle(
            environment=BackendEnvironmentKind.TEST,
            channel_id="channel.stable",
            bundle_id=item.bundle_id,
            client_version=1,
            schema_version=1,
        )
        second = service.fetch_bundle(
            environment=BackendEnvironmentKind.TEST,
            channel_id="channel.stable",
            bundle_id=item.bundle_id,
            client_version=1,
            schema_version=1,
        )
        assert first.disposition is CacheDisposition.MISS
        assert second.disposition is CacheDisposition.HIT
        cached = cache.entry(manifest.digest(), item.bundle_id)
        assert cached is not None and cached.payload == payload


@pytest.mark.parametrize(
    "base_url",
    (
        "https://127.0.0.1:8123",
        "http://example.com:8123",
        "http://127.0.0.1:8123/content",
        "http://user@127.0.0.1:8123",
    ),
)
def test_loopback_http_provider_rejects_non_fixture_endpoints(base_url: str) -> None:
    with pytest.raises(ContentDeliveryPolicyError):
        LoopbackHttpContentProvider(base_url)
