from __future__ import annotations

from pathlib import Path

import pytest

from kodepoia.kodegodot import GodotTextDocumentParser, GodotToolAPI


SCENE = '''[gd_scene load_steps=4 format=3 uid="uid://demo"]

[ext_resource type="Script" uid="uid://script" path="res://player.gd" id="1_script"]
[ext_resource type="PackedScene" path="res://child.tscn" id="2_child"]

[sub_resource type="CapsuleShape3D" id="CapsuleShape3D_test"]
radius = 0.5
height = 1.8

[node name="Player" type="CharacterBody3D"]
script = ExtResource("1_script")
position = Vector3(1, 2, 3)

[node name="Child" parent="." instance=ExtResource("2_child")]

[connection signal="body_entered" from="Player" to="Player" method="_on_body_entered"]
'''

RESOURCE = '''[gd_resource type="StandardMaterial3D" format=3 uid="uid://mat"]

[resource]
albedo_color = Color(1, 0, 0, 1)
'''


def test_parse_scene_structure_and_provenance(tmp_path: Path) -> None:
    (tmp_path / "main.tscn").write_text(SCENE, encoding="utf-8")
    doc = GodotTextDocumentParser(tmp_path).parse("main.tscn")
    assert doc.document_type == "scene"
    assert doc.format == 3
    assert doc.uid == "uid://demo"
    assert doc.load_steps == 4
    assert [item.path for item in doc.external_resources] == ["res://player.gd", "res://child.tscn"]
    assert doc.dependencies == ("res://player.gd", "res://child.tscn")
    assert doc.sub_resources[0].resource_type == "CapsuleShape3D"
    assert doc.nodes[0].name == "Player"
    assert doc.nodes[0].node_type == "CharacterBody3D"
    assert doc.nodes[0].properties[0].raw_value == 'ExtResource("1_script")'
    assert doc.nodes[0].line > 0
    assert doc.connections[0].signal == "body_entered"
    assert doc.connections[0].method == "_on_body_entered"


def test_parse_resource_and_preserve_variant_text(tmp_path: Path) -> None:
    (tmp_path / "material.tres").write_text(RESOURCE, encoding="utf-8")
    doc = GodotTextDocumentParser(tmp_path).parse("material.tres")
    assert doc.document_type == "resource"
    assert doc.format == 3
    resource_section = next(section for section in doc.sections if section.kind == "resource")
    assert resource_section.properties[0].raw_value == "Color(1, 0, 0, 1)"


def test_reject_non_format3_and_workspace_escape(tmp_path: Path) -> None:
    parser = GodotTextDocumentParser(tmp_path)
    with pytest.raises(ValueError, match="format=3"):
        parser.parse_text('[gd_scene format=2]\n', path="old.tscn")
    with pytest.raises(PermissionError):
        parser.parse("../outside.tscn")


def test_reject_non_text_godot_asset(tmp_path: Path) -> None:
    (tmp_path / "binary.scn").write_bytes(b"not a text scene")
    with pytest.raises(ValueError, match=".tscn or .tres"):
        GodotTextDocumentParser(tmp_path).parse("binary.scn")


def test_tool_api_exposes_bounded_document_tools(tmp_path: Path) -> None:
    (tmp_path / "main.tscn").write_text(SCENE, encoding="utf-8")
    api = GodotToolAPI(tmp_path)
    catalog = {entry["function"]["name"]: entry for entry in api.catalog()}
    assert "kodegodot_document_parse" in catalog
    assert "kodegodot_document_dependencies" in catalog
    params = catalog["kodegodot_document_parse"]["function"]["parameters"]
    assert params["additionalProperties"] is False
    result = api.invoke("kodegodot_document_dependencies", {"path": "main.tscn"})
    assert result["dependencies"] == ["res://player.gd", "res://child.tscn"]
