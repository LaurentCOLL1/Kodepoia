from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.desktop.app_model import canonical_sample_app
from kodepoia.mobile.boundary import MobileBoundaryError, MobileToolchainBoundary
from kodepoia.mobile.contracts import MobileFormFactor, MobilePackageKind, MobileSourceKind
from kodepoia.mobile.ios_scaffold import (
    ApplePreviewAction,
    AppleScaffoldDefinition,
    AppleScaffoldEngine,
    AppleScaffoldLineage,
    AppleStateStrategy,
    AppleStringCatalog,
    GodotIOSExportBridgeDefinition,
    build_ios_simulator_build_argv,
)
from kodepoia.project.dna import Dimension, MobileProjectProfile, Platform, ProjectDNA, ProjectType

ROOT = Path(__file__).resolve().parents[1]


def _sha(ch: str) -> str:
    return ch * 64


def _dna(*, minimum: str = "17.0", name: str = "Apple Fixture") -> ProjectDNA:
    return ProjectDNA(
        schema_version=1,
        name=name,
        project_type=ProjectType.MOBILE_APP,
        platforms=[Platform.IOS],
        mobile=MobileProjectProfile(
            source_kind=MobileSourceKind.NATIVE,
            form_factors=(MobileFormFactor.PHONE, MobileFormFactor.TABLET),
            apple_bundle_id="com.kodepoia.fixture",
            apple_min_version=minimum,
            apple_target_version="26.0",
            package_kinds=(MobilePackageKind.APP,),
        ),
    )


def _definition(*, minimum: str = "17.0", name: str = "Apple Fixture") -> AppleScaffoldDefinition:
    return AppleScaffoldDefinition.from_project(
        _dna(minimum=minimum, name=name),
        canonical_sample_app(),
        catalogs=(
            AppleStringCatalog("en", (("app_name", name), ("status_ready", "Ready"))),
            AppleStringCatalog("fr", (("app_name", name), ("status_ready", "Prêt"))),
        ),
    )


def _lineage() -> AppleScaffoldLineage:
    return AppleScaffoldLineage(_sha("a"), _sha("b"))


def test_r13_9_definition_and_manifest_match_strict_schemas() -> None:
    model = canonical_sample_app()
    definition = _definition()
    files, manifest = AppleScaffoldEngine().render(definition, model, _lineage())
    assert files
    definition_schema = json.loads(
        (ROOT / "schemas/r13/apple-scaffold-definition.schema.json").read_text(encoding="utf-8")
    )
    manifest_schema = json.loads(
        (ROOT / "schemas/r13/apple-workspace-manifest.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(definition_schema)
    Draft202012Validator.check_schema(manifest_schema)
    Draft202012Validator(definition_schema).validate(definition.to_dict())
    Draft202012Validator(manifest_schema).validate(manifest.to_dict())


def test_r13_9_render_is_byte_and_semantic_manifest_deterministic() -> None:
    model = canonical_sample_app()
    engine = AppleScaffoldEngine()
    definition = _definition()
    files_a, manifest_a = engine.render(definition, model, _lineage())
    files_b, manifest_b = engine.render(definition, model, _lineage())
    assert files_a == files_b
    assert manifest_a.canonical_bytes() == manifest_b.canonical_bytes()
    assert manifest_a.digest() == manifest_b.digest()
    assert [item.path for item in files_a] == sorted(item.path for item in files_a)
    assert all("\r" not in item.content for item in files_a)
    assert all(hashlib.sha256(item.content.encode()).hexdigest() == item.sha256 for item in files_a)


def test_r13_9_project_contains_swiftui_xcode_assets_localizations_and_shared_model() -> None:
    model = canonical_sample_app()
    files, manifest = AppleScaffoldEngine().render(_definition(), model, _lineage())
    by_path = {item.path: item.content for item in files}
    expected = {
        "KodepoiaIOS.xcodeproj/project.pbxproj",
        "KodepoiaIOS.xcodeproj/xcshareddata/xcschemes/KodepoiaIOS.xcscheme",
        "KodepoiaIOS/KodepoiaIOSApp.swift",
        "KodepoiaIOS/AppState.swift",
        "KodepoiaIOS/AppModelContract.swift",
        "KodepoiaIOS/ContentView.swift",
        "KodepoiaIOS/Info.plist",
        "KodepoiaIOS/Assets.xcassets/Contents.json",
        "KodepoiaIOS/en.lproj/Localizable.strings",
        "KodepoiaIOS/fr.lproj/Localizable.strings",
    }
    assert expected <= set(by_path)
    assert "import SwiftUI" in by_path["KodepoiaIOS/KodepoiaIOSApp.swift"]
    assert "@Observable" in by_path["KodepoiaIOS/AppState.swift"]
    assert model.digest() in by_path["KodepoiaIOS/AppModelContract.swift"]
    assert 'PRODUCT_BUNDLE_IDENTIFIER = "com.kodepoia.fixture";' in by_path[
        "KodepoiaIOS.xcodeproj/project.pbxproj"
    ]
    assert 'TARGETED_DEVICE_FAMILY = "1,2"' in by_path["KodepoiaIOS.xcodeproj/project.pbxproj"]
    assert manifest.state_strategy is AppleStateStrategy.OBSERVATION


def test_r13_9_pre_ios17_uses_documented_observable_object_compatibility() -> None:
    model = canonical_sample_app()
    definition = _definition(minimum="16.0")
    files, manifest = AppleScaffoldEngine().render(definition, model, _lineage())
    state = {item.path: item.content for item in files}["KodepoiaIOS/AppState.swift"]
    content = {item.path: item.content for item in files}["KodepoiaIOS/ContentView.swift"]
    assert definition.state_strategy is AppleStateStrategy.OBSERVABLE_OBJECT_COMPAT
    assert manifest.state_strategy is AppleStateStrategy.OBSERVABLE_OBJECT_COMPAT
    assert "ObservableObject" in state
    assert "@Published" in state
    assert "@StateObject" in content
    assert "@Observable" not in state


def test_r13_9_invalid_bundle_and_os_intent_fail_through_project_dna() -> None:
    bad_bundle = _dna()
    assert bad_bundle.mobile is not None
    bad_bundle.mobile.apple_bundle_id = "../../escape"
    with pytest.raises(ValueError):
        AppleScaffoldDefinition.from_project(bad_bundle, canonical_sample_app())

    bad_versions = _dna()
    assert bad_versions.mobile is not None
    bad_versions.mobile.apple_min_version = "27.0"
    bad_versions.mobile.apple_target_version = "26.0"
    with pytest.raises(ValueError):
        AppleScaffoldDefinition.from_project(bad_versions, canonical_sample_app())


def test_r13_9_godot_bridge_is_metadata_only_and_execution_remains_r5_owned() -> None:
    dna = ProjectDNA(
        schema_version=1,
        name="Godot iOS Fixture",
        project_type=ProjectType.GAME,
        platforms=[Platform.IOS],
        engine="Godot",
        dimension=Dimension.D3,
        mobile=MobileProjectProfile(
            source_kind=MobileSourceKind.GODOT_EXPORT,
            form_factors=(MobileFormFactor.PHONE,),
            apple_bundle_id="com.kodepoia.godotfixture",
            apple_min_version="17.0",
            apple_target_version="26.0",
            package_kinds=(MobilePackageKind.APP,),
        ),
    )
    definition = AppleScaffoldDefinition.from_project(dna, canonical_sample_app())
    assert definition.godot_export_bridge == GodotIOSExportBridgeDefinition()
    assert definition.godot_export_bridge.execution_owned_by_r5 is True
    with pytest.raises(ValueError, match="R5 owns"):
        AppleScaffoldEngine().render(definition, canonical_sample_app(), _lineage())


def test_r13_9_app_name_and_localization_are_context_escaped() -> None:
    name = 'Apple <Fixture> & "Safe"'
    files, _ = AppleScaffoldEngine().render(_definition(name=name), canonical_sample_app(), _lineage())
    by_path = {item.path: item.content for item in files}
    assert "Apple &lt;Fixture&gt; &amp; &quot;Safe&quot;" in by_path["KodepoiaIOS/Info.plist"]
    assert '\\"Safe\\"' in by_path["KodepoiaIOS/en.lproj/Localizable.strings"]
    assert name not in by_path["KodepoiaIOS.xcodeproj/project.pbxproj"]


def test_r13_9_render_does_not_launch_external_process(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("R13.9 render must not launch Xcode")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    files, _ = AppleScaffoldEngine().render(_definition(), canonical_sample_app(), _lineage())
    assert files


def test_r13_9_preview_preserves_user_readme_and_detects_tampered_generated_file(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    (root / "README.md").write_text("user notes\n", encoding="utf-8")
    engine = AppleScaffoldEngine()
    first = engine.preview(root, _definition(), canonical_sample_app(), _lineage())
    actions = {item.path: item.action for item in first.items}
    assert actions["README.md"] is ApplePreviewAction.PRESERVE
    engine.apply(root, first)
    assert (root / "README.md").read_text(encoding="utf-8") == "user notes\n"

    target = root / "KodepoiaIOS/ContentView.swift"
    target.write_text("user tamper\n", encoding="utf-8")
    changed = engine.preview(root, _definition(name="Renamed"), canonical_sample_app(), _lineage())
    action = next(item.action for item in changed.items if item.path == "KodepoiaIOS/ContentView.swift")
    assert action is ApplePreviewAction.CONFLICT
    with pytest.raises(FileExistsError, match="conflicts"):
        engine.apply(root, changed)


def test_r13_9_symlink_escape_fails_closed_when_supported(tmp_path: Path) -> None:
    root = tmp_path / "project"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    link = root / "KodepoiaIOS"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")
    with pytest.raises(ValueError, match="escapes project root"):
        AppleScaffoldEngine().preview(root, _definition(), canonical_sample_app(), _lineage())
    assert not any(outside.iterdir())


def test_r13_9_fixed_simulator_argv_rejects_raw_scheme_and_paths(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    project_root = tmp_path / "project"
    staging = tmp_path / "staging"
    runtime.mkdir()
    project_root.mkdir()
    staging.mkdir()
    tool = runtime / "xcodebuild"
    tool.write_text("fixture", encoding="utf-8")
    project = project_root / "KodepoiaIOS.xcodeproj"
    project.mkdir()
    boundary = MobileToolchainBoundary(
        allowed_runtime_roots=(runtime,),
        project_root=project_root,
        staging_root=staging,
    )
    argv = build_ios_simulator_build_argv(
        boundary,
        tool,
        project_file=project,
        scheme="KodepoiaIOS",
        derived_data_path=staging / "DerivedData",
    )
    assert "generic/platform=iOS Simulator" in argv
    assert "CODE_SIGNING_ALLOWED=NO" in argv
    assert "CODE_SIGNING_REQUIRED=NO" in argv
    assert argv[-1] == "build"
    assert "-sdk" not in argv
    with pytest.raises(MobileBoundaryError):
        build_ios_simulator_build_argv(
            boundary,
            tool,
            project_file=project,
            scheme="KodepoiaIOS -showBuildSettings",
            derived_data_path=staging / "DerivedData",
        )
    with pytest.raises(MobileBoundaryError):
        build_ios_simulator_build_argv(
            boundary,
            tool,
            project_file=project,
            scheme="KodepoiaIOS",
            derived_data_path=tmp_path / "outside" / "DerivedData",
        )


def test_r13_9_manifest_binds_definition_model_and_lineage() -> None:
    model = canonical_sample_app()
    definition = _definition()
    _, manifest = AppleScaffoldEngine().render(definition, model, _lineage())
    assert manifest.definition_sha256 == definition.digest()
    assert manifest.app_model_sha256 == model.digest()
    assert manifest.dna_sha256 == _sha("a")
    assert manifest.product_sha256 == _sha("b")
