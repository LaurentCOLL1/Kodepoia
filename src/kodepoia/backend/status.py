from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .contracts import canonical_sha256


class BackendOperationStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    BLOCKED = "BLOCKED"
    AUTHORIZED = "AUTHORIZED"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class BackendErrorCode(StrEnum):
    INVALID_CONTRACT = "INVALID_CONTRACT"
    ENVIRONMENT_MISMATCH = "ENVIRONMENT_MISMATCH"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    KILL_SWITCH_ACTIVE = "KILL_SWITCH_ACTIVE"
    NETWORK_DENIED = "NETWORK_DENIED"
    ENDPOINT_NOT_ALLOWLISTED = "ENDPOINT_NOT_ALLOWLISTED"
    DNS_RESOLUTION_FAILED = "DNS_RESOLUTION_FAILED"
    SSRF_ADDRESS_REJECTED = "SSRF_ADDRESS_REJECTED"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_FAILED = "PROVIDER_FAILED"


@dataclass(frozen=True, slots=True)
class BackendStatusSnapshot:
    operation_id: str
    status: BackendOperationStatus
    error_code: BackendErrorCode | None = None
    evidence_digest: str = ""

    def __post_init__(self) -> None:
        if (
            not isinstance(self.operation_id, str)
            or not self.operation_id
            or self.operation_id != self.operation_id.strip()
            or len(self.operation_id) > 128
        ):
            raise ValueError("operation_id must be a bounded stable identifier")
        if self.evidence_digest and (
            len(self.evidence_digest) != 64
            or any(char not in "0123456789abcdef" for char in self.evidence_digest)
        ):
            raise ValueError("evidence_digest must be lowercase SHA-256")
        if self.status in {BackendOperationStatus.BLOCKED, BackendOperationStatus.FAILED}:
            if self.error_code is None:
                raise ValueError(f"{self.status.value} requires an error_code")
        elif self.error_code is not None:
            raise ValueError("error_code is only valid for BLOCKED or FAILED status")
        if self.status is BackendOperationStatus.SUCCEEDED and not self.evidence_digest:
            raise ValueError("SUCCEEDED requires evidence_digest")
        if self.status in {BackendOperationStatus.NOT_STARTED, BackendOperationStatus.AUTHORIZED} and self.evidence_digest:
            raise ValueError(f"{self.status.value} cannot claim result evidence")

    def canonical(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "status": self.status.value,
            "error_code": self.error_code.value if self.error_code is not None else None,
            "evidence_digest": self.evidence_digest,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())
