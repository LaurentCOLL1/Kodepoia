from __future__ import annotations

from collections.abc import Iterable

from kodepoia.quality.accessibility import (
    AccessibilityReport,
    AccessibilityResult,
    AccessibilitySeverity,
    AccessibilityStatus,
    KodeAccessibility,
)


ACCESSIBILITY_REQUIRED_PROPERTY = "kodepoiaAccessibilityRequired"
DESCRIPTION_REQUIRED_PROPERTY = "kodepoiaAccessibilityDescriptionRequired"

MAIN_REQUIRED_CONTROL_IDS = (
    "mainNavigation",
    "newProjectButton",
    "killSwitchButton",
    "killSwitchResetButton",
)

WIZARD_REQUIRED_CONTROL_IDS = (
    "wizardTabs",
    "projectName",
    "projectDirectory",
    "browseProjectDirectoryButton",
    "projectType",
    "engine",
    "engineVersion",
    "dimension",
    "genres",
    "graphicsStyle",
    "input_keyboard",
    "input_mouse",
    "input_gamepad",
    "input_touch",
    "input_gyro",
    "input_accelerometer",
    "input_motion_controllers",
    "online",
    "multiplayer",
    "platform_windows",
    "platform_linux",
    "platform_macos",
    "platform_android",
    "platform_ios",
    "platform_web",
    "platform_steam_deck",
    "platform_xr",
    "performanceBudgets",
    "budget_windows_target_fps",
    "budget_windows_min_fps",
    "budget_windows_vram_mb",
    "budget_windows_ram_mb",
    "budget_windows_build_mb",
    "tool_ollama",
    "tool_blender",
    "tool_comfyui",
    "tool_research",
    "downloadPolicy",
    "installPolicy",
    "capability_procedural_generation",
    "capability_modding",
    "capability_voice",
    "capability_accessibility_first",
    "lineageParent",
    "lineageFranchise",
    "lineageTemplate",
    "productDocumentType",
    "productVision",
    "productSummary",
    "productGoals",
    "successMetrics",
    "productConstraints",
    "productMvp",
    "productOutOfScope",
    "productRequirements",
    "addRequirementButton",
    "removeRequirementButton",
    "createProjectButton",
    "cancelProjectButton",
)


def mark_accessible(
    widget,
    *,
    object_name: str,
    name: str,
    description: str = "",
    description_required: bool = False,
):
    if not object_name.strip():
        raise ValueError("Accessible widgets require a stable object name")
    if not name.strip():
        raise ValueError("Accessible widgets require a non-empty accessible name")
    widget.setObjectName(object_name)
    widget.setAccessibleName(name)
    widget.setAccessibleDescription(description)
    widget.setProperty(ACCESSIBILITY_REQUIRED_PROPERTY, True)
    widget.setProperty(DESCRIPTION_REQUIRED_PROPERTY, bool(description_required))
    if description_required and not description.strip():
        raise ValueError("Description-required accessible widgets need a description")
    return widget


def _enum_name(value) -> str:
    name = getattr(value, "name", None)
    return str(name if name is not None else value)


def _enum_int(value) -> int:
    raw = getattr(value, "value", None)
    return int(raw) if raw is not None else int(value)


def _find_widget(root, object_name: str):
    from PySide6.QtWidgets import QWidget

    if root.objectName() == object_name:
        return root
    return root.findChild(QWidget, object_name)


def _marked_widgets(root) -> list:
    from PySide6.QtWidgets import QWidget

    widgets = []
    if bool(root.property(ACCESSIBILITY_REQUIRED_PROPERTY)):
        widgets.append(root)
    widgets.extend(
        widget
        for widget in root.findChildren(QWidget)
        if bool(widget.property(ACCESSIBILITY_REQUIRED_PROPERTY))
    )
    unique = {}
    for widget in widgets:
        name = widget.objectName().strip()
        if name:
            unique[name] = widget
    return [unique[name] for name in sorted(unique)]


def _discover_unregistered_owned_controls(root) -> list:
    from PySide6.QtWidgets import (
        QAbstractButton,
        QAbstractItemView,
        QComboBox,
        QLineEdit,
        QPlainTextEdit,
        QSpinBox,
        QTabWidget,
        QWidget,
    )

    interactive_types = (
        QAbstractButton,
        QAbstractItemView,
        QComboBox,
        QLineEdit,
        QPlainTextEdit,
        QSpinBox,
        QTabWidget,
    )
    unregistered = []
    for widget in root.findChildren(QWidget):
        if not isinstance(widget, interactive_types):
            continue
        object_name = widget.objectName().strip()
        if not object_name or object_name.startswith("qt_"):
            continue
        if bool(widget.property(ACCESSIBILITY_REQUIRED_PROPERTY)):
            continue
        unregistered.append(widget)
    return sorted(unregistered, key=lambda widget: widget.objectName())


def _audit_widget(widget) -> list[AccessibilityResult]:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QAccessible

    target_id = widget.objectName().strip()
    results: list[AccessibilityResult] = []

    explicit_name = widget.accessibleName().strip()
    results.append(
        AccessibilityResult(
            rule_id="qt.name.explicit",
            target_id=target_id,
            status=AccessibilityStatus.PASS if explicit_name else AccessibilityStatus.FAIL,
            severity=AccessibilitySeverity.MAJOR,
            summary=(
                f"Explicit accessible name: {explicit_name}"
                if explicit_name
                else "Interactive control has no explicit accessible name"
            ),
            evidence={"accessible_name": explicit_name},
            blocking=not bool(explicit_name),
        )
    )

    description_required = bool(widget.property(DESCRIPTION_REQUIRED_PROPERTY))
    explicit_description = widget.accessibleDescription().strip()
    if description_required:
        results.append(
            AccessibilityResult(
                rule_id="qt.description.required",
                target_id=target_id,
                status=(
                    AccessibilityStatus.PASS
                    if explicit_description
                    else AccessibilityStatus.FAIL
                ),
                severity=AccessibilitySeverity.MAJOR,
                summary=(
                    "Required accessible description is present"
                    if explicit_description
                    else "Required accessible description is missing"
                ),
                evidence={"accessible_description": explicit_description},
                blocking=not bool(explicit_description),
            )
        )
    else:
        results.append(
            AccessibilityResult(
                rule_id="qt.description.required",
                target_id=target_id,
                status=AccessibilityStatus.NOT_APPLICABLE,
                severity=AccessibilitySeverity.INFO,
                summary="No extra description is required for this self-describing control",
                evidence={"accessible_description": explicit_description},
                applicability_reason="Control contract does not require an additional description",
            )
        )

    if not widget.isEnabled():
        results.append(
            AccessibilityResult(
                rule_id="qt.keyboard.tab_focus",
                target_id=target_id,
                status=AccessibilityStatus.NOT_APPLICABLE,
                severity=AccessibilitySeverity.MAJOR,
                summary="Control is disabled in the audited adaptive state",
                evidence={"enabled": False, "visible": widget.isVisible()},
                applicability_reason="Disabled controls are not keyboard-operable in this state",
            )
        )
    elif not widget.isVisible():
        results.append(
            AccessibilityResult(
                rule_id="qt.keyboard.tab_focus",
                target_id=target_id,
                status=AccessibilityStatus.NOT_APPLICABLE,
                severity=AccessibilitySeverity.MAJOR,
                summary="Control is not visible in the audited adaptive state",
                evidence={"enabled": True, "visible": False},
                applicability_reason="Hidden controls are not keyboard-operable in this state",
            )
        )
    else:
        policy_value = _enum_int(widget.focusPolicy())
        tab_value = _enum_int(Qt.FocusPolicy.TabFocus)
        tab_focus = bool(policy_value & tab_value)
        results.append(
            AccessibilityResult(
                rule_id="qt.keyboard.tab_focus",
                target_id=target_id,
                status=AccessibilityStatus.PASS if tab_focus else AccessibilityStatus.FAIL,
                severity=AccessibilitySeverity.CRITICAL,
                summary=(
                    "Visible enabled control participates in keyboard tab focus"
                    if tab_focus
                    else "Visible enabled control is not reachable through keyboard tab focus"
                ),
                evidence={
                    "enabled": True,
                    "visible": True,
                    "focus_policy": _enum_name(widget.focusPolicy()),
                },
                blocking=not tab_focus,
            )
        )

    interface = QAccessible.queryAccessibleInterface(widget)
    if interface is None:
        results.extend(
            [
                AccessibilityResult(
                    rule_id="qt.accessible.interface",
                    target_id=target_id,
                    status=AccessibilityStatus.FAIL,
                    severity=AccessibilitySeverity.CRITICAL,
                    summary="Qt did not expose a QAccessibleInterface for the control",
                    evidence={"interface": None},
                    blocking=True,
                ),
                AccessibilityResult(
                    rule_id="qt.accessible.role",
                    target_id=target_id,
                    status=AccessibilityStatus.UNKNOWN,
                    severity=AccessibilitySeverity.CRITICAL,
                    summary="Accessible role cannot be inspected without an interface",
                    evidence={},
                ),
                AccessibilityResult(
                    rule_id="qt.accessible.state",
                    target_id=target_id,
                    status=AccessibilityStatus.UNKNOWN,
                    severity=AccessibilitySeverity.MAJOR,
                    summary="Accessible state cannot be inspected without an interface",
                    evidence={},
                ),
            ]
        )
        return results

    interface_name = interface.text(QAccessible.Text.Name).strip()
    role = interface.role()
    state = interface.state()
    results.append(
        AccessibilityResult(
            rule_id="qt.accessible.interface",
            target_id=target_id,
            status=AccessibilityStatus.PASS if interface_name else AccessibilityStatus.FAIL,
            severity=AccessibilitySeverity.CRITICAL,
            summary=(
                f"Qt accessibility interface exposes name: {interface_name}"
                if interface_name
                else "Qt accessibility interface exists but exposes no name"
            ),
            evidence={"interface_name": interface_name},
            blocking=not bool(interface_name),
        )
    )
    role_valid = role != QAccessible.Role.NoRole
    results.append(
        AccessibilityResult(
            rule_id="qt.accessible.role",
            target_id=target_id,
            status=AccessibilityStatus.PASS if role_valid else AccessibilityStatus.FAIL,
            severity=AccessibilitySeverity.CRITICAL,
            summary=(
                f"Accessible role exposed: {_enum_name(role)}"
                if role_valid
                else "Accessible role is NoRole"
            ),
            evidence={"role": _enum_name(role)},
            blocking=not role_valid,
        )
    )
    results.append(
        AccessibilityResult(
            rule_id="qt.accessible.state",
            target_id=target_id,
            status=AccessibilityStatus.PASS,
            severity=AccessibilitySeverity.MAJOR,
            summary="Accessible state is queryable",
            evidence={
                "focusable": bool(getattr(state, "focusable", False)),
                "focused": bool(getattr(state, "focused", False)),
                "disabled": bool(getattr(state, "disabled", False)),
                "invisible": bool(getattr(state, "invisible", False)),
            },
        )
    )
    return results


def audit_qt_surface(
    root,
    *,
    surface: str,
    expected_ids: Iterable[str],
    generated_at: str | None = None,
) -> AccessibilityReport:
    results: list[AccessibilityResult] = []
    expected = tuple(expected_ids)
    expected_set = set(expected)

    for object_name in expected:
        widget = _find_widget(root, object_name)
        if widget is None:
            results.append(
                AccessibilityResult(
                    rule_id="qt.control.present",
                    target_id=object_name,
                    status=AccessibilityStatus.FAIL,
                    severity=AccessibilitySeverity.CRITICAL,
                    summary="Required interactive control is missing from the surface",
                    evidence={},
                    blocking=True,
                )
            )
            continue
        results.append(
            AccessibilityResult(
                rule_id="qt.control.present",
                target_id=object_name,
                status=AccessibilityStatus.PASS,
                severity=AccessibilitySeverity.INFO,
                summary="Required interactive control is present",
                evidence={"class": type(widget).__name__},
            )
        )

    marked = _marked_widgets(root)
    marked_names = {widget.objectName() for widget in marked}
    for object_name in sorted(marked_names - expected_set):
        results.append(
            AccessibilityResult(
                rule_id="qt.control.present",
                target_id=object_name,
                status=AccessibilityStatus.PASS,
                severity=AccessibilitySeverity.INFO,
                summary="Registered dynamic interactive control is present",
                evidence={"dynamic": True},
            )
        )

    for widget in marked:
        results.extend(_audit_widget(widget))

    for widget in _discover_unregistered_owned_controls(root):
        results.append(
            AccessibilityResult(
                rule_id="qt.control.registered",
                target_id=widget.objectName(),
                status=AccessibilityStatus.FAIL,
                severity=AccessibilitySeverity.MAJOR,
                summary="Named interactive control is not registered in the accessibility contract",
                evidence={"class": type(widget).__name__},
                blocking=True,
            )
        )

    return KodeAccessibility.evaluate(
        results,
        surface=surface,
        generated_at=generated_at,
    )
