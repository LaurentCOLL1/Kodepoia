from pathlib import Path

module_path = Path("src/kodepoia/backend/entitlements.py")
text = module_path.read_text(encoding="utf-8")
old = '''        notification_digest = notification.digest()\n        event_key = (provider, environment, notification.message_id)\n        with self._lock:\n            replay = self._event_replays.get(event_key)\n            if replay is not None:\n                if replay.request_digest != notification_digest:\n                    raise EntitlementStateError("message_id_conflict")\n                return replace(replay.result, replayed=True)\n'''
new = '''        notification_digest = canonical_sha256(\n            {\n                "notification": notification.canonical_redacted(),\n                "account_id": account_id,\n            }\n        )\n        event_key = (provider, environment, notification.message_id)\n        with self._lock:\n            replay = self._event_replays.get(event_key)\n            if replay is not None:\n                if replay.request_digest != notification_digest:\n                    raise EntitlementStateError("message_id_conflict")\n                return replace(replay.result, replayed=True)\n'''
assert text.count(old) == 1, text.count(old)
module_path.write_text(text.replace(old, new), encoding="utf-8")

init_path = Path("src/kodepoia/backend/__init__.py")
init = init_path.read_text(encoding="utf-8")
anchor = "from .governance import ("
block = '''from .entitlements import (\n    BillingEnvironment,\n    BillingProductKind,\n    BillingProvider,\n    BillingProviderAdapter,\n    CatalogProductDefinition,\n    EntitlementAccessState,\n    EntitlementAuthorizationError,\n    EntitlementCapacityError,\n    EntitlementMutationResult,\n    EntitlementPolicyError,\n    EntitlementSnapshot,\n    EntitlementStateError,\n    EntitlementVerificationError,\n    FixtureBillingProviderAdapter,\n    InMemoryEntitlementService,\n    ProviderEventRecord,\n    ProviderPurchaseSnapshot,\n    ProviderPurchaseState,\n    PurchaseRecord,\n    ValidatedProviderNotification,\n)\n'''
assert init.count(anchor) == 1, init.count(anchor)
init = init.replace(anchor, block + anchor)
all_anchor = '    "BACKEND_DNA_SERVICE_KINDS",\n'
all_block = '''    "BillingEnvironment",\n    "BillingProductKind",\n    "BillingProvider",\n    "BillingProviderAdapter",\n    "CatalogProductDefinition",\n    "EntitlementAccessState",\n    "EntitlementAuthorizationError",\n    "EntitlementCapacityError",\n    "EntitlementMutationResult",\n    "EntitlementPolicyError",\n    "EntitlementSnapshot",\n    "EntitlementStateError",\n    "EntitlementVerificationError",\n    "FixtureBillingProviderAdapter",\n    "InMemoryEntitlementService",\n    "ProviderEventRecord",\n    "ProviderPurchaseSnapshot",\n    "ProviderPurchaseState",\n    "PurchaseRecord",\n    "ValidatedProviderNotification",\n'''
assert init.count(all_anchor) == 1, init.count(all_anchor)
init_path.write_text(init.replace(all_anchor, all_block + all_anchor), encoding="utf-8")
