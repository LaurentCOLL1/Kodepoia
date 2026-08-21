from __future__ import annotations

from dataclasses import dataclass, field

from kodepoia.project.dna import (
    ApprovalPolicy,
    DecisionState,
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

    def build(self) -> ProjectDNA:
        dna = ProjectDNA(
            schema_version=1,
            name=self.name,
            project_type=self.project_type,
            platforms=list(self.platforms),
            engine=self.engine,
            engine_version=self.engine_version,
            dimension=self.dimension if self.project_type is ProjectType.GAME else None,
            genres=list(self.genres),
            inputs=list(self.inputs),
            graphics_style=self.graphics_style,
            online=self.online,
            multiplayer=self.multiplayer,
            performance=self._performance_for_targets(),
            tools=dict(self.tools),
            download_policy=self.download_policy,
            install_policy=self.install_policy,
            lineage=dict(self.lineage),
            capabilities=dict(self.capabilities),
        )
        dna.validate()
        return dna
