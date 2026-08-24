from __future__ import annotations

import json
from pathlib import Path

import pytest

from kodepoia.desktop.app_model import canonical_sample_app
from kodepoia.desktop.contracts import DesktopFramework
from kodepoia.desktop.winui3 import (
    WinUi3Adapter,
    WinUiDeploymentContract,
    WinUiDeploymentMode,
    canonical_winui_deployment,
)


def test_winui_deployment_contract_is_deterministic() -> None:
    first = canonical_winui_deployment()
    second = canonical_winui_deployment()
    assert first.canonical() == second.canonical()
    assert first.digest() == second.digest()
    assert first.mode is WinUiDeploymentMode.UNPACKAGED_SELF_CONTAINED


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("package_name", "../escape"),
        ("package_name", "A;Exec=calc"),
        ("publisher", "CN=Kodepoia\nInjected"),
        ("version", "1.0.*"),
    ],
)
def test_winui_identity_injection_is_rejected(field: str, value: str) -> None:
    data = {
        "package_name": "Kodepoia.WinUI3.Fixture",
        "publisher": "CN=Kodepoia",
        "version": "1.0.0.0",
        "mode": WinUiDeploymentMode.UNPACKAGED_SELF_CONTAINED,
        "min_windows_build": 17763,
    }
    data[field] = value
    with pytest.raises(ValueError):
        WinUiDeploymentContract(**data)


def test_winui_minimum_windows_build_is_enforced() -> None:
    with pytest.raises(ValueError, match="17763"):
        WinUiDeploymentContract(
            "Kodepoia.WinUI3.Fixture",
            "CN=Kodepoia",
            "1.0.0.0",
            WinUiDeploymentMode.UNPACKAGED_SELF_CONTAINED,
            17000,
        )


def test_winui_render_fixture_maps_shared_logical_model(tmp_path: Path) -> None:
    adapter = WinUi3Adapter(tmp_path, tmp_path / "stage")
    model = canonical_sample_app()
    app, probe, manifest, model_sha = adapter.render_fixture(
        model, canonical_winui_deployment()
    )
    assert model_sha == model.conformance_projection(DesktopFramework.WINUI3).logical_model_sha256
    app_text = app.read_text(encoding="utf-8")
    assert "<UseWinUI>true</UseWinUI>" in app_text
    assert "<WindowsPackageType>None</WindowsPackageType>" in app_text
    assert "<WindowsAppSDKSelfContained>true</WindowsAppSDKSelfContained>" in app_text
    assert WinUi3Adapter.WINDOWS_APP_SDK_VERSION in app_text
    assert probe.is_file()
    manifest_text = manifest.read_text(encoding="utf-8")
    assert 'Name="Kodepoia.WinUI3.Fixture"' in manifest_text
    assert 'Publisher="CN=Kodepoia"' in manifest_text
    assert model_sha in (adapter.fixture_root / "App" / "MainWindow.xaml").read_text(encoding="utf-8")


def test_winui_runtime_fixture_rejects_packaged_mode(tmp_path: Path) -> None:
    adapter = WinUi3Adapter(tmp_path, tmp_path / "stage")
    packaged = WinUiDeploymentContract(
        "Kodepoia.WinUI3.Fixture",
        "CN=Kodepoia",
        "1.0.0.0",
        WinUiDeploymentMode.PACKAGED_MSIX,
    )
    with pytest.raises(ValueError, match="unpackaged self-contained"):
        adapter.render_fixture(canonical_sample_app(), packaged)


def test_winui_schema_is_valid_json() -> None:
    schema = Path("schemas/r12/winui-deployment.schema.json")
    payload = json.loads(schema.read_text(encoding="utf-8"))
    assert payload["additionalProperties"] is False
    assert "packaged_msix" in payload["properties"]["mode"]["enum"]
