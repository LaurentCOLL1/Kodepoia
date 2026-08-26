from __future__ import annotations

from .apple_testing import AppleXCTestPlanDefinition, render_xctest_overlay as _render_overlay

_RELEASE_PREFIX = (
    "\t\t010000000000000000000004 /* Release */ = {\n"
    "\t\t\tisa = XCBuildConfiguration;\n"
    "\t\t\tbuildSettings = {\n"
    "\t\t\t\tCURRENT_PROJECT_VERSION = 1;\n"
    "\t\t\t\tGENERATE_INFOPLIST_FILE = NO;"
)
_RELEASE_REPLACEMENT = (
    "\t\t010000000000000000000004 /* Release */ = {\n"
    "\t\t\tisa = XCBuildConfiguration;\n"
    "\t\t\tbuildSettings = {\n"
    "\t\t\t\tCURRENT_PROJECT_VERSION = 1;\n"
    "\t\t\t\tENABLE_TESTABILITY = NO;\n"
    "\t\t\t\tGENERATE_INFOPLIST_FILE = NO;"
)
_COMMON_MARKER = "\t\t\t\tCURRENT_PROJECT_VERSION = 1;\n\t\t\t\tGENERATE_INFOPLIST_FILE = NO;"


def render_xctest_overlay(
    *,
    pbxproj: str,
    scheme: str,
    plan: AppleXCTestPlanDefinition,
) -> dict[str, str]:
    """Apply the R13.11 XCTest overlay only to an exact canonical R13.9 project shape.

    R13.9 intentionally has identical Debug/Release version/plist lines. The base
    overlay must change only Debug to ENABLE_TESTABILITY=YES, so this adapter first
    marks the canonical Release configuration as explicitly non-testable. Any
    renderer drift fails closed instead of selecting a build setting by position.
    """

    if pbxproj.count(_COMMON_MARKER) != 2:
        raise ValueError("canonical R13.9 app configuration cardinality drift detected")
    if pbxproj.count(_RELEASE_PREFIX) != 1:
        raise ValueError("canonical R13.9 Release configuration drift detected")
    guarded = pbxproj.replace(_RELEASE_PREFIX, _RELEASE_REPLACEMENT, 1)
    return _render_overlay(pbxproj=guarded, scheme=scheme, plan=plan)
