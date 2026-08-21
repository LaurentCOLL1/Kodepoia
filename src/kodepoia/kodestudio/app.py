from __future__ import annotations

import sys


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication, QLabel, QListWidget, QMainWindow, QPushButton, QSplitter, QStackedWidget, QStatusBar, QVBoxLayout, QWidget
    except ImportError:
        print("KodeStudio requires the optional UI extra: pip install -e .[ui]", file=sys.stderr)
        return 2
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Kodepoia — KodeStudio")
    window.resize(1100, 700)
    nav = QListWidget()
    pages = QStackedWidget()
    for title in ["Chat", "Projects", "Security", "Audit", "Settings"]:
        nav.addItem(title)
        if title == "Projects":
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.addWidget(QLabel("<h2>Projects</h2>"))
            create = QPushButton("New project…")
            def open_wizard():
                from kodepoia.kodestudio.project_wizard import create_project_dialog
                create_project_dialog(window).exec()
            create.clicked.connect(open_wizard)
            layout.addWidget(create)
            layout.addStretch(1)
            pages.addWidget(page)
        else:
            pages.addWidget(QLabel(f"<h2>{title}</h2><p>KodeStudio R2.</p>"))
    nav.currentRowChanged.connect(pages.setCurrentIndex)
    nav.setCurrentRow(0)
    splitter = QSplitter()
    splitter.addWidget(nav)
    splitter.addWidget(pages)
    splitter.setStretchFactor(1, 1)
    window.setCentralWidget(splitter)
    status = QStatusBar()
    status.showMessage("Guardian ●  Sandbox ●  Secrets ●  Project DNA ●  R2")
    window.setStatusBar(status)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
