from __future__ import annotations

import sys

from kodepoia.core.kill_switch import GLOBAL_KILL_SWITCH, KillSwitch
from kodepoia.kodestudio.accessibility import mark_accessible


def build_window(kill_switch: KillSwitch | None = None):
    from PySide6.QtWidgets import (
        QLabel,
        QListWidget,
        QMainWindow,
        QPushButton,
        QSplitter,
        QStackedWidget,
        QStatusBar,
        QVBoxLayout,
        QWidget,
    )

    switch = kill_switch or GLOBAL_KILL_SWITCH
    window = QMainWindow()
    window.setObjectName("kodepoiaMainWindow")
    window.setAccessibleName("Kodepoia KodeStudio")
    window.setAccessibleDescription("Kodepoia local-first development workspace")
    window.setWindowTitle("Kodepoia — KodeStudio")
    window.resize(1100, 700)
    window._kodepoia_kill_switch = switch

    nav = QListWidget()
    mark_accessible(
        nav,
        object_name="mainNavigation",
        name="Main navigation",
        description="Choose the active KodeStudio section with the keyboard or mouse.",
        description_required=True,
    )
    pages = QStackedWidget()
    pages.setObjectName("mainPages")
    pages.setAccessibleName("KodeStudio section content")
    status = QStatusBar()
    status.setObjectName("mainStatus")
    status.setAccessibleName("Application status")

    def security_page() -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("<h2>Protected Core</h2>"))
        state = QLabel("Emergency stop: READY")
        state.setObjectName("killSwitchState")
        state.setAccessibleName("Emergency stop: READY")
        stop = QPushButton("STOP ALL PROTECTED PROCESSES")
        mark_accessible(
            stop,
            object_name="killSwitchButton",
            name="Stop all protected processes",
            description="Emergency stop that terminates protected processes and blocks protected execution.",
            description_required=True,
        )
        reset = QPushButton("Reset emergency stop")
        mark_accessible(
            reset,
            object_name="killSwitchResetButton",
            name="Reset emergency stop",
            description="Reset the emergency stop after protected processes have terminated.",
            description_required=True,
        )

        def trigger() -> None:
            stopped = switch.trigger()
            text = f"Emergency stop: ACTIVE — {stopped} process(es) stopped"
            state.setText(text)
            state.setAccessibleName(text)
            status.showMessage("KILL SWITCH ACTIVE — protected execution is blocked")

        def reset_switch() -> None:
            try:
                switch.reset()
            except RuntimeError as exc:
                state.setText(str(exc))
                state.setAccessibleName(str(exc))
                return
            state.setText("Emergency stop: READY")
            state.setAccessibleName("Emergency stop: READY")
            status.showMessage("Guardian ● Sandbox ● Secrets ● Project DNA")

        stop.clicked.connect(trigger)
        reset.clicked.connect(reset_switch)
        layout.addWidget(state)
        layout.addWidget(stop)
        layout.addWidget(reset)
        layout.addStretch(1)
        return page

    def projects_page() -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("<h2>Projects</h2>"))
        create = QPushButton("New project…")
        mark_accessible(
            create,
            object_name="newProjectButton",
            name="New project",
            description="Open the new Kodepoia project wizard.",
            description_required=True,
        )

        def open_wizard() -> None:
            from kodepoia.kodestudio.project_wizard import create_project_dialog

            create_project_dialog(window).exec()

        create.clicked.connect(open_wizard)
        layout.addWidget(create)
        layout.addStretch(1)
        return page

    for title in ["Chat", "Projects", "Security", "Audit", "Settings"]:
        nav.addItem(title)
        if title == "Projects":
            pages.addWidget(projects_page())
        elif title == "Security":
            pages.addWidget(security_page())
        else:
            pages.addWidget(QLabel(f"<h2>{title}</h2><p>KodeStudio foundation.</p>"))

    nav.currentRowChanged.connect(pages.setCurrentIndex)
    nav.setCurrentRow(0)
    splitter = QSplitter()
    splitter.setObjectName("mainSplitter")
    splitter.setAccessibleName("KodeStudio navigation and content")
    splitter.addWidget(nav)
    splitter.addWidget(pages)
    splitter.setStretchFactor(1, 1)
    window.setCentralWidget(splitter)

    status.showMessage("Guardian ● Sandbox ● Secrets ● Project DNA")
    window.setStatusBar(status)
    return window


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print("KodeStudio requires the optional UI extra: pip install -e .[ui]", file=sys.stderr)
        return 2

    app = QApplication.instance() or QApplication(sys.argv)
    window = build_window()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
