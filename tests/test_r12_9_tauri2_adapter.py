from __future__ import annotations

import json
from pathlib import Path

import pytest

from kodepoia.desktop.app_model import canonical_sample_app
from kodepoia.desktop.boundary import DesktopBoundaryError, DesktopToolchainBoundary, validate_environment_overrides
from kodepoia.desktop.contracts import DesktopArchitecture, DesktopOS, DesktopToolKind
from kodepoia.desktop.tauri2 import (
    Tauri2Adapter,
    TauriDependencyDeclaration,
    TauriGeneratedFile,
    TauriKitIdentity,
    TauriLicenseState,
    TauriProjectManifest,
)

_SHA_A = "a" * 64
_SHA_B = "b" * 64
_SHA_C = "c" * 64
_SHA_D = "d" * 64


def test_tauri_manifest_is_canonical_and_default_deny() -> None:
    left = TauriProjectManifest(
        _SHA_A,
        Tauri2Adapter.TAURI_VERSION,
        Tauri2Adapter.TAURI_BUILD_VERSION,
        (),
        (),
        (TauriGeneratedFile("src/main.rs", _SHA_B), TauriGeneratedFile("Cargo.toml", _SHA_C)),
    )
    right = TauriProjectManifest(
        _SHA_A,
        Tauri2Adapter.TAURI_VERSION,
        Tauri2Adapter.TAURI_BUILD_VERSION,
        (),
        (),
        (TauriGeneratedFile("Cargo.toml", _SHA_C), TauriGeneratedFile("src/main.rs", _SHA_B)),
    )
    assert left.canonical() == right.canonical()
    assert left.digest() == right.digest()
    assert left.canonical()["permissions"] == []
    assert left.canonical()["bundle_targets"] == []


def test_tauri_manifest_rejects_permissions_bundle_and_path_escape() -> None:
    with pytest.raises(ValueError):
        TauriGeneratedFile("../escape.rs", _SHA_A)
    with pytest.raises(ValueError):
        TauriProjectManifest(
            _SHA_A,
            Tauri2Adapter.TAURI_VERSION,
            Tauri2Adapter.TAURI_BUILD_VERSION,
            ("core:default",),
            (),
            (),
        )
    with pytest.raises(ValueError):
        TauriProjectManifest(
            _SHA_A,
            Tauri2Adapter.TAURI_VERSION,
            Tauri2Adapter.TAURI_BUILD_VERSION,
            (),
            ("msi",),
            (),
        )


def test_tauri_dependencies_never_infer_redistribution_rights() -> None:
    dependency = TauriDependencyDeclaration("tauri", Tauri2Adapter.TAURI_VERSION)
    assert dependency.license_state is TauriLicenseState.REVIEW_REQUIRED
    assert dependency.redistribution_rights_inferred is False
    with pytest.raises(ValueError):
        TauriDependencyDeclaration(
            "tauri-build",
            Tauri2Adapter.TAURI_BUILD_VERSION,
            redistribution_rights_inferred=True,
        )
    with pytest.raises(ValueError):
        TauriDependencyDeclaration("tauri-plugin-shell", "2.0.0")


def test_tauri_kit_requires_windows_msvc_and_webview_evidence() -> None:
    kwargs = dict(
        platform=DesktopOS.WINDOWS,
        architecture=DesktopArchitecture.X64,
        cargo_version="cargo 1.91.0",
        cargo_sha256=_SHA_A,
        rustc_version="rustc 1.91.0",
        rustc_sha256=_SHA_B,
        host_triple="x86_64-pc-windows-msvc",
        tauri_version=Tauri2Adapter.TAURI_VERSION,
        webview_version="140.0.3485.81",
        cargo_lock_sha256=_SHA_C,
        capability_policy_sha256=_SHA_D,
    )
    assert TauriKitIdentity(**kwargs).digest() == TauriKitIdentity(**kwargs).digest()
    with pytest.raises(ValueError):
        TauriKitIdentity(**(kwargs | {"host_triple": "x86_64-pc-windows-gnu"}))
    with pytest.raises(ValueError):
        TauriKitIdentity(**(kwargs | {"webview_version": ""}))
    with pytest.raises(ValueError):
        TauriKitIdentity(**(kwargs | {"platform": DesktopOS.LINUX}))


def test_tauri_render_fixture_is_deterministic_and_security_closed(tmp_path: Path) -> None:
    project = tmp_path / "project"
    staging = project / ".kodepoia" / "staging"
    project.mkdir()
    staging.mkdir(parents=True)
    adapter = Tauri2Adapter(project, staging)
    cargo, manifest, model_sha = adapter.render_fixture(canonical_sample_app())
    cargo_text = cargo.read_text(encoding="utf-8")
    main_text = (cargo.parent / "src" / "main.rs").read_text(encoding="utf-8")
    config = json.loads((cargo.parent / "tauri.conf.json").read_text(encoding="utf-8"))
    icon = cargo.parent / "icons" / "icon.ico"
    assert f'tauri = "={Tauri2Adapter.TAURI_VERSION}"' in cargo_text
    assert f'tauri-build = "={Tauri2Adapter.TAURI_BUILD_VERSION}"' in cargo_text
    assert "tauri::webview_version()" in main_text
    assert "get_webview_window(\"main\")" in main_text
    assert model_sha in main_text
    assert config["app"]["security"]["capabilities"] == []
    assert config["app"]["withGlobalTauri"] is False
    assert config["bundle"]["active"] is False
    assert config["plugins"] == {}
    assert config["build"] == {"frontendDist": "dist"}
    assert "connect-src 'none'" in config["app"]["security"]["csp"]
    assert icon.is_file()
    assert icon.stat().st_size == 70
    icon_entry = next(item for item in manifest.files if item.path == "icons/icon.ico")
    assert icon_entry.sha256 == adapter._sha(icon)
    assert manifest.digest() == adapter.render_fixture(canonical_sample_app())[1].digest()


def test_tauri_lockfile_requires_exact_runtime_and_build_versions(tmp_path: Path) -> None:
    root = tmp_path / "fixture"
    root.mkdir()
    adapter = Tauri2Adapter(tmp_path, tmp_path / "staging")
    lock = root / "Cargo.lock"
    lock.write_text(
        "version = 4\n\n"
        "[[package]]\nname = \"tauri\"\nversion = \"2.11.5\"\n\n"
        "[[package]]\nname = \"tauri-build\"\nversion = \"2.6.3\"\n",
        encoding="utf-8",
    )
    assert adapter._validate_lockfile(root)[1] == adapter._sha(lock)
    lock.write_text(lock.read_text(encoding="utf-8").replace("2.11.5", "2.11.4"), encoding="utf-8")
    with pytest.raises(ValueError):
        adapter._validate_lockfile(root)


def test_tauri_cargo_boundary_is_locked_offline_and_bounded(tmp_path: Path) -> None:
    project = tmp_path / "project"
    staging = project / "staging"
    project.mkdir()
    staging.mkdir()
    cargo = tmp_path / "toolchain" / "cargo.exe"
    cargo.parent.mkdir()
    cargo.write_bytes(b"cargo")
    manifest = project / "Cargo.toml"
    manifest.write_text("[package]\nname='x'\nversion='0.1.0'\n", encoding="utf-8")
    boundary = DesktopToolchainBoundary(
        allowed_runtime_roots=(cargo.parent,),
        project_root=project,
        staging_root=staging,
    )
    argv = boundary.build_cargo_argv(
        cargo,
        operation="build",
        manifest_path=manifest,
        target_directory=staging / "target",
    )
    assert "--locked" in argv
    assert "--offline" in argv
    with pytest.raises(DesktopBoundaryError):
        boundary.build_cargo_argv(
            cargo,
            operation="build",
            manifest_path=manifest,
            target_directory=tmp_path / "escaped",
        )


def test_tauri_environment_injection_remains_closed() -> None:
    for key in ("CARGO_HOME", "RUSTFLAGS", "RUSTC_WRAPPER", "TAURI_CONFIG", "WEBVIEW2_BROWSER_EXECUTABLE_FOLDER"):
        with pytest.raises(DesktopBoundaryError):
            validate_environment_overrides({key: "attacker-controlled"})
