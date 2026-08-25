from __future__ import annotations

from pathlib import Path

from kodepoia.kodestudio.accessibility import mark_accessible


def create_project_dialog(parent=None, *, locale: str | None = None):
    """Enhance the accepted R12 Project Wizard with R13 mobile intent only."""
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDialogButtonBox,
        QFormLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QSpinBox,
        QWidget,
    )

    from kodepoia.kodestudio.r12_project_wizard import (
        create_project_dialog as create_r12_dialog,
    )
    from kodepoia.kodestudio.r13_wizard_localization import R13WizardTranslator
    from kodepoia.mobile.contracts import (
        MobileFormFactor,
        MobilePackageKind,
        MobileSourceKind,
    )
    from kodepoia.mobile.product_intent import apply_mobile_product_intent
    from kodepoia.product.spec import ProductDocumentType, ProductSpec
    from kodepoia.project.dna import (
        ApprovalPolicy,
        DecisionState,
        Dimension,
        MobileNetworkIntent,
        MobileProjectBudget,
        MobileReleaseChannel,
        MobileSigningIntent,
        Platform,
        ProjectDNA,
        ProjectType,
    )
    from kodepoia.project.initializer import ProjectInitializer
    from kodepoia.project.wizard import ProjectWizardState

    resolved_locale = locale or getattr(parent, "_kodepoia_locale", "en")
    tr = R13WizardTranslator(resolved_locale)
    dialog = create_r12_dialog(parent)
    previous_submit = dialog._r12_desktop_submit

    tab = QWidget()
    form = QFormLayout(tab)
    notice = QLabel(tr.text("r13.wizard.intent_only"))
    notice.setWordWrap(True)
    mark_accessible(
        notice,
        object_name="mobileIntentOnlyNotice",
        name=tr.text("r13.wizard.intent_only"),
    )
    form.addRow(notice)

    dialog.mobile_source = QComboBox()
    dialog._add_enum_items(dialog.mobile_source, MobileSourceKind)
    dialog._set_enum(dialog.mobile_source, MobileSourceKind.NATIVE)
    mark_accessible(
        dialog.mobile_source,
        object_name="mobileSourceKind",
        name=tr.text("r13.wizard.source"),
        description="Governed source intent; no generator or build is executed here.",
        description_required=True,
    )

    factors = QWidget()
    factors_layout = __import__("PySide6.QtWidgets", fromlist=["QHBoxLayout"]).QHBoxLayout(factors)
    factors_layout.setContentsMargins(0, 0, 0, 0)
    dialog.mobile_phone = QCheckBox(MobileFormFactor.PHONE.value)
    dialog.mobile_tablet = QCheckBox(MobileFormFactor.TABLET.value)
    dialog.mobile_phone.setChecked(True)
    for widget, name in (
        (dialog.mobile_phone, "Mobile phone form factor"),
        (dialog.mobile_tablet, "Mobile tablet form factor"),
    ):
        mark_accessible(widget, object_name=name.replace(" ", ""), name=name)
        factors_layout.addWidget(widget)

    dialog.android_application_id = QLineEdit()
    dialog.android_application_id.setPlaceholderText("org.example.app")
    mark_accessible(
        dialog.android_application_id,
        object_name="androidApplicationId",
        name=tr.text("r13.wizard.android_id"),
        description="Stable Android application identity. Leave empty to derive a deterministic new-project default.",
        description_required=True,
    )
    dialog.android_min_api = QSpinBox()
    dialog.android_min_api.setRange(1, 1000)
    dialog.android_min_api.setValue(26)
    mark_accessible(dialog.android_min_api, object_name="androidMinApi", name=tr.text("r13.wizard.android_min"))
    dialog.android_target_api = QSpinBox()
    dialog.android_target_api.setRange(1, 1000)
    dialog.android_target_api.setValue(36)
    mark_accessible(dialog.android_target_api, object_name="androidTargetApi", name=tr.text("r13.wizard.android_target"))
    dialog.android_package = QComboBox()
    for value in (MobilePackageKind.AAB, MobilePackageKind.APK):
        dialog.android_package.addItem(value.value, value.value)
    mark_accessible(dialog.android_package, object_name="androidPackageIntent", name="Android package intent")

    dialog.apple_bundle_id = QLineEdit()
    dialog.apple_bundle_id.setPlaceholderText("org.example.app")
    mark_accessible(
        dialog.apple_bundle_id,
        object_name="appleBundleId",
        name=tr.text("r13.wizard.apple_id"),
        description="Stable Apple bundle identity. Leave empty to derive a deterministic new-project default.",
        description_required=True,
    )
    dialog.apple_min_version = QLineEdit("16.0")
    mark_accessible(dialog.apple_min_version, object_name="appleMinVersion", name=tr.text("r13.wizard.apple_min"))
    dialog.apple_target_version = QLineEdit("26.0")
    mark_accessible(dialog.apple_target_version, object_name="appleTargetVersion", name=tr.text("r13.wizard.apple_target"))
    dialog.apple_package = QComboBox()
    for value in (MobilePackageKind.APP, MobilePackageKind.XCARCHIVE, MobilePackageKind.IPA):
        dialog.apple_package.addItem(value.value, value.value)
    mark_accessible(dialog.apple_package, object_name="applePackageIntent", name="Apple package intent")

    def enum_combo(enum_type, default, object_name: str, accessible_name: str) -> QComboBox:
        combo = QComboBox()
        dialog._add_enum_items(combo, enum_type)
        dialog._set_enum(combo, default)
        mark_accessible(combo, object_name=object_name, name=accessible_name)
        return combo

    dialog.mobile_network = enum_combo(
        MobileNetworkIntent,
        MobileNetworkIntent.OFFLINE,
        "mobileNetworkIntent",
        tr.text("r13.wizard.network"),
    )
    dialog.mobile_release = enum_combo(
        MobileReleaseChannel,
        MobileReleaseChannel.DEVELOPMENT,
        "mobileReleaseChannel",
        tr.text("r13.wizard.release"),
    )
    dialog.mobile_signing = enum_combo(
        MobileSigningIntent,
        MobileSigningIntent.UNSIGNED,
        "mobileSigningIntent",
        tr.text("r13.wizard.signing"),
    )
    dialog.mobile_permissions = QLineEdit()
    dialog.mobile_permissions.setPlaceholderText("camera; location")
    mark_accessible(
        dialog.mobile_permissions,
        object_name="mobilePermissions",
        name=tr.text("r13.wizard.permissions"),
        description="Semicolon-separated permission intent names, not raw manifest or entitlement text.",
        description_required=True,
    )
    dialog.mobile_capabilities = QLineEdit()
    dialog.mobile_capabilities.setPlaceholderText("camera; notifications")
    mark_accessible(
        dialog.mobile_capabilities,
        object_name="mobileCapabilities",
        name=tr.text("r13.wizard.capabilities"),
        description="Semicolon-separated governed capability intent names.",
        description_required=True,
    )

    def bounded_spin(object_name: str, accessible_name: str, maximum: int, value: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(1, maximum)
        spin.setValue(value)
        mark_accessible(spin, object_name=object_name, name=accessible_name)
        return spin

    dialog.mobile_max_package_mb = bounded_spin(
        "mobileMaxPackageMb", tr.text("r13.wizard.package_mb"), 20_480, 250
    )
    dialog.mobile_max_build_seconds = bounded_spin(
        "mobileMaxBuildSeconds", tr.text("r13.wizard.build_seconds"), 86_400, 900
    )
    dialog.mobile_max_matrix_runs = bounded_spin(
        "mobileMaxMatrixRuns", tr.text("r13.wizard.matrix_runs"), 1_000, 16
    )

    form.addRow(tr.text("r13.wizard.source"), dialog.mobile_source)
    form.addRow(tr.text("r13.wizard.form_factors"), factors)
    form.addRow(tr.text("r13.wizard.android_id"), dialog.android_application_id)
    form.addRow(tr.text("r13.wizard.android_min"), dialog.android_min_api)
    form.addRow(tr.text("r13.wizard.android_target"), dialog.android_target_api)
    form.addRow("Android package", dialog.android_package)
    form.addRow(tr.text("r13.wizard.apple_id"), dialog.apple_bundle_id)
    form.addRow(tr.text("r13.wizard.apple_min"), dialog.apple_min_version)
    form.addRow(tr.text("r13.wizard.apple_target"), dialog.apple_target_version)
    form.addRow("Apple package", dialog.apple_package)
    form.addRow(tr.text("r13.wizard.network"), dialog.mobile_network)
    form.addRow(tr.text("r13.wizard.release"), dialog.mobile_release)
    form.addRow(tr.text("r13.wizard.signing"), dialog.mobile_signing)
    form.addRow(tr.text("r13.wizard.permissions"), dialog.mobile_permissions)
    form.addRow(tr.text("r13.wizard.capabilities"), dialog.mobile_capabilities)
    form.addRow(tr.text("r13.wizard.package_mb"), dialog.mobile_max_package_mb)
    form.addRow(tr.text("r13.wizard.build_seconds"), dialog.mobile_max_build_seconds)
    form.addRow(tr.text("r13.wizard.matrix_runs"), dialog.mobile_max_matrix_runs)
    mobile_tab_index = dialog.tabs.addTab(tab, tr.text("r13.wizard.tab"))

    dialog._r13_refreshing = False

    def refresh_mobile(*_args: object) -> None:
        if dialog._r13_refreshing:
            return
        dialog._r13_refreshing = True
        try:
            project_type = dialog._enum_value(dialog.project_type, ProjectType)
            mobile_capable = project_type in {ProjectType.GAME, ProjectType.MOBILE_APP}
            selected = set(dialog._selected_platforms())
            has_mobile = bool({Platform.ANDROID, Platform.IOS} & selected)
            dialog.tabs.setTabVisible(mobile_tab_index, mobile_capable and (has_mobile or project_type is ProjectType.MOBILE_APP))

            if project_type is ProjectType.MOBILE_APP:
                for platform, check in dialog.platform_checks.items():
                    allowed = platform in {Platform.ANDROID, Platform.IOS}
                    check.setEnabled(allowed)
                    if not allowed:
                        check.setChecked(False)
                if not any(
                    dialog.platform_checks[item].isChecked()
                    for item in (Platform.ANDROID, Platform.IOS)
                ):
                    dialog.platform_checks[Platform.ANDROID].setChecked(True)
                dialog._set_enum(dialog.mobile_source, MobileSourceKind.NATIVE)
                dialog.mobile_source.setEnabled(False)
            elif project_type is ProjectType.GAME:
                dialog.mobile_source.setEnabled(False)
                dialog._set_enum(dialog.mobile_source, MobileSourceKind.GODOT_EXPORT)
            else:
                dialog.mobile_source.setEnabled(False)
                for platform in (Platform.ANDROID, Platform.IOS):
                    dialog.platform_checks[platform].setEnabled(False)
                    dialog.platform_checks[platform].setChecked(False)

            selected = set(dialog._selected_platforms())
            android = Platform.ANDROID in selected
            apple = Platform.IOS in selected
            for widget in (
                dialog.android_application_id,
                dialog.android_min_api,
                dialog.android_target_api,
                dialog.android_package,
            ):
                widget.setEnabled(android)
            for widget in (
                dialog.apple_bundle_id,
                dialog.apple_min_version,
                dialog.apple_target_version,
                dialog.apple_package,
            ):
                widget.setEnabled(apple)
            if project_type is ProjectType.MOBILE_APP:
                dialog.engine.setEnabled(False)
                dialog.engine_version.setEnabled(False)
        finally:
            dialog._r13_refreshing = False

    dialog.project_type.currentIndexChanged.connect(refresh_mobile)
    for check in dialog.platform_checks.values():
        check.stateChanged.connect(refresh_mobile)

    def create_mobile() -> None:
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

        project_type = dialog._enum_value(dialog.project_type, ProjectType)
        is_game = project_type is ProjectType.GAME
        factors = tuple(
            factor
            for factor, checked in (
                (MobileFormFactor.PHONE, dialog.mobile_phone.isChecked()),
                (MobileFormFactor.TABLET, dialog.mobile_tablet.isChecked()),
            )
            if checked
        )
        packages: list[MobilePackageKind] = []
        if Platform.ANDROID in platforms:
            packages.append(MobilePackageKind(str(dialog.android_package.currentData())))
        if Platform.IOS in platforms:
            packages.append(MobilePackageKind(str(dialog.apple_package.currentData())))
        lineage = {
            key: value
            for key, value in {
                "parent_project": dialog.lineage_parent.text().strip(),
                "franchise": dialog.lineage_franchise.text().strip(),
                "template": dialog.lineage_template.text().strip(),
            }.items()
            if value
        }
        capabilities = {
            name: dialog._enum_value(combo, DecisionState)
            for name, combo in dialog.capability_combos.items()
        }
        inputs = [
            name
            for name, check in dialog.input_checks.items()
            if is_game and check.isVisible() and check.isChecked()
        ]

        try:
            state = ProjectWizardState(
                name=dialog.name.text().strip(),
                project_type=project_type,
                platforms=platforms,
                engine=(dialog.engine.text().strip() or None) if is_game else None,
                engine_version=(dialog.engine_version.text().strip() or None) if is_game else None,
                dimension=dialog._enum_value(dialog.dimension, Dimension) if is_game else None,
                genres=dialog._split_list(dialog.genres.text()) if is_game else [],
                inputs=inputs,
                graphics_style=(dialog.graphics_style.text().strip() or None) if is_game else None,
                online=dialog._enum_value(dialog.online, DecisionState) if is_game else DecisionState.NO,
                multiplayer=dialog._enum_value(dialog.multiplayer, DecisionState) if is_game else DecisionState.NO,
                performance=dialog._current_budget_values(),
                tools={name: check.isChecked() for name, check in dialog.tool_checks.items()},
                download_policy=dialog._enum_value(dialog.download_policy, ApprovalPolicy),
                install_policy=dialog._enum_value(dialog.install_policy, ApprovalPolicy),
                lineage=lineage,
                capabilities=capabilities,
                mobile_source_kind=dialog._enum_value(dialog.mobile_source, MobileSourceKind),
                mobile_form_factors=factors,
                android_application_id=dialog.android_application_id.text().strip() or None,
                android_min_api=dialog.android_min_api.value(),
                android_target_api=dialog.android_target_api.value(),
                apple_bundle_id=dialog.apple_bundle_id.text().strip() or None,
                apple_min_version=dialog.apple_min_version.text().strip(),
                apple_target_version=dialog.apple_target_version.text().strip(),
                mobile_package_kinds=tuple(packages),
                mobile_permissions=tuple(dialog._split_list(dialog.mobile_permissions.text())),
                mobile_requested_capabilities=tuple(dialog._split_list(dialog.mobile_capabilities.text())),
                mobile_network_intent=dialog._enum_value(dialog.mobile_network, MobileNetworkIntent),
                mobile_release_channel=dialog._enum_value(dialog.mobile_release, MobileReleaseChannel),
                mobile_signing_intent=dialog._enum_value(dialog.mobile_signing, MobileSigningIntent),
                mobile_budget=MobileProjectBudget(
                    max_package_mb=dialog.mobile_max_package_mb.value(),
                    max_build_seconds=dialog.mobile_max_build_seconds.value(),
                    max_device_matrix_runs=dialog.mobile_max_matrix_runs.value(),
                ),
            )
            dna = state.build()
            if dna.mobile is None:
                raise ValueError("Mobile Wizard failed to create mobile Project DNA")
            product = ProductSpec(
                schema_version=1,
                product_name=dna.name,
                vision=vision,
                document_type=dialog._enum_value(dialog.document_type, ProductDocumentType),
                summary=dialog.summary.text().strip(),
                goals=dialog._split_list(dialog.goals.text()),
                success_metrics=dialog._split_list(dialog.metrics.text()),
                constraints=dialog._split_list(dialog.constraints.text()),
                mvp=dialog._split_list(dialog.mvp.text()),
                requirements=dialog._build_requirements(),
                out_of_scope=dialog._split_list(dialog.out_of_scope.text()),
            )
            apply_mobile_product_intent(product, dna.mobile, dna.platforms)
            product.validate()
            ProjectInitializer().initialize(Path(dialog.directory.text()), dna, product)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(dialog, "Kodepoia", str(exc))
            return
        dialog.accept()

    def submit() -> None:
        project_type = dialog._enum_value(dialog.project_type, ProjectType)
        selected = set(dialog._selected_platforms())
        if project_type is ProjectType.MOBILE_APP or (
            project_type is ProjectType.GAME
            and bool({Platform.ANDROID, Platform.IOS} & selected)
        ):
            create_mobile()
        else:
            previous_submit()

    buttons = dialog.findChild(QDialogButtonBox, "wizardButtons")
    if buttons is None:
        raise RuntimeError("KodeStudio Project Wizard action box is unavailable")
    try:
        buttons.accepted.disconnect()
    except RuntimeError:
        pass
    buttons.accepted.connect(submit)
    dialog._r13_mobile_submit = submit
    dialog._r13_mobile_refresh = refresh_mobile
    refresh_mobile()
    return dialog
