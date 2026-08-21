from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DataScope(StrEnum):
    PROJECT = "project"
    GLOBAL = "global"


@dataclass(frozen=True, slots=True)
class GovernancePolicy:
    scope: DataScope = DataScope.PROJECT
    allow_global_memory: bool = False
    allow_training_dataset: bool = False
    delete_with_project: bool = True
    confidential: bool = False

    def can_promote_global(self) -> bool:
        return self.allow_global_memory and not self.confidential

    def can_train(self) -> bool:
        return self.allow_training_dataset and not self.confidential
