from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QLabel,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QWidget,
)

from kodepoia.experience.contracts import (
    ContentRef,
    ExperienceId,
    ExperienceRecord,
    ExperienceState,
    OutcomeLabel,
    PolicyDecision,
    ProvenanceDescriptor,
    SanitizationEvidence,
    SanitizationStatus,
    TrainingAuthorization,
)
from kodepoia.kodestudio.app import build_window
from kodepoia.kodestudio.model_lab_curation import ModelLabCurationService
from kodepoia.tuning.r15_ux import R15UXService, R15WorkflowRequest


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _record() -> ExperienceRecord:
    origin = _digest("ui-origin")
    text = "sanitized-ui-record"
    return ExperienceRecord(
        experience_id=ExperienceId.derive(
            workspace_id="ws-ui",
            source_id="source-ui",
            origin_digest=origin,
        ),
        workspace_id="ws-ui",
        project_id="project-ui",
        task_label="repair",
        domain_label="python",
        state=ExperienceState.SANITIZED,
        outcome=OutcomeLabel.ACCEPTED,
        content=ContentRef(
            workspace_id="ws-ui",
            storage_key="experience/sanitized/project-ui/ui.txt",
            sha256=_digest(text),
            byte_length=len(text.encode("utf-8")),
        ),
        provenance=ProvenanceDescriptor(
            source_type="fixture",
            source_id="source-ui",
            origin_digest=origin,
            project_scope="project-ui",
            license_expression="MIT",
        ),
        authorization=TrainingAuthorization(
            source_scope=PolicyDecision.ALLOW,
            consent=PolicyDecision.ALLOW,
            provenance=PolicyDecision.ALLOW,
            license=PolicyDecision.ALLOW,
            privacy=PolicyDecision.ALLOW,
        ),
        sanitization=SanitizationEvidence(
            status=SanitizationStatus.PASSED,
            sanitizer_digest=_digest("sanitizer"),
        ),
    )


def _service(
    tmp_path: Path,
    calls: list[R15WorkflowRequest],
) -> ModelLabCurationService:
    root = tmp_path / "project"
    record = _record()
    manifest = {
        "schema": "kodepoia.experience.capture",
        "schema_version": 1,
        "record_digest": record.contract_digest(),
        "record": record.to_dict(),
    }
    path = root / ".kodepoia" / "experience" / "record.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest), encoding="utf-8")

    def curate_handler(request: R15WorkflowRequest) -> dict[str, object]:
        calls.append(request)
        return {
            "status": "ok",
            "experience_id": request.identifier,
            "state": "curated",
            "secret": "must-be-redacted",
        }

    def dataset_handler(request: R15WorkflowRequest) -> dict[str, object]:
        calls.append(request)
        return {
            "status": "ok",
            "dataset_id": "ds_" + _digest("ui-dataset"),
            "selection_summary": {
                "selected_records": 1,
                "excluded_by_reason": {},
            },
        }

    r15 = R15UXService(
        root,
        handlers={
            "experience.curate": curate_handler,
            "dataset.build": dataset_handler,
        },
    )
    return ModelLabCurationService(root, r15_service=r15)


def _wait(page: QWidget) -> None:
    deadline = time.monotonic() + 4.0
    while page._model_lab_curation_workers and time.monotonic() < deadline:
        QApplication.processEvents()
        time.sleep(0.01)
    QApplication.processEvents()
    assert page._model_lab_curation_workers == []


def test_curation_workspace_is_wired_structured_accessible_and_localized(
    tmp_path: Path,
) -> None:
    _app()
    calls: list[R15WorkflowRequest] = []
    service = _service(tmp_path, calls)
    window = build_window(
        locale="fr",
        project_root=service.root,
        model_lab_curation_service=service,
    )
    window.show()
    QApplication.processEvents()

    page = window.findChild(QWidget, "modelLabCurationPage")
    assert page is not None
    nav = window.findChild(QListWidget, "mainNavigation")
    assert nav is not None
    labels = [nav.item(index).text() for index in range(nav.count())]
    assert "Curation des données" in labels

    experiences = window.findChild(QTableWidget, "modelLabCurationExperiencesTable")
    evidence = window.findChild(QTableWidget, "modelLabCurationEvidenceTable")
    datasets = window.findChild(QTableWidget, "modelLabCurationDatasetsTable")
    no_raw = window.findChild(QLabel, "modelLabCurationNoRawNotice")
    summary = window.findChild(QLabel, "modelLabCurationSummary")
    assert experiences is not None and experiences.rowCount() == 1
    assert evidence is not None
    assert datasets is not None
    assert no_raw is not None and "Aucun contenu brut" in no_raw.text()
    assert summary is not None and "Curation backend: ready" in summary.text()
    assert experiences.item(0, 1).text() == "sanitized"
    assert experiences.item(0, 4).text() == "MIT"
    assert experiences.item(0, 5).text() == "allow"
    assert experiences.item(0, 7).text() == "passed"

    for object_name in (
        "modelLabCurationPage",
        "modelLabCurationNoRawNotice",
        "modelLabCurationRefresh",
        "modelLabCurationState",
        "modelLabCurationScroll",
        "modelLabCurationSummary",
        "modelLabCurationExperiencesTable",
        "modelLabCurationPreviewExperience",
        "modelLabCurationApplyExperience",
        "modelLabCurationEvidenceTable",
        "modelLabCurationDatasetsTable",
        "modelLabCurationPreviewDataset",
        "modelLabCurationBuildDataset",
        "modelLabCurationInspectDataset",
        "modelLabCurationConfirm",
        "modelLabCurationDiagnostics",
    ):
        widget = window.findChild(QWidget, object_name)
        assert widget is not None, object_name
        assert widget.accessibleName(), object_name
        assert widget.accessibleDescription(), object_name

    forbidden = {
        "modelLabCurationRawPayload",
        "modelLabCurationSecret",
        "modelLabCurationTraining",
        "modelLabCurationPromote",
        "modelLabCurationRollback",
        "modelLabCurationShell",
    }
    present = {
        child.objectName()
        for child in window.findChildren(QWidget)
        if child.objectName()
    }
    assert forbidden.isdisjoint(present)
    assert calls == []
    window.close()


def test_curation_preview_is_non_mutating_and_apply_requires_explicit_confirmation(
    tmp_path: Path,
) -> None:
    _app()
    calls: list[R15WorkflowRequest] = []
    service = _service(tmp_path, calls)
    window = build_window(
        project_root=service.root,
        model_lab_curation_service=service,
    )
    window.show()
    QApplication.processEvents()

    page = window.findChild(QWidget, "modelLabCurationPage")
    experiences = window.findChild(QTableWidget, "modelLabCurationExperiencesTable")
    preview = window.findChild(QPushButton, "modelLabCurationPreviewExperience")
    apply = window.findChild(QPushButton, "modelLabCurationApplyExperience")
    confirm = window.findChild(QCheckBox, "modelLabCurationConfirm")
    diagnostics = window.findChild(QPlainTextEdit, "modelLabCurationDiagnostics")
    state = window.findChild(QLabel, "modelLabCurationState")
    assert page is not None
    assert experiences is not None and preview is not None and apply is not None
    assert confirm is not None and diagnostics is not None and state is not None

    experiences.selectRow(0)
    preview.click()
    _wait(page)
    assert calls == []
    payload = json.loads(diagnostics.toPlainText())
    assert payload["last_action"]["status"] == "dry_run"
    assert payload["last_action"]["would_mutate"] is True

    apply.click()
    _wait(page)
    assert calls == []
    assert "confirmation" in diagnostics.toPlainText().lower()
    assert "blocked" in state.text().lower()

    confirm.setChecked(True)
    apply.click()
    _wait(page)
    assert len(calls) == 1
    assert calls[0].key == "experience.curate"
    rendered = diagnostics.toPlainText()
    assert "must-be-redacted" not in rendered
    assert "<redacted>" in rendered
    window.close()


def test_dataset_build_preview_and_apply_stay_on_typed_r15_backend(tmp_path: Path) -> None:
    _app()
    calls: list[R15WorkflowRequest] = []
    service = _service(tmp_path, calls)
    window = build_window(
        project_root=service.root,
        model_lab_curation_service=service,
    )
    window.show()
    QApplication.processEvents()

    page = window.findChild(QWidget, "modelLabCurationPage")
    preview = window.findChild(QPushButton, "modelLabCurationPreviewDataset")
    build = window.findChild(QPushButton, "modelLabCurationBuildDataset")
    confirm = window.findChild(QCheckBox, "modelLabCurationConfirm")
    diagnostics = window.findChild(QPlainTextEdit, "modelLabCurationDiagnostics")
    assert page is not None and preview is not None and build is not None
    assert confirm is not None and diagnostics is not None

    preview.click()
    _wait(page)
    assert calls == []
    assert '"status": "dry_run"' in diagnostics.toPlainText()

    confirm.setChecked(True)
    build.click()
    _wait(page)
    assert len(calls) == 1
    assert calls[0].key == "dataset.build"
    assert "ds_" in diagnostics.toPlainText()
    window.close()
