from __future__ import annotations

from pathlib import Path

import pytest

from kodepoia.desktop.app_model import canonical_sample_app
from kodepoia.desktop.boundary import DesktopBoundaryError, DesktopToolchainBoundary, validate_environment_overrides
from kodepoia.desktop.contracts import DesktopCapabilityReport, DesktopCapabilityState, DesktopFramework
from kodepoia.desktop.wpf import WpfAdapter


def test_r12_5_wpf_fixture_maps_shared_model_deterministically(tmp_path: Path) -> None:
    root = tmp_path / "project"; root.mkdir()
    staging = root / ".kodepoia" / "staging"; staging.mkdir(parents=True)
    adapter = WpfAdapter(root, staging)
    app, harness, digest = adapter.render_fixture(canonical_sample_app())
    first = {p.relative_to(root).as_posix(): p.read_bytes() for p in adapter.fixture_root.rglob("*") if p.is_file()}
    app2, harness2, digest2 = adapter.render_fixture(canonical_sample_app())
    second = {p.relative_to(root).as_posix(): p.read_bytes() for p in adapter.fixture_root.rglob("*") if p.is_file()}
    assert (app, harness, digest) == (app2, harness2, digest2)
    assert first == second
    assert digest == canonical_sample_app().conformance_projection(DesktopFramework.WPF).logical_model_sha256
    assert "<UseWPF>true</UseWPF>" in app.read_text(encoding="utf-8")
    assert "net10.0-windows" in app.read_text(encoding="utf-8")
    assert WpfAdapter.SENTINEL in (adapter.fixture_root / "Harness" / "Program.cs").read_text(encoding="utf-8")


def test_r12_5_non_windows_is_not_available(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("kodepoia.desktop.wpf.platform.system", lambda: "Linux")
    result = WpfAdapter(tmp_path, tmp_path / "stage").discover_toolchain()
    assert isinstance(result, DesktopCapabilityReport)
    assert result.state is DesktopCapabilityState.UNSUPPORTED
    assert result.blockers == ("windows_required",)


def test_r12_5_missing_dotnet_is_unavailable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("kodepoia.desktop.wpf.platform.system", lambda: "Windows")
    monkeypatch.setattr("kodepoia.desktop.wpf.shutil.which", lambda _name: None)
    result = WpfAdapter(tmp_path, tmp_path / "stage").discover_toolchain()
    assert isinstance(result, DesktopCapabilityReport)
    assert result.state is DesktopCapabilityState.UNAVAILABLE
    assert "dotnet_missing" in result.blockers


def test_r12_5_msbuild_property_and_environment_injection_fail_closed(tmp_path: Path) -> None:
    project = tmp_path / "fixture.csproj"; project.write_text("<Project/>", encoding="utf-8")
    exe = tmp_path / "dotnet.exe"; exe.write_bytes(b"fixture")
    boundary = DesktopToolchainBoundary(allowed_runtime_roots=(tmp_path,), project_root=tmp_path, staging_root=tmp_path / "stage")
    with pytest.raises(DesktopBoundaryError, match="configuration"):
        boundary.build_dotnet_argv(exe, operation="build", project_file=project, configuration="Release -p:Owned=true")
    with pytest.raises(DesktopBoundaryError, match="operation"):
        boundary.build_dotnet_argv(exe, operation="build -p:Owned=true", project_file=project, configuration="Release")
    with pytest.raises(DesktopBoundaryError, match="not allowlisted"):
        validate_environment_overrides({"DOTNET_ROOT": "C:/owned"})
