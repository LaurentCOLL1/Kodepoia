from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DataClass(StrEnum):
    PUBLIC = "public"
    PROJECT = "project"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"


@dataclass(frozen=True, slots=True)
class DataPolicy:
    classification: DataClass
    project_memory: bool = True
    global_memory: bool = False
    training_dataset: bool = False
    external_research: bool = False
    delete_with_project: bool = True


class KodeDataGovernance:
    """Answers whether a data movement is permitted by declared policy."""

    def can_store_globally(self, policy: DataPolicy) -> bool:
        return policy.global_memory and policy.classification in {DataClass.PUBLIC, DataClass.PROJECT}

    def can_train(self, policy: DataPolicy) -> bool:
        return policy.training_dataset and policy.classification is DataClass.PUBLIC

    def can_send_to_research(self, policy: DataPolicy) -> bool:
        return policy.external_research and policy.classification is DataClass.PUBLIC

    def assert_external_research_allowed(self, policy: DataPolicy) -> None:
        if not self.can_send_to_research(policy):
            raise PermissionError("data policy forbids sending this content to external research")
