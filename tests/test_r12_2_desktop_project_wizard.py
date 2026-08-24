from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from kodepoia.desktop.contracts import (
    DesktopArchitecture,
    DesktopFramework,
    DesktopPackageKind,
)
from kodepoia.desktop.product_intent import apply_desktop_product_intent
from kodepoia.product.spec import ProductSpec
from kodepoia.project.dna import (
    DecisionState,
    DesktopProjectProfile,
    Platform,
    ProjectDNA,
    ProjectType,
)
from kodepoia.project.wizard import ProjectWizardState


def test_r12_2_legacy_schema_v1_round_trips_without_desktop_semantic_drift(
    tmp_path: Path,
) -> None:
    legacy = {
        "schema_version": 1,
        "name": "Legacy Tool",
        "project_type": "tool",
        "platforms": ["windows"],
        "engine": None,
        "engine_version": None,
        "dimension": None,
        "genres": [],
        "inputs": [],
        "graphics_style": None,
        "online": "no",
        "multiplayer": "no",
        "performance": {},
        "tools": {},
        "download_policy": "ask",
        "install_policy": "ask",
        "lineage": {},
        "capabilities": {},
    }
    path = tmp_path / "project.yaml"
    path.write_text(yaml.safe_dump(legacy, sort_keys=False), encoding="utf-8")
    dna = ProjectDNA.load(path)
    assert dna.desktop is None
    assert dna.to_dict() == legacy
    assert "desktop" not in dna.to_dict()


def test_r12_2_desktop_wizard_state_builds_explicit_profile() -> None:
    dna = ProjectWizardState(
        name="Desktop Sample",
        project_type=ProjectType.DESKTOP_APP,
        platforms=[Platform.WINDOWS],
        desktop_framework=DesktopFramework.WINUI3,
        desktop_architecture=DesktopArchitecture.X64,
        desktop_package_kind=DesktopPackageKind.UNPACKAGED,
        desktop_persistence=DecisionState.YES,
        desktop_ipc=DecisionState.NO,
        desktop_updates=DecisionState.UNDECIDED,
    ).build()
    assert dna.engine is None
    assert dna.dimension is None
    assert dna.inputs == []
    assert dna.desktop is not None
    assert dna.desktop.framework is DesktopFramework.WINUI3
    payload = dna.to_dict()
    assert payload["desktop"]["architecture"] == "x64"
    assert payload["desktop"]["persistence"] == "yes"


def test_r12_2_impossible_desktop_platform_framework_combinations_fail() -> None:
    with pytest.raises(ValueError, match="Windows only"):
        ProjectWizardState(
            name="Bad WPF",
            project_type=ProjectType.DESKTOP_APP,
            platforms=[Platform.WINDOWS, Platform.LINUX],
            desktop_framework=DesktopFramework.WPF,
        ).build()
    with pytest.raises(ValueError, match="only Windows, Linux or macOS"):
        ProjectWizardState(
            name="Bad Web",
            project_type=ProjectType.DESKTOP_APP,
            platforms=[Platform.WEB],
            desktop_framework=DesktopFramework.TAURI2,
        ).build()
    with pytest.raises(ValueError, match="MSIX requires"):
        ProjectWizardState(
            name="Bad MSIX",
            project_type=ProjectType.DESKTOP_APP,
            platforms=[Platform.LINUX],
            desktop_framework=DesktopFramework.AVALONIA,
            desktop_package_kind=DesktopPackageKind.MSIX,
        ).build()


def test_r12_2_desktop_product_mapping_is_deterministic_and_reserved() -> None:
    profile = DesktopProjectProfile(
        framework=DesktopFramework.QT6,
        architecture=DesktopArchitecture.X64,
        package_kind=DesktopPackageKind.ARCHIVE,
        persistence=DecisionState.YES,
        ipc=DecisionState.YES,
        updates=DecisionState.NO,
    )
    product = ProductSpec(1, "Desk", "Build a desktop application")
    apply_desktop_product_intent(product, profile, [Platform.LINUX, Platform.WINDOWS])
    product.validate()
    assert product.constraints == [
        "desktop.framework=qt6",
        "desktop.architecture=x64",
        "desktop.package=archive",
        "desktop.persistence=yes",
        "desktop.ipc=yes",
        "desktop.updates=no",
    ]
    requirement = product.requirement("DESKTOP-TARGET")
    assert "linux, windows" in requirement.acceptance[0].text
    apply_desktop_product_intent(product, profile, [Platform.WINDOWS, Platform.LINUX])
    assert [item.id for item in product.requirements].count("DESKTOP-TARGET") == 1


def test_r12_2_enhanced_existing_wizard_creates_desktop_dna_and_product(
    tmp_path: Path,
) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from kodepoia.kodestudio.r12_project_wizard import create_project_dialog

    app = QApplication.instance() or QApplication([])
    dialog = create_project_dialog()
    dialog.project_type.setCurrentIndex(dialog.project_type.findData("desktop_app"))
    app.processEvents()

    assert dialog.desktop_framework.isVisibleTo(dialog)
    assert dialog.engine.isEnabled() is False
    assert dialog.platform_checks[Platform.WINDOWS].isChecked()
    assert dialog.platform_checks[Platform.ANDROID].isEnabled() is False

    dialog.name.setText("Desktop Wizard Fixture")
    dialog.directory.setText(str(tmp_path / "project"))
    dialog.vision.setPlainText("Create a deterministic desktop fixture")
    dialog._r12_desktop_submit()

    dna = ProjectDNA.load(tmp_path / "project/.kodepoia/project.yaml")
    product = ProductSpec.load(tmp_path / "project/.kodepoia/product/product.yaml")
    assert dna.project_type is ProjectType.DESKTOP_APP
    assert dna.desktop is not None
    assert dna.desktop.framework is DesktopFramework.WINUI3
    assert product.document_type.value == "prd"
    assert "desktop.framework=winui3" in product.constraints
    assert product.requirement("DESKTOP-TARGET").priority == "P0"
    dialog.close()
