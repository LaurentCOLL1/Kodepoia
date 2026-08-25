from __future__ import annotations

from dataclasses import replace

import pytest

from kodepoia.desktop.accessibility import (
    AccessibilityRole,
    AccessibleElement,
    DesktopUiFixture,
    DpiLayoutProbe,
    LayoutDirection,
    LocalizationBundle,
    LocalizationCatalog,
    LocalizedString,
    QaIssueCode,
    ThemeContract,
    ThemeMode,
    ThemeToken,
    canonical_accessibility_fixture,
    canonical_accessibility_profile,
    canonical_framework_bindings,
    contrast_ratio,
    generate_pseudo_catalog,
    pseudo_localize,
    validate_accessibility_fixture,
)
from kodepoia.desktop.contracts import DesktopFramework


def issue_codes(report) -> set[QaIssueCode]:
    return {item.code for item in report.issues}


def test_canonical_profile_and_fixture_are_digest_stable_and_pass() -> None:
    profile = canonical_accessibility_profile()
    fixture = canonical_accessibility_fixture()
    assert profile.digest() == canonical_accessibility_profile().digest()
    assert fixture.digest() == canonical_accessibility_fixture().digest()
    report = validate_accessibility_fixture(profile, fixture)
    assert report.passed
    assert report.issues == ()
    assert not report.manual_required


def test_framework_bindings_cover_every_frozen_desktop_adapter() -> None:
    bindings = canonical_framework_bindings()
    assert {item.framework for item in bindings} == set(DesktopFramework)
    assert len({item.framework for item in bindings}) == 5
    for binding in bindings:
        payload = binding.canonical()
        assert payload["accessible_name_api"]
        assert payload["focus_api"]
        assert payload["localization_api"]
        assert payload["theme_api"]
        assert payload["dpi_api"]


def test_missing_accessible_name_fails_closed() -> None:
    fixture = canonical_accessibility_fixture()
    elements = tuple(
        replace(item, name_key=None) if item.element_id == "main.build" else item
        for item in fixture.elements
    )
    report = validate_accessibility_fixture(canonical_accessibility_profile(), replace(fixture, elements=elements))
    assert not report.passed
    assert QaIssueCode.ACCESSIBLE_NAME_MISSING in issue_codes(report)


def test_hard_coded_translatable_string_fails_closed() -> None:
    fixture = canonical_accessibility_fixture()
    elements = tuple(
        replace(item, literal_text="Build") if item.element_id == "main.build" else item
        for item in fixture.elements
    )
    report = validate_accessibility_fixture(canonical_accessibility_profile(), replace(fixture, elements=elements))
    assert QaIssueCode.HARD_CODED_TRANSLATABLE_STRING in issue_codes(report)


def test_keyboard_tab_order_requires_unique_indices() -> None:
    fixture = canonical_accessibility_fixture()
    elements = tuple(
        replace(item, tab_index=1) if item.element_id == "main.cancel" else item
        for item in fixture.elements
    )
    report = validate_accessibility_fixture(canonical_accessibility_profile(), replace(fixture, elements=elements))
    assert QaIssueCode.DUPLICATE_TAB_INDEX in issue_codes(report)


def test_keyboard_enabled_interactive_control_requires_tab_stop() -> None:
    fixture = canonical_accessibility_fixture()
    elements = tuple(
        replace(item, tab_index=None) if item.element_id == "main.cancel" else item
        for item in fixture.elements
    )
    report = validate_accessibility_fixture(canonical_accessibility_profile(), replace(fixture, elements=elements))
    assert QaIssueCode.FOCUS_TARGET_INVALID in issue_codes(report)


def test_focus_restoration_must_return_to_originating_control() -> None:
    fixture = canonical_accessibility_fixture()
    scenario = replace(fixture.focus_restorations[0], restore_element_id="main.project")
    report = validate_accessibility_fixture(
        canonical_accessibility_profile(), replace(fixture, focus_restorations=(scenario,))
    )
    assert QaIssueCode.FOCUS_RESTORE_INVALID in issue_codes(report)


def test_localization_fallback_is_explicit_and_deterministic() -> None:
    bundle = canonical_accessibility_fixture().localization
    assert bundle.resolve("fr-FR", "main.build.text") == "Construire"
    assert bundle.resolve("de-DE", "main.build.text") == "Build"
    with pytest.raises(KeyError):
        bundle.resolve("de-DE", "missing.key")


def test_pseudo_localization_preserves_placeholders_and_expands() -> None:
    value = "Build {project} now"
    pseudo = pseudo_localize(value)
    assert pseudo.startswith("⟦") and pseudo.endswith("⟧")
    assert "{project}" in pseudo
    assert len(pseudo) > len(value)
    assert pseudo == pseudo_localize(value)


def test_generated_pseudo_catalog_keeps_exact_default_keys() -> None:
    bundle = canonical_accessibility_fixture().localization
    pseudo = generate_pseudo_catalog(bundle)
    default = bundle.catalog(bundle.default_locale)
    assert default is not None
    assert set(pseudo.as_mapping()) == set(default.as_mapping())
    assert pseudo.locale == "qps-ploc"


def test_rtl_catalog_requires_rtl_safe_layout_intent() -> None:
    fixture = replace(canonical_accessibility_fixture(), supports_rtl=False)
    report = validate_accessibility_fixture(canonical_accessibility_profile(), fixture)
    assert QaIssueCode.RTL_UNSUPPORTED in issue_codes(report)


def test_contrast_gate_matches_accessibility_thresholds() -> None:
    assert contrast_ratio((0, 0, 0), (255, 255, 255)) == pytest.approx(21.0)
    fixture = canonical_accessibility_fixture()
    bad = ThemeContract(
        ThemeMode.LIGHT,
        (ThemeToken("primary_text", (120, 120, 120), (130, 130, 130)),),
    )
    themes = tuple(bad if item.mode is ThemeMode.LIGHT else item for item in fixture.themes)
    report = validate_accessibility_fixture(canonical_accessibility_profile(), replace(fixture, themes=themes))
    assert QaIssueCode.CONTRAST_TOO_LOW in issue_codes(report)


def test_high_contrast_must_honor_system_resources() -> None:
    fixture = canonical_accessibility_fixture()
    themes = tuple(
        replace(item, uses_system_resources=False) if item.mode is ThemeMode.HIGH_CONTRAST else item
        for item in fixture.themes
    )
    report = validate_accessibility_fixture(canonical_accessibility_profile(), replace(fixture, themes=themes))
    assert QaIssueCode.THEME_TOKEN_MISSING in issue_codes(report)


def test_every_required_dpi_scale_requires_a_clean_probe() -> None:
    fixture = canonical_accessibility_fixture()
    probes = tuple(item for item in fixture.layout_probes if item.scale_percent != 250)
    report = validate_accessibility_fixture(canonical_accessibility_profile(), replace(fixture, layout_probes=probes))
    assert QaIssueCode.DPI_PROFILE_INVALID in issue_codes(report)


def test_clipping_overlap_and_hidden_focus_fail_dpi_gate() -> None:
    fixture = canonical_accessibility_fixture()
    bad_probe = DpiLayoutProbe(
        200,
        1024,
        768,
        clipped_element_ids=("main.build",),
        overlapping_element_pairs=(("main.build", "main.cancel"),),
        hidden_focus_element_ids=("main.project",),
    )
    probes = tuple(bad_probe if item.scale_percent == 200 else item for item in fixture.layout_probes)
    report = validate_accessibility_fixture(canonical_accessibility_profile(), replace(fixture, layout_probes=probes))
    codes = issue_codes(report)
    assert QaIssueCode.LAYOUT_CLIPPED in codes
    assert QaIssueCode.LAYOUT_OVERLAP in codes
    assert QaIssueCode.FOCUS_HIDDEN in codes


def test_missing_localization_resource_fails_structural_gate() -> None:
    fixture = canonical_accessibility_fixture()
    default = fixture.localization.catalog("en-US")
    assert default is not None
    reduced = LocalizationCatalog(
        "en-US",
        tuple(item for item in default.entries if item.key != "main.build.name"),
    )
    catalogs = tuple(reduced if item.locale == "en-US" else item for item in fixture.localization.catalogs)
    bundle = LocalizationBundle("en-US", "en-US", catalogs)
    report = validate_accessibility_fixture(canonical_accessibility_profile(), replace(fixture, localization=bundle))
    assert QaIssueCode.LOCALIZATION_KEY_MISSING in issue_codes(report)


def test_interactive_runtime_problem_is_the_only_manual_trigger_surface() -> None:
    fixture = canonical_accessibility_fixture()
    report = validate_accessibility_fixture(
        canonical_accessibility_profile(),
        fixture,
        interactive_runtime_issue="Narrator focus announcement differs from the structural automation tree",
    )
    assert report.manual_required
    assert not report.passed
    assert report.manual_reason is not None


def test_catalog_direction_and_locale_are_bounded() -> None:
    catalog = LocalizationCatalog(
        "ar-SA", (LocalizedString("hello", "مرحبا"),), LayoutDirection.RTL
    )
    assert catalog.direction is LayoutDirection.RTL
    with pytest.raises(ValueError):
        LocalizationCatalog("not a locale!", (LocalizedString("hello", "hello"),))


def test_interactive_element_cannot_hide_from_focus_contract() -> None:
    with pytest.raises(ValueError):
        AccessibleElement("bad.button", AccessibilityRole.BUTTON, True, False, name_key="button.name")


def test_accessibility_report_digest_includes_pass_state_and_issues() -> None:
    fixture = canonical_accessibility_fixture()
    passed = validate_accessibility_fixture(canonical_accessibility_profile(), fixture)
    bad_elements = tuple(
        replace(item, name_key=None) if item.element_id == "main.build" else item
        for item in fixture.elements
    )
    failed = validate_accessibility_fixture(canonical_accessibility_profile(), replace(fixture, elements=bad_elements))
    assert passed.digest() != failed.digest()
