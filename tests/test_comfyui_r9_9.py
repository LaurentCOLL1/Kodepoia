from __future__ import annotations

import pytest

from kodepoia.comfyui.contracts import ComfyCapabilityState
from kodepoia.comfyui.errors import ComfyGovernanceError
from kodepoia.comfyui.inventory import (
    ComfyCapabilitySnapshot,
    ComfyModelInventory,
    normalize_node_inventory,
)
from kodepoia.comfyui.packs import (
    ProductionWorkflowFamily,
    ProductionWorkflowPackCatalog,
    WorkflowPackCompatibilityState,
)
from kodepoia.comfyui.serialization import canonical_sha256


def _snapshot(*, state: ComfyCapabilityState = ComfyCapabilityState.CURRENT) -> ComfyCapabilitySnapshot:
    object_info = {
        "CheckpointLoaderSimple": {
            "input": {"required": {"ckpt_name": [["models/classic-a.safetensors", "models/classic-b.safetensors"]]}},
            "output": ["MODEL", "CLIP", "VAE"],
            "output_is_list": [False, False, False],
            "category": "loaders",
        },
        "CLIPTextEncode": {
            "input": {"required": {"text": ["STRING"], "clip": ["CLIP"]}},
            "output": ["CONDITIONING"],
            "output_is_list": [False],
            "category": "conditioning",
        },
        "EmptyLatentImage": {
            "input": {
                "required": {
                    "width": ["INT", {"min": 16, "max": 4096, "step": 8}],
                    "height": ["INT", {"min": 16, "max": 4096, "step": 8}],
                    "batch_size": ["INT", {"min": 1, "max": 64, "step": 1}],
                }
            },
            "output": ["LATENT"],
            "output_is_list": [False],
            "category": "latent",
        },
        "KSampler": {
            "input": {
                "required": {
                    "model": ["MODEL"],
                    "seed": ["INT", {"min": 0, "max": 18446744073709551615}],
                    "steps": ["INT", {"min": 1, "max": 1000, "step": 1}],
                    "cfg": ["FLOAT", {"min": 0.0, "max": 100.0, "step": 0.1}],
                    "sampler_name": [["euler", "dpmpp_2m"]],
                    "scheduler": [["normal", "karras"]],
                    "positive": ["CONDITIONING"],
                    "negative": ["CONDITIONING"],
                    "latent_image": ["LATENT"],
                    "denoise": ["FLOAT", {"min": 0.0, "max": 1.0, "step": 0.01}],
                }
            },
            "output": ["LATENT"],
            "output_is_list": [False],
            "category": "sampling",
        },
        "VAEDecode": {
            "input": {"required": {"samples": ["LATENT"], "vae": ["VAE"]}},
            "output": ["IMAGE"],
            "output_is_list": [False],
            "category": "latent",
        },
        "SaveImage": {
            "input": {"required": {"images": ["IMAGE"], "filename_prefix": ["STRING"]}},
            "output": [],
            "output_is_list": [],
            "category": "image",
            "output_node": True,
        },
    }
    nodes = normalize_node_inventory(object_info)
    models = (
        ComfyModelInventory(
            model_type="checkpoints",
            tokens=("models/classic-a.safetensors", "models/classic-b.safetensors"),
            digest_sha256=canonical_sha256(
                {
                    "model_type": "checkpoints",
                    "tokens": ["models/classic-a.safetensors", "models/classic-b.safetensors"],
                }
            ),
        ),
    )
    system = {"system": {"comfyui_version": "0.test-r9.9", "python_version": "3.12.test"}}
    features = {"workflow_packs": True}
    system_digest = canonical_sha256(system)
    feature_digest = canonical_sha256(features)
    identity = {
        "endpoint": "http://127.0.0.1:8188",
        "comfyui_version": "0.test-r9.9",
        "python_version": "3.12.test",
        "system_digest_sha256": system_digest,
        "feature_digest_sha256": feature_digest,
        "nodes": [item.canonical() for item in nodes],
        "models": [item.canonical() for item in models],
        "unavailable": [],
    }
    return ComfyCapabilitySnapshot(
        state=state,
        endpoint="http://127.0.0.1:8188",
        captured_at="2026-08-23T12:00:00Z",
        comfyui_version="0.test-r9.9",
        python_version="3.12.test",
        system_digest_sha256=system_digest,
        feature_digest_sha256=feature_digest,
        nodes=nodes,
        models=models,
        unavailable=(),
        identity_sha256=canonical_sha256(identity),
    )


def _valid_request() -> dict[str, object]:
    return {
        "prompt": "clean production concept",
        "negative_prompt": "",
        "width": 512,
        "height": 512,
        "output_count": 1,
        "seed": 42,
        "steps": 24,
        "cfg": 7.0,
    }


def test_catalog_contains_exact_mandatory_families_and_core_only_graphs() -> None:
    catalog = ProductionWorkflowPackCatalog()
    packs = catalog.packs()
    assert tuple(pack.family for pack in packs) == tuple(ProductionWorkflowFamily)
    assert len({pack.definition.definition_id for pack in packs}) == 4
    core = {
        "CheckpointLoaderSimple",
        "CLIPTextEncode",
        "EmptyLatentImage",
        "KSampler",
        "VAEDecode",
        "SaveImage",
    }
    for pack in packs:
        assert set(pack.definition.allowed_node_classes) == core
        assert pack.required_output_node_ids == ("7",)
        assert pack.definition.model_requirements[0].accepted_tokens == ()
        assert pack.identity_sha256 == canonical_sha256(pack.canonical())


def test_pack_policy_bounds_dimensions_outputs_pixels_prompts_and_material_claim() -> None:
    catalog = ProductionWorkflowPackCatalog()
    material = catalog.get(ProductionWorkflowFamily.MATERIAL_SOURCE)
    assert material.material_source_only is True
    normalized = material.validate_request(_valid_request())
    assert normalized["seed"] == 42

    too_many = _valid_request()
    too_many["output_count"] = 8
    with pytest.raises(ComfyGovernanceError, match="output count"):
        material.validate_request(too_many)

    too_large = _valid_request()
    too_large["width"] = 1536
    too_large["height"] = 1536
    too_large["output_count"] = 4
    with pytest.raises(ComfyGovernanceError, match="total-pixel"):
        material.validate_request(too_large)

    hostile = _valid_request()
    hostile["prompt"] = "x" * 9000
    with pytest.raises(ComfyGovernanceError, match="bounded"):
        material.validate_request(hostile)


def test_compatibility_requires_explicit_discovered_model_selection_and_is_deterministic() -> None:
    catalog = ProductionWorkflowPackCatalog()
    snapshot = _snapshot()
    blocked = catalog.compatibility(ProductionWorkflowFamily.CONCEPT, snapshot)
    assert blocked.state is WorkflowPackCompatibilityState.BLOCKED
    assert "ambiguous" in " ".join(blocked.reasons)

    first = catalog.compatibility(
        ProductionWorkflowFamily.CONCEPT,
        snapshot,
        model_selections={"checkpoint": "models/classic-a.safetensors"},
    )
    second = catalog.compatibility(
        ProductionWorkflowFamily.CONCEPT,
        snapshot,
        model_selections={"checkpoint": "models/classic-a.safetensors"},
    )
    assert first.state is WorkflowPackCompatibilityState.COMPATIBLE
    assert first.selected_models == (("checkpoint", "models/classic-a.safetensors"),)
    assert first.report_digest_sha256 == second.report_digest_sha256

    missing = catalog.compatibility(
        ProductionWorkflowFamily.CONCEPT,
        snapshot,
        model_selections={"checkpoint": "missing.safetensors"},
    )
    assert missing.state is WorkflowPackCompatibilityState.BLOCKED


def test_stale_capability_is_not_accepted() -> None:
    report = ProductionWorkflowPackCatalog().compatibility(
        ProductionWorkflowFamily.UI_ILLUSTRATION,
        _snapshot(state=ComfyCapabilityState.STALE),
        model_selections={"checkpoint": "models/classic-a.safetensors"},
    )
    assert report.state is WorkflowPackCompatibilityState.STALE


def test_workflow_instance_has_explicit_seed_dimensions_and_no_graph_markers() -> None:
    catalog = ProductionWorkflowPackCatalog()
    pack = catalog.get(ProductionWorkflowFamily.SPRITE_2D)
    snapshot = _snapshot()
    params = pack.validate_request(_valid_request())

    from kodepoia.comfyui.workflow import GovernedModelResolver, WorkflowValidator

    resolutions = GovernedModelResolver().resolve(
        pack.definition,
        snapshot,
        selections={"checkpoint": "models/classic-a.safetensors"},
    )
    instance = WorkflowValidator().instantiate(
        pack.definition,
        snapshot,
        resolutions,
        parameters=params,
    )
    prompt = instance.prompt()
    assert prompt["4"]["inputs"] == {"batch_size": 1, "height": 512, "width": 512}
    assert prompt["5"]["inputs"]["seed"] == 42
    assert prompt["7"]["class_type"] == "SaveImage"
    assert "$param" not in instance.prompt_json
    assert "$model" not in instance.prompt_json
