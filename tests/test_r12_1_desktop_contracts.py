from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.desktop import (
    DesktopArchitecture,
    DesktopBoundaryError,
    DesktopCapabilityReport,
    DesktopCapabilityState,
    DesktopFramework,
    DesktopOS,
    DesktopPackageKind,
    DesktopTargetProfile,
    DesktopToolKind,
    DesktopToolchainBoundary,
    DesktopToolchainIdentity,
    validate_environment_overrides,
)
from kodepoia.desktop.contracts import canonical_json_bytes

ROOT = Path(__file__).resolve().parents[1]


def _identity() -> DesktopToolchainIdentity:
    return DesktopToolchainIdentity(
        tool_kind=DesktopToolKind.DOTNET,
        executable_name="dotnet.exe",
        executable_sha256="a" * 64,
        version="10.0.100",
        platform=DesktopOS.WINDOWS,
        architecture=DesktopArchitecture.X64,
        capabilities=("test", "build", "build"),
    )


def test_r12_1_target_profile_is_deterministic_and_framework_bounded() -> None:
    profile = DesktopTargetProfile(
        profile_id="desktop.sample",
        framework=DesktopFramework.AVALONIA,
        targets=(DesktopOS.WINDOWS, DesktopOS.LINUX, DesktopOS.WINDOWS),
        architecture=DesktopArchitecture.X64,
        package_kind=DesktopPackageKind.ARCHIVE,
    )
    assert profile.targets == (DesktopOS.LINUX, DesktopOS.WINDOWS)
    assert profile.digest() == DesktopTargetProfile(
        profile_id="desktop.sample",
        framework=DesktopFramework.AVALONIA,
        targets=(DesktopOS.LINUX, DesktopOS.WINDOWS),
        architecture=DesktopArchitecture.X64,
        package_kind=DesktopPackageKind.ARCHIVE,
    ).digest()

    with pytest.raises(ValueError, match="Windows only"):
        DesktopTargetProfile(
            profile_id="desktop.wpf",
            framework=DesktopFramework.WPF,
            targets=(DesktopOS.WINDOWS, DesktopOS.LINUX),
        )
    with pytest.raises(ValueError, match="MSIX requires"):
        DesktopTargetProfile(
            profile_id="desktop.qt",
            framework=DesktopFramework.QT6,
            targets=(DesktopOS.LINUX,),
            package_kind=DesktopPackageKind.MSIX,
        )


def test_r12_1_capability_state_cannot_manufacture_available() -> None:
    with pytest.raises(ValueError, match="AVAILABLE requires"):
        DesktopCapabilityReport(
            adapter_id="adapter.wpf",
            state=DesktopCapabilityState.AVAILABLE,
        )
    with pytest.raises(ValueError, match="requires at least one blocker"):
        DesktopCapabilityReport(
            adapter_id="adapter.wpf",
            state=DesktopCapabilityState.UNAVAILABLE,
        )
    with pytest.raises(ValueError, match="NOT_PROBED"):
        DesktopCapabilityReport(
            adapter_id="adapter.wpf",
            state=DesktopCapabilityState.NOT_PROBED,
            toolchain=_identity(),
        )

    report = DesktopCapabilityReport(
        adapter_id="adapter.wpf",
        state=DesktopCapabilityState.AVAILABLE,
        toolchain=_identity(),
        capabilities=("test", "build", "build"),
    )
    assert report.capabilities == ("build", "test")
    assert report.blockers == ()
    assert len(report.digest()) == 64


def test_r12_1_nonfinite_and_invalid_identity_data_fail_closed() -> None:
    with pytest.raises(ValueError, match="not serializable"):
        canonical_json_bytes({"duration": float("nan")})
    with pytest.raises(ValueError, match="stable identifier"):
        DesktopTargetProfile(
            profile_id="../escape",
            framework=DesktopFramework.QT6,
            targets=(DesktopOS.WINDOWS,),
        )
    with pytest.raises(ValueError, match="SHA-256"):
        DesktopToolchainIdentity(
            tool_kind=DesktopToolKind.DOTNET,
            executable_name="dotnet.exe",
            executable_sha256="not-a-digest",
            version="10.0.100",
            platform=DesktopOS.WINDOWS,
            architecture=DesktopArchitecture.X64,
        )


def test_r12_1_json_schemas_accept_canonical_contracts() -> None:
    target_schema = json.loads(
        (ROOT / "schemas/r12/desktop-target-profile.schema.json").read_text(
            encoding="utf-8"
        )
    )
    report_schema = json.loads(
        (ROOT / "schemas/r12/desktop-capability-report.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator.check_schema(target_schema)
    Draft202012Validator.check_schema(report_schema)

    target = DesktopTargetProfile(
        profile_id="desktop.winui",
        framework=DesktopFramework.WINUI3,
        targets=(DesktopOS.WINDOWS,),
        architecture=DesktopArchitecture.ARM64,
        package_kind=DesktopPackageKind.MSIX,
    )
    report = DesktopCapabilityReport(
        adapter_id="adapter.winui3",
        state=DesktopCapabilityState.AVAILABLE,
        toolchain=_identity(),
        capabilities=("build", "test"),
    )
    Draft202012Validator(target_schema).validate(target.canonical())
    Draft202012Validator(report_schema).validate(report.canonical())

    forged = dict(target.canonical())
    forged["raw_argv"] = ["cmd.exe", "/c", "calc"]
    with pytest.raises(Exception):
        Draft202012Validator(target_schema).validate(forged)


def _boundary(tmp_path: Path) -> tuple[DesktopToolchainBoundary, Path, Path, Path]:
    runtime = tmp_path / "runtime"
    project = tmp_path / "project"
    staging = tmp_path / "staging"
    runtime.mkdir()
    project.mkdir()
    staging.mkdir()
    return (
        DesktopToolchainBoundary(
            allowed_runtime_roots=(runtime,),
            project_root=project,
            staging_root=staging,
        ),
        runtime,
        project,
        staging,
    )


def test_r12_1_environment_overrides_are_minimal_and_fail_closed() -> None:
    assert validate_environment_overrides(
        {"kodepoia_run_id": "fixture-1", "TMP": "tmp"}
    ) == {"KODEPOIA_RUN_ID": "fixture-1", "TMP": "tmp"}

    for key in (
        "PATH",
        "DOTNET_ROOT",
        "MSBuildSDKsPath",
        "CMAKE_GENERATOR",
        "CARGO_HOME",
        "RUSTFLAGS",
        "RUSTC_WRAPPER",
    ):
        with pytest.raises(DesktopBoundaryError, match="not allowlisted"):
            validate_environment_overrides({key: "attacker-controlled"})
    with pytest.raises(DesktopBoundaryError, match="invalid or too large"):
        validate_environment_overrides({"KODEPOIA_RUN_ID": "safe\x00evil"})


def test_r12_1_executable_and_project_paths_are_governed(tmp_path: Path) -> None:
    boundary, runtime, project, staging = _boundary(tmp_path)
    dotnet = runtime / "dotnet"
    dotnet.write_text("fixture", encoding="utf-8")
    assert boundary.validate_executable(DesktopToolKind.DOTNET, dotnet) == dotnet.resolve()

    wrong = runtime / "powershell.exe"
    wrong.write_text("fixture", encoding="utf-8")
    with pytest.raises(DesktopBoundaryError, match="unexpected executable"):
        boundary.validate_executable(DesktopToolKind.DOTNET, wrong)

    outside_runtime = tmp_path / "dotnet"
    outside_runtime.write_text("fixture", encoding="utf-8")
    with pytest.raises(DesktopBoundaryError, match="escapes configured roots"):
        boundary.validate_executable(DesktopToolKind.DOTNET, outside_runtime)

    project_file = project / "App.csproj"
    project_file.write_text("<Project />", encoding="utf-8")
    assert boundary.validate_project_file(
        project_file, suffixes=frozenset({".csproj"})
    ) == project_file.resolve()

    outside_project = tmp_path / "Outside.csproj"
    outside_project.write_text("<Project />", encoding="utf-8")
    with pytest.raises(DesktopBoundaryError, match="escapes project root"):
        boundary.validate_project_file(
            outside_project, suffixes=frozenset({".csproj"})
        )

    text_file = project / "App.txt"
    text_file.write_text("fixture", encoding="utf-8")
    with pytest.raises(DesktopBoundaryError, match="suffix"):
        boundary.validate_project_file(text_file, suffixes=frozenset({".csproj"}))

    assert boundary.validate_staging_path(staging / "build") == (staging / "build").resolve()
    with pytest.raises(DesktopBoundaryError, match="escapes staging root"):
        boundary.validate_staging_path(tmp_path / "outside-build")


def test_r12_1_probe_and_build_argv_are_fixed_templates(tmp_path: Path) -> None:
    boundary, runtime, project, staging = _boundary(tmp_path)
    dotnet = runtime / "dotnet.exe"
    cmake = runtime / "cmake.exe"
    cargo = runtime / "cargo.exe"
    for executable in (dotnet, cmake, cargo):
        executable.write_text("fixture", encoding="utf-8")

    project_file = project / "App.csproj"
    project_file.write_text("<Project />", encoding="utf-8")
    cargo_manifest = project / "Cargo.toml"
    cargo_manifest.write_text("[package]", encoding="utf-8")

    assert boundary.build_probe_argv(DesktopToolKind.DOTNET, dotnet) == (
        str(dotnet.resolve()),
        "--version",
    )
    assert boundary.build_dotnet_argv(
        dotnet,
        operation="build",
        project_file=project_file,
        configuration="Release",
    ) == (
        str(dotnet.resolve()),
        "build",
        str(project_file.resolve()),
        "--no-restore",
        "--nologo",
        "--configuration",
        "Release",
    )
    assert boundary.build_cmake_build_argv(
        cmake,
        build_directory=staging / "cmake-build",
        configuration="Debug",
    )[-2:] == ("--parallel", "2")
    cargo_argv = boundary.build_cargo_argv(
        cargo,
        operation="test",
        manifest_path=cargo_manifest,
        target_directory=staging / "cargo-target",
    )
    assert cargo_argv[1:4] == ("test", "--locked", "--offline")

    with pytest.raises(DesktopBoundaryError, match="operation"):
        boundary.build_dotnet_argv(
            dotnet,
            operation="build;calc",
            project_file=project_file,
            configuration="Release",
        )
    with pytest.raises(DesktopBoundaryError, match="configuration"):
        boundary.build_dotnet_argv(
            dotnet,
            operation="build",
            project_file=project_file,
            configuration="Release /p:Evil=true",
        )
    with pytest.raises(DesktopBoundaryError, match="Cargo operation"):
        boundary.build_cargo_argv(
            cargo,
            operation="run --config evil",
            manifest_path=cargo_manifest,
            target_directory=staging / "cargo-target",
        )
