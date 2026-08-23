from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QWidget,
)

from kodepoia.kodestudio.app import build_window


class FakeComfyService:
    def fork(self):
        return self

    def status(self):
        return {
            "state": "ready",
            "protocol_ready": True,
            "capability_state": "current",
        }

    def vram(self, **_kwargs):
        return {
            "state": "ready",
            "telemetry": {
                "devices": [
                    {"vram_free_bytes": 8 * 1024**3, "vram_total_bytes": 12 * 1024**3}
                ]
            },
            "admission": {"decision": "admit"},
            "ollama_coexistence": {"state": "n/a", "models": []},
        }

    def validate(self, family, **_kwargs):
        return {
            "state": "ready",
            "family": family,
            "compatibility": {
                "state": "compatible",
                "selected_models": [["checkpoint", "fixture.safetensors"]],
            },
        }

    def run(self, family, **_kwargs):
        return {
            "state": "queued",
            "family": family,
            "compatibility": {
                "state": "compatible",
                "selected_models": [["checkpoint", "fixture.safetensors"]],
            },
            "admission": {"decision": "admit"},
            "run": {"run_id": "run_" + "1" * 32, "state": "queued", "progress_fraction": 0.0},
        }

    def run_status(self, run_id, **_kwargs):
        return {"run_id": run_id, "state": "running", "progress_fraction": 0.5}

    def cancel(self, run_id):
        return {"run_id": run_id, "state": "cancelled"}

    def free_memory(self):
        return {"state": "requested", "evidence": {"request_acknowledged": True}}

    def evidence(self, run_id):
        return {"state": "ready", "run": {"run_id": run_id}, "outputs": []}


def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_kodestudio_exposes_service_backed_comfyui_vram_page(tmp_path: Path) -> None:
    qt_app()
    window = build_window(project_root=tmp_path, comfy_service=FakeComfyService())
    window.show()
    QApplication.processEvents()

    page = window.findChild(QWidget, "comfyPage")
    assert page is not None
    assert page.findChild(QComboBox, "comfyWorkflowFamily") is not None
    assert page.findChild(QLineEdit, "comfyModelSelection") is not None
    assert page.findChild(QPlainTextEdit, "comfyPrompt") is not None
    assert page.findChild(QPlainTextEdit, "comfyNegativePrompt") is not None
    assert page.findChild(QPushButton, "comfyRefreshButton") is not None
    assert page.findChild(QPushButton, "comfyValidateButton") is not None
    assert page.findChild(QPushButton, "comfyRunButton") is not None
    assert page.findChild(QPushButton, "comfyRunRefreshButton") is not None
    assert page.findChild(QPushButton, "comfyCancelButton") is not None
    assert page.findChild(QPushButton, "comfyFreeMemoryButton") is not None
    assert page.findChild(QPushButton, "comfyEvidenceButton") is not None
    assert page.findChild(QLabel, "comfyConnectionStatus") is not None
    assert page.findChild(QLabel, "comfyCapabilityStatus") is not None
    assert page.findChild(QLabel, "comfyVramStatus") is not None
    assert page.findChild(QLabel, "comfyOllamaStatus") is not None
    assert page.findChild(QLabel, "comfyModelStatus") is not None
    assert page.findChild(QLabel, "comfyAdmissionStatus") is not None
    assert page.findChild(QLabel, "comfyRunStatus") is not None
    assert page.findChild(QPlainTextEdit, "comfyEvidenceView") is not None
    assert getattr(page, "_kodepoia_comfy_service", None) is not None

    window.close()
