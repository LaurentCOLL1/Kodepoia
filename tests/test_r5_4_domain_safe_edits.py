from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from kodepoia.kodegodot import GodotSceneDomainAnalyzer, GodotSceneEditor, GodotToolAPI


SCENE = '''[gd_scene format=3]

[node name="Root" type="Node3D"]

[node name="Player" type="CharacterBody3D" parent="."]
position = Vector3(0, 1, 0)
visible = true

[node name="Camera" type="Camera3D" parent="."]

[node name="HUD" type="Control" parent="."]

[node name="Legacy" type="TileMap" parent="."]
'''


def _write_scene(root: Path) -> Path:
    target = root / "main.tscn"
    target.write_text(SCENE, encoding="utf-8")
    return target


def test_domain_report_classifies_scene_and_conservative_issues(tmp_path: Path) -> None:
    _write_scene(tmp_path)
    report = GodotSceneDomainAnalyzer(tmp_path).analyze("main.tscn")
    assert report.dimension == "hybrid"
    assert report.character_bodies == ("Player",)
    assert report.cameras == ("Camera",)
    assert report.ui_nodes == ("HUD",)
    codes = {item.code for item in report.issues}
    assert {"legacy-tilemap", "character-no-collision", "hybrid-scene"} <= codes


def test_scene_editor_requires_sha_and_existing_property(tmp_path: Path) -> None:
    target = _write_scene(tmp_path)
    editor = GodotSceneEditor(tmp_path)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    result = editor.set_existing_property(
        "main.tscn",
        node="Player",
        parent=".",
        property_name="position",
        raw_value="Vector3(2, 3, 4)",
        expected_sha256=digest,
    )
    assert result.before_sha256 == digest
    assert result.after_sha256 != digest
    assert "position = Vector3(2, 3, 4)" in target.read_text(encoding="utf-8")

    with pytest.raises(ValueError, match="precondition"):
        editor.set_existing_property(
            "main.tscn",
            node="Player",
            parent=".",
            property_name="visible",
            raw_value="false",
            expected_sha256=digest,
        )


def test_scene_editor_refuses_new_or_protected_or_multiline_property(tmp_path: Path) -> None:
    target = _write_scene(tmp_path)
    editor = GodotSceneEditor(tmp_path)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="already exist"):
        editor.set_existing_property(
            "main.tscn", node="Player", parent=".", property_name="speed", raw_value="5.0", expected_sha256=digest
        )
    with pytest.raises(PermissionError, match="protected"):
        editor.set_existing_property(
            "main.tscn", node="Player", parent=".", property_name="script", raw_value='ExtResource("1")', expected_sha256=digest
        )
    with pytest.raises(ValueError, match="single"):
        editor.set_existing_property(
            "main.tscn", node="Player", parent=".", property_name="position", raw_value="Vector3(1,2,3)\nfoo", expected_sha256=digest
        )


def test_tool_api_exposes_sha_guarded_scene_edit(tmp_path: Path) -> None:
    target = _write_scene(tmp_path)
    api = GodotToolAPI(tmp_path)
    catalog = {entry["function"]["name"]: entry for entry in api.catalog()}
    params = catalog["kodegodot_scene_set_existing_property"]["function"]["parameters"]
    assert "expected_sha256" in params["required"]
    assert params["additionalProperties"] is False
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    result = api.invoke(
        "kodegodot_scene_set_existing_property",
        {
            "path": "main.tscn",
            "node": "Player",
            "parent": ".",
            "property": "visible",
            "raw_value": "false",
            "expected_sha256": digest,
        },
    )
    assert result["property"] == "visible"
