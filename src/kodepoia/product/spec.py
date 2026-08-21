from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path

import yaml


class ProductDocumentType(StrEnum):
    GDD = "gdd"
    PRD = "prd"
    TECHNICAL_SPEC = "technical_spec"


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

    def validate(self) -> None:
        if not self.id.strip():
            raise ValueError("Requirement ID is required")
        if not self.title.strip():
            raise ValueError(f"Requirement {self.id} requires a title")
        if self.priority not in {"P0", "P1", "P2", "P3"}:
            raise ValueError(f"Unsupported requirement priority: {self.priority}")
        acceptance_ids = [item.id for item in self.acceptance]
        if len(acceptance_ids) != len(set(acceptance_ids)):
            raise ValueError(f"Duplicate acceptance criteria in {self.id}")
        if any(not item.id.strip() or not item.text.strip() for item in self.acceptance):
            raise ValueError(f"Acceptance criteria in {self.id} must have id and text")


@dataclass(slots=True)
class ProductSpec:
    schema_version: int
    product_name: str
    vision: str
    document_type: ProductDocumentType = ProductDocumentType.PRD
    summary: str = ""
    goals: list[str] = field(default_factory=list)
    success_metrics: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    mvp: list[str] = field(default_factory=list)
    requirements: list[Requirement] = field(default_factory=list)
    out_of_scope: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if self.schema_version != 1:
            raise ValueError(f"Unsupported ProductSpec schema version: {self.schema_version}")
        if not self.product_name.strip():
            raise ValueError("Product name is required")
        if not self.vision.strip():
            raise ValueError("Product vision is required")
        ids = [requirement.id for requirement in self.requirements]
        if len(ids) != len(set(ids)):
            raise ValueError("Requirement IDs must be unique")
        for requirement in self.requirements:
            requirement.validate()

    def requirement(self, requirement_id: str) -> Requirement:
        for item in self.requirements:
            if item.id == requirement_id:
                return item
        raise KeyError(requirement_id)

    def trace_requirement(
        self,
        requirement_id: str,
        *,
        code_refs: list[str] | None = None,
        test_refs: list[str] | None = None,
    ) -> None:
        requirement = self.requirement(requirement_id)
        if code_refs:
            requirement.code_refs = list(dict.fromkeys([*requirement.code_refs, *code_refs]))
        if test_refs:
            requirement.test_refs = list(dict.fromkeys([*requirement.test_refs, *test_refs]))

    def save(self, path: Path) -> None:
        self.validate()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(self)
        payload["document_type"] = self.document_type.value
        path.write_text(
            yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> "ProductSpec":
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("Product spec must be a YAML object")
        requirements = []
        for item in raw.get("requirements", []):
            requirements.append(
                Requirement(
                    id=str(item["id"]),
                    title=str(item["title"]),
                    description=str(item.get("description", "")),
                    priority=str(item.get("priority", "P1")),
                    acceptance=[
                        AcceptanceCriterion(str(ac["id"]), str(ac["text"]))
                        for ac in item.get("acceptance", [])
                    ],
                    code_refs=[str(value) for value in item.get("code_refs", [])],
                    test_refs=[str(value) for value in item.get("test_refs", [])],
                )
            )
        spec = cls(
            schema_version=int(raw["schema_version"]),
            product_name=str(raw["product_name"]),
            vision=str(raw["vision"]),
            document_type=ProductDocumentType(raw.get("document_type", "prd")),
            summary=str(raw.get("summary", "")),
            goals=[str(value) for value in raw.get("goals", [])],
            success_metrics=[str(value) for value in raw.get("success_metrics", [])],
            constraints=[str(value) for value in raw.get("constraints", [])],
            mvp=[str(value) for value in raw.get("mvp", [])],
            requirements=requirements,
            out_of_scope=[str(value) for value in raw.get("out_of_scope", [])],
        )
        spec.validate()
        return spec
