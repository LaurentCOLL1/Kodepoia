from __future__ import annotations

from typing import Any

import pytest

from kodepoia.comfyui.errors import ComfyProtocolError
from kodepoia.comfyui.inventory import normalize_node_inventory
from kodepoia.comfyui.r9_8_acceptance import _R98WorkflowCapabilityInventory


class _HTTP:
    def get_json(self, path: str) -> dict[str, Any]:
        assert path == "/object_info"
        return {
            "GoodNode": {
                "input": {},
                "output": ["STRING"],
                "output_is_list": [False],
                "category": "fixture",
                "deprecated": False,
                "experimental": False,
                "api_node": False,
            },
            "TextToLowercase": {
                "input": {},
                "output": ["STRING"],
                # Deliberately violates the upstream object_info contract: entries
                # must be booleans. This mirrors the local custom-node regression
                # that triggered the R9.8 REQUIRED gate precursor.
                "output_is_list": [0],
                "category": "fixture/custom",
                "deprecated": False,
                "experimental": False,
                "api_node": False,
            },
        }

    def get_json_value(self, path: str) -> Any:
        if path == "/models":
            return ["diffusion_models", "embeddings", "vae"]
        if path == "/models/diffusion_models":
            return [
                "wanted.safetensors",
                "nested\\unrelated.safetensors",
            ]
        if path == "/models/embeddings":
            return ["nested\\bad.pt"]
        if path == "/models/vae":
            return ["nested\\wanted-vae.safetensors"]
        raise AssertionError(path)


class _Client:
    def __init__(self) -> None:
        self._http = _HTTP()


def test_r98_targeted_inventory_ignores_malformed_unrelated_custom_node() -> None:
    inventory = _R98WorkflowCapabilityInventory(_Client(), ("GoodNode",))
    selected = inventory._object_info()
    assert set(selected) == {"GoodNode"}
    nodes = normalize_node_inventory(selected)
    assert tuple(node.class_type for node in nodes) == ("GoodNode",)


def test_r98_targeted_inventory_keeps_strict_failure_for_required_malformed_node() -> None:
    inventory = _R98WorkflowCapabilityInventory(_Client(), ("TextToLowercase",))
    selected = inventory._object_info()
    assert set(selected) == {"TextToLowercase"}
    with pytest.raises(ComfyProtocolError, match="output_is_list must contain booleans"):
        normalize_node_inventory(selected)


def test_r98_targeted_model_inventory_ignores_unrelated_windows_style_tokens() -> None:
    inventory = _R98WorkflowCapabilityInventory(
        _Client(),
        ("GoodNode",),
        {"diffusion_models": ("wanted.safetensors",)},
    )
    assert inventory._model_types() == ("diffusion_models",)
    assert inventory._models("diffusion_models") == ("wanted.safetensors",)


def test_r98_targeted_model_inventory_does_not_rewrite_required_windows_separator() -> None:
    inventory = _R98WorkflowCapabilityInventory(
        _Client(),
        ("GoodNode",),
        {"vae": ("nested/wanted-vae.safetensors",)},
    )
    assert inventory._model_types() == ("vae",)
    # The upstream Windows-style token does not equal the canonical governed token.
    # R9.8 must surface it as missing later rather than silently rewriting identity.
    assert inventory._models("vae") == ()


def test_r98_targeted_model_inventory_skips_unrelated_model_categories() -> None:
    inventory = _R98WorkflowCapabilityInventory(
        _Client(),
        ("GoodNode",),
        {"diffusion_models": ("wanted.safetensors",)},
    )
    assert "embeddings" not in inventory._model_types()
