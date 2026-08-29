from __future__ import annotations

import kodepoia.backend as backend


EXPECTED = (
    "CacheDisposition",
    "ChannelPointer",
    "ContentBundleDefinition",
    "ContentDeliveryAuthorizationError",
    "ContentDeliveryCapacityError",
    "ContentDeliveryIntegrityError",
    "ContentDeliveryPolicyError",
    "ContentDeliveryStateError",
    "ContentDeliveryStateSnapshot",
    "ContentFetchResponse",
    "ContentManifest",
    "ContentObjectState",
    "ContentSignatureState",
    "DownloadResult",
    "InMemoryContentDeliveryService",
    "LocalContentProvider",
    "VerifiedContentCache",
)


def test_content_delivery_public_exports_are_available() -> None:
    for name in EXPECTED:
        assert hasattr(backend, name), name
        assert name in backend.__all__, name
