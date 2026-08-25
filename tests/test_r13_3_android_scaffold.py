from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.core.audit import AuditLog
from kodepoia.core.backup import BackupManager
from kodepoia.core.safe_change import SafeChangeManager
from kodepoia.desktop.app_model import canonical_sample_app
from kodepoia.mobile.android_scaffold import (
    AndroidDependencyEvidence,
    AndroidPreviewAction,
    AndroidScaffoldDefinition,
    AndroidScaffoldEngine,
    AndroidScaffoldLineage,
    AndroidStringCatalog,
)
from kodepoia.mobile.contracts import MobileFormFactor, MobilePackageKind, MobileSourceKind
from kodepoia.project.dna import (
    MobileProjectProfile,
    Platform,
    ProjectDNA,
    ProjectType,
)

ROOT = Path(__file__).resolve().parents[1]


def _sha(ch: str) -> str:
    return ch * 64


def _evidence() -> AndroidDependencyEvidence:
    return AndroidDependencyEvidence(
        evidence_id="android.compose.2026-08-25",
        android_gradle_plugin="9.1.2",
        compose_bom="2026.08.00",
        compile_sdk=37,
        observed_on="2026-08-25",
        source_urls=(
            "https://developer.android.com/build/migrate-to-catalogs",
            "https://developer.android.com/develop/ui/compose/setup-compose-dependencies-and-compiler",
        ),
    )


def _dna(*, name: str = "Mobile Fixture", source_kind: MobileSourceKind = MobileSourceKind.NATIVE) -> ProjectDNA:
    return ProjectDNA(
        schema_version=1,
        name=name,
        project_type=ProjectType.MOBILE_APP,
        platforms=[Platform.ANDROID],
        mobile=MobileProjectProfile(
            source_kind=source_kind,
            form_factors=(MobileFormFactor.PHONE, MobileFormFactor.TABLET),
            android_application_id="com.kodepoia.fixture",
            android_min_api=26,
            android_target_api=36,
            package_kinds=(MobilePackageKind.APK, MobilePackageKind.AAB),
        ),
    )


def _definition(*, name: str = "Mobile Fixture") -> AndroidScaffoldDefinition:
    return AndroidScaffoldDefinition.from_project(
        _dna(name=name),
        canonical_sample_app(),
        _evidence(),
        catalogs=(
            AndroidStringCatalog("en", (("app_name", name), ("status_ready", "Ready"))),
            AndroidStringCatalog("fr", (("app_name", name), ("status_ready", "Prêt"))),
        ),
    )


def _lineage() -> AndroidScaffoldLineage:
    return AndroidScaffoldLineage(_sha("a"), _sha("b"))


def test_r13_3_definition_and_workspace_manifest_match_strict_schemas() -> None:
    model = canonical_sample_app()
    definition = _definition()
    files, manifest = AndroidScaffoldEngine().render(definition, model, _lineage())
    assert files

    definition_schema = json.loads(
        (ROOT / "schemas/r13/android-scaffold-definition.schema.json").read_text(encoding="utf-8")
    )
    workspace_schema = json.loads(
        (ROOT / "schemas/r13/android-workspace-manifest.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(definition_schema)
    Draft202012Validator.check_schema(workspace_schema)
    Draft202012Validator(definition_schema).validate(definition.to_dict())
    Draft202012Validator(workspace_schema).validate(manifest.to_dict())


def test_r13_3_same_definition_is_byte_and_semantic_manifest_deterministic() -> None:
    engine = AndroidScaffoldEngine()
    model = canonical_sample_app()
    definition = _definition()
    files_a, manifest_a = engine.render(definition, model, _lineage())
    files_b, manifest_b = engine.render(definition, model, _lineage())

    assert files_a == files_b
    assert manifest_a.canonical_bytes() == manifest_b.canonical_bytes()
    assert manifest_a.digest() == manifest_b.digest()
    assert [item.path for item in files_a] == sorted(item.path for item in files_a)
    assert all("\r" not in item.content for item in files_a)
    assert all(hashlib.sha256(item.content.encode()).hexdigest() == item.sha256 for item in files_a)


def test_r13_3_fixed_android_project_contains_kotlin_dsl_compose_and_localization() -> None:
    files, manifest = AndroidScaffoldEngine().render(_definition(), canonical_sample_app(), _lineage())
    by_path = {item.path: item.content for item in files}
    expected = {
        "settings.gradle.kts",
        "build.gradle.kts",
        "gradle/libs.versions.toml",
        "app/build.gradle.kts",
        "app/src/main/AndroidManifest.xml",
        "app/src/main/java/com/kodepoia/fixture/MainActivity.kt",
        "app/src/main/java/com/kodepoia/fixture/KodepoiaAppModel.kt",
        "app/src/main/res/values/strings.xml",
        "app/src/main/res/values-fr/strings.xml",
    }
    assert expected <= set(by_path)
    assert 'compose-bom = "2026.08.00"' in by_path["gradle/libs.versions.toml"]
    assert 'agp = "9.1.2"' in by_path["gradle/libs.versions.toml"]
    assert "latest" not in by_path["gradle/libs.versions.toml"].lower()
    assert "buildFeatures" in by_path["app/build.gradle.kts"]
    assert "compose = true" in by_path["app/build.gradle.kts"]
    assert "BoxWithConstraints" in by_path["app/src/main/java/com/kodepoia/fixture/MainActivity.kt"]
    assert "contentDescription" in by_path["app/src/main/java/com/kodepoia/fixture/MainActivity.kt"]
    assert canonical_sample_app().digest() in by_path[
        "app/src/main/java/com/kodepoia/fixture/KodepoiaAppModel.kt"
    ]
    assert manifest.dependency_evidence_sha256 == _evidence().digest()


def test_r13_3_external_mutable_latest_and_unofficial_evidence_fail_closed() -> None:
    with pytest.raises(ValueError, match="explicit numeric"):
        replace(_evidence(), android_gradle_plugin="latest")
    with pytest.raises(ValueError, match="explicit YYYY"):
        replace(_evidence(), compose_bom="latest")
    with pytest.raises(ValueError, match="developer.android.com"):
        replace(_evidence(), source_urls=("https://example.com/android",))
    with pytest.raises(ValueError, match="below target_sdk"):
        replace(_definition(), dependency_evidence=replace(_evidence(), compile_sdk=35))


def test_r13_3_native_partition_rejects_non_mobile_and_godot_export() -> None:
    model = canonical_sample_app()
    bad = _dna()
    bad.project_type = ProjectType.TOOL
    with pytest.raises(ValueError):
        AndroidScaffoldDefinition.from_project(bad, model, _evidence())

    godot = ProjectDNA(
        schema_version=1,
        name="Game",
        project_type=ProjectType.GAME,
        platforms=[Platform.ANDROID],
        engine="Godot",
        dimension=None,
        mobile=MobileProjectProfile(
            source_kind=MobileSourceKind.GODOT_EXPORT,
            android_application_id="com.kodepoia.game",
            android_min_api=26,
            android_target_api=36,
        ),
    )
    with pytest.raises(ValueError):
        AndroidScaffoldDefinition.from_project(godot, model, _evidence())


def test_r13_3_app_name_is_context_escaped_not_executable_template_text() -> None:
    name = 'Mobile <Fixture> & "Safe"'
    definition = _definition(name=name)
    files, _ = AndroidScaffoldEngine().render(definition, canonical_sample_app(), _lineage())
    by_path = {item.path: item.content for item in files}
    assert 'rootProject.name = "Mobile <Fixture> & \\"Safe\\""' in by_path["settings.gradle.kts"]
    assert "Mobile &lt;Fixture&gt; &amp; &quot;Safe&quot;" in by_path[
        "app/src/main/res/values/strings.xml"
    ]


def test_r13_3_render_does_not_launch_subprocess_or_require_android_sdk(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("R13.3 must not launch external processes")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    files, _ = AndroidScaffoldEngine().render(_definition(), canonical_sample_app(), _lineage())
    assert files


def test_r13_3_preview_preserves_user_owned_readme_and_creates_generated_files(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    (root / "README.md").write_text("user notes\n", encoding="utf-8")
    engine = AndroidScaffoldEngine()
    preview = engine.preview(root, _definition(), canonical_sample_app(), _lineage())
    actions = {item.path: item.action for item in preview.items}
    assert actions["README.md"] is AndroidPreviewAction.PRESERVE
    assert actions["app/build.gradle.kts"] is AndroidPreviewAction.CREATE
    engine.apply(root, preview)
    assert (root / "README.md").read_text(encoding="utf-8") == "user notes\n"
    assert (root / "app/build.gradle.kts").is_file()
    assert (root / AndroidScaffoldEngine.MANIFEST_PATH).is_file()


def test_r13_3_tampered_generated_file_cannot_authorize_replacement(tmp_path: Path) -> None:
    root = tmp_path / "project"
    engine = AndroidScaffoldEngine()
    first = engine.preview(root, _definition(), canonical_sample_app(), _lineage())
    engine.apply(root, first)
    target = root / "app/build.gradle.kts"
    target.write_text("user changed generated file\n", encoding="utf-8")

    changed = engine.preview(root, _definition(name="Renamed App"), canonical_sample_app(), _lineage())
    action = next(item.action for item in changed.items if item.path == "app/build.gradle.kts")
    assert action is AndroidPreviewAction.CONFLICT
    with pytest.raises(FileExistsError, match="conflicts"):
        engine.apply(root, changed)


def test_r13_3_regeneration_uses_safechange_backup_and_audit(tmp_path: Path) -> None:
    root = tmp_path / "project"
    engine = AndroidScaffoldEngine()
    model = canonical_sample_app()
    first = engine.preview(root, _definition(), model, _lineage())
    engine.apply(root, first)

    changed = engine.preview(root, _definition(name="Renamed App"), model, _lineage())
    assert changed.destructive
    with pytest.raises(ValueError, match="SafeChangeManager and BackupManager"):
        engine.apply(root, changed)

    safe_change = SafeChangeManager(root, root / ".kodepoia/snapshots")
    backups = BackupManager(tmp_path / "backups")
    audit = AuditLog(tmp_path / "audit.jsonl")
    engine.apply(
        root,
        changed,
        safe_change=safe_change,
        backup_manager=backups,
        audit_log=audit,
    )
    archives = list((tmp_path / "backups").glob("*.zip"))
    assert len(archives) == 1
    assert backups.verify(archives[0])
    assert audit.verify()
    assert any((root / ".kodepoia/snapshots").iterdir())


def test_r13_3_symlink_escape_fails_closed_when_supported(tmp_path: Path) -> None:
    root = tmp_path / "project"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    link = root / "app"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")

    with pytest.raises(ValueError, match="escapes project root"):
        AndroidScaffoldEngine().preview(root, _definition(), canonical_sample_app(), _lineage())
    assert not any(outside.iterdir())


def test_r13_3_manifest_binds_definition_dna_product_model_and_dependency_evidence() -> None:
    definition = _definition()
    model = canonical_sample_app()
    files, manifest = AndroidScaffoldEngine().render(definition, model, _lineage())
    assert manifest.definition_sha256 == definition.digest()
    assert manifest.dependency_evidence_sha256 == definition.dependency_evidence.digest()
    assert manifest.app_model_sha256 == model.digest()
    assert manifest.dna_sha256 == _sha("a")
    assert manifest.product_sha256 == _sha("b")
    assert all(item.sha256 for item in files)
