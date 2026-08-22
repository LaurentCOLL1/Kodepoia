from __future__ import annotations

import sys

from kodepoia.core.kill_switch import GLOBAL_KILL_SWITCH, KillSwitch
from kodepoia.kodestudio.accessibility import mark_accessible
from kodepoia.kodestudio.localization import KodeStudioTranslator


def build_window(kill_switch: KillSwitch | None = None, *, locale: str = "en"):
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
    tr = KodeStudioTranslator(locale)
    window = QMainWindow()
    window.setObjectName("kodepoiaMainWindow")
    window.setAccessibleName("Kodepoia KodeStudio")
    window.setAccessibleDescription("Kodepoia local-first development workspace")
    window.setWindowTitle(tr.text("app.window.title"))
    window.resize(1100, 700)
    window._kodepoia_kill_switch = switch
    window._kodepoia_locale = locale

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
        layout.addWidget(QLabel(f"<h2>{tr.text('app.security.title')}</h2>"))
        state = QLabel(tr.text("app.security.ready"))
        state.setObjectName("killSwitchState")
        state.setAccessibleName(tr.text("app.security.ready"))
        stop = QPushButton(tr.text("app.security.stop"))
        mark_accessible(
            stop,
            object_name="killSwitchButton",
            name=tr.text("app.security.stop"),
            description="Emergency stop that terminates protected processes and blocks protected execution.",
            description_required=True,
        )
        reset = QPushButton(tr.text("app.security.reset"))
        mark_accessible(
            reset,
            object_name="killSwitchResetButton",
            name=tr.text("app.security.reset"),
            description="Reset the emergency stop after protected processes have terminated.",
            description_required=True,
        )

        def trigger() -> None:
            stopped = switch.trigger()
            text = tr.text("app.security.active", count=stopped)
            state.setText(text)
            state.setAccessibleName(text)
            status.showMessage(tr.text("app.status.blocked"))

        def reset_switch() -> None:
            try:
                switch.reset()
            except RuntimeError as exc:
                state.setText(str(exc))
                state.setAccessibleName(str(exc))
                return
            ready = tr.text("app.security.ready")
            state.setText(ready)
            state.setAccessibleName(ready)
            status.showMessage(tr.text("app.status.ready"))

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
        layout.addWidget(QLabel(f"<h2>{tr.text('app.projects.title')}</h2>"))
        create = QPushButton(tr.text("app.projects.new"))
        mark_accessible(
            create,
            object_name="newProjectButton",
            name=tr.text("app.projects.new").rstrip("…"),
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

    sections = (
        ("app.nav.chat", None),
        ("app.nav.projects", projects_page),
        ("app.nav.security", security_page),
        ("app.nav.audit", None),
        ("app.nav.settings", None),
    )
    for message_id, factory in sections:
        title = tr.text(message_id)
        nav.addItem(title)
        if factory is not None:
            pages.addWidget(factory())
        else:
            pages.addWidget(QLabel(f"<h2>{title}</h2><p>{tr.text('app.page.foundation')}</p>"))

    nav.setMinimumWidth(max(nav.sizeHintForColumn(0) + 24, 160))
    nav.currentRowChanged.connect(pages.setCurrentIndex)
    nav.setCurrentRow(0)
    splitter = QSplitter()
    splitter.setObjectName("mainSplitter")
    splitter.setAccessibleName("KodeStudio navigation and content")
    splitter.addWidget(nav)
    splitter.addWidget(pages)
    splitter.setStretchFactor(1, 1)
    window.setCentralWidget(splitter)

    status.showMessage(tr.text("app.status.ready"))
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
