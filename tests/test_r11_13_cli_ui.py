from __future__ import annotations

import json
import os

import pytest

from kodepoia.cli import build_parser
from kodepoia.media.r11_cli import UNSAFE_OPTION_TOKENS
from kodepoia.media.workspace import R11Capability, R11WorkspaceService, WorkspaceState


EXPECTED_GROUPS = (
    "audio",
    "cues",
    "voice",
    "synthesis",
    "alignment",
    "facial",
    "cinematics",
    "continuity",
    "franchise",
    "canon",
    "savebridge",
)


def test_r11_cli_groups_emit_stable_structured_json(capsys: pytest.CaptureFixture[str]) -> None:
    parser = build_parser()
    for group in EXPECTED_GROUPS:
        args = parser.parse_args(["r11", group, "status"])
        assert args.func(args) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["schema_version"] == 1
        assert payload["operation"] == "status"
        assert payload["group"] == group
        assert payload["state"] in {"READY", "READY_WITH_ACCEPTED_EVIDENCE"}
        assert isinstance(payload["accepted_evidence"], list)
        assert isinstance(payload["blockers"], list)


def test_r11_cli_summary_covers_all_frozen_groups(capsys: pytest.CaptureFixture[str]) -> None:
    args = build_parser().parse_args(["r11", "status"])
    assert args.func(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == 1
    assert payload["operation"] == "summary"
    assert [item["group"] for item in payload["capabilities"]] == list(EXPECTED_GROUPS)
    assert payload["blockers"] == []


def test_r11_cli_exposes_no_raw_process_model_or_migration_options() -> None:
    parser = build_parser()
    seen: set[str] = set()

    def walk(current) -> None:
        for action in current._actions:
            seen.update(action.option_strings)
            choices = getattr(action, "choices", None)
            if isinstance(choices, dict):
                for child in choices.values():
                    walk(child)

    walk(parser)
    assert not (seen & UNSAFE_OPTION_TOKENS)


def test_blocked_capability_has_explicit_nonzero_exit_and_blocker() -> None:
    service = R11WorkspaceService(
        (
            R11Capability(
                "audio",
                "Audio",
                "R11.2",
                WorkspaceState.BLOCKED,
                blockers=("RIGHTS_BLOCKED",),
            ),
        )
    )
    assert service.exit_code_for("audio") == 2
    assert service.status_payload("audio")["blockers"] == ["RIGHTS_BLOCKED"]


def test_required_runtime_evidence_is_named_without_probing_runtime() -> None:
    service = R11WorkspaceService()
    synthesis = service.capability("synthesis")
    cinematics = service.capability("cinematics")
    assert synthesis.runtime_state is WorkspaceState.NOT_PROBED
    assert cinematics.runtime_state is WorkspaceState.NOT_PROBED
    assert synthesis.accepted_evidence == ("docs/roadmap/R11_5_LOCAL_ACCEPTANCE.json",)
    assert cinematics.accepted_evidence == ("docs/roadmap/R11_9_LOCAL_ACCEPTANCE.json",)


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QListWidget, QLineEdit, QPlainTextEdit, QPushButton, QTabWidget

from kodepoia.core.kill_switch import KillSwitch
from kodepoia.kodestudio.accessibility import audit_qt_surface
from kodepoia.kodestudio.app import build_window
from kodepoia.kodestudio.r11_localization import R11Translator
from kodepoia.quality.accessibility import AccessibilityReportStatus, AccessibilityStatus


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_r11_workspace_is_navigable_accessible_and_has_no_raw_editor() -> None:
    _app()
    window = build_window()
    window.show()
    QApplication.processEvents()
    try:
        nav = window.findChild(QListWidget, "mainNavigation")
        assert nav is not None and nav.count() == 10
        assert any(nav.item(index).text() == "Media / Franchise" for index in range(nav.count()))

        tabs = window.findChild(QTabWidget, "r11WorkspaceTabs")
        refresh = window.findChild(QPushButton, "r11RefreshButton")
        cancel = window.findChild(QPushButton, "r11CancelButton")
        assert tabs is not None and tabs.count() == 5
        assert refresh is not None and cancel is not None
        assert tabs.accessibleName()
        assert refresh.accessibleDescription()
        assert cancel.accessibleDescription()

        page = window.findChild(type(tabs.parentWidget()), "r11WorkspacePage")
        assert page is not None
        assert page.findChildren(QLineEdit) == []
        evidence_views = page.findChildren(QPlainTextEdit)
        assert len(evidence_views) == 5
        assert all(view.isReadOnly() for view in evidence_views)

        expected = (
            "r11WorkspaceTabs",
            "r11_audio_table",
            "r11_audio_evidence",
            "r11_voice_table",
            "r11_voice_evidence",
            "r11_cinematics_table",
            "r11_cinematics_evidence",
            "r11_franchise_table",
            "r11_franchise_evidence",
            "r11_persistence_table",
            "r11_persistence_evidence",
            "r11RefreshButton",
            "r11CancelButton",
        )
        report = audit_qt_surface(window, surface="r11-workspace", expected_ids=expected)
        failures = [
            item for item in report.results
            if item.status in {AccessibilityStatus.FAIL, AccessibilityStatus.UNKNOWN}
        ]
        assert report.status is AccessibilityReportStatus.PASS, failures
    finally:
        window.close()
        QApplication.processEvents()


def test_r11_cancel_reuses_global_killswitch_boundary() -> None:
    _app()
    switch = KillSwitch()
    window = build_window(switch)
    window.show()
    QApplication.processEvents()
    try:
        cancel = window.findChild(QPushButton, "r11CancelButton")
        assert cancel is not None
        cancel.click()
        QApplication.processEvents()
        assert switch.triggered
    finally:
        window.close()
        QApplication.processEvents()


def test_r11_workspace_pseudo_localizes_navigation_tabs_and_controls() -> None:
    _app()
    window = build_window(locale="qps-ploc")
    window.show()
    QApplication.processEvents()
    try:
        nav = window.findChild(QListWidget, "mainNavigation")
        tabs = window.findChild(QTabWidget, "r11WorkspaceTabs")
        refresh = window.findChild(QPushButton, "r11RefreshButton")
        cancel = window.findChild(QPushButton, "r11CancelButton")
        assert nav is not None and tabs is not None and refresh is not None and cancel is not None
        assert all(nav.item(index).text().startswith("⟦") for index in range(nav.count()))
        assert all(tabs.tabText(index).startswith("⟦") for index in range(tabs.count()))
        assert refresh.text().startswith("⟦")
        assert cancel.text().startswith("⟦")
        assert R11Translator("qps-ploc").text("r11.nav").startswith("⟦")
    finally:
        window.close()
        QApplication.processEvents()
