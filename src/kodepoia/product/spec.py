from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True, slots=True)
class AcceptanceCriterion:
    id: str
    text: str


@dataclass(slots=True)
class Requirement:
    id: str
    title: str
    description: str
    priority: str = "P1"
    acceptance: list[AcceptanceCriterion] = field(default_factory=list)
    code_refs: list[str] = field(default_factory=list)
    test_refs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ProductSpec:
    schema_version: int
    product_name: str
    vision: str
    mvp: list[str] = field(default_factory=list)
    requirements: list[Requirement] = field(default_factory=list)
    out_of_scope: list[str] = field(default_factory=list)

    def validate(self) -> None:
        ids = [requirement.id for requirement in self.requirements]
        if len(ids) != len(set(ids)):
            raise ValueError("Requirement IDs must be unique")
        for req in self.requirements:
            acceptance_ids = [item.id for item in req.acceptance]
            if len(acceptance_ids) != len(set(acceptance_ids)):
                raise ValueError(f"Duplicate acceptance criteria in {req.id}")

    def save(self, path: Path) -> None:
        self.validate()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(asdict(self), sort_keys=False, allow_unicode=True), encoding="utf-8")
