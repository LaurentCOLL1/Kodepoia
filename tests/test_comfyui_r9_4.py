from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from kodepoia.assets.contracts import AssetRevisionId, ReuseScope
from kodepoia.assets.governance import AssetGovernanceOutcome
from kodepoia.comfyui import (
    ComfyCapabilitySnapshot,
    ComfyCapabilityState,
    ComfyGovernanceError,
    ComfyModelInventory,
    ComfyProtocolError,
    GovernedModelResolver,
    ModelRequirement,
    ModelResolutionState,
    VaultModelEvidence,
    WorkflowCatalog,
    WorkflowDefinition,
    WorkflowInputSlot,
    WorkflowOutputSlot,
    WorkflowParameterKind,
    WorkflowParameterSpec,
    WorkflowValidator,
    canonical_sha256,
    normalize_node_inventory,
)

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_FIXTURE = ROOT / "tests" / "fixtures" / "comfyui" / "r9_3_inventory.json"
WORKFLOW_FIXTURE = ROOT / "tests" / "fixtures" / "comfyui" / "r9_4_workflow_spec.json"
PAYLOAD_SCHEMA = ROOT / "schemas" / "comfy-workflow-definition-payload-v1.schema.json"


@pytest.fixture
def inventory_fixture() -> dict[str, Any]:
    return json.loads(INVENTORY_FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture
def workflow_spec() -> dict[str, Any]:
    return json.loads(WORKFLOW_FIXTURE.read_text(encoding="utf-8"))


def _snapshot(fixture: dict[str, Any], *, state: ComfyCapabilityState = ComfyCapabilityState.CURRENT) -> ComfyCapabilitySnapshot:
    nodes = normalize_node_inventory(fixture["object_info"])
    models: list[ComfyModelInventory] = []
    for model_type in sorted(fixture["models"]["types"]):
        tokens = tuple(sorted(fixture["models"][model_type]))
        models.append(
            ComfyModelInventory(
                model_type=model_type,
                tokens=tokens,
                digest_sha256=canonical_sha256({"model_type": model_type, "tokens": list(tokens)}),
            )
        )
    system_digest = canonical_sha256(fixture["system_stats"])
    feature_digest = canonical_sha256(fixture["features"])
    system = fixture["system_stats"]["system"]
    identity_payload = {
        "endpoint": "http://127.0.0.1:8188",
        "comfyui_version": system["comfyui_version"],
        "python_version": system["python_version"],
        "system_digest_sha256": system_digest,
        "feature_digest_sha256": feature_digest,
        "nodes": [item.canonical() for item in nodes],
        "models": [item.canonical() for item in models],
        "unavailable": [],
    }
    return ComfyCapabilitySnapshot(
        state=state,
        endpoint="http://127.0.0.1:8188",
        captured_at="2026-08-23T08:00:00Z",
        comfyui_version=system["comfyui_version"],
        python_version=system["python_version"],
        system_digest_sha256=system_digest,
        feature_digest_sha256=feature_digest,
        nodes=nodes,
        models=tuple(models),
        unavailable=(),
        identity_sha256=canonical_sha256(identity_payload),
    )


def _definition(spec: dict[str, Any]) -> WorkflowDefinition:
    return WorkflowDefinition.create(
        name=spec["name"],
        revision=spec["revision"],
        graph=spec["graph"],
        parameters=tuple(
            WorkflowParameterSpec(
                name=item["name"],
                node_id=item["node_id"],
                input_name=item["input_name"],
                kind=WorkflowParameterKind(item["kind"]),
                minimum=item["minimum"],
                maximum=item["maximum"],
                choices=tuple(item["choices"]),
            )
            for item in spec["parameters"]
        ),
        input_slots=tuple(
            WorkflowInputSlot(item["name"], item["node_id"], item["input_name"], item["type_token"])
            for item in spec["input_slots"]
        ),
        output_slots=tuple(
            WorkflowOutputSlot(item["name"], item["node_id"], item["output_index"], item["type_token"])
            for item in spec["output_slots"]
        ),
        model_requirements=tuple(
            ModelRequirement(
                requirement_id=item["requirement_id"],
                model_type=item["model_type"],
                node_id=item["node_id"],
                input_name=item["input_name"],
                accepted_tokens=tuple(item["accepted_tokens"]),
            )
            for item in spec["model_requirements"]
        ),
        allowed_node_classes=tuple(spec["allowed_node_classes"]),
    )


def test_validated_instance_is_deterministic_and_contains_no_internal_markers(
    inventory_fixture: dict[str, Any], workflow_spec: dict[str, Any]
) -> None:
    snapshot = _snapshot(inventory_fixture)
    definition = _definition(workflow_spec)
    validator = WorkflowValidator()
    validation = validator.validate(definition, snapshot)
    assert validation.definition_id == definition.definition_id
    assert validation.capability_identity_sha256 == snapshot.identity_sha256

    resolutions = GovernedModelResolver().resolve(definition, snapshot)
    assert resolutions.ready is True
    assert resolutions.resolutions[0].selected_token == "base/model-a.safetensors"
    assert resolutions.resolutions[0].license_token == "NOASSERTION"
    assert resolutions.resolutions[0].exportable is False

    first = validator.instantiate(
        definition,
        snapshot,
        resolutions,
        parameters={"seed": 42, "steps": 20},
    )
    second = validator.instantiate(
        definition,
        snapshot,
        resolutions,
        parameters={"steps": 20, "seed": 42},
    )
    assert first.instance_digest_sha256 == second.instance_digest_sha256
    assert first.prompt() == {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "base/model-a.safetensors"}},
        "2": {
            "class_type": "KSampler",
            "inputs": {
                "cfg": 7.5,
                "control_after_generate": "fixed",
                "model": ["1", 0],
                "seed": 42,
                "steps": 20,
            },
        },
    }
    assert "$param" not in first.prompt_json
    assert "$model" not in first.prompt_json


def test_unknown_node_injection_and_connection_type_mismatch_are_rejected(
    inventory_fixture: dict[str, Any], workflow_spec: dict[str, Any]
) -> None:
    snapshot = _snapshot(inventory_fixture)
    validator = WorkflowValidator()

    injected = copy.deepcopy(workflow_spec)
    injected["graph"]["99"] = {"class_type": "HostileUnknownNode", "inputs": {}}
    injected["allowed_node_classes"].append("HostileUnknownNode")
    with pytest.raises(ComfyGovernanceError, match="absent from capability snapshot"):
        validator.validate(_definition(injected), snapshot)

    wrong_link = copy.deepcopy(workflow_spec)
    wrong_link["graph"]["2"]["inputs"]["model"] = ["1", 2]
    with pytest.raises(ComfyGovernanceError, match="type mismatch"):
        validator.validate(_definition(wrong_link), snapshot)


def test_undeclared_marker_and_graph_fragment_parameter_are_rejected(
    inventory_fixture: dict[str, Any], workflow_spec: dict[str, Any]
) -> None:
    rogue = copy.deepcopy(workflow_spec)
    rogue["graph"]["2"]["inputs"]["steps"] = {"$param": "rogue"}
    with pytest.raises(ValueError, match="markers must exactly match"):
        _definition(rogue)

    snapshot = _snapshot(inventory_fixture)
    definition = _definition(workflow_spec)
    resolutions = GovernedModelResolver().resolve(definition, snapshot)
    with pytest.raises(ComfyGovernanceError, match="JSON scalar"):
        WorkflowValidator().instantiate(
            definition,
            snapshot,
            resolutions,
            parameters={"seed": {"class_type": "HostileNode"}, "steps": 20},
        )


def test_model_resolution_surfaces_ambiguity_missing_and_invalid_selection(
    inventory_fixture: dict[str, Any], workflow_spec: dict[str, Any]
) -> None:
    snapshot = _snapshot(inventory_fixture)
    resolver = GovernedModelResolver()

    ambiguous_spec = copy.deepcopy(workflow_spec)
    ambiguous_spec["model_requirements"][0]["accepted_tokens"] = []
    ambiguous = resolver.resolve(_definition(ambiguous_spec), snapshot)
    assert ambiguous.ready is False
    assert ambiguous.resolutions[0].state is ModelResolutionState.AMBIGUOUS
    assert ambiguous.resolutions[0].candidates == (
        "base/model-a.safetensors",
        "base/model-b.safetensors",
    )

    selected = resolver.resolve(
        _definition(ambiguous_spec),
        snapshot,
        selections={"checkpoint": "base/model-b.safetensors"},
    )
    assert selected.ready is True
    assert selected.resolutions[0].selected_token == "base/model-b.safetensors"

    blocked = resolver.resolve(
        _definition(ambiguous_spec),
        snapshot,
        selections={"checkpoint": "missing/model.safetensors"},
    )
    assert blocked.ready is False
    assert blocked.resolutions[0].state is ModelResolutionState.BLOCKED

    missing_spec = copy.deepcopy(workflow_spec)
    missing_spec["model_requirements"][0]["accepted_tokens"] = ["missing/model.safetensors"]
    missing = resolver.resolve(_definition(missing_spec), snapshot)
    assert missing.resolutions[0].state is ModelResolutionState.MISSING


def test_vault_evidence_is_inherited_and_external_local_never_fabricates_exportability(
    inventory_fixture: dict[str, Any], workflow_spec: dict[str, Any]
) -> None:
    snapshot = _snapshot(inventory_fixture)
    definition = _definition(workflow_spec)
    evidence = VaultModelEvidence(
        revision_id=AssetRevisionId("rev_0123456789abcdef0123456789abcdef"),
        content_sha256="a" * 64,
        reuse_scope=ReuseScope.EXPORTABLE,
        governance_outcome=AssetGovernanceOutcome.ALLOW,
        license_token="MIT",
    )
    resolutions = GovernedModelResolver().resolve(
        definition,
        snapshot,
        vault_evidence={("checkpoints", "base/model-a.safetensors"): evidence},
    )
    resolution = resolutions.resolutions[0]
    assert resolution.exportable is True
    assert resolution.license_token == "MIT"
    assert resolution.vault_evidence == evidence

    unknown = GovernedModelResolver().resolve(definition, snapshot).resolutions[0]
    assert unknown.exportable is False
    assert unknown.license_token == "NOASSERTION"


def test_stale_capability_cannot_validate_or_resolve(
    inventory_fixture: dict[str, Any], workflow_spec: dict[str, Any]
) -> None:
    stale = _snapshot(inventory_fixture, state=ComfyCapabilityState.STALE)
    definition = _definition(workflow_spec)
    with pytest.raises(ComfyGovernanceError, match="CURRENT"):
        WorkflowValidator().validate(definition, stale)
    with pytest.raises(ComfyGovernanceError, match="CURRENT"):
        GovernedModelResolver().resolve(definition, stale)


def test_catalog_roundtrip_and_tamper_detection(
    tmp_path: Path, workflow_spec: dict[str, Any]
) -> None:
    definition = _definition(workflow_spec)
    path = tmp_path / "safe.json"
    path.write_bytes(json.dumps(definition.envelope(), sort_keys=True).encode("utf-8"))
    catalog = WorkflowCatalog.load_files(tmp_path, ["safe.json"])
    assert catalog.get(definition.definition_id) == definition

    document = json.loads(path.read_text(encoding="utf-8"))
    document["payload"]["graph"]["2"]["inputs"]["cfg"] = 8.0
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ComfyProtocolError, match="does not match canonical payload"):
        WorkflowCatalog.load_files(tmp_path, ["safe.json"])

    with pytest.raises(ComfyProtocolError, match="safe explicit JSON basenames"):
        WorkflowCatalog.load_files(tmp_path, ["../escape.json"])


def test_strict_payload_schema_accepts_canonical_definition(workflow_spec: dict[str, Any]) -> None:
    definition = _definition(workflow_spec)
    schema = json.loads(PAYLOAD_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(definition.payload())


def test_parameter_constraints_must_not_widen_capability(
    inventory_fixture: dict[str, Any], workflow_spec: dict[str, Any]
) -> None:
    widened = copy.deepcopy(workflow_spec)
    for parameter in widened["parameters"]:
        if parameter["name"] == "steps":
            parameter["maximum"] = 20_000
    with pytest.raises(ComfyGovernanceError, match="wider than capability maximum"):
        WorkflowValidator().validate(_definition(widened), _snapshot(inventory_fixture))
