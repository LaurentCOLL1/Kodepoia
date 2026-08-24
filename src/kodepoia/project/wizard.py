from __future__ import annotations

from dataclasses import dataclass, field

from kodepoia.desktop.contracts import (
    DesktopArchitecture,
    DesktopFramework,
    DesktopPackageKind,
)
from kodepoia.project.dna import (
    ApprovalPolicy,
    DecisionState,
    DesktopProjectProfile,
    Dimension,
    PerformanceBudget,
    Platform,
    ProjectDNA,
    ProjectType,
)


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

    def build(self) -> ProjectDNA:
        dna = ProjectDNA(
            schema_version=1,
            name=self.name,
            project_type=self.project_type,
            platforms=list(self.platforms),
            engine=self.engine if self.project_type is ProjectType.GAME else None,
            engine_version=(
                self.engine_version if self.project_type is ProjectType.GAME else None
            ),
            dimension=self.dimension if self.project_type is ProjectType.GAME else None,
            genres=list(self.genres) if self.project_type is ProjectType.GAME else [],
            inputs=list(self.inputs) if self.project_type is ProjectType.GAME else [],
            graphics_style=(
                self.graphics_style if self.project_type is ProjectType.GAME else None
            ),
            online=self.online if self.project_type is ProjectType.GAME else DecisionState.NO,
            multiplayer=(
                self.multiplayer if self.project_type is ProjectType.GAME else DecisionState.NO
            ),
            performance=self._performance_for_targets(),
            tools=dict(self.tools),
            download_policy=self.download_policy,
            install_policy=self.install_policy,
            lineage=dict(self.lineage),
            capabilities=dict(self.capabilities),
            desktop=self._desktop_profile(),
        )
        dna.validate()
        return dna
