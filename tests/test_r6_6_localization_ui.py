from __future__ import annotations

import os

import pytest


pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QListWidget, QPushButton

from kodepoia.kodestudio.app import build_window


def test_kodestudio_pseudo_locale_expands_registered_main_surface_without_nav_truncation() -> None:
    app = QApplication.instance() or QApplication([])
    window = build_window(locale="qps-ploc")
    window.show()
    QApplication.processEvents()
    try:
        nav = window.findChild(QListWidget, "mainNavigation")
        assert nav is not None
        texts = [nav.item(index).text() for index in range(nav.count())]
        assert len(texts) == 5
        assert all(text.startswith("⟦") and text.endswith("⟧") for text in texts)
        assert nav.minimumWidth() >= nav.sizeHintForColumn(0) + 24

        new_project = window.findChild(QPushButton, "newProjectButton")
        stop = window.findChild(QPushButton, "killSwitchButton")
        reset = window.findChild(QPushButton, "killSwitchResetButton")
        assert new_project is not None and new_project.text().startswith("⟦")
        assert stop is not None and stop.text().startswith("⟦")
        assert reset is not None and reset.text().startswith("⟦")

        assert window.windowTitle().startswith("⟦")
        assert window.size().width() == 1100
    finally:
        window.close()
        QApplication.processEvents()
