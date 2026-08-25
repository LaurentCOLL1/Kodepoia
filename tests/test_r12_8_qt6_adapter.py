from __future__ import annotations

from pathlib import Path

import pytest

from kodepoia.desktop.app_model import canonical_sample_app
from kodepoia.desktop.boundary import DesktopBoundaryError, validate_environment_overrides
from kodepoia.desktop.contracts import (
    DesktopArchitecture,
    DesktopOS,
    DesktopToolKind,
    DesktopToolchainIdentity,
)
from kodepoia.desktop.qt6 import (
    Qt6Adapter,
    QtDependencyDeclaration,
    QtGeneratedFile,
    QtKitIdentity,
    QtLicenseState,
    QtProjectManifest,
    QtToolchainDiscovery,
)


_SHA_A = "a" * 64
_SHA_B = "b" * 64
_SHA_C = "c" * 64


def _report_identity() -> DesktopToolchainIdentity:
    return DesktopToolchainIdentity(
        DesktopToolKind.QT_PATHS,
        "qtpaths.exe",
        _SHA_A,
        "6.11.2",
        DesktopOS.WINDOWS,
        DesktopArchitecture.X64,
        ("cmake_ready", "qt6_core", "qt6_widgets"),
    )


def test_qt_project_manifest_is_canonical_and_sorted() -> None:
    left = QtProjectManifest(
        _SHA_A,
        "3.22",
        17,
        ("Widgets", "Core"),
        (QtGeneratedFile("main.cpp", _SHA_B), QtGeneratedFile("CMakeLists.txt", _SHA_C)),
    )
    right = QtProjectManifest(
        _SHA_A,
        "3.22",
        17,
        ("Core", "Widgets"),
        (QtGeneratedFile("CMakeLists.txt", _SHA_C), QtGeneratedFile("main.cpp", _SHA_B)),
    )
    assert left.canonical() == right.canonical()
    assert left.digest() == right.digest()
    assert [item["path"] for item in left.canonical()["files"]] == ["CMakeLists.txt", "main.cpp"]


def test_qt_manifest_rejects_path_escape_and_component_injection() -> None:
    with pytest.raises(ValueError):
        QtGeneratedFile("../escape.cpp", _SHA_A)
    with pytest.raises(ValueError):
        QtProjectManifest(_SHA_A, "3.22", 17, ("Core", "WebEngine"), ())
    with pytest.raises(ValueError):
        QtProjectManifest(_SHA_A, "3.21", 17, ("Core", "Widgets"), ())


def test_qt_dependency_declaration_never_infers_redistribution_rights() -> None:
    declaration = QtDependencyDeclaration("Qt6::Core", "6.11.2")
    assert declaration.license_state is QtLicenseState.REVIEW_REQUIRED
    assert declaration.redistribution_rights_inferred is False
    with pytest.raises(ValueError):
        QtDependencyDeclaration("Qt6::Widgets", "6.11.2", redistribution_rights_inferred=True)
    with pytest.raises(ValueError):
        QtDependencyDeclaration("Qt6::Network", "6.11.2")


def test_qt_kit_rejects_generator_and_component_substitution() -> None:
    kwargs = dict(
        qt_version="6.11.2",
        platform=DesktopOS.WINDOWS,
        architecture=DesktopArchitecture.X64,
        generator="Visual Studio 17 2022",
        cmake_version="3.31.6",
        cmake_sha256=_SHA_A,
        qtpaths_sha256=_SHA_B,
        compiler_name="cl.exe",
        compiler_id="MSVC",
        compiler_version="19.44.35213.0",
        compiler_sha256=_SHA_C,
        components=("Core", "Widgets"),
    )
    kit = QtKitIdentity(**kwargs)
    assert kit.digest() == QtKitIdentity(**kwargs).digest()
    with pytest.raises(ValueError):
        QtKitIdentity(**(kwargs | {"generator": "Ninja; calc.exe"}))
    with pytest.raises(ValueError):
        QtKitIdentity(**(kwargs | {"components": ("Core", "Network")}))


def test_qt_render_fixture_is_deterministic_and_uses_fixed_public_contract(tmp_path: Path) -> None:
    project = tmp_path / "project"
    staging = project / ".kodepoia" / "staging"
    project.mkdir()
    staging.mkdir(parents=True)
    adapter = Qt6Adapter(project, staging)
    cmake, manifest, model_sha = adapter.render_fixture(canonical_sample_app())
    text = cmake.read_text(encoding="utf-8")
    source = (cmake.parent / "main.cpp").read_text(encoding="utf-8")
    assert "cmake_minimum_required(VERSION 3.22)" in text
    assert "set(CMAKE_CXX_STANDARD 17)" in text
    assert "find_package(Qt6 6.5 REQUIRED COMPONENTS Core Widgets)" in text
    assert "qt_add_resources" in text
    assert "Qt6::Core Qt6::Widgets" in text
    assert model_sha in source
    assert (cmake.parent / "model.txt").read_text(encoding="utf-8").strip() == model_sha
    second = adapter.render_fixture(canonical_sample_app())[1]
    assert manifest.digest() == second.digest()


def test_qt_configure_argv_is_fixed_and_rejects_output_escape(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project = tmp_path / "project"
    staging = project / ".kodepoia" / "staging"
    source = project / ".kodepoia" / "fixtures" / "qt6"
    qt_prefix = tmp_path / "Qt" / "6.11.2" / "msvc2022_64"
    cmake = tmp_path / "cmake.exe"
    qtpaths = qt_prefix / "bin" / "qtpaths.exe"
    for directory in (project, staging, source, qtpaths.parent):
        directory.mkdir(parents=True, exist_ok=True)
    cmake.write_bytes(b"cmake")
    qtpaths.write_bytes(b"qtpaths")
    discovery = QtToolchainDiscovery(cmake, qtpaths, qt_prefix, "3.31.6", "6.11.2", _report_identity())
    adapter = Qt6Adapter(project, staging)
    monkeypatch.setattr(Qt6Adapter, "current_arch", staticmethod(lambda: DesktopArchitecture.X64))
    argv = adapter._configure_argv(discovery, source, staging / "build")
    assert argv[:5] == (str(cmake), "-S", str(source.resolve()), "-B", str((staging / "build").resolve()))
    assert argv[5:9] == ("-G", "Visual Studio 17 2022", "-A", "x64")
    assert argv[-1] == f"-DQt6_ROOT={qt_prefix.resolve()}"
    with pytest.raises(DesktopBoundaryError):
        adapter._configure_argv(discovery, source, tmp_path / "escaped-build")


def test_qt_environment_and_raw_toolchain_injection_remain_closed() -> None:
    for key in ("CMAKE_PREFIX_PATH", "QT_PLUGIN_PATH", "QTDIR", "CXX", "CC"):
        with pytest.raises(DesktopBoundaryError):
            validate_environment_overrides({key: "attacker-controlled"})


def test_qt_toolchain_metadata_parser_fails_closed(tmp_path: Path) -> None:
    metadata = tmp_path / "kodepoia-toolchain.txt"
    metadata.write_text("compiler_path=C:/fake/cl.exe\ncompiler_id=MSVC\n", encoding="utf-8")
    with pytest.raises(ValueError):
        Qt6Adapter._parse_toolchain_file(metadata)
