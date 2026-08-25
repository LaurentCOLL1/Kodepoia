from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.desktop.app_model import canonical_sample_app
from kodepoia.mobile.android_build import (
    AndroidArtifactKind,
    AndroidBuildEvidence,
    AndroidBuildRequest,
    AndroidBuildStatus,
    AndroidBuildTask,
    AndroidBuildToolchainEvidence,
    inspect_android_artifact,
    prepare_build_staging,
    sanitize_build_environment,
    verify_source_workspace,
)
from kodepoia.mobile.android_scaffold import (
    AndroidDependencyEvidence,
    AndroidScaffoldDefinition,
    AndroidScaffoldEngine,
    AndroidScaffoldLineage,
)
from kodepoia.mobile.contracts import MobileFormFactor, MobilePackageKind, MobileSourceKind
from kodepoia.project.dna import MobileProjectProfile, Platform, ProjectDNA, ProjectType

ROOT = Path(__file__).resolve().parents[1]


def _sha(text: bytes) -> str:
    return hashlib.sha256(text).hexdigest()


def _toolchain() -> AndroidBuildToolchainEvidence:
    return AndroidBuildToolchainEvidence(
        evidence_id="android.build.2026-08-25",
        android_gradle_plugin="9.3.1",
        gradle_version="9.5.0",
        kotlin_version="2.3.21",
        compose_bom="2026.08.00",
        compile_sdk=37,
        build_tools_version="36.0.0",
        jdk_major=17,
        observed_on="2026-08-25",
        source_urls=(
            "https://developer.android.com/build/releases/agp-9-3-0-release-notes",
            "https://developer.android.com/develop/ui/compose/setup-compose-dependencies-and-compiler",
        ),
    )


def _source_dependency() -> AndroidDependencyEvidence:
    return AndroidDependencyEvidence(
        evidence_id="android.compose.r13-3",
        android_gradle_plugin="9.1.2",
        compose_bom="2026.08.00",
        compile_sdk=37,
        observed_on="2026-08-25",
        source_urls=(
            "https://developer.android.com/build/releases/about-agp",
            "https://developer.android.com/develop/ui/compose/setup-compose-dependencies-and-compiler",
        ),
    )


def _dna() -> ProjectDNA:
    return ProjectDNA(
        schema_version=1,
        name="R13 Android Build Fixture",
        project_type=ProjectType.MOBILE_APP,
        platforms=[Platform.ANDROID],
        mobile=MobileProjectProfile(
            source_kind=MobileSourceKind.NATIVE,
            form_factors=(MobileFormFactor.PHONE, MobileFormFactor.TABLET),
            android_application_id="com.kodepoia.r13fixture",
            android_min_api=26,
            android_target_api=36,
            package_kinds=(MobilePackageKind.APK, MobilePackageKind.AAB),
        ),
    )


def _workspace(root: Path) -> tuple[str, Path]:
    model = canonical_sample_app()
    definition = AndroidScaffoldDefinition.from_project(_dna(), model, _source_dependency())
    lineage = AndroidScaffoldLineage(_sha(b"dna"), _sha(b"product"))
    engine = AndroidScaffoldEngine()
    preview = engine.preview(root, definition, model, lineage)
    manifest = engine.apply(root, preview)
    return manifest.digest(), root


def _request(manifest_sha: str) -> AndroidBuildRequest:
    return AndroidBuildRequest(
        source_workspace_manifest_sha256=manifest_sha,
        application_id="com.kodepoia.r13fixture",
        min_sdk=26,
        target_sdk=36,
    )


def _zip(path: Path, entries: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in entries.items():
            archive.writestr(name, payload)


def test_r13_4_toolchain_and_request_are_explicit_and_fixed() -> None:
    toolchain = _toolchain()
    assert toolchain.gradle_version == "9.5.0"
    assert toolchain.jdk_major == 17
    request = _request("a" * 64)
    assert request.argv() == (
        "--no-daemon",
        "--stacktrace",
        ":app:bundleRelease",
        ":app:assembleDebug",
        ":app:testDebugUnitTest",
    )
    assert all("-P" not in item for item in request.argv())
    assert all("init" not in item.casefold() for item in request.argv())


def test_r13_4_dynamic_versions_and_unofficial_sources_fail_closed() -> None:
    with pytest.raises(ValueError, match="explicit numeric"):
        AndroidBuildToolchainEvidence(
            **{**_toolchain().__dict__, "android_gradle_plugin": "9.3.+"}  # type: ignore[attr-defined]
        )


def test_r13_4_unsafe_environment_is_rejected_not_silently_forwarded() -> None:
    with pytest.raises(ValueError, match="GRADLE_OPTS"):
        sanitize_build_environment({"JAVA_HOME": "/jdk", "GRADLE_OPTS": "-Downed=true"})
    with pytest.raises(ValueError, match="ORG_GRADLE_PROJECT"):
        sanitize_build_environment({"ORG_GRADLE_PROJECT_secret": "owned"})
    clean = sanitize_build_environment(
        {"JAVA_HOME": "/jdk", "ANDROID_SDK_ROOT": "/sdk", "PATH": "/untrusted"}
    )
    assert clean == {"ANDROID_SDK_ROOT": "/sdk", "JAVA_HOME": "/jdk"}


def test_r13_4_source_manifest_must_match_every_scaffold_file(tmp_path: Path) -> None:
    manifest_sha, source = _workspace(tmp_path / "source")
    _, observed = verify_source_workspace(source)
    assert observed == manifest_sha
    target = source / "app/build.gradle.kts"
    target.write_text("tampered\n", encoding="utf-8")
    with pytest.raises(ValueError, match="digest mismatch"):
        verify_source_workspace(source)


def test_r13_4_build_overlay_is_deterministic_and_isolated(tmp_path: Path) -> None:
    manifest_sha, source = _workspace(tmp_path / "source")
    staging_a = tmp_path / "build-a"
    staging_b = tmp_path / "build-b"
    overlay_a = prepare_build_staging(source, staging_a, _toolchain())
    overlay_b = prepare_build_staging(source, staging_b, _toolchain())
    assert overlay_a.canonical_bytes() == overlay_b.canonical_bytes()
    assert overlay_a.source_workspace_manifest_sha256 == manifest_sha
    assert overlay_a.toolchain_sha256 == _toolchain().digest()

    catalog = (staging_a / "gradle/libs.versions.toml").read_text(encoding="utf-8")
    root_build = (staging_a / "build.gradle.kts").read_text(encoding="utf-8")
    app_build = (staging_a / "app/build.gradle.kts").read_text(encoding="utf-8")
    assert 'agp = "9.3.1"' in catalog
    assert 'kotlin = "2.3.21"' in catalog
    assert 'compose-bom = "2026.08.00"' in catalog
    assert "compose-compiler" in catalog
    assert "libs.plugins.compose.compiler" in root_build
    assert "libs.plugins.compose.compiler" in app_build
    assert "compileSdk = 37" in app_build
    assert 'agp = "9.1.2"' in (source / "gradle/libs.versions.toml").read_text(encoding="utf-8")


def test_r13_4_staging_inside_source_is_rejected(tmp_path: Path) -> None:
    _, source = _workspace(tmp_path / "source")
    with pytest.raises(ValueError, match="isolated"):
        prepare_build_staging(source, source / "nested-build", _toolchain())


def test_r13_4_valid_apk_and_aab_structural_evidence(tmp_path: Path) -> None:
    apk = tmp_path / "fixture.apk"
    aab = tmp_path / "fixture.aab"
    _zip(
        apk,
        {
            "AndroidManifest.xml": b"manifest",
            "classes.dex": b"dex",
            "resources.arsc": b"resources",
            "lib/arm64-v8a/libfixture.so": b"native",
        },
    )
    _zip(
        aab,
        {
            "base/manifest/AndroidManifest.xml": b"manifest",
            "base/dex/classes.dex": b"dex",
            "base/resources.pb": b"resources",
            "base/lib/arm64-v8a/libfixture.so": b"native",
        },
    )
    apk_evidence = inspect_android_artifact(apk, AndroidArtifactKind.APK)
    aab_evidence = inspect_android_artifact(aab, AndroidArtifactKind.AAB)
    assert apk_evidence.abis == ("arm64-v8a",)
    assert aab_evidence.abis == ("arm64-v8a",)
    assert apk_evidence.sha256 == _sha(apk.read_bytes())
    assert aab_evidence.sha256 == _sha(aab.read_bytes())


def test_r13_4_fake_or_traversing_packages_fail_closed(tmp_path: Path) -> None:
    fake = tmp_path / "fake.apk"
    _zip(fake, {"AndroidManifest.xml": b"manifest", "classes.dex": b"dex"})
    with pytest.raises(ValueError, match="missing required"):
        inspect_android_artifact(fake, AndroidArtifactKind.APK)

    escaping = tmp_path / "escape.aab"
    _zip(
        escaping,
        {
            "../owned": b"bad",
            "base/manifest/AndroidManifest.xml": b"manifest",
            "base/dex/classes.dex": b"dex",
            "base/resources.pb": b"resources",
        },
    )
    with pytest.raises(ValueError, match="unsafe Android build path"):
        inspect_android_artifact(escaping, AndroidArtifactKind.AAB)


def test_r13_4_pass_evidence_requires_both_artifacts_and_target_api_36() -> None:
    apk = type("E", (), {})
    with pytest.raises(ValueError, match="APK and AAB"):
        AndroidBuildEvidence(
            schema_version=1,
            source_sha="a" * 40,
            runner_os="Linux",
            source_workspace_manifest_sha256="b" * 64,
            overlay_manifest_sha256="c" * 64,
            toolchain=_toolchain(),
            request=_request("b" * 64),
            status=AndroidBuildStatus.PASS,
            duration_seconds=1.0,
            artifacts=(),
        )


def test_r13_4_evidence_schema_is_strict() -> None:
    schema = json.loads(
        (ROOT / "schemas/r13/android-build-evidence.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
