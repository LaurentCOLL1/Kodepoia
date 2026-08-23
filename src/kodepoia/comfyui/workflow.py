from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from kodepoia.assets.contracts import AssetRevisionId, ReuseScope
from kodepoia.assets.governance import AssetGovernanceOutcome

from .contracts import ComfyCapabilityState
from .errors import ComfyGovernanceError, ComfyProtocolError
from .inventory import ComfyCapabilitySnapshot, ComfyNodeDefinition, ComfyNodeInputSpec
from .serialization import canonical_json_bytes, canonical_sha256, make_envelope, parse_envelope

_WORKFLOW_SCHEMA = "kodepoia.comfy-workflow-definition"
_WORKFLOW_VERSION = 1
_MAX_GRAPH_NODES = 10_000
_MAX_NODE_INPUTS = 4_096
_MAX_PARAMETERS = 4_096
_MAX_SLOTS = 4_096
_MAX_REQUIREMENTS = 4_096
_MAX_CATALOG_FILE_BYTES = 16 * 1024 * 1024
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")

JsonScalar = str | int | float | bool | None


class WorkflowParameterKind(StrEnum):
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ENUM = "enum"
    SEED = "seed"


class ModelResolutionState(StrEnum):
    RESOLVED = "resolved"
    MISSING = "missing"
    AMBIGUOUS = "ambiguous"
    BLOCKED = "blocked"


class ModelProvenanceState(StrEnum):
    VAULT_GOVERNED = "vault_governed"
    EXTERNAL_LOCAL_UNKNOWN = "external_local_unknown"


@dataclass(frozen=True, slots=True)
class WorkflowParameterSpec:
    name: str
    node_id: str
    input_name: str
    kind: WorkflowParameterKind
    minimum: int | float | None = None
    maximum: int | float | None = None
    choices: tuple[JsonScalar, ...] = ()

    def __post_init__(self) -> None:
        _safe_identifier(self.name, "parameter name", 128)
        _safe_identifier(self.node_id, "parameter node_id", 128)
        _safe_identifier(self.input_name, "parameter input_name", 256)
        if self.minimum is not None:
            _safe_number(self.minimum, "parameter minimum")
        if self.maximum is not None:
            _safe_number(self.maximum, "parameter maximum")
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("parameter minimum exceeds maximum")
        if self.kind is WorkflowParameterKind.ENUM and not self.choices:
            raise ValueError("enum parameter requires choices")
        normalized_choices = tuple(_safe_scalar(item, f"parameter {self.name} choice") for item in self.choices)
        if len(set(_choice_identity(item) for item in normalized_choices)) != len(normalized_choices):
            raise ValueError("parameter choices must be unique")
        object.__setattr__(self, "choices", normalized_choices)

    def validate_value(self, value: Any) -> JsonScalar:
        normalized = _safe_scalar(value, f"parameter {self.name}")
        if self.kind is WorkflowParameterKind.STRING:
            if not isinstance(normalized, str):
                raise ComfyGovernanceError(f"Parameter {self.name!r} requires a string")
        elif self.kind in {WorkflowParameterKind.INTEGER, WorkflowParameterKind.SEED}:
            if isinstance(normalized, bool) or not isinstance(normalized, int):
                raise ComfyGovernanceError(f"Parameter {self.name!r} requires an integer")
            if self.kind is WorkflowParameterKind.SEED and normalized < 0:
                raise ComfyGovernanceError(f"Seed parameter {self.name!r} must be non-negative")
        elif self.kind is WorkflowParameterKind.NUMBER:
            if isinstance(normalized, bool) or not isinstance(normalized, (int, float)):
                raise ComfyGovernanceError(f"Parameter {self.name!r} requires a number")
        elif self.kind is WorkflowParameterKind.BOOLEAN:
            if not isinstance(normalized, bool):
                raise ComfyGovernanceError(f"Parameter {self.name!r} requires a boolean")
        elif self.kind is WorkflowParameterKind.ENUM:
            if _choice_identity(normalized) not in {_choice_identity(item) for item in self.choices}:
                raise ComfyGovernanceError(f"Parameter {self.name!r} is outside its declared choices")
        if isinstance(normalized, (int, float)) and not isinstance(normalized, bool):
            if self.minimum is not None and normalized < self.minimum:
                raise ComfyGovernanceError(f"Parameter {self.name!r} is below its declared minimum")
            if self.maximum is not None and normalized > self.maximum:
                raise ComfyGovernanceError(f"Parameter {self.name!r} exceeds its declared maximum")
        if self.choices and self.kind is not WorkflowParameterKind.ENUM:
            if _choice_identity(normalized) not in {_choice_identity(item) for item in self.choices}:
                raise ComfyGovernanceError(f"Parameter {self.name!r} is outside its declared choices")
        return normalized

    def canonical(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "node_id": self.node_id,
            "input_name": self.input_name,
            "kind": self.kind.value,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "choices": list(self.choices),
        }


@dataclass(frozen=True, slots=True)
class WorkflowInputSlot:
    name: str
    node_id: str
    input_name: str
    type_token: str

    def __post_init__(self) -> None:
        _safe_identifier(self.name, "workflow input slot name", 128)
        _safe_identifier(self.node_id, "workflow input slot node_id", 128)
        _safe_identifier(self.input_name, "workflow input slot input_name", 256)
        _safe_identifier(self.type_token, "workflow input slot type", 256)

    def canonical(self) -> dict[str, str]:
        return {
            "name": self.name,
            "node_id": self.node_id,
            "input_name": self.input_name,
            "type_token": self.type_token,
        }


@dataclass(frozen=True, slots=True)
class WorkflowOutputSlot:
    name: str
    node_id: str
    output_index: int
    type_token: str

    def __post_init__(self) -> None:
        _safe_identifier(self.name, "workflow output slot name", 128)
        _safe_identifier(self.node_id, "workflow output slot node_id", 128)
        if isinstance(self.output_index, bool) or not isinstance(self.output_index, int) or self.output_index < 0:
            raise ValueError("workflow output_index must be a non-negative integer")
        _safe_identifier(self.type_token, "workflow output slot type", 256)

    def canonical(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "node_id": self.node_id,
            "output_index": self.output_index,
            "type_token": self.type_token,
        }


@dataclass(frozen=True, slots=True)
class ModelRequirement:
    requirement_id: str
    model_type: str
    node_id: str
    input_name: str
    accepted_tokens: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _safe_identifier(self.requirement_id, "model requirement id", 128)
        _safe_identifier(self.model_type, "model type", 128)
        _safe_identifier(self.node_id, "model requirement node_id", 128)
        _safe_identifier(self.input_name, "model requirement input_name", 256)
        tokens = tuple(sorted(_safe_model_token(item) for item in self.accepted_tokens))
        if len(set(tokens)) != len(tokens):
            raise ValueError("accepted model tokens must be unique")
        object.__setattr__(self, "accepted_tokens", tokens)

    def canonical(self) -> dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "model_type": self.model_type,
            "node_id": self.node_id,
            "input_name": self.input_name,
            "accepted_tokens": list(self.accepted_tokens),
        }


@dataclass(frozen=True, slots=True)
class VaultModelEvidence:
    revision_id: AssetRevisionId
    content_sha256: str
    reuse_scope: ReuseScope
    governance_outcome: AssetGovernanceOutcome
    license_token: str

    def __post_init__(self) -> None:
        if not _HEX64_RE.fullmatch(self.content_sha256):
            raise ValueError("Vault model content_sha256 must be lowercase SHA-256")
        if not isinstance(self.license_token, str) or not self.license_token.strip() or len(self.license_token) > 512:
            raise ValueError("Vault model license_token must be a bounded non-empty string")

    @property
    def exportable(self) -> bool:
        return (
            self.reuse_scope is ReuseScope.EXPORTABLE
            and self.governance_outcome is not AssetGovernanceOutcome.BLOCK
        )

    def canonical(self) -> dict[str, Any]:
        return {
            "revision_id": str(self.revision_id),
            "content_sha256": self.content_sha256,
            "reuse_scope": self.reuse_scope.value,
            "governance_outcome": self.governance_outcome.value,
            "license_token": self.license_token,
            "exportable": self.exportable,
        }


@dataclass(frozen=True, slots=True)
class ModelResolution:
    requirement_id: str
    model_type: str
    state: ModelResolutionState
    candidates: tuple[str, ...]
    selected_token: str | None
    provenance_state: ModelProvenanceState
    vault_evidence: VaultModelEvidence | None

    @property
    def exportable(self) -> bool:
        return self.vault_evidence.exportable if self.vault_evidence is not None else False

    @property
    def license_token(self) -> str:
        return self.vault_evidence.license_token if self.vault_evidence is not None else "NOASSERTION"

    def canonical(self) -> dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "model_type": self.model_type,
            "state": self.state.value,
            "candidates": list(self.candidates),
            "selected_token": self.selected_token,
            "provenance_state": self.provenance_state.value,
            "vault_evidence": self.vault_evidence.canonical() if self.vault_evidence is not None else None,
            "license_token": self.license_token,
            "exportable": self.exportable,
        }


@dataclass(frozen=True, slots=True)
class ModelResolutionSet:
    capability_identity_sha256: str
    resolutions: tuple[ModelResolution, ...]
    digest_sha256: str

    @property
    def ready(self) -> bool:
        return all(item.state is ModelResolutionState.RESOLVED for item in self.resolutions)

    def canonical_without_digest(self) -> dict[str, Any]:
        return {
            "capability_identity_sha256": self.capability_identity_sha256,
            "resolutions": [item.canonical() for item in self.resolutions],
        }

    def canonical(self) -> dict[str, Any]:
        payload = self.canonical_without_digest()
        payload["digest_sha256"] = self.digest_sha256
        payload["ready"] = self.ready
        return payload


@dataclass(frozen=True, slots=True)
class WorkflowDefinition:
    name: str
    revision: int
    graph_json: str
    parameters: tuple[WorkflowParameterSpec, ...]
    input_slots: tuple[WorkflowInputSlot, ...]
    output_slots: tuple[WorkflowOutputSlot, ...]
    model_requirements: tuple[ModelRequirement, ...]
    allowed_node_classes: tuple[str, ...]
    definition_id: str
    definition_digest_sha256: str

    @classmethod
    def create(
        cls,
        *,
        name: str,
        revision: int,
        graph: Mapping[str, Any],
        parameters: Sequence[WorkflowParameterSpec] = (),
        input_slots: Sequence[WorkflowInputSlot] = (),
        output_slots: Sequence[WorkflowOutputSlot] = (),
        model_requirements: Sequence[ModelRequirement] = (),
        allowed_node_classes: Sequence[str] = (),
    ) -> "WorkflowDefinition":
        safe_name = _safe_text(name, "workflow name", 256)
        if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
            raise ValueError("workflow revision must be an integer >= 1")
        normalized_graph = _normalize_graph(graph)
        parameter_tuple = _unique_by_name(parameters, "parameter", lambda item: item.name, _MAX_PARAMETERS)
        input_tuple = _unique_by_name(input_slots, "input slot", lambda item: item.name, _MAX_SLOTS)
        output_tuple = _unique_by_name(output_slots, "output slot", lambda item: item.name, _MAX_SLOTS)
        requirement_tuple = _unique_by_name(
            model_requirements,
            "model requirement",
            lambda item: item.requirement_id,
            _MAX_REQUIREMENTS,
        )
        allowed = tuple(sorted({_safe_identifier(item, "allowed node class", 256) for item in allowed_node_classes}))
        _validate_marker_declarations(normalized_graph, parameter_tuple, input_tuple, requirement_tuple)
        payload = {
            "name": safe_name,
            "revision": revision,
            "graph": normalized_graph,
            "parameters": [item.canonical() for item in parameter_tuple],
            "input_slots": [item.canonical() for item in input_tuple],
            "output_slots": [item.canonical() for item in output_tuple],
            "model_requirements": [item.canonical() for item in requirement_tuple],
            "allowed_node_classes": list(allowed),
        }
        digest = canonical_sha256(payload)
        return cls(
            name=safe_name,
            revision=revision,
            graph_json=canonical_json_bytes(normalized_graph).decode("utf-8"),
            parameters=parameter_tuple,
            input_slots=input_tuple,
            output_slots=output_tuple,
            model_requirements=requirement_tuple,
            allowed_node_classes=allowed,
            definition_id=f"wf_{digest[:32]}",
            definition_digest_sha256=digest,
        )

    def graph(self) -> dict[str, Any]:
        data = json.loads(self.graph_json)
        if not isinstance(data, dict):
            raise RuntimeError("canonical workflow graph is not an object")
        return data

    def identity_payload(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "revision": self.revision,
            "graph": self.graph(),
            "parameters": [item.canonical() for item in self.parameters],
            "input_slots": [item.canonical() for item in self.input_slots],
            "output_slots": [item.canonical() for item in self.output_slots],
            "model_requirements": [item.canonical() for item in self.model_requirements],
            "allowed_node_classes": list(self.allowed_node_classes),
        }

    def payload(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload["definition_id"] = self.definition_id
        payload["definition_digest_sha256"] = self.definition_digest_sha256
        return payload

    def envelope(self) -> dict[str, Any]:
        return make_envelope(schema=_WORKFLOW_SCHEMA, version=_WORKFLOW_VERSION, payload=self.payload())


@dataclass(frozen=True, slots=True)
class WorkflowValidationEvidence:
    definition_id: str
    definition_digest_sha256: str
    capability_identity_sha256: str
    node_definition_digests: tuple[tuple[str, str], ...]
    digest_sha256: str

    def canonical(self) -> dict[str, Any]:
        return {
            "definition_id": self.definition_id,
            "definition_digest_sha256": self.definition_digest_sha256,
            "capability_identity_sha256": self.capability_identity_sha256,
            "node_definition_digests": [list(item) for item in self.node_definition_digests],
            "digest_sha256": self.digest_sha256,
        }


@dataclass(frozen=True, slots=True)
class WorkflowInstance:
    definition_id: str
    definition_digest_sha256: str
    capability_identity_sha256: str
    model_resolution_digest_sha256: str
    parameter_values: tuple[tuple[str, JsonScalar], ...]
    input_bindings: tuple[tuple[str, JsonScalar], ...]
    prompt_json: str
    instance_digest_sha256: str

    def prompt(self) -> dict[str, Any]:
        data = json.loads(self.prompt_json)
        if not isinstance(data, dict):
            raise RuntimeError("canonical workflow prompt is not an object")
        return data

    def canonical(self) -> dict[str, Any]:
        return {
            "definition_id": self.definition_id,
            "definition_digest_sha256": self.definition_digest_sha256,
            "capability_identity_sha256": self.capability_identity_sha256,
            "model_resolution_digest_sha256": self.model_resolution_digest_sha256,
            "parameter_values": {key: value for key, value in self.parameter_values},
            "input_bindings": {key: value for key, value in self.input_bindings},
            "prompt": self.prompt(),
            "instance_digest_sha256": self.instance_digest_sha256,
        }


class GovernedModelResolver:
    """Resolve declared logical requirements against one accepted R9.3 snapshot only."""

    def resolve(
        self,
        definition: WorkflowDefinition,
        snapshot: ComfyCapabilitySnapshot,
        *,
        selections: Mapping[str, str] | None = None,
        vault_evidence: Mapping[tuple[str, str], VaultModelEvidence] | None = None,
    ) -> ModelResolutionSet:
        if snapshot.state is not ComfyCapabilityState.CURRENT:
            raise ComfyGovernanceError("Model resolution requires a CURRENT capability snapshot")
        selected = dict(selections or {})
        evidence = dict(vault_evidence or {})
        requirement_ids = {item.requirement_id for item in definition.model_requirements}
        unknown_selections = set(selected) - requirement_ids
        if unknown_selections:
            raise ComfyGovernanceError("Model selection contains undeclared requirement IDs")
        inventories = {item.model_type: item.tokens for item in snapshot.models}
        resolutions: list[ModelResolution] = []
        for requirement in definition.model_requirements:
            inventory = inventories.get(requirement.model_type, ())
            if requirement.accepted_tokens:
                candidates = tuple(item for item in inventory if item in set(requirement.accepted_tokens))
            else:
                candidates = tuple(inventory)
            requested = selected.get(requirement.requirement_id)
            state: ModelResolutionState
            chosen: str | None = None
            if requested is not None:
                requested = _safe_model_token(requested)
                if requested in candidates:
                    state = ModelResolutionState.RESOLVED
                    chosen = requested
                else:
                    state = ModelResolutionState.BLOCKED
            elif not candidates:
                state = ModelResolutionState.MISSING
            elif len(candidates) == 1:
                state = ModelResolutionState.RESOLVED
                chosen = candidates[0]
            else:
                state = ModelResolutionState.AMBIGUOUS
            governed = evidence.get((requirement.model_type, chosen)) if chosen is not None else None
            resolutions.append(
                ModelResolution(
                    requirement_id=requirement.requirement_id,
                    model_type=requirement.model_type,
                    state=state,
                    candidates=candidates,
                    selected_token=chosen,
                    provenance_state=(
                        ModelProvenanceState.VAULT_GOVERNED
                        if governed is not None
                        else ModelProvenanceState.EXTERNAL_LOCAL_UNKNOWN
                    ),
                    vault_evidence=governed,
                )
            )
        ordered = tuple(sorted(resolutions, key=lambda item: item.requirement_id))
        payload = {
            "capability_identity_sha256": snapshot.identity_sha256,
            "resolutions": [item.canonical() for item in ordered],
        }
        return ModelResolutionSet(
            capability_identity_sha256=snapshot.identity_sha256,
            resolutions=ordered,
            digest_sha256=canonical_sha256(payload),
        )


class WorkflowValidator:
    """Validate immutable R9.4 templates and instantiate declared scalar/model slots only."""

    def validate(
        self,
        definition: WorkflowDefinition,
        snapshot: ComfyCapabilitySnapshot,
    ) -> WorkflowValidationEvidence:
        if snapshot.state is not ComfyCapabilityState.CURRENT:
            raise ComfyGovernanceError("Workflow validation requires a CURRENT capability snapshot")
        if canonical_sha256(definition.identity_payload()) != definition.definition_digest_sha256:
            raise ComfyGovernanceError("Workflow definition digest does not match its canonical identity")
        if definition.definition_id != f"wf_{definition.definition_digest_sha256[:32]}":
            raise ComfyGovernanceError("Workflow definition ID does not match its digest")
        graph = definition.graph()
        nodes = {item.class_type: item for item in snapshot.nodes}
        graph_classes = {node["class_type"] for node in graph.values()}
        if not graph_classes.issubset(set(definition.allowed_node_classes)):
            raise ComfyGovernanceError("Workflow graph contains a node class outside its allowlist")
        evidence: list[tuple[str, str]] = []
        for node_id, node in graph.items():
            class_type = node["class_type"]
            capability = nodes.get(class_type)
            if capability is None:
                raise ComfyGovernanceError(f"Workflow node class {class_type!r} is absent from capability snapshot")
            evidence.append((node_id, capability.raw_digest_sha256))
            self._validate_node(definition, node_id, node, capability, graph, nodes)
        self._validate_slots(definition, graph, nodes)
        evidence_tuple = tuple(sorted(evidence))
        payload = {
            "definition_id": definition.definition_id,
            "definition_digest_sha256": definition.definition_digest_sha256,
            "capability_identity_sha256": snapshot.identity_sha256,
            "node_definition_digests": [list(item) for item in evidence_tuple],
        }
        return WorkflowValidationEvidence(
            definition_id=definition.definition_id,
            definition_digest_sha256=definition.definition_digest_sha256,
            capability_identity_sha256=snapshot.identity_sha256,
            node_definition_digests=evidence_tuple,
            digest_sha256=canonical_sha256(payload),
        )

    def instantiate(
        self,
        definition: WorkflowDefinition,
        snapshot: ComfyCapabilitySnapshot,
        resolution_set: ModelResolutionSet,
        *,
        parameters: Mapping[str, Any],
        input_bindings: Mapping[str, Any] | None = None,
    ) -> WorkflowInstance:
        self.validate(definition, snapshot)
        if resolution_set.capability_identity_sha256 != snapshot.identity_sha256:
            raise ComfyGovernanceError("Model resolutions were produced against a different capability snapshot")
        if canonical_sha256(resolution_set.canonical_without_digest()) != resolution_set.digest_sha256:
            raise ComfyGovernanceError("Model resolution set digest does not match its evidence")
        if not resolution_set.ready:
            raise ComfyGovernanceError("Workflow instance requires every model requirement to be RESOLVED")
        specs = {item.name: item for item in definition.parameters}
        if set(parameters) != set(specs):
            raise ComfyGovernanceError("Workflow parameters must exactly match declared parameter names")
        normalized_params = {
            name: specs[name].validate_value(value)
            for name, value in parameters.items()
        }
        input_specs = {item.name: item for item in definition.input_slots}
        supplied_inputs = dict(input_bindings or {})
        if set(supplied_inputs) != set(input_specs):
            raise ComfyGovernanceError("Workflow input bindings must exactly match declared input slots")
        normalized_inputs = {
            name: _safe_scalar(value, f"workflow input {name}")
            for name, value in supplied_inputs.items()
        }
        resolutions = {item.requirement_id: item for item in resolution_set.resolutions}
        if set(resolutions) != {item.requirement_id for item in definition.model_requirements}:
            raise ComfyGovernanceError("Model resolution set does not match workflow requirements")
        prompt = definition.graph()
        for spec in definition.parameters:
            prompt[spec.node_id]["inputs"][spec.input_name] = normalized_params[spec.name]
        for slot in definition.input_slots:
            prompt[slot.node_id]["inputs"][slot.input_name] = normalized_inputs[slot.name]
        for requirement in definition.model_requirements:
            resolution = resolutions[requirement.requirement_id]
            if resolution.state is not ModelResolutionState.RESOLVED or resolution.selected_token is None:
                raise ComfyGovernanceError("Unresolved model requirement cannot be instantiated")
            prompt[requirement.node_id]["inputs"][requirement.input_name] = resolution.selected_token
        if _contains_marker(prompt):
            raise ComfyGovernanceError("Workflow instance retains an unresolved internal marker")
        self._validate_concrete_prompt(prompt, snapshot)
        ordered_params = tuple(sorted(normalized_params.items()))
        ordered_inputs = tuple(sorted(normalized_inputs.items()))
        payload = {
            "definition_id": definition.definition_id,
            "definition_digest_sha256": definition.definition_digest_sha256,
            "capability_identity_sha256": snapshot.identity_sha256,
            "model_resolution_digest_sha256": resolution_set.digest_sha256,
            "parameter_values": {key: value for key, value in ordered_params},
            "input_bindings": {key: value for key, value in ordered_inputs},
            "prompt": prompt,
        }
        digest = canonical_sha256(payload)
        return WorkflowInstance(
            definition_id=definition.definition_id,
            definition_digest_sha256=definition.definition_digest_sha256,
            capability_identity_sha256=snapshot.identity_sha256,
            model_resolution_digest_sha256=resolution_set.digest_sha256,
            parameter_values=ordered_params,
            input_bindings=ordered_inputs,
            prompt_json=canonical_json_bytes(prompt).decode("utf-8"),
            instance_digest_sha256=digest,
        )

    def _validate_node(
        self,
        definition: WorkflowDefinition,
        node_id: str,
        node: dict[str, Any],
        capability: ComfyNodeDefinition,
        graph: Mapping[str, Any],
        nodes: Mapping[str, ComfyNodeDefinition],
    ) -> None:
        specs = {item.name: item for item in (*capability.required_inputs, *capability.optional_inputs)}
        inputs = node["inputs"]
        missing = {item.name for item in capability.required_inputs} - set(inputs)
        if missing:
            raise ComfyGovernanceError(f"Workflow node {node_id!r} omits required inputs: {sorted(missing)!r}")
        unknown = set(inputs) - set(specs)
        if unknown:
            raise ComfyGovernanceError(f"Workflow node {node_id!r} contains unknown inputs: {sorted(unknown)!r}")
        for input_name, value in inputs.items():
            spec = specs[input_name]
            marker = _marker(value)
            if marker is not None:
                kind, name = marker
                if kind == "param":
                    parameter = next(
                        (item for item in definition.parameters if item.name == name),
                        None,
                    )
                    if parameter is None or parameter.node_id != node_id or parameter.input_name != input_name:
                        raise ComfyGovernanceError("Parameter marker does not match its declared target")
                    _validate_parameter_against_capability(parameter, spec)
                elif kind == "input":
                    slot = next((item for item in definition.input_slots if item.name == name), None)
                    if slot is None or slot.node_id != node_id or slot.input_name != input_name:
                        raise ComfyGovernanceError("Input marker does not match its declared target")
                    if spec.type_token is not None and spec.type_token != slot.type_token:
                        raise ComfyGovernanceError("Workflow input slot type conflicts with capability metadata")
                elif kind == "model":
                    requirement = next(
                        (item for item in definition.model_requirements if item.requirement_id == name),
                        None,
                    )
                    if requirement is None or requirement.node_id != node_id or requirement.input_name != input_name:
                        raise ComfyGovernanceError("Model marker does not match its declared target")
                continue
            if _is_link(value):
                source_id, output_index = value
                source = graph.get(source_id)
                if source is None:
                    raise ComfyGovernanceError("Workflow link refers to a missing source node")
                source_capability = nodes.get(source["class_type"])
                if source_capability is None or output_index >= len(source_capability.output_types):
                    raise ComfyGovernanceError("Workflow link refers to an invalid output slot")
                if spec.choices:
                    raise ComfyGovernanceError("Workflow cannot feed a node link into a scalar choice input")
                source_type = source_capability.output_types[output_index]
                if spec.type_token is not None and source_type != spec.type_token:
                    raise ComfyGovernanceError(
                        f"Workflow link type mismatch: {source_type!r} -> {spec.type_token!r}"
                    )
                continue
            _validate_literal_against_capability(value, spec)

    def _validate_slots(
        self,
        definition: WorkflowDefinition,
        graph: Mapping[str, Any],
        nodes: Mapping[str, ComfyNodeDefinition],
    ) -> None:
        for output in definition.output_slots:
            node = graph.get(output.node_id)
            if node is None:
                raise ComfyGovernanceError("Workflow output slot refers to a missing node")
            capability = nodes.get(node["class_type"])
            if capability is None or output.output_index >= len(capability.output_types):
                raise ComfyGovernanceError("Workflow output slot refers to an invalid output index")
            if capability.output_types[output.output_index] != output.type_token:
                raise ComfyGovernanceError("Workflow output slot type conflicts with capability metadata")

    def _validate_concrete_prompt(
        self,
        prompt: Mapping[str, Any],
        snapshot: ComfyCapabilitySnapshot,
    ) -> None:
        nodes = {item.class_type: item for item in snapshot.nodes}
        for node_id, node in prompt.items():
            capability = nodes[node["class_type"]]
            specs = {item.name: item for item in (*capability.required_inputs, *capability.optional_inputs)}
            for input_name, value in node["inputs"].items():
                if _is_link(value):
                    continue
                _validate_literal_against_capability(value, specs[input_name])


class WorkflowCatalog:
    """Tamper-checked catalog of explicit files; no recursive workflow discovery."""

    def __init__(self, definitions: Sequence[WorkflowDefinition] = ()) -> None:
        self._definitions: dict[str, WorkflowDefinition] = {}
        for definition in definitions:
            self.add(definition)

    def add(self, definition: WorkflowDefinition) -> None:
        existing = self._definitions.get(definition.definition_id)
        if existing is not None and existing.definition_digest_sha256 != definition.definition_digest_sha256:
            raise ComfyGovernanceError("Workflow definition ID collision")
        self._definitions[definition.definition_id] = definition

    def get(self, definition_id: str) -> WorkflowDefinition:
        safe_id = _safe_identifier(definition_id, "workflow definition id", 64)
        try:
            return self._definitions[safe_id]
        except KeyError as exc:
            raise KeyError(f"Unknown workflow definition: {safe_id}") from exc

    def definitions(self) -> tuple[WorkflowDefinition, ...]:
        return tuple(sorted(self._definitions.values(), key=lambda item: item.definition_id))

    @classmethod
    def load_files(cls, root: Path | str, filenames: Sequence[str]) -> "WorkflowCatalog":
        root_path = Path(root).resolve()
        if root_path.is_symlink():
            raise ComfyProtocolError("Workflow catalog root must not be a symlink")
        definitions: list[WorkflowDefinition] = []
        seen: set[str] = set()
        for filename in filenames:
            if not isinstance(filename, str) or not _SAFE_NAME_RE.fullmatch(filename) or not filename.endswith(".json"):
                raise ComfyProtocolError("Workflow catalog filenames must be safe explicit JSON basenames")
            if filename in seen:
                raise ComfyProtocolError("Workflow catalog filename list contains duplicates")
            seen.add(filename)
            path = (root_path / filename).resolve(strict=False)
            if not path.is_relative_to(root_path) or path.is_symlink():
                raise ComfyProtocolError("Workflow catalog path escapes root or is a symlink")
            try:
                raw = path.read_bytes()
            except FileNotFoundError as exc:
                raise ComfyProtocolError(f"Workflow catalog entry {filename!r} is missing") from exc
            if len(raw) > _MAX_CATALOG_FILE_BYTES:
                raise ComfyProtocolError("Workflow catalog entry exceeds the accepted byte bound")
            try:
                document = json.loads(raw)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ComfyProtocolError("Workflow catalog entry is invalid JSON") from exc
            if not isinstance(document, dict):
                raise ComfyProtocolError("Workflow catalog document root must be an object")
            payload = parse_envelope(document, expected_schema=_WORKFLOW_SCHEMA)
            definitions.append(workflow_definition_from_payload(payload))
        return cls(definitions)


def workflow_definition_from_payload(payload: Mapping[str, Any]) -> WorkflowDefinition:
    expected = {
        "name",
        "revision",
        "graph",
        "parameters",
        "input_slots",
        "output_slots",
        "model_requirements",
        "allowed_node_classes",
        "definition_id",
        "definition_digest_sha256",
    }
    if set(payload) != expected:
        raise ComfyProtocolError("Workflow definition payload fields are invalid")
    raw_parameters = _require_list(payload["parameters"], "workflow parameters", _MAX_PARAMETERS)
    raw_inputs = _require_list(payload["input_slots"], "workflow input slots", _MAX_SLOTS)
    raw_outputs = _require_list(payload["output_slots"], "workflow output slots", _MAX_SLOTS)
    raw_requirements = _require_list(payload["model_requirements"], "model requirements", _MAX_REQUIREMENTS)
    raw_allowed = _require_list(payload["allowed_node_classes"], "allowed node classes", _MAX_GRAPH_NODES)
    try:
        definition = WorkflowDefinition.create(
            name=payload["name"],
            revision=payload["revision"],
            graph=_require_mapping(payload["graph"], "workflow graph"),
            parameters=tuple(_parameter_from_dict(item) for item in raw_parameters),
            input_slots=tuple(_input_slot_from_dict(item) for item in raw_inputs),
            output_slots=tuple(_output_slot_from_dict(item) for item in raw_outputs),
            model_requirements=tuple(_requirement_from_dict(item) for item in raw_requirements),
            allowed_node_classes=tuple(_safe_identifier(item, "allowed node class", 256) for item in raw_allowed),
        )
    except (TypeError, ValueError) as exc:
        raise ComfyProtocolError("Workflow definition payload contains invalid typed fields") from exc
    if payload["definition_id"] != definition.definition_id:
        raise ComfyProtocolError("Workflow definition ID does not match canonical payload")
    if payload["definition_digest_sha256"] != definition.definition_digest_sha256:
        raise ComfyProtocolError("Workflow definition digest does not match canonical payload")
    return definition


def _normalize_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(graph, Mapping) or len(graph) > _MAX_GRAPH_NODES:
        raise ValueError("workflow graph must be a bounded object")
    result: dict[str, Any] = {}
    for node_id, raw_node in graph.items():
        safe_id = _safe_identifier(node_id, "workflow node_id", 128)
        if not isinstance(raw_node, Mapping) or set(raw_node) != {"class_type", "inputs"}:
            raise ValueError("workflow nodes must contain exactly class_type and inputs")
        class_type = _safe_identifier(raw_node["class_type"], "workflow node class_type", 256)
        raw_inputs = raw_node["inputs"]
        if not isinstance(raw_inputs, Mapping) or len(raw_inputs) > _MAX_NODE_INPUTS:
            raise ValueError("workflow node inputs must be a bounded object")
        inputs: dict[str, Any] = {}
        for input_name, value in raw_inputs.items():
            safe_input = _safe_identifier(input_name, "workflow input name", 256)
            inputs[safe_input] = _normalize_graph_value(value)
        result[safe_id] = {"class_type": class_type, "inputs": inputs}
    return {key: result[key] for key in sorted(result)}


def _normalize_graph_value(value: Any) -> Any:
    marker = _marker(value)
    if marker is not None:
        kind, name = marker
        return {f"${kind}": name}
    if _is_link(value):
        source, index = value
        return [source, index]
    return _safe_scalar(value, "workflow graph literal")


def _validate_marker_declarations(
    graph: Mapping[str, Any],
    parameters: Sequence[WorkflowParameterSpec],
    input_slots: Sequence[WorkflowInputSlot],
    requirements: Sequence[ModelRequirement],
) -> None:
    declared: dict[tuple[str, str], tuple[str, str]] = {}
    for item in parameters:
        key = (item.node_id, item.input_name)
        if key in declared:
            raise ValueError("workflow target is declared more than once")
        declared[key] = ("param", item.name)
    for item in input_slots:
        key = (item.node_id, item.input_name)
        if key in declared:
            raise ValueError("workflow target is declared more than once")
        declared[key] = ("input", item.name)
    for item in requirements:
        key = (item.node_id, item.input_name)
        if key in declared:
            raise ValueError("workflow target is declared more than once")
        declared[key] = ("model", item.requirement_id)
    found: dict[tuple[str, str], tuple[str, str]] = {}
    for node_id, node in graph.items():
        for input_name, value in node["inputs"].items():
            marker = _marker(value)
            if marker is not None:
                found[(node_id, input_name)] = marker
    if found != declared:
        raise ValueError("workflow markers must exactly match declared parameter/input/model targets")


def _validate_parameter_against_capability(parameter: WorkflowParameterSpec, spec: ComfyNodeInputSpec) -> None:
    if parameter.minimum is not None and spec.minimum is not None and parameter.minimum < spec.minimum:
        raise ComfyGovernanceError("Parameter minimum is wider than capability minimum")
    if parameter.maximum is not None and spec.maximum is not None and parameter.maximum > spec.maximum:
        raise ComfyGovernanceError("Parameter maximum is wider than capability maximum")
    if spec.choices and parameter.choices:
        allowed = {_choice_identity(item) for item in spec.choices}
        if not {_choice_identity(item) for item in parameter.choices}.issubset(allowed):
            raise ComfyGovernanceError("Parameter choices exceed capability choices")
    if spec.type_token is None:
        if parameter.kind is not WorkflowParameterKind.ENUM:
            raise ComfyGovernanceError("Choice-based capability input requires an ENUM parameter")
        return
    mapping = {
        "INT": {WorkflowParameterKind.INTEGER, WorkflowParameterKind.SEED},
        "FLOAT": {WorkflowParameterKind.NUMBER, WorkflowParameterKind.INTEGER},
        "STRING": {WorkflowParameterKind.STRING},
        "BOOLEAN": {WorkflowParameterKind.BOOLEAN},
        "BOOL": {WorkflowParameterKind.BOOLEAN},
    }
    accepted = mapping.get(spec.type_token)
    if accepted is not None and parameter.kind not in accepted:
        raise ComfyGovernanceError("Parameter kind conflicts with capability input type")


def _validate_literal_against_capability(value: Any, spec: ComfyNodeInputSpec) -> None:
    scalar = _safe_scalar(value, f"literal for {spec.name}")
    if spec.choices:
        if _choice_identity(scalar) not in {_choice_identity(item) for item in spec.choices}:
            raise ComfyGovernanceError(f"Literal for {spec.name!r} is outside capability choices")
        return
    token = spec.type_token
    if token == "INT" and (isinstance(scalar, bool) or not isinstance(scalar, int)):
        raise ComfyGovernanceError(f"Literal for {spec.name!r} must be INT")
    if token == "FLOAT" and (isinstance(scalar, bool) or not isinstance(scalar, (int, float))):
        raise ComfyGovernanceError(f"Literal for {spec.name!r} must be FLOAT")
    if token in {"BOOLEAN", "BOOL"} and not isinstance(scalar, bool):
        raise ComfyGovernanceError(f"Literal for {spec.name!r} must be boolean")
    if token == "STRING" and not isinstance(scalar, str):
        raise ComfyGovernanceError(f"Literal for {spec.name!r} must be string")
    if isinstance(scalar, (int, float)) and not isinstance(scalar, bool):
        if spec.minimum is not None and scalar < spec.minimum:
            raise ComfyGovernanceError(f"Literal for {spec.name!r} is below capability minimum")
        if spec.maximum is not None and scalar > spec.maximum:
            raise ComfyGovernanceError(f"Literal for {spec.name!r} exceeds capability maximum")


def _marker(value: Any) -> tuple[str, str] | None:
    if not isinstance(value, Mapping) or len(value) != 1:
        return None
    key, raw_name = next(iter(value.items()))
    if key not in {"$param", "$input", "$model"}:
        return None
    name = _safe_identifier(raw_name, "workflow marker name", 128)
    return key[1:], name


def _contains_marker(value: Any) -> bool:
    if _marker(value) is not None:
        return True
    if isinstance(value, Mapping):
        return any(_contains_marker(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_marker(item) for item in value)
    return False


def _is_link(value: Any) -> bool:
    return (
        isinstance(value, (list, tuple))
        and len(value) == 2
        and isinstance(value[0], str)
        and bool(value[0])
        and isinstance(value[1], int)
        and not isinstance(value[1], bool)
        and value[1] >= 0
    )


def _safe_scalar(value: Any, field_name: str) -> JsonScalar:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value != value or value in {float("inf"), float("-inf")}:
            raise ValueError(f"{field_name} must be finite")
        return value
    if isinstance(value, str):
        return _safe_text(value, field_name, 16_384)
    raise ComfyGovernanceError(f"{field_name} must be a JSON scalar; graph fragments are not accepted")


def _safe_number(value: Any, field_name: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number")
    if isinstance(value, float) and (value != value or value in {float("inf"), float("-inf")}):
        raise ValueError(f"{field_name} must be finite")
    return value


def _safe_identifier(value: Any, field_name: str, maximum: int) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum or _CONTROL_RE.search(value):
        raise ValueError(f"{field_name} must be a bounded non-empty string without controls")
    return value


def _safe_text(value: Any, field_name: str, maximum: int) -> str:
    return _safe_identifier(value, field_name, maximum)


def _safe_model_token(value: Any) -> str:
    token = _safe_identifier(value, "model token", 1_024)
    if token.startswith(("/", "\\")) or "\\" in token or re.match(r"^[A-Za-z]:", token):
        raise ValueError("model token must be a relative ComfyUI inventory token")
    if any(part in {"", ".", ".."} for part in token.split("/")):
        raise ValueError("model token contains unsafe path segments")
    return token


def _choice_identity(value: JsonScalar) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _unique_by_name(items: Sequence[Any], label: str, key: Any, maximum: int) -> tuple[Any, ...]:
    if len(items) > maximum:
        raise ValueError(f"{label} count exceeds accepted bound")
    ordered = tuple(sorted(items, key=key))
    keys = [key(item) for item in ordered]
    if len(set(keys)) != len(keys):
        raise ValueError(f"duplicate {label} names are not allowed")
    return ordered


def _require_list(value: Any, field_name: str, maximum: int) -> list[Any]:
    if not isinstance(value, list) or len(value) > maximum:
        raise ComfyProtocolError(f"{field_name} must be a bounded array")
    return value


def _require_mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ComfyProtocolError(f"{field_name} must be an object")
    return value


def _parameter_from_dict(raw: Any) -> WorkflowParameterSpec:
    if not isinstance(raw, dict) or set(raw) != {"name", "node_id", "input_name", "kind", "minimum", "maximum", "choices"}:
        raise ComfyProtocolError("Workflow parameter record fields are invalid")
    try:
        kind = WorkflowParameterKind(raw["kind"])
    except (TypeError, ValueError) as exc:
        raise ComfyProtocolError("Workflow parameter kind is invalid") from exc
    choices = raw["choices"]
    if not isinstance(choices, list):
        raise ComfyProtocolError("Workflow parameter choices must be an array")
    return WorkflowParameterSpec(
        name=raw["name"],
        node_id=raw["node_id"],
        input_name=raw["input_name"],
        kind=kind,
        minimum=raw["minimum"],
        maximum=raw["maximum"],
        choices=tuple(choices),
    )


def _input_slot_from_dict(raw: Any) -> WorkflowInputSlot:
    if not isinstance(raw, dict) or set(raw) != {"name", "node_id", "input_name", "type_token"}:
        raise ComfyProtocolError("Workflow input slot fields are invalid")
    return WorkflowInputSlot(raw["name"], raw["node_id"], raw["input_name"], raw["type_token"])


def _output_slot_from_dict(raw: Any) -> WorkflowOutputSlot:
    if not isinstance(raw, dict) or set(raw) != {"name", "node_id", "output_index", "type_token"}:
        raise ComfyProtocolError("Workflow output slot fields are invalid")
    return WorkflowOutputSlot(raw["name"], raw["node_id"], raw["output_index"], raw["type_token"])


def _requirement_from_dict(raw: Any) -> ModelRequirement:
    if not isinstance(raw, dict) or set(raw) != {"requirement_id", "model_type", "node_id", "input_name", "accepted_tokens"}:
        raise ComfyProtocolError("Model requirement fields are invalid")
    tokens = raw["accepted_tokens"]
    if not isinstance(tokens, list):
        raise ComfyProtocolError("Model requirement accepted_tokens must be an array")
    return ModelRequirement(
        requirement_id=raw["requirement_id"],
        model_type=raw["model_type"],
        node_id=raw["node_id"],
        input_name=raw["input_name"],
        accepted_tokens=tuple(tokens),
    )
