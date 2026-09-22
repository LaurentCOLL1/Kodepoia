from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QTableWidget, QWidget

from kodepoia.kodestudio.app import build_window
from kodepoia.kodestudio.model_lab import ModelLabInventoryService
from kodepoia.kodestudio.preferences import ApplicationPreferences


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _service(tmp_path: Path) -> ModelLabInventoryService:
    root = tmp_path / "project"
    tuning = root / ".kodepoia" / "tuning"
    tuning.mkdir(parents=True)
    topology = {
        "schema": "kodepoia.v2.4.1.accelerator-topology",
        "disposition": "ready",
        "topology_digest": "c" * 64,
        "provider_request": {
            "provider": "kaggle",
            "shape": "NvidiaTeslaT4",
            "expected_backend": "cuda",
            "expected_device_count": 2,
            "expected_name_contains": "T4",
        },
        "observed": {
            "backend_type": "cuda",
            "device_count": 2,
            "devices": [
                {"backend_type": "cuda", "index": 0, "name": "NVIDIA Tesla T4", "vram_free_bytes": 12, "vram_total_bytes": 16},
                {"backend_type": "cuda", "index": 1, "name": "NVIDIA Tesla T4", "vram_free_bytes": 11, "vram_total_bytes": 16},
            ],
        },
    }
    (tuning / "topology.json").write_text(json.dumps(topology), encoding="utf-8")
    for strategy, digest, ordinals, world_size in (
        ("single_gpu", "d" * 64, [0], 1),
        ("replicated_data_parallel", "e" * 64, [0, 1], 2),
    ):
        (tuning / f"{strategy}.json").write_text(
            json.dumps(
                {
                    "schema": "kodepoia.v2.4.2.execution-strategy-plan",
                    "strategy": strategy,
                    "strategy_plan_digest": digest,
                    "training_plan_digest": "a" * 64,
                    "topology_report_digest": "b" * 64,
                    "topology_digest": "c" * 64,
                    "world_size": world_size,
                    "device_ordinals": ordinals,
                    "device_budgets": [],
                    "per_device_batch_size": 1,
                    "gradient_accumulation_steps": 4 // world_size,
                    "effective_global_batch_size": 4,
                }
            ),
            encoding="utf-8",
        )
    prefs = ApplicationPreferences(tmp_path / "settings.json")
    return ModelLabInventoryService(
        root,
        preferences=prefs,
        kaggle_doctor_provider=lambda: {
            "ready": False,
            "authenticated": False,
            "cli_available": True,
            "version": "fixture",
            "detail": "authentication unavailable",
        },
        kaggle_quota_provider=lambda: {
            "version": "fixture",
            "entries": [],
        },
        ollama_snapshot_provider=lambda: {"base_url": "", "models": [], "version": None},
    )


def test_model_lab_accelerator_ui_is_structured_localized_and_accessible(tmp_path: Path) -> None:
    _app()
    service = _service(tmp_path)
    window = build_window(locale="fr", project_root=service.root, model_lab_service=service)
    window.show()
    QApplication.processEvents()
    provider = window.findChild(QLabel, "modelLabAcceleratorProvider")
    topology = window.findChild(QLabel, "modelLabAcceleratorTopology")
    devices = window.findChild(QTableWidget, "modelLabAcceleratorDevices")
    selector = window.findChild(QComboBox, "modelLabAcceleratorStrategy")
    mapping = window.findChild(QTableWidget, "modelLabAcceleratorStrategyMapping")
    live = window.findChild(QLabel, "modelLabAcceleratorLiveQualification")
    assert provider is not None and "NvidiaTeslaT4" in provider.text()
    assert topology is not None and "ready" in topology.text()
    assert devices is not None and devices.rowCount() == 2
    assert selector is not None and selector.count() == 2
    assert mapping is not None and mapping.rowCount() == 1
    assert live is not None and "absente" in live.text().lower()
    for widget in (devices, selector, mapping):
        assert widget.accessibleName()
        assert widget.accessibleDescription()
    assert window.findChild(QWidget, "modelLabAcceleratorLaunch") is None
    window.close()


def test_strategy_selector_changes_projection_only_and_runtime_refresh_is_explicit(
    tmp_path: Path,
) -> None:
    _app()
    service = _service(tmp_path)
    window = build_window(project_root=service.root, model_lab_service=service)
    selector = window.findChild(QComboBox, "modelLabAcceleratorStrategy")
    mapping = window.findChild(QTableWidget, "modelLabAcceleratorStrategyMapping")
    kaggle = window.findChild(QLabel, "modelLabKaggleState")
    assert selector is not None and mapping is not None and kaggle is not None
    assert "not_checked" in kaggle.text()
    selector.setCurrentText("replicated_data_parallel")
    QApplication.processEvents()
    assert mapping.item(0, 0).text() == "replicated_data_parallel"
    assert mapping.item(0, 1).text() == "2"
    assert "0, 1" in mapping.item(0, 2).text()
    assert mapping.item(0, 5).text() == "4"
    window.close()
