from pathlib import Path

from kodepoia.project.initializer import ProjectInitializer
from kodepoia.project.wizard import ProjectWizardState


def test_initializer_creates_project_metadata(tmp_path: Path) -> None:
    result = ProjectInitializer().initialize(tmp_path / "Demo", ProjectWizardState(name="Demo").build())
    assert result.dna_path.exists()
    assert result.product_path.exists()
    assert (result.metadata_root / "memory").is_dir()
    assert (result.metadata_root / "audit").is_dir()
