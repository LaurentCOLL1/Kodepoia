from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping

from kodepoia.media.contracts import bounded_text, stable_id


class BranchOperator(StrEnum):
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"


Scalar = str | int | float | bool


def _scalar(value: object, *, field: str) -> Scalar:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        if abs(value) > 1_000_000_000:
            raise ValueError(f"{field} integer outside bounded range")
        return value
    if isinstance(value, float):
        if not math.isfinite(value) or abs(value) > 1_000_000_000:
            raise ValueError(f"{field} float must be finite and bounded")
        return value
    if isinstance(value, str):
        return bounded_text(value, field=field, maximum=256)
    raise TypeError(f"{field} must be a scalar")


@dataclass(frozen=True, slots=True)
class BranchCondition:
    condition_id: str
    context_key: str
    operator: BranchOperator
    expected: Scalar
    true_target: str
    false_target: str

    def __post_init__(self) -> None:
        stable_id(self.condition_id, field="condition_id")
        stable_id(self.context_key, field="context_key")
        if not isinstance(self.operator, BranchOperator):
            raise TypeError("operator must be BranchOperator")
        _scalar(self.expected, field="expected")
        stable_id(self.true_target, field="true_target")
        stable_id(self.false_target, field="false_target")
        if self.true_target == self.false_target:
            raise ValueError("branch targets must differ")


def evaluate_branch(condition: BranchCondition, context: Mapping[str, object]) -> str:
    if set(context) - {condition.context_key}:
        raise ValueError("branch context contains unrequested keys")
    if condition.context_key not in context:
        raise KeyError(condition.context_key)
    actual = _scalar(context[condition.context_key], field="actual")
    expected = _scalar(condition.expected, field="expected")
    if condition.operator in {BranchOperator.GT, BranchOperator.GTE, BranchOperator.LT, BranchOperator.LTE}:
        if isinstance(actual, bool) or isinstance(expected, bool) or not isinstance(actual, (int, float)) or not isinstance(expected, (int, float)):
            raise TypeError("ordered branch operators require numeric scalars")
    result = {
        BranchOperator.EQ: actual == expected,
        BranchOperator.NE: actual != expected,
        BranchOperator.GT: actual > expected,
        BranchOperator.GTE: actual >= expected,
        BranchOperator.LT: actual < expected,
        BranchOperator.LTE: actual <= expected,
    }[condition.operator]
    return condition.true_target if result else condition.false_target
