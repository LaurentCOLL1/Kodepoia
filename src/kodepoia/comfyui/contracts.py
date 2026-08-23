from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


def _bounded_text(value: str, *, field_name: str, maximum: int, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if (not allow_empty and not value) or len(value) > maximum:
        if allow_empty:
            raise ValueError(f"{field_name} must be at most {maximum} characters")
        raise ValueError(f"{field_name} must be between 1 and {maximum} characters")
    if _CONTROL_RE.search(value):
        raise ValueError(f"{field_name} must not contain control characters")
    return value


class ComfyCapabilityState(StrEnum):
    UNKNOWN = "unknown"
    CURRENT = "current"
    STALE = "stale"
    UNAVAILABLE = "unavailable"
    BLOCKED = "blocked"
    CORRUPT = "corrupt"


class ComfyQueueState(StrEnum):
    UNKNOWN = "unknown"
    NOT_QUEUED = "not_queued"
    QUEUED = "queued"
    RUNNING = "running"
    TERMINAL = "terminal"


class ComfyRunState(StrEnum):
    UNKNOWN = "unknown"
    PREPARED = "prepared"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ComfyResourceStatus(StrEnum):
    UNKNOWN = "unknown"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    BLOCKED = "blocked"
    STALE = "stale"
    MISSING = "missing"
    CORRUPT = "corrupt"


_TERMINAL_RUN_STATES = frozenset(
    {ComfyRunState.SUCCEEDED, ComfyRunState.FAILED, ComfyRunState.CANCELLED}
)
_RUN_TRANSITIONS: dict[ComfyRunState, frozenset[ComfyRunState]] = {
    ComfyRunState.UNKNOWN: frozenset(
        {
            ComfyRunState.PREPARED,
            ComfyRunState.QUEUED,
            ComfyRunState.RUNNING,
            ComfyRunState.SUCCEEDED,
            ComfyRunState.FAILED,
            ComfyRunState.CANCELLED,
        }
    ),
    ComfyRunState.PREPARED: frozenset(
        {ComfyRunState.QUEUED, ComfyRunState.FAILED, ComfyRunState.CANCELLED}
    ),
    ComfyRunState.QUEUED: frozenset(
        {ComfyRunState.RUNNING, ComfyRunState.FAILED, ComfyRunState.CANCELLED}
    ),
    ComfyRunState.RUNNING: frozenset(_TERMINAL_RUN_STATES),
    ComfyRunState.SUCCEEDED: frozenset(),
    ComfyRunState.FAILED: frozenset(),
    ComfyRunState.CANCELLED: frozenset(),
}


def is_terminal_run_state(state: ComfyRunState) -> bool:
    return state in _TERMINAL_RUN_STATES


def can_transition_run_state(previous: ComfyRunState, current: ComfyRunState) -> bool:
    return previous == current or current in _RUN_TRANSITIONS[previous]


@dataclass(frozen=True, slots=True)
class ComfyPromptReference:
    prompt_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "prompt_id",
            _bounded_text(self.prompt_id, field_name="prompt_id", maximum=128),
        )

    def canonical(self) -> dict[str, Any]:
        return {"prompt_id": self.prompt_id}


@dataclass(frozen=True, slots=True)
class ComfyHistoryReference:
    prompt_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "prompt_id",
            _bounded_text(self.prompt_id, field_name="prompt_id", maximum=128),
        )

    @classmethod
    def from_prompt(cls, prompt: ComfyPromptReference) -> "ComfyHistoryReference":
        return cls(prompt_id=prompt.prompt_id)

    def canonical(self) -> dict[str, Any]:
        return {"prompt_id": self.prompt_id}


@dataclass(frozen=True, slots=True)
class ComfyOutputReference:
    prompt_id: str
    node_id: str
    output_index: int
    server_filename: str
    server_subfolder: str = ""
    storage_type: str = "output"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "prompt_id",
            _bounded_text(self.prompt_id, field_name="prompt_id", maximum=128),
        )
        object.__setattr__(
            self,
            "node_id",
            _bounded_text(self.node_id, field_name="node_id", maximum=128),
        )
        if self.output_index < 0:
            raise ValueError("output_index must be >= 0")
        object.__setattr__(
            self,
            "server_filename",
            _bounded_text(self.server_filename, field_name="server_filename", maximum=512),
        )
        object.__setattr__(
            self,
            "server_subfolder",
            _bounded_text(
                self.server_subfolder,
                field_name="server_subfolder",
                maximum=512,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "storage_type",
            _bounded_text(self.storage_type, field_name="storage_type", maximum=64),
        )

    def canonical(self) -> dict[str, Any]:
        return {
            "prompt_id": self.prompt_id,
            "node_id": self.node_id,
            "output_index": self.output_index,
            "server_filename": self.server_filename,
            "server_subfolder": self.server_subfolder,
            "storage_type": self.storage_type,
        }


@dataclass(frozen=True, slots=True)
class ComfyTransportLimits:
    connect_timeout_seconds: float = 5.0
    read_timeout_seconds: float = 30.0
    total_timeout_seconds: float = 120.0
    max_json_bytes: int = 8 * 1024 * 1024
    max_binary_bytes: int = 256 * 1024 * 1024
    max_websocket_frame_bytes: int = 16 * 1024 * 1024

    def __post_init__(self) -> None:
        for name in (
            "connect_timeout_seconds",
            "read_timeout_seconds",
            "total_timeout_seconds",
        ):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and > 0")
        if self.total_timeout_seconds < self.connect_timeout_seconds:
            raise ValueError("total_timeout_seconds must be >= connect_timeout_seconds")
        for name in ("max_json_bytes", "max_binary_bytes", "max_websocket_frame_bytes"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")

    def canonical(self) -> dict[str, Any]:
        return {
            "connect_timeout_seconds": self.connect_timeout_seconds,
            "read_timeout_seconds": self.read_timeout_seconds,
            "total_timeout_seconds": self.total_timeout_seconds,
            "max_json_bytes": self.max_json_bytes,
            "max_binary_bytes": self.max_binary_bytes,
            "max_websocket_frame_bytes": self.max_websocket_frame_bytes,
        }
