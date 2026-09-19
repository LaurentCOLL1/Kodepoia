from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QListWidget,
    QPushButton,
    QTableWidget,
    QWidget,
)

from kodepoia.kodestudio.app import build_window
from kodepoia.kodestudio.model_lab import ModelLabInventoryService
from kodepoia.kodestudio.preferences import ApplicationPreferences


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _service(tmp_path: Path) -> ModelLabInventoryService:
    root = tmp_path / "project"
    dataset = root / ".kodepoia" / "datasets" / "dataset.json"
    dataset.parent.mkdir(parents=True)
    dataset.write_text(
        json.dumps(
            {
                "schema": "kodepoia.r15.dataset.manifest",
                "dataset_id": "dataset-ui-v1",
                "manifest_digest": "1" * 64,
                "state": "ready",
            }
        ),
        encoding="utf-8",
    )
    preferences = ApplicationPreferences(tmp_path / "settings.json")
    preferences.update(
        {
            "model_roles": {"core": "qwen3.5:9b"},
            "ollama_base_url": "http://127.0.0.1:11434",
        }
    )
    return ModelLabInventoryService(
        root,
        preferences=preferences,
        ollama_snapshot_provider=lambda: {
            "base_url": "http://127.0.0.1:11434",
            "version": "0.fixture",
            "models": ["qwen3.5:9b", "granite4.1:3b"],
        },
        kaggle_doctor_provider=lambda: {
            "ready": True,
            "installed": True,
            "authenticated": True,
            "version": "fixture",
            "detail": "fixture ready",
        },
        kaggle_quota_provider=lambda: {
            "version": "fixture",
            "entries": [],
        },
    )


def test_model_lab_is_wired_localized_structured_and_read_only(tmp_path: Path) -> None:
    _app()
    service = _service(tmp_path)
    window = build_window(
        locale="fr",
        project_root=service.root,
        model_lab_service=service,
    )
    window.show()
    QApplication.processEvents()

    page = window.findChild(QWidget, "modelLabPage")
    assert page is not None
    nav = window.findChild(QListWidget, "mainNavigation")
    assert nav is not None
    labels = [nav.item(index).text() for index in range(nav.count())]
    assert "Laboratoire modèles" in labels

    notice = window.findChild(QLabel, "modelLabReadOnlyNotice")
    state = window.findChild(QLabel, "modelLabState")
    evidence = window.findChild(QTableWidget, "modelLabEvidenceTable")
    registry = window.findChild(QTableWidget, "modelLabRegistryTable")
    models = window.findChild(QTableWidget, "modelLabModelsTable")
    capabilities = window.findChild(QTableWidget, "modelLabCapabilitiesTable")
    lineage = window.findChild(QTableWidget, "modelLabLineageTable")
    assert notice is not None and "Lecture seule" in notice.text()
    assert state is not None
    assert evidence is not None and evidence.rowCount() == 1
    assert evidence.item(0, 1).text() == "dataset-ui-v1"
    assert registry is not None
    assert models is not None and models.rowCount() == 1
    assert "qwen3.5:9b" in models.item(0, 0).text()
    assert capabilities is not None and capabilities.rowCount() >= 8
    assert lineage is not None

    for object_name in (
        "modelLabRefreshInventory",
        "modelLabRefreshRuntime",
        "modelLabStoresTable",
        "modelLabEvidenceTable",
        "modelLabRegistryTable",
        "modelLabModelsTable",
        "modelLabCapabilitiesTable",
        "modelLabLineageTable",
        "modelLabDiagnostics",
    ):
        widget = window.findChild(QWidget, object_name)
        assert widget is not None, object_name
        assert widget.accessibleName(), object_name
        assert widget.accessibleDescription(), object_name

    forbidden = {
        "modelLabBuildDataset",
        "modelLabTrain",
        "modelLabConvert",
        "modelLabPromote",
        "modelLabRollback",
        "modelLabRawCommand",
        "modelLabSecret",
    }
    present = {
        child.objectName()
        for child in window.findChildren(QWidget)
        if child.objectName()
    }
    assert forbidden.isdisjoint(present)
    window.close()


def test_model_lab_runtime_refresh_is_explicit_and_runs_off_ui_thread(tmp_path: Path) -> None:
    _app()
    service = _service(tmp_path)
    window = build_window(
        project_root=service.root,
        model_lab_service=service,
    )
    page = window.findChild(QWidget, "modelLabPage")
    refresh = window.findChild(QPushButton, "modelLabRefreshRuntime")
    models = window.findChild(QTableWidget, "modelLabModelsTable")
    ollama_state = window.findChild(QLabel, "modelLabOllamaState")
    kaggle_state = window.findChild(QLabel, "modelLabKaggleState")
    assert page is not None and refresh is not None
    assert models is not None and ollama_state is not None and kaggle_state is not None
    assert "not_checked" in ollama_state.text()

    refresh.click()
    deadline = time.monotonic() + 4.0
    while page._model_lab_workers and time.monotonic() < deadline:
        QApplication.processEvents()
        time.sleep(0.01)
    QApplication.processEvents()

    assert page._model_lab_workers == []
    assert refresh.isEnabled()
    assert "ready" in ollama_state.text()
    assert "ready" in kaggle_state.text()
    assert models.rowCount() == 2
    names = {models.item(index, 0).text() for index in range(models.rowCount())}
    assert names == {"granite4.1:3b", "qwen3.5:9b"}
    window.close()
