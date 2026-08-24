from __future__ import annotations

from pathlib import Path

from kodepoia.kodestudio.accessibility import mark_accessible


def create_project_dialog(parent=None):
    """Return the existing KodeStudio Project Wizard enhanced with R12 desktop intent."""
    from PySide6.QtWidgets import (
        QComboBox,
        QDialogButtonBox,
        QFormLayout,
        QMessageBox,
        QWidget,
    )

    from kodepoia.desktop.contracts import (
        DesktopArchitecture,
        DesktopFramework,
        DesktopPackageKind,
    )
    from kodepoia.desktop.product_intent import apply_desktop_product_intent
    from kodepoia.kodestudio.project_wizard import create_project_dialog as create_base_dialog
    from kodepoia.product.spec import ProductSpec
    from kodepoia.project.dna import ApprovalPolicy, DecisionState, Platform, ProjectType
    from kodepoia.project.initializer import ProjectInitializer
    from kodepoia.project.wizard import ProjectWizardState

    dialog = create_base_dialog(parent)
    original_create = dialog._create

    tab = QWidget()
    form = QFormLayout(tab)

    dialog.desktop_framework = QComboBox()
    dialog._add_enum_items(dialog.desktop_framework, DesktopFramework)
    dialog._set_enum(dialog.desktop_framework, DesktopFramework.WINUI3)
    mark_accessible(
        dialog.desktop_framework,
        object_name="desktopFramework",
        name="Desktop framework",
        description="Select the governed desktop application framework intent.",
        description_required=True,
    )

    dialog.desktop_architecture = QComboBox()
    dialog._add_enum_items(dialog.desktop_architecture, DesktopArchitecture)
    dialog._set_enum(dialog.desktop_architecture, DesktopArchitecture.X64)
    mark_accessible(
        dialog.desktop_architecture,
        object_name="desktopArchitecture",
        name="Desktop architecture",
    )

    dialog.desktop_package = QComboBox()
    dialog._add_enum_items(dialog.desktop_package, DesktopPackageKind)
    dialog._set_enum(dialog.desktop_package, DesktopPackageKind.UNPACKAGED)
    mark_accessible(
        dialog.desktop_package,
        object_name="desktopPackageKind",
        name="Desktop package intent",
        description="Select unpackaged, MSIX, MSI or archive intent without building it yet.",
        description_required=True,
    )

    def decision_combo(object_name: str, accessible_name: str) -> QComboBox:
        combo = QComboBox()
        dialog._add_enum_items(combo, DecisionState)
        dialog._set_enum(combo, DecisionState.UNDECIDED)
        mark_accessible(combo, object_name=object_name, name=accessible_name)
        return combo

    dialog.desktop_persistence = decision_combo(
        "desktopPersistence", "Desktop persistence decision"
    )
    dialog.desktop_ipc = decision_combo("desktopIpc", "Desktop IPC decision")
    dialog.desktop_updates = decision_combo(
        "desktopUpdates", "Desktop update decision"
    )

    form.addRow("Framework", dialog.desktop_framework)
    form.addRow("Architecture", dialog.desktop_architecture)
    form.addRow("Package", dialog.desktop_package)
    form.addRow("Persistence", dialog.desktop_persistence)
    form.addRow("Local IPC", dialog.desktop_ipc)
    form.addRow("Updates", dialog.desktop_updates)
    desktop_tab_index = dialog.tabs.addTab(tab, "Desktop")

    dialog._r12_refreshing = False

    def refresh_desktop(*_args: object) -> None:
        if dialog._r12_refreshing:
            return
        dialog._r12_refreshing = True
        try:
            project_type = dialog._enum_value(dialog.project_type, ProjectType)
            is_desktop = project_type is ProjectType.DESKTOP_APP
            dialog.tabs.setTabVisible(desktop_tab_index, is_desktop)
            if not is_desktop:
                for check in dialog.platform_checks.values():
                    check.setEnabled(True)
                return

            framework = dialog._enum_value(dialog.desktop_framework, DesktopFramework)
            desktop_platforms = {Platform.WINDOWS, Platform.LINUX, Platform.MACOS}
            windows_only = framework in {DesktopFramework.WPF, DesktopFramework.WINUI3}
            for platform, check in dialog.platform_checks.items():
                allowed = platform in desktop_platforms and (
                    not windows_only or platform is Platform.WINDOWS
                )
                check.setEnabled(allowed)
                if not allowed:
                    check.setChecked(False)
            if windows_only:
                dialog.platform_checks[Platform.WINDOWS].setChecked(True)
            elif not any(
                dialog.platform_checks[item].isChecked()
                for item in (Platform.WINDOWS, Platform.LINUX, Platform.MACOS)
            ):
                dialog.platform_checks[Platform.WINDOWS].setChecked(True)

            selected = set(dialog._selected_platforms())
            package = dialog._enum_value(dialog.desktop_package, DesktopPackageKind)
            if Platform.WINDOWS not in selected and package in {
                DesktopPackageKind.MSIX,
                DesktopPackageKind.MSI,
            }:
                dialog._set_enum(dialog.desktop_package, DesktopPackageKind.ARCHIVE)
            dialog._refresh_budget_rows()
        finally:
            dialog._r12_refreshing = False

    dialog.project_type.currentIndexChanged.connect(refresh_desktop)
    dialog.desktop_framework.currentIndexChanged.connect(refresh_desktop)
    for check in dialog.platform_checks.values():
        check.stateChanged.connect(refresh_desktop)

    def create_desktop() -> None:
        platforms = dialog._selected_platforms()
        if not platforms:
            QMessageBox.warning(dialog, "Kodepoia", "Select at least one target platform.")
            return
        if not dialog.name.text().strip() or not dialog.directory.text().strip():
            QMessageBox.warning(dialog, "Kodepoia", "Name and directory are required.")
            return
        vision = dialog.vision.toPlainText().strip()
        if not vision:
            QMessageBox.warning(dialog, "Kodepoia", "Product vision is required.")
            return

        download_policy = dialog._enum_value(dialog.download_policy, ApprovalPolicy)
        install_policy = dialog._enum_value(dialog.install_policy, ApprovalPolicy)
        capabilities = {
            name: dialog._enum_value(combo, DecisionState)
            for name, combo in dialog.capability_combos.items()
        }
        lineage = {
            key: value
            for key, value in {
                "parent_project": dialog.lineage_parent.text().strip(),
                "franchise": dialog.lineage_franchise.text().strip(),
                "template": dialog.lineage_template.text().strip(),
            }.items()
            if value
        }
        try:
            state = ProjectWizardState(
                name=dialog.name.text().strip(),
                project_type=ProjectType.DESKTOP_APP,
                platforms=platforms,
                performance=dialog._current_budget_values(),
                tools={name: check.isChecked() for name, check in dialog.tool_checks.items()},
                download_policy=download_policy,
                install_policy=install_policy,
                lineage=lineage,
                capabilities=capabilities,
                desktop_framework=dialog._enum_value(dialog.desktop_framework, DesktopFramework),
                desktop_architecture=dialog._enum_value(
                    dialog.desktop_architecture, DesktopArchitecture
                ),
                desktop_package_kind=dialog._enum_value(
                    dialog.desktop_package, DesktopPackageKind
                ),
                desktop_persistence=dialog._enum_value(
                    dialog.desktop_persistence, DecisionState
                ),
                desktop_ipc=dialog._enum_value(dialog.desktop_ipc, DecisionState),
                desktop_updates=dialog._enum_value(
                    dialog.desktop_updates, DecisionState
                ),
            )
            dna = state.build()
            product = ProductSpec(
                schema_version=1,
                product_name=dna.name,
                vision=vision,
                document_type=dialog._enum_value(
                    dialog.document_type,
                    __import__(
                        "kodepoia.product.spec", fromlist=["ProductDocumentType"]
                    ).ProductDocumentType,
                ),
                summary=dialog.summary.text().strip(),
                goals=dialog._split_list(dialog.goals.text()),
                success_metrics=dialog._split_list(dialog.metrics.text()),
                constraints=dialog._split_list(dialog.constraints.text()),
                mvp=dialog._split_list(dialog.mvp.text()),
                requirements=dialog._build_requirements(),
                out_of_scope=dialog._split_list(dialog.out_of_scope.text()),
            )
            if dna.desktop is None:
                raise ValueError("Desktop Wizard failed to create desktop Project DNA")
            apply_desktop_product_intent(product, dna.desktop, dna.platforms)
            product.validate()
            ProjectInitializer().initialize(Path(dialog.directory.text()), dna, product)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(dialog, "Kodepoia", str(exc))
            return
        dialog.accept()

    def submit() -> None:
        if dialog._enum_value(dialog.project_type, ProjectType) is ProjectType.DESKTOP_APP:
            create_desktop()
        else:
            original_create()

    buttons = dialog.findChild(QDialogButtonBox, "wizardButtons")
    if buttons is None:
        raise RuntimeError("KodeStudio Project Wizard action box is unavailable")
    try:
        buttons.accepted.disconnect()
    except RuntimeError:
        pass
    buttons.accepted.connect(submit)
    dialog._r12_desktop_submit = submit
    dialog._r12_desktop_refresh = refresh_desktop
    refresh_desktop()
    return dialog
