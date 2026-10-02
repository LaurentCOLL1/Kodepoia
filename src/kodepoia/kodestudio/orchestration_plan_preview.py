from __future__ import annotations

from kodepoia.orchestrator.plan import OrchestrationPlan


def create_orchestration_plan_preview_widget(
    plan: OrchestrationPlan | None,
    *,
    locale: str = "en",
):
    """Create a read-only V2.5.3 orchestration plan preview."""

    from PySide6.QtWidgets import (
        QLabel,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    french = locale.lower().startswith("fr")

    def ui(fr: str, en: str) -> str:
        return fr if french else en

    widget = QWidget()
    widget.setObjectName("orchestrationPlanPreview")
    layout = QVBoxLayout(widget)

    title = QLabel(f"<b>{ui('Aperçu du plan d’orchestration', 'Orchestration plan preview')}</b>")
    layout.addWidget(title)

    state = QLabel()
    state.setObjectName("orchestrationPlanState")
    state.setWordWrap(True)
    layout.addWidget(state)

    table = QTableWidget(0, 7)
    table.setObjectName("orchestrationPlanTable")
    table.setHorizontalHeaderLabels(
        [
            ui("Tâche", "Task"),
            ui("Espace", "Workspace"),
            ui("Route", "Route"),
            ui("Capacité", "Capability"),
            ui("Effet", "Effect"),
            ui("Dépendances", "Dependencies"),
            ui("État", "State"),
        ]
    )
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.horizontalHeader().setStretchLastSection(True)
    layout.addWidget(table)

    if plan is None:
        state.setText(ui("Aucun plan chargé.", "No plan loaded."))
    else:
        preview = plan.preview()
        by_id = {task.task_id: task for task in plan.tasks}
        table.setRowCount(len(preview.topological_order))
        for row, task_id in enumerate(preview.topological_order):
            task = by_id[task_id]
            blocked = task_id in preview.blocked_tasks
            values = (
                task.task_id,
                task.workspace_id[:12],
                task.route.value,
                task.capability,
                task.effect.value,
                ", ".join(task.dependencies) or "none",
                ui("bloquée", "blocked") if blocked else ui("prête", "ready"),
            )
            for column, value in enumerate(values):
                table.setItem(row, column, QTableWidgetItem(value))
        state.setText(
            ui(
                f"plan={plan.plan_id} | digest={plan.digest_sha256[:16]} | "
                f"mutations proposées={len(preview.mutation_proposed_tasks)} | exécution=non autorisée",
                f"plan={plan.plan_id} | digest={plan.digest_sha256[:16]} | "
                f"proposed mutations={len(preview.mutation_proposed_tasks)} | execution=not authorized",
            )
        )

    widget._kodepoia_orchestration_plan = plan
    return widget


__all__ = ["create_orchestration_plan_preview_widget"]
