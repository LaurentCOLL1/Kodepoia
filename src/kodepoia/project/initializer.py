from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from kodepoia.product.spec import ProductSpec
from kodepoia.project.dna import ProjectDNA


@dataclass(frozen=True, slots=True)
class InitializedProject:
    root: Path
    metadata_root: Path
    dna_path: Path
    product_path: Path


class ProjectInitializer:
    DIRECTORIES = ("architecture", "decisions", "memory", "graphs", "health", "budgets", "tests", "visual_tests", "benchmarks", "audit", "backups", "snapshots", "research", "licenses", "bom", "workflows", "diagnostics", "releases")

    def initialize(self, root: Path, dna: ProjectDNA, product: ProductSpec | None = None) -> InitializedProject:
        root = root.resolve(strict=False)
        root.mkdir(parents=True, exist_ok=True)
        metadata = root / ".kodepoia"
        metadata.mkdir(parents=True, exist_ok=True)
        for name in self.DIRECTORIES:
            (metadata / name).mkdir(exist_ok=True)
        dna_path = metadata / "project.yaml"
        dna.save(dna_path)
        product_path = metadata / "product" / "product.yaml"
        product_path.parent.mkdir(exist_ok=True)
        (product or ProductSpec(1, dna.name, "To be defined")).save(product_path)
        return InitializedProject(root, metadata, dna_path, product_path)
