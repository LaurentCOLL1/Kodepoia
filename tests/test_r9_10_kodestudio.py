from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QWidget,
)

from kodepoia.kodestudio.app import build_window


def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def wait_for(predicate, *, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        QApplication.processEvents()
        if predicate():
            return
        time.sleep(0.01)
    QApplication.processEvents()
    assert predicate()


class FakeComfyService:
    def __init__(self) -> None:
        self.ready = True
        self.capability_state = "current"
        self.delay = 0.0
        self.validate_state = "compatible"
        self.run_state = "queued"
        self.run_progress = 0.2
        self.run_error: str | None = None
        self.closed = False

    def fork(self):
        return self

    def close(self) -> None:
        self.closed = True

    def workflow_families(self):
        return (
            {"family": "concept"},
            {"family": "ui_illustration"},
            {"family": "material_source"},
            {"family": "sprite_2d"},
        )

    def status(self):
        if self.delay:
            time.sleep(self.delay)
        return {
            "ready": self.ready,
            "capability_state": self.capability_state,
            "vram_total_bytes": 12_000 * 1024 * 1024 if self.ready else None,
            "vram_free_bytes": 8_000 * 1024 * 1024 if self.ready else None,
            "reason": "fixture-ready" if self.ready else f"fixture-{self.capability_state}",
        }

    def inventory_snapshot(self):
        return {
            "models": [
                {"model_type": "checkpoints", "tokens": ["models/a.safetensors", "models/b.safetensors"]}
            ]
        }

    def validate_workflow(self, _family, *, model_selections):
        assert model_selections["checkpoint"]
        return {"state": self.validate_state, "reasons": [] if self.validate_state == "compatible" else ["missing model"]}

    def run_workflow(self, _family, *, parameters, model_selections, allow_memory_cleanup=False):
        assert parameters["prompt"]
        assert parameters["negative_prompt"]
        assert model_selections["checkpoint"]
        assert isinstance(allow_memory_cleanup, bool)
        if self.run_error:
            raise RuntimeError(self.run_error)
        return {
            "manifest": self._manifest(self.run_state, self.run_progress),
            "admission": {"decision": "admit"},
            "cleanup_trace": None,
        }

    def run_status(self, _run_id):
        return self._manifest(self.run_state, self.run_progress)

    def cancel_run(self, _run_id):
        self.run_state = "cancelled"
        self.run_progress = 0.2
        return self._manifest("cancelled", self.run_progress)

    def capture_run_outputs(self, _run_id):
        return {"state": "complete", "outputs": [{"revision_id": "rev_fixture"}]}

    def free_memory(self, *, confirmed=False):
        assert confirmed is True
        return {"request_acknowledged": True, "reclaimed_bytes": None}

    @staticmethod
    def _manifest(state: str, progress: float):
        refs = []
        if state == "succeeded":
            refs = [
                {
                    "node_id": "7",
                    "output_index": 0,
                    "server_filename": "fixture.png",
                    "storage_type": "output",
                }
            ]
        return {
            "run_id": "run_0123456789abcdef0123456789abcdef",
            "state": state,
            "progress_fraction": progress,
            "output_references": refs,
        }


def _page(tmp_path: Path, service: FakeComfyService, *, locale: str = "en"):
    qt_app()
    window = build_window(project_root=tmp_path, comfy_service=service, locale=locale)
    window.show()
    QApplication.processEvents()
    page = window.findChild(QWidget, "comfyPage")
    assert page is not None
    return window, page


def test_kodestudio_exposes_service_backed_comfy_panel_and_pseudo_localizes(tmp_path: Path) -> None:
    service = FakeComfyService()
    window, page = _page(tmp_path, service, locale="qps-ploc")
    try:
        assert page.findChild(QLabel, "comfyServiceStatus") is not None
        assert page.findChild(QLabel, "comfyCapabilityStatus") is not None
        assert page.findChild(QLabel, "comfyVramStatus") is not None
        assert page.findChild(QPushButton, "comfyRefreshButton") is not None
        assert page.findChild(QComboBox, "comfyWorkflowFamily") is not None
        assert page.findChild(QComboBox, "comfyModelCheckpoint") is not None
        assert page.findChild(QPlainTextEdit, "comfyPrompt") is not None
        assert page.findChild(QPlainTextEdit, "comfyNegativePrompt") is not None
        assert page.findChild(QLineEdit, "comfySeed") is not None
        assert page.findChild(QPushButton, "comfyValidateButton") is not None
        assert page.findChild(QPushButton, "comfyRunButton") is not None
        assert page.findChild(QPushButton, "comfyCancelButton") is not None
        assert page.findChild(QPushButton, "comfyCaptureButton") is not None
        assert page.findChild(QPushButton, "comfyFreeMemoryButton") is not None
        assert page.findChild(QProgressBar, "comfyProgress") is not None
        assert page.findChild(QTableWidget, "comfyOutputTable") is not None
        assert page.findChild(QPlainTextEdit, "comfyEvidenceView") is not None
        assert hasattr(page, "_kodepoia_comfy_service")
        assert "ComfyUI" in page.accessibleName()
    finally:
        window.close()


def test_comfy_refresh_is_non_blocking_and_surfaces_disconnected_stale_and_current(tmp_path: Path) -> None:
    service = FakeComfyService()
    service.delay = 0.25
    window, page = _page(tmp_path, service)
    refresh = page.findChild(QPushButton, "comfyRefreshButton")
    state = page.findChild(QLabel, "comfyServiceStatus")
    capability = page.findChild(QLabel, "comfyCapabilityStatus")
    assert refresh is not None and state is not None and capability is not None
    try:
        started = time.monotonic()
        refresh.click()
        QApplication.processEvents()
        assert time.monotonic() - started < 0.12
        wait_for(lambda: "LOCAL READY" in state.text(), timeout=2.0)
        assert "current" in capability.text()

        service.delay = 0.0
        service.ready = False
        service.capability_state = "unavailable"
        refresh.click()
        wait_for(lambda: "UNAVAILABLE" in state.text())

        service.capability_state = "stale"
        refresh.click()
        wait_for(lambda: "stale" in capability.text())
    finally:
        window.close()


def test_comfy_ui_covers_missing_model_queue_running_success_failure_cancel_and_resource_block(tmp_path: Path) -> None:
    service = FakeComfyService()
    window, page = _page(tmp_path, service)
    model = page.findChild(QComboBox, "comfyModelCheckpoint")
    prompt = page.findChild(QPlainTextEdit, "comfyPrompt")
    negative = page.findChild(QPlainTextEdit, "comfyNegativePrompt")
    validate = page.findChild(QPushButton, "comfyValidateButton")
    run = page.findChild(QPushButton, "comfyRunButton")
    refresh_run = page.findChild(QPushButton, "comfyRunRefreshButton")
    cancel = page.findChild(QPushButton, "comfyCancelButton")
    warning = page.findChild(QLabel, "comfyWarning")
    operation = page.findChild(QLabel, "comfyOperationStatus")
    run_id = page.findChild(QLineEdit, "comfyRunId")
    output_table = page.findChild(QTableWidget, "comfyOutputTable")
    assert all(item is not None for item in (model, prompt, negative, validate, run, refresh_run, cancel, warning, operation, run_id, output_table))
    try:
        model.setEditText("models/a.safetensors")
        prompt.setPlainText("fixture prompt")
        negative.setPlainText("fixture negative")

        service.validate_state = "blocked"
        validate.click()
        wait_for(lambda: "blocked" in warning.text().lower())

        service.validate_state = "compatible"
        validate.click()
        wait_for(lambda: "READY" in operation.text())

        service.run_state = "queued"
        service.run_progress = 0.1
        run.click()
        wait_for(lambda: run_id.text().startswith("run_"))
        assert "queued" in operation.text()

        service.run_state = "running"
        service.run_progress = 0.55
        refresh_run.click()
        wait_for(lambda: "running" in operation.text())

        service.run_state = "succeeded"
        service.run_progress = 1.0
        refresh_run.click()
        wait_for(lambda: "succeeded" in operation.text())
        assert output_table.rowCount() == 1

        service.run_state = "failed"
        refresh_run.click()
        wait_for(lambda: "failed" in operation.text())

        service.run_state = "running"
        cancel.click()
        wait_for(lambda: "cancelled" in operation.text())

        service.run_error = "GPU admission is reject: resource blocked"
        run.click()
        wait_for(lambda: "resource blocked" in operation.text().lower())
    finally:
        window.close()


def test_free_memory_button_requires_explicit_ui_confirmation(tmp_path: Path) -> None:
    service = FakeComfyService()
    window, page = _page(tmp_path, service)
    confirm = page.findChild(QCheckBox, "comfyFreeConfirm")
    button = page.findChild(QPushButton, "comfyFreeMemoryButton")
    operation = page.findChild(QLabel, "comfyOperationStatus")
    assert confirm is not None and button is not None and operation is not None
    try:
        assert button.isEnabled() is False
        confirm.setChecked(True)
        assert button.isEnabled() is True
        button.click()
        wait_for(lambda: "remeasurement" in operation.text().lower())
        assert confirm.isChecked() is False
        assert button.isEnabled() is False
    finally:
        window.close()
