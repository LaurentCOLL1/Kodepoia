from __future__ import annotations

from pathlib import Path


def create_project_dialog(parent=None):
    from PySide6.QtWidgets import QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget
    from kodepoia.project.dna import Dimension, Platform, ProjectType
    from kodepoia.project.initializer import ProjectInitializer
    from kodepoia.project.wizard import ProjectWizardState

    class ProjectDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("New Kodepoia Project")
            self.resize(620, 480)
            self.name = QLineEdit()
            self.directory = QLineEdit()
            browse = QPushButton("Browse…")
            browse.clicked.connect(self._browse)
            path_row = QWidget()
            path_layout = QHBoxLayout(path_row)
            path_layout.setContentsMargins(0, 0, 0, 0)
            path_layout.addWidget(self.directory)
            path_layout.addWidget(browse)
            self.project_type = QComboBox()
            for item in ProjectType:
                self.project_type.addItem(item.value, item)
            self.engine = QLineEdit("Godot")
            self.engine_version = QLineEdit("4.7")
            self.dimension = QComboBox()
            for item in Dimension:
                self.dimension.addItem(item.value, item)
            self.platform_checks = {}
            platform_widget = QWidget()
            platform_layout = QVBoxLayout(platform_widget)
            platform_layout.setContentsMargins(0, 0, 0, 0)
            for platform in Platform:
                check = QCheckBox(platform.value)
                check.setChecked(platform is Platform.WINDOWS)
                self.platform_checks[platform] = check
                platform_layout.addWidget(check)
            form = QFormLayout()
            form.addRow("Name", self.name)
            form.addRow("Directory", path_row)
            form.addRow("Type", self.project_type)
            form.addRow("Engine", self.engine)
            form.addRow("Engine version", self.engine_version)
            form.addRow("Dimension", self.dimension)
            form.addRow("Target platforms (required)", platform_widget)
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
            buttons.rejected.connect(self.reject)
            buttons.accepted.connect(self._create)
            layout = QVBoxLayout(self)
            layout.addLayout(form)
            layout.addWidget(buttons)

        def _browse(self):
            selected = QFileDialog.getExistingDirectory(self, "Project directory")
            if selected:
                self.directory.setText(selected)

        def _create(self):
            platforms = [platform for platform, check in self.platform_checks.items() if check.isChecked()]
            if not platforms:
                QMessageBox.warning(self, "Kodepoia", "Select at least one target platform.")
                return
            if not self.name.text().strip() or not self.directory.text().strip():
                QMessageBox.warning(self, "Kodepoia", "Name and directory are required.")
                return
            state = ProjectWizardState(name=self.name.text().strip(), project_type=self.project_type.currentData(), platforms=platforms, engine=self.engine.text().strip() or None, engine_version=self.engine_version.text().strip() or None, dimension=self.dimension.currentData())
            ProjectInitializer().initialize(Path(self.directory.text()), state.build())
            self.accept()

    return ProjectDialog(parent)
