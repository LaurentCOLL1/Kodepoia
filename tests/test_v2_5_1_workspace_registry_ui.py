from __future__ import annotations

from pathlib import Path

import pytest


pytest.importorskip("PySide6")


def _project(root: Path, name: str) -> Path:
    (root / ".kodepoia").mkdir(parents=True)
    (root / ".kodepoia" / "project.yaml").write_text(
        f"schema_version: 1\nname: {name}\nproject_type: tool\nplatforms:\n  - windows\n",
        encoding="utf-8",
    )
    return root


def test_workspace_inventory_is_read_only_and_project_scoped(tmp_path: Path) -> None:
    from PySide6.QtWidgets import QApplication, QTableWidget

    from kodepoia.kodestudio.workspace_inventory import create_workspace_inventory_widget

    app = QApplication.instance() or QApplication([])
    first = _project(tmp_path / "alpha", "Alpha")
    second = _project(tmp_path / "beta", "Beta")

    widget = create_workspace_inventory_widget([first, second, first], locale="en")
    table = widget.findChild(QTableWidget, "workspaceInventoryTable")

    assert table is not None
    assert table.rowCount() == 2
    assert table.editTriggers() == QTableWidget.EditTrigger.NoEditTriggers
    assert len(widget._kodepoia_workspace_registry.workspaces()) == 2
    assert len(widget._kodepoia_workspace_rejected) == 1
    widget.close()
    app.processEvents()
