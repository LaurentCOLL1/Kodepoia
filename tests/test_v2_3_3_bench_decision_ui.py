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
    QCheckBox,
    QLabel,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QWidget,
)

from kodepoia.kodestudio.app import build_window
from kodepoia.kodestudio.model_lab_bench import ModelLabBenchDecisionService
from kodepoia.tuning.r15_ux import R15UXService, R15WorkflowRequest


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _fixture_report() -> dict[str, object]:
    config = {
        "num_predict": 128,
        "repeats": 1,
        "role": "baseline",
        "seed_base": 101,
        "temperature": 0.0,
    }
    suite = {
        "suite_id": "ui-suite",
        "tasks": [
            {
                "critical": True,
                "domain": "python",
                "prompt_digest": "1" * 64,
                "protected_holdout_id": None,
                "scorer": {"digest": "2" * 64},
                "task_id": "python-gap",
            }
        ],
        "version": "v1",
    }

    import hashlib

    def digest(value: object) -> str:
        return hashlib.sha256(
            json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(
                "utf-8"
            )
        ).hexdigest()

    payload = {
        "config": config,
        "config_digest": digest(config),
        "model_identities": [
            {
                "model_digest": "3" * 64,
                "model_ref": "base",
                "resolved": True,
                "runtime": "fixture",
                "runtime_version": "1",
            }
        ],
        "outcomes": [
            {
                "category": "model_failure",
                "critical": True,
                "domain": "python",
                "error": None,
                "model_ref": "base",
                "passed": False,
                "repeat": 0,
                "resources": {},
                "response_digest": "4" * 64,
                "scorer_digest": "2" * 64,
                "seed": 101,
                "task_id": "python-gap",
            }
        ],
        "protection_manifest_digest": "5" * 64,
        "schema": "kodepoia.kodebench.v2.report",
        "schema_version": 1,
        "suite": suite,
        "suite_digest": digest(suite),
        "summary": {},
    }
    payload["report_digest"] = digest(payload)
    return payload


def _fixture_decision(report_digest: str) -> dict[str, object]:
    import hashlib

    def digest(value: object) -> str:
        return hashlib.sha256(
            json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(
                "utf-8"
            )
        ).hexdigest()

    payload = {
        "adapter_method": None,
        "base_model": {
            "model_digest": "3" * 64,
            "model_ref": "base",
            "resolved": True,
            "runtime": "fixture",
            "runtime_version": "1",
        },
        "benchmark": {
            "config_digest": "6" * 64,
            "protection_manifest_digest": "5" * 64,
            "report_digest": report_digest,
            "suite_digest": "7" * 64,
        },
        "blockers": ["system_defect:retrieval"],
        "dataset": {
            "dataset_digest": None,
            "dataset_file_digest": None,
            "dataset_id": None,
            "train_examples_by_domain": {},
        },
        "disposition": "fix_system_first",
        "evidence": {
            "backend_capability": "unknown",
            "base_model_license": "allow",
            "benchmark_reproducible": True,
            "budget_status": "unknown",
            "contamination_valid": True,
            "dataset_license": "allow",
            "diagnostics": [
                {
                    "affected_domains": ["python"],
                    "component": "retrieval",
                    "evidence_digest": "8" * 64,
                    "status": "defect",
                },
                {
                    "affected_domains": [],
                    "component": "prompt",
                    "evidence_digest": "9" * 64,
                    "status": "pass",
                },
            ],
            "evidence_digests": {},
            "expected_impact": "unknown",
            "rollback_ready": None,
            "supersedes_decision_digest": None,
        },
        "evidence_digest": "a" * 64,
        "gaps": [
            {
                "categories": ["model_failure"],
                "critical": True,
                "domain": "python",
                "passed": 0,
                "score": 0.0,
                "task_id": "python-gap",
                "total": 1,
            }
        ],
        "policy": {},
        "policy_digest": "b" * 64,
        "reasons": ["A retrieval defect explains the target gap."],
        "schema": "kodepoia.r15.7.gap-decision",
        "schema_version": 1,
        "target_domains": ["python"],
        "targets": [
            {
                "baseline_score": 0.0,
                "critical": True,
                "domain": "python",
                "minimum_score": 1.0,
            }
        ],
    }
    payload["decision_digest"] = digest(payload)
    return payload


def _service(tmp_path: Path, calls: list[R15WorkflowRequest]) -> ModelLabBenchDecisionService:
    root = tmp_path / "project"
    evidence = root / ".kodepoia" / "benchmarks"
    evidence.mkdir(parents=True)
    report = _fixture_report()
    (evidence / "report.json").write_text(json.dumps(report), encoding="utf-8")
    decision = _fixture_decision(str(report["report_digest"]))
    (evidence / "decision.json").write_text(json.dumps(decision), encoding="utf-8")

    def handler(request: R15WorkflowRequest) -> dict[str, object]:
        calls.append(request)
        return {"status": "ok", "identifier": request.identifier}

    r15 = R15UXService(
        root,
        handlers={
            "bench.status": handler,
            "bench.run": handler,
            "gap.diagnose": handler,
        },
    )
    return ModelLabBenchDecisionService(root, r15_service=r15)


def _wait(page: QWidget) -> None:
    deadline = time.monotonic() + 4.0
    while page._model_lab_bench_decision_workers and time.monotonic() < deadline:
        QApplication.processEvents()
        time.sleep(0.01)
    QApplication.processEvents()
    assert page._model_lab_bench_decision_workers == []


def test_bench_decision_workspace_is_wired_accessible_localized_and_training_free(
    tmp_path: Path,
) -> None:
    _app()
    calls: list[R15WorkflowRequest] = []
    service = _service(tmp_path, calls)
    window = build_window(
        locale="fr",
        project_root=service.root,
        model_lab_bench_service=service,
    )
    window.show()
    QApplication.processEvents()

    page = window.findChild(QWidget, "modelLabBenchDecisionPage")
    nav = window.findChild(QListWidget, "mainNavigation")
    assert page is not None and nav is not None
    labels = [nav.item(index).text() for index in range(nav.count())]
    assert "Bench & Décision" in labels

    reports = window.findChild(QTableWidget, "modelLabBenchDecisionReportsTable")
    tasks = window.findChild(QTableWidget, "modelLabBenchDecisionTasksTable")
    decisions = window.findChild(QTableWidget, "modelLabBenchDecisionDecisionsTable")
    diagnosis = window.findChild(QTableWidget, "modelLabBenchDecisionDiagnosisTable")
    targets = window.findChild(QTableWidget, "modelLabBenchDecisionTargetsTable")
    summary = window.findChild(QLabel, "modelLabBenchDecisionSummary")
    reference = window.findChild(QLabel, "modelLabBenchDecisionReferenceNotice")
    no_training = window.findChild(QLabel, "modelLabBenchDecisionNoTrainingNotice")

    assert reports is not None and reports.rowCount() == 1
    assert tasks is not None and tasks.rowCount() == 1
    assert decisions is not None and decisions.rowCount() == 1
    assert diagnosis is not None and diagnosis.rowCount() == 6
    assert targets is not None and targets.rowCount() == 1
    assert summary is not None and "Reports: 1" in summary.text()
    assert reference is not None and "références" in reference.text()
    assert no_training is not None and "ne sont pas exposés" in no_training.text()
    assert decisions.item(0, 1).text() == "FIX_SYSTEM_FIRST"

    for object_name in (
        "modelLabBenchDecisionPage",
        "modelLabBenchDecisionReferenceNotice",
        "modelLabBenchDecisionNoTrainingNotice",
        "modelLabBenchDecisionRefresh",
        "modelLabBenchDecisionInspectStatus",
        "modelLabBenchDecisionPreviewRun",
        "modelLabBenchDecisionRun",
        "modelLabBenchDecisionConfirm",
        "modelLabBenchDecisionState",
        "modelLabBenchDecisionScroll",
        "modelLabBenchDecisionSummary",
        "modelLabBenchDecisionReportsTable",
        "modelLabBenchDecisionTasksTable",
        "modelLabBenchDecisionDecisionsTable",
        "modelLabBenchDecisionInspectDecision",
        "modelLabBenchDecisionDiagnosisTable",
        "modelLabBenchDecisionTargetsTable",
        "modelLabBenchDecisionDiagnosticsJson",
    ):
        widget = window.findChild(QWidget, object_name)
        assert widget is not None, object_name
        assert widget.accessibleName(), object_name
        assert widget.accessibleDescription(), object_name

    forbidden = {
        "modelLabBenchDecisionTraining",
        "modelLabBenchDecisionCancelTraining",
        "modelLabBenchDecisionRecoverTraining",
        "modelLabBenchDecisionConversion",
        "modelLabBenchDecisionPromotion",
        "modelLabBenchDecisionRollback",
        "modelLabBenchDecisionShell",
    }
    present = {
        child.objectName()
        for child in window.findChildren(QWidget)
        if child.objectName()
    }
    assert forbidden.isdisjoint(present)
    assert calls == []
    window.close()


def test_benchmark_preview_and_apply_stay_on_typed_r15_handler(tmp_path: Path) -> None:
    _app()
    calls: list[R15WorkflowRequest] = []
    service = _service(tmp_path, calls)
    window = build_window(
        project_root=service.root,
        model_lab_bench_service=service,
    )
    window.show()
    QApplication.processEvents()

    page = window.findChild(QWidget, "modelLabBenchDecisionPage")
    preview = window.findChild(QPushButton, "modelLabBenchDecisionPreviewRun")
    run = window.findChild(QPushButton, "modelLabBenchDecisionRun")
    confirm = window.findChild(QCheckBox, "modelLabBenchDecisionConfirm")
    raw = window.findChild(QPlainTextEdit, "modelLabBenchDecisionDiagnosticsJson")
    state = window.findChild(QLabel, "modelLabBenchDecisionState")
    assert page is not None and preview is not None and run is not None
    assert confirm is not None and raw is not None and state is not None

    preview.click()
    _wait(page)
    assert calls == []
    assert '"status": "dry_run"' in raw.toPlainText()

    run.click()
    _wait(page)
    assert calls == []
    assert "confirmation" in raw.toPlainText().lower()
    assert "blocked" in state.text().lower()

    confirm.setChecked(True)
    run.click()
    _wait(page)
    assert len(calls) == 1
    assert calls[0].key == "bench.run"
    window.close()
