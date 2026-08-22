from __future__ import annotations

from pathlib import Path

import pytest

from kodepoia.assets import (
    AssetId,
    AssetKind,
    CacheState,
    DeterministicTextTransform,
    ProvenanceRef,
    TransformRecipe,
    TransformRegistry,
    TransformService,
    VaultBoundary,
    VaultStore,
)
from kodepoia.core.kill_switch import KillSwitch
from kodepoia.kodecode.workspace import WorkspaceBoundary


def _source(tmp_path: Path) -> tuple[VaultStore, object]:
    vault = tmp_path / "vault"
    project = tmp_path / "project"
    vault.mkdir()
    project.mkdir()
    (project / "source.txt").write_text("kodepoia", encoding="utf-8")
    store = VaultStore(VaultBoundary(vault))
    revision = store.ingest(
        project_boundary=WorkspaceBoundary(project),
        source_path="source.txt",
        asset_id=AssetId.from_seed("tests", "source"),
        kind=AssetKind.DOCUMENT,
        display_name="Source",
        provenance=(ProvenanceRef("project", "source.txt"),),
    )
    return store, revision


def _service(store: VaultStore, switch: KillSwitch | None = None) -> TransformService:
    registry = TransformRegistry()
    registry.register(DeterministicTextTransform())
    return TransformService(store, registry, kill_switch=switch, environment_identity={"runtime": "ci"})


def test_identical_recipe_hits_verified_cache_and_rebuild_hash_matches(tmp_path: Path) -> None:
    store, source = _source(tmp_path)
    try:
        service = _service(store)
        recipe = TransformRecipe("fixture.text-uppercase.v1", 1, {"suffix": "!"}, AssetKind.DOCUMENT)
        output_asset = AssetId.from_seed("tests", "derived")
        first = service.run((source.revision_id,), recipe, output_asset_id=output_asset, display_name="Derived")
        assert first.cache_state is CacheState.MISS
        second = service.run((source.revision_id,), recipe, output_asset_id=output_asset, display_name="Derived")
        assert second.cache_state is CacheState.HIT
        assert second.output_revision_ids == first.output_revision_ids
        output = store.object_path(first.output_revision_ids[0])
        assert output.read_text(encoding="utf-8") == "KODEPOIA!"
    finally:
        store.close()


def test_changed_setting_changes_cache_key(tmp_path: Path) -> None:
    store, source = _source(tmp_path)
    try:
        service = _service(store)
        a = TransformRecipe("fixture.text-uppercase.v1", 1, {"suffix": "!"}, AssetKind.DOCUMENT)
        b = TransformRecipe("fixture.text-uppercase.v1", 1, {"suffix": "?"}, AssetKind.DOCUMENT)
        assert service.cache_key((source.revision_id,), a) != service.cache_key((source.revision_id,), b)
    finally:
        store.close()


def test_missing_input_blocks_rebuild(tmp_path: Path) -> None:
    store, _ = _source(tmp_path)
    try:
        service = _service(store)
        recipe = TransformRecipe("fixture.text-uppercase.v1", 1, {}, AssetKind.DOCUMENT)
        from kodepoia.assets import AssetRevisionId

        with pytest.raises(FileNotFoundError):
            service.run(
                (AssetRevisionId("rev_" + "0" * 32),),
                recipe,
                output_asset_id=AssetId.from_seed("tests", "missing-output"),
                display_name="Missing",
            )
    finally:
        store.close()


def test_lineage_cycle_is_rejected(tmp_path: Path) -> None:
    store, source = _source(tmp_path)
    try:
        service = _service(store)
        recipe = TransformRecipe("fixture.text-uppercase.v1", 1, {}, AssetKind.DOCUMENT)
        with pytest.raises(ValueError, match="cycle"):
            service.run((source.revision_id,), recipe, output_asset_id=source.asset_id, display_name="Cycle")
    finally:
        store.close()


def test_kill_switch_blocks_transform_before_promotion(tmp_path: Path) -> None:
    store, source = _source(tmp_path)
    switch = KillSwitch()
    switch.trigger()
    try:
        service = _service(store, switch)
        recipe = TransformRecipe("fixture.text-uppercase.v1", 1, {}, AssetKind.DOCUMENT)
        output_asset = AssetId.from_seed("tests", "cancelled")
        with pytest.raises(RuntimeError, match="kill switch"):
            service.run((source.revision_id,), recipe, output_asset_id=output_asset, display_name="Cancelled")
        assert store.list_revisions(output_asset) == []
    finally:
        store.close()


def test_corrupt_cache_is_not_treated_as_hit(tmp_path: Path) -> None:
    store, source = _source(tmp_path)
    try:
        service = _service(store)
        recipe = TransformRecipe("fixture.text-uppercase.v1", 1, {}, AssetKind.DOCUMENT)
        key = service.cache_key((source.revision_id,), recipe)
        path = store.boundary.resolve(f"cache/transforms/{key}.json")
        path.write_text("not json", encoding="utf-8")
        result = service.run(
            (source.revision_id,),
            recipe,
            output_asset_id=AssetId.from_seed("tests", "fresh-after-corrupt"),
            display_name="Fresh",
        )
        assert result.cache_state is CacheState.MISS
    finally:
        store.close()
