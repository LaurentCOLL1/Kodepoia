from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.assets import (
    AssetId,
    AssetKind,
    AssetRevision,
    AssetRole,
    GodotAssetBridge,
    GodotAssetClassification,
    GodotRebuildState,
    PreservationPolicy,
    ProjectAssetReference,
)


@dataclass(frozen=True)
class _Wrapped:
    result: dict


class _FakeGodotExecutor:
    def __init__(self, root: Path, *, available: bool = True, mutate_source: bool = False) -> None:
        self.root = root
        self.available = available
        self.mutate_source = mutate_source
        self.calls: list[tuple[str, dict]] = []

    def invoke(self, tool_name, arguments=None, *, actor="brain", confirmed=False):
        args = dict(arguments or {})
        self.calls.append((tool_name, args))
        if tool_name == "kodegodot_engine_version":
            if not self.available:
                raise FileNotFoundError("godot")
            return _Wrapped(
                {
                    "raw": "4.7.2.stable.fixture",
                    "major": 4,
                    "minor": 7,
                    "patch": 2,
                    "suffix": "stable.fixture",
                    "compatible_47": True,
                }
            )
        if tool_name == "kodegodot_import_project":
            if self.mutate_source:
                (self.root / "source.svg").write_text("tampered", encoding="utf-8")
            (self.root / "source.svg.import").write_text(
                '[remap]\nimporter="image"\n'
                'path="res://.godot/imported/source.svg-fixture.ctex"\n',
                encoding="utf-8",
            )
            cache = self.root / ".godot" / "imported"
            cache.mkdir(parents=True, exist_ok=True)
            (cache / "source.svg-fixture.ctex").write_bytes(b"fixture-cache")
            return _Wrapped(
                {
                    "operation": "import",
                    "returncode": 0,
                    "stdout": "",
                    "stderr": "",
                    "timed_out": False,
                    "cancelled": False,
                }
            )
        raise AssertionError(f"Unexpected structured tool: {tool_name}")


def _fixture(root: Path) -> ProjectAssetReference:
    (root / "project.godot").write_text("config_version=5\n", encoding="utf-8")
    (root / "source.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"></svg>\n',
        encoding="utf-8",
    )
    data = (root / "source.svg").read_bytes()
    asset_id = AssetId.from_seed("r8.9-test", "source.svg")
    revision = AssetRevision.create(
        asset_id=asset_id,
        role=AssetRole.SOURCE,
        kind=AssetKind.IMAGE,
        content_sha256=hashlib.sha256(data).hexdigest(),
        content_length=len(data),
        preservation=PreservationPolicy.PINNED_SOURCE,
    )
    return ProjectAssetReference(
        "r8.9-test",
        asset_id,
        revision.revision_id,
        "source.svg",
    )


def test_classification_keeps_source_sidecar_and_cache_distinct(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    bridge = GodotAssetBridge(root, _FakeGodotExecutor(root))
    assert bridge.classify("source.svg") is GodotAssetClassification.SOURCE
    assert bridge.classify("source.svg.import") is GodotAssetClassification.IMPORT_METADATA
    assert bridge.classify(".godot/imported/a.ctex") is GodotAssetClassification.GENERATED_CACHE
    assert bridge.classify(".import/legacy.cache") is GodotAssetClassification.GENERATED_CACHE
    assert bridge.classify("scene.tscn") is GodotAssetClassification.GODOT_NATIVE


def test_missing_godot_is_unavailable_and_does_not_purge_cache(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    reference = _fixture(root)
    cache = root / ".godot" / "imported"
    cache.mkdir(parents=True)
    marker = cache / "keep-until-capability-known"
    marker.write_text("cache", encoding="utf-8")
    before = (root / "source.svg").read_bytes()

    report = GodotAssetBridge(
        root,
        _FakeGodotExecutor(root, available=False),
    ).rebuild(["source.svg"], references=(reference,))

    assert report.state is GodotRebuildState.UNAVAILABLE
    assert marker.is_file()
    assert (root / "source.svg").read_bytes() == before
    assert [item.code for item in report.issues] == ["GODOT_UNAVAILABLE"]


def test_successful_rebuild_preserves_source_and_regenerates_disposable_cache(
    tmp_path: Path,
) -> None:
    root = tmp_path / "project"
    root.mkdir()
    reference = _fixture(root)
    legacy = root / ".import"
    legacy.mkdir()
    (legacy / "old.cache").write_text("old", encoding="utf-8")
    source_before = (root / "source.svg").read_bytes()
    fake = _FakeGodotExecutor(root)
    bridge = GodotAssetBridge(root, fake)

    report = bridge.rebuild(["source.svg"], references=(reference,))

    assert report.state is GodotRebuildState.READY
    assert (root / "source.svg").read_bytes() == source_before
    assert not legacy.exists()
    assert report.generated_cache_files == 1
    assert report.sources[0].import_settings is not None
    assert report.sources[0].asset_id == str(reference.asset_id)
    assert report.sources[0].revision_id == str(reference.revision_id)
    assert report.manifest_digest is not None
    assert [name for name, _ in fake.calls] == [
        "kodegodot_engine_version",
        "kodegodot_import_project",
    ]


def test_source_mutation_during_import_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    reference = _fixture(root)
    bridge = GodotAssetBridge(root, _FakeGodotExecutor(root, mutate_source=True))

    report = bridge.rebuild(["source.svg"], references=(reference,))

    assert report.state is GodotRebuildState.FAILED
    assert "SOURCE_MUTATED" in {item.code for item in report.issues}


def test_portability_rejects_cache_reference_and_missing_materialization(
    tmp_path: Path,
) -> None:
    root = tmp_path / "project"
    root.mkdir()
    reference = _fixture(root)
    cache_ref = ProjectAssetReference(
        reference.project_id,
        reference.asset_id,
        reference.revision_id,
        ".godot/imported/source.ctex",
    )
    missing_ref = ProjectAssetReference(
        reference.project_id,
        reference.asset_id,
        reference.revision_id,
        "missing.svg",
    )
    issues = GodotAssetBridge(
        root,
        _FakeGodotExecutor(root),
    ).portability_diagnostics((cache_ref, missing_ref))
    assert {item.code for item in issues} == {
        "GENERATED_CACHE_REFERENCE",
        "MISSING_MATERIALIZED_SOURCE",
    }


def test_import_manifest_matches_versioned_json_schema(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    reference = _fixture(root)
    report = GodotAssetBridge(root, _FakeGodotExecutor(root)).rebuild(
        ["source.svg"],
        references=(reference,),
    )
    schema_path = Path("schemas/godot-import-manifest-v1.schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(report.manifest_payload())


def test_cache_symlink_is_never_followed(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (root / ".godot").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Symlink creation unavailable on this platform")
    bridge = GodotAssetBridge(root, _FakeGodotExecutor(root))
    with pytest.raises(PermissionError):
        bridge.purge_generated_cache()
