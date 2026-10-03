from __future__ import annotations

import json
from pathlib import Path

from kodepoia.orchestrator.execution import (
    GovernedExecutionCoordinator,
    MutationApproval,
    RecoveryBinding,
)
from kodepoia.orchestrator.handoff import WorkspaceContextHandoff
from kodepoia.orchestrator.history import OrchestrationHistoryStore
from kodepoia.orchestrator.plan import OrchestrationEffect, OrchestrationPlan
from kodepoia.orchestrator.workspaces import (
    WorkspaceRegistry,
    WorkspaceRelationshipKind,
)


def _localized(locale: str, fr: str, en: str) -> str:
    lowered = locale.lower()
    if lowered.startswith("fr"):
        return fr
    if lowered.startswith("qps"):
        return f"⟦{en} !!!⟧"
    return en


def orchestration_nav_text(locale: str = "en") -> str:
    return _localized(locale, "Orchestration", "Orchestration")


def create_orchestration_workspace(
    project_root: Path | str,
    *,
    locale: str = "en",
    registry: WorkspaceRegistry | None = None,
    handoff: WorkspaceContextHandoff | None = None,
    plan: OrchestrationPlan | None = None,
    coordinator: GovernedExecutionCoordinator | None = None,
    history_store: OrchestrationHistoryStore | None = None,
):
    """Create the integrated V2.5.5 KodeStudio orchestration workspace."""

    from PySide6.QtWidgets import (
        QComboBox,
        QHBoxLayout,
        QLabel,
        QMessageBox,
        QPushButton,
        QTabWidget,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    def ui(fr: str, en: str) -> str:
        return _localized(locale, fr, en)
    root = Path(project_root).resolve(strict=False)
    registry = registry or WorkspaceRegistry()
    history_store = history_store or OrchestrationHistoryStore(root)
    approvals: dict[str, MutationApproval] = {}

    page = QWidget()
    page.setObjectName("orchestrationWorkspace")
    page.setAccessibleName(ui("Espace d’orchestration", "Orchestration workspace"))
    page.setAccessibleDescription(
        ui(
            "Coordonne des projets Kodepoia avec approbations et preuves visibles.",
            "Coordinates Kodepoia projects with visible approvals and evidence.",
        )
    )
    layout = QVBoxLayout(page)

    title = QLabel(f"<h2>{ui('Orchestration inter-projets', 'Cross-workspace orchestration')}</h2>")
    title.setObjectName("orchestrationWorkspaceTitle")
    layout.addWidget(title)

    state = QLabel()
    state.setObjectName("orchestrationWorkspaceState")
    state.setAccessibleName(ui("État de l’orchestration", "Orchestration state"))
    state.setWordWrap(True)
    layout.addWidget(state)

    tabs = QTabWidget()
    tabs.setObjectName("orchestrationWorkspaceTabs")
    tabs.setAccessibleName(ui("Détails de l’orchestration", "Orchestration details"))
    layout.addWidget(tabs, 1)

    # Workspace and relationship management.
    workspace_tab = QWidget()
    workspace_layout = QVBoxLayout(workspace_tab)
    workspace_table = QTableWidget(0, 4)
    workspace_table.setObjectName("orchestrationWorkspaceTable")
    workspace_table.setAccessibleName(ui("Espaces sélectionnés", "Selected workspaces"))
    workspace_table.setHorizontalHeaderLabels(
        [
            ui("Projet", "Project"),
            ui("ID", "ID"),
            ui("Portée", "Scope"),
            ui("Racine", "Root"),
        ]
    )
    workspace_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    workspace_table.horizontalHeader().setStretchLastSection(True)
    workspace_layout.addWidget(workspace_table)

    relationship_table = QTableWidget(0, 4)
    relationship_table.setObjectName("orchestrationRelationshipTable")
    relationship_table.setAccessibleName(ui("Relations des espaces", "Workspace relationships"))
    relationship_table.setHorizontalHeaderLabels(
        [
            ui("Source", "Source"),
            ui("Destination", "Destination"),
            ui("Type", "Kind"),
            ui("Libellé", "Label"),
        ]
    )
    relationship_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    relationship_table.horizontalHeader().setStretchLastSection(True)
    workspace_layout.addWidget(relationship_table)

    relation_controls = QHBoxLayout()
    relation_source = QComboBox()
    relation_source.setObjectName("orchestrationRelationSource")
    relation_source.setAccessibleName(ui("Espace source", "Source workspace"))
    relation_destination = QComboBox()
    relation_destination.setObjectName("orchestrationRelationDestination")
    relation_destination.setAccessibleName(ui("Espace destination", "Destination workspace"))
    relation_kind = QComboBox()
    relation_kind.setObjectName("orchestrationRelationKind")
    relation_kind.setAccessibleName(ui("Type de relation", "Relationship kind"))
    for kind in WorkspaceRelationshipKind:
        relation_kind.addItem(kind.value, kind.value)
    add_relation = QPushButton(ui("Ajouter la relation", "Add relationship"))
    add_relation.setObjectName("orchestrationAddRelationshipButton")
    add_relation.setAccessibleName(ui("Ajouter la relation", "Add relationship"))
    relation_controls.addWidget(relation_source)
    relation_controls.addWidget(relation_destination)
    relation_controls.addWidget(relation_kind)
    relation_controls.addWidget(add_relation)
    workspace_layout.addLayout(relation_controls)
    tabs.addTab(workspace_tab, ui("Espaces", "Workspaces"))

    # Handoff inspection reuses the accepted V2.5.2 inspector.
    from kodepoia.kodestudio.workspace_handoff import create_workspace_handoff_inspector

    handoff_widget = create_workspace_handoff_inspector(handoff, locale=locale)
    tabs.addTab(handoff_widget, ui("Transfert", "Handoff"))

    # Plan preview reuses the accepted V2.5.3 preview.
    from kodepoia.kodestudio.orchestration_plan_preview import (
        create_orchestration_plan_preview_widget,
    )

    plan_widget = create_orchestration_plan_preview_widget(plan, locale=locale)
    tabs.addTab(plan_widget, ui("Plan", "Plan"))

    # Governed execution controls are a UI facade over V2.5.4.
    operations_tab = QWidget()
    operations_layout = QVBoxLayout(operations_tab)
    task_selector = QComboBox()
    task_selector.setObjectName("orchestrationTaskSelector")
    task_selector.setAccessibleName(ui("Tâche sélectionnée", "Selected task"))
    if plan is not None:
        for task in plan.tasks:
            task_selector.addItem(f"{task.task_id} — {task.effect.value}", task.task_id)
    operations_layout.addWidget(task_selector)

    buttons = QHBoxLayout()
    approve = QPushButton(ui("Approuver la mutation…", "Approve mutation…"))
    approve.setObjectName("orchestrationApproveButton")
    approve.setAccessibleName(ui("Approuver la mutation sélectionnée", "Approve selected mutation"))
    execute = QPushButton(ui("Exécuter la tâche", "Run task"))
    execute.setObjectName("orchestrationExecuteButton")
    execute.setAccessibleName(ui("Exécuter la tâche sélectionnée", "Run selected task"))
    cancel = QPushButton(ui("Annuler le plan", "Cancel plan"))
    cancel.setObjectName("orchestrationCancelButton")
    cancel.setAccessibleName(ui("Annuler le plan d’orchestration", "Cancel orchestration plan"))
    recover = QPushButton(ui("Récupérer la tâche", "Recover task"))
    recover.setObjectName("orchestrationRecoverButton")
    recover.setAccessibleName(ui("Récupérer la tâche sélectionnée", "Recover selected task"))
    buttons.addWidget(approve)
    buttons.addWidget(execute)
    buttons.addWidget(cancel)
    buttons.addWidget(recover)
    operations_layout.addLayout(buttons)

    operation_state = QLabel()
    operation_state.setObjectName("orchestrationOperationState")
    operation_state.setAccessibleName(ui("État de la tâche", "Task state"))
    operation_state.setWordWrap(True)
    operations_layout.addWidget(operation_state)
    tabs.addTab(operations_tab, ui("Opérations", "Operations"))

    # Persistent operational timeline.
    history_tab = QWidget()
    history_layout = QVBoxLayout(history_tab)
    history_table = QTableWidget(0, 6)
    history_table.setObjectName("orchestrationHistoryTable")
    history_table.setAccessibleName(ui("Historique opérationnel", "Operational history"))
    history_table.setHorizontalHeaderLabels(
        [
            "#",
            ui("Événement", "Event"),
            ui("Tâche", "Task"),
            ui("État", "State"),
            ui("Preuve", "Evidence"),
            ui("Détail", "Detail"),
        ]
    )
    history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    history_table.horizontalHeader().setStretchLastSection(True)
    history_layout.addWidget(history_table)
    tabs.addTab(history_tab, ui("Historique", "History"))

    def selected_task():
        if plan is None:
            return None
        task_id = str(task_selector.currentData() or "")
        return next((item for item in plan.tasks if item.task_id == task_id), None)

    def refresh_workspaces() -> None:
        workspaces = registry.workspaces()
        workspace_table.setRowCount(len(workspaces))
        relation_source.clear()
        relation_destination.clear()
        for row, workspace in enumerate(workspaces):
            values = (
                workspace.project_name,
                workspace.workspace_id[:16],
                workspace.project_scope,
                workspace.canonical_root,
            )
            for column, value in enumerate(values):
                workspace_table.setItem(row, column, QTableWidgetItem(value))
            label = f"{workspace.project_name} — {workspace.workspace_id[:12]}"
            relation_source.addItem(label, workspace.workspace_id)
            relation_destination.addItem(label, workspace.workspace_id)

        relationships = registry.relationships()
        relationship_table.setRowCount(len(relationships))
        for row, relation in enumerate(relationships):
            values = (
                relation.source_workspace_id[:16],
                relation.destination_workspace_id[:16],
                relation.kind.value,
                relation.label,
            )
            for column, value in enumerate(values):
                relationship_table.setItem(row, column, QTableWidgetItem(value))

    history_valid = True

    def refresh_history() -> bool:
        nonlocal history_valid
        try:
            records = history_store.records()
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            history_valid = False
            state.setText(ui(f"Historique invalide : {exc}", f"Invalid history: {exc}"))
            history_table.setRowCount(0)
            for control in (approve, execute, cancel, recover):
                control.setEnabled(False)
            return False
        history_valid = True
        history_table.setRowCount(len(records))
        for row, record in enumerate(records):
            values = (
                str(record.sequence),
                record.event,
                record.task_id or "—",
                record.state or "—",
                record.evidence_digest_sha256[:16] if record.evidence_digest_sha256 else "—",
                record.detail,
            )
            for column, value in enumerate(values):
                history_table.setItem(row, column, QTableWidgetItem(value))
        return True

    def add_relationship() -> None:
        source = str(relation_source.currentData() or "")
        destination = str(relation_destination.currentData() or "")
        kind_value = str(relation_kind.currentData() or "")
        try:
            registry.add_relationship(
                source,
                destination,
                WorkspaceRelationshipKind(kind_value),
            )
        except (KeyError, ValueError) as exc:
            operation_state.setText(str(exc))
            return
        refresh_workspaces()

    def approve_task() -> None:
        task = selected_task()
        if plan is None or task is None:
            operation_state.setText(ui("Aucune tâche sélectionnée.", "No task selected."))
            return
        if task.effect is not OrchestrationEffect.MUTATION_PROPOSED:
            operation_state.setText(
                ui("Cette tâche ne nécessite pas d’approbation de mutation.", "This task does not require mutation approval.")
            )
            return
        answer = QMessageBox.question(
            page,
            ui("Confirmer la mutation", "Confirm mutation"),
            ui(
                f"Approuver explicitement la mutation proposée par la tâche « {task.task_id} » ?",
                f"Explicitly approve the mutation proposed by task “{task.task_id}”?",
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        approval = MutationApproval.for_task(plan, task)
        approvals[task.task_id] = approval
        history_store.append(
            event="mutation_approved",
            plan_digest_sha256=plan.digest_sha256,
            task_id=task.task_id,
            task_digest_sha256=task.digest_sha256,
            workspace_id=task.workspace_id,
            detail=approval.digest_sha256,
        )
        operation_state.setText(ui("Mutation approuvée pour cette tâche uniquement.", "Mutation approved for this task only."))
        refresh_history()

    def execute_task() -> None:
        task = selected_task()
        if plan is None or task is None or coordinator is None:
            operation_state.setText(ui("Exécution indisponible.", "Execution unavailable."))
            return
        evidence = coordinator.execute(
            plan,
            task.task_id,
            approval=approvals.get(task.task_id),
        )
        history_store.append(
            event="task_execution",
            plan_digest_sha256=plan.digest_sha256,
            task_id=task.task_id,
            task_digest_sha256=task.digest_sha256,
            workspace_id=task.workspace_id,
            state=evidence.state.value,
            evidence_digest_sha256=evidence.digest_sha256,
            detail=evidence.error_type,
        )
        operation_state.setText(
            ui(f"État : {evidence.state.value}", f"State: {evidence.state.value}")
        )
        refresh_history()

    def cancel_plan() -> None:
        if plan is None or coordinator is None:
            operation_state.setText(ui("Annulation indisponible.", "Cancellation unavailable."))
            return
        stopped = coordinator.cancel_plan(plan)
        history_store.append(
            event="plan_cancelled",
            plan_digest_sha256=plan.digest_sha256,
            state="cancelled",
            detail=str(stopped),
        )
        operation_state.setText(
            ui(f"Plan annulé ; {stopped} processus protégé(s) arrêté(s).", f"Plan cancelled; {stopped} protected process(es) stopped.")
        )
        refresh_history()

    def recover_task() -> None:
        task = selected_task()
        if plan is None or task is None or coordinator is None:
            operation_state.setText(ui("Récupération indisponible.", "Recovery unavailable."))
            return
        binding = RecoveryBinding.for_task(plan, task)
        try:
            evidence = coordinator.recover(
                plan,
                task.task_id,
                binding,
                approval=approvals.get(task.task_id),
            )
        except (KeyError, ValueError) as exc:
            operation_state.setText(str(exc))
            return
        history_store.append(
            event="task_recovery",
            plan_digest_sha256=plan.digest_sha256,
            task_id=task.task_id,
            task_digest_sha256=task.digest_sha256,
            workspace_id=task.workspace_id,
            state=evidence.state.value,
            evidence_digest_sha256=evidence.digest_sha256,
        )
        operation_state.setText(
            ui(f"Recovery : {evidence.state.value}", f"Recovery: {evidence.state.value}")
        )
        refresh_history()

    add_relation.clicked.connect(add_relationship)
    approve.clicked.connect(approve_task)
    execute.clicked.connect(execute_task)
    cancel.clicked.connect(cancel_plan)
    recover.clicked.connect(recover_task)

    refresh_workspaces()
    history_ok = refresh_history()

    if not history_ok:
        pass
    elif plan is None and handoff is None:
        state.setText(
            ui(
                "Aucun plan ni transfert chargé. Les espaces et l’historique restent consultables.",
                "No plan or handoff loaded. Workspaces and history remain available.",
            )
        )
    elif coordinator is None:
        state.setText(
            ui(
                "Plan consultable ; exécution indisponible tant qu’aucun coordinator gouverné n’est fourni.",
                "Plan is inspectable; execution is unavailable until a governed coordinator is provided.",
            )
        )
    else:
        state.setText(ui("Orchestration prête.", "Orchestration ready."))

    if plan is not None:
        try:
            existing = history_store.records()
        except (OSError, ValueError, json.JSONDecodeError):
            existing = ()
        if not any(item.event == "plan_loaded" and item.plan_digest_sha256 == plan.digest_sha256 for item in existing):
            history_store.append(event="plan_loaded", plan_digest_sha256=plan.digest_sha256)
            refresh_history()

    page._kodepoia_registry = registry
    page._kodepoia_handoff = handoff
    page._kodepoia_plan = plan
    page._kodepoia_coordinator = coordinator
    page._kodepoia_history_store = history_store
    page._kodepoia_approvals = approvals
    page._kodepoia_refresh_history = refresh_history
    return page


__all__ = ["create_orchestration_workspace", "orchestration_nav_text"]
