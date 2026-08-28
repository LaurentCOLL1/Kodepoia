from __future__ import annotations

import json
from pathlib import Path


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match in {path}, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


contracts = Path("src/kodepoia/backend/contracts.py")
replace_once(
    contracts,
    '    PROGRESSION = "progression"\n    ENTITLEMENT = "entitlement"\n',
    '    PROGRESSION = "progression"\n    CATALOG = "catalog"\n    ENTITLEMENT = "entitlement"\n    BILLING = "billing"\n',
    "backend service kinds",
)

backend_init = Path("src/kodepoia/backend/__init__.py")
replace_once(
    backend_init,
    'from .status import BackendErrorCode, BackendOperationStatus, BackendStatusSnapshot\n',
    'from .intent import (\n    BACKEND_DNA_SERVICE_KINDS,\n    BACKEND_SERVICE_DEPENDENCIES,\n    BackendProjectProfile,\n    BackendRuntimeIntent,\n    backend_runtime_intents,\n    backend_wizard_questions,\n)\nfrom .status import BackendErrorCode, BackendOperationStatus, BackendStatusSnapshot\n',
    "backend intent imports",
)
replace_once(
    backend_init,
    '__all__ = [\n    "BackendBoundaryError",\n',
    '__all__ = [\n    "BACKEND_DNA_SERVICE_KINDS",\n    "BACKEND_SERVICE_DEPENDENCIES",\n    "BackendBoundaryError",\n',
    "backend intent exports prefix",
)
replace_once(
    backend_init,
    '    "BackendProviderRequest",\n    "BackendRuntimeBudget",\n',
    '    "BackendProjectProfile",\n    "BackendProviderRequest",\n    "BackendRuntimeBudget",\n    "BackendRuntimeIntent",\n',
    "backend intent exports models",
)
replace_once(
    backend_init,
    '    "BackendStatusSnapshot",\n    "canonical_json_bytes",\n',
    '    "BackendStatusSnapshot",\n    "backend_runtime_intents",\n    "backend_wizard_questions",\n    "canonical_json_bytes",\n',
    "backend intent exports functions",
)

dna = Path("src/kodepoia/project/dna.py")
replace_once(
    dna,
    'import yaml\n\nfrom kodepoia.desktop.contracts import (\n',
    'import yaml\n\nfrom kodepoia.backend.contracts import BackendServiceKind\nfrom kodepoia.backend.intent import BackendProjectProfile\nfrom kodepoia.desktop.contracts import (\n',
    "dna backend imports",
)
replace_once(
    dna,
    '    desktop: DesktopProjectProfile | None = None\n    mobile: MobileProjectProfile | None = None\n',
    '    desktop: DesktopProjectProfile | None = None\n    mobile: MobileProjectProfile | None = None\n    backend: BackendProjectProfile | None = None\n',
    "dna backend field",
)
replace_once(
    dna,
    '        elif self.project_type is ProjectType.MOBILE_APP:\n            raise ValueError("mobile_app projects require an explicit mobile profile")\n\n        normalized_inputs = {item.lower() for item in self.inputs}\n',
    '        elif self.project_type is ProjectType.MOBILE_APP:\n            raise ValueError("mobile_app projects require an explicit mobile profile")\n\n        if self.backend is not None:\n            self.backend.validate()\n\n        normalized_inputs = {item.lower() for item in self.inputs}\n',
    "dna backend validate",
)
replace_once(
    dna,
    '        if self.mobile is None:\n            payload.pop("mobile", None)\n        return payload\n',
    '        if self.mobile is None:\n            payload.pop("mobile", None)\n        if self.backend is None:\n            payload.pop("backend", None)\n        return payload\n',
    "dna backend serialization",
)
replace_once(
    dna,
    '                budget=MobileProjectBudget(**raw_budget),\n            )\n\n        dna = cls(\n',
    '                budget=MobileProjectBudget(**raw_budget),\n            )\n\n        raw_backend = raw.get("backend")\n        backend = None\n        if raw_backend is not None:\n            if not isinstance(raw_backend, dict):\n                raise ValueError("Backend Project DNA profile must be an object")\n            allowed_backend_keys = {"enabled", "services"}\n            unknown_backend_keys = set(raw_backend) - allowed_backend_keys\n            if unknown_backend_keys:\n                raise ValueError(\n                    "Backend Project DNA profile contains unsupported fields: "\n                    + ", ".join(sorted(str(item) for item in unknown_backend_keys))\n                )\n            enabled = raw_backend.get("enabled", False)\n            if not isinstance(enabled, bool):\n                raise ValueError("Backend Project DNA enabled must be boolean")\n            raw_services = raw_backend.get("services", [])\n            if not isinstance(raw_services, list):\n                raise ValueError("Backend Project DNA services must be an array")\n            backend = BackendProjectProfile(\n                enabled=enabled,\n                services=tuple(BackendServiceKind(item) for item in raw_services),\n            )\n\n        dna = cls(\n',
    "dna backend load",
)
replace_once(
    dna,
    '            desktop=desktop,\n            mobile=mobile,\n        )\n',
    '            desktop=desktop,\n            mobile=mobile,\n            backend=backend,\n        )\n',
    "dna backend construct",
)

wizard = Path("src/kodepoia/project/wizard.py")
replace_once(
    wizard,
    'from kodepoia.desktop.contracts import (\n',
    'from kodepoia.backend.contracts import BackendServiceKind\nfrom kodepoia.backend.intent import BackendProjectProfile, backend_wizard_questions\nfrom kodepoia.desktop.contracts import (\n',
    "wizard backend imports",
)
replace_once(
    wizard,
    '    mobile_budget: MobileProjectBudget = field(default_factory=MobileProjectBudget)\n\n    def relevant_questions(self) -> tuple[str, ...]:\n',
    '    mobile_budget: MobileProjectBudget = field(default_factory=MobileProjectBudget)\n    backend_enabled: bool = False\n    backend_services: tuple[BackendServiceKind, ...] = ()\n\n    def _backend_relevant(self) -> bool:\n        if self.backend_enabled or self.backend_services:\n            return True\n        if self.online is not DecisionState.NO or self.multiplayer is not DecisionState.NO:\n            return True\n        if self.mobile_network_intent is not MobileNetworkIntent.OFFLINE:\n            return True\n        backend_capabilities = {\n            "backend",\n            "auth",\n            "authoritative_server",\n            "matchmaking",\n            "cloud_save",\n            "progression",\n            "catalog",\n            "entitlement",\n            "billing",\n            "remote_config",\n            "content_delivery",\n            "events",\n        }\n        return any(\n            key.casefold() in backend_capabilities and value is not DecisionState.NO\n            for key, value in self.capabilities.items()\n        )\n\n    def _backend_profile(self) -> BackendProjectProfile | None:\n        if not self.backend_enabled and not self.backend_services:\n            return None\n        return BackendProjectProfile(\n            enabled=self.backend_enabled,\n            services=tuple(self.backend_services),\n        )\n\n    def relevant_questions(self) -> tuple[str, ...]:\n',
    "wizard backend fields",
)
replace_once(
    wizard,
    '        if Platform.XR in self.platforms:\n            questions += ["openxr", "motion_controllers", "xr_performance"]\n        return tuple(questions)\n',
    '        if Platform.XR in self.platforms:\n            questions += ["openxr", "motion_controllers", "xr_performance"]\n        questions += list(\n            backend_wizard_questions(\n                self._backend_profile(),\n                backend_relevant=self._backend_relevant(),\n            )\n        )\n        return tuple(questions)\n',
    "wizard backend questions",
)
replace_once(
    wizard,
    '            desktop=self._desktop_profile(),\n            mobile=self._mobile_profile(),\n        )\n',
    '            desktop=self._desktop_profile(),\n            mobile=self._mobile_profile(),\n            backend=self._backend_profile(),\n        )\n',
    "wizard backend build",
)

schema_path = Path("schemas/project-dna-v1.schema.json")
schema = json.loads(schema_path.read_text(encoding="utf-8"))
if "backend" in schema["properties"]:
    raise SystemExit("project DNA schema already contains backend")
schema["properties"]["backend"] = {"$ref": "#/$defs/backendProfile"}
service_enum = [
    "auth",
    "authoritative_server",
    "matchmaking",
    "cloud_save",
    "progression",
    "catalog",
    "entitlement",
    "billing",
    "remote_config",
    "content_delivery",
    "events",
]
schema["$defs"]["backendProfile"] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["enabled", "services"],
    "properties": {
        "enabled": {"type": "boolean"},
        "services": {
            "type": "array",
            "uniqueItems": True,
            "items": {"type": "string", "enum": service_enum},
        },
    },
    "allOf": [
        {
            "if": {"properties": {"enabled": {"const": False}}, "required": ["enabled"]},
            "then": {"properties": {"services": {"maxItems": 0}}},
        },
        {
            "if": {"properties": {"enabled": {"const": True}}, "required": ["enabled"]},
            "then": {"properties": {"services": {"minItems": 1}}},
        },
        {
            "if": {
                "properties": {"services": {"contains": {"const": "matchmaking"}}},
                "required": ["services"],
            },
            "then": {
                "properties": {"services": {"contains": {"const": "authoritative_server"}}}
            },
        },
        {
            "if": {
                "properties": {"services": {"contains": {"const": "billing"}}},
                "required": ["services"],
            },
            "then": {
                "properties": {
                    "services": {
                        "allOf": [
                            {"contains": {"const": "catalog"}},
                            {"contains": {"const": "entitlement"}},
                        ]
                    }
                }
            },
        },
    ],
}
schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("R14.2 core DNA/Wizard/schema patch applied")
