from __future__ import annotations

import json
from pathlib import Path

import pytest

from kodepoia.cli import build_parser
from kodepoia.core.kill_switch import KillSwitch
from kodepoia.desktop.contracts import DesktopArchitecture, DesktopFramework, DesktopPackageKind
from kodepoia.desktop.workspace import (
    DesktopExecutionReceipt,
    DesktopWorkspaceOperation,
    DesktopWorkspaceService,
    DesktopWorkspaceState,
)
from kodepoia.kodestudio.r12_localization import PSEUDO_LOCALE, r12_nav_text, registered_r12_messages
from kodepoia.project.dna import DesktopProjectProfile, Platform, ProjectDNA, ProjectType
from kodepoia.project.initializer import ProjectInitializer


def _desktop_project(root: Path) -> Path:
    dna = ProjectDNA(
        schema_version=1,
        name="R12DesktopFixture",
        project_type=ProjectType.DESKTOP_APP,
        platforms=[Platform.WINDOWS],
        desktop=DesktopProjectProfile(
            framework=DesktopFramework.WPF,
            architecture=DesktopArchitecture.X64,
            package_kind=DesktopPackageKind.ARCHIVE,
        ),
    )
    ProjectInitializer().initialize(root, dna)
    return root


def test_passive_status_never_calls_executor_and_reported_pass_is_not_promoted(tmp_path: Path) -> None:
    root = _desktop_project(tmp_path / "project")
    evidence_dir = root / ".kodepoia" / "desktop" / "evidence"
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "build.json").write_text(
        json.dumps({"status": "pass", "run_id": "user-editable-report"}),
        encoding="utf-8",
    )
    calls: list[DesktopWorkspaceOperation] = []

    def executor(operation, context, kill_switch):
        calls.append(operation)
        return DesktopExecutionReceipt(DesktopWorkspaceState.PASS, "unexpected")

    result = DesktopWorkspaceService(root, executor=executor, kill_switch=KillSwitch()).status()

    assert calls == []
    assert result.state is DesktopWorkspaceState.READY
    assert result.ok
    assert dict(result.evidence)["build"] == {
        "available": True,
        "read_only": True,
        "reported_status": "pass",
        "evidence_id": "user-editable-report",
    }


def test_validate_is_pure_and_build_requires_explicit_governed_backend(tmp_path: Path) -> None:
    root = _desktop_project(tmp_path / "project")
    service = DesktopWorkspaceService(root, kill_switch=KillSwitch())

    assert service.validate().state is DesktopWorkspaceState.PASS
    blocked = service.execute(DesktopWorkspaceOperation.BUILD)
    assert blocked.state is DesktopWorkspaceState.BLOCKED
    assert blocked.blockers == ("EXECUTION_BACKEND_UNAVAILABLE",)


def test_explicit_execution_receipt_is_structured_and_no_raw_command_surface(tmp_path: Path) -> None:
    root = _desktop_project(tmp_path / "project")
    observed: list[tuple[str, str, str]] = []

    def executor(operation, context, kill_switch):
        observed.append((operation.value, context.framework, context.architecture))
        return DesktopExecutionReceipt(
            DesktopWorkspaceState.PASS,
            "governed fixture completed",
            evidence=(("run_id", "bounded-run-1"),),
        )

    result = DesktopWorkspaceService(root, executor=executor, kill_switch=KillSwitch()).execute(
        DesktopWorkspaceOperation.TEST
    )
    assert result.state is DesktopWorkspaceState.PASS
    assert observed == [("test", "wpf", "x64")]
    assert dict(result.evidence) == {"run_id": "bounded-run-1"}

    parser = build_parser()
    args = parser.parse_args(["r12", "build", "--project", str(root)])
    assert args.r12_operation == "build"
    with pytest.raises(SystemExit):
        parser.parse_args(["r12", "build", "--project", str(root), "--executable", "cmd.exe"])
    with pytest.raises(SystemExit):
        parser.parse_args(["r12", "build", "--project", str(root), "--flag", "/p:Evil=true"])


def test_cli_status_json_is_stable_and_execution_blocked_is_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _desktop_project(tmp_path / "project")
    parser = build_parser()

    status_args = parser.parse_args(["r12", "status", "--project", str(root)])
    assert status_args.func(status_args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == 1
    assert payload["operation"] == "status"
    assert payload["state"] == "ready"
    assert payload["framework"] == "wpf"

    build_args = parser.parse_args(["r12", "build", "--project", str(root)])
    assert build_args.func(build_args) == 2
    blocked = json.loads(capsys.readouterr().out)
    assert blocked["state"] == "blocked"
    assert blocked["blockers"] == ["EXECUTION_BACKEND_UNAVAILABLE"]


def test_global_kill_switch_cancels_explicit_execution_before_backend(tmp_path: Path) -> None:
    root = _desktop_project(tmp_path / "project")
    switch = KillSwitch()
    calls: list[str] = []

    def executor(operation, context, kill_switch):
        calls.append(operation.value)
        return DesktopExecutionReceipt(DesktopWorkspaceState.PASS, "must not execute")

    service = DesktopWorkspaceService(root, executor=executor, kill_switch=switch)
    switch.trigger()
    result = service.execute(DesktopWorkspaceOperation.PACKAGE)
    assert result.state is DesktopWorkspaceState.CANCELLED
    assert result.blockers == ("KILL_SWITCH_ACTIVE",)
    assert calls == []


def test_missing_or_non_desktop_project_is_truthfully_blocked(tmp_path: Path) -> None:
    missing = DesktopWorkspaceService(tmp_path / "missing", kill_switch=KillSwitch()).status()
    assert missing.state is DesktopWorkspaceState.BLOCKED
    assert missing.blockers == ("PROJECT_DNA_MISSING",)

    root = tmp_path / "tool"
    dna = ProjectDNA(
        schema_version=1,
        name="NotDesktop",
        project_type=ProjectType.TOOL,
        platforms=[Platform.WINDOWS],
    )
    ProjectInitializer().initialize(root, dna)
    result = DesktopWorkspaceService(root, kill_switch=KillSwitch()).status()
    assert result.state is DesktopWorkspaceState.BLOCKED
    assert result.blockers == ("PROJECT_NOT_DESKTOP_APP",)


def test_r12_workspace_localization_has_source_and_pseudo_locale() -> None:
    messages = registered_r12_messages()
    assert "r12.nav" in messages
    assert "r12.refresh" in messages
    assert r12_nav_text("en") == "Desktop"
    assert r12_nav_text(PSEUDO_LOCALE) != "Desktop"


def test_kodestudio_r12_workspace_is_read_only_when_ui_available(tmp_path: Path, monkeypatch) -> None:
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication, QPlainTextEdit

    from kodepoia.kodestudio.r12_localization import R12Translator
    from kodepoia.kodestudio.r12_workspace import create_r12_workspace_page

    app = QApplication.instance() or QApplication([])
    root = _desktop_project(tmp_path / "project")
    page = create_r12_workspace_page(
        root,
        translator=R12Translator("en"),
        service=DesktopWorkspaceService(root, kill_switch=KillSwitch()),
    )
    evidence = page.findChild(QPlainTextEdit, "r12Evidence")
    assert evidence is not None
    assert evidence.isReadOnly()
    assert "\"state\": \"ready\"" in evidence.toPlainText()
    page.close()
    app.processEvents()
