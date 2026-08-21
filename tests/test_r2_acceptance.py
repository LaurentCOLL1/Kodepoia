from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import yaml

from kodepoia.product.spec import (
    AcceptanceCriterion,
    ProductDocumentType,
    ProductSpec,
    Requirement,
)
from kodepoia.project.dna import (
    ApprovalPolicy,
    DecisionState,
    Dimension,
    PerformanceBudget,
    Platform,
    ProjectDNA,
    ProjectType,
)
from kodepoia.project.initializer import ProjectInitializer
from kodepoia.project.wizard import ProjectWizardState


ROOT = Path(__file__).resolve().parents[1]


def complete_state() -> ProjectWizardState:
    return ProjectWizardState(
        name="AcceptanceGame",
        project_type=ProjectType.GAME,
        platforms=[Platform.WINDOWS, Platform.ANDROID],
        engine="Godot",
        engine_version="4.7",
        dimension=Dimension.D3,
        genres=["RPG", "simulation"],
        inputs=["keyboard", "mouse", "touch", "gyro"],
        graphics_style="realistic",
        online=DecisionState.UNDECIDED,
        multiplayer=DecisionState.NO,
        performance={
            "windows": PerformanceBudget(60, 45, 12_000, 24_000, 20_000),
            "android": PerformanceBudget(60, 30, 4_000, 8_000, 4_000),
        },
        tools={"ollama": True, "blender": True, "comfyui": True, "research": False},
        download_policy=ApprovalPolicy.ASK,
        install_policy=ApprovalPolicy.DENY,
        lineage={"franchise": "DemoVerse", "template": "Godot-3D"},
        capabilities={
            "modding": DecisionState.UNDECIDED,
            "procedural_generation": DecisionState.YES,
        },
    )


def test_complete_project_dna_roundtrip_and_schema(tmp_path: Path) -> None:
    dna = complete_state().build()
    path = tmp_path / "project.yaml"
    dna.save(path)
    loaded = ProjectDNA.load(path)

    assert loaded.platforms == [Platform.WINDOWS, Platform.ANDROID]
    assert loaded.performance["windows"].max_vram_mb == 12_000
    assert loaded.tools["comfyui"] is True
    assert loaded.install_policy is ApprovalPolicy.DENY
    assert loaded.lineage["franchise"] == "DemoVerse"
    assert loaded.capabilities["procedural_generation"] is DecisionState.YES

    schema = json.loads((ROOT / "schemas" / "project-dna-v1.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(loaded.to_dict(), schema)


def test_wizard_adapts_to_mobile_xr_and_non_game() -> None:
    windows = ProjectWizardState(name="WindowsOnly", platforms=[Platform.WINDOWS])
    assert "touch" not in windows.relevant_questions()
    assert "motion_controllers" not in windows.relevant_questions()

    mobile_xr = ProjectWizardState(
        name="Hybrid",
        platforms=[Platform.WINDOWS, Platform.ANDROID, Platform.XR],
    )
    questions = mobile_xr.relevant_questions()
    assert "touch" in questions
    assert "gyro" in questions
    assert "motion_controllers" in questions

    app = ProjectWizardState(
        name="DesktopTool",
        project_type=ProjectType.DESKTOP_APP,
        platforms=[Platform.WINDOWS],
        dimension=Dimension.D3,
    )
    app_questions = app.relevant_questions()
    assert "dimension" not in app_questions
    assert app.build().dimension is None


def test_product_gdd_roundtrip_traceability_and_schema(tmp_path: Path) -> None:
    product = ProductSpec(
        schema_version=1,
        product_name="AcceptanceGame",
        vision="Build a local-first game project with measurable acceptance.",
        document_type=ProductDocumentType.GDD,
        summary="Acceptance GDD",
        goals=["Playable vertical slice"],
        success_metrics=["60 FPS on Windows"],
        constraints=["No cloud LLM dependency"],
        mvp=["Movement", "Save/load"],
        requirements=[
            Requirement(
                "REQ-001",
                "Windows target",
                "The first build targets Windows.",
                priority="P0",
                acceptance=[AcceptanceCriterion("REQ-001-AC-1", "Windows build succeeds")],
            )
        ],
        out_of_scope=["Console release"],
    )
    product.trace_requirement(
        "REQ-001",
        code_refs=["project.godot"],
        test_refs=["tests/windows_export.gd"],
    )

    path = tmp_path / "product.yaml"
    product.save(path)
    loaded = ProductSpec.load(path)
    assert loaded.document_type is ProductDocumentType.GDD
    assert loaded.requirement("REQ-001").code_refs == ["project.godot"]
    assert loaded.requirement("REQ-001").test_refs == ["tests/windows_export.gd"]

    schema = json.loads((ROOT / "schemas" / "product-spec-v1.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(yaml.safe_load(path.read_text(encoding="utf-8")), schema)


def test_initializer_persists_full_dna_and_product(tmp_path: Path) -> None:
    dna = complete_state().build()
    product = ProductSpec(
        1,
        dna.name,
        "Persistent product vision",
        document_type=ProductDocumentType.GDD,
        mvp=["First playable"],
    )
    result = ProjectInitializer().initialize(tmp_path / "AcceptanceGame", dna, product)
    loaded_dna = ProjectDNA.load(result.dna_path)
    loaded_product = ProductSpec.load(result.product_path)
    assert loaded_dna.tools["blender"] is True
    assert loaded_product.mvp == ["First playable"]
