from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, RefResolver

from kodepoia.media.continuity import (
    ContinuityBridgePackage,
    ContinuityFact,
    ContinuityRefState,
    ContinuityScope,
    ContinuitySnapshot,
    compare_snapshots,
    import_bridge_package,
)


ROOT = Path(__file__).resolve().parents[1]


def _fact(
    fact_id: str,
    value: object,
    *,
    state: ContinuityRefState = ContinuityRefState.ACTIVE,
    authority: str = "project",
    version: str = "v1",
) -> ContinuityFact:
    return ContinuityFact(
        fact_id,
        "world.character",
        fact_id,
        value,
        authority,
        f"source:{fact_id}",
        version,
        state,
    )


def _snapshot(snapshot_id: str, facts: tuple[ContinuityFact, ...], *, project_id: str = "project.alpha") -> ContinuitySnapshot:
    return ContinuitySnapshot(
        snapshot_id,
        ContinuityScope.PROJECT,
        project_id,
        "content.v1",
        facts,
        {"kodepoia.scene": {"scene_id": "scene.main"}},
    )


def test_snapshot_identity_is_order_independent_and_deterministic() -> None:
    a = _fact("character.alex.location", "home")
    b = _fact("world.time.day", 3)
    first = _snapshot("snap.one", (a, b))
    second = _snapshot("snap.one", (b, a))
    assert first.canonical() == second.canonical()
    assert first.digest() == second.digest()
    assert len(first.digest()) == 64


def test_snapshot_rejects_duplicate_ids_nonfinite_values_and_unscoped_extensions() -> None:
    fact = _fact("character.alex.location", "home")
    with pytest.raises(ValueError, match="Duplicate"):
        _snapshot("snap.dupe", (fact, fact))
    with pytest.raises(ValueError, match="finite"):
        _fact("world.temperature", float("nan"))
    with pytest.raises(ValueError, match="namespaced"):
        ContinuitySnapshot("snap.ext", ContinuityScope.SCENE, "project.alpha", "v1", (), {"bad": {}})


def test_compare_snapshots_has_stable_findings_and_fail_closed_states() -> None:
    before = _snapshot(
        "snap.before",
        (
            _fact("character.alex.location", "home"),
            _fact("character.alex.voice", "voice.v1"),
            _fact("world.time.day", 3),
        ),
    )
    after = _snapshot(
        "snap.after",
        (
            _fact("character.alex.location", "school"),
            _fact("character.alex.voice", "voice.v1", state=ContinuityRefState.MISSING),
            _fact("world.weather", "rain"),
        ),
    )
    report = compare_snapshots(before, after)
    kinds = {item.kind for item in report.findings}
    assert kinds == {"VALUE_CHANGED", "STATE_CHANGED", "FACT_MISSING", "FACT_ADDED"}
    missing = next(item for item in report.findings if item.kind == "STATE_CHANGED")
    assert missing.severity.value == "ERROR"
    assert report.digest() == compare_snapshots(before, after).digest()


def test_compare_rejects_cross_project_identity_collision() -> None:
    before = _snapshot("a", (), project_id="project.alpha")
    after = _snapshot("b", (), project_id="project.beta")
    with pytest.raises(ValueError, match="same project_id"):
        compare_snapshots(before, after)


def test_bridge_package_is_digest_bound_and_cannot_auto_promote_canon() -> None:
    snapshot = _snapshot("snap.bridge", (_fact("character.alex.location", "home"),))
    package = ContinuityBridgePackage(
        "bridge.alpha.beta",
        "project.alpha",
        "project.beta",
        "r8.revision.001",
        snapshot,
        snapshot.digest(),
    )
    document = package.canonical()
    assert document["promotion_policy"] == "compare_only_no_canon_mutation"
    result = import_bridge_package(document, expected_target_project_id="project.beta")
    assert result["status"] == "VALIDATED"
    assert result["fact_count"] == 1
    assert package.digest() == package.digest()

    tampered = json.loads(json.dumps(document))
    tampered["snapshot"]["facts"][0]["value"] = "elsewhere"
    with pytest.raises(ValueError, match="digest mismatch"):
        import_bridge_package(tampered, expected_target_project_id="project.beta")

    promoted = json.loads(json.dumps(document))
    promoted["promotion_policy"] = "auto_canon"
    with pytest.raises(ValueError, match="cannot auto-promote"):
        import_bridge_package(promoted, expected_target_project_id="project.beta")


def test_bridge_rejects_wrong_target_and_same_project_package() -> None:
    snapshot = _snapshot("snap.bridge", ())
    with pytest.raises(ValueError, match="different project"):
        ContinuityBridgePackage("bridge.self", "project.alpha", "project.alpha", "r8.rev", snapshot, snapshot.digest())
    package = ContinuityBridgePackage("bridge.ab", "project.alpha", "project.beta", "r8.rev", snapshot, snapshot.digest())
    with pytest.raises(ValueError, match="target project mismatch"):
        import_bridge_package(package.canonical(), expected_target_project_id="project.gamma")


def test_r11_10_schemas_accept_canonical_examples() -> None:
    snapshot = _snapshot("snap.schema", (_fact("character.alex.location", "home"),))
    diff = compare_snapshots(snapshot, _snapshot("snap.schema.2", (_fact("character.alex.location", "school"),)))
    package = ContinuityBridgePackage("bridge.schema", "project.alpha", "project.beta", "r8.rev", snapshot, snapshot.digest())

    snapshot_schema = json.loads((ROOT / "schemas/r11/continuity-snapshot.schema.json").read_text(encoding="utf-8"))
    diff_schema = json.loads((ROOT / "schemas/r11/continuity-diff.schema.json").read_text(encoding="utf-8"))
    bridge_schema = json.loads((ROOT / "schemas/r11/continuity-bridge-package.schema.json").read_text(encoding="utf-8"))

    Draft202012Validator(snapshot_schema).validate(snapshot.canonical())
    Draft202012Validator(diff_schema).validate(diff.canonical())
    resolver = RefResolver(base_uri=(ROOT / "schemas/r11/").as_uri() + "/", referrer=bridge_schema)
    Draft202012Validator(bridge_schema, resolver=resolver).validate(package.canonical())
