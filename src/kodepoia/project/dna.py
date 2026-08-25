from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from enum import Enum, StrEnum
from pathlib import Path
from typing import Any

import yaml

from kodepoia.desktop.contracts import (
    DesktopArchitecture,
    DesktopFramework,
    DesktopOS,
    DesktopPackageKind,
    DesktopTargetProfile,
)
from kodepoia.mobile.contracts import (
    MobileApplicationIdentity,
    MobileFormFactor,
    MobilePackageKind,
    MobilePlatform,
    MobileSourceKind,
    MobileTargetProfile,
)

_MOBILE_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,127}$")
_MOBILE_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){0,3}$")


class ProjectType(StrEnum):
    GAME = "game"
    DESKTOP_APP = "desktop_app"
    MOBILE_APP = "mobile_app"
    TOOL = "tool"
    PLUGIN = "plugin"
    LIBRARY = "library"
    AI_PROJECT = "ai_project"
    OTHER = "other"


class Platform(StrEnum):
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    ANDROID = "android"
    IOS = "ios"
    WEB = "web"
    STEAM_DECK = "steam_deck"
    XR = "xr"


class Dimension(StrEnum):
    D2 = "2d"
    D25 = "2.5d"
    D3 = "3d"
    HYBRID = "hybrid"


class DecisionState(StrEnum):
    YES = "yes"
    NO = "no"
    UNDECIDED = "undecided"


class ApprovalPolicy(StrEnum):
    DENY = "deny"
    ASK = "ask"
    ALLOW_TRUSTED = "allow_trusted"


class MobileNetworkIntent(StrEnum):
    OFFLINE = "offline"
    OPTIONAL = "optional"
    REQUIRED = "required"


class MobileReleaseChannel(StrEnum):
    DEVELOPMENT = "development"
    INTERNAL = "internal"
    BETA = "beta"
    PRODUCTION = "production"


class MobileSigningIntent(StrEnum):
    UNSIGNED = "unsigned"
    DEBUG = "debug"
    TEST = "test"
    DISTRIBUTION = "distribution"


@dataclass(slots=True)
class PerformanceBudget:
    target_fps: int = 60
    min_fps: int = 30
    max_vram_mb: int | None = None
    max_ram_mb: int | None = None
    max_build_mb: int | None = None

    def validate(self) -> None:
        if self.target_fps <= 0 or self.min_fps <= 0:
            raise ValueError("FPS budgets must be positive")
        if self.min_fps > self.target_fps:
            raise ValueError("Minimum FPS cannot exceed target FPS")
        for name in ("max_vram_mb", "max_ram_mb", "max_build_mb"):
            value = getattr(self, name)
            if value is not None and value <= 0:
                raise ValueError(f"{name} must be positive when defined")


@dataclass(slots=True)
class MobileProjectBudget:
    max_package_mb: int = 250
    max_build_seconds: int = 900
    max_device_matrix_runs: int = 16

    def validate(self) -> None:
        limits = {
            "max_package_mb": (self.max_package_mb, 1, 20_480),
            "max_build_seconds": (self.max_build_seconds, 1, 86_400),
            "max_device_matrix_runs": (self.max_device_matrix_runs, 1, 1_000),
        }
        for name, (value, minimum, maximum) in limits.items():
            if not isinstance(value, int) or not minimum <= value <= maximum:
                raise ValueError(f"{name} is outside the bounded mobile budget range")


@dataclass(slots=True)
class DesktopProjectProfile:
    """Backward-compatible desktop intent carried by Project DNA schema v1."""

    framework: DesktopFramework = DesktopFramework.WINUI3
    architecture: DesktopArchitecture = DesktopArchitecture.X64
    package_kind: DesktopPackageKind = DesktopPackageKind.UNPACKAGED
    persistence: DecisionState = DecisionState.UNDECIDED
    ipc: DecisionState = DecisionState.UNDECIDED
    updates: DecisionState = DecisionState.UNDECIDED

    def validate(self, platforms: list[Platform]) -> None:
        desktop_platforms = {Platform.WINDOWS, Platform.LINUX, Platform.MACOS}
        if not platforms or any(item not in desktop_platforms for item in platforms):
            raise ValueError("Desktop projects may target only Windows, Linux or macOS")
        DesktopTargetProfile(
            profile_id="project.desktop",
            framework=self.framework,
            targets=tuple(DesktopOS(item.value) for item in platforms),
            architecture=self.architecture,
            package_kind=self.package_kind,
        )
        for name in ("persistence", "ipc", "updates"):
            if not isinstance(getattr(self, name), DecisionState):
                raise ValueError(f"Desktop {name} must use DecisionState")


@dataclass(slots=True)
class MobileProjectProfile:
    """Optional R13 mobile intent; absence preserves pre-R13 schema-v1 semantics."""

    source_kind: MobileSourceKind = MobileSourceKind.NATIVE
    form_factors: tuple[MobileFormFactor, ...] = (MobileFormFactor.PHONE,)
    android_application_id: str | None = None
    android_min_api: int | None = None
    android_target_api: int | None = None
    apple_bundle_id: str | None = None
    apple_min_version: str | None = None
    apple_target_version: str | None = None
    package_kinds: tuple[MobilePackageKind, ...] = ()
    permissions: tuple[str, ...] = ()
    requested_capabilities: tuple[str, ...] = ()
    network_intent: MobileNetworkIntent = MobileNetworkIntent.OFFLINE
    release_channel: MobileReleaseChannel = MobileReleaseChannel.DEVELOPMENT
    signing_intent: MobileSigningIntent = MobileSigningIntent.UNSIGNED
    budget: MobileProjectBudget = field(default_factory=MobileProjectBudget)

    @staticmethod
    def _bounded_names(values: tuple[str, ...], *, field_name: str) -> tuple[str, ...]:
        normalized = tuple(sorted(set(values)))
        if len(normalized) > 64:
            raise ValueError(f"{field_name} must contain at most 64 entries")
        for value in normalized:
            if _MOBILE_NAME_RE.fullmatch(value) is None:
                raise ValueError(f"invalid mobile {field_name} entry: {value!r}")
        return normalized

    @staticmethod
    def _version_tuple(value: str) -> tuple[int, ...]:
        if _MOBILE_VERSION_RE.fullmatch(value) is None:
            raise ValueError("Apple platform versions must be bounded numeric versions")
        return tuple(int(part) for part in value.split("."))

    def validate(
        self,
        platforms: list[Platform],
        project_type: ProjectType,
        engine: str | None,
    ) -> None:
        selected_mobile = {item for item in platforms if item in {Platform.ANDROID, Platform.IOS}}
        if not selected_mobile:
            raise ValueError("Mobile profile requires at least one Android or iOS target")

        if self.source_kind is MobileSourceKind.NATIVE:
            if project_type is not ProjectType.MOBILE_APP:
                raise ValueError("Native mobile source is valid only for mobile_app projects")
        elif self.source_kind is MobileSourceKind.GODOT_EXPORT:
            if project_type is not ProjectType.GAME:
                raise ValueError("Godot mobile export is valid only for game projects")
            if not engine or engine.strip().casefold() != "godot":
                raise ValueError("Godot mobile export requires the Godot engine")

        if project_type is ProjectType.MOBILE_APP:
            if any(item not in {Platform.ANDROID, Platform.IOS} for item in platforms):
                raise ValueError("Mobile apps may target only Android and/or iOS")
            if engine is not None:
                raise ValueError("Native mobile apps do not define a game engine")

        factors = tuple(sorted(set(self.form_factors), key=lambda item: item.value))
        if not factors:
            raise ValueError("Mobile form_factors must contain at least one item")
        self.form_factors = factors

        kinds = tuple(sorted(set(self.package_kinds), key=lambda item: item.value))
        if not kinds:
            defaults: list[MobilePackageKind] = []
            if Platform.ANDROID in selected_mobile:
                defaults.append(MobilePackageKind.AAB)
            if Platform.IOS in selected_mobile:
                defaults.append(MobilePackageKind.APP)
            kinds = tuple(defaults)
        allowed_kinds: set[MobilePackageKind] = set()
        if Platform.ANDROID in selected_mobile:
            allowed_kinds.update({MobilePackageKind.APK, MobilePackageKind.AAB})
        if Platform.IOS in selected_mobile:
            allowed_kinds.update(
                {MobilePackageKind.APP, MobilePackageKind.XCARCHIVE, MobilePackageKind.IPA}
            )
        if any(item not in allowed_kinds for item in kinds):
            raise ValueError("Mobile package intent does not match selected target platforms")
        self.package_kinds = kinds

        if Platform.ANDROID in selected_mobile:
            if self.android_application_id is None:
                raise ValueError("Android target requires android_application_id")
            MobileApplicationIdentity(
                identity_id="project.android",
                platform=MobilePlatform.ANDROID,
                package_identifier=self.android_application_id,
            )
            if (
                not isinstance(self.android_min_api, int)
                or not isinstance(self.android_target_api, int)
                or not 1 <= self.android_min_api <= self.android_target_api <= 1000
            ):
                raise ValueError("Android target requires bounded min/target API intent")
            MobileTargetProfile(
                profile_id="project.android",
                platform=MobilePlatform.ANDROID,
                form_factors=factors,
                source_kind=self.source_kind,
                minimum_platform_version=str(self.android_min_api),
                target_api_level=self.android_target_api,
                package_kinds=tuple(
                    item for item in kinds if item in {MobilePackageKind.APK, MobilePackageKind.AAB}
                ),
            )
        elif any(
            value is not None
            for value in (self.android_application_id, self.android_min_api, self.android_target_api)
        ):
            raise ValueError("Android intent cannot be set without an Android target")

        if Platform.IOS in selected_mobile:
            if self.apple_bundle_id is None:
                raise ValueError("iOS target requires apple_bundle_id")
            MobileApplicationIdentity(
                identity_id="project.ios",
                platform=MobilePlatform.IOS,
                package_identifier=self.apple_bundle_id,
            )
            if self.apple_min_version is None or self.apple_target_version is None:
                raise ValueError("iOS target requires minimum and target OS version intent")
            minimum = self._version_tuple(self.apple_min_version)
            target = self._version_tuple(self.apple_target_version)
            if minimum > target:
                raise ValueError("Apple minimum version cannot exceed target version")
            MobileTargetProfile(
                profile_id="project.ios",
                platform=MobilePlatform.IOS,
                form_factors=factors,
                source_kind=self.source_kind,
                minimum_platform_version=self.apple_min_version,
                package_kinds=tuple(
                    item
                    for item in kinds
                    if item
                    in {MobilePackageKind.APP, MobilePackageKind.XCARCHIVE, MobilePackageKind.IPA}
                ),
            )
        elif any(
            value is not None
            for value in (self.apple_bundle_id, self.apple_min_version, self.apple_target_version)
        ):
            raise ValueError("Apple intent cannot be set without an iOS target")

        self.permissions = self._bounded_names(self.permissions, field_name="permissions")
        self.requested_capabilities = self._bounded_names(
            self.requested_capabilities, field_name="capabilities"
        )
        self.budget.validate()


@dataclass(slots=True)
class ProjectDNA:
    schema_version: int
    name: str
    project_type: ProjectType
    platforms: list[Platform]
    engine: str | None = None
    engine_version: str | None = None
    dimension: Dimension | None = None
    genres: list[str] = field(default_factory=list)
    inputs: list[str] = field(default_factory=list)
    graphics_style: str | None = None
    online: DecisionState = DecisionState.NO
    multiplayer: DecisionState = DecisionState.NO
    performance: dict[str, PerformanceBudget] = field(default_factory=dict)
    tools: dict[str, bool] = field(default_factory=dict)
    download_policy: ApprovalPolicy = ApprovalPolicy.ASK
    install_policy: ApprovalPolicy = ApprovalPolicy.ASK
    lineage: dict[str, str] = field(default_factory=dict)
    capabilities: dict[str, DecisionState] = field(default_factory=dict)
    desktop: DesktopProjectProfile | None = None
    mobile: MobileProjectProfile | None = None

    def validate(self) -> None:
        if self.schema_version != 1:
            raise ValueError(f"Unsupported Project DNA schema version: {self.schema_version}")
        if not self.name.strip():
            raise ValueError("Project name is required")
        if not self.platforms:
            raise ValueError("At least one target platform is required")
        if len(self.platforms) != len(set(self.platforms)):
            raise ValueError("Target platforms must be unique")
        if self.project_type is ProjectType.GAME and not self.dimension:
            raise ValueError("Game projects require a dimension")
        if self.project_type is not ProjectType.GAME and self.dimension is not None:
            raise ValueError("Only game projects can define a game dimension")
        if self.project_type is ProjectType.DESKTOP_APP:
            if self.desktop is not None:
                self.desktop.validate(self.platforms)
        elif self.desktop is not None:
            raise ValueError("Desktop profile is valid only for desktop_app projects")

        selected_mobile = {Platform.ANDROID, Platform.IOS} & set(self.platforms)
        if self.mobile is not None:
            self.mobile.validate(self.platforms, self.project_type, self.engine)
        elif self.project_type is ProjectType.MOBILE_APP:
            raise ValueError("mobile_app projects require an explicit mobile profile")

        normalized_inputs = {item.lower() for item in self.inputs}
        if not selected_mobile:
            forbidden = {"touch", "gyro", "accelerometer"} & normalized_inputs
            if forbidden:
                raise ValueError(
                    f"Mobile-only inputs selected without mobile platform: {sorted(forbidden)}"
                )
        if Platform.XR not in self.platforms and "motion_controllers" in normalized_inputs:
            raise ValueError("XR motion controllers selected without XR target")

        target_platforms = {platform.value for platform in self.platforms}
        for platform, budget in self.performance.items():
            if platform not in target_platforms:
                raise ValueError(f"Performance budget defined for non-target platform: {platform}")
            budget.validate()

        for key, value in self.capabilities.items():
            if not key.strip():
                raise ValueError("Capability names cannot be empty")
            if not isinstance(value, DecisionState):
                raise ValueError(f"Capability {key} must use DecisionState")
        for key, value in self.tools.items():
            if not key.strip() or not isinstance(value, bool):
                raise ValueError("Tool configuration must map non-empty names to booleans")
        for key, value in self.lineage.items():
            if not key.strip() or not isinstance(value, str):
                raise ValueError("Lineage must map non-empty names to strings")

    def to_dict(self) -> dict[str, Any]:
        self.validate()

        def primitive(value: Any) -> Any:
            if isinstance(value, Enum):
                return value.value
            if isinstance(value, dict):
                return {str(primitive(key)): primitive(item) for key, item in value.items()}
            if isinstance(value, (list, tuple)):
                return [primitive(item) for item in value]
            return value

        payload = primitive(asdict(self))
        if self.desktop is None:
            payload.pop("desktop", None)
        if self.mobile is None:
            payload.pop("mobile", None)
        return payload

    def save(self, path: Path) -> None:
        self.validate()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            yaml.safe_dump(self.to_dict(), sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> "ProjectDNA":
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("Project DNA must be a YAML object")
        performance = {
            key: PerformanceBudget(**value) for key, value in raw.get("performance", {}).items()
        }
        raw_desktop = raw.get("desktop")
        desktop = None
        if raw_desktop is not None:
            if not isinstance(raw_desktop, dict):
                raise ValueError("Desktop Project DNA profile must be an object")
            desktop = DesktopProjectProfile(
                framework=DesktopFramework(raw_desktop.get("framework", "winui3")),
                architecture=DesktopArchitecture(raw_desktop.get("architecture", "x64")),
                package_kind=DesktopPackageKind(raw_desktop.get("package_kind", "unpackaged")),
                persistence=DecisionState(raw_desktop.get("persistence", "undecided")),
                ipc=DecisionState(raw_desktop.get("ipc", "undecided")),
                updates=DecisionState(raw_desktop.get("updates", "undecided")),
            )

        raw_mobile = raw.get("mobile")
        mobile = None
        if raw_mobile is not None:
            if not isinstance(raw_mobile, dict):
                raise ValueError("Mobile Project DNA profile must be an object")
            raw_budget = raw_mobile.get("budget", {})
            if not isinstance(raw_budget, dict):
                raise ValueError("Mobile Project DNA budget must be an object")
            mobile = MobileProjectProfile(
                source_kind=MobileSourceKind(raw_mobile.get("source_kind", "native")),
                form_factors=tuple(
                    MobileFormFactor(item)
                    for item in raw_mobile.get("form_factors", ["phone"])
                ),
                android_application_id=raw_mobile.get("android_application_id"),
                android_min_api=raw_mobile.get("android_min_api"),
                android_target_api=raw_mobile.get("android_target_api"),
                apple_bundle_id=raw_mobile.get("apple_bundle_id"),
                apple_min_version=raw_mobile.get("apple_min_version"),
                apple_target_version=raw_mobile.get("apple_target_version"),
                package_kinds=tuple(
                    MobilePackageKind(item) for item in raw_mobile.get("package_kinds", [])
                ),
                permissions=tuple(str(item) for item in raw_mobile.get("permissions", [])),
                requested_capabilities=tuple(
                    str(item) for item in raw_mobile.get("requested_capabilities", [])
                ),
                network_intent=MobileNetworkIntent(
                    raw_mobile.get("network_intent", "offline")
                ),
                release_channel=MobileReleaseChannel(
                    raw_mobile.get("release_channel", "development")
                ),
                signing_intent=MobileSigningIntent(
                    raw_mobile.get("signing_intent", "unsigned")
                ),
                budget=MobileProjectBudget(**raw_budget),
            )

        dna = cls(
            schema_version=int(raw["schema_version"]),
            name=str(raw["name"]),
            project_type=ProjectType(raw["project_type"]),
            platforms=[Platform(item) for item in raw["platforms"]],
            engine=raw.get("engine"),
            engine_version=raw.get("engine_version"),
            dimension=Dimension(raw["dimension"]) if raw.get("dimension") else None,
            genres=list(raw.get("genres", [])),
            inputs=list(raw.get("inputs", [])),
            graphics_style=raw.get("graphics_style"),
            online=DecisionState(raw.get("online", "no")),
            multiplayer=DecisionState(raw.get("multiplayer", "no")),
            performance=performance,
            tools={str(key): bool(value) for key, value in raw.get("tools", {}).items()},
            download_policy=ApprovalPolicy(raw.get("download_policy", "ask")),
            install_policy=ApprovalPolicy(raw.get("install_policy", "ask")),
            lineage={str(key): str(value) for key, value in raw.get("lineage", {}).items()},
            capabilities={
                str(key): DecisionState(value)
                for key, value in raw.get("capabilities", {}).items()
            },
            desktop=desktop,
            mobile=mobile,
        )
        dna.validate()
        return dna
