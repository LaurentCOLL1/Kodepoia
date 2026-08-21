from pathlib import Path

import pytest

from kodepoia.product.spec import AcceptanceCriterion, ProductSpec, Requirement
from kodepoia.project.dna import Dimension, Platform, ProjectDNA, ProjectType
from kodepoia.project.wizard import ProjectWizardState


def test_windows_only_wizard_hides_mobile_questions() -> None:
    state = ProjectWizardState(name="Demo", platforms=[Platform.WINDOWS])
    questions = state.relevant_questions()
    assert "touch" not in questions
    assert "gyro" not in questions


def test_windows_only_rejects_touch_input() -> None:
    dna = ProjectDNA(schema_version=1, name="Demo", project_type=ProjectType.GAME, platforms=[Platform.WINDOWS], dimension=Dimension.D3, inputs=["keyboard", "touch"])
    with pytest.raises(ValueError):
        dna.validate()


def test_dna_roundtrip(tmp_path: Path) -> None:
    dna = ProjectWizardState(name="Demo").build()
    path = tmp_path / "project.yaml"
    dna.save(path)
    loaded = ProjectDNA.load(path)
    assert loaded.name == "Demo"
    assert loaded.platforms == [Platform.WINDOWS]


def test_product_requirement_ids_unique() -> None:
    spec = ProductSpec(schema_version=1, product_name="Demo", vision="Test", requirements=[Requirement("REQ-001", "A", "B", acceptance=[AcceptanceCriterion("AC-1", "Works")])])
    spec.validate()
