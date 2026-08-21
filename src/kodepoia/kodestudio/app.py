from __future__ import annotations

import sys


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication, QLabel, QListWidget, QMainWindow, QSplitter, QStackedWidget, QStatusBar
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
        pages.addWidget(QLabel(f"<h2>{title}</h2><p>KodeStudio R1 minimal.</p>"))
    nav.currentRowChanged.connect(pages.setCurrentIndex)
    nav.setCurrentRow(0)
    splitter = QSplitter()
    splitter.addWidget(nav)
    splitter.addWidget(pages)
    splitter.setStretchFactor(1, 1)
    window.setCentralWidget(splitter)
    status = QStatusBar()
    status.showMessage("Guardian ●  Sandbox ●  Secrets ●  R1")
    window.setStatusBar(status)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
