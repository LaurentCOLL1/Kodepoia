from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from kodepoia.kodestudio.accessibility import mark_accessible
from kodepoia.kodestudio.model_lab_curation import ModelLabCurationService
from kodepoia.kodestudio.model_lab_curation_localization import (
    ModelLabCurationTranslator,
)


def create_model_lab_curation_page(
    project_root: Path,
    *,
    locale: str = "en",
    service: ModelLabCurationService | None = None,
    status_bar=None,
):
    from PySide6.QtCore import QObject, QRunnable, QThreadPool, Qt, Signal
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QCheckBox,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QPlainTextEdit,
        QPushButton,
        QScrollArea,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    curation = service or ModelLabCurationService.for_project(project_root)
    tr = ModelLabCurationTranslator(locale)

    page = QWidget()
    mark_accessible(
        page,
        object_name="modelLabCurationPage",
        name=tr.text("title"),
        description=tr.text("subtitle"),
        description_required=True,
    )
    outer = QVBoxLayout(page)
    outer.addWidget(QLabel(f"<h2>{tr.text('title')}</h2>"))

    subtitle = QLabel(tr.text("subtitle"))
    subtitle.setWordWrap(True)
    outer.addWidget(subtitle)

    no_raw = QLabel(tr.text("no_raw"))
    no_raw.setWordWrap(True)
    mark_accessible(
        no_raw,
        object_name="modelLabCurationNoRawNotice",
        name=tr.text("no_raw"),
        description=tr.text("no_raw"),
        description_required=True,
    )
    outer.addWidget(no_raw)

    toolbar = QHBoxLayout()
    refresh_button = QPushButton(tr.text("refresh"))
    mark_accessible(
        refresh_button,
        object_name="modelLabCurationRefresh",
        name=tr.text("refresh"),
        description=tr.text("refresh"),
        description_required=True,
    )
    toolbar.addWidget(refresh_button)
    toolbar.addStretch(1)
    outer.addLayout(toolbar)

    state = QLabel(tr.text("ready"))
    mark_accessible(
        state,
        object_name="modelLabCurationState",
        name=tr.text("ready"),
        description=tr.text("ready"),
        description_required=True,
    )
    state.setWordWrap(True)
    outer.addWidget(state)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setObjectName("modelLabCurationScroll")
    scroll.setAccessibleName(tr.text("title"))
    scroll.setAccessibleDescription(tr.text("subtitle"))
    body = QWidget()
    body_layout = QVBoxLayout(body)

    summary_group = QGroupBox(tr.text("summary"))
    summary_layout = QVBoxLayout(summary_group)
    summary_label = QLabel()
    summary_label.setWordWrap(True)
    mark_accessible(
        summary_label,
        object_name="modelLabCurationSummary",
        name=tr.text("summary"),
        description=tr.text("summary"),
        description_required=True,
    )
    summary_layout.addWidget(summary_label)
    body_layout.addWidget(summary_group)

    def create_table(name: str, headers: list[str], accessible_name: str) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        mark_accessible(
            table,
            object_name=name,
            name=accessible_name,
            description=accessible_name,
            description_required=True,
        )
        table.setMinimumHeight(170)
        return table

    experiences_group = QGroupBox(tr.text("experiences"))
    experiences_layout = QVBoxLayout(experiences_group)
    experiences = create_table(
        "modelLabCurationExperiencesTable",
        [
            "Experience",
            "State",
            "Source",
            "Project",
            "License",
            "Consent",
            "Privacy",
            "Sanitization",
            "Integrity",
            "Dataset eligibility",
        ],
        tr.text("experiences"),
    )
    experiences_layout.addWidget(experiences)

    experience_actions = QHBoxLayout()
    preview_curation = QPushButton(tr.text("preview_curation"))
    apply_curation = QPushButton(tr.text("apply_curation"))
    for widget, name, text in (
        (
            preview_curation,
            "modelLabCurationPreviewExperience",
            tr.text("preview_curation"),
        ),
        (
            apply_curation,
            "modelLabCurationApplyExperience",
            tr.text("apply_curation"),
        ),
    ):
        mark_accessible(
            widget,
            object_name=name,
            name=text,
            description=text,
            description_required=True,
        )
        experience_actions.addWidget(widget)
    experience_actions.addStretch(1)
    experiences_layout.addLayout(experience_actions)
    body_layout.addWidget(experiences_group)

    evidence_group = QGroupBox(tr.text("evidence"))
    evidence_layout = QVBoxLayout(evidence_group)
    evidence = create_table(
        "modelLabCurationEvidenceTable",
        ["Kind", "State", "Policy digest", "Findings / clusters", "Quarantined", "Path"],
        tr.text("evidence"),
    )
    evidence_layout.addWidget(evidence)
    body_layout.addWidget(evidence_group)

    datasets_group = QGroupBox(tr.text("datasets"))
    datasets_layout = QVBoxLayout(datasets_group)
    datasets = create_table(
        "modelLabCurationDatasetsTable",
        ["Dataset", "Integrity", "Rows", "Groups", "Licenses", "Domains", "Tasks", "Digest"],
        tr.text("datasets"),
    )
    datasets_layout.addWidget(datasets)

    dataset_actions = QHBoxLayout()
    preview_dataset = QPushButton(tr.text("preview_dataset"))
    build_dataset = QPushButton(tr.text("build_dataset"))
    inspect_dataset = QPushButton(tr.text("inspect_dataset"))
    for widget, name, text in (
        (
            preview_dataset,
            "modelLabCurationPreviewDataset",
            tr.text("preview_dataset"),
        ),
        (
            build_dataset,
            "modelLabCurationBuildDataset",
            tr.text("build_dataset"),
        ),
        (
            inspect_dataset,
            "modelLabCurationInspectDataset",
            tr.text("inspect_dataset"),
        ),
    ):
        mark_accessible(
            widget,
            object_name=name,
            name=text,
            description=text,
            description_required=True,
        )
        dataset_actions.addWidget(widget)
    dataset_actions.addStretch(1)
    datasets_layout.addLayout(dataset_actions)
    body_layout.addWidget(datasets_group)

    confirm = QCheckBox(tr.text("confirm"))
    mark_accessible(
        confirm,
        object_name="modelLabCurationConfirm",
        name=tr.text("confirm"),
        description=tr.text("confirm"),
        description_required=True,
    )
    body_layout.addWidget(confirm)

    diagnostics_group = QGroupBox(tr.text("diagnostics"))
    diagnostics_layout = QVBoxLayout(diagnostics_group)
    diagnostics = QPlainTextEdit()
    diagnostics.setReadOnly(True)
    diagnostics.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
    mark_accessible(
        diagnostics,
        object_name="modelLabCurationDiagnostics",
        name=tr.text("diagnostics"),
        description=tr.text("diagnostics"),
        description_required=True,
    )
    diagnostics.setMinimumHeight(150)
    diagnostics_layout.addWidget(diagnostics)
    body_layout.addWidget(diagnostics_group)

    body_layout.addStretch(1)
    scroll.setWidget(body)
    outer.addWidget(scroll, 1)

    snapshot: dict[str, object] = {}
    last_action: dict[str, object] | None = None

    def set_rows(table: QTableWidget, rows: list[list[str]]) -> None:
        table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                table.setItem(row_index, column_index, QTableWidgetItem(value))
        table.resizeColumnsToContents()

    def render_diagnostics() -> None:
        diagnostics.setPlainText(
            json.dumps(
                {
                    "snapshot": snapshot,
                    "last_action": last_action,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )

    def render_snapshot(payload: dict[str, object]) -> None:
        nonlocal snapshot
        snapshot = payload

        summary = payload.get("summary")
        summary_map = summary if isinstance(summary, dict) else {}
        actions = payload.get("actions")
        actions_map = actions if isinstance(actions, dict) else {}
        curate_action = actions_map.get("experience_curate")
        build_action = actions_map.get("dataset_build")
        curate_available = (
            bool(curate_action.get("available"))
            if isinstance(curate_action, dict)
            else False
        )
        build_available = (
            bool(build_action.get("available"))
            if isinstance(build_action, dict)
            else False
        )
        summary_label.setText(
            " | ".join(
                (
                    f"Experiences: {summary_map.get('experience_count', 0)}",
                    f"Curation ready: {summary_map.get('curation_ready', 0)}",
                    f"Dataset eligible: {summary_map.get('dataset_eligible', 0)}",
                    f"Datasets: {summary_map.get('dataset_count', 0)}",
                    f"Curation backend: {'ready' if curate_available else 'unavailable'}",
                    f"Dataset build backend: {'ready' if build_available else 'unavailable'}",
                )
            )
        )

        experience_rows: list[list[str]] = []
        for item in payload.get("experiences", []):
            if not isinstance(item, dict):
                continue
            auth = item.get("authorization")
            auth_map = auth if isinstance(auth, dict) else {}
            sanitization = item.get("sanitization")
            sanitization_map = sanitization if isinstance(sanitization, dict) else {}
            blockers = item.get("dataset_blockers")
            blockers_list = blockers if isinstance(blockers, list) else []
            experience_rows.append(
                [
                    str(item.get("experience_id", "")),
                    str(item.get("state", "")),
                    f"{item.get('source_type', '')}:{item.get('source_id', '')}",
                    str(item.get("project_id", "")),
                    str(item.get("license_expression") or "missing"),
                    str(auth_map.get("consent", "unknown")),
                    str(auth_map.get("privacy", "unknown")),
                    str(sanitization_map.get("status", "not_run")),
                    str(item.get("integrity", "")),
                    "eligible"
                    if bool(item.get("dataset_eligible"))
                    else ", ".join(str(value) for value in blockers_list),
                ]
            )
        set_rows(experiences, experience_rows)

        evidence_rows: list[list[str]] = []
        for item in payload.get("dedup_and_contamination", []):
            if not isinstance(item, dict):
                continue
            count = item.get("finding_count", item.get("cluster_count", 0))
            quarantined = item.get("quarantined_item_ids")
            quarantined_count = len(quarantined) if isinstance(quarantined, list) else 0
            evidence_rows.append(
                [
                    str(item.get("kind", "")),
                    str(item.get("state", "")),
                    str(item.get("policy_digest", "")),
                    str(count),
                    str(quarantined_count),
                    str(item.get("path", "")),
                ]
            )
        set_rows(evidence, evidence_rows)

        dataset_rows: list[list[str]] = []
        for item in payload.get("datasets", []):
            if not isinstance(item, dict):
                continue
            dataset_rows.append(
                [
                    str(item.get("dataset_id", "")),
                    str(item.get("integrity", "")),
                    str(item.get("rows", 0)),
                    str(item.get("selected_groups", "")),
                    ", ".join(str(value) for value in item.get("licenses", [])),
                    ", ".join(str(value) for value in item.get("domains", [])),
                    ", ".join(str(value) for value in item.get("tasks", [])),
                    str(item.get("dataset_digest", "")),
                ]
            )
        set_rows(datasets, dataset_rows)
        render_diagnostics()

    def set_state(message: str) -> None:
        state.setText(message)
        state.setAccessibleName(message)
        state.setAccessibleDescription(message)
        if status_bar is not None:
            status_bar.showMessage(message)

    def refresh_now() -> None:
        try:
            render_snapshot(curation.snapshot())
        except Exception as exc:
            set_state(f"{tr.text('blocked')}: {exc}")
            return
        set_state(tr.text("ready"))

    class WorkerSignals(QObject):
        done = Signal(object)
        failed = Signal(str)

    class Task(QRunnable):
        def __init__(self, operation: Callable[[], object]) -> None:
            super().__init__()
            self.operation = operation
            self.signals = WorkerSignals()

        def run(self) -> None:
            try:
                payload = self.operation()
            except Exception as exc:
                self.signals.failed.emit(str(exc))
            else:
                self.signals.done.emit(payload)

    pool = QThreadPool.globalInstance()
    workers: list[Task] = []
    action_buttons = (
        preview_curation,
        apply_curation,
        preview_dataset,
        build_dataset,
        inspect_dataset,
    )

    def run_action(operation: Callable[[], object], *, refresh_after: bool = False) -> None:
        nonlocal last_action
        for button in action_buttons:
            button.setEnabled(False)
        set_state(tr.text("running"))
        task = Task(operation)
        workers.append(task)

        def finish(payload: object) -> None:
            nonlocal last_action
            if task in workers:
                workers.remove(task)
            for button in action_buttons:
                button.setEnabled(True)
            last_action = payload if isinstance(payload, dict) else {"result": str(payload)}
            if refresh_after:
                refresh_now()
            else:
                render_diagnostics()
                set_state(tr.text("complete"))

        def fail(detail: str) -> None:
            nonlocal last_action
            if task in workers:
                workers.remove(task)
            for button in action_buttons:
                button.setEnabled(True)
            last_action = {
                "schema": ModelLabCurationService.schema,
                "status": "blocked",
                "detail": detail,
            }
            render_diagnostics()
            set_state(f"{tr.text('blocked')}: {detail}")

        task.signals.done.connect(finish)
        task.signals.failed.connect(fail)
        pool.start(task)

    def selected_experience_id() -> str | None:
        row = experiences.currentRow()
        if row < 0:
            return None
        item = experiences.item(row, 0)
        return item.text().strip() if item is not None else None

    def selected_dataset_id() -> str | None:
        row = datasets.currentRow()
        if row < 0:
            return None
        item = datasets.item(row, 0)
        return item.text().strip() if item is not None else None

    def preview_selected_curation() -> None:
        experience_id = selected_experience_id()
        if not experience_id:
            set_state(tr.text("select_experience"))
            return
        run_action(lambda: curation.preview_curation(experience_id))

    def apply_selected_curation() -> None:
        experience_id = selected_experience_id()
        if not experience_id:
            set_state(tr.text("select_experience"))
            return
        run_action(
            lambda: curation.apply_curation(
                experience_id,
                confirmed=confirm.isChecked(),
            ),
            refresh_after=True,
        )

    def preview_build() -> None:
        run_action(curation.preview_dataset_build)

    def apply_build() -> None:
        run_action(
            lambda: curation.apply_dataset_build(confirmed=confirm.isChecked()),
            refresh_after=True,
        )

    def inspect_selected_dataset() -> None:
        dataset_id = selected_dataset_id()
        if not dataset_id:
            set_state(tr.text("select_dataset"))
            return
        run_action(lambda: curation.inspect_dataset(dataset_id))

    refresh_button.clicked.connect(refresh_now)
    preview_curation.clicked.connect(preview_selected_curation)
    apply_curation.clicked.connect(apply_selected_curation)
    preview_dataset.clicked.connect(preview_build)
    build_dataset.clicked.connect(apply_build)
    inspect_dataset.clicked.connect(inspect_selected_dataset)

    refresh_now()
    page._model_lab_curation_service = curation
    page._model_lab_curation_workers = workers
    page._model_lab_curation_refresh = refresh_now
    page._model_lab_curation_render_snapshot = render_snapshot
    return page


__all__ = ["create_model_lab_curation_page"]
