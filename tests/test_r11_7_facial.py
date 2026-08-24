from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import validate

from kodepoia.media.alignment.adapters import make_synthetic_alignment
from kodepoia.media.alignment.visemes import build_viseme_timeline, default_viseme_set
from kodepoia.media.facial.adapters import R10FacialTargetAdapter, R5FacialTrackKind, build_godot_facial_intents
from kodepoia.media.facial.contracts import (
    FacialLODLevel,
    FacialMapping,
    FacialPerformanceProfile,
    FacialTarget,
    FacialTargetCatalog,
    FacialTargetKind,
    validate_profile_against_catalog,
)
from kodepoia.media.facial.curves import FacialCurveKey, FacialCurveSet, FacialTargetCurve, build_facial_curves
from kodepoia.media.facial.qa import FacialQAProfile, FacialQAStatus, evaluate_facial_qa


def _catalog() -> FacialTargetCatalog:
    return FacialTargetCatalog(
        "r10.face.synthetic.v1",
        "b" * 64,
        (
            FacialTarget("target.jaw_open", "mouth.open", FacialTargetKind.BLEND_SHAPE, 0.0, 1.0, "c" * 64),
            FacialTarget("target.lip_close", "mouth.close", FacialTargetKind.BLEND_SHAPE, 0.0, 1.0, "d" * 64),
            FacialTarget("target.jaw_bone", "jaw.rotate", FacialTargetKind.BONE, -1.0, 1.0, "e" * 64),
        ),
    )


def _profile(catalog: FacialTargetCatalog, *, clamp: bool = False, open_weight: float = 0.8) -> FacialPerformanceProfile:
    visemes = default_viseme_set()
    return FacialPerformanceProfile(
        "facial.profile.synthetic.v1",
        catalog.digest(),
        visemes.digest(),
        (
            FacialMapping("viseme.a", "target.jaw_open", open_weight),
            FacialMapping("viseme.mbp", "target.lip_close", 0.9),
            FacialMapping("viseme.tdn", "target.jaw_bone", 0.25),
        ),
        (
            FacialLODLevel(
                "lod.full",
                ("target.jaw_open", "target.lip_close", "target.jaw_bone"),
                60,
                ("mouth.open", "mouth.close"),
            ),
            FacialLODLevel(
                "lod.low",
                ("target.jaw_open", "target.lip_close"),
                10,
                ("mouth.open", "mouth.close"),
            ),
        ),
        clamp_out_of_range=clamp,
    )


def _timeline():
    alignment = make_synthetic_alignment(
        timeline_id="align.synthetic.r11.7",
        audio_sha256="a" * 64,
        locale="fr-FR",
        duration_seconds=1.2,
        phonemes=("a", "m", "t", "sil"),
    )
    return build_viseme_timeline(alignment, default_viseme_set(), timeline_id="viseme.synthetic.r11.7")


def test_r10_metadata_adapter_is_strict_and_identity_bound() -> None:
    catalog = _catalog()
    doc = catalog.canonical()
    parsed = R10FacialTargetAdapter.from_metadata(doc)
    assert parsed.digest() == catalog.digest()
    with pytest.raises(ValueError):
        R10FacialTargetAdapter.from_metadata({**doc, "raw_path": "res://spoof"})
    bad = {**doc, "targets": [{**doc["targets"][0], "kind": "script"}]}
    with pytest.raises(ValueError):
        R10FacialTargetAdapter.from_metadata(bad)


def test_profile_rejects_missing_spoofed_or_out_of_range_targets() -> None:
    catalog = _catalog()
    profile = _profile(catalog)
    validate_profile_against_catalog(profile, catalog)
    missing = FacialPerformanceProfile(
        "facial.profile.bad",
        catalog.digest(),
        default_viseme_set().digest(),
        (FacialMapping("viseme.a", "target.missing", 0.5),),
        (FacialLODLevel("lod.bad", ("target.missing",), 30),),
    )
    with pytest.raises(KeyError):
        validate_profile_against_catalog(missing, catalog)
    with pytest.raises(ValueError):
        validate_profile_against_catalog(_profile(catalog, open_weight=1.5), catalog)


def test_lod_must_preserve_declared_critical_semantics() -> None:
    catalog = _catalog()
    profile = FacialPerformanceProfile(
        "facial.profile.lodbad",
        catalog.digest(),
        default_viseme_set().digest(),
        (FacialMapping("viseme.a", "target.jaw_open", 0.8),),
        (FacialLODLevel("lod.bad", ("target.jaw_open",), 30, ("mouth.open", "mouth.close")),),
    )
    with pytest.raises(ValueError, match="does not preserve"):
        validate_profile_against_catalog(profile, catalog)


def test_facial_curves_are_deterministic_and_lod_filtered() -> None:
    catalog = _catalog()
    profile = _profile(catalog)
    timeline = _timeline()
    full_a = build_facial_curves(timeline, profile, catalog, curve_set_id="curves.full", lod_id="lod.full")
    full_b = build_facial_curves(timeline, profile, catalog, curve_set_id="curves.full", lod_id="lod.full")
    assert full_a.digest() == full_b.digest()
    assert {curve.target_id for curve in full_a.curves} == {"target.jaw_open", "target.lip_close", "target.jaw_bone"}
    low = build_facial_curves(timeline, profile, catalog, curve_set_id="curves.low", lod_id="lod.low")
    assert {curve.target_id for curve in low.curves} == {"target.jaw_open", "target.lip_close"}
    assert all(len(curve.keys) <= 13 for curve in low.curves)


def test_clamp_is_explicit_and_reported() -> None:
    catalog = _catalog()
    profile = _profile(catalog, clamp=True, open_weight=1.5)
    curves = build_facial_curves(_timeline(), profile, catalog, curve_set_id="curves.clamped", lod_id="lod.full")
    assert curves.clipped_key_count > 0
    report = evaluate_facial_qa(curves, profile, catalog, qa_profile=FacialQAProfile(max_clipped_keys=0))
    assert report.status is FacialQAStatus.FAIL
    assert "clipped_key_budget_exceeded" in report.blockers


def test_qa_enforces_key_budget_and_missing_targets() -> None:
    catalog = _catalog()
    profile = _profile(catalog)
    curves = build_facial_curves(_timeline(), profile, catalog, curve_set_id="curves.qa", lod_id="lod.full")
    report = evaluate_facial_qa(curves, profile, catalog, qa_profile=FacialQAProfile(max_total_keys=2))
    assert report.status is FacialQAStatus.FAIL
    assert "key_budget_exceeded" in report.blockers
    spoof = FacialCurveSet(
        "curves.spoof",
        profile.digest(),
        _timeline().digest(),
        catalog.digest(),
        "lod.full",
        1.2,
        (FacialTargetCurve("target.unknown", (FacialCurveKey(0.0, 0.0), FacialCurveKey(0.2, 0.5))),),
        0,
    )
    report = evaluate_facial_qa(spoof, profile, catalog)
    assert "missing_target" in report.blockers


def test_r5_intents_are_typed_and_contain_no_raw_resource_or_script_surface() -> None:
    catalog = _catalog()
    profile = _profile(catalog)
    curves = build_facial_curves(_timeline(), profile, catalog, curve_set_id="curves.intent", lod_id="lod.full")
    intents = build_godot_facial_intents(curves, catalog)
    assert intents
    by_target = {intent.target_id: intent for intent in intents}
    assert by_target["target.jaw_open"].track_kind is R5FacialTrackKind.BLEND_SHAPE
    assert by_target["target.jaw_bone"].track_kind is R5FacialTrackKind.BONE_PROPERTY
    for intent in intents:
        payload = intent.canonical()
        assert "script" not in payload and "path" not in payload and "resource" not in payload


def test_schema_examples_validate() -> None:
    catalog = _catalog()
    profile = _profile(catalog)
    curves = build_facial_curves(_timeline(), profile, catalog, curve_set_id="curves.schema", lod_id="lod.full")
    intent = build_godot_facial_intents(curves, catalog)[0]
    report = evaluate_facial_qa(curves, profile, catalog)
    fixtures = (
        ("facial-target-catalog.schema.json", catalog.canonical()),
        ("facial-performance-profile.schema.json", profile.canonical()),
        ("facial-curve-set.schema.json", curves.canonical()),
        ("godot-facial-animation-intent.schema.json", intent.canonical()),
        ("facial-qa.schema.json", report.canonical()),
    )
    for filename, payload in fixtures:
        schema = json.loads(Path("schemas/r11", filename).read_text(encoding="utf-8"))
        validate(instance=payload, schema=schema)


def test_non_finite_curve_values_fail_closed() -> None:
    with pytest.raises(ValueError):
        FacialCurveKey(0.0, float("nan"))
