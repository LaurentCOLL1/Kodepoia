from __future__ import annotations

import json
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QTableWidget, QWidget

from kodepoia.kodestudio.app import build_window
from kodepoia.kodestudio.model_lab import ModelLabInventoryService


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_v246_empty_accelerator_state_is_accessible_missing_and_non_authorizing(tmp_path) -> None:
    _app()
    root = tmp_path / "project"
    service = ModelLabInventoryService(
        root,
        kaggle_doctor_provider=lambda: {
            "ready": False,
            "authenticated": False,
            "cli_available": True,
            "version": "fixture",
            "detail": "authentication unavailable",
        },
        kaggle_quota_provider=lambda: {"version": "fixture", "entries": []},
        ollama_snapshot_provider=lambda: {"base_url": "", "models": [], "version": None},
    )
    window = build_window(project_root=root, model_lab_service=service, locale="qps-ploc")
    window.show()
    QApplication.processEvents()

    topology = window.findChild(QLabel, "modelLabAcceleratorTopology")
    devices = window.findChild(QTableWidget, "modelLabAcceleratorDevices")
    selector = window.findChild(QComboBox, "modelLabAcceleratorStrategy")
    mapping = window.findChild(QTableWidget, "modelLabAcceleratorStrategyMapping")
    live = window.findChild(QLabel, "modelLabAcceleratorLiveQualification")

    assert topology is not None and "missing" in topology.text().lower()
    assert devices is not None and devices.rowCount() == 0
    assert selector is not None and selector.count() == 0
    assert mapping is not None and mapping.rowCount() == 0
    assert live is not None and live.text()
    for widget in (devices, selector, mapping):
        assert widget.accessibleName()
        assert widget.accessibleDescription()

    assert window.findChild(QWidget, "modelLabAcceleratorLaunch") is None
    assert window.findChild(QWidget, "modelLabInstallDependency") is None
    assert window.findChild(QWidget, "modelLabPublicPublish") is None
    window.close()


def test_v246_blocked_live_evidence_is_rendered_as_blocked_not_qualified(tmp_path) -> None:
    _app()
    root = tmp_path / "project"
    tuning = root / ".kodepoia" / "tuning"
    tuning.mkdir(parents=True)
    (tuning / "live-blocked.json").write_text(
        json.dumps(
            {
                "schema": "kodepoia.v2.4.5.kaggle-live-qualification-report",
                "schema_version": 1,
                "source_sha": "1" * 40,
                "status": "blocked",
                "production_qualified": False,
                "blockers": [
                    "provider_auth_unavailable",
                    "download_revalidation_missing",
                ],
                "report_digest": "a" * 64,
            }
        ),
        encoding="utf-8",
    )
    service = ModelLabInventoryService(
        root,
        kaggle_doctor_provider=lambda: {
            "ready": False,
            "authenticated": False,
            "cli_available": True,
            "version": "fixture",
            "detail": "network unavailable",
        },
        kaggle_quota_provider=lambda: {"version": "fixture", "entries": []},
        ollama_snapshot_provider=lambda: {"base_url": "", "models": [], "version": None},
    )
    window = build_window(project_root=root, model_lab_service=service, locale="en")
    window.show()
    QApplication.processEvents()

    live = window.findChild(QLabel, "modelLabAcceleratorLiveQualification")
    assert live is not None
    text = live.text().lower()
    assert "provider_auth_unavailable" in text
    assert "download_revalidation_missing" in text
    assert "qualified" not in text or "not qualified" in text
    assert window.findChild(QWidget, "modelLabAcceleratorLaunch") is None
    window.close()
