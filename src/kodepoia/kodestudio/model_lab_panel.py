from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from kodepoia.kodestudio.accessibility import mark_accessible
from kodepoia.kodestudio.model_lab import ModelLabInventoryService
from kodepoia.kodestudio.model_lab_localization import ModelLabTranslator


def create_model_lab_page(
    project_root: Path,
    *,
    locale: str = "en",
    service: ModelLabInventoryService | None = None,
    status_bar=None,
):
    from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
    from PySide6.QtWidgets import (
        QAbstractItemView,
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

    inventory_service = service or ModelLabInventoryService.for_project(project_root)
    tr = ModelLabTranslator(locale)

    page = QWidget()
    page.setObjectName("modelLabPage")
    outer = QVBoxLayout(page)
    outer.addWidget(QLabel(f"<h2>{tr.text('title')}</h2>"))
    subtitle = QLabel(tr.text("subtitle"))
    subtitle.setObjectName("modelLabSubtitle")
    subtitle.setWordWrap(True)
    outer.addWidget(subtitle)

    read_only = QLabel(tr.text("read_only"))
    read_only.setObjectName("modelLabReadOnlyNotice")
    read_only.setWordWrap(True)
    read_only.setAccessibleName(tr.text("read_only"))
    outer.addWidget(read_only)

    actions = QHBoxLayout()
    refresh_inventory = QPushButton(tr.text("refresh_inventory"))
    mark_accessible(
        refresh_inventory,
        object_name="modelLabRefreshInventory",
        name=tr.text("refresh_inventory"),
        description=tr.text("refresh_inventory"),
        description_required=True,
    )
    refresh_runtime = QPushButton(tr.text("refresh_runtime"))
    mark_accessible(
        refresh_runtime,
        object_name="modelLabRefreshRuntime",
        name=tr.text("refresh_runtime"),
        description=tr.text("refresh_runtime"),
        description_required=True,
    )
    actions.addWidget(refresh_inventory)
    actions.addWidget(refresh_runtime)
    actions.addStretch(1)
    outer.addLayout(actions)

    state = QLabel(tr.text("state_ready"))
    state.setObjectName("modelLabState")
    state.setAccessibleName(tr.text("state_ready"))
    state.setWordWrap(True)
    outer.addWidget(state)

    scroll = QScrollArea()
    scroll.setObjectName("modelLabScroll")
    scroll.setWidgetResizable(True)
    body = QWidget()
    body_layout = QVBoxLayout(body)

    def table(name: str, headers: list[str], accessible: str) -> QTableWidget:
        widget = QTableWidget(0, len(headers))
        widget.setHorizontalHeaderLabels(headers)
        widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        mark_accessible(
            widget,
            object_name=name,
            name=accessible,
            description=accessible,
            description_required=True,
        )
        widget.setMinimumHeight(125)
        return widget

    stores_group = QGroupBox(tr.text("stores"))
    stores_layout = QVBoxLayout(stores_group)
    stores = table(
        "modelLabStoresTable",
        ["Category", "State", "Files", "Path"],
        tr.text("stores"),
    )
    stores_layout.addWidget(stores)
    body_layout.addWidget(stores_group)

    evidence_group = QGroupBox(tr.text("evidence"))
    evidence_layout = QVBoxLayout(evidence_group)
    evidence = table(
        "modelLabEvidenceTable",
        ["Category", "ID", "State", "Kind", "Digest", "Path"],
        tr.text("evidence"),
    )
    evidence.setMinimumHeight(180)
    evidence_layout.addWidget(evidence)
    body_layout.addWidget(evidence_group)

    registry_group = QGroupBox(tr.text("registry"))
    registry_layout = QVBoxLayout(registry_group)
    registry_state = QLabel()
    registry_state.setObjectName("modelLabRegistryState")
    registry_state.setWordWrap(True)
    registry_layout.addWidget(registry_state)
    registry = table(
        "modelLabRegistryTable",
        ["Version", "State", "Disposition", "Roles", "Preferred", "Digest"],
        tr.text("registry"),
    )
    registry_layout.addWidget(registry)
    body_layout.addWidget(registry_group)

    models_group = QGroupBox(tr.text("models"))
    models_layout = QVBoxLayout(models_group)
    ollama_state = QLabel(tr.text("not_checked"))
    ollama_state.setObjectName("modelLabOllamaState")
    ollama_state.setWordWrap(True)
    models_layout.addWidget(ollama_state)
    models = table(
        "modelLabModelsTable",
        ["Model", "Preferred roles"],
        tr.text("models"),
    )
    models_layout.addWidget(models)
    body_layout.addWidget(models_group)

    capabilities_group = QGroupBox(tr.text("capabilities"))
    capabilities_layout = QVBoxLayout(capabilities_group)
    kaggle_state = QLabel(tr.text("not_checked"))
    kaggle_state.setObjectName("modelLabKaggleState")
    kaggle_state.setWordWrap(True)
    capabilities_layout.addWidget(kaggle_state)
    capabilities = table(
        "modelLabCapabilitiesTable",
        ["Capability", "State", "Detail"],
        tr.text("capabilities"),
    )
    capabilities_layout.addWidget(capabilities)
    body_layout.addWidget(capabilities_group)

    lineage_group = QGroupBox(tr.text("lineage"))
    lineage_layout = QVBoxLayout(lineage_group)
    lineage = table(
        "modelLabLineageTable",
        ["Source", "Digest", "Target", "Target kind"],
        tr.text("lineage"),
    )
    lineage.setMinimumHeight(160)
    lineage_layout.addWidget(lineage)
    body_layout.addWidget(lineage_group)

    diagnostics_group = QGroupBox(tr.text("diagnostics"))
    diagnostics_layout = QVBoxLayout(diagnostics_group)
    diagnostics = QPlainTextEdit()
    diagnostics.setReadOnly(True)
    mark_accessible(
        diagnostics,
        object_name="modelLabDiagnostics",
        name=tr.text("diagnostics"),
        description=tr.text("diagnostics"),
        description_required=True,
    )
    diagnostics.setMaximumBlockCount(5000)
    diagnostics.setMinimumHeight(140)
    diagnostics_layout.addWidget(diagnostics)
    body_layout.addWidget(diagnostics_group)

    body_layout.addStretch(1)
    scroll.setWidget(body)
    outer.addWidget(scroll, 1)

    def set_rows(widget: QTableWidget, rows: list[list[str]]) -> None:
        widget.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                item = QTableWidgetItem(value)
                widget.setItem(row_index, column_index, item)
        widget.resizeColumnsToContents()

    latest_snapshot: dict[str, object] = {}
    latest_runtime: dict[str, object] | None = None

    def render_snapshot(payload: dict[str, object]) -> None:
        nonlocal latest_snapshot
        latest_snapshot = payload

        store_rows: list[list[str]] = []
        for item in payload.get("stores", []):
            if not isinstance(item, dict):
                continue
            store_rows.append(
                [
                    str(item.get("category", "")),
                    str(item.get("state", "")),
                    str(item.get("file_count", 0)),
                    str(item.get("path", "")),
                ]
            )
        set_rows(stores, store_rows)

        evidence_rows: list[list[str]] = []
        for item in payload.get("evidence", []):
            if not isinstance(item, dict):
                continue
            digest = item.get("sha256")
            evidence_rows.append(
                [
                    str(item.get("category", "")),
                    str(item.get("evidence_id", "")),
                    str(item.get("state", "")),
                    str(item.get("kind", "")),
                    "" if digest is None else str(digest),
                    str(item.get("path", "")),
                ]
            )
        set_rows(evidence, evidence_rows)

        registry_payload = payload.get("registry")
        if isinstance(registry_payload, dict):
            registry_state.setText(
                f"{registry_payload.get('state', 'unknown')} — "
                f"{registry_payload.get('path', '')} "
                f"{registry_payload.get('detail', '')}".strip()
            )
            registry_rows: list[list[str]] = []
            for item in registry_payload.get("records", []):
                if not isinstance(item, dict):
                    continue
                registry_rows.append(
                    [
                        str(item.get("version_id", "")),
                        str(item.get("state", "")),
                        str(item.get("disposition", "")),
                        ", ".join(str(value) for value in item.get("roles", [])),
                        str(item.get("preferred_variant", "")),
                        str(item.get("record_digest", "")),
                    ]
                )
            set_rows(registry, registry_rows)

        ollama_payload = payload.get("ollama")
        if isinstance(ollama_payload, dict):
            roles_raw = ollama_payload.get("roles")
            roles = roles_raw if isinstance(roles_raw, dict) else {}
            configured_models = sorted(
                {str(value) for value in roles.values() if str(value).strip()},
                key=str.casefold,
            )
            set_rows(
                models,
                [
                    [
                        model_name,
                        ", ".join(
                            sorted(
                                str(role)
                                for role, chosen in roles.items()
                                if str(chosen) == model_name
                            )
                        ),
                    ]
                    for model_name in configured_models
                ],
            )
            ollama_state.setText(
                f"{ollama_payload.get('state', 'not_checked')} — "
                f"{ollama_payload.get('base_url', '')}".strip()
            )

        capability_rows: list[list[str]] = []
        for item in payload.get("capabilities", []):
            if not isinstance(item, dict):
                continue
            capability_rows.append(
                [
                    str(item.get("capability", "")),
                    str(item.get("state", "")),
                    str(item.get("detail", "")),
                ]
            )
        set_rows(capabilities, capability_rows)

        lineage_rows: list[list[str]] = []
        for item in payload.get("lineage", []):
            if not isinstance(item, dict):
                continue
            lineage_rows.append(
                [
                    str(item.get("source", "")),
                    str(item.get("digest", "")),
                    str(item.get("target", "")),
                    str(item.get("target_kind", "")),
                ]
            )
        set_rows(lineage, lineage_rows)
        render_diagnostics()

    def render_runtime(payload: dict[str, object]) -> None:
        nonlocal latest_runtime
        latest_runtime = payload
        ollama = payload.get("ollama")
        if isinstance(ollama, dict):
            ollama_state.setText(
                f"{ollama.get('state', 'unknown')} — "
                f"{ollama.get('version') or ''} "
                f"{ollama.get('detail') or ''}".strip()
            )
            role_map = ollama.get("roles")
            roles = role_map if isinstance(role_map, dict) else {}
            runtime_models = {
                str(model)
                for model in ollama.get("models", [])
                if str(model).strip()
            }
            configured_models = {
                str(value)
                for value in roles.values()
                if str(value).strip()
            }
            model_rows: list[list[str]] = []
            for model_text in sorted(runtime_models | configured_models, key=str.casefold):
                preferred = sorted(
                    str(role) for role, chosen in roles.items() if str(chosen) == model_text
                )
                suffix = "" if model_text in runtime_models else " (configured; not reported installed)"
                model_rows.append([model_text + suffix, ", ".join(preferred)])
            set_rows(models, model_rows)
        kaggle = payload.get("kaggle")
        if isinstance(kaggle, dict):
            doctor = kaggle.get("doctor")
            doctor_detail = ""
            if isinstance(doctor, dict):
                doctor_detail = str(doctor.get("detail", ""))
            kaggle_state.setText(
                f"Kaggle: {kaggle.get('state', 'unknown')} — "
                f"{doctor_detail or kaggle.get('detail', '')}".strip()
            )
        render_diagnostics()

    def render_diagnostics() -> None:
        payload = {"inventory": latest_snapshot, "runtime": latest_runtime}
        diagnostics.setPlainText(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
        )

    def refresh_inventory_now() -> None:
        try:
            payload = inventory_service.snapshot()
        except Exception as exc:
            message = f"{tr.text('state_error')}: {exc}"
            state.setText(message)
            state.setAccessibleName(message)
            if status_bar is not None:
                status_bar.showMessage(message)
            return
        render_snapshot(dict(payload))
        message = tr.text("state_ready")
        state.setText(message)
        state.setAccessibleName(message)
        if status_bar is not None:
            status_bar.showMessage(message)

    class WorkerSignals(QObject):
        done = Signal(object)
        error = Signal(str)

    class Task(QRunnable):
        def __init__(self, operation: Callable[[], object]) -> None:
            super().__init__()
            self.operation = operation
            self.signals = WorkerSignals()

        def run(self) -> None:
            try:
                value = self.operation()
            except Exception as exc:
                self.signals.error.emit(str(exc))
            else:
                self.signals.done.emit(value)

    pool = QThreadPool.globalInstance()
    workers: list[Task] = []

    def refresh_runtime_now() -> None:
        refresh_runtime.setEnabled(False)
        message = tr.text("state_runtime")
        state.setText(message)
        state.setAccessibleName(message)
        task = Task(inventory_service.runtime_snapshot)
        workers.append(task)

        def finished(value: object) -> None:
            refresh_runtime.setEnabled(True)
            if task in workers:
                workers.remove(task)
            if isinstance(value, dict):
                render_runtime(value)
            message_done = tr.text("state_ready")
            state.setText(message_done)
            state.setAccessibleName(message_done)
            if status_bar is not None:
                status_bar.showMessage(message_done)

        def failed(reason: str) -> None:
            refresh_runtime.setEnabled(True)
            if task in workers:
                workers.remove(task)
            message_failed = f"{tr.text('state_error')}: {reason}"
            state.setText(message_failed)
            state.setAccessibleName(message_failed)
            if status_bar is not None:
                status_bar.showMessage(message_failed)

        task.signals.done.connect(finished)
        task.signals.error.connect(failed)
        pool.start(task)

    refresh_inventory.clicked.connect(refresh_inventory_now)
    refresh_runtime.clicked.connect(refresh_runtime_now)
    refresh_inventory_now()

    page._model_lab_service = inventory_service
    page._model_lab_refresh_inventory = refresh_inventory_now
    page._model_lab_refresh_runtime = refresh_runtime_now
    page._model_lab_workers = workers
    page._model_lab_render_snapshot = render_snapshot
    page._model_lab_render_runtime = render_runtime
    return page


__all__ = ["create_model_lab_page"]
