from pathlib import Path

path = Path("src/kodepoia/backend/__init__.py")
text = path.read_text(encoding="utf-8")

import_anchor = "from .contracts import (\n"
assert text.count(import_anchor) == 1
block = '''from .content_delivery import (
    CacheDisposition,
    ChannelPointer,
    ContentBundleDefinition,
    ContentDeliveryAuthorizationError,
    ContentDeliveryCapacityError,
    ContentDeliveryIntegrityError,
    ContentDeliveryPolicyError,
    ContentDeliveryStateError,
    ContentDeliveryStateSnapshot,
    ContentFetchResponse,
    ContentManifest,
    ContentObjectState,
    ContentSignatureState,
    DownloadResult,
    InMemoryContentDeliveryService,
    LocalContentProvider,
    VerifiedContentCache,
)
'''
assert "from .content_delivery import (" not in text
text = text.replace(import_anchor, block + import_anchor, 1)

all_anchor = '    "BackendCapabilitySnapshot",\n'
assert text.count(all_anchor) == 1
all_block = '''    "CacheDisposition",
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
'''
assert '    "ContentManifest",\n' not in text
text = text.replace(all_anchor, all_block + all_anchor, 1)
path.write_text(text, encoding="utf-8")
