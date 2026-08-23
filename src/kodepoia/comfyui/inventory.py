from __future__ import annotations

import json
import os
import re
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote

from .client import ComfySystemSnapshot, ComfyUIClient
from .contracts import ComfyCapabilityState
from .errors import ComfyProtocolError, ComfyUnavailableError
from .serialization import canonical_json_bytes, canonical_sha256, make_envelope, parse_envelope

_CAPABILITY_SCHEMA = "kodepoia.comfy-capability-snapshot"
_CAPABILITY_VERSION = 1
_MAX_NODES = 100_000
_MAX_MODEL_TYPES = 4_096
_MAX_MODELS_PER_TYPE = 250_000
_MAX_INPUTS_PER_SECTION = 4_096
_MAX_OUTPUTS = 4_096
_MAX_TOKEN = 1_024
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_DRIVE_RE = re.compile(r"^[A-Za-z]:")


@dataclass(frozen=True, slots=True)
class ComfyNodeInputSpec:
    name: str
    section: str
    type_token: str | None
    choices: tuple[str | int | float | bool, ...]
    minimum: float | int | None
    maximum: float | int | None
    step: float | int | None
    spec_digest_sha256: str

    def canonical(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "section": self.section,
            "type_token": self.type_token,
            "choices": list(self.choices),
            "minimum": self.minimum,
            "maximum": self.maximum,
            "step": self.step,
            "spec_digest_sha256": self.spec_digest_sha256,
        }


@dataclass(frozen=True, slots=True)
class ComfyNodeDefinition:
    class_type: str
    category: str | None
    required_inputs: tuple[ComfyNodeInputSpec, ...]
    optional_inputs: tuple[ComfyNodeInputSpec, ...]
    output_types: tuple[str, ...]
    output_is_list: tuple[bool, ...]
    deprecated: bool
    experimental: bool
    api_node: bool
    raw_digest_sha256: str

    def canonical(self) -> dict[str, Any]:
        return {
            "class_type": self.class_type,
            "category": self.category,
            "required_inputs": [item.canonical() for item in self.required_inputs],
            "optional_inputs": [item.canonical() for item in self.optional_inputs],
            "output_types": list(self.output_types),
            "output_is_list": list(self.output_is_list),
            "deprecated": self.deprecated,
            "experimental": self.experimental,
            "api_node": self.api_node,
            "raw_digest_sha256": self.raw_digest_sha256,
        }


@dataclass(frozen=True, slots=True)
class ComfyModelInventory:
    model_type: str
    tokens: tuple[str, ...]
    digest_sha256: str

    def canonical(self) -> dict[str, Any]:
        return {
            "model_type": self.model_type,
            "tokens": list(self.tokens),
            "digest_sha256": self.digest_sha256,
        }


@dataclass(frozen=True, slots=True)
class ComfyCapabilitySnapshot:
    state: ComfyCapabilityState
    endpoint: str
    captured_at: str
    comfyui_version: str | None
    python_version: str | None
    system_digest_sha256: str | None
    feature_digest_sha256: str | None
    nodes: tuple[ComfyNodeDefinition, ...]
    models: tuple[ComfyModelInventory, ...]
    unavailable: tuple[str, ...]
    identity_sha256: str

    def identity_payload(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "comfyui_version": self.comfyui_version,
            "python_version": self.python_version,
            "system_digest_sha256": self.system_digest_sha256,
            "feature_digest_sha256": self.feature_digest_sha256,
            "nodes": [node.canonical() for node in self.nodes],
            "models": [model.canonical() for model in self.models],
            "unavailable": list(self.unavailable),
        }

    def payload(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "endpoint": self.endpoint,
            "captured_at": self.captured_at,
            "comfyui_version": self.comfyui_version,
            "python_version": self.python_version,
            "system_digest_sha256": self.system_digest_sha256,
            "feature_digest_sha256": self.feature_digest_sha256,
            "nodes": [node.canonical() for node in self.nodes],
            "models": [model.canonical() for model in self.models],
            "unavailable": list(self.unavailable),
            "identity_sha256": self.identity_sha256,
        }

    def envelope(self) -> dict[str, Any]:
        return make_envelope(schema=_CAPABILITY_SCHEMA, version=_CAPABILITY_VERSION, payload=self.payload())


@dataclass(frozen=True, slots=True)
class ComfyCapabilityDiff:
    previous_identity_sha256: str
    current_identity_sha256: str
    state: ComfyCapabilityState
    added_nodes: tuple[str, ...]
    removed_nodes: tuple[str, ...]
    changed_nodes: tuple[str, ...]
    changed_model_types: tuple[str, ...]
    system_changed: bool

    @property
    def changed(self) -> bool:
        return self.previous_identity_sha256 != self.current_identity_sha256

    def canonical(self) -> dict[str, Any]:
        return {
            "previous_identity_sha256": self.previous_identity_sha256,
            "current_identity_sha256": self.current_identity_sha256,
            "state": self.state.value,
            "added_nodes": list(self.added_nodes),
            "removed_nodes": list(self.removed_nodes),
            "changed_nodes": list(self.changed_nodes),
            "changed_model_types": list(self.changed_model_types),
            "system_changed": self.system_changed,
            "changed": self.changed,
        }


class ComfyCapabilityInventory:
    """Read-only R9.3 inventory over fixed loopback ComfyUI routes."""

    def __init__(self, client: ComfyUIClient) -> None:
        self.client = client

    def capture(self, *, captured_at: datetime | None = None) -> ComfyCapabilitySnapshot:
        now = captured_at or datetime.now(timezone.utc)
        if now.tzinfo is None:
            raise ValueError("captured_at must be timezone-aware")
        evidence_time = now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        unavailable: list[str] = []

        system: ComfySystemSnapshot | None = None
        features: dict[str, Any] | None = None
        raw_nodes: dict[str, Any] | None = None
        model_types: tuple[str, ...] | None = None

        try:
            system = self.client.system_stats()
        except ComfyUnavailableError:
            unavailable.append("system_stats")
        try:
            features = self.client.features()
        except ComfyUnavailableError:
            unavailable.append("features")
        try:
            raw_nodes = self._object_info()
        except ComfyUnavailableError:
            unavailable.append("object_info")
        try:
            model_types = self._model_types()
        except ComfyUnavailableError:
            unavailable.append("models")

        nodes = normalize_node_inventory(raw_nodes) if raw_nodes is not None else ()
        model_inventory: list[ComfyModelInventory] = []
        if model_types is not None:
            for model_type in model_types:
                try:
                    model_inventory.append(
                        ComfyModelInventory(
                            model_type=model_type,
                            tokens=self._models(model_type),
                            digest_sha256="",
                        )
                    )
                except ComfyUnavailableError:
                    unavailable.append(f"models:{model_type}")
        models = tuple(_finalize_model_inventory(item) for item in sorted(model_inventory, key=lambda x: x.model_type))

        state = ComfyCapabilityState.CURRENT if not unavailable else ComfyCapabilityState.UNAVAILABLE
        preliminary = {
            "endpoint": self.client.endpoint.origin,
            "comfyui_version": system.comfyui_version if system is not None else None,
            "python_version": system.python_version if system is not None else None,
            "system_digest_sha256": system.digest_sha256 if system is not None else None,
            "feature_digest_sha256": canonical_sha256(features) if features is not None else None,
            "nodes": [node.canonical() for node in nodes],
            "models": [model.canonical() for model in models],
            "unavailable": sorted(set(unavailable)),
        }
        identity = canonical_sha256(preliminary)
        return ComfyCapabilitySnapshot(
            state=state,
            endpoint=self.client.endpoint.origin,
            captured_at=evidence_time,
            comfyui_version=system.comfyui_version if system is not None else None,
            python_version=system.python_version if system is not None else None,
            system_digest_sha256=system.digest_sha256 if system is not None else None,
            feature_digest_sha256=canonical_sha256(features) if features is not None else None,
            nodes=nodes,
            models=models,
            unavailable=tuple(sorted(set(unavailable))),
            identity_sha256=identity,
        )

    def _object_info(self) -> dict[str, Any]:
        data = self.client._http.get_json("/object_info")
        if len(data) > _MAX_NODES:
            raise ComfyProtocolError("ComfyUI object_info exceeds the accepted node-count bound")
        return data

    def _model_types(self) -> tuple[str, ...]:
        raw = self.client._http.get_json_value("/models")
        if not isinstance(raw, list) or len(raw) > _MAX_MODEL_TYPES:
            raise ComfyProtocolError("ComfyUI /models must be a bounded array")
        result = {_safe_identifier(item, "model type", 128) for item in raw}
        if len(result) != len(raw):
            raise ComfyProtocolError("ComfyUI /models contains duplicate model types")
        return tuple(sorted(result))

    def _models(self, model_type: str) -> tuple[str, ...]:
        safe_type = _safe_identifier(model_type, "model type", 128)
        raw = self.client._http.get_json_value(f"/models/{quote(safe_type, safe='')}")
        if not isinstance(raw, list) or len(raw) > _MAX_MODELS_PER_TYPE:
            raise ComfyProtocolError("ComfyUI model inventory must be a bounded array")
        tokens = tuple(sorted(_safe_model_token(item) for item in raw))
        if len(set(tokens)) != len(tokens):
            raise ComfyProtocolError(f"ComfyUI model inventory {safe_type!r} contains duplicate tokens")
        return tokens


def normalize_node_inventory(raw_nodes: Mapping[str, Any]) -> tuple[ComfyNodeDefinition, ...]:
    if len(raw_nodes) > _MAX_NODES:
        raise ComfyProtocolError("ComfyUI object_info exceeds the accepted node-count bound")
    result: list[ComfyNodeDefinition] = []
    for class_type, raw in raw_nodes.items():
        safe_class = _safe_identifier(class_type, "node class_type", 256)
        if not isinstance(raw, dict):
            raise ComfyProtocolError(f"Node {safe_class!r} metadata must be an object")
        inputs = raw.get("input", {})
        if not isinstance(inputs, dict):
            raise ComfyProtocolError(f"Node {safe_class!r} input metadata must be an object")
        required = _normalize_input_section(inputs.get("required", {}), "required")
        optional = _normalize_input_section(inputs.get("optional", {}), "optional")
        output_types = _normalize_string_array(raw.get("output", []), "node output", _MAX_OUTPUTS, 256)
        output_is_list_raw = raw.get("output_is_list", [False] * len(output_types))
        if not isinstance(output_is_list_raw, list) or len(output_is_list_raw) != len(output_types):
            raise ComfyProtocolError(f"Node {safe_class!r} output_is_list shape is invalid")
        if any(not isinstance(value, bool) for value in output_is_list_raw):
            raise ComfyProtocolError(f"Node {safe_class!r} output_is_list must contain booleans")
        category = raw.get("category")
        if category is not None:
            category = _safe_text(category, "node category", 512)
        result.append(
            ComfyNodeDefinition(
                class_type=safe_class,
                category=category,
                required_inputs=required,
                optional_inputs=optional,
                output_types=output_types,
                output_is_list=tuple(output_is_list_raw),
                deprecated=_safe_bool(raw.get("deprecated", False), "deprecated"),
                experimental=_safe_bool(raw.get("experimental", False), "experimental"),
                api_node=_safe_bool(raw.get("api_node", False), "api_node"),
                raw_digest_sha256=canonical_sha256(raw),
            )
        )
    return tuple(sorted(result, key=lambda node: node.class_type))


def diff_capability_snapshots(
    previous: ComfyCapabilitySnapshot,
    current: ComfyCapabilitySnapshot,
) -> ComfyCapabilityDiff:
    previous_nodes = {node.class_type: node for node in previous.nodes}
    current_nodes = {node.class_type: node for node in current.nodes}
    common = previous_nodes.keys() & current_nodes.keys()
    changed_nodes = tuple(
        sorted(name for name in common if previous_nodes[name].canonical() != current_nodes[name].canonical())
    )
    previous_models = {item.model_type: item for item in previous.models}
    current_models = {item.model_type: item for item in current.models}
    model_types = previous_models.keys() | current_models.keys()
    changed_model_types = tuple(
        sorted(
            name
            for name in model_types
            if name not in previous_models
            or name not in current_models
            or previous_models[name].canonical() != current_models[name].canonical()
        )
    )
    changed = previous.identity_sha256 != current.identity_sha256
    return ComfyCapabilityDiff(
        previous_identity_sha256=previous.identity_sha256,
        current_identity_sha256=current.identity_sha256,
        state=ComfyCapabilityState.STALE if changed else current.state,
        added_nodes=tuple(sorted(current_nodes.keys() - previous_nodes.keys())),
        removed_nodes=tuple(sorted(previous_nodes.keys() - current_nodes.keys())),
        changed_nodes=changed_nodes,
        changed_model_types=changed_model_types,
        system_changed=(
            previous.comfyui_version != current.comfyui_version
            or previous.python_version != current.python_version
            or previous.system_digest_sha256 != current.system_digest_sha256
            or previous.feature_digest_sha256 != current.feature_digest_sha256
        ),
    )


class CapabilitySnapshotStore:
    """Rebuildable, root-confined, atomic capability snapshot cache."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        if self.root.is_symlink():
            raise ComfyProtocolError("Capability snapshot cache root must not be a symlink")

    def save(self, name: str, snapshot: ComfyCapabilitySnapshot) -> Path:
        safe_name = _safe_cache_name(name)
        target = self._resolve(f"{safe_name}.json")
        document = snapshot.envelope()
        data = canonical_json_bytes(document) + b"\n"
        fd, temporary_name = tempfile.mkstemp(prefix=f".{safe_name}.", suffix=".tmp", dir=self.root)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            temp_path = Path(temporary_name)
            if temp_path.is_symlink():
                raise ComfyProtocolError("Capability snapshot temporary path must not be a symlink")
            os.replace(temp_path, target)
        finally:
            try:
                Path(temporary_name).unlink(missing_ok=True)
            except OSError:
                pass
        return target

    def load(self, name: str) -> ComfyCapabilitySnapshot:
        safe_name = _safe_cache_name(name)
        target = self._resolve(f"{safe_name}.json")
        if target.is_symlink():
            raise ComfyProtocolError("Capability snapshot cache entry must not be a symlink")
        try:
            raw = target.read_bytes()
        except FileNotFoundError as exc:
            raise ComfyProtocolError("Capability snapshot cache entry is missing") from exc
        if len(raw) > 64 * 1024 * 1024:
            raise ComfyProtocolError("Capability snapshot cache entry exceeds the accepted bound")
        try:
            document = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ComfyProtocolError("Capability snapshot cache entry is invalid JSON") from exc
        if not isinstance(document, dict):
            raise ComfyProtocolError("Capability snapshot cache root must be an object")
        payload = parse_envelope(document, expected_schema=_CAPABILITY_SCHEMA)
        return capability_snapshot_from_payload(payload)

    def _resolve(self, relative: str) -> Path:
        candidate = (self.root / relative).resolve(strict=False)
        if not candidate.is_relative_to(self.root):
            raise ComfyProtocolError("Capability snapshot cache path escapes its root")
        return candidate


def capability_snapshot_from_payload(payload: Mapping[str, Any]) -> ComfyCapabilitySnapshot:
    expected = {
        "state", "endpoint", "captured_at", "comfyui_version", "python_version",
        "system_digest_sha256", "feature_digest_sha256", "nodes", "models", "unavailable",
        "identity_sha256",
    }
    if set(payload) != expected:
        raise ComfyProtocolError("Capability snapshot payload fields are invalid")
    try:
        state = ComfyCapabilityState(payload["state"])
    except (ValueError, TypeError) as exc:
        raise ComfyProtocolError("Capability snapshot state is invalid") from exc
    endpoint = _safe_text(payload["endpoint"], "endpoint", 2_048)
    captured_at = _safe_text(payload["captured_at"], "captured_at", 128)
    comfyui_version = _optional_safe_text(payload["comfyui_version"], "comfyui_version", 256)
    python_version = _optional_safe_text(payload["python_version"], "python_version", 1_024)
    system_digest = _optional_digest(payload["system_digest_sha256"], "system_digest_sha256")
    feature_digest = _optional_digest(payload["feature_digest_sha256"], "feature_digest_sha256")
    raw_nodes = payload["nodes"]
    raw_models = payload["models"]
    raw_unavailable = payload["unavailable"]
    if not isinstance(raw_nodes, list) or not isinstance(raw_models, list) or not isinstance(raw_unavailable, list):
        raise ComfyProtocolError("Capability snapshot collection fields are invalid")
    nodes = tuple(_node_from_canonical(item) for item in raw_nodes)
    models = tuple(_model_from_canonical(item) for item in raw_models)
    unavailable = tuple(_safe_text(item, "unavailable token", 256) for item in raw_unavailable)
    identity = _safe_digest(payload["identity_sha256"], "identity_sha256")
    snapshot = ComfyCapabilitySnapshot(
        state=state,
        endpoint=endpoint,
        captured_at=captured_at,
        comfyui_version=comfyui_version,
        python_version=python_version,
        system_digest_sha256=system_digest,
        feature_digest_sha256=feature_digest,
        nodes=nodes,
        models=models,
        unavailable=unavailable,
        identity_sha256=identity,
    )
    if canonical_sha256(snapshot.identity_payload()) != identity:
        raise ComfyProtocolError("Capability snapshot identity digest does not match payload")
    return snapshot


def _normalize_input_section(raw: Any, section: str) -> tuple[ComfyNodeInputSpec, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, dict) or len(raw) > _MAX_INPUTS_PER_SECTION:
        raise ComfyProtocolError(f"Node {section} input section must be a bounded object")
    result: list[ComfyNodeInputSpec] = []
    for name, spec in raw.items():
        safe_name = _safe_identifier(name, f"{section} input name", 256)
        if not isinstance(spec, (list, tuple)) or not 1 <= len(spec) <= 2:
            raise ComfyProtocolError(f"Input {safe_name!r} spec shape is invalid")
        type_decl = spec[0]
        config = spec[1] if len(spec) == 2 else {}
        if not isinstance(config, dict):
            raise ComfyProtocolError(f"Input {safe_name!r} config must be an object")
        type_token: str | None = None
        choices: tuple[str | int | float | bool, ...] = ()
        if isinstance(type_decl, str):
            type_token = _safe_text(type_decl, f"{safe_name} type", 256)
        elif isinstance(type_decl, (list, tuple)):
            if len(type_decl) > 100_000:
                raise ComfyProtocolError(f"Input {safe_name!r} choices exceed accepted bound")
            choices = tuple(_safe_choice(item, safe_name) for item in type_decl)
        else:
            raise ComfyProtocolError(f"Input {safe_name!r} type declaration is invalid")
        minimum = _safe_number_or_none(config.get("min"), f"{safe_name} min")
        maximum = _safe_number_or_none(config.get("max"), f"{safe_name} max")
        step = _safe_number_or_none(config.get("step"), f"{safe_name} step")
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ComfyProtocolError(f"Input {safe_name!r} min exceeds max")
        if step is not None and step <= 0:
            raise ComfyProtocolError(f"Input {safe_name!r} step must be positive")
        result.append(
            ComfyNodeInputSpec(
                name=safe_name,
                section=section,
                type_token=type_token,
                choices=choices,
                minimum=minimum,
                maximum=maximum,
                step=step,
                spec_digest_sha256=canonical_sha256({"spec": list(spec)}),
            )
        )
    return tuple(sorted(result, key=lambda item: item.name))


def _node_from_canonical(raw: Any) -> ComfyNodeDefinition:
    if not isinstance(raw, dict):
        raise ComfyProtocolError("Capability snapshot node must be an object")
    required = tuple(_input_from_canonical(item) for item in raw.get("required_inputs", []))
    optional = tuple(_input_from_canonical(item) for item in raw.get("optional_inputs", []))
    outputs = _normalize_string_array(raw.get("output_types", []), "snapshot output", _MAX_OUTPUTS, 256)
    oil = raw.get("output_is_list", [])
    if not isinstance(oil, list) or len(oil) != len(outputs) or any(not isinstance(v, bool) for v in oil):
        raise ComfyProtocolError("Capability snapshot output_is_list is invalid")
    return ComfyNodeDefinition(
        class_type=_safe_identifier(raw.get("class_type"), "snapshot class_type", 256),
        category=_optional_safe_text(raw.get("category"), "snapshot category", 512),
        required_inputs=required,
        optional_inputs=optional,
        output_types=outputs,
        output_is_list=tuple(oil),
        deprecated=_safe_bool(raw.get("deprecated", False), "deprecated"),
        experimental=_safe_bool(raw.get("experimental", False), "experimental"),
        api_node=_safe_bool(raw.get("api_node", False), "api_node"),
        raw_digest_sha256=_safe_digest(raw.get("raw_digest_sha256"), "raw_digest_sha256"),
    )


def _input_from_canonical(raw: Any) -> ComfyNodeInputSpec:
    if not isinstance(raw, dict):
        raise ComfyProtocolError("Capability snapshot input must be an object")
    choices_raw = raw.get("choices", [])
    if not isinstance(choices_raw, list):
        raise ComfyProtocolError("Capability snapshot choices must be an array")
    return ComfyNodeInputSpec(
        name=_safe_identifier(raw.get("name"), "snapshot input name", 256),
        section=_safe_identifier(raw.get("section"), "snapshot input section", 32),
        type_token=_optional_safe_text(raw.get("type_token"), "snapshot type_token", 256),
        choices=tuple(_safe_choice(item, "snapshot choice") for item in choices_raw),
        minimum=_safe_number_or_none(raw.get("minimum"), "snapshot minimum"),
        maximum=_safe_number_or_none(raw.get("maximum"), "snapshot maximum"),
        step=_safe_number_or_none(raw.get("step"), "snapshot step"),
        spec_digest_sha256=_safe_digest(raw.get("spec_digest_sha256"), "spec_digest_sha256"),
    )


def _model_from_canonical(raw: Any) -> ComfyModelInventory:
    if not isinstance(raw, dict):
        raise ComfyProtocolError("Capability snapshot model inventory must be an object")
    tokens_raw = raw.get("tokens", [])
    if not isinstance(tokens_raw, list):
        raise ComfyProtocolError("Capability snapshot model tokens must be an array")
    tokens = tuple(_safe_model_token(item) for item in tokens_raw)
    inventory = ComfyModelInventory(
        model_type=_safe_identifier(raw.get("model_type"), "snapshot model_type", 128),
        tokens=tokens,
        digest_sha256=_safe_digest(raw.get("digest_sha256"), "model digest"),
    )
    if canonical_sha256({"model_type": inventory.model_type, "tokens": list(inventory.tokens)}) != inventory.digest_sha256:
        raise ComfyProtocolError("Capability snapshot model inventory digest does not match")
    return inventory


def _finalize_model_inventory(item: ComfyModelInventory) -> ComfyModelInventory:
    digest = canonical_sha256({"model_type": item.model_type, "tokens": list(item.tokens)})
    return ComfyModelInventory(model_type=item.model_type, tokens=item.tokens, digest_sha256=digest)


def _normalize_string_array(raw: Any, field_name: str, maximum: int, text_maximum: int) -> tuple[str, ...]:
    if not isinstance(raw, list) or len(raw) > maximum:
        raise ComfyProtocolError(f"{field_name} must be a bounded array")
    return tuple(_safe_text(item, field_name, text_maximum) for item in raw)


def _safe_model_token(value: Any) -> str:
    token = _safe_text(value, "model token", _MAX_TOKEN)
    if "\\" in token or token.startswith("/") or _DRIVE_RE.match(token):
        raise ComfyProtocolError("Model token must be a relative forward-slash token")
    path = PurePosixPath(token)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ComfyProtocolError("Model token contains an unsafe path segment")
    return token


def _safe_cache_name(value: Any) -> str:
    name = _safe_identifier(value, "cache name", 128)
    if name in {".", ".."} or "/" in name or "\\" in name:
        raise ComfyProtocolError("Capability snapshot cache name must be a single safe component")
    return name


def _safe_identifier(value: Any, field_name: str, maximum: int) -> str:
    text = _safe_text(value, field_name, maximum)
    if any(ch in text for ch in ("/", "\\")) or text in {".", ".."}:
        raise ComfyProtocolError(f"{field_name} must be a single identifier token")
    return text


def _safe_text(value: Any, field_name: str, maximum: int) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum or _CONTROL_RE.search(value):
        raise ComfyProtocolError(f"{field_name} must be a non-empty bounded string without controls")
    return value


def _optional_safe_text(value: Any, field_name: str, maximum: int) -> str | None:
    if value is None:
        return None
    return _safe_text(value, field_name, maximum)


def _safe_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ComfyProtocolError(f"{field_name} must be boolean")
    return value


def _safe_choice(value: Any, field_name: str) -> str | int | float | bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return _safe_text(value, f"{field_name} choice", 2_048)
    if isinstance(value, (int, float)):
        if isinstance(value, float) and (value != value or value in {float("inf"), float("-inf")}):
            raise ComfyProtocolError(f"{field_name} choice must be finite")
        return value
    raise ComfyProtocolError(f"{field_name} choice type is unsupported")


def _safe_number_or_none(value: Any, field_name: str) -> int | float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ComfyProtocolError(f"{field_name} must be numeric when present")
    if isinstance(value, float) and (value != value or value in {float("inf"), float("-inf")}):
        raise ComfyProtocolError(f"{field_name} must be finite")
    return value


def _safe_digest(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ComfyProtocolError(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _optional_digest(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    return _safe_digest(value, field_name)
