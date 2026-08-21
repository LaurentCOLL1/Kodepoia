from __future__ import annotations

from dataclasses import dataclass, field

from kodepoia.project.dna import Dimension, PerformanceBudget, Platform, ProjectDNA, ProjectType


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

    def relevant_questions(self) -> tuple[str, ...]:
        questions = ["project_type", "platforms"]
        if self.project_type is ProjectType.GAME:
            questions += ["engine", "engine_version", "dimension", "genres", "graphics_style", "inputs"]
        if {Platform.ANDROID, Platform.IOS} & set(self.platforms):
            questions += ["touch", "gyro", "mobile_performance"]
        if Platform.XR in self.platforms:
            questions += ["openxr", "motion_controllers"]
        return tuple(questions)

    def build(self) -> ProjectDNA:
        performance = {platform.value: PerformanceBudget() for platform in self.platforms}
        dna = ProjectDNA(schema_version=1, name=self.name, project_type=self.project_type, platforms=self.platforms,
                         engine=self.engine, engine_version=self.engine_version,
                         dimension=self.dimension if self.project_type is ProjectType.GAME else None,
                         genres=self.genres, inputs=self.inputs, graphics_style=self.graphics_style, performance=performance)
        dna.validate()
        return dna
