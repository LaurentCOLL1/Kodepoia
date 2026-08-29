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
        # R10.11 added Blender / 3D, R11.13 added Media / Franchise,
        # R12.15 added the governed Desktop workspace, R13.16 added
        # Mobile / DeviceLab / Release, and R14.16 adds Backend / LiveOps.
        assert len(texts) == 13
        assert all(text.startswith("⟦") and text.endswith("⟧") for text in texts)
        assert nav.minimumWidth() >= nav.sizeHintForColumn(0) + 24

        new_project = window.findChild(QPushButton, "newProjectButton")
        stop = window.findChild(QPushButton, "killSwitchButton")
        reset = window.findChild(QPushButton, "killSwitchResetButton")
        research = window.findChild(QPushButton, "researchSearchButton")
        vault = window.findChild(QPushButton, "vaultSearchButton")
        comfy = window.findChild(QPushButton, "comfyRunButton")
        r11_refresh = window.findChild(QPushButton, "r11RefreshButton")
        r11_cancel = window.findChild(QPushButton, "r11CancelButton")
        r12_refresh = window.findChild(QPushButton, "r12Refresh")
        r12_cancel = window.findChild(QPushButton, "r12Cancel")
        r13_refresh = window.findChild(QPushButton, "r13Refresh")
        r13_cancel = window.findChild(QPushButton, "r13Cancel")
        r14_execute = window.findChild(QPushButton, "r14ExecuteButton")
        assert new_project is not None and new_project.text().startswith("⟦")
        assert stop is not None and stop.text().startswith("⟦")
        assert reset is not None and reset.text().startswith("⟦")
        assert research is not None and research.text().startswith("⟦")
        assert vault is not None and vault.text().startswith("⟦")
        assert comfy is not None and comfy.text().startswith("⟦")
        assert r11_refresh is not None and r11_refresh.text().startswith("⟦")
        assert r11_cancel is not None and r11_cancel.text().startswith("⟦")
        assert r12_refresh is not None and r12_refresh.text().startswith("⟦")
        assert r12_cancel is not None and r12_cancel.text().startswith("⟦")
        assert r13_refresh is not None and r13_refresh.text().startswith("⟦")
        assert r13_cancel is not None and r13_cancel.text().startswith("⟦")
        assert r14_execute is not None and r14_execute.text().startswith("⟦")

        assert window.windowTitle().startswith("⟦")
        assert window.size().width() >= 1100
        assert window.size().height() >= 700
    finally:
        window.close()
        QApplication.processEvents()
