from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QWidget,
)

from kodepoia.kodestudio.app import build_window


def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_kodestudio_exposes_service_backed_vault_panel(tmp_path: Path) -> None:
    qt_app()
    window = build_window(project_root=tmp_path)
    window.show()
    QApplication.processEvents()

    page = window.findChild(QWidget, "vaultPage")
    assert page is not None
    assert page.findChild(QLineEdit, "vaultSearchInput") is not None
    assert page.findChild(QCheckBox, "vaultIncludeBlocked") is not None
    assert page.findChild(QPushButton, "vaultSearchButton") is not None
    assert page.findChild(QPushButton, "vaultRefreshButton") is not None
    assert page.findChild(QPushButton, "vaultDuplicatesButton") is not None
    assert page.findChild(QPushButton, "vaultRebuildButton") is not None
    assert page.findChild(QPushButton, "vaultCancelButton") is not None
    assert page.findChild(QTableWidget, "vaultAssetTable") is not None
    assert page.findChild(QPlainTextEdit, "vaultLineageView") is not None
    progress = page.findChild(QLabel, "vaultOperationStatus")
    budget = page.findChild(QLabel, "vaultOperationBudget")
    assert progress is not None and progress.text().strip()
    assert budget is not None and budget.text().startswith("Budget:")
    assert hasattr(page, "_kodepoia_asset_service")

    window.close()
