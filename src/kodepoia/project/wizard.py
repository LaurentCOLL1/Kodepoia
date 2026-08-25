from __future__ import annotations

import re
from dataclasses import dataclass, field

from kodepoia.desktop.contracts import (
    DesktopArchitecture,
    DesktopFramework,
    DesktopPackageKind,
)
from kodepoia.mobile.contracts import MobileFormFactor, MobilePackageKind, MobileSourceKind
from kodepoia.project.dna import (
    ApprovalPolicy,
    DecisionState,
    DesktopProjectProfile,
    Dimension,
    MobileNetworkIntent,
    MobileProjectBudget,
    MobileProjectProfile,
    MobileReleaseChannel,
    MobileSigningIntent,
    PerformanceBudget,
    Platform,
    ProjectDNA,
    ProjectType,
)


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "", value.casefold())
    return normalized or "app"


@dataclass(slots=True)
class ProjectWizardState:
    name: str = ""
    project_type: ProjectType = ProjectType.GAME
    platforms: list[Platform] = field(default_factory=lambda: [Platform.WINDOWS])
    engine: str | None = "Godot"
    engine_version: str | None = "4.7"
    dimension: Dimension | None = Dimension.D3
    genres: list[str] = field(default_factory=list)
    inputs: list[str] = field(default_factory=lambda: ["keyboard", "mouse"])
    graphics_style: str | None = None
    online: DecisionState = DecisionState.NO
    multiplayer: DecisionState = DecisionState.NO
    performance: dict[str, PerformanceBudget] = field(default_factory=dict)
    tools: dict[str, bool] = field(
        default_factory=lambda: {
            "ollama": True,
            "blender": False,
            "comfyui": False,
            "research": False,
        }
    )
    download_policy: ApprovalPolicy = ApprovalPolicy.ASK
    install_policy: ApprovalPolicy = ApprovalPolicy.ASK
    lineage: dict[str, str] = field(default_factory=dict)
    capabilities: dict[str, DecisionState] = field(default_factory=dict)
    desktop_framework: DesktopFramework = DesktopFramework.WINUI3
    desktop_architecture: DesktopArchitecture = DesktopArchitecture.X64
    desktop_package_kind: DesktopPackageKind = DesktopPackageKind.UNPACKAGED
    desktop_persistence: DecisionState = DecisionState.UNDECIDED
    desktop_ipc: DecisionState = DecisionState.UNDECIDED
    desktop_updates: DecisionState = DecisionState.UNDECIDED
    mobile_source_kind: MobileSourceKind | None = None
    mobile_form_factors: tuple[MobileFormFactor, ...] = (MobileFormFactor.PHONE,)
    android_application_id: str | None = None
    android_min_api: int = 26
    android_target_api: int = 36
    apple_bundle_id: str | None = None
    apple_min_version: str = "16.0"
    apple_target_version: str = "26.0"
    mobile_package_kinds: tuple[MobilePackageKind, ...] = ()
    mobile_permissions: tuple[str, ...] = ()
    mobile_requested_capabilities: tuple[str, ...] = ()
    mobile_network_intent: MobileNetworkIntent = MobileNetworkIntent.OFFLINE
    mobile_release_channel: MobileReleaseChannel = MobileReleaseChannel.DEVELOPMENT
    mobile_signing_intent: MobileSigningIntent = MobileSigningIntent.UNSIGNED
    mobile_budget: MobileProjectBudget = field(default_factory=MobileProjectBudget)

    def relevant_questions(self) -> tuple[str, ...]:
        questions = [
            "project_type",
            "platforms",
            "performance",
            "tools",
            "download_policy",
            "install_policy",
            "lineage",
            "capabilities",
        ]
        if self.project_type is ProjectType.GAME:
            questions += [
                "engine",
                "engine_version",
                "dimension",
                "genres",
                "graphics_style",
                "inputs",
                "online",
                "multiplayer",
            ]
        if self.project_type is ProjectType.DESKTOP_APP:
            questions += [
                "desktop_framework",
                "desktop_architecture",
                "desktop_package_kind",
                "desktop_persistence",
                "desktop_ipc",
                "desktop_updates",
            ]
        if {Platform.ANDROID, Platform.IOS} & set(self.platforms):
            questions += [
                "mobile_source_kind",
                "mobile_form_factors",
                "mobile_identity",
                "mobile_platform_versions",
                "mobile_permissions",
                "mobile_requested_capabilities",
                "mobile_network_intent",
                "mobile_package_kinds",
                "mobile_release_channel",
                "mobile_signing_intent",
                "mobile_budget",
            ]
            if self.project_type is ProjectType.GAME:
                questions += ["touch", "gyro", "accelerometer", "mobile_performance"]
        if Platform.XR in self.platforms:
            questions += ["openxr", "motion_controllers", "xr_performance"]
        return tuple(questions)

    def _performance_for_targets(self) -> dict[str, PerformanceBudget]:
        result: dict[str, PerformanceBudget] = {}
        for platform in self.platforms:
            existing = self.performance.get(platform.value)
            result[platform.value] = existing or PerformanceBudget()
        return result

    def _desktop_profile(self) -> DesktopProjectProfile | None:
        if self.project_type is not ProjectType.DESKTOP_APP:
            return None
        return DesktopProjectProfile(
            framework=self.desktop_framework,
            architecture=self.desktop_architecture,
            package_kind=self.desktop_package_kind,
            persistence=self.desktop_persistence,
            ipc=self.desktop_ipc,
            updates=self.desktop_updates,
        )

    def _mobile_profile(self) -> MobileProjectProfile | None:
        selected = {Platform.ANDROID, Platform.IOS} & set(self.platforms)
        if not selected:
            if self.project_type is ProjectType.MOBILE_APP:
                raise ValueError("mobile_app requires Android and/or iOS")
            return None

        source = self.mobile_source_kind
        if source is None:
            source = (
                MobileSourceKind.GODOT_EXPORT
                if self.project_type is ProjectType.GAME
                else MobileSourceKind.NATIVE
            )
        suffix = _slug(self.name)
        android_id = self.android_application_id
        apple_id = self.apple_bundle_id
        if Platform.ANDROID in selected and not android_id:
            android_id = f"org.kodepoia.{suffix}"
        if Platform.IOS in selected and not apple_id:
            apple_id = f"org.kodepoia.{suffix}"

        package_kinds = self.mobile_package_kinds
        if not package_kinds:
            defaults: list[MobilePackageKind] = []
            if Platform.ANDROID in selected:
                defaults.append(MobilePackageKind.AAB)
            if Platform.IOS in selected:
                defaults.append(MobilePackageKind.APP)
            package_kinds = tuple(defaults)

        return MobileProjectProfile(
            source_kind=source,
            form_factors=tuple(self.mobile_form_factors),
            android_application_id=android_id if Platform.ANDROID in selected else None,
            android_min_api=self.android_min_api if Platform.ANDROID in selected else None,
            android_target_api=self.android_target_api if Platform.ANDROID in selected else None,
            apple_bundle_id=apple_id if Platform.IOS in selected else None,
            apple_min_version=self.apple_min_version if Platform.IOS in selected else None,
            apple_target_version=self.apple_target_version if Platform.IOS in selected else None,
            package_kinds=tuple(package_kinds),
            permissions=tuple(self.mobile_permissions),
            requested_capabilities=tuple(self.mobile_requested_capabilities),
            network_intent=self.mobile_network_intent,
            release_channel=self.mobile_release_channel,
            signing_intent=self.mobile_signing_intent,
            budget=self.mobile_budget,
        )

    def build(self) -> ProjectDNA:
        is_game = self.project_type is ProjectType.GAME
        dna = ProjectDNA(
            schema_version=1,
            name=self.name,
            project_type=self.project_type,
            platforms=list(self.platforms),
            engine=self.engine if is_game else None,
            engine_version=self.engine_version if is_game else None,
            dimension=self.dimension if is_game else None,
            genres=list(self.genres) if is_game else [],
            inputs=list(self.inputs) if is_game else [],
            graphics_style=self.graphics_style if is_game else None,
            online=self.online if is_game else DecisionState.NO,
            multiplayer=self.multiplayer if is_game else DecisionState.NO,
            performance=self._performance_for_targets(),
            tools=dict(self.tools),
            download_policy=self.download_policy,
            install_policy=self.install_policy,
            lineage=dict(self.lineage),
            capabilities=dict(self.capabilities),
            desktop=self._desktop_profile(),
            mobile=self._mobile_profile(),
        )
        dna.validate()
        return dna
