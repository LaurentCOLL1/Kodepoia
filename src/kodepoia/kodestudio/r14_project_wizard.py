from __future__ import annotations

from pathlib import Path

from kodepoia.backend.contracts import BackendServiceKind
from kodepoia.backend.intent import BackendProjectProfile
from kodepoia.backend.product_intent import apply_backend_product_intent
from kodepoia.kodestudio.accessibility import mark_accessible
from kodepoia.product.spec import ProductSpec
from kodepoia.project.dna import ProjectDNA

_BACKEND_UI_SERVICES = (
    BackendServiceKind.AUTH,
    BackendServiceKind.AUTHORITATIVE_SERVER,
    BackendServiceKind.MATCHMAKING,
    BackendServiceKind.CLOUD_SAVE,
    BackendServiceKind.PROGRESSION,
    BackendServiceKind.CATALOG,
    BackendServiceKind.ENTITLEMENT,
    BackendServiceKind.BILLING,
    BackendServiceKind.REMOTE_CONFIG,
    BackendServiceKind.CONTENT_DELIVERY,
    BackendServiceKind.EVENTS,
)


def _selected_backend_profile(dialog) -> BackendProjectProfile | None:
    if not dialog.backend_enabled.isChecked():
        if any(check.isChecked() for check in dialog.backend_service_checks.values()):
            raise ValueError("Enable backend intent before selecting backend services")
        return None
    services = tuple(
        service
        for service in _BACKEND_UI_SERVICES
        if dialog.backend_service_checks[service].isChecked()
    )
    return BackendProjectProfile(enabled=True, services=services)


def create_project_dialog(parent=None, *, locale: str | None = None):
    """Enhance the accepted R13 wizard with optional R14 backend service intent only."""
    from PySide6.QtWidgets import (
        QCheckBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLabel,
        QMessageBox,
        QWidget,
    )

    from kodepoia.kodestudio.r13_project_wizard import (
        create_project_dialog as create_r13_dialog,
    )

    dialog = create_r13_dialog(parent, locale=locale)
    previous_submit = dialog._r13_mobile_submit

    tab = QWidget()
    form = QFormLayout(tab)
    notice = QLabel(
        "Backend services are optional product intent. This wizard does not provision "
        "providers, store credentials or execute network operations."
    )
    notice.setWordWrap(True)
    mark_accessible(
        notice,
        object_name="backendIntentOnlyNotice",
        name="Backend intent only notice",
    )
    form.addRow(notice)

    dialog.backend_enabled = QCheckBox("Enable backend service intent")
    mark_accessible(
        dialog.backend_enabled,
        object_name="backendIntentEnabled",
        name="Enable backend service intent",
        description="Opt in to provider-neutral backend requirements for this project.",
        description_required=True,
    )
    form.addRow(dialog.backend_enabled)

    dialog.backend_service_checks = {}
    labels = {
        BackendServiceKind.AUTH: "Authentication / identity",
        BackendServiceKind.AUTHORITATIVE_SERVER: "Authoritative state / session",
        BackendServiceKind.MATCHMAKING: "Multiplayer matchmaking",
        BackendServiceKind.CLOUD_SAVE: "Cloud saves",
        BackendServiceKind.PROGRESSION: "Progression",
        BackendServiceKind.CATALOG: "Catalog",
        BackendServiceKind.ENTITLEMENT: "Entitlements",
        BackendServiceKind.BILLING: "Billing",
        BackendServiceKind.REMOTE_CONFIG: "Remote config / flags",
        BackendServiceKind.CONTENT_DELIVERY: "Content delivery",
        BackendServiceKind.EVENTS: "Events",
    }
    for service in _BACKEND_UI_SERVICES:
        check = QCheckBox(labels[service])
        check.setEnabled(False)
        mark_accessible(
            check,
            object_name=f"backendService_{service.value}",
            name=labels[service],
            description=f"Declare provider-neutral {service.value} product intent.",
            description_required=True,
        )
        dialog.backend_service_checks[service] = check
        form.addRow(check)

    dialog.backend_dependency_hint = QLabel("")
    dialog.backend_dependency_hint.setWordWrap(True)
    mark_accessible(
        dialog.backend_dependency_hint,
        object_name="backendDependencyHint",
        name="Backend dependency guidance",
    )
    form.addRow(dialog.backend_dependency_hint)
    backend_tab_index = dialog.tabs.addTab(tab, "Backend")

    def refresh_backend(*_args: object) -> None:
        enabled = dialog.backend_enabled.isChecked()
        for check in dialog.backend_service_checks.values():
            check.setEnabled(enabled)
        if not enabled:
            dialog.backend_dependency_hint.setText("Backend disabled: no runtime intent is generated.")
            return
        selected = {
            service
            for service, check in dialog.backend_service_checks.items()
            if check.isChecked()
        }
        notes: list[str] = []
        if BackendServiceKind.MATCHMAKING in selected:
            notes.append("Matchmaking requires authoritative state/session.")
        if BackendServiceKind.BILLING in selected:
            notes.append("Billing requires catalog and entitlement intents.")
        dialog.backend_dependency_hint.setText(
            " ".join(notes) if notes else "Select only services required by the product."
        )

    dialog.backend_enabled.stateChanged.connect(refresh_backend)
    for check in dialog.backend_service_checks.values():
        check.stateChanged.connect(refresh_backend)

    def submit() -> None:
        try:
            profile = _selected_backend_profile(dialog)
        except ValueError as exc:
            QMessageBox.critical(dialog, "Kodepoia", str(exc))
            return

        previous_submit()
        if dialog.result() != QDialog.DialogCode.Accepted:
            return

        root = Path(dialog.directory.text()).resolve(strict=False)
        dna_path = root / ".kodepoia" / "project.yaml"
        product_path = root / ".kodepoia" / "product" / "product.yaml"
        try:
            dna = ProjectDNA.load(dna_path)
            dna.backend = profile
            dna.save(dna_path)
            product = ProductSpec.load(product_path)
            apply_backend_product_intent(product, profile)
            product.save(product_path)
        except (OSError, ValueError) as exc:
            dialog.reject()
            QMessageBox.critical(dialog, "Kodepoia", str(exc))

    buttons = dialog.findChild(QDialogButtonBox, "wizardButtons")
    if buttons is None:
        raise RuntimeError("KodeStudio Project Wizard action box is unavailable")
    try:
        buttons.accepted.disconnect()
    except RuntimeError:
        pass
    buttons.accepted.connect(submit)
    dialog._r14_backend_submit = submit
    dialog._r14_backend_profile = lambda: _selected_backend_profile(dialog)
    dialog._r14_backend_refresh = refresh_backend
    dialog._r14_backend_tab_index = backend_tab_index
    refresh_backend()
    return dialog
