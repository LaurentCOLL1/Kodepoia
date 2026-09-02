from __future__ import annotations

import platform
from pathlib import Path

import pytest

from kodepoia.desktop.boundary import DesktopBoundaryError, DesktopToolchainBoundary
from kodepoia.desktop.windows_beta_acceptance import (
    build_dotnet_publish_argv,
    build_windows_desktop_report,
)

ROOT = Path(__file__).resolve().parents[1]


def test_r16_12_publish_argv_is_shell_free_and_bounded(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    project_root = tmp_path / "Representative App With Spaces"
    staging = project_root / ".kodepoia" / "staging with spaces"
    runtime.mkdir()
    staging.mkdir(parents=True)
    dotnet = runtime / "dotnet.exe"
    dotnet.write_bytes(b"synthetic")
    project = project_root / "App With Spaces" / "App.csproj"
    project.parent.mkdir(parents=True)
    project.write_text("<Project />\n", encoding="utf-8")

    boundary = DesktopToolchainBoundary(
        allowed_runtime_roots=(runtime,),
        project_root=project_root,
        staging_root=staging,
    )
    output = staging / "Published Package With Spaces"
    argv = build_dotnet_publish_argv(
        boundary,
        dotnet,
        project_file=project,
        output_directory=output,
    )

    assert argv[0] == str(dotnet.resolve())
    assert argv[1] == "publish"
    assert str(project.resolve()) in argv
    assert str(output.resolve()) in argv
    assert "--no-restore" in argv
    assert len(argv) == 9


def test_r16_12_publish_rejects_project_escape(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    project_root = tmp_path / "project"
    staging = project_root / "staging"
    runtime.mkdir()
    staging.mkdir(parents=True)
    dotnet = runtime / "dotnet.exe"
    dotnet.write_bytes(b"synthetic")
    outside = tmp_path / "outside.csproj"
    outside.write_text("<Project />\n", encoding="utf-8")

    boundary = DesktopToolchainBoundary(
        allowed_runtime_roots=(runtime,),
        project_root=project_root,
        staging_root=staging,
    )
    with pytest.raises(DesktopBoundaryError, match="escapes project root"):
        build_dotnet_publish_argv(
            boundary,
            dotnet,
            project_file=outside,
            output_directory=staging / "publish",
        )


def test_r16_12_publish_rejects_output_escape(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    project_root = tmp_path / "project"
    staging = project_root / "staging"
    runtime.mkdir()
    staging.mkdir(parents=True)
    dotnet = runtime / "dotnet.exe"
    dotnet.write_bytes(b"synthetic")
    project = project_root / "App.csproj"
    project.write_text("<Project />\n", encoding="utf-8")

    boundary = DesktopToolchainBoundary(
        allowed_runtime_roots=(runtime,),
        project_root=project_root,
        staging_root=staging,
    )
    with pytest.raises(DesktopBoundaryError, match="escapes staging root"):
        build_dotnet_publish_argv(
            boundary,
            dotnet,
            project_file=project,
            output_directory=tmp_path / "outside-publish",
        )


@pytest.mark.skipif(platform.system() != "Windows", reason="R16.12 live WPF acceptance is Windows-only")
def test_r16_12_live_windows_report() -> None:
    report = build_windows_desktop_report(
        ROOT,
        source_sha="1" * 40,
        platform="Windows-test",
    )
    failed = [item for item in report["cases"] if not item["pass"]]
    assert report["security_claim"] is True, failed
    assert report["critical_veto"] is False
    assert report["manual_state"] == "NONE"
    assert report["canonical_framework"] == "wpf"
    assert report["summary"]["failed"] == 0
    assert report["secret_free"] is True
    assert report["package_manifest"]["signing_state"] == "UNSIGNED"
    assert len(report["package_manifest_sha256"]) == 64
    assert len(report["semantic_sha256"]) == 64
    assert len(report["evidence_sha256"]) == 64
