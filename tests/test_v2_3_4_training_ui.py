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
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QWidget,
)

from kodepoia.kodestudio.app import build_window


class FakeTrainingService:
    schema = "kodepoia.v2.3.4.model-lab-training"

    def __init__(self, root: Path) -> None:
        self.root = root
        self.calls: list[tuple[str, str | None, str | None, bool]] = []

    def snapshot(self) -> dict[str, object]:
        plan_digest = "a" * 64
        run_id = "train-" + "a" * 20
        return {
            "schema": self.schema,
            "status": "ok",
            "plans": [
                {
                    "plan_digest": plan_digest,
                    "authorized": True,
                    "mode": "sft",
                    "model": {
                        "model_ref": "base",
                        "model_revision": "rev",
                        "model_digest": "b" * 64,
                        "tokenizer_ref": "tokenizer",
                        "tokenizer_revision": "tok-rev",
                        "tokenizer_digest": "c" * 64,
                    },
                    "dataset": {
                        "dataset_id": "dataset",
                        "dataset_digest": "d" * 64,
                    },
                    "decision_digest": "e" * 64,
                    "capability_report_digest": "f" * 64,
                    "sft": {"max_steps": 2},
                    "lora": {"rank": 8, "alpha": 16},
                    "blockers": [],
                }
            ],
            "capabilities": [
                {
                    "report_digest": "f" * 64,
                    "integrity": "ready",
                    "disposition": "ready",
                    "backend": "cpu",
                    "dtype_supported": True,
                    "four_bit_supported": False,
                    "blockers": [],
                }
            ],
            "runs": [
                {
                    "run_id": run_id,
                    "state": "completed",
                    "plan_digest": plan_digest,
                    "completed_steps": 2,
                    "train_loss": 0.4,
                    "eval_loss": 0.5,
                    "resumed_from": None,
                    "blockers": [],
                    "checkpoints": [
                        {
                            "checkpoint_id": "checkpoint-00000001",
                            "step": 1,
                            "plan_digest": plan_digest,
                            "lineage_bound": True,
                            "train_loss": 0.6,
                            "eval_loss": 0.7,
                            "artifact_digest": "1" * 64,
                        }
                    ],
                }
            ],
            "summary": {
                "plan_count": 1,
                "authorized_plans": 1,
                "capability_count": 1,
                "run_count": 1,
                "active_runs": 0,
            },
            "backends": [],
            "reference_context": {},
            "later_mutations": {},
        }

    def inspect_doctor(self, backend: str) -> dict[str, object]:
        self.calls.append(("doctor", None, backend, False))
        return {"status": "ok", "backend": backend}

    def inspect_plan(self, plan_digest: str) -> dict[str, object]:
        self.calls.append(("plan", plan_digest, None, False))
        return {"status": "ok", "identifier": plan_digest}

    def preview_run(self, plan_digest: str, backend: str) -> dict[str, object]:
        self.calls.append(("preview", plan_digest, backend, False))
        return {"status": "dry_run", "identifier": plan_digest, "backend": backend}

    def run_training(
        self,
        plan_digest: str,
        backend: str,
        *,
        confirmed: bool = False,
    ) -> dict[str, object]:
        if not confirmed:
            raise RuntimeError("explicit confirmation is required for mutation")
        self.calls.append(("run", plan_digest, backend, confirmed))
        return {"status": "ok", "identifier": plan_digest, "backend": backend}

    def inspect_run(self, run_id: str, backend: str) -> dict[str, object]:
        self.calls.append(("status", run_id, backend, False))
        return {"status": "ok", "identifier": run_id, "backend": backend}

    def cancel_run(
        self,
        run_id: str,
        backend: str,
        *,
        confirmed: bool = False,
    ) -> dict[str, object]:
        if not confirmed:
            raise RuntimeError("explicit confirmation is required for mutation")
        self.calls.append(("cancel", run_id, backend, confirmed))
        return {"status": "ok", "identifier": run_id, "backend": backend}

    def resume_checkpoint(
        self,
        checkpoint_id: str,
        backend: str,
        *,
        confirmed: bool = False,
    ) -> dict[str, object]:
        if not confirmed:
            raise RuntimeError("explicit confirmation is required for mutation")
        self.calls.append(("resume", checkpoint_id, backend, confirmed))
        return {
            "status": "ok",
            "identifier": checkpoint_id,
            "parent_identifier": "a" * 64,
            "backend": backend,
        }


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _wait(page: QWidget) -> None:
    deadline = time.monotonic() + 4.0
    while page._model_lab_training_workers and time.monotonic() < deadline:
        QApplication.processEvents()
        time.sleep(0.01)
    QApplication.processEvents()
    assert page._model_lab_training_workers == []


def test_training_workspace_is_wired_structured_accessible_localized_and_bounded(
    tmp_path: Path,
) -> None:
    _app()
    service = FakeTrainingService(tmp_path)
    window = build_window(
        locale="fr",
        project_root=tmp_path,
        model_lab_training_service=service,
    )
    window.show()
    QApplication.processEvents()

    page = window.findChild(QWidget, "modelLabTrainingPage")
    nav = window.findChild(QListWidget, "mainNavigation")
    assert page is not None and nav is not None
    labels = [nav.item(index).text() for index in range(nav.count())]
    assert "Entraînement" in labels

    plans = window.findChild(QTableWidget, "modelLabTrainingPlansTable")
    capabilities = window.findChild(QTableWidget, "modelLabTrainingCapabilitiesTable")
    runs = window.findChild(QTableWidget, "modelLabTrainingRunsTable")
    checkpoints = window.findChild(QTableWidget, "modelLabTrainingCheckpointsTable")
    assert plans is not None and plans.rowCount() == 1
    assert capabilities is not None and capabilities.rowCount() == 1
    assert runs is not None and runs.rowCount() == 1
    assert checkpoints is not None and checkpoints.rowCount() == 1
    assert plans.item(0, 1).text() == "yes"

    for object_name in (
        "modelLabTrainingPage",
        "modelLabTrainingReferenceNotice",
        "modelLabTrainingBoundaryNotice",
        "modelLabTrainingBackendTruth",
        "modelLabTrainingRefresh",
        "modelLabTrainingBackend",
        "modelLabTrainingDoctor",
        "modelLabTrainingInspectPlan",
        "modelLabTrainingPreviewRun",
        "modelLabTrainingLaunch",
        "modelLabTrainingInspectRun",
        "modelLabTrainingCancel",
        "modelLabTrainingResume",
        "modelLabTrainingConfirm",
        "modelLabTrainingState",
        "modelLabTrainingScroll",
        "modelLabTrainingSummary",
        "modelLabTrainingPlansTable",
        "modelLabTrainingCapabilitiesTable",
        "modelLabTrainingRunsTable",
        "modelLabTrainingCheckpointsTable",
        "modelLabTrainingDiagnostics",
    ):
        widget = window.findChild(QWidget, object_name)
        assert widget is not None, object_name
        assert widget.accessibleName(), object_name
        assert widget.accessibleDescription(), object_name

    forbidden = {
        "modelLabTrainingConvert",
        "modelLabTrainingPromote",
        "modelLabTrainingRollback",
        "modelLabTrainingPublish",
        "modelLabTrainingRawCommand",
        "modelLabTrainingPackageInstall",
    }
    present = {
        child.objectName()
        for child in window.findChildren(QWidget)
        if child.objectName()
    }
    assert forbidden.isdisjoint(present)
    assert service.calls == []
    window.close()


def test_training_preview_apply_cancel_and_resume_use_typed_handlers(tmp_path: Path) -> None:
    _app()
    service = FakeTrainingService(tmp_path)
    window = build_window(
        project_root=tmp_path,
        model_lab_training_service=service,
    )
    window.show()
    QApplication.processEvents()

    page = window.findChild(QWidget, "modelLabTrainingPage")
    backend = window.findChild(QComboBox, "modelLabTrainingBackend")
    preview = window.findChild(QPushButton, "modelLabTrainingPreviewRun")
    launch = window.findChild(QPushButton, "modelLabTrainingLaunch")
    cancel = window.findChild(QPushButton, "modelLabTrainingCancel")
    resume = window.findChild(QPushButton, "modelLabTrainingResume")
    confirm = window.findChild(QCheckBox, "modelLabTrainingConfirm")
    diagnostics = window.findChild(QPlainTextEdit, "modelLabTrainingDiagnostics")
    assert all(
        item is not None
        for item in (page, backend, preview, launch, cancel, resume, confirm, diagnostics)
    )

    preview.click()
    _wait(page)
    assert service.calls[-1][0] == "preview"
    assert '"status": "dry_run"' in diagnostics.toPlainText()

    launch.click()
    _wait(page)
    assert service.calls[-1][0] == "preview"
    assert "confirmation" in diagnostics.toPlainText().lower()

    confirm.setChecked(True)
    launch.click()
    _wait(page)
    assert service.calls[-1][0] == "run"
    assert service.calls[-1][2] == "local"

    cancel.click()
    _wait(page)
    assert service.calls[-1][0] == "cancel"

    backend.setCurrentIndex(backend.findData("kaggle"))
    resume.click()
    _wait(page)
    assert service.calls[-1][0] == "resume"
    assert service.calls[-1][2] == "kaggle"

    window.close()
