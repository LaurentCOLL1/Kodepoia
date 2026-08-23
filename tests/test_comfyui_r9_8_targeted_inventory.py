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
