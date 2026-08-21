from __future__ import annotations

from pathlib import Path
from typing import TypeVar


EnumT = TypeVar("EnumT")


def create_project_dialog(parent=None):
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QFileDialog,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPlainTextEdit,
        QPushButton,
        QSpinBox,
        QTabWidget,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    from kodepoia.product.spec import (
        AcceptanceCriterion,
        ProductDocumentType,
        ProductSpec,
        Requirement,
    )
    from kodepoia.project.dna import (
        ApprovalPolicy,
        DecisionState,
        Dimension,
        PerformanceBudget,
        Platform,
        ProjectType,
    )
    from kodepoia.project.initializer import ProjectInitializer
    from kodepoia.project.wizard import ProjectWizardState

    class ProjectDialog(QDialog):
        TOOL_NAMES = ("ollama", "blender", "comfyui", "research")
        CAPABILITY_NAMES = (
            "procedural_generation",
            "modding",
            "voice",
            "accessibility_first",
        )
        INPUT_NAMES = (
            "keyboard",
            "mouse",
            "gamepad",
            "touch",
            "gyro",
            "accelerometer",
            "motion_controllers",
        )

        def __init__(self, parent=None):
            super().__init__(parent)
            self.setObjectName("kodepoiaProjectWizard")
            self.setWindowTitle("New Kodepoia Project")
            self.resize(900, 720)

            self.tabs = QTabWidget()
            self.tabs.setObjectName("wizardTabs")
            self._build_general_tab()
            self._build_platform_tab()
            self._build_tools_tab()
            self._build_product_tab()

            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
            )
            buttons.rejected.connect(self.reject)
            buttons.accepted.connect(self._create)

            layout = QVBoxLayout(self)
            layout.addWidget(self.tabs)
            layout.addWidget(buttons)

            self.project_type.currentIndexChanged.connect(self._refresh_adaptive)
            for check in self.platform_checks.values():
                check.stateChanged.connect(self._refresh_adaptive)
            self._refresh_adaptive()

        @staticmethod
        def _enum_value(combo: QComboBox, enum_type):
            """Normalize Qt item data into a domain Enum.

            PySide6 may return StrEnum itemData as its string value depending on
            binding/platform details. KodeStudio therefore stores primitive values
            in Qt widgets and explicitly rebuilds the domain enum at the boundary.
            """
            raw = combo.currentData()
            if isinstance(raw, enum_type):
                return raw
            return enum_type(str(raw))

        @staticmethod
        def _add_enum_items(combo: QComboBox, enum_type) -> None:
            for item in enum_type:
                combo.addItem(item.value, item.value)

        @staticmethod
        def _set_enum(combo: QComboBox, value) -> None:
            index = combo.findData(value.value)
            if index >= 0:
                combo.setCurrentIndex(index)

        def _build_general_tab(self) -> None:
            tab = QWidget()
            form = QFormLayout(tab)

            self.name = QLineEdit()
            self.name.setObjectName("projectName")
            self.directory = QLineEdit()
            self.directory.setObjectName("projectDirectory")
            browse = QPushButton("Browse…")
            browse.clicked.connect(self._browse)
            path_row = QWidget()
            path_layout = QHBoxLayout(path_row)
            path_layout.setContentsMargins(0, 0, 0, 0)
            path_layout.addWidget(self.directory)
            path_layout.addWidget(browse)

            self.project_type = QComboBox()
            self.project_type.setObjectName("projectType")
            self._add_enum_items(self.project_type, ProjectType)
            self._set_enum(self.project_type, ProjectType.GAME)

            self.engine = QLineEdit("Godot")
            self.engine.setObjectName("engine")
            self.engine_version = QLineEdit("4.7")
            self.engine_version.setObjectName("engineVersion")
            self.dimension = QComboBox()
            self.dimension.setObjectName("dimension")
            self._add_enum_items(self.dimension, Dimension)
            self._set_enum(self.dimension, Dimension.D3)

            self.genres = QLineEdit()
            self.genres.setPlaceholderText("RPG; simulation; strategy")
            self.genres.setObjectName("genres")
            self.graphics_style = QLineEdit()
            self.graphics_style.setPlaceholderText("realistic, pixel art, isometric…")
            self.graphics_style.setObjectName("graphicsStyle")

            input_box = QGroupBox("Inputs")
            input_layout = QVBoxLayout(input_box)
            self.input_checks = {}
            for name in self.INPUT_NAMES:
                check = QCheckBox(name)
                check.setObjectName(f"input_{name}")
                check.setChecked(name in {"keyboard", "mouse"})
                self.input_checks[name] = check
                input_layout.addWidget(check)

            self.online = self._decision_combo("online")
            self.multiplayer = self._decision_combo("multiplayer")

            form.addRow("Name", self.name)
            form.addRow("Directory", path_row)
            form.addRow("Type", self.project_type)
            form.addRow("Engine", self.engine)
            form.addRow("Engine version", self.engine_version)
            form.addRow("Dimension", self.dimension)
            form.addRow("Genres (; separated)", self.genres)
            form.addRow("Graphics style", self.graphics_style)
            form.addRow(input_box)
            form.addRow("Online", self.online)
            form.addRow("Multiplayer", self.multiplayer)
            self.tabs.addTab(tab, "General")

        def _build_platform_tab(self) -> None:
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.addWidget(
                QLabel("Target platforms are mandatory. Budgets are stored per selected target.")
            )

            platform_box = QGroupBox("Target platforms")
            platform_layout = QHBoxLayout(platform_box)
            self.platform_checks = {}
            for platform in Platform:
                check = QCheckBox(platform.value)
                check.setObjectName(f"platform_{platform.value}")
                check.setChecked(platform is Platform.WINDOWS)
                self.platform_checks[platform] = check
                platform_layout.addWidget(check)
            layout.addWidget(platform_box)

            self.budget_table = QTableWidget(0, 6)
            self.budget_table.setObjectName("performanceBudgets")
            self.budget_table.setHorizontalHeaderLabels(
                ["Platform", "Target FPS", "Min FPS", "VRAM MB", "RAM MB", "Build MB"]
            )
            self.budget_table.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.Stretch
            )
            layout.addWidget(self.budget_table)
            self.tabs.addTab(tab, "Platforms & budgets")

        def _build_tools_tab(self) -> None:
            tab = QWidget()
            layout = QVBoxLayout(tab)

            tool_box = QGroupBox("Local AI / creation tools")
            tool_layout = QVBoxLayout(tool_box)
            self.tool_checks = {}
            for name in self.TOOL_NAMES:
                check = QCheckBox(name)
                check.setObjectName(f"tool_{name}")
                check.setChecked(name == "ollama")
                self.tool_checks[name] = check
                tool_layout.addWidget(check)
            layout.addWidget(tool_box)

            policy_box = QGroupBox("Download / install policy")
            policy_form = QFormLayout(policy_box)
            self.download_policy = self._policy_combo("downloadPolicy")
            self.install_policy = self._policy_combo("installPolicy")
            policy_form.addRow("Downloads", self.download_policy)
            policy_form.addRow("Installs", self.install_policy)
            layout.addWidget(policy_box)

            capability_box = QGroupBox("Feature decisions")
            capability_form = QFormLayout(capability_box)
            self.capability_combos = {}
            for name in self.CAPABILITY_NAMES:
                combo = self._decision_combo(f"capability_{name}")
                self.capability_combos[name] = combo
                capability_form.addRow(name, combo)
            layout.addWidget(capability_box)

            lineage_box = QGroupBox("Lineage")
            lineage_form = QFormLayout(lineage_box)
            self.lineage_parent = QLineEdit()
            self.lineage_parent.setObjectName("lineageParent")
            self.lineage_franchise = QLineEdit()
            self.lineage_franchise.setObjectName("lineageFranchise")
            self.lineage_template = QLineEdit()
            self.lineage_template.setObjectName("lineageTemplate")
            lineage_form.addRow("Parent project", self.lineage_parent)
            lineage_form.addRow("Franchise", self.lineage_franchise)
            lineage_form.addRow("Template", self.lineage_template)
            layout.addWidget(lineage_box)
            layout.addStretch(1)
            self.tabs.addTab(tab, "Features & tools")

        def _build_product_tab(self) -> None:
            tab = QWidget()
            layout = QVBoxLayout(tab)
            form = QFormLayout()

            self.document_type = QComboBox()
            self.document_type.setObjectName("productDocumentType")
            self._add_enum_items(self.document_type, ProductDocumentType)
            self._set_enum(self.document_type, ProductDocumentType.GDD)

            self.vision = QPlainTextEdit()
            self.vision.setObjectName("productVision")
            self.vision.setPlaceholderText("What product/game are we building and why?")
            self.summary = QLineEdit()
            self.goals = QLineEdit()
            self.goals.setPlaceholderText("goal one; goal two")
            self.metrics = QLineEdit()
            self.metrics.setPlaceholderText("60 FPS; zero P0 crashes")
            self.constraints = QLineEdit()
            self.constraints.setPlaceholderText("local-first; Windows-only…")
            self.mvp = QLineEdit()
            self.mvp.setPlaceholderText("MVP capability one; MVP capability two")
            self.out_of_scope = QLineEdit()

            form.addRow("Document", self.document_type)
            form.addRow("Vision (required)", self.vision)
            form.addRow("Summary", self.summary)
            form.addRow("Goals (; separated)", self.goals)
            form.addRow("Success metrics (; separated)", self.metrics)
            form.addRow("Constraints (; separated)", self.constraints)
            form.addRow("MVP (; separated)", self.mvp)
            form.addRow("Out of scope (; separated)", self.out_of_scope)
            layout.addLayout(form)

            layout.addWidget(QLabel("Requirements and acceptance criteria"))
            self.requirements = QTableWidget(0, 5)
            self.requirements.setObjectName("productRequirements")
            self.requirements.setHorizontalHeaderLabels(
                ["ID", "Priority", "Title", "Description", "Acceptance criteria (; separated)"]
            )
            self.requirements.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.Stretch
            )
            layout.addWidget(self.requirements)

            row_buttons = QHBoxLayout()
            add_requirement = QPushButton("Add requirement")
            add_requirement.clicked.connect(self._add_requirement)
            remove_requirement = QPushButton("Remove selected")
            remove_requirement.clicked.connect(self._remove_requirement)
            row_buttons.addWidget(add_requirement)
            row_buttons.addWidget(remove_requirement)
            row_buttons.addStretch(1)
            layout.addLayout(row_buttons)
            self.tabs.addTab(tab, "Product")

        @staticmethod
        def _split_list(text: str) -> list[str]:
            return [item.strip() for item in text.split(";") if item.strip()]

        @classmethod
        def _decision_combo(cls, object_name: str):
            combo = QComboBox()
            combo.setObjectName(object_name)
            cls._add_enum_items(combo, DecisionState)
            cls._set_enum(combo, DecisionState.NO)
            return combo

        @classmethod
        def _policy_combo(cls, object_name: str):
            combo = QComboBox()
            combo.setObjectName(object_name)
            cls._add_enum_items(combo, ApprovalPolicy)
            cls._set_enum(combo, ApprovalPolicy.ASK)
            return combo

        def _browse(self) -> None:
            selected = QFileDialog.getExistingDirectory(self, "Project directory")
            if selected:
                self.directory.setText(selected)

        def _selected_platforms(self) -> list[Platform]:
            return [
                platform
                for platform, check in self.platform_checks.items()
                if check.isChecked()
            ]

        def _current_budget_values(self) -> dict[str, PerformanceBudget]:
            values: dict[str, PerformanceBudget] = {}
            for row in range(self.budget_table.rowCount()):
                platform_item = self.budget_table.item(row, 0)
                if platform_item is None:
                    continue
                widgets = [
                    self.budget_table.cellWidget(row, column)
                    for column in range(1, 6)
                ]
                if any(widget is None for widget in widgets):
                    continue
                numbers = [widget.value() for widget in widgets]
                values[platform_item.text()] = PerformanceBudget(
                    target_fps=numbers[0],
                    min_fps=numbers[1],
                    max_vram_mb=numbers[2] or None,
                    max_ram_mb=numbers[3] or None,
                    max_build_mb=numbers[4] or None,
                )
            return values

        def _refresh_budget_rows(self) -> None:
            previous = self._current_budget_values()
            selected = self._selected_platforms()
            self.budget_table.setRowCount(len(selected))
            for row, platform in enumerate(selected):
                self.budget_table.setItem(row, 0, QTableWidgetItem(platform.value))
                budget = previous.get(platform.value, PerformanceBudget())
                values = [
                    budget.target_fps,
                    budget.min_fps,
                    budget.max_vram_mb or 0,
                    budget.max_ram_mb or 0,
                    budget.max_build_mb or 0,
                ]
                for column, value in enumerate(values, start=1):
                    spin = QSpinBox()
                    spin.setRange(0 if column >= 3 else 1, 1_000_000)
                    spin.setValue(value)
                    if column >= 3:
                        spin.setSpecialValueText("unlimited")
                    self.budget_table.setCellWidget(row, column, spin)

        def _refresh_adaptive(self, *_args: object) -> None:
            project_type = self._enum_value(self.project_type, ProjectType)
            is_game = project_type is ProjectType.GAME
            for widget in (
                self.engine,
                self.engine_version,
                self.dimension,
                self.genres,
                self.graphics_style,
                self.online,
                self.multiplayer,
            ):
                widget.setEnabled(is_game)
            for name in ("keyboard", "mouse", "gamepad"):
                self.input_checks[name].setEnabled(is_game)

            selected = set(self._selected_platforms())
            has_mobile = bool({Platform.ANDROID, Platform.IOS} & selected)
            for name in ("touch", "gyro", "accelerometer"):
                self.input_checks[name].setVisible(is_game and has_mobile)
                if not has_mobile:
                    self.input_checks[name].setChecked(False)
            has_xr = Platform.XR in selected
            self.input_checks["motion_controllers"].setVisible(is_game and has_xr)
            if not has_xr:
                self.input_checks["motion_controllers"].setChecked(False)

            default_doc = ProductDocumentType.GDD if is_game else ProductDocumentType.PRD
            self._set_enum(self.document_type, default_doc)
            self._refresh_budget_rows()

        def _add_requirement(self) -> None:
            row = self.requirements.rowCount()
            self.requirements.insertRow(row)
            self.requirements.setItem(row, 0, QTableWidgetItem(f"REQ-{row + 1:03d}"))
            priority = QComboBox()
            for value in ("P0", "P1", "P2", "P3"):
                priority.addItem(value)
            priority.setCurrentText("P1")
            self.requirements.setCellWidget(row, 1, priority)
            self.requirements.setItem(row, 2, QTableWidgetItem(""))
            self.requirements.setItem(row, 3, QTableWidgetItem(""))
            self.requirements.setItem(row, 4, QTableWidgetItem(""))

        def _remove_requirement(self) -> None:
            rows = sorted(
                {index.row() for index in self.requirements.selectedIndexes()},
                reverse=True,
            )
            for row in rows:
                self.requirements.removeRow(row)

        def _build_requirements(self) -> list[Requirement]:
            result: list[Requirement] = []
            for row in range(self.requirements.rowCount()):
                def text(column: int) -> str:
                    item = self.requirements.item(row, column)
                    return item.text().strip() if item else ""

                req_id = text(0)
                title = text(2)
                description = text(3)
                acceptance_texts = self._split_list(text(4))
                priority_widget = self.requirements.cellWidget(row, 1)
                priority = priority_widget.currentText() if priority_widget else "P1"
                if not req_id or not title:
                    raise ValueError(
                        f"Requirement row {row + 1} needs an ID and title"
                    )
                acceptance = [
                    AcceptanceCriterion(f"{req_id}-AC-{index + 1}", value)
                    for index, value in enumerate(acceptance_texts)
                ]
                result.append(
                    Requirement(
                        req_id,
                        title,
                        description,
                        priority=priority,
                        acceptance=acceptance,
                    )
                )
            return result

        def _create(self) -> None:
            platforms = self._selected_platforms()
            if not platforms:
                QMessageBox.warning(
                    self, "Kodepoia", "Select at least one target platform."
                )
                return
            if not self.name.text().strip() or not self.directory.text().strip():
                QMessageBox.warning(
                    self, "Kodepoia", "Name and directory are required."
                )
                return
            vision = self.vision.toPlainText().strip()
            if not vision:
                QMessageBox.warning(self, "Kodepoia", "Product vision is required.")
                return

            project_type = self._enum_value(self.project_type, ProjectType)
            is_game = project_type is ProjectType.GAME
            dimension = self._enum_value(self.dimension, Dimension) if is_game else None
            online = self._enum_value(self.online, DecisionState) if is_game else DecisionState.NO
            multiplayer = (
                self._enum_value(self.multiplayer, DecisionState)
                if is_game
                else DecisionState.NO
            )
            download_policy = self._enum_value(self.download_policy, ApprovalPolicy)
            install_policy = self._enum_value(self.install_policy, ApprovalPolicy)
            document_type = self._enum_value(self.document_type, ProductDocumentType)
            capabilities = {
                name: self._enum_value(combo, DecisionState)
                for name, combo in self.capability_combos.items()
            }

            inputs = [
                name
                for name, check in self.input_checks.items()
                if is_game and check.isVisible() and check.isChecked()
            ]
            lineage = {
                key: value
                for key, value in {
                    "parent_project": self.lineage_parent.text().strip(),
                    "franchise": self.lineage_franchise.text().strip(),
                    "template": self.lineage_template.text().strip(),
                }.items()
                if value
            }

            try:
                state = ProjectWizardState(
                    name=self.name.text().strip(),
                    project_type=project_type,
                    platforms=platforms,
                    engine=(self.engine.text().strip() or None) if is_game else None,
                    engine_version=(
                        self.engine_version.text().strip() or None
                    ) if is_game else None,
                    dimension=dimension,
                    genres=self._split_list(self.genres.text()) if is_game else [],
                    inputs=inputs,
                    graphics_style=(
                        self.graphics_style.text().strip() or None
                    ) if is_game else None,
                    online=online,
                    multiplayer=multiplayer,
                    performance=self._current_budget_values(),
                    tools={
                        name: check.isChecked()
                        for name, check in self.tool_checks.items()
                    },
                    download_policy=download_policy,
                    install_policy=install_policy,
                    lineage=lineage,
                    capabilities=capabilities,
                )
                dna = state.build()
                product = ProductSpec(
                    schema_version=1,
                    product_name=dna.name,
                    vision=vision,
                    document_type=document_type,
                    summary=self.summary.text().strip(),
                    goals=self._split_list(self.goals.text()),
                    success_metrics=self._split_list(self.metrics.text()),
                    constraints=self._split_list(self.constraints.text()),
                    mvp=self._split_list(self.mvp.text()),
                    requirements=self._build_requirements(),
                    out_of_scope=self._split_list(self.out_of_scope.text()),
                )
                product.validate()
                ProjectInitializer().initialize(Path(self.directory.text()), dna, product)
            except (OSError, ValueError) as exc:
                QMessageBox.critical(self, "Kodepoia", str(exc))
                return
            self.accept()

    return ProjectDialog(parent)
