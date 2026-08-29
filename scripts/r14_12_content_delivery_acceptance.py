from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

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
    InMemoryContentDeliveryService,
    LocalContentProvider,
    VerifiedContentCache,
)
from kodepoia.backend.contracts import BackendEnvironmentKind


class Clock:
    def __init__(self, value: int = 1_700_000_000_000) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value


AUTHORIZED_OBJECTS = (
    "bundle.base",
    "bundle.extra",
    "bundle.patch",
    "channel.stable",
    "manifest.prod",
    "manifest.v1",
    "manifest.v2",
    "manifest.v3",
    "production",
    "test",
)


def actor(*, permissions: tuple[str, ...] = ("*",), objects: tuple[str, ...] = AUTHORIZED_OBJECTS) -> AuthorityActorContext:
    return AuthorityActorContext(
        account_id="acceptance-operator",
        session_id="acceptance-session",
        permissions=permissions,
        authorized_object_ids=objects,
    )


def bundle(bundle_id: str, payload: bytes, *, version: int = 1, dependencies: tuple[str, ...] = ()) -> ContentBundleDefinition:
    return ContentBundleDefinition(
        bundle_id=bundle_id,
        version=version,
        object_id=bundle_id,
        payload_name=f"{bundle_id}.asset",
        media_type="application/octet-stream",
        size_bytes=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
        dependencies=dependencies,
    )


def manifest(
    manifest_id: str,
    revision: int,
    bundles: tuple[ContentBundleDefinition, ...],
    *,
    environment: BackendEnvironmentKind = BackendEnvironmentKind.TEST,
    min_client_version: int = 1,
    max_client_version: int = 4,
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
        created_at_ms=1_699_999_000_000 + revision,
    )


def expected_exception(exc_type: type[BaseException], fn, text: str | None = None) -> bool:
    try:
        fn()
    except exc_type as exc:
        return text is None or text in str(exc)
    return False


def run(source_sha: str) -> dict[str, object]:
    if len(source_sha) != 40 or any(char not in "0123456789abcdef" for char in source_sha):
        raise ValueError("source_sha must be a lowercase 40-character Git SHA")

    clock = Clock()
    provider = LocalContentProvider(max_object_bytes=1024 * 1024, max_objects=32)
    cache = VerifiedContentCache(max_entries=32, max_bytes=2 * 1024 * 1024)
    service = InMemoryContentDeliveryService(
        clock_ms=clock,
        provider=provider,
        cache=cache,
        max_manifests=16,
        max_bundles_per_manifest=16,
        max_channels=8,
        max_trace_records=256,
    )
    who = actor()

    base_payload = b"kodepoia-content-base-v1\n" * 16
    extra_payload = b"kodepoia-content-extra-v1\n" * 12
    patch_payload = b"kodepoia-content-patch-v2\n" * 10
    base = bundle("bundle.base", base_payload)
    extra = bundle("bundle.extra", extra_payload, dependencies=("bundle.base",))
    patch = bundle("bundle.patch", patch_payload, version=2, dependencies=("bundle.base",))
    for item, payload in ((base, base_payload), (extra, extra_payload), (patch, patch_payload)):
        assert provider.put(item.object_id, payload) == item.sha256

    m1 = manifest("manifest.v1", 1, (extra, base))
    m2 = manifest("manifest.v2", 2, (patch, base))
    service.register_manifest(who, m1)
    service.register_manifest(who, m2)

    checks: dict[str, bool] = {}
    checks["immutable_bundle_identity"] = base.digest() == bundle("bundle.base", base_payload).digest()
    checks["immutable_manifest_identity"] = service.register_manifest(who, m1).digest() == m1.digest()
    checks["executable_payload_rejected"] = expected_exception(
        ContentDeliveryPolicyError,
        lambda: ContentBundleDefinition(
            bundle_id="bundle.bad",
            version=1,
            object_id="bundle.bad",
            payload_name="payload.exe",
            media_type="application/octet-stream",
            size_bytes=1,
            sha256=hashlib.sha256(b"x").hexdigest(),
        ),
        "executable_payload_forbidden",
    )
    missing = bundle("bundle.missing", b"missing", dependencies=("bundle.unknown",))
    checks["missing_dependency_rejected"] = expected_exception(
        ContentDeliveryPolicyError,
        lambda: service.register_manifest(who, manifest("manifest.missing", 3, (missing,))),
        "dependency_not_found",
    )
    cycle_a = bundle("bundle.cycle.a", b"a", dependencies=("bundle.cycle.b",))
    cycle_b = bundle("bundle.cycle.b", b"b", dependencies=("bundle.cycle.a",))
    checks["dependency_cycle_rejected"] = expected_exception(
        ContentDeliveryPolicyError,
        lambda: service.register_manifest(who, manifest("manifest.cycle", 3, (cycle_a, cycle_b))),
        "dependency_cycle",
    )

    # Integrity failures are tested on isolated providers so canonical accepted state is unchanged.
    bad_provider = LocalContentProvider(max_object_bytes=1024, max_objects=4)
    bad_cache = VerifiedContentCache(max_entries=4, max_bytes=4096)
    bad_service = InMemoryContentDeliveryService(clock_ms=clock, provider=bad_provider, cache=bad_cache, max_manifests=4, max_bundles_per_manifest=4, max_channels=2, max_trace_records=32)
    bad_bundle = bundle("bundle.base", b"trusted-object")
    bad_manifest = manifest("manifest.v1", 1, (bad_bundle,))
    bad_provider.put(bad_bundle.object_id, b"trusted-object")
    bad_service.register_manifest(who, bad_manifest)
    bad_provider.tamper_for_test(bad_bundle.object_id, b"tampered-object")
    checks["tampered_content_rejected"] = expected_exception(
        ContentDeliveryIntegrityError,
        lambda: bad_service.promote_channel(who, environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", manifest_id=bad_manifest.manifest_id),
    )

    short_provider = LocalContentProvider(max_object_bytes=1024, max_objects=4)
    short_cache = VerifiedContentCache(max_entries=4, max_bytes=4096)
    short_service = InMemoryContentDeliveryService(clock_ms=clock, provider=short_provider, cache=short_cache, max_manifests=4, max_bundles_per_manifest=4, max_channels=2, max_trace_records=32)
    short_bundle = bundle("bundle.base", b"0123456789")
    short_manifest = manifest("manifest.v1", 1, (short_bundle,))
    short_provider.put(short_bundle.object_id, b"0123456789")
    short_service.register_manifest(who, short_manifest)
    short_provider.tamper_for_test(short_bundle.object_id, b"012")
    checks["truncated_content_rejected"] = expected_exception(
        ContentDeliveryIntegrityError,
        lambda: short_service.promote_channel(who, environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", manifest_id=short_manifest.manifest_id),
        "bundle_size_mismatch",
    )

    first_pointer = service.promote_channel(
        who,
        environment=BackendEnvironmentKind.TEST,
        channel_id="channel.stable",
        manifest_id=m1.manifest_id,
    )
    checks["atomic_channel_promotion"] = first_pointer.manifest_digest == m1.digest() and first_pointer.revision == 1
    checks["client_schema_compatibility"] = (
        service.resolve_channel(environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", client_version=1, schema_version=1).digest() == m1.digest()
        and expected_exception(
            ContentDeliveryPolicyError,
            lambda: service.resolve_channel(environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", client_version=99, schema_version=1),
            "client_manifest_incompatible",
        )
        and expected_exception(
            ContentDeliveryPolicyError,
            lambda: service.resolve_channel(environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", client_version=1, schema_version=2),
            "client_manifest_incompatible",
        )
    )
    unauthorized = actor(objects=("manifest.v1", "manifest.v2", "test"))
    checks["object_authorization"] = expected_exception(
        ContentDeliveryAuthorizationError,
        lambda: service.promote_channel(unauthorized, environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", manifest_id=m2.manifest_id),
        "forbidden",
    )
    restricted = actor(permissions=("content.channel.promote",))
    checks["function_authorization"] = expected_exception(
        ContentDeliveryAuthorizationError,
        lambda: service.register_manifest(restricted, m1),
        "forbidden",
    )
    checks["environment_isolation"] = expected_exception(
        ContentDeliveryStateError,
        lambda: service.promote_channel(who, environment=BackendEnvironmentKind.PRODUCTION, channel_id="channel.stable", manifest_id=m1.manifest_id),
        "manifest_not_found",
    )

    first_download = service.fetch_bundle(
        environment=BackendEnvironmentKind.TEST,
        channel_id="channel.stable",
        bundle_id="bundle.base",
        client_version=1,
        schema_version=1,
    )
    second_download = service.fetch_bundle(
        environment=BackendEnvironmentKind.TEST,
        channel_id="channel.stable",
        bundle_id="bundle.base",
        client_version=1,
        schema_version=1,
    )
    checks["etag_cache_hit"] = first_download.disposition is CacheDisposition.MISS and second_download.disposition is CacheDisposition.HIT

    partial = service.fetch_bundle_range(
        environment=BackendEnvironmentKind.TEST,
        channel_id="channel.stable",
        bundle_id="bundle.base",
        client_version=1,
        schema_version=1,
        start=2,
        end_exclusive=10,
        if_range=base.etag,
    )
    full = service.fetch_bundle_range(
        environment=BackendEnvironmentKind.TEST,
        channel_id="channel.stable",
        bundle_id="bundle.base",
        client_version=1,
        schema_version=1,
        start=2,
        end_exclusive=10,
        if_range='"stale"',
    )
    checks["range_if_range_semantics"] = partial.payload == base_payload[2:10] and partial.is_partial and full.payload == base_payload and not full.is_partial

    cache.corrupt_for_test(m1.digest(), base.bundle_id, b"cache-corrupt")
    rebuilt = service.fetch_bundle(
        environment=BackendEnvironmentKind.TEST,
        channel_id="channel.stable",
        bundle_id="bundle.base",
        client_version=1,
        schema_version=1,
    )
    checks["cache_corruption_rebuilt"] = rebuilt.disposition is CacheDisposition.REBUILT and cache.entry(m1.digest(), base.bundle_id).digest() == base.sha256  # type: ignore[union-attr]

    clock.value += 1
    second_pointer = service.promote_channel(
        who,
        environment=BackendEnvironmentKind.TEST,
        channel_id="channel.stable",
        manifest_id=m2.manifest_id,
        expected_current_manifest_id=m1.manifest_id,
    )
    checks["stale_promotion_rejected"] = expected_exception(
        ContentDeliveryStateError,
        lambda: service.promote_channel(
            who,
            environment=BackendEnvironmentKind.TEST,
            channel_id="channel.stable",
            manifest_id=m1.manifest_id,
            expected_current_manifest_id=m1.manifest_id,
        ),
        "stale_channel_pointer",
    )
    clock.value += 1
    rollback_pointer = service.rollback_channel(
        who,
        environment=BackendEnvironmentKind.TEST,
        channel_id="channel.stable",
        to_manifest_id=m1.manifest_id,
    )
    checks["rollback_converges"] = second_pointer.manifest_digest == m2.digest() and rollback_pointer.manifest_digest == m1.digest() and rollback_pointer.revision == 3

    service.revoke_manifest(who, environment=BackendEnvironmentKind.TEST, manifest_id=m2.manifest_id)
    checks["revocation_enforced"] = expected_exception(
        ContentDeliveryStateError,
        lambda: service.promote_channel(who, environment=BackendEnvironmentKind.TEST, channel_id="channel.stable", manifest_id=m2.manifest_id),
        "manifest_revoked",
    )

    tiny_provider = LocalContentProvider(max_object_bytes=1024, max_objects=4)
    tiny_cache = VerifiedContentCache(max_entries=4, max_bytes=4096)
    tiny = InMemoryContentDeliveryService(clock_ms=clock, provider=tiny_provider, cache=tiny_cache, max_manifests=1, max_bundles_per_manifest=1, max_channels=1, max_trace_records=16)
    tiny_item = bundle("bundle.base", b"a")
    tiny.register_manifest(who, manifest("manifest.v1", 1, (tiny_item,)))
    checks["bounded_capacity"] = expected_exception(
        ContentDeliveryCapacityError,
        lambda: tiny.register_manifest(who, manifest("manifest.v2", 2, (bundle("bundle.extra", b"b"),))),
        "manifest_capacity",
    )

    redacted = service.redacted_evidence()
    rendered = json.dumps(redacted, sort_keys=True).lower()
    checks["redacted_evidence"] = (
        redacted["provider_live_claim"] is False
        and redacted["secrets_exposed"] is False
        and redacted["raw_urls_exposed"] is False
        and redacted["executable_content_allowed"] is False
        and "http://" not in rendered
        and "https://" not in rendered
    )

    if not all(checks.values()):
        failed = sorted(name for name, ok in checks.items() if not ok)
        raise AssertionError(f"R14.12 acceptance checks failed: {failed}")

    state = service.state_snapshot()
    evidence = {
        "schema_version": 1,
        "source_sha": source_sha,
        "status": "pass",
        "checks": checks,
        "digests": {
            "manifest_v1": m1.digest(),
            "manifest_v2": m2.digest(),
            "state": state.digest(),
            "trace": state.trace_digest,
            "channel": service.channel(BackendEnvironmentKind.TEST, "channel.stable").digest(),
            "bundle": base.digest(),
            "download": first_download.digest(),
            "rollback": rollback_pointer.digest(),
        },
        "counts": {
            "manifests": len(state.manifest_digests),
            "bundles": len(m1.bundles) + len(m2.bundles),
            "channel_revision": service.channel(BackendEnvironmentKind.TEST, "channel.stable").revision,
            "cache_bytes": state.cache_bytes,
        },
        "budgets": {
            "max_manifests": service.max_manifests,
            "max_bundles_per_manifest": service.max_bundles_per_manifest,
            "max_channels": service.max_channels,
            "max_cache_entries": cache.max_entries,
            "max_cache_bytes": cache.max_bytes,
            "max_object_bytes": provider.max_object_bytes,
        },
        "manual_state": "conditional_not_triggered",
        "provider_live_claim": False,
        "secrets_exposed": False,
        "raw_urls_exposed": False,
        "executable_content_allowed": False,
    }
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic R14.12 content delivery acceptance evidence")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    evidence = run(args.source_sha)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
