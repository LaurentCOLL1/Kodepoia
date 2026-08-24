from __future__ import annotations

import json
from pathlib import Path

import pytest

from kodepoia.desktop.app_model import canonical_sample_app
from kodepoia.desktop.avalonia import (
    AvaloniaAdapter,
    AvaloniaTargetMatrix,
    canonical_avalonia_matrix,
)
from kodepoia.desktop.contracts import DesktopFramework, DesktopOS


def test_avalonia_target_matrix_is_deterministic_and_desktop_only() -> None:
    matrix = canonical_avalonia_matrix()
    assert matrix.targets == (DesktopOS.LINUX, DesktopOS.MACOS, DesktopOS.WINDOWS)
    assert matrix.digest() == canonical_avalonia_matrix().digest()


def test_avalonia_empty_matrix_is_rejected() -> None:
    with pytest.raises(ValueError, match="desktop"):
        AvaloniaTargetMatrix(())


def test_avalonia_render_fixture_maps_shared_model(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(AvaloniaAdapter, "current_os", staticmethod(lambda: DesktopOS.LINUX))
    adapter = AvaloniaAdapter(tmp_path, tmp_path / "stage")
    model = canonical_sample_app()
    app, probe, digest = adapter.render_fixture(model, canonical_avalonia_matrix())
    assert digest == model.conformance_projection(DesktopFramework.AVALONIA).logical_model_sha256
    project = app.read_text(encoding="utf-8")
    assert '<TargetFramework>net10.0</TargetFramework>' in project
    assert 'Include="Avalonia" Version="12.1.1"' in project
    assert 'Include="Avalonia.Desktop" Version="12.1.1"' in project
    assert probe.is_file()
    assert digest in (adapter.fixture_root(DesktopOS.LINUX) / "App" / "MainWindow.axaml").read_text(encoding="utf-8")


def test_avalonia_unselected_current_platform_is_rejected(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(AvaloniaAdapter, "current_os", staticmethod(lambda: DesktopOS.MACOS))
    adapter = AvaloniaAdapter(tmp_path, tmp_path / "stage")
    with pytest.raises(ValueError, match="not selected"):
        adapter.render_fixture(canonical_sample_app(), AvaloniaTargetMatrix((DesktopOS.WINDOWS,)))


def test_avalonia_schema_rejects_mobile_surface() -> None:
    payload = json.loads(Path("schemas/r12/avalonia-target-matrix.schema.json").read_text(encoding="utf-8"))
    values = set(payload["properties"]["targets"]["items"]["enum"])
    assert values == {"windows", "linux", "macos"}
    assert "android" not in values
    assert "ios" not in values
