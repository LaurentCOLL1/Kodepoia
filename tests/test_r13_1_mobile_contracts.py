from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.mobile import (
    DeviceIdentity,
    DeviceTestMatrix,
    MobileApplicationIdentity,
    MobileArchitecture,
    MobileBoundaryError,
    MobileCapabilityReport,
    MobileCapabilityState,
    MobileFormFactor,
    MobileHostOS,
    MobilePackageKind,
    MobilePlatform,
    MobileSourceKind,
    MobileTargetProfile,
    MobileToolKind,
    MobileToolchainBoundary,
    MobileToolchainIdentity,
    StoreReadinessState,
    StoreReleaseStatus,
)
from kodepoia.mobile.contracts import canonical_json_bytes

ROOT = Path(__file__).resolve().parents[1]


def _tool(kind: MobileToolKind = MobileToolKind.ADB) -> MobileToolchainIdentity:
    name = {
        MobileToolKind.ADB: "adb",
        MobileToolKind.JAVA: "java",
        MobileToolKind.XCODEBUILD: "xcodebuild",
    }.get(kind, kind.value)
    return MobileToolchainIdentity(
        tool_kind=kind,
        executable_name=name,
        executable_sha256="a" * 64,
        version="1.0.0",
        host_os=MobileHostOS.LINUX,
        architecture=MobileArchitecture.X86_64,
        capabilities=("probe", "build", "probe"),
    )


def _boundary(tmp_path: Path) -> tuple[MobileToolchainBoundary, Path, Path, Path]:
    runtime = tmp_path / "runtime"
    project = tmp_path / "project"
    staging = tmp_path / "staging"
    runtime.mkdir()
    project.mkdir()
    staging.mkdir()
    return (
        MobileToolchainBoundary(
            allowed_runtime_roots=(runtime,),
            project_root=project,
            staging_root=staging,
        ),
        runtime,
        project,
        staging,
    )


def test_r13_1_target_profiles_are_platform_bounded_and_deterministic() -> None:
    android = MobileTargetProfile(
        profile_id="mobile.android",
        platform=MobilePlatform.ANDROID,
        form_factors=(MobileFormFactor.TABLET, MobileFormFactor.PHONE, MobileFormFactor.PHONE),
        source_kind=MobileSourceKind.NATIVE,
        minimum_platform_version="26.0",
        target_api_level=36,
        package_kinds=(MobilePackageKind.AAB, MobilePackageKind.APK),
    )
    assert android.form_factors == (MobileFormFactor.PHONE, MobileFormFactor.TABLET)
    assert android.digest() == MobileTargetProfile(
        profile_id="mobile.android",
        platform=MobilePlatform.ANDROID,
        form_factors=(MobileFormFactor.PHONE, MobileFormFactor.TABLET),
        source_kind=MobileSourceKind.NATIVE,
        minimum_platform_version="26.0",
        target_api_level=36,
        package_kinds=(MobilePackageKind.APK, MobilePackageKind.AAB),
    ).digest()

    apple = MobileTargetProfile(
        profile_id="mobile.ios",
        platform=MobilePlatform.IOS,
        form_factors=(MobileFormFactor.PHONE,),
        source_kind=MobileSourceKind.NATIVE,
        minimum_platform_version="18.0",
    )
    assert apple.target_api_level is None
    assert apple.package_kinds == (MobilePackageKind.APP, MobilePackageKind.XCARCHIVE)

    with pytest.raises(ValueError, match="target_api_level"):
        MobileTargetProfile(
            profile_id="bad.android",
            platform=MobilePlatform.ANDROID,
            form_factors=(MobileFormFactor.PHONE,),
            source_kind=MobileSourceKind.NATIVE,
            minimum_platform_version="26",
        )
    with pytest.raises(ValueError, match="do not use Android"):
        MobileTargetProfile(
            profile_id="bad.ios",
            platform=MobilePlatform.IOS,
            form_factors=(MobileFormFactor.PHONE,),
            source_kind=MobileSourceKind.NATIVE,
            minimum_platform_version="18",
            target_api_level=36,
        )
    with pytest.raises(ValueError, match="Android targets"):
        MobileTargetProfile(
            profile_id="bad.pkg",
            platform=MobilePlatform.ANDROID,
            form_factors=(MobileFormFactor.PHONE,),
            source_kind=MobileSourceKind.NATIVE,
            minimum_platform_version="26",
            target_api_level=36,
            package_kinds=(MobilePackageKind.IPA,),
        )


def test_r13_1_capability_state_cannot_be_manufactured_from_config() -> None:
    with pytest.raises(ValueError, match="AVAILABLE requires"):
        MobileCapabilityReport(
            adapter_id="android.local",
            platform=MobilePlatform.ANDROID,
            state=MobileCapabilityState.AVAILABLE,
            capabilities=("build",),
        )
    with pytest.raises(ValueError, match="requires at least one blocker"):
        MobileCapabilityReport(
            adapter_id="android.local",
            platform=MobilePlatform.ANDROID,
            state=MobileCapabilityState.UNAVAILABLE,
        )
    with pytest.raises(ValueError, match="NOT_PROBED"):
        MobileCapabilityReport(
            adapter_id="android.local",
            platform=MobilePlatform.ANDROID,
            state=MobileCapabilityState.NOT_PROBED,
            toolchains=(_tool(),),
        )

    report = MobileCapabilityReport(
        adapter_id="android.local",
        platform=MobilePlatform.ANDROID,
        state=MobileCapabilityState.AVAILABLE,
        toolchains=(_tool(),),
        capabilities=("test", "build", "build"),
    )
    assert report.capabilities == ("build", "test")
    assert len(report.digest()) == 64


def test_r13_1_identity_artifact_device_and_release_bindings() -> None:
    app = MobileApplicationIdentity(
        identity_id="app.android.sample",
        platform=MobilePlatform.ANDROID,
        package_identifier="io.kodepoia.sample",
    )
    with pytest.raises(ValueError, match="Android application id"):
        MobileApplicationIdentity(
            identity_id="bad",
            platform=MobilePlatform.ANDROID,
            package_identifier="../escape",
        )
    with pytest.raises(ValueError, match="Apple bundle"):
        MobileApplicationIdentity(
            identity_id="bad.apple",
            platform=MobilePlatform.IOS,
            package_identifier="bad bundle id",
        )

    device = DeviceIdentity(
        device_id="device.fixture.1",
        provider_id="hosted.ci",
        platform=MobilePlatform.ANDROID,
        architecture=MobileArchitecture.X86_64,
        os_version="16.0",
        model="virtual-phone",
        virtual=True,
        capabilities=("portrait", "landscape", "portrait"),
    )
    matrix = DeviceTestMatrix(
        matrix_id="matrix.fixture",
        platform=MobilePlatform.ANDROID,
        device_digests=(device.digest(),),
        locales=("fr-FR", "en-US"),
        orientations=("portrait", "landscape"),
    )
    assert matrix.locales == ("en-US", "fr-FR")
    assert app.digest() != device.digest()

    with pytest.raises(ValueError, match="STORE_READY"):
        StoreReleaseStatus(
            release_id="release.bad",
            platform=MobilePlatform.ANDROID,
            readiness=StoreReadinessState.STORE_READY,
        )
    status = StoreReleaseStatus(
        release_id="release.ok",
        platform=MobilePlatform.ANDROID,
        readiness=StoreReadinessState.STORE_READY,
        artifact_digest="b" * 64,
        compliance_snapshot_digest="c" * 64,
    )
    assert len(status.digest()) == 64


def test_r13_1_nonfinite_and_invalid_contract_data_fail_closed() -> None:
    with pytest.raises(ValueError, match="not serializable"):
        canonical_json_bytes({"duration": float("nan")})
    with pytest.raises(ValueError, match="stable identifier"):
        MobileTargetProfile(
            profile_id="../escape",
            platform=MobilePlatform.ANDROID,
            form_factors=(MobileFormFactor.PHONE,),
            source_kind=MobileSourceKind.NATIVE,
            minimum_platform_version="26",
            target_api_level=36,
        )
    with pytest.raises(ValueError, match="SHA-256"):
        MobileToolchainIdentity(
            tool_kind=MobileToolKind.ADB,
            executable_name="adb",
            executable_sha256="not-a-digest",
            version="37.0.1",
            host_os=MobileHostOS.LINUX,
            architecture=MobileArchitecture.X86_64,
        )


def test_r13_1_json_schemas_accept_canonical_contracts() -> None:
    target_schema = json.loads(
        (ROOT / "schemas/r13/mobile-target-profile.schema.json").read_text(encoding="utf-8")
    )
    report_schema = json.loads(
        (ROOT / "schemas/r13/mobile-capability-report.schema.json").read_text(encoding="utf-8")
    )
    matrix_schema = json.loads(
        (ROOT / "schemas/r13/device-test-matrix.schema.json").read_text(encoding="utf-8")
    )
    for schema in (target_schema, report_schema, matrix_schema):
        Draft202012Validator.check_schema(schema)

    target = MobileTargetProfile(
        profile_id="mobile.android.schema",
        platform=MobilePlatform.ANDROID,
        form_factors=(MobileFormFactor.PHONE,),
        source_kind=MobileSourceKind.NATIVE,
        minimum_platform_version="26",
        target_api_level=36,
    )
    report = MobileCapabilityReport(
        adapter_id="android.schema",
        platform=MobilePlatform.ANDROID,
        state=MobileCapabilityState.AVAILABLE,
        toolchains=(_tool(),),
        capabilities=("build",),
    )
    device = DeviceIdentity(
        device_id="device.schema",
        provider_id="ci",
        platform=MobilePlatform.ANDROID,
        architecture=MobileArchitecture.X86_64,
        os_version="16",
        model="virtual",
        virtual=True,
    )
    matrix = DeviceTestMatrix(
        matrix_id="matrix.schema",
        platform=MobilePlatform.ANDROID,
        device_digests=(device.digest(),),
    )
    Draft202012Validator(target_schema).validate(target.canonical())
    Draft202012Validator(report_schema).validate(report.canonical())
    Draft202012Validator(matrix_schema).validate(matrix.canonical())

    forged = dict(target.canonical())
    forged["raw_argv"] = ["sh", "-c", "curl attacker"]
    with pytest.raises(Exception):
        Draft202012Validator(target_schema).validate(forged)


def test_r13_1_tools_and_paths_are_allowlisted(tmp_path: Path) -> None:
    boundary, runtime, project, staging = _boundary(tmp_path)
    adb = runtime / ("adb.exe" if os.name == "nt" else "adb")
    adb.write_text("fixture", encoding="utf-8")
    assert boundary.validate_tool(MobileToolKind.ADB, adb) == adb.resolve()

    wrong = runtime / ("powershell.exe" if os.name == "nt" else "bash")
    wrong.write_text("fixture", encoding="utf-8")
    with pytest.raises(MobileBoundaryError, match="unexpected tool"):
        boundary.validate_tool(MobileToolKind.ADB, wrong)

    outside = tmp_path / adb.name
    outside.write_text("fixture", encoding="utf-8")
    with pytest.raises(MobileBoundaryError, match="escapes configured runtime roots"):
        boundary.validate_tool(MobileToolKind.ADB, outside)

    manifest = project / "AndroidManifest.xml"
    manifest.write_text("<manifest />", encoding="utf-8")
    assert boundary.validate_project_file(
        manifest, names=frozenset({"AndroidManifest.xml"})
    ) == manifest.resolve()
    outside_manifest = tmp_path / "AndroidManifest.xml"
    outside_manifest.write_text("<manifest />", encoding="utf-8")
    with pytest.raises(MobileBoundaryError, match="escapes project root"):
        boundary.validate_project_file(
            outside_manifest, names=frozenset({"AndroidManifest.xml"})
        )

    assert boundary.validate_staging_path(staging / "build") == (staging / "build").resolve()
    with pytest.raises(MobileBoundaryError, match="escapes staging root"):
        boundary.validate_staging_path(tmp_path / "outside")


def test_r13_1_symlink_escape_is_rejected_when_supported(tmp_path: Path) -> None:
    boundary, runtime, project, _ = _boundary(tmp_path)
    outside = tmp_path / "outside-adb"
    outside.write_text("fixture", encoding="utf-8")
    link = runtime / ("adb.exe" if os.name == "nt" else "adb")
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable in this environment")
    with pytest.raises(MobileBoundaryError, match="escapes configured runtime roots"):
        boundary.validate_tool(MobileToolKind.ADB, link)

    outside_project = tmp_path / "outside.gradle.kts"
    outside_project.write_text("plugins {}", encoding="utf-8")
    project_link = project / "build.gradle.kts"
    try:
        project_link.symlink_to(outside_project)
    except (OSError, NotImplementedError):
        pytest.skip("project symlinks unavailable")
    with pytest.raises(MobileBoundaryError, match="escapes project root"):
        boundary.validate_project_file(
            project_link, names=frozenset({"build.gradle.kts"})
        )


def test_r13_1_environment_is_allowlisted_and_path_bounded(tmp_path: Path) -> None:
    boundary, runtime, _, staging = _boundary(tmp_path)
    java_home = runtime / "jdk"
    java_home.mkdir()
    gradle_home = staging / "gradle-home"
    assert boundary.validate_environment_overrides(
        {
            "kodepoia_run_id": "fixture-1",
            "JAVA_HOME": str(java_home),
            "GRADLE_USER_HOME": str(gradle_home),
        }
    ) == {
        "KODEPOIA_RUN_ID": "fixture-1",
        "JAVA_HOME": str(java_home.resolve()),
        "GRADLE_USER_HOME": str(gradle_home.resolve()),
    }

    for key in ("PATH", "CLASSPATH", "GRADLE_OPTS", "JAVA_TOOL_OPTIONS", "ADB_TRACE"):
        with pytest.raises(MobileBoundaryError, match="not allowlisted"):
            boundary.validate_environment_overrides({key: "attacker-controlled"})
    with pytest.raises(MobileBoundaryError, match="escapes allowed roots"):
        boundary.validate_environment_overrides({"ANDROID_HOME": str(tmp_path / "outside")})
    with pytest.raises(MobileBoundaryError, match="invalid or too large"):
        boundary.validate_environment_overrides({"KODEPOIA_RUN_ID": "safe\x00evil"})


def test_r13_1_argv_builders_are_fixed_and_reject_raw_operations(tmp_path: Path) -> None:
    boundary, runtime, project, _ = _boundary(tmp_path)
    java = runtime / ("java.exe" if os.name == "nt" else "java")
    adb = runtime / ("adb.exe" if os.name == "nt" else "adb")
    gradle = runtime / ("gradle.bat" if os.name == "nt" else "gradle")
    bundletool = runtime / "bundletool.jar"
    xcrun = runtime / "xcrun"
    for path in (java, adb, gradle, bundletool, xcrun):
        path.write_text("fixture", encoding="utf-8")

    assert boundary.build_probe_argv(MobileToolKind.ADB, adb) == (
        str(adb.resolve()),
        "version",
    )
    assert boundary.build_bundletool_probe_argv(
        java=java, bundletool_jar=bundletool
    ) == (str(java.resolve()), "-jar", str(bundletool.resolve()), "version")
    assert boundary.build_adb_devices_argv(adb) == (
        str(adb.resolve()),
        "devices",
        "-l",
    )
    assert boundary.build_xcrun_simctl_list_argv(xcrun) == (
        str(xcrun.resolve()),
        "simctl",
        "list",
        "devices",
        "--json",
    )

    with pytest.raises(MobileBoundaryError, match="not allowlisted"):
        boundary.build_gradle_task_argv(
            gradle,
            project_directory=project,
            task="--init-script=attacker.gradle",
        )
