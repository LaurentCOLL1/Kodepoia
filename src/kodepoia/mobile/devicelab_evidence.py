from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .contracts import canonical_json_bytes
from .devicelab import (
    DeviceLabLease,
    DeviceLabMatrixDefinition,
    DeviceLabNormalizedResult,
    DeviceLabResultState,
    DeviceLabRouteDecision,
)


@dataclass(frozen=True, slots=True)
class DeviceLabEvidenceBundle:
    schema_version: int
    matrix: DeviceLabMatrixDefinition
    route: DeviceLabRouteDecision
    lease: DeviceLabLease
    results: tuple[DeviceLabNormalizedResult, ...]
    cleanup_complete: bool
    status: str = "pass"

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("R13.12 DeviceLab evidence schema version must be 1")
        results = tuple(self.results)
        if not results or len(results) > 64:
            raise ValueError("DeviceLab evidence requires 1..64 normalized results")
        object.__setattr__(self, "results", results)
        self.lease.assert_matches(self.matrix, self.route)
        for result in results:
            result.assert_bound_to(self.matrix)
            if result.provider is not self.route.provider:
                raise ValueError("provider result does not match selected DeviceLab route")
        if self.status != "pass":
            raise ValueError("this evidence type represents accepted DeviceLab evidence only")
        if any(result.result is not DeviceLabResultState.PASSED for result in results):
            raise ValueError("DeviceLab PASS requires every normalized result to pass")
        if not self.cleanup_complete:
            raise ValueError("DeviceLab PASS requires owned lease/execution cleanup")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "matrix": self.matrix.to_dict(),
            "matrix_sha256": self.matrix.digest(),
            "route": self.route.to_dict(),
            "route_sha256": self.route.digest(),
            "lease": self.lease.to_dict(),
            "results": [item.to_dict() for item in self.results],
            "cleanup_complete": self.cleanup_complete,
            "status": self.status,
        }

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_dict())

    def digest(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()
