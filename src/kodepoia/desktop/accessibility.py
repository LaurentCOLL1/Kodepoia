from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping, Sequence

from .contracts import DesktopFramework, canonical_sha256

_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_LOCALE_RE = re.compile(r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")
_PLACEHOLDER_RE = re.compile(r"(\{[^{}]+\})")


def _stable_id(value: str, field: str) -> str:
    if not isinstance(value, str) or _ID_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be a stable identifier")
    return value


def _text(value: str, field: str, maximum: int = 2048) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or "\x00" in value:
        raise ValueError(f"{field} must be non-empty bounded text")
    return value


def _locale(value: str, field: str = "locale") -> str:
    if not isinstance(value, str) or _LOCALE_RE.fullmatch(value) is None or len(value) > 35:
        raise ValueError(f"{field} must be a bounded BCP-47-like locale")
    return value


class AccessibilityRole(StrEnum):
    BUTTON = "button"
    CHECKBOX = "checkbox"
    COMBOBOX = "combobox"
    DIALOG = "dialog"
    HEADING = "heading"
    IMAGE = "image"
    LABEL = "label"
    LINK = "link"
    LIST = "list"
    LIST_ITEM = "list_item"
    MENU = "menu"
    MENU_ITEM = "menu_item"
    PROGRESS = "progress"
    RADIO = "radio"
    SLIDER = "slider"
    STATUS = "status"
    TAB = "tab"
    TAB_PANEL = "tab_panel"
    TEXT = "text"
    TEXTBOX = "textbox"
    WINDOW = "window"


class ThemeMode(StrEnum):
    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"
    HIGH_CONTRAST = "high_contrast"


class LayoutDirection(StrEnum):
    LTR = "ltr"
    RTL = "rtl"
    AUTO = "auto"


class QaSeverity(StrEnum):
    ERROR = "ERROR"
    WARNING = "WARNING"


class QaIssueCode(StrEnum):
    ACCESSIBLE_NAME_MISSING = "ACCESSIBLE_NAME_MISSING"
    DESCRIPTION_RESOURCE_MISSING = "DESCRIPTION_RESOURCE_MISSING"
    DUPLICATE_TAB_INDEX = "DUPLICATE_TAB_INDEX"
    FOCUS_TARGET_INVALID = "FOCUS_TARGET_INVALID"
    FOCUS_RESTORE_INVALID = "FOCUS_RESTORE_INVALID"
    HARD_CODED_TRANSLATABLE_STRING = "HARD_CODED_TRANSLATABLE_STRING"
    LOCALIZATION_KEY_MISSING = "LOCALIZATION_KEY_MISSING"
    PSEUDO_LOCALIZATION_FAILED = "PSEUDO_LOCALIZATION_FAILED"
    RTL_UNSUPPORTED = "RTL_UNSUPPORTED"
    THEME_TOKEN_MISSING = "THEME_TOKEN_MISSING"
    CONTRAST_TOO_LOW = "CONTRAST_TOO_LOW"
    DPI_PROFILE_INVALID = "DPI_PROFILE_INVALID"
    LAYOUT_CLIPPED = "LAYOUT_CLIPPED"
    LAYOUT_OVERLAP = "LAYOUT_OVERLAP"
    FOCUS_HIDDEN = "FOCUS_HIDDEN"


@dataclass(frozen=True, slots=True)
class LocalizedString:
    key: str
    value: str

    def __post_init__(self) -> None:
        _stable_id(self.key, "key")
        _text(self.value, "value")

    def canonical(self) -> dict[str, str]:
        return {"key": self.key, "value": self.value}


@dataclass(frozen=True, slots=True)
class LocalizationCatalog:
    locale: str
    entries: tuple[LocalizedString, ...]
    direction: LayoutDirection = LayoutDirection.LTR

    def __post_init__(self) -> None:
        _locale(self.locale)
        entries = tuple(sorted(self.entries, key=lambda item: item.key))
        if not entries or len(entries) > 2048:
            raise ValueError("entries must contain 1..2048 localized strings")
        keys = [item.key for item in entries]
        if len(keys) != len(set(keys)):
            raise ValueError("localization keys must be unique")
        object.__setattr__(self, "entries", entries)

    def as_mapping(self) -> dict[str, str]:
        return {item.key: item.value for item in self.entries}

    def canonical(self) -> dict[str, Any]:
        return {
            "locale": self.locale,
            "direction": self.direction.value,
            "entries": [item.canonical() for item in self.entries],
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class LocalizationBundle:
    default_locale: str
    fallback_locale: str
    catalogs: tuple[LocalizationCatalog, ...]
    pseudo_locale: str = "qps-ploc"

    def __post_init__(self) -> None:
        _locale(self.default_locale, "default_locale")
        _locale(self.fallback_locale, "fallback_locale")
        _locale(self.pseudo_locale, "pseudo_locale")
        catalogs = tuple(sorted(self.catalogs, key=lambda item: item.locale.lower()))
        if not catalogs or len(catalogs) > 128:
            raise ValueError("catalogs must contain 1..128 locales")
        locales = [item.locale.lower() for item in catalogs]
        if len(locales) != len(set(locales)):
            raise ValueError("catalog locales must be unique")
        if self.default_locale.lower() not in locales:
            raise ValueError("default locale catalog is required")
        if self.fallback_locale.lower() not in locales:
            raise ValueError("fallback locale catalog is required")
        object.__setattr__(self, "catalogs", catalogs)

    def catalog(self, locale: str) -> LocalizationCatalog | None:
        wanted = _locale(locale).lower()
        return next((item for item in self.catalogs if item.locale.lower() == wanted), None)

    def resolve(self, locale: str, key: str) -> str:
        _stable_id(key, "key")
        requested = self.catalog(locale)
        fallback = self.catalog(self.fallback_locale)
        default = self.catalog(self.default_locale)
        assert fallback is not None and default is not None
        for catalog in (requested, fallback, default):
            if catalog is not None:
                value = catalog.as_mapping().get(key)
                if value is not None:
                    return value
        raise KeyError(key)

    def canonical(self) -> dict[str, Any]:
        return {
            "default_locale": self.default_locale,
            "fallback_locale": self.fallback_locale,
            "pseudo_locale": self.pseudo_locale,
            "catalogs": [item.canonical() for item in self.catalogs],
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class AccessibleElement:
    element_id: str
    role: AccessibilityRole
    interactive: bool
    focusable: bool
    tab_index: int | None = None
    name_key: str | None = None
    description_key: str | None = None
    text_key: str | None = None
    literal_text: str | None = None
    translatable: bool = False
    enabled: bool = True

    def __post_init__(self) -> None:
        _stable_id(self.element_id, "element_id")
        for field_name in ("name_key", "description_key", "text_key"):
            value = getattr(self, field_name)
            if value is not None:
                _stable_id(value, field_name)
        if self.tab_index is not None and not 0 <= self.tab_index <= 65535:
            raise ValueError("tab_index must be within 0..65535")
        if self.literal_text is not None:
            _text(self.literal_text, "literal_text")
        if self.interactive and not self.focusable:
            raise ValueError("interactive elements must be focusable")
        if not self.focusable and self.tab_index is not None:
            raise ValueError("non-focusable elements cannot have a tab_index")

    def canonical(self) -> dict[str, Any]:
        return {
            "element_id": self.element_id,
            "role": self.role.value,
            "interactive": self.interactive,
            "focusable": self.focusable,
            "tab_index": self.tab_index,
            "name_key": self.name_key,
            "description_key": self.description_key,
            "text_key": self.text_key,
            "literal_text": self.literal_text,
            "translatable": self.translatable,
            "enabled": self.enabled,
        }


@dataclass(frozen=True, slots=True)
class FocusRestoration:
    scenario_id: str
    source_element_id: str
    temporary_element_id: str
    restore_element_id: str

    def __post_init__(self) -> None:
        _stable_id(self.scenario_id, "scenario_id")
        _stable_id(self.source_element_id, "source_element_id")
        _stable_id(self.temporary_element_id, "temporary_element_id")
        _stable_id(self.restore_element_id, "restore_element_id")

    def canonical(self) -> dict[str, str]:
        return {
            "scenario_id": self.scenario_id,
            "source_element_id": self.source_element_id,
            "temporary_element_id": self.temporary_element_id,
            "restore_element_id": self.restore_element_id,
        }


@dataclass(frozen=True, slots=True)
class ThemeToken:
    token_id: str
    foreground_rgb: tuple[int, int, int]
    background_rgb: tuple[int, int, int]
    large_text: bool = False

    def __post_init__(self) -> None:
        _stable_id(self.token_id, "token_id")
        for value in (*self.foreground_rgb, *self.background_rgb):
            if not isinstance(value, int) or not 0 <= value <= 255:
                raise ValueError("RGB components must be integers within 0..255")

    def canonical(self) -> dict[str, Any]:
        return {
            "token_id": self.token_id,
            "foreground_rgb": list(self.foreground_rgb),
            "background_rgb": list(self.background_rgb),
            "large_text": self.large_text,
        }


@dataclass(frozen=True, slots=True)
class ThemeContract:
    mode: ThemeMode
    tokens: tuple[ThemeToken, ...]
    uses_system_resources: bool = True

    def __post_init__(self) -> None:
        tokens = tuple(sorted(self.tokens, key=lambda item: item.token_id))
        if not tokens or len(tokens) > 256:
            raise ValueError("theme tokens must contain 1..256 entries")
        ids = [item.token_id for item in tokens]
        if len(ids) != len(set(ids)):
            raise ValueError("theme token ids must be unique")
        object.__setattr__(self, "tokens", tokens)

    def canonical(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "uses_system_resources": self.uses_system_resources,
            "tokens": [item.canonical() for item in self.tokens],
        }


@dataclass(frozen=True, slots=True)
class DpiLayoutProbe:
    scale_percent: int
    width_dip: int
    height_dip: int
    clipped_element_ids: tuple[str, ...] = ()
    overlapping_element_pairs: tuple[tuple[str, str], ...] = ()
    hidden_focus_element_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.scale_percent not in {100, 125, 150, 175, 200, 225, 250, 300, 350, 400}:
            raise ValueError("scale_percent must use an accepted Windows QA scale")
        if not 320 <= self.width_dip <= 7680 or not 240 <= self.height_dip <= 4320:
            raise ValueError("layout viewport is outside bounded QA dimensions")
        for item in (*self.clipped_element_ids, *self.hidden_focus_element_ids):
            _stable_id(item, "element_id")
        for left, right in self.overlapping_element_pairs:
            _stable_id(left, "left element")
            _stable_id(right, "right element")
            if left == right:
                raise ValueError("overlap pair must contain two elements")
        object.__setattr__(self, "clipped_element_ids", tuple(sorted(set(self.clipped_element_ids))))
        object.__setattr__(self, "hidden_focus_element_ids", tuple(sorted(set(self.hidden_focus_element_ids))))
        object.__setattr__(self, "overlapping_element_pairs", tuple(sorted(set(self.overlapping_element_pairs))))

    def canonical(self) -> dict[str, Any]:
        return {
            "scale_percent": self.scale_percent,
            "width_dip": self.width_dip,
            "height_dip": self.height_dip,
            "clipped_element_ids": list(self.clipped_element_ids),
            "overlapping_element_pairs": [list(item) for item in self.overlapping_element_pairs],
            "hidden_focus_element_ids": list(self.hidden_focus_element_ids),
        }


@dataclass(frozen=True, slots=True)
class FrameworkAccessibilityBinding:
    framework: DesktopFramework
    accessible_name_api: str
    accessible_description_api: str
    role_api: str
    focus_api: str
    localization_api: str
    theme_api: str
    dpi_api: str

    def __post_init__(self) -> None:
        for field_name in (
            "accessible_name_api", "accessible_description_api", "role_api", "focus_api",
            "localization_api", "theme_api", "dpi_api",
        ):
            _text(getattr(self, field_name), field_name, maximum=256)

    def canonical(self) -> dict[str, str]:
        return {
            "framework": self.framework.value,
            "accessible_name_api": self.accessible_name_api,
            "accessible_description_api": self.accessible_description_api,
            "role_api": self.role_api,
            "focus_api": self.focus_api,
            "localization_api": self.localization_api,
            "theme_api": self.theme_api,
            "dpi_api": self.dpi_api,
        }


@dataclass(frozen=True, slots=True)
class DesktopAccessibilityProfile:
    profile_id: str
    frameworks: tuple[DesktopFramework, ...]
    required_scales: tuple[int, ...] = (100, 125, 150, 200, 250, 300, 400)
    required_themes: tuple[ThemeMode, ...] = (
        ThemeMode.LIGHT, ThemeMode.DARK, ThemeMode.HIGH_CONTRAST,
    )
    require_keyboard_only: bool = True
    require_focus_restoration: bool = True
    require_pseudo_localization: bool = True
    require_rtl_intent: bool = True

    def __post_init__(self) -> None:
        _stable_id(self.profile_id, "profile_id")
        frameworks = tuple(sorted(set(self.frameworks), key=lambda item: item.value))
        if not frameworks:
            raise ValueError("frameworks cannot be empty")
        scales = tuple(sorted(set(self.required_scales)))
        if not scales or any(item < 100 or item > 400 for item in scales):
            raise ValueError("required_scales must stay within 100..400")
        themes = tuple(sorted(set(self.required_themes), key=lambda item: item.value))
        if not themes:
            raise ValueError("required_themes cannot be empty")
        object.__setattr__(self, "frameworks", frameworks)
        object.__setattr__(self, "required_scales", scales)
        object.__setattr__(self, "required_themes", themes)

    def canonical(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "frameworks": [item.value for item in self.frameworks],
            "required_scales": list(self.required_scales),
            "required_themes": [item.value for item in self.required_themes],
            "require_keyboard_only": self.require_keyboard_only,
            "require_focus_restoration": self.require_focus_restoration,
            "require_pseudo_localization": self.require_pseudo_localization,
            "require_rtl_intent": self.require_rtl_intent,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class DesktopUiFixture:
    fixture_id: str
    elements: tuple[AccessibleElement, ...]
    localization: LocalizationBundle
    themes: tuple[ThemeContract, ...]
    layout_probes: tuple[DpiLayoutProbe, ...]
    focus_restorations: tuple[FocusRestoration, ...] = ()
    supports_rtl: bool = True

    def __post_init__(self) -> None:
        _stable_id(self.fixture_id, "fixture_id")
        elements = tuple(sorted(self.elements, key=lambda item: item.element_id))
        if not elements or len(elements) > 4096:
            raise ValueError("elements must contain 1..4096 items")
        ids = [item.element_id for item in elements]
        if len(ids) != len(set(ids)):
            raise ValueError("element ids must be unique")
        themes = tuple(sorted(self.themes, key=lambda item: item.mode.value))
        if len({item.mode for item in themes}) != len(themes):
            raise ValueError("theme modes must be unique")
        probes = tuple(sorted(self.layout_probes, key=lambda item: (item.scale_percent, item.width_dip, item.height_dip)))
        restores = tuple(sorted(self.focus_restorations, key=lambda item: item.scenario_id))
        object.__setattr__(self, "elements", elements)
        object.__setattr__(self, "themes", themes)
        object.__setattr__(self, "layout_probes", probes)
        object.__setattr__(self, "focus_restorations", restores)

    def canonical(self) -> dict[str, Any]:
        return {
            "fixture_id": self.fixture_id,
            "elements": [item.canonical() for item in self.elements],
            "localization": self.localization.canonical(),
            "themes": [item.canonical() for item in self.themes],
            "layout_probes": [item.canonical() for item in self.layout_probes],
            "focus_restorations": [item.canonical() for item in self.focus_restorations],
            "supports_rtl": self.supports_rtl,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class QaIssue:
    code: QaIssueCode
    severity: QaSeverity
    subject: str
    detail: str

    def __post_init__(self) -> None:
        _text(self.subject, "subject", maximum=256)
        _text(self.detail, "detail", maximum=1024)

    def canonical(self) -> dict[str, str]:
        return {
            "code": self.code.value,
            "severity": self.severity.value,
            "subject": self.subject,
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class AccessibilityQaReport:
    profile_id: str
    fixture_id: str
    issues: tuple[QaIssue, ...]
    manual_required: bool = False
    manual_reason: str | None = None

    def __post_init__(self) -> None:
        _stable_id(self.profile_id, "profile_id")
        _stable_id(self.fixture_id, "fixture_id")
        issues = tuple(sorted(self.issues, key=lambda item: (item.code.value, item.subject, item.detail)))
        if len(issues) > 4096:
            raise ValueError("issues are not bounded")
        if self.manual_required:
            if self.manual_reason is None:
                raise ValueError("manual_required needs a reason")
            _text(self.manual_reason, "manual_reason", maximum=1024)
        elif self.manual_reason is not None:
            raise ValueError("manual_reason requires manual_required")
        object.__setattr__(self, "issues", issues)

    @property
    def passed(self) -> bool:
        return not self.manual_required and not any(item.severity is QaSeverity.ERROR for item in self.issues)

    def canonical(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "fixture_id": self.fixture_id,
            "passed": self.passed,
            "manual_required": self.manual_required,
            "manual_reason": self.manual_reason,
            "issues": [item.canonical() for item in self.issues],
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


_PSEUDO_MAP = str.maketrans({
    "a": "à", "e": "ë", "i": "ï", "o": "ô", "u": "ü", "y": "ÿ",
    "A": "À", "E": "Ë", "I": "Ï", "O": "Ô", "U": "Ü", "Y": "Ÿ",
})


def pseudo_localize(value: str, *, expansion_ratio: float = 0.30) -> str:
    _text(value, "value")
    if not 0.0 <= expansion_ratio <= 1.0:
        raise ValueError("expansion_ratio must be within 0..1")
    pieces = _PLACEHOLDER_RE.split(value)
    translated = "".join(piece if _PLACEHOLDER_RE.fullmatch(piece or "") else piece.translate(_PSEUDO_MAP) for piece in pieces)
    visible_len = sum(len(piece) for piece in pieces if not _PLACEHOLDER_RE.fullmatch(piece or ""))
    padding = "~" * max(1, int(visible_len * expansion_ratio))
    return f"⟦{translated}{padding}⟧"


def generate_pseudo_catalog(bundle: LocalizationBundle) -> LocalizationCatalog:
    source = bundle.catalog(bundle.default_locale)
    assert source is not None
    entries = tuple(LocalizedString(item.key, pseudo_localize(item.value)) for item in source.entries)
    return LocalizationCatalog(bundle.pseudo_locale, entries, LayoutDirection.LTR)


def _linearized(channel: float) -> float:
    channel /= 255.0
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def contrast_ratio(foreground: tuple[int, int, int], background: tuple[int, int, int]) -> float:
    def luminance(rgb: tuple[int, int, int]) -> float:
        red, green, blue = (_linearized(float(item)) for item in rgb)
        return 0.2126 * red + 0.7152 * green + 0.0722 * blue

    lighter, darker = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def canonical_framework_bindings() -> tuple[FrameworkAccessibilityBinding, ...]:
    return (
        FrameworkAccessibilityBinding(
            DesktopFramework.WPF, "AutomationProperties.Name", "AutomationProperties.HelpText",
            "AutomationPeer/GetAutomationControlType", "Keyboard.Focus/FocusManager",
            ".resx/ResourceManager", "DynamicResource/SystemColors", "device-independent units + WPF DPI APIs",
        ),
        FrameworkAccessibilityBinding(
            DesktopFramework.WINUI3, "AutomationProperties.Name", "AutomationProperties.HelpText",
            "AutomationPeer", "FocusManager/Control.Focus", "MRT Core resources",
            "ThemeResource/HighContrast", "effective pixels + XAML scaling",
        ),
        FrameworkAccessibilityBinding(
            DesktopFramework.AVALONIA, "AutomationProperties.Name", "AutomationProperties.HelpText",
            "AutomationProperties/automation peers", "FocusManager/Focusable",
            "resource dictionaries/localizer service", "ThemeVariant/DynamicResource", "layout scaling/RenderScaling",
        ),
        FrameworkAccessibilityBinding(
            DesktopFramework.QT6, "QAccessibleInterface accessible name", "QAccessibleInterface description",
            "QAccessible::Role", "QWidget/QQuickItem focus APIs", "QTranslator/QCoreApplication::translate",
            "QPalette/system color scheme", "device-independent pixels/devicePixelRatio",
        ),
        FrameworkAccessibilityBinding(
            DesktopFramework.TAURI2, "HTML accessible name/ARIA", "aria-describedby/description",
            "semantic HTML/WAI-ARIA role", "DOM focus/tabindex", "frontend localization resources",
            "CSS prefers-color-scheme/forced-colors", "CSS pixels + webview devicePixelRatio",
        ),
    )


def _issue(code: QaIssueCode, subject: str, detail: str, severity: QaSeverity = QaSeverity.ERROR) -> QaIssue:
    return QaIssue(code, severity, subject, detail)


def validate_accessibility_fixture(
    profile: DesktopAccessibilityProfile,
    fixture: DesktopUiFixture,
    *,
    interactive_runtime_issue: str | None = None,
) -> AccessibilityQaReport:
    issues: list[QaIssue] = []
    ids = {item.element_id for item in fixture.elements}
    default_catalog = fixture.localization.catalog(fixture.localization.default_locale)
    assert default_catalog is not None
    default_keys = set(default_catalog.as_mapping())

    tab_indices: dict[int, str] = {}
    for element in fixture.elements:
        if element.interactive and element.name_key is None:
            issues.append(_issue(QaIssueCode.ACCESSIBLE_NAME_MISSING, element.element_id, "interactive element requires an accessible name resource key"))
        if element.name_key is not None and element.name_key not in default_keys:
            issues.append(_issue(QaIssueCode.LOCALIZATION_KEY_MISSING, element.element_id, f"missing accessible-name key {element.name_key}"))
        if element.description_key is not None and element.description_key not in default_keys:
            issues.append(_issue(QaIssueCode.DESCRIPTION_RESOURCE_MISSING, element.element_id, f"missing description key {element.description_key}"))
        if element.text_key is not None and element.text_key not in default_keys:
            issues.append(_issue(QaIssueCode.LOCALIZATION_KEY_MISSING, element.element_id, f"missing text key {element.text_key}"))
        if element.translatable and element.literal_text is not None:
            issues.append(_issue(QaIssueCode.HARD_CODED_TRANSLATABLE_STRING, element.element_id, "translatable UI text must use a localization resource key"))
        if element.translatable and element.text_key is None and element.name_key is None:
            issues.append(_issue(QaIssueCode.LOCALIZATION_KEY_MISSING, element.element_id, "translatable element has no localization key"))
        if element.tab_index is not None:
            previous = tab_indices.get(element.tab_index)
            if previous is not None:
                issues.append(_issue(QaIssueCode.DUPLICATE_TAB_INDEX, element.element_id, f"tab index {element.tab_index} is also used by {previous}"))
            else:
                tab_indices[element.tab_index] = element.element_id

    if profile.require_keyboard_only:
        interactive_enabled = [item for item in fixture.elements if item.interactive and item.enabled]
        if any(not item.focusable or item.tab_index is None for item in interactive_enabled):
            for item in interactive_enabled:
                if not item.focusable or item.tab_index is None:
                    issues.append(_issue(QaIssueCode.FOCUS_TARGET_INVALID, item.element_id, "enabled interactive element must be keyboard focusable and participate in tab navigation"))

    if profile.require_focus_restoration:
        if not fixture.focus_restorations:
            issues.append(_issue(QaIssueCode.FOCUS_RESTORE_INVALID, fixture.fixture_id, "at least one focus-restoration scenario is required"))
        for scenario in fixture.focus_restorations:
            if scenario.source_element_id not in ids or scenario.temporary_element_id not in ids or scenario.restore_element_id not in ids:
                issues.append(_issue(QaIssueCode.FOCUS_RESTORE_INVALID, scenario.scenario_id, "focus-restoration scenario references an unknown element"))
            if scenario.source_element_id != scenario.restore_element_id:
                issues.append(_issue(QaIssueCode.FOCUS_RESTORE_INVALID, scenario.scenario_id, "focus must restore to the originating control"))

    if profile.require_pseudo_localization:
        pseudo = generate_pseudo_catalog(fixture.localization)
        source_map = default_catalog.as_mapping()
        pseudo_map = pseudo.as_mapping()
        if set(source_map) != set(pseudo_map):
            issues.append(_issue(QaIssueCode.PSEUDO_LOCALIZATION_FAILED, fixture.fixture_id, "pseudo catalog keys diverge from default catalog"))
        for key, source_value in source_map.items():
            value = pseudo_map[key]
            for placeholder in _PLACEHOLDER_RE.findall(source_value):
                if placeholder not in value:
                    issues.append(_issue(QaIssueCode.PSEUDO_LOCALIZATION_FAILED, key, f"placeholder {placeholder} was not preserved"))

    if profile.require_rtl_intent:
        rtl_catalogs = [item for item in fixture.localization.catalogs if item.direction is LayoutDirection.RTL]
        if rtl_catalogs and not fixture.supports_rtl:
            issues.append(_issue(QaIssueCode.RTL_UNSUPPORTED, fixture.fixture_id, "RTL catalog exists but fixture does not declare RTL-safe layout intent"))

    theme_by_mode = {item.mode: item for item in fixture.themes}
    for mode in profile.required_themes:
        theme = theme_by_mode.get(mode)
        if theme is None:
            issues.append(_issue(QaIssueCode.THEME_TOKEN_MISSING, fixture.fixture_id, f"required theme {mode.value} is missing"))
            continue
        if mode is ThemeMode.HIGH_CONTRAST and not theme.uses_system_resources:
            issues.append(_issue(QaIssueCode.THEME_TOKEN_MISSING, fixture.fixture_id, "high-contrast theme must honor system resources"))
        for token in theme.tokens:
            minimum = 3.0 if token.large_text else 4.5
            ratio = contrast_ratio(token.foreground_rgb, token.background_rgb)
            if ratio + 1e-9 < minimum:
                issues.append(_issue(QaIssueCode.CONTRAST_TOO_LOW, f"{mode.value}:{token.token_id}", f"contrast ratio {ratio:.3f} is below {minimum:.1f}:1"))

    probes_by_scale: dict[int, list[DpiLayoutProbe]] = {}
    for probe in fixture.layout_probes:
        probes_by_scale.setdefault(probe.scale_percent, []).append(probe)
        for item in probe.clipped_element_ids:
            issues.append(_issue(QaIssueCode.LAYOUT_CLIPPED, f"{probe.scale_percent}:{item}", "element is clipped at the tested scale"))
        for left, right in probe.overlapping_element_pairs:
            issues.append(_issue(QaIssueCode.LAYOUT_OVERLAP, f"{probe.scale_percent}:{left}:{right}", "elements overlap at the tested scale"))
        for item in probe.hidden_focus_element_ids:
            issues.append(_issue(QaIssueCode.FOCUS_HIDDEN, f"{probe.scale_percent}:{item}", "focused element is hidden at the tested scale"))
    for scale in profile.required_scales:
        if scale not in probes_by_scale:
            issues.append(_issue(QaIssueCode.DPI_PROFILE_INVALID, fixture.fixture_id, f"required scale {scale}% has no layout probe"))

    manual_required = interactive_runtime_issue is not None
    manual_reason = None
    if interactive_runtime_issue is not None:
        manual_reason = _text(interactive_runtime_issue, "interactive_runtime_issue", maximum=1024)

    return AccessibilityQaReport(profile.profile_id, fixture.fixture_id, tuple(issues), manual_required, manual_reason)


def canonical_accessibility_profile() -> DesktopAccessibilityProfile:
    return DesktopAccessibilityProfile(
        "r12.desktop.accessibility.v1",
        tuple(DesktopFramework),
    )


def canonical_accessibility_fixture() -> DesktopUiFixture:
    strings_en = (
        LocalizedString("app.title", "Kodepoia Desktop"),
        LocalizedString("main.build.name", "Build project"),
        LocalizedString("main.build.text", "Build"),
        LocalizedString("main.cancel.name", "Cancel operation"),
        LocalizedString("main.cancel.text", "Cancel"),
        LocalizedString("main.project.name", "Project name"),
        LocalizedString("main.project.text", "Project"),
        LocalizedString("status.ready", "Ready"),
    )
    strings_fr = (
        LocalizedString("app.title", "Kodepoia Bureau"),
        LocalizedString("main.build.name", "Construire le projet"),
        LocalizedString("main.build.text", "Construire"),
        LocalizedString("main.cancel.name", "Annuler l’opération"),
        LocalizedString("main.cancel.text", "Annuler"),
        LocalizedString("main.project.name", "Nom du projet"),
        LocalizedString("main.project.text", "Projet"),
        LocalizedString("status.ready", "Prêt"),
    )
    strings_ar = (
        LocalizedString("app.title", "Kodepoia Desktop"),
        LocalizedString("main.build.name", "بناء المشروع"),
        LocalizedString("main.build.text", "بناء"),
        LocalizedString("main.cancel.name", "إلغاء العملية"),
        LocalizedString("main.cancel.text", "إلغاء"),
        LocalizedString("main.project.name", "اسم المشروع"),
        LocalizedString("main.project.text", "المشروع"),
        LocalizedString("status.ready", "جاهز"),
    )
    localization = LocalizationBundle(
        "en-US", "en-US",
        (
            LocalizationCatalog("en-US", strings_en),
            LocalizationCatalog("fr-FR", strings_fr),
            LocalizationCatalog("ar-SA", strings_ar, LayoutDirection.RTL),
        ),
    )
    elements = (
        AccessibleElement("app.window", AccessibilityRole.WINDOW, False, False, name_key="app.title"),
        AccessibleElement("main.project", AccessibilityRole.TEXTBOX, True, True, 0, "main.project.name", text_key="main.project.text", translatable=True),
        AccessibleElement("main.build", AccessibilityRole.BUTTON, True, True, 1, "main.build.name", text_key="main.build.text", translatable=True),
        AccessibleElement("main.cancel", AccessibilityRole.BUTTON, True, True, 2, "main.cancel.name", text_key="main.cancel.text", translatable=True),
        AccessibleElement("main.status", AccessibilityRole.STATUS, False, False, text_key="status.ready", translatable=True),
    )
    def tokens() -> tuple[ThemeToken, ...]:
        return (
            ThemeToken("primary_text", (0, 0, 0), (255, 255, 255)),
            ThemeToken("inverse_text", (255, 255, 255), (0, 0, 0)),
        )
    themes = (
        ThemeContract(ThemeMode.LIGHT, tokens()),
        ThemeContract(ThemeMode.DARK, tokens()),
        ThemeContract(ThemeMode.HIGH_CONTRAST, tokens(), True),
    )
    probes = tuple(DpiLayoutProbe(scale, 1024, 768) for scale in (100, 125, 150, 200, 250, 300, 400))
    restorations = (FocusRestoration("build.dialog.return", "main.build", "main.cancel", "main.build"),)
    return DesktopUiFixture("r12.canonical.ui", elements, localization, themes, probes, restorations, True)
