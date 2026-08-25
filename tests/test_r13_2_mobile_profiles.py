from __future__ import annotations

import json
import os
from dataclasses import replace
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from kodepoia.mobile.contracts import MobileFormFactor, MobilePackageKind, MobileSourceKind
from kodepoia.mobile.product_intent import apply_mobile_product_intent
from kodepoia.product.spec import AcceptanceCriterion, ProductSpec, Requirement
from kodepoia.project.dna import (
    MobileNetworkIntent,
    MobileProjectBudget,
    MobileProjectProfile,
    MobileReleaseChannel,
    MobileSigningIntent,
    Platform,
    ProjectDNA,
    ProjectType,
)
from kodepoia.project.wizard import ProjectWizardState

ROOT = Path(__file__).resolve().parents[1]


def _legacy_payload() -> dict[str, object]:
    return {
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


def test_r13_2_legacy_project_dna_roundtrips_without_mobile_drift(tmp_path: Path) -> None:
    legacy = _legacy_payload()
    path = tmp_path / "project.yaml"
    path.write_text(yaml.safe_dump(legacy, sort_keys=False), encoding="utf-8")
    dna = ProjectDNA.load(path)
    assert dna.mobile is None
    assert dna.to_dict() == legacy
    assert "mobile" not in dna.to_dict()


def test_r13_2_native_android_mobile_app_defaults_are_deterministic() -> None:
    dna = ProjectWizardState(
        name="Mobile Sample",
        project_type=ProjectType.MOBILE_APP,
        platforms=[Platform.ANDROID],
    ).build()
    assert dna.project_type is ProjectType.MOBILE_APP
    assert dna.engine is None
    assert dna.dimension is None
    assert dna.inputs == []
    assert dna.mobile is not None
    assert dna.mobile.source_kind is MobileSourceKind.NATIVE
    assert dna.mobile.form_factors == (MobileFormFactor.PHONE,)
    assert dna.mobile.android_application_id == "org.kodepoia.mobilesample"
    assert dna.mobile.android_min_api == 26
    assert dna.mobile.android_target_api == 36
    assert dna.mobile.apple_bundle_id is None
    assert dna.mobile.package_kinds == (MobilePackageKind.AAB,)
    assert dna.mobile.network_intent is MobileNetworkIntent.OFFLINE
    assert dna.mobile.release_channel is MobileReleaseChannel.DEVELOPMENT
    assert dna.mobile.signing_intent is MobileSigningIntent.UNSIGNED


def test_r13_2_native_android_ios_mobile_app_roundtrip(tmp_path: Path) -> None:
    dna = ProjectWizardState(
        name="Cross Mobile",
        project_type=ProjectType.MOBILE_APP,
        platforms=[Platform.IOS, Platform.ANDROID],
        mobile_form_factors=(MobileFormFactor.TABLET, MobileFormFactor.PHONE),
        mobile_permissions=("camera", "notifications", "camera"),
        mobile_requested_capabilities=("offline_cache", "camera"),
        mobile_network_intent=MobileNetworkIntent.OPTIONAL,
        mobile_release_channel=MobileReleaseChannel.BETA,
        mobile_signing_intent=MobileSigningIntent.TEST,
        mobile_budget=MobileProjectBudget(
            max_package_mb=512,
            max_build_seconds=1200,
            max_device_matrix_runs=24,
        ),
    ).build()
    assert dna.mobile is not None
    assert dna.mobile.form_factors == (
        MobileFormFactor.PHONE,
        MobileFormFactor.TABLET,
    )
    assert dna.mobile.android_application_id == "org.kodepoia.crossmobile"
    assert dna.mobile.apple_bundle_id == "org.kodepoia.crossmobile"
    assert dna.mobile.package_kinds == (MobilePackageKind.AAB, MobilePackageKind.APP)
    assert dna.mobile.permissions == ("camera", "notifications")
    assert dna.mobile.requested_capabilities == ("camera", "offline_cache")

    path = tmp_path / "project.yaml"
    dna.save(path)
    loaded = ProjectDNA.load(path)
    assert loaded.to_dict() == dna.to_dict()


def test_r13_2_game_mobile_intent_uses_godot_export_without_parallel_app_model() -> None:
    dna = ProjectWizardState(
        name="Godot Mobile",
        project_type=ProjectType.GAME,
        platforms=[Platform.WINDOWS, Platform.ANDROID],
        engine="Godot",
    ).build()
    assert dna.mobile is not None
    assert dna.mobile.source_kind is MobileSourceKind.GODOT_EXPORT
    assert dna.mobile.android_application_id == "org.kodepoia.godotmobile"
    assert dna.mobile.package_kinds == (MobilePackageKind.AAB,)
    assert Platform.WINDOWS in dna.platforms


def test_r13_2_impossible_mobile_platform_and_source_combinations_fail() -> None:
    with pytest.raises(ValueError, match="only Android and/or iOS"):
        ProjectWizardState(
            name="Bad Mobile",
            project_type=ProjectType.MOBILE_APP,
            platforms=[Platform.ANDROID, Platform.WINDOWS],
        ).build()

    with pytest.raises(ValueError, match="Native mobile source"):
        ProjectWizardState(
            name="Bad Native Game",
            project_type=ProjectType.GAME,
            platforms=[Platform.ANDROID],
            engine="Godot",
            mobile_source_kind=MobileSourceKind.NATIVE,
        ).build()

    with pytest.raises(ValueError, match="Godot mobile export"):
        ProjectWizardState(
            name="Bad Export App",
            project_type=ProjectType.MOBILE_APP,
            platforms=[Platform.ANDROID],
            mobile_source_kind=MobileSourceKind.GODOT_EXPORT,
        ).build()

    with pytest.raises(ValueError, match="Godot engine"):
        ProjectWizardState(
            name="Bad Engine",
            project_type=ProjectType.GAME,
            platforms=[Platform.ANDROID],
            engine="Unity",
            mobile_source_kind=MobileSourceKind.GODOT_EXPORT,
        ).build()


def test_r13_2_invalid_identity_versions_packages_and_injected_names_fail() -> None:
    with pytest.raises(ValueError):
        ProjectWizardState(
            name="Bad Android ID",
            project_type=ProjectType.MOBILE_APP,
            platforms=[Platform.ANDROID],
            android_application_id="bad id;rm -rf",
        ).build()

    with pytest.raises(ValueError, match="min/target API"):
        ProjectWizardState(
            name="Bad API",
            project_type=ProjectType.MOBILE_APP,
            platforms=[Platform.ANDROID],
            android_min_api=40,
            android_target_api=36,
        ).build()

    with pytest.raises(ValueError):
        ProjectWizardState(
            name="Bad Apple ID",
            project_type=ProjectType.MOBILE_APP,
            platforms=[Platform.IOS],
            apple_bundle_id="org.example.$(shell)",
        ).build()

    with pytest.raises(ValueError, match="minimum version"):
        ProjectWizardState(
            name="Bad Apple Version",
            project_type=ProjectType.MOBILE_APP,
            platforms=[Platform.IOS],
            apple_min_version="27.0",
            apple_target_version="26.0",
        ).build()

    with pytest.raises(ValueError, match="package intent"):
        ProjectWizardState(
            name="Bad Package",
            project_type=ProjectType.MOBILE_APP,
            platforms=[Platform.ANDROID],
            mobile_package_kinds=(MobilePackageKind.IPA,),
        ).build()

    with pytest.raises(ValueError, match="invalid mobile permissions"):
        ProjectWizardState(
            name="Bad Permission",
            project_type=ProjectType.MOBILE_APP,
            platforms=[Platform.ANDROID],
            mobile_permissions=("camera;--stacktrace",),
        ).build()


def test_r13_2_mobile_profile_rejects_cross_platform_hidden_fields() -> None:
    profile = MobileProjectProfile(
        source_kind=MobileSourceKind.NATIVE,
        android_application_id="org.example.app",
        android_min_api=26,
        android_target_api=36,
        apple_bundle_id="org.example.hidden",
        apple_min_version="16.0",
        apple_target_version="26.0",
        package_kinds=(MobilePackageKind.AAB,),
    )
    with pytest.raises(ValueError, match="Apple intent"):
        profile.validate([Platform.ANDROID], ProjectType.MOBILE_APP, None)


def test_r13_2_product_mapping_is_deterministic_idempotent_and_reserved() -> None:
    dna = ProjectWizardState(
        name="Product Mobile",
        project_type=ProjectType.MOBILE_APP,
        platforms=[Platform.ANDROID, Platform.IOS],
        mobile_release_channel=MobileReleaseChannel.INTERNAL,
    ).build()
    assert dna.mobile is not None
    product = ProductSpec(1, "Product Mobile", "Create a governed mobile application")
    apply_mobile_product_intent(product, dna.mobile, dna.platforms)
    product.validate()
    first_constraints = list(product.constraints)
    requirement = product.requirement("MOBILE-TARGET")
    assert requirement.priority == "P0"
    assert "android, ios" in requirement.acceptance[0].text
    assert dna.mobile.android_application_id in requirement.acceptance[1].text

    apply_mobile_product_intent(product, dna.mobile, reversed(dna.platforms))
    assert product.constraints == first_constraints
    assert [item.id for item in product.requirements].count("MOBILE-TARGET") == 1

    forged = ProductSpec(1, "Forged", "Create a forged fixture")
    forged.requirements.append(
        Requirement(
            "MOBILE-TARGET",
            "Attacker override",
            "not authoritative",
            priority="P0",
            acceptance=[AcceptanceCriterion("MOBILE-TARGET-AC-1", "fake")],
        )
    )
    with pytest.raises(ValueError, match="reserved"):
        apply_mobile_product_intent(forged, dna.mobile, dna.platforms)


def test_r13_2_project_dna_and_dedicated_mobile_schemas_accept_canonical_data() -> None:
    project_schema = json.loads(
        (ROOT / "schemas/project-dna-v1.schema.json").read_text(encoding="utf-8")
    )
    mobile_schema = json.loads(
        (ROOT / "schemas/r13/mobile-project-profile.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator.check_schema(project_schema)
    Draft202012Validator.check_schema(mobile_schema)

    legacy = _legacy_payload()
    Draft202012Validator(project_schema).validate(legacy)

    dna = ProjectWizardState(
        name="Schema Mobile",
        project_type=ProjectType.MOBILE_APP,
        platforms=[Platform.ANDROID, Platform.IOS],
    ).build()
    payload = dna.to_dict()
    Draft202012Validator(project_schema).validate(payload)
    Draft202012Validator(mobile_schema).validate(payload["mobile"])

    forged = dict(payload["mobile"])
    forged["raw_gradle_args"] = ["--stacktrace", "-Ppassword=secret"]
    with pytest.raises(Exception):
        Draft202012Validator(mobile_schema).validate(forged)

    forged = dict(payload["mobile"])
    forged["xcode_build_setting"] = "CODE_SIGN_IDENTITY=attacker"
    with pytest.raises(Exception):
        Draft202012Validator(mobile_schema).validate(forged)


def test_r13_2_wizard_localization_and_pseudo_localization_are_registered() -> None:
    from kodepoia.kodestudio.r13_wizard_localization import (
        R13WizardTranslator,
        registered_r13_wizard_messages,
    )

    messages = registered_r13_wizard_messages()
    assert "r13.wizard.intent_only" in messages
    assert "SDK" in messages["r13.wizard.intent_only"]
    pseudo = R13WizardTranslator("qps-ploc")
    assert pseudo.text("r13.wizard.tab") != "Mobile"
    assert pseudo.text("r13.wizard.intent_only") != messages["r13.wizard.intent_only"]


def test_r13_2_existing_kodestudio_wizard_creates_mobile_dna_and_product(
    tmp_path: Path,
) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from kodepoia.kodestudio.r13_project_wizard import create_project_dialog

    app = QApplication.instance() or QApplication([])
    dialog = create_project_dialog(locale="qps-ploc")
    dialog.project_type.setCurrentIndex(dialog.project_type.findData("mobile_app"))
    app.processEvents()

    assert dialog.platform_checks[Platform.ANDROID].isEnabled()
    assert dialog.platform_checks[Platform.ANDROID].isChecked()
    assert dialog.platform_checks[Platform.IOS].isEnabled()
    assert dialog.platform_checks[Platform.WINDOWS].isEnabled() is False
    assert dialog.engine.isEnabled() is False
    assert str(dialog.mobile_source.currentData()) == "native"
    assert dialog.mobile_source.isEnabled() is False
    assert dialog.android_application_id.accessibleName()
    assert dialog.android_application_id.accessibleDescription()
    assert dialog.mobile_permissions.accessibleDescription()

    dialog.name.setText("Mobile Wizard Fixture")
    dialog.directory.setText(str(tmp_path / "project"))
    dialog.vision.setPlainText("Create a deterministic mobile fixture")
    dialog.mobile_permissions.setText("camera; notifications")
    dialog._r13_mobile_submit()

    dna = ProjectDNA.load(tmp_path / "project/.kodepoia/project.yaml")
    product = ProductSpec.load(tmp_path / "project/.kodepoia/product/product.yaml")
    assert dna.project_type is ProjectType.MOBILE_APP
    assert dna.mobile is not None
    assert dna.mobile.source_kind is MobileSourceKind.NATIVE
    assert dna.mobile.android_target_api == 36
    assert dna.mobile.permissions == ("camera", "notifications")
    assert product.requirement("MOBILE-TARGET").priority == "P0"
    assert "mobile.source=native" in product.constraints
    assert not list((tmp_path / "project").rglob("*.apk"))
    assert not list((tmp_path / "project").rglob("*.aab"))
    dialog.close()


def test_r13_2_game_wizard_mobile_source_is_locked_to_godot_export() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from kodepoia.kodestudio.r13_project_wizard import create_project_dialog

    app = QApplication.instance() or QApplication([])
    dialog = create_project_dialog()
    dialog.project_type.setCurrentIndex(dialog.project_type.findData("game"))
    dialog.platform_checks[Platform.ANDROID].setChecked(True)
    app.processEvents()
    assert str(dialog.mobile_source.currentData()) == "godot_export"
    assert dialog.mobile_source.isEnabled() is False
    assert dialog.platform_checks[Platform.WINDOWS].isEnabled()
    dialog.close()
