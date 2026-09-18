from __future__ import annotations

from kodepoia.intelligence.project_context import (
    ExplainableProjectContextBuilder,
    ProjectContextCandidate,
    ProjectContextOverride,
)
from kodepoia.intelligence.project_retrieval import (
    ProjectRetrievalResult,
    ProjectRetrievalState,
)
from kodepoia.kodestudio.accessibility import mark_accessible


def create_project_context_preview_widget(*, budget_tokens: int = 16_000):
    """Create the V2.2.3 inspectable context-preview surface.

    The widget never creates an embedding provider or performs retrieval itself.
    Load an explicit V2.2.2 result through the exposed widget callback.
    """

    from PySide6.QtWidgets import (
        QComboBox,
        QHBoxLayout,
        QLabel,
        QPlainTextEdit,
        QPushButton,
        QSpinBox,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    widget = QWidget()
    widget.setObjectName("projectContextPreview")
    widget.setAccessibleName("Project Knowledge context preview")
    layout = QVBoxLayout(widget)

    title = QLabel("<h3>Project Knowledge context preview</h3>")
    title.setObjectName("projectContextPreviewTitle")
    layout.addWidget(title)

    state = QLabel(
        "No retrieval result loaded. Context preview never starts hidden network "
        "access or model downloads."
    )
    state.setObjectName("projectContextPreviewState")
    state.setAccessibleName("Project Knowledge context preview state")
    state.setWordWrap(True)
    layout.addWidget(state)

    controls = QHBoxLayout()
    budget_label = QLabel("Token budget")
    budget_label.setObjectName("projectContextBudgetLabel")
    budget = mark_accessible(
        QSpinBox(),
        object_name="projectContextBudget",
        name="Project context token budget",
        description=(
            "Maximum estimated tokens for optional project knowledge. Explicit "
            "mandatory or Include items remain selected and are reported if they "
            "exceed the budget."
        ),
        description_required=True,
    )
    budget.setRange(1, 1_000_000)
    budget.setValue(budget_tokens)
    build_button = mark_accessible(
        QPushButton("Build context preview"),
        object_name="projectContextBuildButton",
        name="Build project context preview",
        description=(
            "Assemble the currently loaded retrieval hits using the visible "
            "Auto, Include, and Exclude overrides."
        ),
        description_required=True,
    )
    build_button.setEnabled(False)
    controls.addWidget(budget_label)
    controls.addWidget(budget)
    controls.addWidget(build_button)
    controls.addStretch(1)
    layout.addLayout(controls)

    table = mark_accessible(
        QTableWidget(0, 7),
        object_name="projectContextCandidatesTable",
        name="Project context candidates",
        description=(
            "Retrieved project knowledge with source, score, trust, freshness, "
            "token cost, override, and selection rationale."
        ),
        description_required=True,
    )
    table.setHorizontalHeaderLabels(
        [
            "Override",
            "Source",
            "Score",
            "Trust",
            "Freshness / version",
            "Tokens",
            "Decision / reason",
        ]
    )
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.horizontalHeader().setStretchLastSection(True)
    layout.addWidget(table)

    summary = QLabel("Selected 0 items.")
    summary.setObjectName("projectContextBudgetSummary")
    summary.setAccessibleName("Project context budget summary")
    summary.setWordWrap(True)
    layout.addWidget(summary)

    preview = mark_accessible(
        QPlainTextEdit(),
        object_name="projectContextRenderedPreview",
        name="Rendered project context",
        description=(
            "Final bounded context with source traceability and preserved "
            "UNTRUSTED_DATA boundaries."
        ),
        description_required=True,
    )
    preview.setReadOnly(True)
    preview.setMaximumHeight(240)
    layout.addWidget(preview)

    widget._project_context_result = None
    widget._project_context_bundle = None
    widget._project_context_override_boxes = {}

    def source_text(candidate: ProjectContextCandidate) -> str:
        rendered = [
            f"{ref.source_kind.value}: {ref.locator}"
            for ref in candidate.source_refs
        ]
        return " | ".join(rendered)

    def freshness_text(candidate: ProjectContextCandidate) -> str:
        fresh = ", ".join(candidate.freshness) or "unknown"
        versions = ", ".join(candidate.versions) or "none"
        return f"{fresh} | version={versions}"

    def load_result(result: ProjectRetrievalResult) -> None:
        widget._project_context_result = result
        widget._project_context_bundle = None
        widget._project_context_override_boxes = {}
        preview.clear()
        table.setRowCount(len(result.hits))

        for row, hit in enumerate(result.hits):
            candidate = ProjectContextCandidate.from_hit(hit)
            override = QComboBox()
            override.setObjectName(f"projectContextOverride_{row}")
            override.setAccessibleName(
                f"Context override for {candidate.content_sha256[:12]}"
            )
            for value in ProjectContextOverride:
                override.addItem(value.value.capitalize(), value.value)
            table.setCellWidget(row, 0, override)
            widget._project_context_override_boxes[candidate.content_sha256] = (
                override
            )
            table.setItem(row, 1, QTableWidgetItem(source_text(candidate)))
            table.setItem(
                row,
                2,
                QTableWidgetItem(f"{candidate.retrieval_score:.6f}"),
            )
            table.setItem(
                row,
                3,
                QTableWidgetItem(", ".join(candidate.trust_classes)),
            )
            table.setItem(
                row,
                4,
                QTableWidgetItem(freshness_text(candidate)),
            )
            table.setItem(
                row,
                5,
                QTableWidgetItem(str(candidate.estimated_tokens)),
            )
            table.setItem(row, 6, QTableWidgetItem("not assembled"))

        if result.state is ProjectRetrievalState.READY and result.hits:
            state.setText(
                f"READY — {len(result.hits)} retrieved candidate(s). "
                "Review source/trust/budget and choose Auto, Include, or Exclude "
                "before final assembly."
            )
            build_button.setEnabled(True)
        else:
            state.setText(
                f"{result.state.value.upper()} — {result.diagnostic}. "
                "No context assembly is available for this retrieval state."
            )
            build_button.setEnabled(False)
        summary.setText(
            f"Retrieved {len(result.hits)} candidate(s); no context assembled yet."
        )

    def build_preview():
        result = widget._project_context_result
        if result is None:
            state.setText("No retrieval result loaded.")
            return None
        overrides = {
            digest: ProjectContextOverride(str(box.currentData()))
            for digest, box in widget._project_context_override_boxes.items()
        }
        bundle = ExplainableProjectContextBuilder(
            budget_tokens=budget.value()
        ).build(
            result,
            overrides=overrides,
        )
        widget._project_context_bundle = bundle
        decisions = {
            item.candidate.content_sha256: (
                f"{item.decision.value} / {item.reason.value}"
            )
            for item in (*bundle.selected, *bundle.omitted)
        }
        for row, hit in enumerate(result.hits):
            table.setItem(
                row,
                6,
                QTableWidgetItem(decisions[hit.content_sha256]),
            )
        preview.setPlainText(bundle.render())
        summary.setText(
            f"Selected {len(bundle.selected)} / {len(result.hits)} item(s) | "
            f"tokens={bundle.selected_tokens}/{bundle.budget_tokens} | "
            f"remaining={bundle.remaining_tokens} | "
            f"over-budget={bundle.over_budget_tokens}"
        )
        state.setText(
            "Context preview assembled. Selection changes relevance/budget only; "
            "project knowledge remains data-only and cannot grant protected authority."
        )
        return bundle

    build_button.clicked.connect(build_preview)
    widget._project_context_load_result = load_result
    widget._project_context_build_preview = build_preview
    return widget
