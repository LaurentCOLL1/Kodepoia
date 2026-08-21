from __future__ import annotations

import sys

from kodepoia.core.kill_switch import GLOBAL_KILL_SWITCH, KillSwitch


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
    window.setWindowTitle("Kodepoia — KodeStudio")
    window.resize(1100, 700)
    window._kodepoia_kill_switch = switch

    nav = QListWidget()
    nav.setObjectName("mainNavigation")
    pages = QStackedWidget()
    pages.setObjectName("mainPages")
    status = QStatusBar()
    status.setObjectName("mainStatus")

    def security_page() -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("<h2>Protected Core</h2>"))
        state = QLabel("Emergency stop: READY")
        state.setObjectName("killSwitchState")
        stop = QPushButton("STOP ALL PROTECTED PROCESSES")
        stop.setObjectName("killSwitchButton")
        reset = QPushButton("Reset emergency stop")
        reset.setObjectName("killSwitchResetButton")

        def trigger() -> None:
            stopped = switch.trigger()
            state.setText(f"Emergency stop: ACTIVE — {stopped} process(es) stopped")
            status.showMessage("KILL SWITCH ACTIVE — protected execution is blocked")

        def reset_switch() -> None:
            try:
                switch.reset()
            except RuntimeError as exc:
                state.setText(str(exc))
                return
            state.setText("Emergency stop: READY")
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
        create.setObjectName("newProjectButton")

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
